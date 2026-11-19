"""打包作业A的源码提交包（zip），并在打包后做正向校验。

任务书要求：可运行源代码压缩包，含完整代码与简明的 README（注明依赖环境与运行命令）。
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
DST = LAB / "提交包" / "机器学习实践-大作业-源码包.zip"
DST.parent.mkdir(parents=True, exist_ok=True)

INCLUDE_DIRS = {
    "src": ["*.py"],
    "checks": ["*.py", "*.md"],
    # 原始数据随包提供，让「可运行」名副其实（四个独立镜像已逐字节核对一致，
    # 这里只放 A 系列，即脚本默认读取的文件名）
    "raw": ["A-*.csv", "*.json"],
}
INCLUDE_FILES = ["README.md"]
INCLUDE_OUT = ["results.json", "tuning.json", "scaling.json", "tabpfn_scaling.json",
               "fig_metrics.png", "fig_roc.png", "fig_confusion.png",
               "fig_calibration.png", "fig_importance.png", "fig_error.png",
               "fig_scaling.png", "submission.csv"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    added = []
    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for d, pats in INCLUDE_DIRS.items():
            base = LAB / d
            if not base.exists():
                continue
            for pat in pats:
                for f in sorted(base.glob(pat)):
                    if f.is_file():
                        z.write(f, f"{d}/{f.name}")
                        added.append(f"{d}/{f.name}")
        # checks/evidence 下的证据文件
        ev = LAB / "checks" / "evidence"
        if ev.exists():
            for f in sorted(ev.glob("*.md")):
                z.write(f, f"checks/evidence/{f.name}")
                added.append(f"checks/evidence/{f.name}")
        for f in INCLUDE_FILES:
            p = LAB / f
            if p.exists():
                z.write(p, f)
                added.append(f)
        for f in INCLUDE_OUT:
            p = LAB / "out" / f
            if p.exists():
                z.write(p, f"out/{f}")
                added.append(f"out/{f}")
        # 数据来源说明（数据本体不入包，说明文件入包）
        note = LAB / "提交包" / "数据说明.md"
        note.write_text(
            "# 数据说明\n\n"
            "本包不含原始数据文件（train.csv/test.csv 合计约 1.2 MB，另有公开来源）。\n\n"
            "数据来源：Kaggle 竞赛 Spaceship Titanic。竞赛页面下载需登录账号，本实验经公开镜像获取。\n\n"
            "所用文件的 SHA256（四个独立副本逐字节一致）：\n\n"
            "- train.csv（8693 行 × 14 列，805421 字节）：\n"
            "  `17336d553f49ebdf6ecb266d2b5d3746e5dd308445f7c7864141c4f28d2a88d0`\n"
            "- test.csv（4277 行 × 13 列，372487 字节）：\n"
            "  `3c02b0703423d27d51a657a111b15a37b8d03b3c1de325e3a1e6b26f6572fc88`\n"
            "- sample_submission.csv（4277 行，59902 字节）：\n"
            "  `c77c0a5ed1f3d2728d6add6079266a543d12755aebaf00f230ff1966b364ebed`\n\n"
            "校验脚本：`checks/check_data.py`（22 项正向断言）、`checks/cross_source.py`（多源比对）。\n"
            "竞赛官方数据说明的存档见 `checks/evidence/`。\n",
            encoding="utf-8")
        z.write(note, "提交包/数据说明.md")
        added.append("提交包/数据说明.md")

    # 正向校验：重新打开 zip，确认条目数与哈希
    with zipfile.ZipFile(DST) as z:
        bad = z.testzip()
        names = z.namelist()
        print(f"压缩包：{DST}")
        print(f"  条目数 {len(names)}，大小 {DST.stat().st_size} 字节，SHA256 {sha256(DST)[:16]}…")
        print(f"  testzip() -> {bad if bad else 'OK（无损坏条目）'}")
        for key in ["README.md", "src/features.py", "src/run_experiment.py",
                    "src/analyze_results.py", "checks/check_data.py",
                    "out/results.json", "out/submission.csv",
                    "提交包/数据说明.md"]:
            assert key in names, f"压缩包缺少 {key}"
            print(f"  含 {key}")
        pngs = [n for n in names if n.endswith(".png")]
        print(f"  图表 {len(pngs)} 张：{sorted(pngs)}")
        assert len(names) >= 25, f"条目数过少：{len(names)}"
    print("打包校验通过")


if __name__ == "__main__":
    main()
