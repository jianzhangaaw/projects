# -*- coding: utf-8 -*-
"""DHP（Direct Hashing and Pruning，直接哈希与修剪）算法的实现。

核心思想（相对 Apriori 的两处改进）：
1. 直接哈希：在统计频繁 1 项集的同时，把每条事务内部所有 2 项组合通过哈希函数
   映射到哈希表的一个桶里并累加桶计数。若某个桶的计数小于最小支持度计数，
   则该桶内所有 2 项集的计数一定更小，可以整桶删除，不必再逐个精确计数。
   桶计数可以反复用于第 3、4…… 层的候选裁剪（本轮扫描时顺便为下一层建表）。
2. 事务修剪：第 k 轮之后，把事务中不频繁的项删掉，并丢弃长度小于 k 的事务。
   事务只会变短，而变短的事务不会产生新的频繁项集，因此不会漏掉结果，
   但后续每轮需要处理的数据量显著减少。

计数口径与 Apriori 保持一致（tid 集合交集），以保证两种算法结果可比。
"""
from __future__ import annotations

import time
from collections import defaultdict

from apriori import (apriori_gen, build_tid_sets, count_candidates,  # noqa: F401
                     count_candidates_scan)


def hash_pair(i: int, j: int, n_items: int, n_buckets: int) -> int:
    """2 项集哈希函数：h({i,j}) = (i * n_items + j) mod B（i < j）。"""
    return (i * n_items + j) % n_buckets


def _hash_buckets_for_pairs(transactions, item_id, n_items, n_buckets, keep=None):
    """统计事务内部所有 2 项组合的桶计数。

    keep 为 None 时统计事务中的全部项；否则只统计 keep 里的项（用于已修剪事务）。
    """
    buckets = [0] * n_buckets
    for t in transactions:
        ids = [item_id[x] for x in t if keep is None or x in keep]
        ids.sort()
        m = len(ids)
        for a in range(m):
            ia = ids[a]
            base = ia * n_items
            for b in range(a + 1, m):
                buckets[(base + ids[b]) % n_buckets] += 1
    return buckets


def _hash_buckets_for_tuples(transactions, item_id, n_items, n_buckets, size, keep=None):
    """统计事务内部所有 size 项组合的桶计数（size >= 3）。"""
    from itertools import combinations

    buckets = [0] * n_buckets
    for t in transactions:
        ids = sorted(item_id[x] for x in t if keep is None or x in keep)
        if len(ids) < size:
            continue
        for combo in combinations(ids, size):
            h = 0
            for c in combo:
                h = (h * n_items + c) % n_buckets
            buckets[h] += 1
    return buckets


def _hash_key(itemset, item_id, n_items, n_buckets):
    """按项编号计算项集的哈希桶下标，与建表时的哈希函数保持一致。"""
    h = 0
    for c in itemset:
        h = (h * n_items + item_id[c]) % n_buckets
    return h


def dhp(transactions, min_support: float, n_buckets: int = 3000, max_len=None,
        verbose=False, count_mode: str = "tid"):
    """DHP 主过程。返回 frequent / stats / hash_info / total_time。

    count_mode="tid"  用 tid 集合交集计数（默认）；
    count_mode="scan" 在**已修剪的事务**上逐条扫描计数——事务修剪带来的收益
                      只有在扫描式计数下才体现得出来。
    """
    n = len(transactions)
    min_count = max(1, int(-(-min_support * n // 1)))

    t0 = time.perf_counter()
    items = sorted({x for t in transactions for x in t})
    item_id = {x: i for i, x in enumerate(items)}
    n_items = len(items)

    item_tids = build_tid_sets(transactions)

    # ---- 第 1 轮：统计 1 项集，同时为 2 项集建立哈希表 ----
    L1 = {}
    for item, s in item_tids.items():
        if len(s) >= min_count:
            L1[(item,)] = len(s)
    t_scan1 = time.perf_counter() - t0

    buckets2 = _hash_buckets_for_pairs(transactions, item_id, n_items, n_buckets)
    t_hash1 = time.perf_counter() - t0 - t_scan1

    frequent = dict(L1)
    # C2 全量候选 = 频繁 1 项集两两组合；DHP 用桶计数把它们裁剪一遍
    l1_items = sorted(L1.keys())
    full_pairs = []
    for a in range(len(l1_items)):
        ia = item_id[l1_items[a][0]]
        for b in range(a + 1, len(l1_items)):
            ib = item_id[l1_items[b][0]]
            full_pairs.append((l1_items[a][0], l1_items[b][0], (ia * n_items + ib) % n_buckets))

    c2 = [tuple(sorted((x, y))) for x, y, h in full_pairs if buckets2[h] >= min_count]
    hash_pruned_2 = len(full_pairs) - len(c2)

    stats = [{
        "k": 1,
        "candidates": len(items),
        "frequent": len(L1),
        "time": t_scan1 + t_hash1,
        "hash_pruned": 0,
    }]
    if verbose:
        print(f"  k=1 候选 {len(items):>7} 频繁 {len(L1):>6} 耗时 {stats[-1]['time']:.3f}s"
              f"（含 2 项集哈希表构建 {t_hash1:.3f}s）")

    # 事务修剪：第 1 轮后先删掉事务中不频繁的项
    l1_set = {x for (x,) in L1}
    kept_transactions = []
    removed_items = 0
    for t in transactions:
        kept = frozenset(x for x in t if x in l1_set)
        removed_items += len(t) - len(kept)
        if len(kept) >= 2:
            kept_transactions.append(kept)

    # ---- 第 2 轮：精确计数 C2 ----
    t_start = time.perf_counter()
    if count_mode == "tid":
        L2 = count_candidates(c2, item_tids, min_count)
    else:
        L2 = count_candidates_scan(c2, kept_transactions, min_count)
    t_scan2 = time.perf_counter() - t_start
    stats.append({
        "k": 2,
        "candidates": len(c2),
        "frequent": len(L2),
        "time": t_scan2,
        "hash_pruned": hash_pruned_2,
    })
    if verbose:
        print(f"  k=2 候选 {len(c2):>7}（哈希裁剪掉 {hash_pruned_2}）频繁 {len(L2):>6} "
              f"耗时 {t_scan2:.3f}s")
    frequent.update(L2)

    # 为第 3 层构建 3 项集哈希表（在已修剪事务上进行）
    buckets3 = _hash_buckets_for_tuples(kept_transactions, item_id, n_items,
                                        n_buckets, 3)

    prev = set(L2.keys())
    k = 3
    while prev and (max_len is None or k <= max_len):
        t_start = time.perf_counter()
        candidates = apriori_gen(prev, k)
        # 用上一轮建立的 k 项集哈希表裁剪候选
        if k == 3:
            table = buckets3
        else:
            table = _hash_buckets_for_tuples(kept_transactions, item_id, n_items,
                                             n_buckets, k)
        pruned = {c for c in candidates
                  if table[_hash_key(c, item_id, n_items, n_buckets)] >= min_count}
        n_pruned = len(candidates) - len(pruned)

        if count_mode == "tid":
            Lk = count_candidates(pruned, item_tids, min_count)
        else:
            Lk = count_candidates_scan(pruned, kept_transactions, min_count)
        elapsed = time.perf_counter() - t_start
        stats.append({
            "k": k,
            "candidates": len(pruned),
            "frequent": len(Lk),
            "time": elapsed,
            "hash_pruned": n_pruned,
        })
        if verbose:
            print(f"  k={k} 候选 {len(pruned):>7}（哈希裁剪掉 {n_pruned}）频繁 {len(Lk):>6} "
                  f"耗时 {elapsed:.3f}s")
        if not Lk:
            break
        frequent.update(Lk)
        # 事务修剪：保留含 k+1 个频繁项的事务，为下一层哈希表做准备
        lk_items = {x for itemset in Lk for x in itemset}
        new_kept = []
        for t in kept_transactions:
            kept = frozenset(x for x in t if x in lk_items)
            if len(kept) >= k + 1:
                new_kept.append(kept)
        kept_transactions = new_kept
        buckets3 = _hash_buckets_for_tuples(kept_transactions, item_id, n_items,
                                            n_buckets, k + 1)
        prev = set(Lk.keys())
        k += 1

    total = time.perf_counter() - t0
    return {
        "frequent": frequent,
        "stats": stats,
        "total_time": total,
        "min_count": min_count,
        "n_transactions": n,
        "min_support": min_support,
        "hash_info": {
            "n_buckets": n_buckets,
            "full_c2": len(full_pairs),
            "c2_after_hash": len(c2),
            "hash_pruned_2": hash_pruned_2,
            "items_removed_by_pruning": removed_items,
            "transactions_after_pruning": len(kept_transactions),
        },
    }
