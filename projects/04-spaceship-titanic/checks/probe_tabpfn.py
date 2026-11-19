"""TabPFN 权重下载 + 最小可用性验证（走 hf-mirror）。

背景：TabPFN 是可复现的关键算法之一，但权重需要从 HuggingFace 拉取，本机直连
huggingface.co 超时、hf-mirror.com 可达，所以这里用镜像下载并做正向断言。
"""
import os
import sys
import time

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

import numpy as np

t0 = time.time()
print("HF_ENDPOINT =", os.environ["HF_ENDPOINT"], flush=True)

import tabpfn
print("tabpfn", tabpfn.__version__, flush=True)

from tabpfn import TabPFNClassifier
import inspect

print("TabPFNClassifier 签名:", inspect.signature(TabPFNClassifier.__init__), flush=True)

try:
    import tabpfn.model_loading as ml
    print("model_loading 可用常量:", [n for n in dir(ml) if "MODEL" in n.upper() or "PATH" in n.upper()][:20], flush=True)
except Exception as e:
    print("model_loading 探测失败:", e, flush=True)

rng = np.random.default_rng(0)
X = rng.normal(size=(120, 6))
y = (X[:, 0] + 0.5 * X[:, 1] > 0).astype(int)

clf = TabPFNClassifier(device="cpu")
print("构造完成，开始 fit（首次会触发权重下载）", flush=True)
clf.fit(X, y)
print(f"fit 完成，用时 {time.time() - t0:.1f}s", flush=True)
pred = clf.predict(X[:20])
proba = clf.predict_proba(X[:20])
print("predict 前 20:", pred.tolist(), flush=True)
print("predict_proba shape:", proba.shape, "| 行和:", np.round(proba.sum(axis=1)[:5], 6).tolist(), flush=True)
print("准确率(训练集自评):", float((pred == y[:20]).mean()), flush=True)
print("OK: TabPFN 可用", flush=True)
print(f"总用时 {time.time() - t0:.1f}s", flush=True)

# 记录权重落盘位置与体积，便于后续写报告
cache = os.environ.get("HF_HOME") or os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
hub = os.path.join(cache, "hub")
print("HF 缓存目录:", cache, "存在:", os.path.isdir(cache), flush=True)
if os.path.isdir(hub):
    for root, dirs, files in os.walk(hub):
        for f in files:
            p = os.path.join(root, f)
            if f.endswith((".ckpt", ".safetensors")) or "tabpfn" in f.lower():
                print(f"  {os.path.getsize(p) / 1e6:.1f} MB  {p}", flush=True)
sys.exit(0)
