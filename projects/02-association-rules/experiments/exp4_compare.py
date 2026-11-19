# -*- coding: utf-8 -*-
"""实验四：Apriori、DHP、FP-Growth 三种算法的效率对比。

对比分三部分：
  1) 同一数据集（groceries.csv）上，随最小支持度下降，三种算法的耗时、
     候选数、频繁项集数如何变化；
  2) 数据规模放大（把 9835 条事务按行重复 1/2/4/8 倍）后，三种算法的耗时增长；
  3) 逐层候选数对比：Apriori 的候选生成与 DHP 的哈希裁剪差异。
每个配置重复运行 3 次，取最短耗时（避免操作系统调度抖动）。

运行：python experiments/exp4_compare.py
输出：results/compare_support_scan.csv、results/compare_scale_scan.csv、
      results/compare_layers.csv、results/compare_result.json
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apriori import apriori                      # noqa: E402
from data_utils import load_car, load_groceries  # noqa: E402
from dhp import dhp                              # noqa: E402
from fpgrowth import fpgrowth                    # noqa: E402
from rules import itemset_stats                  # noqa: E402

RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
REPEAT = 3


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def timed(fn, repeat=REPEAT):
    """重复运行取最短耗时，同时返回最后一次的结果。"""
    best = None
    result = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        result = fn()
        dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
    return best, result


def main():
    groc = load_groceries()
    n = len(groc)
    report = {}

    # ---------- 1) 支持度扫描 ----------
    print("=" * 78)
    print("一、同一数据集上随最小支持度变化的耗时对比（每个配置重复 3 次取最短）")
    print("=" * 78)
    print(f"{'min_sup':>8} {'计数':>5} | {'Apriori':>9} {'DHP':>9} {'FP-Growth':>10} | "
          f"{'候选总数':>8} {'DHP候选':>8} | {'频繁项集':>8}")
    rows = []
    for ms in [0.02, 0.015, 0.012, 0.01, 0.008, 0.006]:
        t_ap, r_ap = timed(lambda: apriori(groc, ms))
        t_dh, r_dh = timed(lambda: dhp(groc, ms, n_buckets=3000))
        t_fp, r_fp = timed(lambda: fpgrowth(groc, ms))
        assert r_ap["frequent"] == r_dh["frequent"] == r_fp["frequent"], \
            f"min_support={ms} 时三种算法结果不一致"
        cand_ap = sum(s["candidates"] for s in r_ap["stats"])
        cand_dh = sum(s["candidates"] for s in r_dh["stats"])
        rows.append([ms, r_ap["min_count"], t_ap, t_dh, t_fp, cand_ap, cand_dh,
                     len(r_ap["frequent"]), t_ap / t_fp, t_dh / t_fp])
        print(f"{ms:>8.3f} {r_ap['min_count']:>5} | {t_ap:>9.4f} {t_dh:>9.4f} "
              f"{t_fp:>10.4f} | {cand_ap:>8} {cand_dh:>8} | {len(r_ap['frequent']):>8}",
              flush=True)
    write_csv(RESULTS / "compare_support_scan.csv",
              ["min_support", "min_count", "apriori_time_s", "dhp_time_s",
               "fpgrowth_time_s", "apriori_candidates_total", "dhp_candidates_total",
               "n_frequent", "apriori_over_fpgrowth", "dhp_over_fpgrowth"], rows)
    report["support_scan"] = rows

    # ---------- 2) 数据规模放大 ----------
    print("\n" + "=" * 78)
    print("二、数据规模放大后的耗时（把事务表按行重复 1/2/4/8 倍，min_support=0.01）")
    print("=" * 78)
    scale_rows = []
    for mult in [1, 2, 4, 8]:
        data = groc * mult
        t_ap, r_ap = timed(lambda: apriori(data, 0.01), repeat=2)
        t_dh, r_dh = timed(lambda: dhp(data, 0.01, n_buckets=3000), repeat=2)
        t_fp, r_fp = timed(lambda: fpgrowth(data, 0.01), repeat=2)
        assert r_ap["frequent"] == r_dh["frequent"] == r_fp["frequent"]
        scale_rows.append([len(data), mult, t_ap, t_dh, t_fp,
                           sum(s["candidates"] for s in r_ap["stats"]),
                           sum(s["candidates"] for s in r_dh["stats"]),
                           len(r_ap["frequent"])])
        print(f"  事务数 {len(data):>6}（×{mult}）: Apriori {t_ap:.3f}s / "
              f"DHP {t_dh:.3f}s / FP-Growth {t_fp:.3f}s；频繁项集 "
              f"{len(r_ap['frequent'])} 个", flush=True)
    write_csv(RESULTS / "compare_scale_scan.csv",
              ["n_transactions", "multiplier", "apriori_time_s", "dhp_time_s",
               "fpgrowth_time_s", "apriori_candidates_total", "dhp_candidates_total",
               "n_frequent"], scale_rows)
    report["scale_scan"] = scale_rows

    # ---------- 3) 逐层候选数对比（min_support=0.01） ----------
    print("\n" + "=" * 78)
    print("三、逐层候选数对比（groceries.csv，min_support=0.01）")
    print("=" * 78)
    r_ap = apriori(groc, 0.01)
    r_dh = dhp(groc, 0.01, n_buckets=3000)
    layer_rows = []
    for s_ap in r_ap["stats"]:
        k = s_ap["k"]
        s_dh = next((s for s in r_dh["stats"] if s["k"] == k), None)
        layer_rows.append([k, s_ap["candidates"], s_ap["frequent"],
                           s_dh["candidates"] if s_dh else None,
                           s_dh["frequent"] if s_dh else None,
                           s_dh["hash_pruned"] if s_dh else None])
        print(f"  k={k}: Apriori 候选 {s_ap['candidates']:>6} 频繁 {s_ap['frequent']:>5} | "
              f"DHP 候选 {s_dh['candidates'] if s_dh else '-':>6} "
              f"频繁 {s_dh['frequent'] if s_dh else '-':>5} "
              f"哈希额外裁剪 {s_dh['hash_pruned'] if s_dh else '-'}")
    write_csv(RESULTS / "compare_layers.csv",
              ["k", "apriori_candidates", "apriori_frequent", "dhp_candidates",
               "dhp_frequent", "dhp_hash_pruned"], layer_rows)
    report["layers"] = layer_rows

    # ---------- 4) 汽车评估数据库上的对比（小数据、稠密） ----------
    print("\n" + "=" * 78)
    print("四、汽车评估数据库（1728 条事务、25 个项）上的耗时对比")
    print("=" * 78)
    car, _, _ = load_car()
    car_rows = []
    for ms in [0.20, 0.15, 0.10]:
        t_ap, r_ap = timed(lambda: apriori(car, ms))
        t_dh, r_dh = timed(lambda: dhp(car, ms, n_buckets=300))
        t_fp, r_fp = timed(lambda: fpgrowth(car, ms))
        assert r_ap["frequent"] == r_dh["frequent"] == r_fp["frequent"]
        by_len = itemset_stats(r_ap["frequent"])
        car_rows.append([ms, len(car), t_ap, t_dh, t_fp, len(r_ap["frequent"]),
                         max(by_len), r_dh["hash_info"]["full_c2"],
                         r_dh["hash_info"]["c2_after_hash"]])
        print(f"  min_support={ms:.2f}: Apriori {t_ap * 1000:.3f}ms / "
              f"DHP {t_dh * 1000:.3f}ms / FP-Growth {t_fp * 1000:.3f}ms；"
              f"频繁项集 {len(r_ap['frequent'])} 个；DHP C2 {r_dh['hash_info']['full_c2']}"
              f"→{r_dh['hash_info']['c2_after_hash']}", flush=True)
    write_csv(RESULTS / "compare_car.csv",
              ["min_support", "n_transactions", "apriori_time_s", "dhp_time_s",
               "fpgrowth_time_s", "n_frequent", "max_len", "dhp_c2_full",
               "dhp_c2_after_hash"], car_rows)
    report["car"] = car_rows

    # ---------- 5) 换成"逐条扫描事务计数"的实现后 DHP 的收益 ----------
    print("\n" + "=" * 78)
    print("五、换成逐条扫描事务计数的实现：Apriori 与 DHP 的耗时（候选个数决定工作量）")
    print("=" * 78)
    scan_rows = []
    for ms in [0.02, 0.01]:
        t_ap, r_ap = timed(lambda: apriori(groc, ms, count_mode="scan"), repeat=2)
        t_dh, r_dh = timed(lambda: dhp(groc, ms, n_buckets=3000, count_mode="scan"),
                           repeat=2)
        assert r_ap["frequent"] == r_dh["frequent"], f"min_support={ms} 结果不一致"
        cand_ap = sum(s["candidates"] for s in r_ap["stats"])
        cand_dh = sum(s["candidates"] for s in r_dh["stats"])
        scan_rows.append([ms, t_ap, t_dh, cand_ap, cand_dh, t_ap / t_dh,
                          len(r_ap["frequent"])])
        print(f"  min_support={ms:.3f}: Apriori(扫描) {t_ap:.3f}s，候选合计 {cand_ap} 个；"
              f"DHP(扫描) {t_dh:.3f}s，候选合计 {cand_dh} 个；"
              f"DHP 快 {t_ap / t_dh:.2f} 倍", flush=True)
    write_csv(RESULTS / "compare_scan_mode.csv",
              ["min_support", "apriori_scan_time_s", "dhp_scan_time_s",
               "apriori_candidates_total", "dhp_candidates_total", "speedup",
               "n_frequent"], scan_rows)
    report["scan_mode"] = scan_rows

    with open(RESULTS / "compare_result.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n实验四完成，总耗时 {time.perf_counter() - t_start:.3f}s")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    t_start = time.perf_counter()
    main()
