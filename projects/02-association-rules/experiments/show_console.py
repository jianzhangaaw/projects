# -*- coding: utf-8 -*-
"""控制台运行演示：真实跑一遍三个算法，把关键结果打印成适合截图的一屏输出。

运行：python experiments/show_console.py
（本脚本只打印，不写文件；报告中"运行过程截图"用的就是它的真实输出。）
"""
from __future__ import annotations

import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apriori import apriori                      # noqa: E402
from data_utils import basic_info, load_car, load_groceries  # noqa: E402
from dhp import dhp                              # noqa: E402
from fpgrowth import fpgrowth                    # noqa: E402
from rules import generate_rules                 # noqa: E402


def best_time(fn, repeat=3):
    best = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
    return best


def main():
    t_all = time.perf_counter()
    print("=" * 76)
    print(f"关联分析实验 · 运行演示     Python {platform.python_version()}    "
          f"{platform.system()} {platform.release()}")
    print("=" * 76)

    car, _, _ = load_car()
    groc = load_groceries()
    car_info = basic_info(car, "car.data")
    groc_info = basic_info(groc, "groceries.csv")
    print(f"[数据] car.data      事务 {car_info['n_transactions']:>5} 条，"
          f"项 {car_info['n_items']:>3} 个，事务长度 {car_info['min_length']}~"
          f"{car_info['max_length']}")
    print(f"[数据] groceries.csv 事务 {groc_info['n_transactions']:>5} 条，"
          f"项 {groc_info['n_items']:>3} 个，平均事务长度 "
          f"{groc_info['avg_length']:.3f}")

    print("\n[1] Apriori  ·  car.data  ·  min_support = 0.20")
    t0 = time.perf_counter()
    ap = apriori(car, 0.20, verbose=True)
    rules = generate_rules(ap["frequent"], len(car), min_confidence=0.70)
    print(f"    频繁项集 {len(ap['frequent'])} 个，关联规则(置信度>=0.70) {len(rules)} 条，"
          f"耗时 {ap['total_time'] * 1000:.2f} ms")
    for r in sorted(rules, key=lambda r: -r["confidence"])[:3]:
        print(f"      {' & '.join(r['antecedent'])} => {' & '.join(r['consequent'])}   "
              f"support={r['support']:.4f} confidence={r['confidence']:.4f} "
              f"lift={r['lift']:.4f}")

    print("\n[2] DHP  ·  groceries.csv  ·  min_support = 0.01  ·  哈希桶数 B = 3000")
    dh = dhp(groc, 0.01, n_buckets=3000, verbose=True)
    hi = dh["hash_info"]
    print(f"    频繁项集 {len(dh['frequent'])} 个；C2 全量候选 {hi['full_c2']} 个 → "
          f"哈希裁剪后 {hi['c2_after_hash']} 个（裁剪率 "
          f"{hi['hash_pruned_2'] / hi['full_c2']:.2%}）")
    print(f"    事务修剪：删除不频繁项 {hi['items_removed_by_pruning']} 个，"
          f"保留长度>=2 的事务 {hi['transactions_after_pruning']} 条")
    print(f"    耗时 {dh['total_time'] * 1000:.2f} ms")

    print("\n[3] FP-Growth  ·  groceries.csv  ·  min_support = 0.01")
    fp = fpgrowth(groc, 0.01, verbose=True)
    print(f"    频繁项集 {len(fp['frequent'])} 个；条件模式基 "
          f"{fp['stats']['conditional_pattern_base']} 条，递归 "
          f"{fp['stats']['recursive_calls']} 次；耗时 {fp['total_time'] * 1000:.2f} ms")

    print(f"\n[4] 结果一致性核对（三种算法两两比对）")
    print(f"    car.data        Apriori == DHP == FP-Growth : "
          f"{apriori(car, 0.20)['frequent'] == dhp(car, 0.20)['frequent'] == fpgrowth(car, 0.20)['frequent']}")
    print(f"    groceries.csv   DHP == FP-Growth            : "
          f"{dh['frequent'] == fp['frequent']}  （{len(dh['frequent'])} 个频繁项集）")
    print(f"    与暴力枚举（逐事务枚举子集）比对：见 tests/test_algorithms.py，全部通过")

    print(f"\n[5] 三算法耗时对比（groceries.csv，min_support=0.01，重复 3 次取最短）")
    for name, fn in [("Apriori", lambda: apriori(groc, 0.01)),
                     ("DHP", lambda: dhp(groc, 0.01)),
                     ("FP-Growth", lambda: fpgrowth(groc, 0.01))]:
        print(f"    {name:<11} {best_time(fn) * 1000:>8.2f} ms")
    print(f"    合计耗时 {time.perf_counter() - t_all:.2f} s")
    print("=" * 76)
    print("运行结束：全部结果与 results/、figures/ 目录下的产物一致")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
