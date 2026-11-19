# -*- coding: utf-8 -*-
"""把 MNIST 原始 IDX 文件解析成 npz，作为 fetch_openml 之外的本地数据源。

IDX 格式（大端）：
images: magic(4) count(4) rows(4) cols(4) 之后 count*rows*cols 字节
labels: magic(4) count(4) 之后 count 字节
"""
import gzip
import os
import struct

import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
idx_dir = os.path.join(here, "data", "idx")


def read_idx(path):
    with gzip.open(path, "rb") as f:
        magic = struct.unpack(">I", f.read(4))[0]
        ndim = magic & 0xFF
        if magic >> 8 != 0x0803 and magic >> 8 != 0x0801:
            raise ValueError(f"unexpected magic {magic:#x} in {path}")
        dims = struct.unpack(">" + "I" * ndim, f.read(4 * ndim))
        data = np.frombuffer(f.read(), dtype=np.uint8)
    expected = int(np.prod(dims))
    if data.size != expected:
        raise ValueError(f"{path}: got {data.size} bytes, expected {expected}")
    return data.reshape(dims), dims


if __name__ == "__main__":
    tr_img, tr_shape = read_idx(os.path.join(idx_dir, "train-images-idx3-ubyte.gz"))
    tr_lbl, _ = read_idx(os.path.join(idx_dir, "train-labels-idx1-ubyte.gz"))
    te_img, te_shape = read_idx(os.path.join(idx_dir, "t10k-images-idx3-ubyte.gz"))
    te_lbl, _ = read_idx(os.path.join(idx_dir, "t10k-labels-idx1-ubyte.gz"))

    print("train images", tr_shape, tr_img.dtype, "labels", tr_lbl.shape)
    print("test  images", te_shape, te_img.dtype, "labels", te_lbl.shape)
    assert tr_img.shape[0] == tr_lbl.shape[0] == 60000, "train 数量不对"
    assert te_img.shape[0] == te_lbl.shape[0] == 10000, "test 数量不对"
    assert tr_img.shape == (60000, 28, 28) and te_img.shape == (10000, 28, 28)

    X = np.concatenate([tr_img, te_img]).reshape(-1, 784).astype(np.uint8)
    y = np.concatenate([tr_lbl, te_lbl]).astype(np.uint8)
    assert X.shape == (70000, 784) and y.shape == (70000,)
    # 像素范围校验：MNIST 应当是 0-255
    assert X.min() == 0 and X.max() == 255, (X.min(), X.max())

    out = os.path.join(here, "data", "mnist_idx.npz")
    np.savez_compressed(out, X=X, y=y)
    print("saved", out, os.path.getsize(out), "bytes; label counts:", np.bincount(y).tolist())
