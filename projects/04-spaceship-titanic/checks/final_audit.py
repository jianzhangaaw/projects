"""终检：对两项作业全部交付物做独立复核。

原则：不复用被验方的结论，用独立通道重新计算。
- 指标：从 out/preds/*.npz 的原始预测重新计算，与 out/results.json 比对；
- 报告：从 PDF 文本层重新统计字数、章节、文献条数，与交付声明比对；
- 数据：重新计算 SHA256，与 checks/cross_source_manifest.json 比对；
- 源码包：重新打开 zip 逐条校验。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

# pypdf：优先使用已安装的版本；若未安装则回退到仓库内的本地副本（开发机上使用）
try:
    import pypdf  # noqa: F401
except ImportError:  # pragma: no cover
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".pdflib"))
from pypdf import PdfReader  # noqa: E402

WS = Path(__file__).resolve().parents[2]
LAB = WS / "spaceship-lab"
ML = WS / "ml-report"
fails, passes = [], []


def check(cond, msg):
    (passes if cond else fails).append(msg)
    print(("  PASS  " if cond else "  FAIL  ") + msg)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


print("=" * 70)
print("一、交付物存在性")
deliverables = {
    "作业A 报告 PDF": LAB / "【机器学习实践】大作业报告.pdf",
    "作业A 报告 docx": LAB / "【机器学习实践】大作业报告.docx",
    "作业A 源码包": LAB / "提交包" / "机器学习实践-大作业-源码包.zip",
    "作业B 报告 PDF": ML / "【机器学习】大作业报告.pdf",
    "作业B 报告 docx": ML / "【机器学习】大作业报告.docx",
    "作业B 文献清单": ML / "refs" / "references.json",
}
for name, p in deliverables.items():
    ok = p.exists() and p.stat().st_size > 10000
    check(ok, f"{name}: {p.name} {p.stat().st_size if p.exists() else 0} 字节")
    if ok:
        print(f"         SHA256 {sha256(p)[:32]}…")

print("=" * 70)
print("二、指标独立重算（从 npz 原始预测 vs results.json）")
res = json.loads((LAB / "out" / "results.json").read_text(encoding="utf-8"))
for m, v in res["models"].items():
    npz = LAB / "out" / "preds" / f"{m}__seed42.npz"
    if not npz.exists():
        check(False, f"{m} 的 seed42 预测文件缺失")
        continue
    d = np.load(npz, allow_pickle=True)
    oof, y = d["oof"], d["y"]
    acc = accuracy_score(y, (oof >= 0.5).astype(int))
    auc = roc_auc_score(y, oof)
    f1 = f1_score(y, (oof >= 0.5).astype(int))
    claimed = v["per_seed"]["42"]
    check(abs(acc - claimed["accuracy"]) < 1e-9,
          f"{m}: 重算准确率 {acc:.6f} == results.json {claimed['accuracy']:.6f}")
    check(abs(auc - claimed["roc_auc"]) < 1e-9,
          f"{m}: 重算 AUC {auc:.6f} == results.json {claimed['roc_auc']:.6f}")
    check(abs(f1 - claimed["f1"]) < 1e-9,
          f"{m}: 重算 F1 与记录一致（{f1:.6f}）")

print("=" * 70)
print("三、数据来源复核")
man = json.loads((LAB / "raw" / "cross_source_manifest.json").read_text(encoding="utf-8"))
files = man["files"]
# manifest 里记录的是两个 HuggingFace 源（HF1/HF2）；GitHub 的 A/B 两份由 check_data.py 下载。
# 这里对每个文件做三重独立比对：A 的实际哈希 vs HF1、HF2 的记录，以及 A vs B 的现场比对。
for f, kind in [("train.csv", "train"), ("test.csv", "test")]:
    pa, pb = LAB / "raw" / f"A-{f}", LAB / "raw" / f"B-{f}"
    ha, hb = sha256(pa), sha256(pb)
    check(ha == hb, f"{f}: GitHub 两个镜像 A/B 现场重算哈希一致（{ha[:16]}…）")
    for tag in ["HF1", "HF2"]:
        rec = files.get(f"{tag}-{kind}", {})
        check(rec.get("sha256") == ha,
              f"{f}: HuggingFace 源 {tag} 记录哈希与 A 一致"
              f"（{str(rec.get('sha256'))[:16]}…）")
    check(files.get(f"HF1-{kind}", {}).get("bytes") == pa.stat().st_size,
          f"{f}: 字节数一致（{pa.stat().st_size}）")
# sample_submission 不在 cross_source 的 manifest 里，用 A/B 现场比对
pa, pb = LAB / "raw" / "A-sample_submission.csv", LAB / "raw" / "B-sample_submission.csv"
check(pa.exists() and pb.exists() and sha256(pa) == sha256(pb),
      f"sample_submission.csv: A/B 现场重算哈希一致（{sha256(pa)[:16]}…）")

print("=" * 70)
print("四、作业A报告 PDF 复核")
pdf_a = PdfReader(str(LAB / "【机器学习实践】大作业报告.pdf"))
text_a = "\n".join((p.extract_text() or "") for p in pdf_a.pages)
print(f"  页数 {len(pdf_a.pages)}，汉字 {len(re.findall(chr(0x4e00) + '-' + chr(0x9fff), text_a)) if False else len(re.findall(r'[一-龥]', text_a))}")
for h in ["一、问题定义与实验设定", "二、算法选择与实现分析", "三、实验结果与对比分析", "四、总结与改进方向"]:
    check(h in text_a, f"章节存在：{h}")
# 数字一致性：全部模型的 accuracy 与 auc
for m, v in res["models"].items():
    for k in ["accuracy", "roc_auc"]:
        s = f"{v['agg'][k]['mean']:.4f}"
        check(s in text_a, f"{m} 的 {k} 均值 {s} 出现在报告中")
han_a = len(re.findall(r"[\u4e00-\u9fff]", text_a))
check(han_a >= 2000, f"作业A报告汉字数 {han_a} ≥ 2000")

print("=" * 70)
print("五、作业B报告 PDF 复核")
pdf_b = PdfReader(str(ML / "【机器学习】大作业报告.pdf"))
text_b = "\n".join((p.extract_text() or "") for p in pdf_b.pages)
han_b = len(re.findall(r"[\u4e00-\u9fff]", text_b))
check(han_b >= 2500, f"作业B报告汉字数 {han_b} ≥ 2500")
refs = json.loads((ML / "refs" / "references.json").read_text(encoding="utf-8"))
check(len(refs) >= 25, f"参考文献 {len(refs)} 条 ≥ 25")
foreign = [r for r in refs if re.search(r"[A-Za-z]", r.get("authors", ""))]
check(len(foreign) >= 15, f"外文文献 {len(foreign)} 条 ≥ 15")
for h in ["一、问题定义与研究背景", "二、发展脉络与算法分析", "三、研究瓶颈与未来展望", "四、参考文献"]:
    check(h in text_b, f"章节存在：{h}")
n_ref_in_pdf = len(re.findall(r"\[\d{1,2}\]\s+\S+", text_b))
check(n_ref_in_pdf >= 25, f"PDF 文本中可识别出 {n_ref_in_pdf} 条带编号的文献")
# 关键文献的实际落地
for kw in ["Nature", "637(8045)", "s41586-024-08328-6", "LightGBM", "ICML 2024"]:
    check(kw in text_b, f"PDF 含关键元数据：{kw}")

print("=" * 70)
print("六、源码包复核")
zp = LAB / "提交包" / "机器学习实践-大作业-源码包.zip"
with zipfile.ZipFile(zp) as z:
    bad = z.testzip()
    names = z.namelist()
    check(bad is None, f"zip 无损坏条目（testzip={bad}）")
    for key in ["README.md", "src/features.py", "src/run_experiment.py",
                "src/analyze_results.py", "checks/check_data.py",
                "out/results.json"]:
        check(key in names, f"含 {key}")
    check(sum(1 for n in names if n.endswith(".png")) >= 6, "含 ≥6 张图表")
    readme = z.read("README.md").decode("utf-8")
    check("py -m pip install" in readme, "README 注明依赖安装命令")
    check("py src\\run_experiment.py" in readme, "README 注明运行命令")

print("=" * 70)
print(f"通过 {len(passes)} 项，失败 {len(fails)} 项")
if fails:
    print("失败清单：")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("终检全部通过")
