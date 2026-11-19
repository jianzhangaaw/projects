# -*- coding: utf-8 -*-
"""实验二：商品购买记录数据库（groceries.csv）的 DHP 频繁项集发现。

运行：python experiments/exp2_groceries_dhp.py
输出：results/groceries_basic_info.txt、results/dhp_support_scan.csv、
      results/dhp_bucket_scan.csv、results/dhp_frequent_itemsets.csv、
      results/dhp_rules.csv、results/dhp_main_result.json
"""
from __future__ import annotations

import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apriori import apriori                       # noqa: E402
from data_utils import basic_info, format_info, load_groceries, min_count_of  # noqa: E402
from dhp import dhp                               # noqa: E402
from rules import generate_rules, itemset_stats   # noqa: E402

RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

MAIN_SUPPORT = 0.01
SCAN_SUPPORTS = [0.03, 0.02, 0.015, 0.01]
BUCKETS = [200, 500, 1000, 2000, 3000, 5000, 10000]
MIN_CONFIDENCE = 0.30


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    transactions = load_groceries()
    n = len(transactions)

    info = basic_info(transactions, "商品购买记录数据库 groceries.csv")
    lines = [
        "=" * 72,
        "一、数据基本信息与预处理",
        "=" * 72,
        "原始文件：data/groceries.csv，每行是一条购物事务，商品名之间用逗号分隔，",
        "文件不含表头，单行商品数即该次购物的事务长度。",
        "",
        format_info(info),
        "",
        "预处理：",
        "  1) 逐行读取并切分商品名，去掉空字段（部分行末尾有逗号），得到 9835 条事务；",
        "  2) 每条事务内部的商品做去重，同一商品在一次购物中只算一次；",
        "  3) 事务中商品种类数 1~32，平均 4.409 种，属于典型的稀疏购物篮数据；",
        "  4) 不做离散化或归一化——关联分析直接以商品名作为项。",
        "",
        "事务长度分布（长度:事务数）：",
        "  " + ", ".join(f"{k}:{v}" for k, v in info["length_dist"].items()),
    ]
    text = "\n".join(lines)
    print(text)
    with open(RESULTS / "groceries_basic_info.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")

    # ---------- 不同支持度下 DHP 与 Apriori 的对照 ----------
    print("\n" + "=" * 72)
    print("二、不同最小支持度下的 DHP 挖掘结果（并与 Apriori 的结果一致性核对）")
    print("=" * 72)
    scan_rows = []
    consistency = []
    for ms in SCAN_SUPPORTS:
        t0 = time.perf_counter()
        d = dhp(transactions, ms, n_buckets=3000)
        t_dhp = time.perf_counter() - t0
        a = apriori(transactions, ms)
        t_ap = a["total_time"]
        same = (d["frequent"] == a["frequent"])
        consistency.append(same)
        hi = d["hash_info"]
        by_len = itemset_stats(d["frequent"])
        scan_rows.append([
            f"{ms:.3f}", min_count_of(ms, n), d["total_time"], t_ap,
            len(d["frequent"]), max(by_len) if by_len else 0,
            hi["full_c2"], hi["c2_after_hash"],
            f"{hi['hash_pruned_2'] / max(1, hi['full_c2']):.4f}",
            hi["items_removed_by_pruning"],
        ])
        print(f"  min_support={ms:.3f}（计数≥{min_count_of(ms, n)}）: "
              f"DHP 频繁项集 {len(d['frequent'])} 个，最长 {max(by_len) if by_len else 0} 项；"
              f"C2 全量 {hi['full_c2']} → 哈希裁剪后 {hi['c2_after_hash']}；"
              f"DHP {d['total_time']:.3f}s / Apriori {t_ap:.3f}s；"
              f"两算法结果一致：{same}", flush=True)
    write_csv(RESULTS / "dhp_support_scan.csv",
              ["min_support", "min_count", "dhp_time_s", "apriori_time_s", "n_frequent",
               "max_len", "c2_full", "c2_after_hash", "hash_prune_ratio",
               "items_removed_by_pruning"], scan_rows)
    if not all(consistency):
        raise SystemExit("DHP 与 Apriori 结果不一致，终止实验")

    # ---------- 主阈值下的详细结果 ----------
    print("\n" + "=" * 72)
    print(f"三、主实验：min_support={MAIN_SUPPORT} 的 DHP 结果")
    print("=" * 72)
    res = dhp(transactions, MAIN_SUPPORT, n_buckets=3000, verbose=True)
    frequent = res["frequent"]
    by_len = itemset_stats(frequent)
    hi = res["hash_info"]
    print(f"  合计频繁项集 {len(frequent)} 个，按长度分布：{by_len}")
    print(f"  哈希裁剪：C2 全量候选 {hi['full_c2']} 个，"
          f"哈希桶（桶数 {hi['n_buckets']}）裁剪后剩 {hi['c2_after_hash']} 个，"
          f"裁剪率 {hi['hash_pruned_2'] / max(1, hi['full_c2']):.2%}")
    print(f"  事务修剪：第 1 轮后从 {n} 条事务中删除 {hi['items_removed_by_pruning']} 个"
          f"不频繁项，保留 {hi['transactions_after_pruning']} 条长度≥2 的事务")
    print(f"  DHP 总耗时 {res['total_time']:.3f}s")

    rows = sorted(frequent.items(), key=lambda kv: (-len(kv[0]), -kv[1], kv[0]))
    write_csv(RESULTS / "dhp_frequent_itemsets.csv",
              ["itemset", "length", "count", "support"],
              [[" & ".join(k), len(k), v, f"{v / n:.6f}"] for k, v in rows])
    print(f"  频繁项集明细已写入 results/dhp_frequent_itemsets.csv")

    top_l1 = sorted(((k[0], v) for k, v in frequent.items() if len(k) == 1),
                    key=lambda kv: -kv[1])[:15]
    print("\n  支持度最高的 15 个单项：")
    for k, v in top_l1:
        print(f"    {k:<28} 计数 {v:>5}  支持度 {v / n:.4f}")

    top_multi = [kv for kv in rows if len(kv[0]) >= 2][:10]
    print("\n  支持度最高的 10 个多项集：")
    for k, v in top_multi:
        print(f"    {' & '.join(k):<60} 计数 {v:>5}  支持度 {v / n:.4f}")

    rules = generate_rules(frequent, n, min_confidence=MIN_CONFIDENCE)
    rules.sort(key=lambda r: (-r["lift"], -r["support"]))
    write_csv(RESULTS / "dhp_rules.csv",
              ["antecedent", "consequent", "support", "confidence", "lift", "count"],
              [[" & ".join(r["antecedent"]), " & ".join(r["consequent"]),
                f"{r['support']:.6f}", f"{r['confidence']:.4f}", f"{r['lift']:.4f}",
                r["count"]] for r in rules])
    print(f"\n  置信度≥{MIN_CONFIDENCE} 的关联规则 {len(rules)} 条，"
          f"按提升度排序，提升度最高的 10 条：")
    for r in rules[:10]:
        print(f"    {' & '.join(r['antecedent'])} => {' & '.join(r['consequent'])}  "
              f"support={r['support']:.4f} confidence={r['confidence']:.4f} "
              f"lift={r['lift']:.4f}")

    # ---------- 哈希桶数对裁剪效果的影响 ----------
    print("\n" + "=" * 72)
    print("四、哈希桶数对 DHP 裁剪效果与耗时的影响")
    print("=" * 72)
    bucket_rows = []
    for B in BUCKETS:
        r = dhp(transactions, MAIN_SUPPORT, n_buckets=B)
        h = r["hash_info"]
        ratio = h["hash_pruned_2"] / max(1, h["full_c2"])
        bucket_rows.append([B, h["full_c2"], h["c2_after_hash"], h["hash_pruned_2"],
                            f"{ratio:.4f}", r["total_time"]])
        print(f"  桶数 B={B:>6}: C2 {h['full_c2']} → {h['c2_after_hash']}"
              f"（裁剪率 {ratio:.2%}），耗时 {r['total_time']:.3f}s", flush=True)
    write_csv(RESULTS / "dhp_bucket_scan.csv",
              ["n_buckets", "c2_full", "c2_after_hash", "c2_pruned",
               "prune_ratio", "time_s"], bucket_rows)

    with open(RESULTS / "dhp_main_result.json", "w", encoding="utf-8") as f:
        json.dump({
            "dataset": "groceries.csv",
            "n_transactions": n,
            "n_items": info["n_items"],
            "min_support": MAIN_SUPPORT,
            "min_count": res["min_count"],
            "n_frequent": len(frequent),
            "itemset_by_len": {str(k): v for k, v in by_len.items()},
            "n_rules": len(rules),
            "min_confidence": MIN_CONFIDENCE,
            "time_s": res["total_time"],
            "hash_info": hi,
            "layers": res["stats"],
            "top_items": [{"item": k, "count": v, "support": v / n} for k, v in top_l1],
            "top_itemsets": [{"itemset": " & ".join(k), "count": v, "support": v / n}
                             for k, v in top_multi],
            "top_rules": [{"antecedent": " & ".join(r["antecedent"]),
                           "consequent": " & ".join(r["consequent"]),
                           "support": r["support"], "confidence": r["confidence"],
                           "lift": r["lift"]} for r in rules[:10]],
            "bucket_scan": bucket_rows,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n实验二完成，总耗时 {time.perf_counter() - t_start:.3f}s")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    t_start = time.perf_counter()
    main()
