# -*- coding: utf-8 -*-
"""算法正确性校验：把 Apriori、DHP、FP-Growth 的结果与暴力枚举结果逐一比对。

暴力枚举的口径：对每个项集，直接遍历全部事务统计包含它的事务数，
计数 >= 最小支持度计数的项集即为频繁项集。这是最朴素也最不容易出错的判据，
三种算法的结果必须与它完全一致（项集集合完全相同、计数也完全相同）。
"""
from __future__ import annotations

import random
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apriori import apriori                      # noqa: E402
from data_utils import load_car, load_groceries  # noqa: E402
from dhp import dhp                              # noqa: E402
from fpgrowth import fpgrowth                    # noqa: E402


def brute_force(transactions, min_support, max_k=None):
    """暴力核对：直接枚举每条事务的所有非空子集并累加计数。

    这个口径不依赖任何"先验性质"或候选生成逻辑，是独立于三种算法的第二把尺子。
    max_k 限制枚举的子集长度上限，用于项数很多的数据集（超过上限的频繁项集
    由调用方检查并报告为"核对范围不足"）。
    """
    n = len(transactions)
    min_count = max(1, int(-(-min_support * n // 1)))
    counts = Counter()
    for t in transactions:
        items = sorted(t)
        top = len(items) if max_k is None else min(max_k, len(items))
        for k in range(1, top + 1):
            for combo in combinations(items, k):
                counts[combo] += 1
    return {c: v for c, v in counts.items() if v >= min_count}


def compare(name, transactions, min_support, check_dhp=True, max_k=None):
    expect = brute_force(transactions, min_support, max_k=max_k)
    expect_max_len = max((len(k) for k in expect), default=0)
    ap = apriori(transactions, min_support)["frequent"]
    fp = fpgrowth(transactions, min_support)["frequent"]
    got = {"Apriori": ap, "FP-Growth": fp}
    if check_dhp:
        got["DHP"] = dhp(transactions, min_support)["frequent"]
    ok = True
    algo_max_len = max((len(k) for k in ap), default=0)
    if max_k is not None and algo_max_len > expect_max_len:
        ok = False
        print(f"  [INCOMPLETE] {name}：Apriori 结果中存在长度 {algo_max_len} 的频繁项集，"
              f"超过暴力核对的长度上限 {expect_max_len}，核对范围不足")
    for algo, res in got.items():
        if res != expect:
            ok = False
            missing = set(expect) - set(res)
            extra = set(res) - set(expect)
            diff_cnt = {k for k in set(expect) & set(res) if expect[k] != res[k]}
            print(f"  [FAIL] {name} / {algo}: 缺失 {len(missing)} 多余 {len(extra)} "
                  f"计数不一致 {len(diff_cnt)}")
            if missing:
                print("         缺失示例:", list(missing)[:3])
            if extra:
                print("         多余示例:", list(extra)[:3])
            if diff_cnt:
                k = list(diff_cnt)[0]
                print(f"         计数不一致示例: {k} 期望 {expect[k]} 实际 {res[k]}")
    if ok:
        print(f"  [PASS] {name}（阈值 {min_support}）：频繁项集 {len(expect)} 个"
              f"（最长 {expect_max_len} 项），三种算法与暴力枚举完全一致", flush=True)
    return ok


def make_random_transactions(seed, n_trx, n_items, max_len):
    rng = random.Random(seed)
    pool = [f"i{x}" for x in range(n_items)]
    trx = []
    for _ in range(n_trx):
        k = rng.randint(1, max_len)
        trx.append(frozenset(rng.sample(pool, k)))
    return trx


def main():
    all_ok = True

    # 1) 手工小样本：能人工核对的规模
    toy = [
        frozenset("abc"), frozenset("abd"), frozenset("acd"),
        frozenset("abcd"), frozenset("bc"), frozenset("ab"),
    ]
    print("[1] 手工小样本", flush=True)
    all_ok &= compare("手工小样本", toy, 0.3)

    # 2) 随机数据，不同规模与阈值
    print("[2] 随机数据", flush=True)
    for seed, n_trx, n_items, max_len in [(1, 40, 8, 4), (2, 60, 10, 5), (3, 120, 12, 6)]:
        trx = make_random_transactions(seed, n_trx, n_items, max_len)
        for ms in (0.1, 0.2):
            all_ok &= compare(f"随机数据 seed={seed} n={n_trx}", trx, ms)

    # 3) 汽车评估数据库：项少、事务短，可以全量暴力核对
    print("[3] 汽车评估数据库", flush=True)
    car, _, _ = load_car()
    for ms in (0.25, 0.20):
        all_ok &= compare("汽车评估数据库", car, ms, check_dhp=True)

    # 4) DHP 哈希桶数变化不应影响结果
    print("[4] DHP 不同哈希桶数", flush=True)
    ap = apriori(car, 0.25)["frequent"]
    for B in (17, 101, 1000, 5000):
        r = dhp(car, 0.25, n_buckets=B)["frequent"]
        if r != ap:
            all_ok = False
            print(f"  [FAIL] DHP 桶数 B={B} 结果与 Apriori 不一致")
        else:
            print(f"  [PASS] DHP 桶数 B={B}：结果与 Apriori 一致", flush=True)

    # 5) 商品数据库：事务较长，暴力核对限制在 4 项集以内
    print("[5] 商品购买记录数据库", flush=True)
    groc = load_groceries()
    all_ok &= compare("商品购买记录数据库", groc, 0.06, max_k=4)

    # 6) 两种计数方式（tid 交集 / 逐条扫描）结果必须一致
    print("[6] 两种计数方式的一致性", flush=True)
    a_tid = apriori(groc, 0.02)["frequent"]
    a_scan = apriori(groc, 0.02, count_mode="scan")["frequent"]
    d_tid = dhp(groc, 0.02)["frequent"]
    d_scan = dhp(groc, 0.02, count_mode="scan")["frequent"]
    for label, a, b in [("Apriori tid vs scan", a_tid, a_scan),
                        ("DHP tid vs scan", d_tid, d_scan),
                        ("Apriori vs DHP（scan）", a_scan, d_scan)]:
        if a != b:
            all_ok = False
            print(f"  [FAIL] {label}：不一致")
        else:
            print(f"  [PASS] {label}：{len(a)} 个频繁项集完全一致", flush=True)

    print("\n全部校验通过" if all_ok else "\n存在不一致，需要检查")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
