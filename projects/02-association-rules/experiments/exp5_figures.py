# -*- coding: utf-8 -*-
"""实验五：把实验结果画成图，供实验报告插图使用。

运行：python experiments/exp5_figures.py
输出：figures/*.png
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np              # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
FIGURES.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "src"))

from data_utils import CAR_COLUMNS, CAR_LABELS, load_car  # noqa: E402

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200
plt.rcParams["font.size"] = 10.5
plt.rcParams["axes.titlesize"] = 11
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3

COLORS = ["#2E5C8A", "#C0504D", "#4F8A5B", "#8064A2", "#E36C0A"]


def read_csv(name):
    path = RESULTS / name
    if not path.exists():
        print(f"  [跳过] 缺少 {name}")
        return None
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save(fig, name):
    path = FIGURES / name
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  已生成 {path.name}")


def fig_car_distribution():
    _, raw, _ = load_car()
    fig, axes = plt.subplots(2, 4, figsize=(11, 5))
    for i, col in enumerate(CAR_COLUMNS):
        ax = axes[i // 4][i % 4]
        values = [row[i] for row in raw]
        labels = sorted(set(values))
        counts = [values.count(v) for v in labels]
        ax.bar(labels, counts, color=COLORS[0], width=0.6)
        ax.set_title(f"{col}（{CAR_LABELS[col]}）")
        ax.set_ylabel("记录数")
        ax.tick_params(axis="x", rotation=30)
        for x, c in zip(range(len(labels)), counts):
            ax.text(x, c + 15, str(c), ha="center", fontsize=8)
    axes[1][3].axis("off")
    fig.suptitle("图 1  汽车评估数据库各属性取值分布", fontsize=12)
    save(fig, "fig01_car_distribution.png")


def fig_car_support_scan():
    rows = read_csv("car_support_scan.csv")
    if not rows:
        return
    ms = [float(r["min_support"]) for r in rows]
    n = [int(r["n_frequent"]) for r in rows]
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.plot(ms, n, "o-", color=COLORS[0], label="频繁项集总数")
    for key, label, color in [("L2", "2 项集", COLORS[1]), ("L3", "3 项集", COLORS[2])]:
        ax.plot(ms, [int(r[key]) for r in rows], "s--", color=color, label=label)
    ax.set_xlabel("最小支持度")
    ax.set_ylabel("频繁项集个数")
    ax.invert_xaxis()
    ax.set_title("图 2  car.data 上支持度阈值与频繁项集数量的关系")
    ax.legend()
    save(fig, "fig02_car_support_scan.png")


def fig_car_apriori_layers():
    data = json.loads((RESULTS / "car_main_result.json").read_text(encoding="utf-8"))
    layers = data["layers"]
    ks = [f"k={s['k']}" for s in layers]
    cand = [s["candidates"] for s in layers]
    freq = [s["frequent"] for s in layers]
    x = np.arange(len(ks))
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.bar(x - 0.2, cand, 0.4, label="候选项集", color=COLORS[0])
    ax.bar(x + 0.2, freq, 0.4, label="频繁项集", color=COLORS[1])
    for xi, (c, f) in enumerate(zip(cand, freq)):
        ax.text(xi - 0.2, c, str(c), ha="center", va="bottom", fontsize=8)
        ax.text(xi + 0.2, f, str(f), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x, ks)
    ax.set_ylabel("项集个数")
    ax.set_ylim(0, max(cand) * 1.18)
    ax.set_title("图 3  Apriori 逐层候选与频繁项集（car.data，min_support=0.20）")
    ax.legend()
    save(fig, "fig03_car_apriori_layers.png")


def fig_dhp_bucket():
    rows = read_csv("dhp_bucket_scan.csv")
    if not rows:
        return
    b = [int(r["n_buckets"]) for r in rows]
    ratio = [float(r["prune_ratio"]) * 100 for r in rows]
    time_s = [float(r["time_s"]) for r in rows]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.bar([str(x) for x in b], ratio, color=COLORS[0], width=0.55, label="候选裁剪率")
    for i, v in enumerate(ratio):
        ax.text(i, v + 1.5, f"{v:.1f}%", ha="center", fontsize=8)
    ax.set_xlabel("哈希桶数 B")
    ax.set_ylabel("C2 候选裁剪率 / %")
    ax.set_ylim(0, 105)
    ax2 = ax.twinx()
    ax2.plot([str(x) for x in b], [t * 1000 for t in time_s], "o-",
             color=COLORS[1], label="DHP 耗时")
    ax2.set_ylabel("DHP 耗时 / ms")
    ax2.grid(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="center right")
    ax.set_title("图 4  哈希桶数对 DHP 候选裁剪率与耗时的影响（min_support=0.01）")
    save(fig, "fig04_dhp_bucket.png")


def fig_groceries_basket():
    with open(ROOT / "data" / "groceries.csv", encoding="utf-8") as f:
        lengths = [len([x for x in line.strip().split(",") if x]) for line in f if line.strip()]
    from collections import Counter
    dist = Counter(lengths)
    xs = sorted(dist)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.bar([str(x) for x in xs], [dist[x] for x in xs], color=COLORS[2], width=0.75)
    ax.set_xlabel("事务长度（一次购物的商品种类数）")
    ax.set_ylabel("事务数")
    ax.tick_params(axis="x", labelsize=7)
    ax.set_title(f"图 5  商品购买记录数据库事务长度分布（共 {len(lengths)} 条事务，"
                 f"平均 {np.mean(lengths):.2f} 项）")
    save(fig, "fig05_groceries_basket_length.png")


def fig_top_items():
    data = json.loads((RESULTS / "dhp_main_result.json").read_text(encoding="utf-8"))
    items = data["top_items"][:15]
    labels = [i["item"] for i in items][::-1]
    sup = [i["support"] * 100 for i in items][::-1]
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.barh(labels, sup, color=COLORS[0])
    for y, v in enumerate(sup):
        ax.text(v + 0.3, y, f"{v:.2f}%", va="center", fontsize=8)
    ax.set_xlabel("支持度 / %")
    ax.set_xlim(0, max(sup) * 1.15)
    ax.set_title("图 6  支持度最高的 15 种商品（min_support=0.01）")
    save(fig, "fig06_top_items.png")


def fig_top_itemsets():
    data = json.loads((RESULTS / "dhp_main_result.json").read_text(encoding="utf-8"))
    ts = data["top_itemsets"][:10]
    labels = [" & ".join(i["itemset"].split(" & ")) for i in ts][::-1]
    sup = [i["support"] * 100 for i in ts][::-1]
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    ax.barh(labels, sup, color=COLORS[2])
    for y, v in enumerate(sup):
        ax.text(v + 0.02, y, f"{v:.2f}%", va="center", fontsize=8)
    ax.set_xlabel("支持度 / %")
    ax.set_xlim(0, max(sup) * 1.18)
    ax.tick_params(axis="y", labelsize=8.5)
    ax.set_title("图 7  支持度最高的 10 个频繁项集（min_support=0.01）")
    save(fig, "fig07_top_itemsets.png")


def fig_support_scan_compare():
    rows = read_csv("compare_support_scan.csv")
    if not rows:
        return
    ms = [f"{float(r['min_support']):.3f}" for r in rows]
    ap = [float(r["apriori_time_s"]) * 1000 for r in rows]
    dh = [float(r["dhp_time_s"]) * 1000 for r in rows]
    fp = [float(r["fpgrowth_time_s"]) * 1000 for r in rows]
    x = np.arange(len(ms))
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.bar(x - 0.26, ap, 0.26, label="Apriori", color=COLORS[0])
    ax.bar(x, dh, 0.26, label="DHP", color=COLORS[1])
    ax.bar(x + 0.26, fp, 0.26, label="FP-Growth", color=COLORS[2])
    ax.set_xticks(x, ms)
    ax.set_xlabel("最小支持度")
    ax.set_ylabel("挖掘耗时 / ms")
    ax2 = ax.twinx()
    ax2.plot(x, [int(r["n_frequent"]) for r in rows], "k^--", label="频繁项集数")
    ax2.set_ylabel("频繁项集个数")
    ax2.grid(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=9)
    ax.set_title("图 8  groceries.csv 上三种算法耗时随支持度阈值的变化")
    save(fig, "fig08_support_time_compare.png")


def fig_scale():
    rows = read_csv("compare_scale_scan.csv")
    if not rows:
        return
    n = [int(r["n_transactions"]) for r in rows]
    ap = [float(r["apriori_time_s"]) * 1000 for r in rows]
    dh = [float(r["dhp_time_s"]) * 1000 for r in rows]
    fp = [float(r["fpgrowth_time_s"]) * 1000 for r in rows]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot(n, ap, "o-", color=COLORS[0], label="Apriori")
    ax.plot(n, dh, "s-", color=COLORS[1], label="DHP")
    ax.plot(n, fp, "^-", color=COLORS[2], label="FP-Growth")
    for xi, yi in zip(n, ap):
        ax.text(xi, yi * 1.06, f"{yi:.0f}", ha="center", fontsize=8)
    ax.set_xlabel("事务数（把 9835 条事务按行重复 1/2/4/8 倍）")
    ax.set_ylabel("挖掘耗时 / ms（对数刻度）")
    ax.set_yscale("log")
    ax.set_xticks(n)
    ax.set_title("图 9  数据规模放大后三种算法的耗时变化（min_support=0.01）")
    ax.legend()
    save(fig, "fig09_scale.png")


def fig_layers_compare():
    rows = read_csv("compare_layers.csv")
    if not rows:
        return
    ks = [f"k={r['k']}" for r in rows]
    ap = [int(r["apriori_candidates"]) for r in rows]
    dh = [int(r["dhp_candidates"]) if r["dhp_candidates"] else 0 for r in rows]
    x = np.arange(len(ks))
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.bar(x - 0.2, ap, 0.4, label="Apriori 候选数", color=COLORS[0])
    ax.bar(x + 0.2, dh, 0.4, label="DHP 候选数（哈希裁剪后）", color=COLORS[1])
    for xi, (a, d) in enumerate(zip(ap, dh)):
        ax.text(xi - 0.2, a, str(a), ha="center", va="bottom", fontsize=8)
        ax.text(xi + 0.2, d, str(d), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x, ks)
    ax.set_ylabel("候选项集个数")
    ax.set_ylim(0, max(ap) * 1.2)
    ax.set_title("图 10  逐层候选数对比（groceries.csv，min_support=0.01）")
    ax.legend()
    save(fig, "fig10_layers_compare.png")


def fig_car_time():
    rows = read_csv("compare_car.csv")
    if not rows:
        return
    ms = [f"{float(r['min_support']):.2f}" for r in rows]
    ap = [float(r["apriori_time_s"]) * 1000 for r in rows]
    dh = [float(r["dhp_time_s"]) * 1000 for r in rows]
    fp = [float(r["fpgrowth_time_s"]) * 1000 for r in rows]
    x = np.arange(len(ms))
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    ax.bar(x - 0.26, ap, 0.26, label="Apriori", color=COLORS[0])
    ax.bar(x, dh, 0.26, label="DHP", color=COLORS[1])
    ax.bar(x + 0.26, fp, 0.26, label="FP-Growth", color=COLORS[2])
    ax.set_xticks(x, ms)
    ax.set_xlabel("最小支持度")
    ax.set_ylabel("挖掘耗时 / ms")
    ax.set_title("图 11  car.data 上三种算法耗时对比")
    ax.legend()
    save(fig, "fig11_car_time.png")


def main():
    print("开始绘图……")
    fig_car_distribution()
    fig_car_support_scan()
    fig_car_apriori_layers()
    fig_dhp_bucket()
    fig_groceries_basket()
    fig_top_items()
    fig_top_itemsets()
    fig_support_scan_compare()
    fig_scale()
    fig_layers_compare()
    fig_car_time()
    print("绘图完成")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
