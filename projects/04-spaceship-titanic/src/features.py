"""Spaceship Titanic 特征工程。

设计原则（写进报告）：
1. 不使用任何与标签相关的特征（例如"同组内有几人被传送"）——那会引入折叠间泄漏。
   组特征只用乘客属性本身（组大小、组内舱位是否一致等），这类信息在训练集与测试集中
   都可得，属于乘客记录的一部分。
2. 所有会"学到参数"的预处理（缺失填补的统计量、标准化、独热编码的类别集合）都封装在
   sklearn Pipeline 里，只在交叉验证的训练折上 fit，避免用验证折的信息。
3. 输出统一的稠密数值矩阵，供五类算法共用，保证对比公平。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SPEND = ["RoomService", "FoodCourt", "ShoppingMall", "Spa", "VRDeck"]
LUXURY = ["RoomService", "Spa", "VRDeck"]
BASIC = ["FoodCourt", "ShoppingMall"]
CAT_COLS = ["HomePlanet", "Destination", "Deck", "Side", "CryoSleep", "VIP"]


def add_group_features(df: pd.DataFrame) -> pd.DataFrame:
    """由 PassengerId 与 Cabin 派生结构特征；不使用标签。"""
    df = df.copy()

    pid = df["PassengerId"].str.split("_", expand=True)
    df["Group"] = pid[0].astype(int)
    df["MemberNum"] = pid[1].astype(int)

    cabin = df["Cabin"].str.split("/", expand=True)
    df["Deck"] = cabin[0]
    df["CabinNum"] = pd.to_numeric(cabin[1], errors="coerce")
    df["Side"] = cabin[2]

    # 消费：总量、是否零消费、奢侈/基础两类（原始五项右偏严重，后续做 log1p）
    spend_sum = df[SPEND].sum(axis=1, min_count=1)
    df["TotalSpend"] = spend_sum
    df["NoSpend"] = (df[SPEND].fillna(0).sum(axis=1) == 0).astype(int)
    df["LuxurySpend"] = df[LUXURY].sum(axis=1, min_count=1)
    df["BasicSpend"] = df[BASIC].sum(axis=1, min_count=1)
    df["SpendTypes"] = (df[SPEND].fillna(0) > 0).sum(axis=1)

    # 年龄段（树模型可从原始 Age 自行划分，这里是给线性/核方法的显式非线性）
    df["IsChild"] = (df["Age"] < 13).astype(float)
    df.loc[df["Age"].isna(), "IsChild"] = np.nan

    # 组内结构：组大小、是否独行、组内舱位/母星是否一致、组内消费总量
    g = df.groupby("Group")
    df["GroupSize"] = g["PassengerId"].transform("size")
    df["IsAlone"] = (df["GroupSize"] == 1).astype(int)
    df["GroupDeckNunique"] = g["Deck"].transform("nunique")
    df["GroupPlanetNunique"] = g["HomePlanet"].transform("nunique")
    df["GroupSpendSum"] = g["TotalSpend"].transform("sum")
    df["GroupCryoCount"] = g["CryoSleep"].transform(lambda s: s.fillna(False).sum())
    df["GroupAgeMean"] = g["Age"].transform("mean")
    df["AgeMinusGroupMean"] = df["Age"] - df["GroupAgeMean"]
    # 同一组内的人往往共享舱位：用组内 CabinNum 的中位数替代缺失
    df["CabinNumGroupMedian"] = g["CabinNum"].transform("median")
    df["CabinNumFilled"] = df["CabinNum"].fillna(df["CabinNumGroupMedian"])

    # CryoSleep 与消费的耦合：冷冻睡眠者不出现在任何消费场所
    df["CryoNoSpend"] = ((df["CryoSleep"] == True) & (df["NoSpend"] == 1)).astype(float)  # noqa: E712
    df.loc[df["CryoSleep"].isna(), "CryoNoSpend"] = np.nan

    return df


def raw_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """返回用于建模的"原始语义列"（未编码、未缩放），Pipeline 会接在它后面。"""
    d = add_group_features(df)
    num = [
        "Age", "RoomService", "FoodCourt", "ShoppingMall", "Spa", "VRDeck",
        "TotalSpend", "LuxurySpend", "BasicSpend", "SpendTypes", "NoSpend",
        "CabinNumFilled", "MemberNum", "GroupSize", "IsAlone",
        "GroupDeckNunique", "GroupPlanetNunique", "GroupSpendSum",
        "GroupCryoCount", "AgeMinusGroupMean", "IsChild", "CryoNoSpend",
    ]
    out = d[num + CAT_COLS].copy()
    # 对数变换：消费类特征呈长尾（0 与上万的混合），log1p 让线性/核方法与神经网络更易拟合
    for c in ["RoomService", "FoodCourt", "ShoppingMall", "Spa", "VRDeck",
              "TotalSpend", "LuxurySpend", "BasicSpend", "GroupSpendSum"]:
        out[c] = np.log1p(out[c].clip(lower=0))
    return out


def get_xy(train_csv, test_csv):
    """读入原始 CSV，返回 (X_train, y_train, X_test, test_ids)。"""
    tr = pd.read_csv(train_csv)
    te = pd.read_csv(test_csv)
    y = tr["Transported"].astype(int).to_numpy()
    Xtr = raw_feature_frame(tr)
    Xte = raw_feature_frame(te)
    # 列必须完全一致（对齐断言）
    assert list(Xtr.columns) == list(Xte.columns), "训练/测试特征列不一致"
    assert len(Xtr) == len(tr) and len(Xte) == len(te), "行数在特征构造后发生变化"
    return Xtr, y, Xte, te["PassengerId"].to_numpy()


def describe(Xtr: pd.DataFrame, Xte: pd.DataFrame) -> dict:
    """供报告使用的特征清单与缺失统计。"""
    return {
        "n_features_raw": int(Xtr.shape[1]),
        "numeric": [c for c in Xtr.columns if c not in CAT_COLS],
        "categorical": CAT_COLS,
        "missing_train": {k: int(v) for k, v in Xtr.isna().sum().items() if v},
        "missing_test": {k: int(v) for k, v in Xte.isna().sum().items() if v},
        "n_train": int(len(Xtr)),
        "n_test": int(len(Xte)),
    }
