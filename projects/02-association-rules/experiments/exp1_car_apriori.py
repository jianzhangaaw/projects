# -*- coding: utf-8 -*-
"""实验一：汽车评估数据库（car.data）的基本信息、预处理与 Apriori 频繁项集发现。

运行：python experiments/exp1_car_apriori.py
输出：results/car_basic_info.txt、results/car_support_scan.csv、
      results/car_frequent_itemsets.csv、results/car_rules.csv
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apriori import apriori                    # noqa: E402
from data_utils import (CAR_COLUMNS, CAR_LABELS, basic_info, format_info,  # noqa: E402
                        load_car, min_count_of)
from rules import generate_rules, itemset_stats  # noqa: E402

RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

MAIN_SUPPORT = 0.20          # 主实验支持度阈值
SCAN_SUPPORTS = [0.40, 0.30, 0.25, 0.20, 0.15, 0.10]
LOW_SUPPORT = 0.10           # 补充实验：降低支持度后出现的更长项集
MIN_CONFIDENCE = 0.70


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    transactions, raw_rows, labels = load_car()

    info = basic_info(transactions, "汽车评估数据库 car.data（属性=取值 编码）")
    lines = [
        "=" * 72,
        "一、数据基本信息与预处理",
        "=" * 72,
        f"原始文件：data/car.data，共 {len(raw_rows)} 行，每行 7 个字段（6 个条件属性 + 1 个类别属性）",
        f"字段：{', '.join(CAR_COLUMNS)}（中文含义："
        + "、".join(f"{c}={CAR_LABELS[c]}" for c in CAR_COLUMNS) + "）",
        "缺失值：无；重复记录：无（1728 行的 6 个条件属性组合互不相同）",
        "",
        "预处理做法：关联分析要求输入是事务-项集合。这里把每一行看作一条事务，",
        "把「属性=取值」拼成一个项（例如 buying=vhigh、safety=low），",
        "6 个条件属性构成 6 个项；类别属性 class 同样编码为 class=unacc 这类项，",
        "于是一条事务共 7 个项，以便挖掘「什么条件组合会导致某评估等级」的规则。",
        "编码后不同取值共 25 个，其中 23 个的出现次数达到主实验阈值。",
        "",
        format_info(info),
        "",
        "各属性取值分布：",
    ]
    print("\n".join(lines))

    for i, col in enumerate(CAR_COLUMNS):
        from collections import Counter
        vc = Counter(row[i] for row in raw_rows)
        line = f"  {col}({CAR_LABELS[col]}): " + ", ".join(f"{k}={v}" for k, v in sorted(vc.items()))
        print(line)
        lines.append(line)

    with open(RESULTS / "car_basic_info.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # ---------- 不同支持度下的 Apriori ----------
    print("\n" + "=" * 72)
    print("二、不同最小支持度下的 Apriori 挖掘结果")
    print("=" * 72)
    scan_rows = []
    for ms in SCAN_SUPPORTS:
        res = apriori(transactions, ms)
        by_len = itemset_stats(res["frequent"])
        scan_rows.append([
            f"{ms:.2f}", min_count_of(ms, len(transactions)), res["total_time"],
            len(res["frequent"]), sum(len(k) for k in res["frequent"]),
            by_len.get(1, 0), by_len.get(2, 0), by_len.get(3, 0), by_len.get(4, 0),
            by_len.get(5, 0), by_len.get(6, 0), max(by_len) if by_len else 0,
        ])
        print(f"  min_support={ms:.2f}（计数≥{min_count_of(ms, len(transactions))}）: "
              f"频繁项集 {len(res['frequent'])} 个，最长 "
              f"{max(by_len) if by_len else 0} 项，耗时 {res['total_time']:.3f}s")
    write_csv(RESULTS / "car_support_scan.csv",
              ["min_support", "min_count", "time_s", "n_frequent", "sum_len",
               "L1", "L2", "L3", "L4", "L5", "L6", "max_len"], scan_rows)

    # ---------- 主阈值下的详细结果 ----------
    print("\n" + "=" * 72)
    print(f"三、主实验：min_support={MAIN_SUPPORT} 的频繁项集与关联规则")
    print("=" * 72)
    res = apriori(transactions, MAIN_SUPPORT, verbose=True)
    frequent = res["frequent"]
    by_len = itemset_stats(frequent)
    print(f"  合计频繁项集 {len(frequent)} 个，按长度分布：{by_len}")
    print(f"  Apriori 逐层统计：")
    for st in res["stats"]:
        print(f"    k={st['k']}: 候选 {st['candidates']}，频繁 {st['frequent']}，"
              f"耗时 {st['time']:.3f}s")
    print(f"  挖掘耗时合计 {res['total_time']:.3f}s")

    rows = sorted(frequent.items(), key=lambda kv: (-len(kv[0]), -kv[1], kv[0]))
    write_csv(RESULTS / "car_frequent_itemsets.csv",
              ["itemset", "length", "count", "support"],
              [[" & ".join(k), len(k), v, f"{v / len(transactions):.4f}"] for k, v in rows])
    print(f"  频繁项集明细已写入 results/car_frequent_itemsets.csv")

    rules = generate_rules(frequent, len(transactions), min_confidence=MIN_CONFIDENCE)
    rules_by_class = [r for r in rules if r["consequent"] == ("class=unacc",)]
    rules_by_class.sort(key=lambda r: (-r["confidence"], -r["support"]))
    write_csv(RESULTS / "car_rules.csv",
              ["antecedent", "consequent", "support", "confidence", "lift", "count"],
              [[" & ".join(r["antecedent"]), " & ".join(r["consequent"]),
                f"{r['support']:.4f}", f"{r['confidence']:.4f}", f"{r['lift']:.4f}",
                r["count"]] for r in rules])
    print(f"  置信度≥{MIN_CONFIDENCE} 的关联规则 {len(rules)} 条，"
          f"其中后件为 class=unacc 的 {len(rules_by_class)} 条")

    print(f"\n  后件为 class=unacc 且置信度最高的 10 条规则：")
    for r in rules_by_class[:10]:
        print(f"    {' & '.join(r['antecedent'])} => class=unacc  "
              f"support={r['support']:.4f} confidence={r['confidence']:.4f} lift={r['lift']:.4f}")

    # 按后件汇总
    print("\n  按后件统计规则条数（置信度≥0.70）：")
    from collections import Counter
    cc = Counter(r["consequent"][0] for r in rules)
    for k, v in cc.most_common():
        print(f"    {k}: {v} 条")

    # ---------- 补充实验：降低支持度后的更长项集 ----------
    print("\n" + "=" * 72)
    print(f"四、补充实验：min_support={LOW_SUPPORT} 时出现了更长的项集")
    print("=" * 72)
    low = apriori(transactions, LOW_SUPPORT)
    low_by_len = itemset_stats(low["frequent"])
    print(f"  频繁项集 {len(low['frequent'])} 个，按长度分布 {low_by_len}，"
          f"耗时 {low['total_time']:.3f}s")
    long_itemsets = sorted(((k, v) for k, v in low["frequent"].items() if len(k) >= 3),
                           key=lambda kv: -kv[1])
    print(f"  长度≥3 的频繁项集 {len(long_itemsets)} 个，其中支持度最高的 8 个：")
    for k, v in long_itemsets[:8]:
        print(f"    {' & '.join(k):<55} 计数 {v:>4}  支持度 {v / len(transactions):.4f}")
    low_rules = generate_rules(low["frequent"], len(transactions), min_confidence=0.70)
    print(f"  该阈值下置信度≥0.70 的关联规则 {len(low_rules)} 条，"
          f"提升度最高的 6 条：")
    low_rules_by_lift = sorted(low_rules, key=lambda r: -r["lift"])
    for r in low_rules_by_lift[:6]:
        print(f"    {' & '.join(r['antecedent'])} => {' & '.join(r['consequent'])}  "
              f"support={r['support']:.4f} confidence={r['confidence']:.4f} "
              f"lift={r['lift']:.4f}")
    write_csv(RESULTS / "car_frequent_itemsets_low_support.csv",
              ["itemset", "length", "count", "support"],
              [[" & ".join(k), len(k), v, f"{v / len(transactions):.4f}"]
               for k, v in sorted(low["frequent"].items(),
                                  key=lambda kv: (-len(kv[0]), -kv[1], kv[0]))])
    write_csv(RESULTS / "car_rules_low_support.csv",
              ["antecedent", "consequent", "support", "confidence", "lift", "count"],
              [[" & ".join(r["antecedent"]), " & ".join(r["consequent"]),
                f"{r['support']:.4f}", f"{r['confidence']:.4f}", f"{r['lift']:.4f}",
                r["count"]] for r in low_rules_by_lift])

    summary = [
        f"数据集：car.data，{len(transactions)} 条事务，{info['n_items']} 个项",
        f"主实验最小支持度：{MAIN_SUPPORT}（计数≥{res['min_count']}），"
        f"最小置信度：{MIN_CONFIDENCE}",
        f"频繁项集：{len(frequent)} 个，按长度分布 {by_len}",
        f"关联规则：{len(rules)} 条",
        f"Apriori 耗时：{res['total_time']:.6f} s",
        "逐层统计：" + "; ".join(
            f"k={st['k']} 候选{st['candidates']}/频繁{st['frequent']}" for st in res["stats"]),
        f"补充实验 min_support={LOW_SUPPORT}：频繁项集 {len(low['frequent'])} 个，"
        f"按长度分布 {low_by_len}，规则 {len(low_rules)} 条（置信度≥0.70）",
    ]
    with open(RESULTS / "car_summary.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(summary) + "\n")

    # 供后续脚本与报告引用的机器可读结果
    import json
    with open(RESULTS / "car_main_result.json", "w", encoding="utf-8") as f:
        json.dump({
            "dataset": "car.data",
            "n_transactions": len(transactions),
            "n_items": info["n_items"],
            "min_support": MAIN_SUPPORT,
            "min_count": res["min_count"],
            "n_frequent": len(frequent),
            "itemset_by_len": {str(k): v for k, v in by_len.items()},
            "n_rules": len(rules),
            "min_confidence": MIN_CONFIDENCE,
            "time_s": res["total_time"],
            "layers": res["stats"],
            "top_rules_unacc": [
                {"antecedent": " & ".join(r["antecedent"]), "support": r["support"],
                 "confidence": r["confidence"], "lift": r["lift"]}
                for r in rules_by_class[:10]
            ],
            "all_rules": [
                {"antecedent": " & ".join(r["antecedent"]),
                 "consequent": " & ".join(r["consequent"]), "support": r["support"],
                 "confidence": r["confidence"], "lift": r["lift"]}
                for r in rules
            ],
            "low_support": {
                "min_support": LOW_SUPPORT,
                "n_frequent": len(low["frequent"]),
                "itemset_by_len": {str(k): v for k, v in low_by_len.items()},
                "n_rules": len(low_rules),
                "time_s": low["total_time"],
                "long_itemsets": [{"itemset": " & ".join(k), "count": v,
                                   "support": v / len(transactions)}
                                  for k, v in long_itemsets[:20]],
                "top_rules_by_lift": [
                    {"antecedent": " & ".join(r["antecedent"]),
                     "consequent": " & ".join(r["consequent"]), "support": r["support"],
                     "confidence": r["confidence"], "lift": r["lift"]}
                    for r in low_rules_by_lift[:10]
                ],
            },
        }, f, ensure_ascii=False, indent=2)

    t_end = time.perf_counter()
    print(f"\n实验一完成，总耗时 {t_end - t_start:.3f}s")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    t_start = time.perf_counter()
    main()
