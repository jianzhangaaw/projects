# -*- coding: utf-8 -*-
"""实验三：商品购买记录数据库（groceries.csv）的 FP-Growth 频繁项集发现。

运行：python experiments/exp3_groceries_fpgrowth.py
输出：results/fpgrowth_support_scan.csv、results/fpgrowth_frequent_itemsets.csv、
      results/fpgrowth_rules.csv、results/fpgrowth_main_result.json
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_utils import basic_info, load_groceries, min_count_of  # noqa: E402
from dhp import dhp                                             # noqa: E402
from fpgrowth import fpgrowth                                   # noqa: E402
from rules import generate_rules, itemset_stats                 # noqa: E402

RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

MAIN_SUPPORT = 0.01
SCAN_SUPPORTS = [0.03, 0.02, 0.015, 0.01]
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

    print("=" * 72)
    print("一、不同最小支持度下的 FP-Growth 结果（并与 DHP 的结果核对）")
    print("=" * 72)
    scan_rows = []
    all_same = True
    for ms in SCAN_SUPPORTS:
        fp = fpgrowth(transactions, ms, verbose=True)
        d = dhp(transactions, ms, n_buckets=3000)
        same = (fp["frequent"] == d["frequent"])
        all_same &= same
        by_len = itemset_stats(fp["frequent"])
        scan_rows.append([f"{ms:.3f}", min_count_of(ms, n), fp["build_time"],
                          fp["total_time"], d["total_time"], len(fp["frequent"]),
                          max(by_len) if by_len else 0, fp["stats"]["tree_nodes"],
                          fp["stats"]["conditional_tree_nodes"],
                          fp["stats"]["conditional_pattern_base"],
                          fp["stats"]["recursive_calls"]])
        print(f"  min_support={ms:.3f}: 频繁项集 {len(fp['frequent'])} 个，"
              f"最长 {max(by_len) if by_len else 0} 项；FP-Growth 总耗时 {fp['total_time']:.3f}s "
              f"(建树 {fp['build_time']:.3f}s) / DHP {d['total_time']:.3f}s；"
              f"与 DHP 结果一致：{same}", flush=True)
    if not all_same:
        raise SystemExit("FP-Growth 与 DHP 结果不一致，终止实验")
    write_csv(RESULTS / "fpgrowth_support_scan.csv",
              ["min_support", "min_count", "build_time_s", "fpgrowth_time_s",
               "dhp_time_s", "n_frequent", "max_len", "main_tree_nodes",
               "conditional_tree_nodes", "conditional_pattern_base",
               "recursive_calls"], scan_rows)

    print("\n" + "=" * 72)
    print(f"二、主实验：min_support={MAIN_SUPPORT} 的 FP-Growth 结果")
    print("=" * 72)
    res = fpgrowth(transactions, MAIN_SUPPORT, verbose=True)
    frequent = res["frequent"]
    by_len = itemset_stats(frequent)
    st = res["stats"]
    print(f"  FP 树：主树非根结点 {st['tree_nodes']} 个，事务数 {n}，"
          f"压缩比约 {n / max(1, st['tree_nodes']):.2f}:1")
    print(f"  挖掘过程：条件模式基 {st['conditional_pattern_base']} 条，"
          f"递归构造条件 FP 树 {st['recursive_calls']} 次，"
          f"条件树结点累计 {st['conditional_tree_nodes']} 个")
    print(f"  频繁项集 {len(frequent)} 个，按长度分布 {by_len}")
    print(f"  总耗时 {res['total_time']:.3f}s（其中建树 {res['build_time']:.3f}s）")

    rows = sorted(frequent.items(), key=lambda kv: (-len(kv[0]), -kv[1], kv[0]))
    write_csv(RESULTS / "fpgrowth_frequent_itemsets.csv",
              ["itemset", "length", "count", "support"],
              [[" & ".join(k), len(k), v, f"{v / n:.6f}"] for k, v in rows])
    print("  频繁项集明细已写入 results/fpgrowth_frequent_itemsets.csv")

    top_multi = [kv for kv in rows if len(kv[0]) >= 2][:10]
    print("\n  支持度最高的 10 个多项集：")
    for k, v in top_multi:
        print(f"    {' & '.join(k):<58} 计数 {v:>5}  支持度 {v / n:.4f}")

    rules = generate_rules(frequent, n, min_confidence=MIN_CONFIDENCE)
    rules.sort(key=lambda r: (-r["lift"], -r["support"]))
    write_csv(RESULTS / "fpgrowth_rules.csv",
              ["antecedent", "consequent", "support", "confidence", "lift", "count"],
              [[" & ".join(r["antecedent"]), " & ".join(r["consequent"]),
                f"{r['support']:.6f}", f"{r['confidence']:.4f}", f"{r['lift']:.4f}",
                r["count"]] for r in rules])
    print(f"\n  置信度≥{MIN_CONFIDENCE} 的关联规则 {len(rules)} 条，提升度最高的 10 条：")
    for r in rules[:10]:
        print(f"    {' & '.join(r['antecedent'])} => {' & '.join(r['consequent'])}  "
              f"support={r['support']:.4f} confidence={r['confidence']:.4f} "
              f"lift={r['lift']:.4f}")

    # 与 DHP 导出的规则逐条比对（两个算法项集相同，规则也应完全相同）
    dhp_rules_file = RESULTS / "dhp_rules.csv"
    if dhp_rules_file.exists():
        with open(dhp_rules_file, encoding="utf-8-sig") as f:
            dhp_rules = {tuple(r["antecedent"].split(" & ")) + tuple(
                r["consequent"].split(" & ")): (r["support"], r["confidence"], r["lift"])
                for r in csv.DictReader(f)}
        mine = {tuple(r["antecedent"]) + tuple(r["consequent"]):
                (f"{r['support']:.6f}", f"{r['confidence']:.4f}", f"{r['lift']:.4f}")
                for r in rules}
        if dhp_rules == mine:
            print(f"  与实验二 DHP 导出的 {len(mine)} 条规则逐条比对：完全一致")
        else:
            print(f"  [警告] 与 DHP 的规则不一致：DHP {len(dhp_rules)} 条 / "
                  f"FP-Growth {len(mine)} 条")

    with open(RESULTS / "fpgrowth_main_result.json", "w", encoding="utf-8") as f:
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
            "build_time_s": res["build_time"],
            "tree": st,
            "compression_ratio": n / max(1, st["tree_nodes"]),
            "top_itemsets": [{"itemset": " & ".join(k), "count": v, "support": v / n}
                             for k, v in top_multi],
            "top_rules": [{"antecedent": " & ".join(r["antecedent"]),
                           "consequent": " & ".join(r["consequent"]),
                           "support": r["support"], "confidence": r["confidence"],
                           "lift": r["lift"]} for r in rules[:10]],
        }, f, ensure_ascii=False, indent=2)

    print(f"\n实验三完成，总耗时 {time.perf_counter() - t_start:.3f}s")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    t_start = time.perf_counter()
    main()
