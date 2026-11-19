"""从 HuggingFace 镜像拉取第三方副本，与 GitHub 副本做交叉核对（第三条独立管道）。"""
import hashlib
import io
import json
import urllib.request
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "raw"
HF = "https://hf-mirror.com/datasets"
UA = {"User-Agent": "dsh-probe/1.0"}

SOURCES = [
    ("HF1", f"{HF}/Hugo0133/Spaceship-Titanic/resolve/main/train.csv", "train"),
    ("HF1", f"{HF}/Hugo0133/Spaceship-Titanic/resolve/main/test.csv", "test"),
    ("HF2", f"{HF}/StevenSch12/spaceship-titanic-train/resolve/main/train.csv", "train"),
    ("HF2", f"{HF}/StevenSch12/spaceship-titanic-test/resolve/main/test.csv", "test"),
]


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


manifest = {}
for tag, url, kind in SOURCES:
    dst = RAW / f"{tag}-{kind}.csv"
    if not dst.exists():
        data = fetch(url)
        dst.write_bytes(data)
    data = dst.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    manifest[f"{tag}-{kind}"] = {"bytes": len(data), "sha256": h}
    print(f"{tag}-{kind}: {len(data)} bytes  sha256={h[:16]}…")

print("=" * 72)
print("字节级比对（GitHub 镜像 A 为基准）")
for tag, kind in [("HF1", "train"), ("HF2", "train"), ("HF1", "test"), ("HF2", "test")]:
    a = (RAW / f"A-{kind}.csv").read_bytes()
    b = (RAW / f"{tag}-{kind}.csv").read_bytes()
    same = hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest()
    print(f"  byte-identical  A-{kind} vs {tag}-{kind}: {same}")

print("=" * 72)
print("语义级逐行比对（忽略列顺序与格式差异）")
report = {}
for kind in ["train", "test"]:
    base = pd.read_csv(RAW / f"A-{kind}.csv")
    report[kind] = {}
    for tag in ["B", "HF1", "HF2"]:
        other = pd.read_csv(RAW / f"{tag}-{kind}.csv")
        cols = [c for c in base.columns if c in other.columns]
        same_shape = base.shape == other.shape
        same_cols = list(base.columns) == list(other.columns)
        eq = base[cols].equals(other[cols].astype(base[cols].dtypes.to_dict()))
        # 逐格比对（NaN 视作相等）
        cell = (base[cols].fillna("\x00") == other[cols].fillna("\x00")).all().all()
        report[kind][tag] = {
            "shape": [list(base.shape), list(other.shape)],
            "same_shape": bool(same_shape),
            "same_column_order": bool(same_cols),
            "frame_equals": bool(eq),
            "all_cells_equal_ignoring_order": bool(cell),
            "shared_columns": len(cols),
        }
        print(f"  {kind}: A vs {tag}  同形状={same_shape} 同列序={same_cols} "
              f"逐格相等={cell} 共享列={len(cols)}")

(RAW / "cross_source_manifest.json").write_text(
    json.dumps({"files": manifest, "semantic": report}, indent=2, ensure_ascii=False),
    encoding="utf-8")
print("写出 raw/cross_source_manifest.json")
