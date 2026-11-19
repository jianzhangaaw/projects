# -*- coding: utf-8 -*-
"""Apriori 算法的实现。

基本思想：频繁项集的所有子集都必须是频繁的，因此可以用第 k-1 层的频繁项集
连接产生第 k 层候选，再用「所有 k-1 子集都频繁」这一先验性质剪枝。

计数方式：把每个项映射成整数编号，并为每个项保存包含它的事务编号集合（tid 集），
则候选项集 {a,b,c} 的支持度计数 = tid(a) ∩ tid(b) ∩ tid(c) 的元素个数。
这与逐条扫描事务逐层计数的结果完全等价，但省去了对无效事务的重复扫描。
"""
from __future__ import annotations

import time
from collections import defaultdict


def build_tid_sets(transactions):
    """把事务集合转换成「项 -> 事务编号集合」的倒排结构，同时统计 1 项集计数。"""
    tids = defaultdict(set)
    for tid, t in enumerate(transactions):
        for item in t:
            tids[item].add(tid)
    return tids


def apriori_gen(prev_freq: set, k: int) -> set:
    """由第 k-1 层频繁项集生成第 k 层候选（连接 + 剪枝）。

    prev_freq 中的每个元素是升序 tuple，长度 k-1。
    连接：前缀相同、最后一个项不同的两个项集连接；
    剪枝：候选的任意 k-1 子集若不在频繁项集中，则该候选一定不频繁，直接删除。
    """
    by_prefix = defaultdict(list)
    for itemset in prev_freq:
        by_prefix[itemset[:-1]].append(itemset[-1])

    candidates = set()
    for prefix, lasts in by_prefix.items():
        if len(lasts) < 2:
            continue
        lasts.sort()
        for i in range(len(lasts)):
            for j in range(i + 1, len(lasts)):
                cand = prefix + (lasts[i], lasts[j])
                ok = True
                for skip in range(k - 1):
                    sub = cand[:skip] + cand[skip + 1:]
                    if sub not in prev_freq:
                        ok = False
                        break
                if ok:
                    candidates.add(cand)
    return candidates


def count_candidates(candidates, item_tids, min_count):
    """用 tid 集合交集统计每个候选项集的支持度计数，返回频繁项集字典。"""
    frequent = {}
    for cand in candidates:
        sets = [item_tids[i] for i in cand]
        sets.sort(key=len)
        inter = sets[0]
        for s in sets[1:]:
            inter = inter & s
            if len(inter) < min_count:
                break
        c = len(inter)
        if c >= min_count:
            frequent[cand] = c
        # 提前跳出时 c 表示交集大小上界，不影响"是否频繁"的判断
    return frequent


def count_candidates_scan(candidates, transactions, min_count):
    """经典的逐条扫描事务计数：对每个候选检查每条事务是否包含它。

    候选数 × 事务数 就是这层的工作量，因此候选个数直接决定耗时，
    这正是 DHP 用哈希表裁剪候选能够生效的场景。
    """
    frequent = {}
    for cand in candidates:
        cset = set(cand)
        c = 0
        for t in transactions:
            if cset <= t:
                c += 1
        if c >= min_count:
            frequent[cand] = c
    return frequent


def apriori(transactions, min_support: float, max_len=None, verbose=False,
            count_mode: str = "tid"):
    """Apriori 主过程。

    count_mode="tid"  用 tid 集合交集计数（默认，垂直格式，速度更快）；
    count_mode="scan" 逐条扫描事务计数（经典实现，候选个数直接决定耗时）。

    返回 dict：frequent（项集 tuple -> 计数）、stats（逐层候选数/频繁数/耗时）、
    total_time（挖掘频繁项集耗时，不含数据准备）。
    """
    n = len(transactions)
    min_count = max(1, int(-(-min_support * n // 1)))

    t0 = time.perf_counter()
    item_tids = build_tid_sets(transactions)

    def count(cands):
        if count_mode == "tid":
            return count_candidates(cands, item_tids, min_count)
        return count_candidates_scan(cands, transactions, min_count)

    # 第 1 层：直接统计单项计数
    L1 = {}
    for item, s in item_tids.items():
        if len(s) >= min_count:
            L1[(item,)] = len(s)
    frequent = dict(L1)
    stats = [{
        "k": 1,
        "candidates": len(item_tids),
        "frequent": len(L1),
        "time": time.perf_counter() - t0,
    }]
    if verbose:
        print(f"  k=1 候选 {len(item_tids):>7} 频繁 {len(L1):>6} "
              f"耗时 {stats[-1]['time']:.3f}s")

    prev = set(L1.keys())
    k = 2
    while prev and (max_len is None or k <= max_len):
        t_start = time.perf_counter()
        candidates = apriori_gen(prev, k)
        if not candidates:
            break
        Lk = count(candidates)
        elapsed = time.perf_counter() - t_start
        stats.append({
            "k": k,
            "candidates": len(candidates),
            "frequent": len(Lk),
            "time": elapsed,
        })
        if verbose:
            print(f"  k={k} 候选 {len(candidates):>7} 频繁 {len(Lk):>6} "
                  f"耗时 {elapsed:.3f}s")
        if not Lk:
            break
        frequent.update(Lk)
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
    }
