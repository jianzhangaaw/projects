"""TabPFN v2（Nature 2025 论文对应版本）权重下载与可用性验证。

背景与判据：
- tabpfn 9.0.0 的默认模型是 v3.5，其 HF 仓库 Prior-Labs/tabpfn_3_5 需要接受 gated 许可
  （必须人工登录接受条款），本机不可自动化。
- v2 模型的 HF 仓库是 Prior-Labs/TabPFN-v2-clf，不在库的 gated 列表里，无需 token。
- 报告登记的参考论文即 TabPFN v2，因此用 v2 权重既可行又更贴合。
"""
import os
import sys
import time

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"

import numpy as np
import torch

print("HF_ENDPOINT =", os.environ["HF_ENDPOINT"], flush=True)
print("torch =", torch.__version__, "| threads =", torch.get_num_threads(), flush=True)

from tabpfn import TabPFNClassifier

MODEL = "tabpfn-v2-classifier-v2_default.ckpt"

rng = np.random.default_rng(0)
X = rng.normal(size=(200, 8))
y = (X[:, 0] + 0.6 * X[:, 1] - 0.4 * X[:, 2] > 0).astype(int)

t0 = time.time()
clf = TabPFNClassifier(
    model_path=MODEL,
    device="cpu",
    random_state=0,
    n_estimators=4,
)
print("构造完成，开始 fit（首次触发下载）", flush=True)
clf.fit(X, y)
print(f"fit 用时 {time.time() - t0:.1f}s", flush=True)
p = clf.predict(X[:40])
proba = clf.predict_proba(X[:40])
acc = float((p == y[:40]).mean())
print("predict:", p.tolist(), flush=True)
print("proba shape:", proba.shape, "行和:", np.round(proba.sum(1)[:3], 6).tolist(), flush=True)
print("训练子集准确率:", acc, flush=True)

assert proba.shape == (40, 2), "predict_proba 形状异常"
assert np.allclose(proba.sum(1), 1.0, atol=1e-5), "概率未归一"
assert set(np.unique(p)).issubset({0, 1}), "预测值域异常"
assert acc >= 0.8, f"训练子集准确率过低：{acc}"
print("OK: TabPFN v2 可用（断言全部通过）", flush=True)

# 权重落盘位置
cache = os.path.join(os.environ.get("APPDATA", ""), "tabpfn")
print("模型缓存目录:", cache, "存在:", os.path.isdir(cache), flush=True)
if os.path.isdir(cache):
    for root, _dirs, files in os.walk(cache):
        for f in files:
            fp = os.path.join(root, f)
            print(f"  {os.path.getsize(fp) / 1e6:8.1f} MB  {fp}", flush=True)
print(f"总用时 {time.time() - t0:.1f}s", flush=True)
