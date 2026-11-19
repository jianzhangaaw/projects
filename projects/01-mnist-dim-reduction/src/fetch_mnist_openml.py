# -*- coding: utf-8 -*-
"""加载 MNIST：优先 fetch_openml，成功后缓存为 npz；缓存存在则直接复用。"""
import os
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "mnist_openml.npz")


def load_openml():
    from sklearn.datasets import fetch_openml

    t0 = time.time()
    print("[data] 调用 sklearn.datasets.fetch_openml('mnist_784', version=1) ...", flush=True)
    ds = fetch_openml("mnist_784", version=1, as_frame=False, data_home=os.path.join(DATA, "openml"))
    X = np.asarray(ds.data, dtype=np.float32)
    y = np.asarray(ds.target, dtype=np.int64)
    print(f"[data] fetch_openml 完成，用时 {time.time()-t0:.1f}s，X={X.shape} y={y.shape}", flush=True)
    return X, y


if __name__ == "__main__":
    if os.path.exists(CACHE):
        d = np.load(CACHE)
        print("cache exists:", CACHE, d["X"].shape, os.path.getsize(CACHE))
    else:
        X, y = load_openml()
        assert X.shape == (70000, 784), X.shape
        assert y.shape == (70000,)
        assert X.min() == 0 and X.max() == 255, (float(X.min()), float(X.max()))
        print("label counts:", np.bincount(y).tolist())
        np.savez_compressed(CACHE, X=X.astype(np.uint8), y=y.astype(np.uint8))
        print("saved", CACHE, os.path.getsize(CACHE))
    print("DONE")
