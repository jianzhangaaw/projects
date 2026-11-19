"""评估概率集成能否优于单模型，为 submission.csv 的选择提供依据。

只用已有的 OOF 预测（不额外训练），比较：
- 各单模型
- 全部模型等权平均
- 去掉最弱模型后的等权平均
- 最优两个模型的平均
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score

LAB = Path(__file__).resolve().parents[1]
SEED = 42

preds, y = {}, None
for f in sorted((LAB / "out" / "preds").glob(f"*__seed{SEED}.npz")):
    m = f.stem.split("__")[0]
    d = np.load(f, allow_pickle=True)
    preds[m] = d["oof"]
    y = d["y"]

print(f"参与评估的模型：{sorted(preds)}\n")
rows = []
for m, p in preds.items():
    rows.append((m, accuracy_score(y, (p >= 0.5).astype(int)), roc_auc_score(y, p)))
for m, a, auc in sorted(rows, key=lambda x: -x[1]):
    print(f"  单模型 {m:10s} acc={a:.4f} auc={auc:.4f}")

print()
models = sorted(preds)
best_combo, best_acc = None, -1
for k in range(2, len(models) + 1):
    for combo in combinations(models, k):
        p = np.mean([preds[m] for m in combo], axis=0)
        a = accuracy_score(y, (p >= 0.5).astype(int))
        auc = roc_auc_score(y, p)
        if a > best_acc:
            best_acc, best_combo = a, combo
        if k == len(models) or k <= 3:
            print(f"  集成 {'+'.join(combo):45s} acc={a:.4f} auc={auc:.4f}")

print(f"\n最优组合：{'+'.join(best_combo)}  acc={best_acc:.4f}")
best_single = max(rows, key=lambda x: x[1])
print(f"最优单模型：{best_single[0]}  acc={best_single[1]:.4f}")
print(f"集成增益：{(best_acc - best_single[1]) * 100:+.2f} 个百分点")

json.dump({
    "single": {m: {"acc": a, "auc": auc} for m, a, auc in rows},
    "best_combo": list(best_combo),
    "best_combo_acc": float(best_acc),
    "best_single": best_single[0],
    "best_single_acc": float(best_single[1]),
    "gain_pp": float((best_acc - best_single[1]) * 100),
}, open(LAB / "out" / "ensemble_check.json", "w", encoding="utf-8"),
    indent=2, ensure_ascii=False)
print("\n写出 out/ensemble_check.json")
