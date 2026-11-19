#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段二（数据一致性）的验证脚本。

覆盖：
  - 投递的重复约束（靠数据库唯一索引 + 捕获 DuplicateKeyException，不再是 500）
  - 投递状态机（PENDING -> PASSED/REJECTED，终态不可回退）
  - 撤回限制（只有 PENDING 能撤回）
  - 企业建岗位/企业资料时不能指定别人的 id、不能自封已发布
  - 审核的状态机与驳回原因必填
  - 审核通过后 review_reason 被清空
  - 审核产生的通知确实落库

用法：
    python scripts/check-consistency.py [base_url]

退出码 0 表示全部通过。
"""
import json
import sys
import time
import urllib.error
import urllib.request

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
SUFFIX = str(int(time.time()))[-6:]
PWD = "Demo1234"
SEED_PWD = "Demo@1234"

passed = 0
failed = 0
failures = []


def call(method, path, body=None, token=None):
    url = BASE + path
    data = None
    hdrs = {}
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    if token:
        hdrs["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        payload = e.read()
        try:
            return json.loads(payload.decode() or "{}")
        except Exception:
            return {"code": e.code, "message": payload.decode(errors="replace")}


def check(name, actual, expected_code, note=""):
    global passed, failed
    code = actual.get("code") if isinstance(actual, dict) else None
    if code == expected_code:
        passed += 1
        print("  PASS  %-56s code=%s %s" % (name, code, note))
    else:
        failed += 1
        msg = actual.get("message") if isinstance(actual, dict) else actual
        failures.append("%s: 期望 %s 实际 %s (%s)" % (name, expected_code, code, msg))
        print("  FAIL  %-56s 期望 %s 实际 %s  %s" % (name, expected_code, code, msg))


def register(username, role, phone_prefix):
    return call("POST", "/api/auth/register", {
        "username": username,
        "password": PWD,
        "email": "%s@example.com" % username,
        "phone": "%s%08d" % (phone_prefix, int(SUFFIX) % 100000000),
        "role": role,
    })


def login(username, password=PWD):
    r = call("POST", "/api/auth/login", {"username": username, "password": password})
    return (r["data"]["token"] if r.get("code") == 200 else None), r


print("后端: " + BASE)
S3 = "stu2_" + SUFFIX
C3 = "com2_" + SUFFIX
print("临时账号: %s / %s" % (S3, C3))
print()

# ---------------- 准备 ----------------
print("[准备]")
r = register(S3, "STUDENT", "136")
assert r.get("code") == 200, r
r = register(C3, "COMPANY", "135")
assert r.get("code") == 200, r
tok_s, _ = login(S3)
tok_c, _ = login(C3)
tok_admin, _ = login("admin", SEED_PWD)
assert tok_s and tok_c and tok_admin, "登录失败"
print("  账号就绪")

# 学生建一份简历（投递必须带 resumeId）
resume = call("POST", "/api/student/resumes", {
    "resumeName": "一致性测试简历",
    "resumeType": "ONLINE",
    "targetPosition": "Java",
    "school": "南昌大学",
    "major": "软件工程",
    "educationLevel": "本科",
}, token=tok_s)
assert resume.get("code") == 200, resume
rid = resume["data"]["id"]

# 企业建资料
comp = call("POST", "/api/company/companies", {
    "companyName": "一致性测试企业",
    "industry": "测试",
    "contactName": "测试联系人",
    "contactPhone": "13500000000",
    "reviewStatus": "APPROVED",   # 故意自封通过，应被忽略
    "userId": 999999,             # 故意指定别人，应被忽略
}, token=tok_c)
check("A1 建企业资料时忽略请求体里的 reviewStatus/userId", comp, 200)
cid = comp["data"]["id"] if comp.get("data") else None
if comp.get("data"):
    check("A2 建出来的企业是 PENDING 而不是 APPROVED",
          {"code": 200 if comp["data"].get("reviewStatus") == "PENDING" else -1}, 200,
          "(%s)" % comp["data"].get("reviewStatus"))
    check("A3 建出来的企业挂在当前账号下而不是请求体里的 userId",
          {"code": 200 if comp["data"].get("userId") != 999999 else -1}, 200,
          "(userId=%s)" % comp["data"].get("userId"))

# 管理员审核企业
rv = call("PATCH", "/api/admin/reviews/companies/%s/approve" % cid, token=tok_admin)
check("A4 管理员审核通过企业", rv, 200)
rv2 = call("PATCH", "/api/admin/reviews/companies/%s/approve" % cid, token=tok_admin)
check("A5 重复审核已通过的企业被拒", rv2, 400, "(%s)" % rv2.get("message"))

# 企业建岗位（故意指定 status=PUBLISHED 与别人的 companyId）
job = call("POST", "/api/jobs", {
    "jobName": "一致性测试岗位",
    "jobType": "全职",
    "city": "南昌",
    "salaryRange": "10-20K",
    "educationRequirement": "本科",
    "description": "测试用",
    "status": "PUBLISHED",
    "companyId": 999999,
}, token=tok_c)
check("B1 建岗位时忽略请求体里的 status/companyId", job, 200)
jid = job["data"]["id"] if job.get("data") else None
if job.get("data"):
    check("B2 新岗位是 DRAFT 而不是 PUBLISHED",
          {"code": 200 if job["data"].get("status") == "DRAFT" else -1}, 200,
          "(%s)" % job["data"].get("status"))
    check("B3 新岗位挂在当前企业下",
          {"code": 200 if job["data"].get("companyId") != 999999 else -1}, 200,
          "(companyId=%s)" % job["data"].get("companyId"))

# 提交审核
sub = call("PATCH", "/api/jobs/%s/status?status=PENDING" % jid, token=tok_c)
check("B4 企业提交岗位审核", sub, 200)
ap = call("PATCH", "/api/admin/reviews/jobs/%s/approve" % jid, token=tok_admin)
check("B5 管理员审核通过岗位", ap, 200)
ap2 = call("PATCH", "/api/admin/reviews/jobs/%s/approve" % jid, token=tok_admin)
check("B6 重复审核已发布岗位被拒", ap2, 400, "(%s)" % ap2.get("message"))
rej = call("PATCH", "/api/admin/reviews/jobs/%s/reject?reviewReason=test" % jid, token=tok_admin)
check("B7 驳回已发布岗位被拒（状态机）", rej, 400, "(%s)" % rej.get("message"))
print()

# ---------------- C. 投递 ----------------
print("[C] 投递")
app = call("POST", "/api/applications", {"jobId": jid, "resumeId": rid}, token=tok_s)
check("C1 学生投递已发布岗位", app, 200)
aid = app["data"]["id"] if app.get("data") else None

dup = call("POST", "/api/applications", {"jobId": jid, "resumeId": rid}, token=tok_s)
check("C2 重复投递返回 400 而不是 500", dup, 400, "(%s)" % dup.get("message"))

# 别人的简历
other = call("POST", "/api/applications", {"jobId": jid, "resumeId": 1}, token=tok_s)
check("C3 用别人的简历投递被拒", other, 403, "(%s)" % other.get("message"))
print()

# ---------------- D. 状态机 ----------------
print("[D] 投递状态机")
st1 = call("PATCH", "/api/applications/%s/status?status=PASSED" % aid, token=tok_c)
check("D1 企业把 PENDING 改成 PASSED", st1, 200)
st2 = call("PATCH", "/api/applications/%s/status?status=PENDING" % aid, token=tok_c)
check("D2 从 PASSED 改回 PENDING 被拒", st2, 400, "(%s)" % st2.get("message"))
st3 = call("PATCH", "/api/applications/%s/status?status=REJECTED" % aid, token=tok_c)
check("D3 从 PASSED 改成 REJECTED 被拒", st3, 400, "(%s)" % st3.get("message"))
st4 = call("PATCH", "/api/applications/%s/status?status=FOO" % aid, token=tok_c)
check("D4 非法状态值被拒", st4, 400, "(%s)" % st4.get("message"))
wd = call("DELETE", "/api/applications/%s" % aid, token=tok_s)
check("D5 已处理的投递不能撤回", wd, 400, "(%s)" % wd.get("message"))
print()

# ---------------- E. 通知 ----------------
print("[E] 通知")
notes = call("GET", "/api/notifications/mine", token=tok_s)
if notes.get("code") == 200:
    has = any("状态已更新" in (n.get("content") or "") for n in (notes.get("data") or []))
    check("E1 学生收到投递状态变更通知", {"code": 200 if has else -1}, 200)
else:
    check("E1 学生收到投递状态变更通知", notes, 200)
print()

# ---------------- F. 审核通过后 review_reason 清空 ----------------
print("[F] 审核字段")
# 建一个新岗位，先驳回（带原因），再重新提交并通过，最后检查 reason 是否残留
job2 = call("POST", "/api/jobs", {"jobName": "驳回再通过测试岗位", "jobType": "全职", "city": "南昌"}, token=tok_c)
jid2 = job2["data"]["id"]
call("PATCH", "/api/jobs/%s/status?status=PENDING" % jid2, token=tok_c)
rej2 = call("PATCH", "/api/admin/reviews/jobs/%s/reject?reviewReason=incomplete" % jid2, token=tok_admin)
check("F1 驳回岗位（带原因）", rej2, 200)
rej3 = call("PATCH", "/api/admin/reviews/jobs/%s/reject" % jid2, token=tok_admin)
check("F2 驳回时不带原因被拒", rej3, 400, "(%s)" % rej3.get("message"))
# 重新提交并通过
call("PATCH", "/api/jobs/%s/status?status=PENDING" % jid2, token=tok_c)
ok2 = call("PATCH", "/api/admin/reviews/jobs/%s/approve" % jid2, token=tok_admin)
check("F3 驳回后重新提交并通过", ok2, 200)
detail = call("GET", "/api/jobs/%s" % jid2, token=tok_admin)
if detail.get("code") == 200:
    reason = detail["data"].get("reviewReason")
    check("F4 通过后 reviewReason 被清空", {"code": 200 if reason is None else -1}, 200, "(reason=%r)" % reason)
else:
    check("F4 通过后 reviewReason 被清空", detail, 200, "(detail=%s)" % detail)

print()
print("=" * 70)
print("结果: %d 通过, %d 失败" % (passed, failed))
if failures:
    print()
    for f in failures:
        print("  - " + f)
sys.exit(0 if failed == 0 else 1)
