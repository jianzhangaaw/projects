# -*- coding: utf-8 -*-
"""
实验：MNIST 手写数字数据集降维与可视化
- 数据加载：MNIST（70000 x 784）
- 预处理：像素归一化、抽样
- 降维：PCA、RandomProjection、LDA（线性）/ KernelPCA(RBF)、t-SNE（非线性）
- 可视化：matplotlib 二维散点图（按数字类别着色）+ 对比图
- 定量评价：trustworthiness、2 维嵌入上的 5-NN 分类准确率、类内/类间距离比、耗时
"""
import json
import os
import sys
import time

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
ROOTS = [HERE, PARENT]  # 开发目录（脚本同级放 data/figures/results）/ 归档目录（实验根下放 数据/结果）


def resolve_dir(names, fallback):
    """在脚本目录、上一级目录里找已有同名目录；都没有就在脚本目录下新建 fallback。

    这样同一份脚本既能直接运行（data、figures、results 与脚本同级），
    也能在归档布局（代码/、数据/、结果/）下运行，不需要改路径。
    """
    for root in ROOTS:
        for n in names:
            p = os.path.join(root, n)
            if os.path.isdir(p):
                return p
    p = os.path.join(HERE, fallback)
    os.makedirs(p, exist_ok=True)
    return p


DATA = resolve_dir(["data", "数据"], "data")
OUT = RESULT = resolve_dir(["results", "结果"], "results")
# 开发目录里图放 figures、指标放 results；归档布局里两者都在“结果”目录下
FIG = RESULT if os.path.basename(RESULT) == "结果" else resolve_dir(["figures"], "figures")
os.makedirs(FIG, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

SAMPLE_N = 5000
RANDOM_STATE = 42
NEIGHBORS = 5

# 中文字体：模板正文是中文，图题也用中文，避免方块
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 130


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- 1. 加载数据
def load_mnist():
    cache = os.path.join(DATA, "mnist_openml.npz")
    idx_cache = os.path.join(DATA, "mnist_idx.npz")
    if os.path.exists(cache):
        d = np.load(cache)
        log(f"从 fetch_openml 缓存加载: {cache}")
        return d["X"].astype(np.float32), d["y"].astype(np.int64), "sklearn.datasets.fetch_openml('mnist_784')"
    if os.path.exists(idx_cache):
        d = np.load(idx_cache)
        log(f"从原始 IDX 缓存加载: {idx_cache}")
        return d["X"].astype(np.float32), d["y"].astype(np.int64), "MNIST 原始 IDX 文件"
    raise FileNotFoundError("找不到数据缓存，请先运行 fetch_mnist_openml.py 或 prepare_idx_data.py")


X_all, y_all, source = load_mnist()
log(f"数据来源: {source}")
log(f"完整数据集形状: X={X_all.shape}, y={y_all.shape}, X.dtype={X_all.dtype}")
log(f"像素取值范围: min={X_all.min():.0f}, max={X_all.max():.0f}, mean={X_all.mean():.2f}")
counts = np.bincount(y_all, minlength=10)
log("各类别样本数: " + ", ".join(f"{i}:{c}" for i, c in enumerate(counts)))
log(f"非零像素占比: {(X_all > 0).mean() * 100:.2f}%")

# ---------------------------------------------------------------- 2. 预处理
# 固定随机种子分层抽样，保证每个数字类别样本数接近
rng = np.random.RandomState(RANDOM_STATE)
idx = []
per_class = SAMPLE_N // 10
for digit in range(10):
    cls_idx = np.where(y_all == digit)[0]
    idx.append(rng.choice(cls_idx, size=per_class, replace=False))
idx = np.concatenate(idx)
rng.shuffle(idx)
X_raw = X_all[idx]
y = y_all[idx]
X = X_raw / 255.0  # 归一化到 [0,1]，消除量纲影响

log(f"抽样后数据: X={X.shape}, 每类 {per_class} 个样本")
log(f"归一化后像素范围: [{X.min():.3f}, {X.max():.3f}]")
assert X.shape[0] == SAMPLE_N and len(np.unique(y)) == 10

# 样本预览图
fig, axes = plt.subplots(2, 10, figsize=(12, 2.8))
for digit in range(10):
    for row in range(2):
        ax = axes[row, digit]
        ax.imshow(X_raw[y == digit][row].reshape(28, 28), cmap="gray_r")
        ax.axis("off")
        if row == 0:
            ax.set_title(str(digit), fontsize=10)
fig.suptitle("MNIST 样本预览（每列一个数字类别）", fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig1_samples.png"), bbox_inches="tight")
plt.close(fig)
log("已保存 fig1_samples.png")

# ---------------------------------------------------------------- 3. 降维算法
from sklearn.decomposition import PCA, KernelPCA, IncrementalPCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.manifold import TSNE, trustworthiness
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score
from sklearn.random_projection import GaussianRandomProjection

methods = [
    ("PCA", PCA(n_components=2, random_state=RANDOM_STATE), True, "线性（无监督，方差最大方向）"),
    ("RandomProjection", GaussianRandomProjection(n_components=2, random_state=RANDOM_STATE), True,
     "线性（无监督，随机高斯矩阵）"),
    ("LDA", LinearDiscriminantAnalysis(n_components=2), True, "线性（有监督，类间/类内散度比最大）"),
    ("KernelPCA-RBF", KernelPCA(n_components=2, kernel="rbf", gamma=1e-3), False, "非线性（核技巧）"),
    ("t-SNE", TSNE(n_components=2, perplexity=30, init="pca", learning_rate="auto",
                   max_iter=1000, random_state=RANDOM_STATE, n_jobs=-1), False, "非线性（流形学习，保持局部邻域）"),
]

results = {}
embeddings = {}
log(f"开始降维，样本数 {SAMPLE_N}，原始维度 {X.shape[1]}")

for name, model, _linear, desc in methods:
    t0 = time.time()
    Z = model.fit_transform(X, y) if name == "LDA" else model.fit_transform(X)
    fit_time = time.time() - t0
    embeddings[name] = Z

    # 评价指标 1：trustworthiness（2 维嵌入在多大程度上保留了原始空间的近邻关系）
    t0 = time.time()
    tw = trustworthiness(X, Z, n_neighbors=NEIGHBORS)
    tw_time = time.time() - t0
    # 评价指标 2：2 维嵌入上 5-NN 分类交叉验证准确率
    t0 = time.time()
    knn = KNeighborsClassifier(n_neighbors=NEIGHBORS, n_jobs=-1)
    acc = cross_val_score(knn, Z, y, cv=5, n_jobs=1).mean()
    knn_time = time.time() - t0
    # 评价指标 3：类内平均距离 / 类间中心平均距离（越小说明类内越紧凑）
    intra = np.mean([np.linalg.norm(Z[y == d] - Z[y == d].mean(axis=0), axis=1).mean() for d in range(10)])
    centers = np.stack([Z[y == d].mean(axis=0) for d in range(10)])
    inter = np.mean([np.linalg.norm(centers[i] - centers[j]) for i in range(10) for j in range(i + 1, 10)])
    ratio = intra / inter

    results[name] = {
        "描述": desc,
        "fit_time_s": round(fit_time, 2),
        "trustworthiness": round(float(tw), 4),
        "knn5_accuracy": round(float(acc), 4),
        "intra_over_inter": round(float(ratio), 4),
        "tw_time_s": round(tw_time, 2),
        "knn_time_s": round(knn_time, 2),
    }
    log(f"{name:<17} 耗时 {fit_time:6.2f}s | trustworthiness={tw:.4f} | 5-NN准确率={acc:.4f} | 类内/类间={ratio:.4f}")

# PCA 主成分解释方差
pca_full = PCA(n_components=50, random_state=RANDOM_STATE).fit(X)
evr = pca_full.explained_variance_ratio_
results["_PCA_explained_variance"] = {
    "PC1": round(float(evr[0]), 4),
    "PC2": round(float(evr[1]), 4),
    "PC1_PC2_sum": round(float(evr[:2].sum()), 4),
    "top50_sum": round(float(evr.sum()), 4),
}
log(f"PCA: PC1 解释方差 {evr[0]:.4f}，PC2 {evr[1]:.4f}，两者合计 {evr[:2].sum():.4f}，前 50 维合计 {evr.sum():.4f}")

# ---------------------------------------------------------------- 4. 可视化
colors = plt.get_cmap("tab10")
def scatter(ax, Z, title, subtitle=""):
    for d in range(10):
        m = y == d
        ax.scatter(Z[m, 0], Z[m, 1], s=4, alpha=0.65, color=colors(d), label=str(d), linewidths=0)
    ax.set_title(title + (f"\n{subtitle}" if subtitle else ""), fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])

for name, Z in embeddings.items():
    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    r = results[name]
    scatter(ax, Z, f"{name} 降维结果（MNIST，{SAMPLE_N} 样本）",
            f"trustworthiness={r['trustworthiness']:.3f}  5-NN 准确率={r['knn5_accuracy']:.3f}  耗时={r['fit_time_s']}s")
    ax.legend(title="数字类别", markerscale=3, fontsize=8, loc="best", framealpha=0.85, ncol=2)
    fig.tight_layout()
    fn = os.path.join(FIG, f"fig_{name.replace('-', '_').lower()}.png")
    fig.savefig(fn, bbox_inches="tight")
    plt.close(fig)
    log(f"已保存 {os.path.basename(fn)}")

# 2x3 对比大图
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
names = [m[0] for m in methods]
for ax, name in zip(axes.ravel(), names):
    Z = embeddings[name]
    r = results[name]
    scatter(ax, Z, f"{name}", f"trustworthiness={r['trustworthiness']:.3f} | 5-NN acc={r['knn5_accuracy']:.3f}")
handles = [plt.Line2D([], [], marker="o", linestyle="", color=colors(d), label=str(d), markersize=6) for d in range(10)]
axes.ravel()[-1].axis("off")
axes.ravel()[-1].legend(handles=handles, title="数字类别", loc="center", ncol=2, fontsize=12, title_fontsize=13)
fig.suptitle(f"五种降维算法在 MNIST 上的二维可视化对比（{SAMPLE_N} 个样本）", fontsize=15)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_grid_compare.png"), bbox_inches="tight")
plt.close(fig)
log("已保存 fig_grid_compare.png")

# 指标条形图
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
for ax, key, title, ylim in zip(
    axes,
    ["trustworthiness", "knn5_accuracy", "intra_over_inter"],
    ["Trustworthiness（越高越好）", "2 维嵌入上 5-NN 准确率（越高越好）", "类内/类间距离比（越低越紧凑）"],
    [None, None, None],
):
    vals = [results[n][key] for n in names]
    bars = ax.bar(names, vals, color=[colors(i) for i in range(len(names))])
    ax.set_title(title, fontsize=11)
    ax.tick_params(axis="x", rotation=20)
    ax.bar_label(bars, fmt="%.3f", fontsize=9)
    if ylim:
        ax.set_ylim(*ylim)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_metrics.png"), bbox_inches="tight")
plt.close(fig)
log("已保存 fig_metrics.png")

# PCA 累计解释方差曲线
fig, ax = plt.subplots(figsize=(7, 4.4))
cum = np.cumsum(evr)
ax.plot(range(1, 51), cum * 100, marker="o", ms=3)
ax.axhline(cum[1] * 100, color="crimson", ls="--", lw=1)
ax.annotate(f"前 2 维：{cum[1]*100:.1f}%", xy=(2, cum[1] * 100), xytext=(10, 30), fontsize=10,
            arrowprops=dict(arrowstyle="->", color="crimson"))
ax.set_xlabel("主成分个数")
ax.set_ylabel("累计解释方差 (%)")
ax.set_title("PCA 累计解释方差（MNIST 5000 样本，前 50 个主成分）")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_pca_variance.png"), bbox_inches="tight")
plt.close(fig)
log("已保存 fig_pca_variance.png")

# 保存降维后坐标与指标
np.savez_compressed(os.path.join(OUT, "embeddings.npz"), y=y,
                    **{f"Z_{k}": v for k, v in embeddings.items()})
with open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
with open(os.path.join(OUT, "metrics.csv"), "w", encoding="utf-8-sig") as f:
    f.write("算法,描述,耗时(s),trustworthiness,5NN准确率,类内/类间比,样本数,原始维度\n")
    for n in names:
        r = results[n]
        f.write(f"{n},{r['描述']},{r['fit_time_s']},{r['trustworthiness']},{r['knn5_accuracy']},"
                f"{r['intra_over_inter']},{SAMPLE_N},784\n")
log(f"结果已写入 {OUT}")

# 控制台汇总表
log("=" * 92)
log(f"{'算法':<18}{'类型':<6}{'耗时(s)':>9}{'trustworthiness':>17}{'5-NN准确率':>12}{'类内/类间':>11}")
log("-" * 92)
for n in names:
    r = results[n]
    kind = "线性" if any(m[0] == n and m[2] for m in methods) else "非线性"
    log(f"{n:<18}{kind:<6}{r['fit_time_s']:>9.2f}{r['trustworthiness']:>17.4f}"
        f"{r['knn5_accuracy']:>12.4f}{r['intra_over_inter']:>11.4f}")
log("=" * 92)
log("实验完成")
