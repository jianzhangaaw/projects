#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段一安全改动的验证脚本。

对着一个正在跑的后端（默认 http://127.0.0.1:8080）逐条验证：
  - 水平越权被拒（企业改别家资料、学生删别人简历/技能）
  - 合法请求仍然通过（防止修过了头）
  - 登录错误信息不再泄露用户名是否存在
  - 弱密码注册被拒
  - 连续失败登录触发临时锁定
  - CORS 不再对任意来源放行

用法：
    python scripts/check-authz.py [base_url]

退出码 0 表示全部通过。脚本会注册两个临时账号（student02 / company02），
重复执行时用户名带时间戳后缀，不会冲突。
"""
import json
import sys
import time
import urllib.error
import urllib.request

# Windows 控制台默认 GBK，中文断言信息会抛 UnicodeEncodeError
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
SUFFIX = str(int(time.time()))[-6:]
STUDENT2 = "student02_" + SUFFIX
COMPANY2 = "company02_" + SUFFIX
PWD = "Demo1234"            # 脚本新注册账号用的密码（满足 8 位 + 字母数字）
SEED_PWD = "Demo@1234"      # 种子数据里三个演示账号的密码

passed = 0
failed = 0
failures = []


def call(method, path, body=None, token=None, raw=False, headers=None):
    url = BASE + path
    data = None
    hdrs = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    if token:
        hdrs["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = resp.read()
            if raw:
                return resp.status, dict(resp.headers), payload
            return json.loads(payload.decode() or "{}")
    except urllib.error.HTTPError as e:
        payload = e.read()
        if raw:
            return e.code, dict(e.headers), payload
        try:
            return json.loads(payload.decode() or "{}")
        except Exception:
            return {"code": e.code, "message": payload.decode(errors="replace")}


def check(name, actual, expected_code, note=""):
    global passed, failed
    code = actual.get("code") if isinstance(actual, dict) else None
    if code == expected_code:
        passed += 1
        print("  PASS  %-52s code=%s %s" % (name, code, note))
    else:
        failed += 1
        msg = actual.get("message") if isinstance(actual, dict) else actual
        failures.append("%s: 期望 code=%s，实际 code=%s (%s)" % (name, expected_code, code, msg))
        print("  FAIL  %-52s 期望 %s 实际 %s  %s" % (name, expected_code, code, msg))


def register(username, role, tag):
    return call("POST", "/api/auth/register", {
        "username": username,
        "password": PWD,
        "email": "%s@example.com" % username,
        "phone": "139%08d" % (int(SUFFIX) % 100000000) if tag == "a" else "138%08d" % (int(SUFFIX) % 100000000),
        "role": role,
    })


def login(username, password=PWD):
    r = call("POST", "/api/auth/login", {"username": username, "password": password})
    if r.get("code") != 200:
        return None, r
    return r["data"]["token"], r


print("后端: " + BASE)
print("临时账号: %s / %s" % (STUDENT2, COMPANY2))
print()

# ---------------- 准备账号 ----------------
print("[准备] 注册临时账号")
r1 = register(STUDENT2, "STUDENT", "a")
if r1.get("code") != 200:
    print("  注册 student02 失败: %s" % r1)
    sys.exit(2)
r2 = register(COMPANY2, "COMPANY", "b")
if r2.get("code") != 200:
    print("  注册 company02 失败: %s" % r2)
    sys.exit(2)

tok_s1, _ = login("student01", SEED_PWD)
tok_s2, _ = login(STUDENT2)
tok_c1, _ = login("company01", SEED_PWD)
tok_c2, _ = login(COMPANY2)
for name, t in (("student01", tok_s1), ("student02", tok_s2), ("company01", tok_c1), ("company02", tok_c2)):
    if not t:
        print("  登录 %s 失败" % name)
        sys.exit(2)
print("  OK")

# student01 / student02 的档案 id
p1 = call("GET", "/api/student/profiles/me", token=tok_s1)
p2 = call("GET", "/api/student/profiles/me", token=tok_s2)
sid1 = p1["data"]["id"]
sid2 = p2["data"]["id"]
print("  student01 profileId=%s, student02 profileId=%s" % (sid1, sid2))

# company01 / company02 的 userId
c1 = call("GET", "/api/company/companies/mine", token=tok_c1)
c2 = call("GET", "/api/company/companies/mine", token=tok_c2)
uid_c1 = c1["data"]["userId"] if c1.get("data") else None
# company02 还没建企业资料，用它的登录用户 id
me_c2 = call("GET", "/api/auth/me", token=tok_c2)
uid_c2 = me_c2["data"]["userId"]
print("  company01 userId=%s, company02 userId=%s" % (uid_c1, uid_c2))
print()

# ---------------- A. 水平越权 ----------------
print("[A] 水平越权（应被拒）")

# A1: 企业改别家企业的资料
a1 = call("POST", "/api/company/companies/mine?userId=%s" % uid_c2,
          {"companyName": "被篡改的企业名"}, token=tok_c1)
check("A1 企业 A 用企业 B 的 userId 改资料", a1, 403)

# A2: 企业读别家企业的资料
a2 = call("GET", "/api/company/companies/mine?userId=%s" % uid_c2, token=tok_c1)
check("A2 企业 A 用企业 B 的 userId 读资料", a2, 403)

# A3: 学生建一份简历，另一个学生尝试删
res1 = call("POST", "/api/student/resumes",
            {"resumeName": "student01 的简历", "resumeType": "ONLINE", "targetPosition": "Java", "school": "南昌大学", "major": "软件工程", "educationLevel": "本科"}, token=tok_s1)
rid1 = res1["data"]["id"] if res1.get("data") else None
if rid1:
    a3 = call("DELETE", "/api/student/resumes/%s" % rid1, token=tok_s2)
    check("A3 学生 B 删学生 A 的简历", a3, 403)

    a4 = call("PUT", "/api/student/resumes/%s" % rid1,
            {"resumeName": "被篡改", "resumeType": "ONLINE", "targetPosition": "Java",
             "school": "南昌大学", "major": "软件工程"}, token=tok_s2)
    check("A4 学生 B 改学生 A 的简历", a4, 403)

    a5 = call("GET", "/api/student/resumes/%s" % rid1, token=tok_s2)
    check("A5 学生 B 读学生 A 的简历", a5, 403)
else:
    failed += 3
    failures.append("A3-A5: 无法创建测试简历 (%s)" % res1)

# A6: 学生 B 改学生 A 的技能
skill = call("POST", "/api/student/skills", {"skillName": "Java", "proficiency": "掌握"}, token=tok_s1)
skill_id = skill["data"]["id"] if skill.get("data") else None
if skill_id:
    a6 = call("PUT", "/api/student/skills/%s" % skill_id, {"skillName": "篡改"}, token=tok_s2)
    check("A6 学生 B 改学生 A 的技能", a6, 403)

    a7 = call("DELETE", "/api/student/skills/%s" % skill_id, token=tok_s2)
    check("A7 学生 B 删学生 A 的技能", a7, 403)
else:
    failed += 2
    failures.append("A6-A7: 无法创建测试技能 (%s)" % skill)

# A8: 学生 B 读学生 A 的资料
a8 = call("GET", "/api/student/profiles/%s" % sid1, token=tok_s2)
check("A8 学生 B 读学生 A 的个人资料", a8, 403)

print()

# ---------------- B. 正常请求仍然通过 ----------------
print("[B] 合法请求（应通过）")
b1 = call("GET", "/api/student/profiles/me", token=tok_s1)
check("B1 学生读自己的资料", b1, 200)
b2 = call("GET", "/api/student/resumes/%s" % rid1, token=tok_s1) if rid1 else {"code": -1}
check("B2 学生读自己的简历", b2, 200)
b3 = call("GET", "/api/student/skills/%s" % skill_id, token=tok_s1) if skill_id else {"code": -1}
check("B3 学生读自己的技能", b3, 200)
b4 = call("GET", "/api/company/companies/mine", token=tok_c1)
check("B4 企业读自己的资料（不带 userId 参数）", b4, 200)
b5 = call("GET", "/api/company/companies/mine?userId=%s" % uid_c1, token=tok_c1)
check("B5 企业读自己的资料（带正确的 userId）", b5, 200)
print()

# ---------------- C. 认证 ----------------
print("[C] 认证行为")
c_unknown = call("POST", "/api/auth/login", {"username": "no_such_user_xyz", "password": "Demo1234"})
c_wrongpwd = call("POST", "/api/auth/login", {"username": "student01", "password": "WrongPwd123"})
same = c_unknown.get("message") == c_wrongpwd.get("message")
check("C1 不存在的用户名与密码错误返回同一句提示", {"code": 200 if same else -1},
      200, "(%s / %s)" % (c_unknown.get("message"), c_wrongpwd.get("message")))

weak = register("weakpwd_" + SUFFIX, "STUDENT", "a") if False else call("POST", "/api/auth/register", {
    "username": "weakpwd_" + SUFFIX, "password": "1",
    "email": "weakpwd_%s@example.com" % SUFFIX, "phone": "137%08d" % (int(SUFFIX) % 100000000),
    "role": "STUDENT",
})
check("C2 弱密码注册被拒", weak, 400, "(%s)" % weak.get("message"))

# 连续失败 5 次后用第 6 次验证锁定
lock_user = "locktest_" + SUFFIX
register(lock_user, "STUDENT", "b")
for i in range(5):
    call("POST", "/api/auth/login", {"username": lock_user, "password": "WrongPwd123"})
locked = call("POST", "/api/auth/login", {"username": lock_user, "password": PWD})
msg = locked.get("message") or ""
check("C3 连续 5 次失败后触发临时锁定", {"code": 200 if "次数过多" in msg else -1},
      200, "(%s)" % msg)
print()

# ---------------- D. CORS ----------------
print("[D] CORS")
status, headers, _ = call("GET", "/api/jobs/published", raw=True,
                          headers={"Origin": "http://evil.example.com"})
acao = headers.get("Access-Control-Allow-Origin") or headers.get("access-control-allow-origin")
check("D1 恶意来源不被放行", {"code": 200 if not acao else -1}, 200,
      "(%s)" % (acao or "无 Access-Control-Allow-Origin"))
status2, headers2, _ = call("GET", "/api/jobs/published", raw=True,
                            headers={"Origin": "http://localhost:5173"})
acao2 = headers2.get("Access-Control-Allow-Origin") or headers2.get("access-control-allow-origin")
check("D2 前端来源正常放行", {"code": 200 if acao2 else -1}, 200, "(%s)" % (acao2 or "无"))

print()
print("=" * 70)
print("结果: %d 通过, %d 失败" % (passed, failed))
if failures:
    print()
    for f in failures:
        print("  - " + f)
sys.exit(0 if failed == 0 else 1)
