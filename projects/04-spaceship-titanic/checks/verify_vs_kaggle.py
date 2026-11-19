"""比对 Kaggle 官方下载的数据与本实验使用的镜像数据。

用法：
1) 登录 Kaggle，在 https://www.kaggle.com/competitions/spaceship-titanic/data
   下载 spaceship-titanic.zip（或分别下载 train.csv / test.csv / sample_submission.csv）；
2) 把下载到的文件放进 spaceship-lab\\kaggle-official\\ 目录
   （放 zip 或放解压后的 csv 都行）；
3) 运行：py checks\\verify_vs_kaggle.py

脚本会做三重比对并输出结论到 out/kaggle_verification.json：
  ① 逐字节 SHA256 是否相同；
  ② 形状（行数×列数）与列名顺序是否相同；
  ③ 逐格语义比对（把 NaN 视作相等），排除换行符/引号等格式差异的干扰。

结论为「完全一致」时，报告里关于数据来源的表述才可以改成
「经 Kaggle 账号下载并核对」，否则应当保留现有的镜像来源说明。
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd

LAB = Path(__file__).resolve().parents[1]
KAGGLE_DIR = LAB / "kaggle-official"
RAW = LAB / "raw"
OUT = LAB / "out"
FILES = ["train.csv", "test.csv", "sample_submission.csv"]

fails = []


def check(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def locate_kaggle_files():
    """在 kaggle-official 目录里找 csv；若只有 zip 就解压出来。"""
    KAGGLE_DIR.mkdir(parents=True, exist_ok=True)
    found = {}
    for f in FILES:
        p = KAGGLE_DIR / f
        if p.exists():
            found[f] = p
    zips = list(KAGGLE_DIR.glob("*.zip"))
    if zips and len(found) < len(FILES):
        for z in zips:
            try:
                with zipfile.ZipFile(z) as zf:
                    zf.extractall(KAGGLE_DIR)
                print(f"  已解压 {z.name}")
            except Exception as e:  # noqa: BLE001
                print(f"  解压 {z.name} 失败：{e}")
        for f in FILES:
            p = KAGGLE_DIR / f
            if p.exists():
                found[f] = p
    return found


def main():
    if not KAGGLE_DIR.exists() or not any(KAGGLE_DIR.iterdir()):
        print(f"目录 {KAGGLE_DIR} 是空的。")
        print("请先登录 Kaggle 下载 spaceship-titanic.zip 并放到该目录，再运行本脚本。")
        sys.exit(2)

    kaggle = locate_kaggle_files()
    print(f"在 {KAGGLE_DIR} 找到：{sorted(kaggle)}\n")
    if not kaggle:
        print("没有找到任何 csv 或可解压的 zip。请确认下载的是 Spaceship Titanic 的数据文件。")
        sys.exit(2)

    result = {"compared": {}, "verdict": None, "kaggle_dir": str(KAGGLE_DIR)}

    for f in FILES:
        print(f"=== {f} ===")
        kp = kaggle.get(f)
        mp = RAW / f"A-{f}"
        if kp is None:
            print("  SKIP  未提供该文件的 Kaggle 版本")
            continue
        if not mp.exists():
            check(False, f"镜像版本缺失：{mp}")
            continue

        hk, hm = sha256(kp), sha256(mp)
        byte_same = hk == hm
        print(f"  Kaggle 版本：{kp.stat().st_size} 字节  SHA256 {hk}")
        print(f"  镜像版本  ：{mp.stat().st_size} 字节  SHA256 {hm}")

        dk, dm = pd.read_csv(kp), pd.read_csv(mp)
        shape_same = dk.shape == dm.shape
        cols_same = list(dk.columns) == list(dm.columns)
        cells_same = None
        if shape_same and cols_same:
            cells_same = bool((dk.fillna("\x00") == dm.fillna("\x00")).all().all())

        check(byte_same, f"{f}: 逐字节完全相同")
        check(shape_same, f"{f}: 形状相同（Kaggle {dk.shape} vs 镜像 {dm.shape}）")
        check(cols_same, f"{f}: 列名与顺序相同")
        if cells_same is not None:
            check(cells_same, f"{f}: 逐格语义相同")

        result["compared"][f] = {
            "kaggle_sha256": hk, "mirror_sha256": hm,
            "byte_identical": byte_same, "shape": [list(dk.shape), list(dm.shape)],
            "columns_identical": cols_same, "cells_identical": cells_same,
            "kaggle_bytes": kp.stat().st_size,
        }
        print()

    if result["compared"]:
        all_same = all(v["byte_identical"] for v in result["compared"].values())
        result["verdict"] = "identical" if all_same else "differs"
        OUT.mkdir(exist_ok=True)
        (OUT / "kaggle_verification.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"结论：{result['verdict']}（已写出 out/kaggle_verification.json）")
        if all_same:
            print("\n所有文件与 Kaggle 官方下载逐字节一致。")
            print("此时报告里关于数据来源的表述可以改为：")
            print("  「数据经 Kaggle 账号从竞赛页面下载，并与四个公开镜像逐字节核对一致」——")
            print("  这比原来的镜像说明更强，因为它包含与源站的直接比对。")
        else:
            print("\n存在差异。报告里应当保留现有的镜像来源说明，并把差异如实写入。")

    print()
    if fails:
        print(f"未通过 {len(fails)} 项：")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("比对全部通过")


if __name__ == "__main__":
    main()
