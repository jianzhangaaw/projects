# -*- coding: utf-8 -*-
"""FP-Growth（频繁模式增长）算法的实现。

基本思想：把事务数据库压缩成一棵 FP 树（前缀树），树上每个结点记录经过它的
事务数，因此相同前缀只存一份；再从"条件模式基"出发递归地为每个频繁项构造
条件 FP 树并继续挖掘。整个过程只扫描数据库两次，且不需要产生候选项集。
"""
from __future__ import annotations

import time
from collections import Counter


class FPNode:
    __slots__ = ("name", "count", "parent", "children", "link")

    def __init__(self, name, count, parent):
        self.name = name
        self.count = count
        self.parent = parent
        self.children = {}
        self.link = None  # 指向同名结点的链表后一项


def _insert(node, items, count, header):
    for item in items:
        child = node.children.get(item)
        if child is None:
            child = FPNode(item, 0, node)
            node.children[item] = child
            # 挂到同名链表的尾部
            if header[item] is None:
                header[item] = child
            else:
                cur = header[item]
                while cur.link is not None:
                    cur = cur.link
                cur.link = child
        child.count += count
        node = child


def _build_tree(transactions, min_count):
    counts = Counter()
    for t in transactions:
        counts.update(t)
    freq = {i: c for i, c in counts.items() if c >= min_count}
    order = {item: rank for rank, (item, _) in
             enumerate(sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])))}
    root = FPNode(None, 0, None)
    header = {item: None for item in freq}
    for t in transactions:
        items = sorted((x for x in t if x in freq), key=lambda x: order[x])
        if items:
            _insert(root, items, 1, header)
    return root, header, freq, order


def _mine(header, support, prefix, min_count, patterns, stats, max_len=None):
    """递归挖掘：按支持度升序枚举后缀项，构造条件 FP 树后继续递归。"""
    for item in sorted(header.keys(), key=lambda x: (support[x], x)):
        new_prefix = prefix + (item,)
        patterns[new_prefix] = support[item]

        # 1) 收集条件模式基：从 item 的结点链上溯到根，得到各条前缀路径及其计数
        cond_paths = []
        node = header[item]
        while node is not None:
            path = []
            p = node.parent
            while p is not None and p.name is not None:
                path.append(p.name)
                p = p.parent
            if path:
                cond_paths.append((path, node.count))
            node = node.link
        stats["conditional_pattern_base"] += len(cond_paths)
        if not cond_paths:
            continue
        if max_len is not None and len(new_prefix) >= max_len:
            continue

        # 2) 在条件模式基上重新统计，得到条件频繁项
        cond_counts = Counter()
        for path, cnt in cond_paths:
            for x in path:
                cond_counts[x] += cnt
        cond_freq = {x: c for x, c in cond_counts.items() if c >= min_count}
        if not cond_freq:
            continue

        # 3) 构造条件 FP 树并递归
        order = {x: r for r, (x, _) in
                 enumerate(sorted(cond_freq.items(), key=lambda kv: (-kv[1], kv[0])))}
        cond_root = FPNode(None, 0, None)
        cond_header = {x: None for x in cond_freq}
        for path, cnt in cond_paths:
            items = sorted((x for x in path if x in cond_freq), key=lambda x: order[x])
            if items:
                _insert(cond_root, items, cnt, cond_header)
        stats["recursive_calls"] += 1
        stats["conditional_tree_nodes"] += _count_nodes(cond_root) - 1
        _mine(cond_header, cond_freq, new_prefix, min_count, patterns, stats, max_len)


def _count_nodes(node):
    total = 1
    for child in node.children.values():
        total += _count_nodes(child)
    return total


def fpgrowth(transactions, min_support: float, max_len=None, verbose=False):
    """FP-Growth 主过程。返回 frequent / stats / total_time。"""
    n = len(transactions)
    min_count = max(1, int(-(-min_support * n // 1)))

    t0 = time.perf_counter()
    root, header, freq, order = _build_tree(transactions, min_count)
    t_build = time.perf_counter() - t0

    patterns = {}
    stats = {
        "tree_nodes": _count_nodes(root) - 1,   # 主 FP 树的非根结点数
        "conditional_tree_nodes": 0,            # 递归过程中所有条件 FP 树的结点总数
        "conditional_pattern_base": 0,
        "recursive_calls": 0,
    }
    _mine(header, freq, (), min_count, patterns, stats, max_len)
    # 统一项集内部的项顺序（挖掘时按支持度升序拼接），便于与其他算法逐项比对
    patterns = {tuple(sorted(k)): v for k, v in patterns.items()}
    total = time.perf_counter() - t0

    if verbose:
        print(f"  FP 树结点数 {stats['tree_nodes']}，事务数 {n}，压缩比 "
              f"{n / max(1, stats['tree_nodes']):.2f}:1；建树 {t_build:.3f}s；"
              f"递归 {stats['recursive_calls']} 次，频繁项集 {len(patterns)} 个")

    return {
        "frequent": patterns,
        "stats": stats,
        "total_time": total,
        "build_time": t_build,
        "min_count": min_count,
        "n_transactions": n,
        "min_support": min_support,
    }


def fpgrowth_from_counts(transactions, min_support: float, max_len=None, verbose=False):
    """与 fpgrowth 等价的参考实现：先精确统计每个项集。

    只用于小规模数据的正确性校验（暴力枚举所有项集）。大样本上不适用。
    """
    from itertools import combinations

    n = len(transactions)
    min_count = max(1, int(-(-min_support * n // 1)))
    counts = Counter()
    for t in transactions:
        counts.update(t)
    items = sorted(i for i, c in counts.items() if c >= min_count)
    result = {}
    for k in range(1, len(items) + 1):
        for combo in combinations(items, k):
            c = 0
            cset = set(combo)
            for t in transactions:
                if cset <= t:
                    c += 1
            if c >= min_count:
                result[combo] = c
    return {"frequent": result, "total_time": 0.0}
