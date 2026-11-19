"""特征工程自检 + 各算法单折耗时探测（决定实验能否在合理时间内跑完）。"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from features import CAT_COLS, describe, get_xy  # noqa: E402

LAB = Path(__file__).resolve().parents[1]
RAW = LAB / "raw"

t0 = time.time()
Xtr, y, Xte, test_ids = get_xy(RAW / "A-train.csv", RAW / "A-test.csv")
print(f"特征构造完成 {time.time() - t0:.1f}s  X_train={Xtr.shape}  X_test={Xte.shape}  y={y.shape}")
print("列：", list(Xtr.columns))

d = describe(Xtr, Xte)
print("特征数（原始列）:", d["n_features_raw"])
print("数值列", len(d["numeric"]), "类别列", d["categorical"])
print("缺失（部分）:", json.dumps(dict(list(d["missing_train"].items())[:6]), ensure_ascii=False))

# ---- 断言 ----
assert Xtr.shape == (8693, d["n_features_raw"]), "训练矩阵形状异常"
assert Xte.shape == (4277, d["n_features_raw"]), "测试矩阵形状异常"
assert list(Xtr.columns) == list(Xte.columns), "列不一致"
assert set(np.unique(y)) == {0, 1}, "标签不是 0/1"
assert int(y.sum()) == 4378, "正类数量异常"
assert not Xtr.columns.duplicated().any(), "存在重复列名"
assert Xtr["GroupSize"].min() >= 1, "组大小异常"
assert (Xtr["GroupSize"] > 1).sum() > 0 and (Xtr["IsAlone"] == 1).sum() > 0, "组特征全为常量，疑似计算失败"
print("特征断言全部通过")

# ---- 单折耗时探测 ----
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.preprocessing import StandardScaler, OneHotEncoder  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402

num_cols = d["numeric"]
cat_cols = CAT_COLS


def make_pre():
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), num_cols),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), cat_cols),
    ])


Xa, Xb, ya, yb = train_test_split(Xtr, y, test_size=0.25, stratify=y, random_state=42)
print(f"\n单折探测：train={Xa.shape} valid={Xb.shape}")

# 特征维度（编码后）
pre = make_pre().fit(Xa)
n_encoded = pre.transform(Xa).shape[1]
print("编码后特征维度:", n_encoded)

results = {}

from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.neighbors import KNeighborsClassifier  # noqa: E402
import lightgbm as lgb  # noqa: E402

for name, clf in [
    ("logreg", LogisticRegression(max_iter=2000, C=1.0)),
    ("knn", KNeighborsClassifier(n_neighbors=25, n_jobs=-1)),
    ("lightgbm", lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31,
                                    verbose=-1, n_jobs=-1, random_state=42)),
]:
    t = time.time()
    pipe = Pipeline([("pre", make_pre()), ("clf", clf)])
    pipe.fit(Xa, ya)
    acc = float((pipe.predict(Xb) == yb).mean())
    dt = time.time() - t
    results[name] = {"seconds": round(dt, 2), "acc": round(acc, 4)}
    print(f"  {name:10s} {dt:7.2f}s  acc={acc:.4f}")

# ---- TabPFN 计时（分规模） ----
import os  # noqa: E402
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
from tabpfn import TabPFNClassifier  # noqa: E402

pre_full = make_pre().fit(Xa)
Xa_e = pre_full.transform(Xa).astype(np.float32)
Xb_e = pre_full.transform(Xb).astype(np.float32)

for n_sub, n_est in [(2000, 4), (8693, 4)]:
    n = min(n_sub, len(Xa_e))
    Xs, ys = Xa_e[:n], ya[:n]
    t = time.time()
    clf = TabPFNClassifier(model_path="tabpfn-v2-classifier-v2_default.ckpt",
                           device="cpu", n_estimators=n_est, random_state=0)
    clf.fit(Xs, ys)
    t_fit = time.time() - t
    t = time.time()
    pr = clf.predict(Xb_e)
    t_pred = time.time() - t
    acc = float((pr == yb).mean())
    results[f"tabpfn_n{n}_e{n_est}"] = {"fit_s": round(t_fit, 1), "predict_s": round(t_pred, 1),
                                        "acc": round(acc, 4), "features": int(Xa_e.shape[1])}
    print(f"  tabpfn n={n:5d} n_est={n_est}: fit={t_fit:6.1f}s predict={t_pred:6.1f}s acc={acc:.4f}")
    if n_sub == 2000 and t_pred > 600:
        print("  预测过慢，跳过全量计时")
        break

out = LAB / "out"
out.mkdir(exist_ok=True)
(out / "timing_probe.json").write_text(json.dumps({
    "single_fold": results,
    "n_encoded_features": int(n_encoded),
    "features": d,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print("\n写出 out/timing_probe.json")
print(f"总用时 {time.time() - t0:.1f}s")
