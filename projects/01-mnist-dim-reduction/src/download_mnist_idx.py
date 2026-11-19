# -*- coding: utf-8 -*-
"""下载 MNIST 原始 IDX 文件（备用数据源）。"""
import os
import time
import urllib.request

BASE = "https://ossci-datasets.s3.amazonaws.com/mnist/"
FILES = [
    "train-images-idx3-ubyte.gz",
    "train-labels-idx1-ubyte.gz",
    "t10k-images-idx3-ubyte.gz",
    "t10k-labels-idx1-ubyte.gz",
]

outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "idx")
os.makedirs(outdir, exist_ok=True)

for name in FILES:
    dst = os.path.join(outdir, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        print(f"skip {name} ({os.path.getsize(dst)} bytes)")
        continue
    t0 = time.time()
    urllib.request.urlretrieve(BASE + name, dst + ".part")
    os.replace(dst + ".part", dst)
    dt = time.time() - t0
    print(f"ok   {name} {os.path.getsize(dst)} bytes {dt:.1f}s")
print("DONE")
