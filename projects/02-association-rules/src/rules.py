# -*- coding: utf-8 -*-
"""由频繁项集生成关联规则（支持度 / 置信度 / 提升度）。"""
from __future__ import annotations

from itertools import combinations


def generate_rules(frequent: dict, n_transactions: int, min_confidence: float = 0.5,
                   min_lift: float = 0.0, max_rules=None):
    """对每个频繁项集枚举其全部非空真子集作为前件，计算三个度量。

    support(A→B)    = P(A∪B)
    confidence(A→B) = P(B|A)
    lift(A→B)       = P(B|A) / P(B)
    """
    rules = []
    for itemset, count in frequent.items():
        if len(itemset) < 2:
            continue
        support = count / n_transactions
        for r in range(1, len(itemset)):
            for antecedent in combinations(itemset, r):
                consequent = tuple(x for x in itemset if x not in antecedent)
                a_count = frequent.get(antecedent)
                c_count = frequent.get(consequent)
                if a_count is None or c_count is None or a_count == 0:
                    continue
                confidence = count / a_count
                if confidence < min_confidence:
                    continue
                consequent_support = c_count / n_transactions
                lift = confidence / consequent_support if consequent_support else 0.0
                if lift < min_lift:
                    continue
                rules.append({
                    "antecedent": antecedent,
                    "consequent": consequent,
                    "support": support,
                    "confidence": confidence,
                    "lift": lift,
                    "count": count,
                })
    rules.sort(key=lambda r: (-r["confidence"], -r["support"], -r["lift"]))
    if max_rules is not None:
        rules = rules[:max_rules]
    return rules


def itemset_stats(frequent: dict):
    """按项集长度统计频繁项集个数。"""
    from collections import Counter

    by_len = Counter(len(k) for k in frequent)
    return dict(sorted(by_len.items()))
