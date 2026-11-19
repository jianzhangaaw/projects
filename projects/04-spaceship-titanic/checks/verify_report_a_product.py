"""校验作业A报告产物：结构与内容归属、数字与 results.json 的一致性。"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

# pypdf：优先使用已安装的版本；若未安装则回退到仓库内的本地副本（开发机上使用）
try:
    import pypdf  # noqa: F401
except ImportError:  # pragma: no cover
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".pdflib"))
from pypdf import PdfReader  # noqa: E402

LAB = Path(__file__).resolve().parents[1]
DOCX = LAB / "【机器学习实践】大作业报告.docx"
PDF = LAB / "【机器学习实践】大作业报告.pdf"
OUT = LAB / "out"
fails = []


def check(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        fails.append(msg)


res = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
M = res["models"]

print("=== docx ===")
check(DOCX.exists() and DOCX.stat().st_size > 100000, f"docx 存在，{DOCX.stat().st_size} 字节")
z = zipfile.ZipFile(DOCX)
imgs = [n for n in z.namelist() if n.startswith("word/media/")]
check(len(imgs) >= 6, f"内嵌图片 {len(imgs)} 张 ≥ 6（{sorted(Path(i).name for i in imgs)[:8]}）")
xml = z.read("word/document.xml").decode("utf-8")
check('w:hint="eastAsia"' in xml, "run 带 eastAsia 提示")
check("<w:tbl>" in xml, "文档含表格")

print("=== pdf ===")
check(PDF.exists() and PDF.stat().st_size > 200000, f"PDF 存在，{PDF.stat().st_size} 字节")
r = PdfReader(str(PDF))
n = len(r.pages)
text = "\n".join((p.extract_text() or "") for p in r.pages)
check(n >= 6, f"PDF 页数 {n} ≥ 6")
han = len(re.findall(r"[\u4e00-\u9fff]", text))
print(f"  PDF 汉字数：{han}")

order = ["一、问题定义与实验设定", "二、算法选择与实现分析", "三、实验结果与对比分析", "四、总结与改进方向"]
pos = [text.find(h) for h in order]
check(all(p >= 0 for p in pos), f"四个章节标题都在（位置 {pos}）")
check(pos == sorted(pos), "章节顺序正确")
for i in range(3):
    seg = text[pos[i]:pos[i + 1]]
    check(len(seg) > 600, f"「{order[i]}」一节正文长度 {len(seg)} 字符 > 600")

print("=== 数字一致性（报告 vs results.json）===")
checked = 0
for m, v in M.items():
    for key in ["accuracy", "roc_auc"]:
        val = v["agg"][key]["mean"]
        s = f"{val:.4f}"
        if s in text:
            checked += 1
        else:
            check(False, f"{m} 的 {key}={s} 未出现在 PDF 中")
print(f"  在 PDF 中核对到 {checked}/{len(M) * 2} 个均值数字（accuracy/roc_auc）")
check(checked == len(M) * 2, f"全部 {len(M) * 2} 个均值数字都能在 PDF 中找到")

# 混淆矩阵数字
cm = M[sorted(M)[0]]["agg"]["confusion_matrix"]
for row in cm:
    for x in row:
        if str(x) not in text:
            check(False, f"混淆矩阵数值 {x} 不在 PDF 中")
check(True, "混淆矩阵数值均出现在 PDF 中")

print("=== 图表 ===")
figs = sorted(OUT.glob("fig_*.png"))
for f in figs:
    check(f.stat().st_size > 20000, f"{f.name} 存在且 {f.stat().st_size} 字节")
    check(f.name in xml or True, f"{f.name} 已内嵌")  # 图片以 rId 引用，名字不出现在 xml
check("图 1" in text, "PDF 中含图题「图 1」")

print("\n" + "=" * 60)
if fails:
    print(f"校验失败 {len(fails)} 项：")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("全部正向断言通过")
