# -*- coding: utf-8 -*-
"""数据加载与预处理工具。

两个数据集：
  car.data       —— UCI Car Evaluation 汽车评估数据库，1728 条记录、6 个条件属性 + 1 个类别属性；
  groceries.csv  —— 商品购买记录数据库，9835 条事务、169 种商品。

关联分析要求输入是"事务-项"集合的形式，因此汽车评估数据需要把
每一行的「属性=取值」转成一个项（如 buying=low），一行 6 个项构成一个事务。
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CAR_FILE = DATA_DIR / "car.data"
GROCERIES_FILE = DATA_DIR / "groceries.csv"

CAR_COLUMNS = ["buying", "maint", "doors", "persons", "lug_boot", "safety", "class"]
CAR_LABELS = {
    "buying": "购买价格",
    "maint": "维护费用",
    "doors": "车门数",
    "persons": "载人数",
    "lug_boot": "后备箱",
    "safety": "安全性",
    "class": "评估等级",
}


def load_car(path: Path = CAR_FILE, onehot: bool = True, keep_class: bool = True):
    """加载汽车评估数据库。

    onehot=True 时把「属性=取值」作为一个项（如 buying=low），这是本实验采用的形式；
    onehot=False 时直接用取值本身作为项（不同属性下同名取值会被合并，仅用于对照）。
    返回 (transactions, raw_rows, class_labels)。
    """
    transactions = []
    raw_rows = []
    labels = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            values = [v.strip() for v in line.split(",")]
            raw_rows.append(values)
            labels.append(values[-1])
            used = CAR_COLUMNS if keep_class else CAR_COLUMNS[:-1]
            if onehot:
                items = [f"{col}={values[i]}" for i, col in enumerate(used)]
            else:
                items = [values[i] for i in range(len(used))]
            transactions.append(frozenset(items))
    return transactions, raw_rows, labels


def load_groceries(path: Path = GROCERIES_FILE):
    """加载商品购买记录数据库，每行是一条购物事务，商品之间用逗号分隔。"""
    transactions = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            items = [x.strip() for x in row if x.strip()]
            if items:
                transactions.append(frozenset(items))
    return transactions


def basic_info(transactions, name: str) -> dict:
    """统计事务数、项数、事务长度分布等基本信息。"""
    counter = Counter()
    lengths = []
    for t in transactions:
        counter.update(t)
        lengths.append(len(t))
    n = len(transactions)
    info = {
        "name": name,
        "n_transactions": n,
        "n_items": len(counter),
        "n_total_items": sum(lengths),
        "avg_length": sum(lengths) / n if n else 0.0,
        "max_length": max(lengths) if lengths else 0,
        "min_length": min(lengths) if lengths else 0,
        "length_dist": dict(sorted(Counter(lengths).items())),
        "item_freq": counter.most_common(),
    }
    return info


def format_info(info: dict) -> str:
    lines = [
        f"数据集：{info['name']}",
        f"事务数：{info['n_transactions']}",
        f"不同项（商品/属性取值）数：{info['n_items']}",
        f"项总数：{info['n_total_items']}",
        f"平均事务长度：{info['avg_length']:.3f} 项/事务",
        f"事务长度范围：{info['min_length']} ~ {info['max_length']}",
        f"事务长度分布（长度:事务数）：{info['length_dist']}",
        "出现最频繁的 10 个项：" + ", ".join(f"{k}({v})" for k, v in info["item_freq"][:10]),
    ]
    return "\n".join(lines)


def min_count_of(min_support: float, n_transactions: int) -> int:
    """支持度阈值换算成最小计数（向上取整）。"""
    import math

    return max(1, math.ceil(min_support * n_transactions - 1e-12))
