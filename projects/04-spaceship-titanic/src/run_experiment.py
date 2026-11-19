"""主实验：分层 5 折交叉验证 × 多个随机种子，五类算法统一评测。

特性：
- 每个 (模型, 种子) 的组合单独落盘（out/preds/*.npz + out/cv/*.json），中断后可续跑；
- 预处理（中位数填补、标准化、独热）全部在 Pipeline 内，只在训练折 fit；
- 超参数来自 out/tuning.json（tune.py 的产物），未调参的模型用默认配置。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, brier_score_loss,
                             confusion_matrix, f1_score, precision_score, recall_score,
                             roc_auc_score)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import CAT_COLS, get_xy  # noqa: E402
from models import MODEL_SPECS  # noqa: E402

LAB = Path(__file__).resolve().parents[1]
OUT = LAB / "out"
PRED_DIR = OUT / "preds"
CV_DIR = OUT / "cv"
N_FOLDS = 5


def build_preprocessor(num_cols):
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), num_cols),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore",
                                               sparse_output=False))]), CAT_COLS),
    ])


def apply_params(pipe, params: dict):
    """把 tune.py 得到的 {'C': 1.0} 形式写回 Pipeline 的 clf__ 前缀参数。"""
    if not params:
        return pipe
    return pipe.set_params(**{f"clf__{k}" if not k.startswith("clf__") else k: v
                              for k, v in params.items()})


def compute_metrics(y_true, proba, fold_ids=None):
    pred = (proba >= 0.5).astype(int)
    m = {
        "accuracy": float(accuracy_score(y_true, pred)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "f1": float(f1_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred)),
        "recall": float(recall_score(y_true, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, pred)),
        "brier": float(brier_score_loss(y_true, proba)),
        "confusion_matrix": confusion_matrix(y_true, pred).tolist(),
        "n": int(len(y_true)),
    }
    if fold_ids is not None:
        per_fold = []
        for k in sorted(set(fold_ids.tolist())):
            sel = fold_ids == k
            pk = (proba[sel] >= 0.5).astype(int)
            per_fold.append({
                "fold": int(k),
                "n": int(sel.sum()),
                "accuracy": float(accuracy_score(y_true[sel], pk)),
                "roc_auc": float(roc_auc_score(y_true[sel], proba[sel])),
                "f1": float(f1_score(y_true[sel], pk)),
            })
        m["per_fold"] = per_fold
        accs = [f["accuracy"] for f in per_fold]
        m["fold_acc_mean"] = float(np.mean(accs))
        m["fold_acc_std"] = float(np.std(accs, ddof=1))
    return m


def run_one(name, seed, X, y, params, save=True):
    pred_path = PRED_DIR / f"{name}__seed{seed}.npz"
    if pred_path.exists():
        d = np.load(pred_path, allow_pickle=True)
        print(f"  [skip] {name} seed={seed} 已有结果", flush=True)
        return json.loads(str(d["meta"]))

    spec = MODEL_SPECS[name]
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    oof = np.zeros(len(y), dtype=float)
    fold_ids = np.zeros(len(y), dtype=int)
    num_cols = [c for c in X.columns if c not in CAT_COLS]

    t0 = time.time()
    fold_time = []
    for k, (tr, va) in enumerate(skf.split(X, y)):
        tf = time.time()
        pipe = Pipeline([("pre", build_preprocessor(num_cols)),
                         ("clf", spec["factory"](rs=seed))])
        pipe = apply_params(pipe, params)
        pipe.fit(X.iloc[tr], y[tr])
        oof[va] = pipe.predict_proba(X.iloc[va])[:, 1]
        fold_ids[va] = k
        dt = time.time() - tf
        fold_time.append(round(dt, 1))
        acc = float(accuracy_score(y[va], (oof[va] >= 0.5).astype(int)))
        print(f"  fold {k}: {dt:7.1f}s  acc={acc:.4f}", flush=True)
    total = time.time() - t0

    metrics = compute_metrics(y, oof, fold_ids)
    meta = {
        "model": name,
        "label": spec["label"],
        "seed": seed,
        "params": params,
        "seconds": round(total, 1),
        "fold_seconds": fold_time,
        "metrics": metrics,
    }
    if save:
        PRED_DIR.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(pred_path, oof=oof, fold_ids=fold_ids, y=y,
                            meta=json.dumps(meta, ensure_ascii=False))
        (CV_DIR).mkdir(parents=True, exist_ok=True)
        (CV_DIR / f"{name}__seed{seed}.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  -> {name} seed={seed}: acc={metrics['accuracy']:.4f} "
          f"auc={metrics['roc_auc']:.4f} 用时 {total:.1f}s", flush=True)
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="logreg,knn,lightgbm,mlp,tabpfn")
    ap.add_argument("--seeds", default="42")
    ap.add_argument("--no-tuning", action="store_true",
                    help="忽略 out/tuning.json，用模型默认超参")
    args = ap.parse_args()

    X, y, Xte, test_ids = get_xy(LAB / "raw" / "A-train.csv", LAB / "raw" / "A-test.csv")
    tuning = {}
    tp = OUT / "tuning.json"
    if tp.exists() and not args.no_tuning:
        tuning = json.loads(tp.read_text(encoding="utf-8"))
        print("已载入调参结果:", {k: v["best_params"] for k, v in tuning.items()}, flush=True)

    seeds = [int(s) for s in args.seeds.split(",")]
    summary = {}
    for name in args.models.split(","):
        name = name.strip()
        if not name:
            continue
        params = {} if args.no_tuning else (tuning.get(name, {}).get("best_params") or {})
        for seed in seeds:
            print(f"\n=== {name} seed={seed} ===", flush=True)
            summary[f"{name}__seed{seed}"] = run_one(name, seed, X, y, params)

    OUT.mkdir(parents=True, exist_ok=True)
    sp = OUT / "cv_summary.json"
    merged = {}
    if sp.exists():
        merged = json.loads(sp.read_text(encoding="utf-8"))
    merged.update(summary)
    sp.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n写出", sp)


if __name__ == "__main__":
    main()
