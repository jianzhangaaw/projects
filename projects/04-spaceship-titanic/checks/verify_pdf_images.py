"""确认两份报告 PDF 里的图片真的被渲染出来（页面级 XObject 检查）。"""
from __future__ import annotations

import sys
from pathlib import Path

# pypdf：优先使用已安装的版本；若未安装则回退到仓库内的本地副本（开发机上使用）
try:
    import pypdf  # noqa: F401
except ImportError:  # pragma: no cover
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".pdflib"))
from pypdf import PdfReader  # noqa: E402

WS = Path(__file__).resolve().parents[2]
fails = []

# 期望：作业A 报告含 7 张统计图；作业B 报告是纯文字综述，不含图，属正常。
EXPECT = {"作业A": 6, "作业B": 0}

for name, pdf in [("作业A", WS / "spaceship-lab" / "【机器学习实践】大作业报告.pdf"),
                  ("作业B", WS / "ml-report" / "【机器学习】大作业报告.pdf")]:
    r = PdfReader(str(pdf))
    unique = {}          # id(对象) -> 尺寸，用于跨页去重
    for i, page in enumerate(r.pages, 1):
        res = page.get("/Resources")
        xo = res.get("/XObject") if res else None
        if not xo:
            continue
        xo = xo.get_object()
        for k in xo:
            o = xo[k].get_object()
            if o.get("/Subtype") == "/Image":
                w, h = int(o.get("/Width") or 0), int(o.get("/Height") or 0)
                unique[id(o)] = (w, h, i)
    n = len(unique)
    print(f"{name}：{len(r.pages)} 页，去重后内嵌图片 {n} 张")
    for oid, (w, h, first) in sorted(unique.items(), key=lambda x: x[1][2]):
        print(f"    {w}x{h}（首次出现于第 {first} 页）")
        if w < 100 or h < 100:
            fails.append(f"{name} 中有过小的图片 {w}x{h}")
    if n < EXPECT[name]:
        fails.append(f"{name} 期望至少 {EXPECT[name]} 张图，实际 {n} 张")
    elif EXPECT[name] == 0:
        print(f"    （作业B 为纯文字综述，不插图，符合预期）")

print()
if fails:
    print("失败：")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("两份 PDF 的图片均已实际嵌入渲染")
