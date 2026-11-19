"""超参数调优：在训练集上做内层 3 折 CV 的小网格搜索。

与主实验分开，目的有三：
1. 成本可控——调参只用 1 个种子的内层 CV，主实验再跑 5 折 × 3 种子；
2. 报告里能给出真实的"调优过程"（每个候选的 CV 分数），而不是事后编一组超参；
3. 避免把验证折信息带进调参（内层 CV 只在训练折内做）。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import CAT_COLS, get_xy  # noqa: E402
from models import MODEL_SPECS  # noqa: E402

from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: E402

LAB = Path(__file__).resolve().parents[1]


def build_preprocessor(num_cols):
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), num_cols),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore",
                                               sparse_output=False))]), CAT_COLS),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="logreg,knn,lightgbm,mlp")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--inner-folds", type=int, default=3)
    args = ap.parse_args()

    X, y, Xte, _ = get_xy(LAB / "raw" / "A-train.csv", LAB / "raw" / "A-test.csv")
    num_cols = [c for c in X.columns if c not in CAT_COLS]

    out_path = LAB / "out" / "tuning.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}

    inner = StratifiedKFold(n_splits=args.inner_folds, shuffle=True, random_state=args.seed)

    for name in args.models.split(","):
        name = name.strip()
        if not name:
            continue
        spec = MODEL_SPECS[name]
        grid = spec["grid"]
        n_cand = int(np.prod([len(v) for v in grid.values()])) if grid else 1
        print(f"\n=== {name} ({spec['label']}) 候选组合 {n_cand} × {args.inner_folds} 折 ===",
              flush=True)
        t0 = time.time()
        pipe = Pipeline([("pre", build_preprocessor(num_cols)),
                         ("clf", spec["factory"](rs=args.seed))])
        gs = GridSearchCV(pipe, grid, cv=inner, scoring="accuracy", n_jobs=1,
                          refit=False, verbose=0, return_train_score=False)
        gs.fit(X, y)
        dt = time.time() - t0

        order = np.argsort(gs.cv_results_["mean_test_score"])[::-1]
        table = []
        for i in order:
            table.append({
                "params": {k.replace("clf__", ""): (list(v) if isinstance(v, tuple) else v)
                           for k, v in gs.cv_results_["params"][i].items()},
                "mean_cv_acc": round(float(gs.cv_results_["mean_test_score"][i]), 5),
                "std_cv_acc": round(float(gs.cv_results_["std_test_score"][i]), 5),
            })
        best = table[0]
        print(f"  最优：{best['params']}  内层 CV 准确率 {best['mean_cv_acc']:.4f} "
              f"± {best['std_cv_acc']:.4f}（{dt:.1f}s，{n_cand} 组候选）", flush=True)
        for row in table[:5]:
            print(f"    {row['mean_cv_acc']:.4f}  {row['params']}", flush=True)

        existing[name] = {
            "label": spec["label"],
            "grid": {k: [list(v) if isinstance(v, tuple) else v for v in vals]
                     for k, vals in grid.items()},
            "n_candidates": n_cand,
            "inner_folds": args.inner_folds,
            "seed": args.seed,
            "seconds": round(dt, 1),
            "best_params": best["params"],
            "best_mean_cv_acc": best["mean_cv_acc"],
            "best_std_cv_acc": best["std_cv_acc"],
            "all_results": table,
        }
        out_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  已写入 {out_path}", flush=True)

    print("\n完成，写出", out_path)


if __name__ == "__main__":
    main()
