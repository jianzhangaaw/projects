"""样本效率曲线：固定验证集，训练集规模从 100 递增到 4000，比较五类算法。

这是 TabPFN 论文（Nature 2025）核心主张在本数据上的可证伪检验：
「在小样本区间，基于先验的表格基础模型优于需要从零拟合的梯度提升树」。
如果在本数据上不成立，就如实记录。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("TABPFN_ALLOW_CPU_LARGE_DATASET", "1")
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import numpy as np  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.metrics import accuracy_score, roc_auc_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: E402

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB / "src"))
from features import CAT_COLS, get_xy  # noqa: E402
from models import MODEL_SPECS  # noqa: E402

SIZES = [100, 250, 500, 1000, 2000, 4000]
MODELS = ["logreg", "knn", "lightgbm", "mlp", "tabpfn"]


def build_params():
    tp = LAB / "out" / "tuning.json"
    if tp.exists():
        t = json.loads(tp.read_text(encoding="utf-8"))
        return {k: (v.get("best_params") or {}) for k, v in t.items()}
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="42")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--sizes", default=",".join(str(s) for s in SIZES))
    args = ap.parse_args()

    X, y, _, _ = get_xy(LAB / "raw" / "A-train.csv", LAB / "raw" / "A-test.csv")
    num_cols = [c for c in X.columns if c not in CAT_COLS]
    pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num_cols),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), CAT_COLS),
    ])

    # 固定验证集：分层留出 2174 行（与 5 折中单折规模相当），所有规模档共用
    Xtr_all, Xva, ytr_all, yva = train_test_split(
        X, y, test_size=2174, stratify=y, random_state=42)
    Xva_e = pre.fit_transform(Xva).astype(np.float32)
    print(f"固定验证集 {Xva_e.shape}，候选训练池 {len(Xtr_all)}", flush=True)

    params = build_params()
    out_path = LAB / "out" / "scaling.json"
    acc = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {
        "sizes": [], "data": {}, "labels": {m: MODEL_SPECS[m]["label"] for m in MODELS},
        "models": MODELS, "n_valid": int(len(yva)), "valid_seed": 42,
    }
    acc["data"] = {str(k): v for k, v in acc.get("data", {}).items()}

    for n in [int(s) for s in args.sizes.split(",")]:
        for seed in [int(s) for s in args.seeds.split(",")]:
            rng = np.random.default_rng(seed)
            # 分层抽取 n 个训练样本
            idx = []
            for cls in (0, 1):
                pool = np.where(ytr_all == cls)[0]
                k = int(round(n * len(pool) / len(ytr_all)))
                idx.extend(rng.choice(pool, size=min(k, len(pool)), replace=False).tolist())
            idx = np.array(sorted(idx))
            Xs_raw, ys = Xtr_all.iloc[idx], ytr_all[idx]
            Xs_e = pre.transform(Xs_raw).astype(np.float32)

            for m in args.models.split(","):
                m = m.strip()
                key = str(n)
                acc["data"].setdefault(key, {}).setdefault(m, {})
                if str(seed) in acc["data"][key][m]:
                    print(f"  [skip] n={n} seed={seed} {m}", flush=True)
                    continue
                t0 = time.time()
                try:
                    est = MODEL_SPECS[m]["factory"](rs=seed)(**{k: v for k, v in params.get(m, {}).items()
                                                              if k in MODEL_SPECS[m]["factory"](
                                                                  rs=seed).get_params()})
                except Exception:
                    est = MODEL_SPECS[m]["factory"](rs=seed)
                # 统一用网格里选定的参数重设
                try:
                    est.set_params(**params.get(m, {}))
                except Exception:  # noqa: BLE001
                    pass
                try:
                    est.fit(Xs_e, ys)
                    proba = est.predict_proba(Xva_e)[:, 1]
                    a = float(accuracy_score(yva, (proba >= 0.5).astype(int)))
                    auc = float(roc_auc_score(yva, proba))
                    dt = time.time() - t0
                    acc["data"][key][m][str(seed)] = {
                        "accuracy": a, "auc": auc, "seconds": round(dt, 1), "n_train": int(len(idx))}
                    print(f"  n={len(idx):5d} seed={seed} {m:9s} acc={a:.4f} auc={auc:.4f} "
                          f"({dt:.1f}s)", flush=True)
                except Exception as e:  # noqa: BLE001
                    acc["data"][key][m][str(seed)] = {"error": f"{type(e).__name__}: {e}"}
                    print(f"  n={n} seed={seed} {m}: 失败 {type(e).__name__}: {e}", flush=True)
                acc["sizes"] = sorted({int(k) for k in acc["data"]})
                out_path.write_text(json.dumps(acc, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n写出", out_path)
    for n in sorted(acc["data"], key=lambda x: int(x)):
        row = []
        for m in acc["models"]:
            cell = acc["data"][n].get(m, {})
            vals = [v["accuracy"] for v in cell.values() if "accuracy" in v]
            row.append(f"{m}={np.mean(vals):.4f}" if vals else f"{m}=--")
        print(f"n={n:>5}: " + "  ".join(row))


if __name__ == "__main__":
    main()
