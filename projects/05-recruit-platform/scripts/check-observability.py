#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段三（性能与可观测）的验证脚本。

对着一个正在跑的后端（默认 http://127.0.0.1:8080）逐条断言：

  1. /actuator/health 返回 UP（数据库探针通）
  2. Actuator 只暴露 health/info，/actuator/env 是 404
  3. 鉴权没有被健康检查改动：无 token 的 /api/notifications 仍返回 401
  4. 日志级别分离：
       --profile dev   -> 有 MyBatis 的 Preparing 行（SQL 日志确实开着）
       --profile prod  -> 没有 Preparing 行，但「登录成功」这类 INFO 业务日志还在
     后半句是阳性对照：证明「没有 SQL」不是因为日志根本没写。
  5. 两处列表接口的 N+1 已消掉：file_resource 查询数与列表条数无关（3 条和 1 条都只查 1 次），
     并且返回体里每条的 fileUrl 确实被批量装配上了（不是靠少查几条把数据丢掉换来的）。

用法：
    py -3 scripts/check-observability.py --profile dev
    py -3 scripts/check-observability.py --profile prod

SQL 计数依赖 MyBatis 的 DEBUG 日志，只有 dev profile 能测；prod 模式下这几条记 SKIP。
本脚本用 docker exec 直接读写演示库做夹具，需要 recruit-mysql 容器在跑。
"""
import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = "http://127.0.0.1:8080"
SEED_PWD = "Demo@1234"
PREFIX = "stage3check-"
DEFAULT_LOG = Path(__file__).resolve().parents[1] / "backend" / "logs" / "application.log"

rows = []


def add(state, label, detail=""):
    rows.append((state, label, detail))


def call(method, path, body=None, token=None, raw=False):
    data = json.dumps(body).encode() if body is not None else None
    headers = {}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read()
            if raw:
                return resp.status, payload
            return resp.status, json.loads(payload.decode() or "{}")
    except urllib.error.HTTPError as exc:
        payload = exc.read()
        if raw:
            return exc.code, payload
        try:
            return exc.code, json.loads(payload.decode() or "{}")
        except Exception:
            return exc.code, {"code": exc.code, "message": payload[:80].decode("utf-8", "replace")}


def mysql(sql, container):
    """执行 SQL，返回行的列表（每个元素是按 tab 切开的字段）。失败抛 RuntimeError。"""
    proc = subprocess.run(
        ["docker", "exec", container, "mysql", "-uroot", "-proot_pwd_2026", "-N", "-B", "-e", sql],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "").strip()[:300])
    head = proc.stdout.split("\n", 1)[0].strip().lower()
    if head.startswith("mysql:") or head.startswith("warning"):
        proc.stdout = proc.stdout.split("\n", 1)[1] if "\n" in proc.stdout else ""
    return [line.split("\t") for line in proc.stdout.splitlines() if line.strip()]


def log_size(log_path):
    try:
        return Path(log_path).stat().st_size
    except OSError:
        return None


def new_log_lines(log_path, mark):
    path = Path(log_path)
    try:
        size = path.stat().st_size
    except OSError:
        return []
    if mark is None or size < mark:
        mark = 0
    with open(path, "rb") as handle:
        handle.seek(mark)
        text = handle.read().decode("utf-8", errors="replace")
    return text.splitlines()


def count_sql(lines, table=None):
    pattern = re.compile(r"Preparing:\s*.*\bFROM\s+" + (re.escape(table) if table else r"\w+"), re.I)
    return sum(1 for line in lines if pattern.search(line))


def main():
    global BASE
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE)
    parser.add_argument("--profile", choices=["dev", "prod"], default="dev")
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--mysql-container", default="recruit-mysql")
    args = parser.parse_args()

    BASE = args.base
    profile = args.profile
    log_path = args.log

    # ---------------------------------------------------------------- 1. 健康检查
    status, body = call("GET", "/actuator/health", raw=True)
    try:
        health = json.loads(body.decode() or "{}")
    except Exception:
        health = {}
    if status == 200 and health.get("status") == "UP":
        add("PASS", "GET /actuator/health 返回 UP", f"{status}")
    else:
        add("FAIL", "GET /actuator/health 返回 UP", f"status={status} body={body[:120]!r}")

    # ---------------------------------------------------------------- 2. 端点暴露范围
    status, body = call("GET", "/actuator", raw=True)
    try:
        links = sorted(json.loads(body.decode() or "{}").get("_links", {}).keys())
    except Exception:
        links = []
    exposed = [link for link in links if link != "self"]
    sensitive = {"env", "beans", "heapdump", "threaddump", "configprops", "mappings", "loggers"}
    if status == 200 and "health" in exposed and not (sensitive & set(exposed)):
        add("PASS", "/actuator 只暴露健康检查相关端点", f"{exposed}")
    else:
        add("FAIL", "/actuator 只暴露健康检查相关端点", f"status={status} links={links}")

    status, body = call("GET", "/actuator/env", raw=True)
    if b"propertySources" not in body and b"systemProperties" not in body:
        add("PASS", "/actuator/env 取不到配置内容", f"status={status} body={body[:60]!r}")
    else:
        add("FAIL", "/actuator/env 取不到配置内容", f"status={status} 返回了配置")

    # ---------------------------------------------------------------- 3. 鉴权仍生效
    status, body = call("GET", "/api/notifications")
    code = body.get("code") if isinstance(body, dict) else None
    if code == 401:
        add("PASS", "无 token 访问 /api/notifications 仍被拒", f"code={code}")
    else:
        add("FAIL", "无 token 访问 /api/notifications 仍被拒", f"status={status} code={code}")

    # ---------------------------------------------------------------- 登录（也用作日志阳性对照）
    status, body = call("POST", "/api/auth/login", {"username": "student01", "password": SEED_PWD})
    token = (body.get("data") or {}).get("token") if isinstance(body, dict) else None
    if not token:
        add("FAIL", "演示账号 student01 能登录", f"{body}")
        return
    add("PASS", "演示账号 student01 能登录", "")

    # ---------------------------------------------------------------- 4. 日志级别分离
    mark = log_size(log_path)
    if mark is None:
        add("SKIP", "日志文件可读", f"{log_path} 不存在（确认后端工作目录）")
        lines = []
    else:
        call("POST", "/api/auth/login", {"username": "student01", "password": SEED_PWD})
        call("GET", f"/api/student/resumes/by-student?studentId=1", token=token)
        time.sleep(0.8)
        lines = new_log_lines(log_path, mark)
        info_lines = [line for line in lines if "登录成功" in line]
        sql_lines = [line for line in lines if "Preparing:" in line]
        if info_lines:
            add("PASS", "本次请求留下 INFO 业务日志（阳性对照）", "登录成功")
        else:
            add("FAIL", "本次请求留下 INFO 业务日志（阳性对照）", f"新增 {len(lines)} 行，没有「登录成功」")
        if profile == "dev":
            if sql_lines:
                add("PASS", "dev profile 打印 MyBatis SQL", f"{len(sql_lines)} 行 Preparing")
            else:
                add("FAIL", "dev profile 打印 MyBatis SQL", "没有任何 Preparing 行")
        else:
            if not sql_lines:
                add("PASS", "prod（默认 profile）不打印 SQL", f"新增 {len(lines)} 行日志里 0 行 Preparing")
            else:
                add("FAIL", "prod（默认 profile）不打印 SQL", f"出现 {len(sql_lines)} 行 Preparing")

    # ---------------------------------------------------------------- 5. N+1
    if profile != "dev":
        add("SKIP", "N+1 SQL 计数", "需要 dev profile 的 SQL 日志")
        return

    try:
        cleanup_sql = (
            f"DELETE FROM recruit_resume.resume WHERE resume_name LIKE '{PREFIX}%';"
            f"DELETE FROM recruit_resume.student_skill WHERE skill_name LIKE '{PREFIX}%';"
            f"DELETE FROM recruit_resume.file_resource WHERE file_name LIKE '{PREFIX}%';"
        )
        mysql(cleanup_sql, args.mysql_container)
        html_urls = [f"http://127.0.0.1:9/{PREFIX}f{i}.txt" for i in range(1, 4)]
        values = ",".join(
            f"(2, '{PREFIX}f{i}.txt', 'txt', '{url}', 12, 'CERTIFICATE')"
            for i, url in enumerate(html_urls, 1)
        )
        mysql(
            "INSERT INTO recruit_resume.file_resource "
            "(uploader_id, file_name, file_type, file_url, file_size, business_type) "
            f"VALUES {values};",
            args.mysql_container,
        )
        file_rows = mysql(
            f"SELECT id, file_url FROM recruit_resume.file_resource WHERE file_name LIKE '{PREFIX}%' ORDER BY id;",
            args.mysql_container,
        )
        file_ids = [int(row[0]) for row in file_rows]
        url_by_file = {int(row[0]): row[1] for row in file_rows}
        if len(file_ids) != 3:
            add("FAIL", "夹具：3 个文件资源", f"实际 {len(file_ids)}")
            return
        add("PASS", "夹具：3 个文件资源", ",".join(map(str, file_ids)))
    except Exception as exc:  # noqa: BLE001
        add("SKIP", "N+1 夹具（docker/mysql）", repr(exc)[:200])
        return

    created = []
    try:
        for index, file_id in enumerate(file_ids, 1):
            status, body = call("POST", "/api/student/resumes", {
                "resumeName": f"{PREFIX}resume-{index}",
                "resumeType": "UPLOAD",
                "targetPosition": "阶段三验证",
                "school": "南昌大学",
                "major": "软件工程",
                "fileId": file_id,
            }, token=token)
            data = body.get("data") if isinstance(body, dict) else None
            if isinstance(data, dict) and data.get("id"):
                created.append({"id": data["id"], "fileId": file_id})
        if len(created) != 3:
            add("FAIL", "夹具：创建 3 条简历", f"实际 {len(created)} 条，返回 {body}")
            return
        add("PASS", "夹具：创建 3 条简历", ",".join(str(item["id"]) for item in created))

        def measure(path, label, table_expected_ids):
            mark = log_size(log_path)
            status, body = call("GET", path, token=token)
            time.sleep(0.8)
            lines = new_log_lines(log_path, mark)
            count = count_sql(lines, "file_resource")
            items = (body.get("data") if isinstance(body, dict) else None) or []
            by_id = {item.get("id"): item for item in items if isinstance(item, dict)}
            missing = [i for i in table_expected_ids if i not in by_id]
            return count, by_id, missing

        count3, by_id3, missing3 = measure(
            "/api/student/resumes/by-student?studentId=1", "resumes", [item["id"] for item in created])
        if count3 == 1:
            add("PASS", "简历列表 3 条只查 1 次 file_resource", f"{count3} 次")
        else:
            add("FAIL", "简历列表 3 条只查 1 次 file_resource", f"{count3} 次（N+1 就是 3 次）")
        if not missing3:
            good = all(by_id3[item["id"]].get("fileUrl") == url_by_file[item["fileId"]] for item in created
                       if item["id"] in by_id3)
            if good:
                add("PASS", "简历列表 fileUrl 被正确装配", "3/3 与夹具 URL 一致")
            else:
                add("FAIL", "简历列表 fileUrl 被正确装配", "有条目 fileUrl 为空或不对")
        else:
            add("FAIL", "简历列表 fileUrl 被正确装配", f"返回里缺 {missing3}")

        # 删掉两条，验证「查询数与条数无关」
        for item in created[1:]:
            call("DELETE", f"/api/student/resumes/{item['id']}", token=token)
        count1, by_id1, _missing1 = measure(
            "/api/student/resumes/by-student?studentId=1", "resumes", [created[0]["id"]])
        if count1 == 1 and count1 == count3:
            add("PASS", "简历列表 1 条与 3 条的 SQL 数相同", f"1 条={count1} 3 条={count3}")
        else:
            add("FAIL", "简历列表 1 条与 3 条的 SQL 数相同", f"1 条={count1} 3 条={count3}")

        # 技能列表：同样的批量装配
        created_skills = []
        for index, file_id in enumerate(file_ids, 1):
            status, body = call("POST", "/api/student/skills", {
                "skillName": f"{PREFIX}skill-{index}",
                "skillType": "test",
                "fileId": file_id,
            }, token=token)
            data = body.get("data") if isinstance(body, dict) else None
            if isinstance(data, dict) and data.get("id"):
                created_skills.append({"id": data["id"], "fileId": file_id})
        if len(created_skills) != 3:
            add("FAIL", "夹具：创建 3 条技能", f"实际 {len(created_skills)} 条，返回 {body}")
        else:
            add("PASS", "夹具：创建 3 条技能", ",".join(str(item["id"]) for item in created_skills))
            count_skill, skill_by_id, missing_skill = measure(
                "/api/student/skills/by-student?studentId=1", "skills",
                [item["id"] for item in created_skills])
            if count_skill == 1:
                add("PASS", "技能列表 3 条只查 1 次 file_resource", f"{count_skill} 次")
            else:
                add("FAIL", "技能列表 3 条只查 1 次 file_resource", f"{count_skill} 次（N+1 就是 3 次）")
            if not missing_skill and all(
                    skill_by_id[item["id"]].get("fileUrl") == url_by_file[item["fileId"]]
                    for item in created_skills):
                add("PASS", "技能列表 fileUrl 被正确装配", "3/3 与夹具 URL 一致")
            else:
                add("FAIL", "技能列表 fileUrl 被正确装配", f"缺失 {missing_skill} 或 URL 不对")
    finally:
        try:
            mysql(cleanup_sql, args.mysql_container)
            leftover = mysql(
                f"SELECT (SELECT COUNT(*) FROM recruit_resume.resume WHERE resume_name LIKE '{PREFIX}%')"
                f" + (SELECT COUNT(*) FROM recruit_resume.student_skill WHERE skill_name LIKE '{PREFIX}%')"
                f" + (SELECT COUNT(*) FROM recruit_resume.file_resource WHERE file_name LIKE '{PREFIX}%');",
                args.mysql_container,
            )
            remaining = int(leftover[0][0]) if leftover else -1
            if remaining == 0:
                add("PASS", "夹具已清理干净", "resume / skill / file_resource 残留 0")
            else:
                add("FAIL", "夹具已清理干净", f"残留 {remaining} 行")
        except Exception as exc:  # noqa: BLE001
            add("FAIL", "夹具已清理干净", repr(exc)[:200])


try:
    main()
except Exception as exc:  # noqa: BLE001
    add("FAIL", "脚本执行", repr(exc))

width = max((len(row[1]) for row in rows), default=10)
for state, label, detail in rows:
    print(f"[{state}] {label:<{width}}  {detail}")
counts = {state: sum(1 for row in rows if row[0] == state) for state in ("PASS", "SKIP", "FAIL")}
print(f"\n合计 PASS {counts['PASS']}  SKIP {counts['SKIP']}  FAIL {counts['FAIL']}")
sys.exit(1 if counts["FAIL"] else 0)
