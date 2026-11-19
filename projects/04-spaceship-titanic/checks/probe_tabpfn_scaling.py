"""TabPFN v2 在 CPU 上的规模-耗时-精度曲线探测。

背景：tabpfn 9.0.0 默认禁止在 CPU 上使用超过 1000 个训练样本（RuntimeError）。
TabPFN v2 论文的设计场景是 ≤10000 样本 / ≤500 特征，本数据集 8693×28 正落在该范围内，
因此需要显式放开限制，并实测耗时以决定实验协议。
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TABPFN_ALLOW_CPU_LARGE_DATASET"] = "1"

import numpy as np  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.preprocessing import StandardScaler, OneHotEncoder  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from features import CAT_COLS, get_xy  # noqa: E402
from tabpfn import TabPFNClassifier  # noqa: E402

LAB = Path(__file__).resolve().parents[1]
Xtr, y, Xte, _ = get_xy(LAB / "raw" / "A-train.csv", LAB / "raw" / "A-test.csv")

num_cols = [c for c in Xtr.columns if c not in CAT_COLS]
pre = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num_cols),
    ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                      ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), CAT_COLS),
])

Xa, Xb, ya, yb = train_test_split(Xtr, y, test_size=0.25, stratify=y, random_state=42)
Xa_e = pre.fit_transform(Xa).astype(np.float32)
Xb_e = pre.transform(Xb).astype(np.float32)
print(f"编码后：train={Xa_e.shape} valid={Xb_e.shape}", flush=True)

rows = []
MODEL = "tabpfn-v2-classifier-v2_default.ckpt"

for n, n_est in [(500, 8), (1000, 8), (2000, 8)]:
    # 分层取 n 个训练样本
    idx = np.random.default_rng(0).permutation(len(ya))[:n]
    Xs, ys = Xa_e[idx], ya[idx]
    t = time.time()
    clf = TabPFNClassifier(model_path=MODEL, device="cpu", n_estimators=n_est, random_state=0)
    clf.fit(Xs, ys)
    t_fit = time.time() - t
    t = time.time()
    pred = clf.predict(Xb_e)
    t_pred = time.time() - t
    acc = float((pred == yb).mean())
    t = time.time()
    proba = clf.predict_proba(Xb_e)
    t_proba = time.time() - t
    from sklearn.metrics import roc_auc_score
    auc = float(roc_auc_score(yb, proba[:, 1]))
    rows.append({"n_train": n, "n_estimators": n_est, "fit_s": round(t_fit, 1),
                 "predict_s": round(t_pred, 1), "predict_proba_s": round(t_proba, 1),
                 "acc": round(acc, 4), "auc": round(auc, 4), "n_valid": int(len(yb))})
    print(f"n={n:5d} est={n_est}: fit={t_fit:6.1f}s predict={t_pred:6.1f}s proba={t_proba:6.1f}s "
          f"acc={acc:.4f} auc={auc:.4f}", flush=True)

# 外推全量（6519 训练样本 / 2174 验证）的粗略耗时
probe = LAB / "out" / "tabpfn_scaling.json"
probe.parent.mkdir(exist_ok=True)
probe.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print("写出 out/tabpfn_scaling.json", flush=True)

if len(rows) >= 2:
    r0, r1 = rows[-2], rows[-1]
    scale = r1["n_train"] / r0["n_train"]
    ratio = max(r1["predict_s"], 1e-6) / max(r0["predict_s"], 1e-6)
    print(f"predict 耗时随样本数从 {r0['n_train']}→{r1['n_train']}（×{scale:g}）变化 ×{ratio:.1f}", flush=True)
