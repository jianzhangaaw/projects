# -*- coding: utf-8 -*-
"""
数据预处理实验 —— 分析主脚本
数据集：Kaggle Titanic (train.csv, 891 x 12)
输出：out/results.json（结构化结果）、out/fig_*.png（图）、data/titanic_clean.csv（清洗后数据）
运行：py src/analyze.py
"""
import json
import os
import sys
import math

# Windows 控制台默认是 GBK，脚本里的中文与统计符号会触发 UnicodeEncodeError。
# 统一把 stdout/stderr 切到 UTF-8，并对无法编码的字符降级替换，保证任何终端都能跑完。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler, MinMaxScaler

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "titanic.csv")
OUT = os.path.join(BASE, "out")
os.makedirs(OUT, exist_ok=True)

# 中文字体
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.bbox"] = "tight"

R = {}          # 结果字典，最后写 results.json
LOG = []        # 控制台报告


def p(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s)


def jnum(x, nd=4):
    """把 numpy 标量转成 python 可序列化、且四舍五入的数；极小值保留数量级不丢成 0"""
    if x is None:
        return None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        r = round(v, nd)
        if r == 0 and v != 0:
            return float("%.3e" % v)
        return r
    return x


# =====================================================================
# 1 数据导入与初步查看
# =====================================================================
p("=" * 78)
p("1 数据导入与初步查看")
p("=" * 78)

raw = pd.read_csv(DATA)
p("原始数据规模（行, 列）:", raw.shape)
p("列名:", list(raw.columns))
p("各列数据类型:")
for c, t in raw.dtypes.astype(str).items():
    p("   %-12s %s" % (c, t))

R["shape"] = list(raw.shape)
R["columns"] = list(raw.columns)
R["dtypes"] = {c: str(t) for c, t in raw.dtypes.items()}
R["head5"] = raw.head(5).astype(str).values.tolist()
R["memory_kb"] = round(raw.memory_usage(deep=True).sum() / 1024, 1)

# 字段含义表（写进报告）
R["field_desc"] = [
    ["PassengerId", "整数", "乘客编号（唯一）", "无缺失", "标识，建模时剔除"],
    ["Survived", "整数(0/1)", "是否生还：0=遇难，1=生还", "无缺失", "目标变量"],
    ["Pclass", "整数(1/2/3)", "船票等级：1=头等，2=二等，3=三等", "无缺失", "有序类别，可作社会经济地位代理"],
    ["Name", "文本", "姓名，含称谓（Mr/Mrs/Miss…）", "无缺失", "可提取称谓特征"],
    ["Sex", "文本", "性别 male/female", "无缺失", "二值类别"],
    ["Age", "浮点", "年龄（年），小于 1 岁为小数", "177 缺失", "数值，右偏轻微"],
    ["SibSp", "整数", "同船兄弟姐妹/配偶数", "无缺失", "计数型，右偏"],
    ["Parch", "整数", "同船父母/子女数", "无缺失", "计数型，右偏"],
    ["Ticket", "文本", "船票号", "无缺失", "高基数，含前缀信息"],
    ["Fare", "浮点", "票价（英镑）", "无缺失", "数值，强烈右偏"],
    ["Cabin", "文本", "客舱号（首字母为甲板层）", "687 缺失（77.1%）", "缺失过多，转为 Deck 特征"],
    ["Embarked", "文本", "登船港：C=Cherbourg, Q=Queenstown, S=Southampton", "2 缺失", "三值类别"],
]

# info() 式的非空计数
nonnull = raw.notna().sum()
R["nonnull"] = {c: [int(nonnull[c]), int(raw.shape[0] - nonnull[c])] for c in raw.columns}

R["describe_raw"] = json.loads(raw.describe().to_json(force_ascii=False))

# 类型转换（category）对内存占用的实测影响
_cat = raw.copy()
for _c in ["Pclass", "Embarked", "Sex"]:
    _cat[_c] = _cat[_c].astype("category")
mem_before = raw.memory_usage(deep=True).sum()
mem_after = _cat.memory_usage(deep=True).sum()
R["mem_cat"] = [round(mem_before / 1024, 1), round(mem_after / 1024, 1),
                round((1 - mem_after / mem_before) * 100, 1)]
p("1.1 深拷贝内存占用：object 版 %.1f KB → Pclass/Embarked/Sex 转 category 后 %.1f KB（下降 %.1f%%）"
  % (mem_before / 1024, mem_after / 1024, (1 - mem_after / mem_before) * 100))

# =====================================================================
# 2 数据清洗
# =====================================================================
p("")
p("=" * 78)
p("2 数据清洗")
p("=" * 78)

# --- 2.1 缺失值 ---
miss = raw.isna().sum()
missp = (miss / len(raw) * 100).round(2)
p("2.1 缺失值统计（缺失数 / 缺失率%）:")
for c in raw.columns:
    if miss[c] > 0:
        p("   %-10s %4d  %6.2f%%" % (c, miss[c], missp[c]))
p("   缺失单元格合计: %d / %d = %.2f%%" % (miss.sum(), raw.size, miss.sum() / raw.size * 100))
R["missing_raw"] = [[c, int(miss[c]), float(missp[c])] for c in raw.columns if miss[c] > 0]
R["missing_cells_raw"] = int(miss.sum())
R["cells_total"] = int(raw.size)
R["missing_cell_pct"] = round(float(miss.sum() / raw.size * 100), 2)

# --- 2.2 重复值 ---
dup = int(raw.duplicated().sum())
dup_id = int(raw["PassengerId"].duplicated().sum())
p("2.2 完全重复行数: %d ；PassengerId 重复数: %d" % (dup, dup_id))
R["dup_rows"] = dup
R["dup_id"] = dup_id

df = raw.copy()

# 类型转换：把取值重复的类别列转为 category
for _c in ["Sex", "Embarked", "Pclass"]:
    df[_c] = df[_c].astype("category")

# --- 2.3 一致性检查 ---
cons = {}
for c in ["Sex", "Embarked", "Pclass", "Survived"]:
    vals = sorted(df[c].dropna().unique().tolist())
    cons[c] = [str(v) for v in vals]
cons["Age_range"] = [jnum(df["Age"].min()), jnum(df["Age"].max())]
cons["Fare_range"] = [jnum(df["Fare"].min()), jnum(df["Fare"].max())]
cons["Fare_negative"] = int((df["Fare"] < 0).sum())
cons["Age_le0"] = int((df["Age"] <= 0).sum())
cons["Fare_zero"] = int((df["Fare"] == 0).sum())
p("2.3 一致性检查: Sex=%s, Embarked=%s, Pclass=%s" % (cons["Sex"], cons["Embarked"], cons["Pclass"]))
p("   Age 取值 [%.2f, %.1f]，Fare 取值 [%.4f, %.4f]，负票价 %d 条，Fare=0 共 %d 条"
  % (cons["Age_range"][0], cons["Age_range"][1], cons["Fare_range"][0], cons["Fare_range"][1],
     cons["Fare_negative"], cons["Fare_zero"]))
R["consistency"] = cons

fare_zero_rows = df.loc[df["Fare"] == 0, ["PassengerId", "Pclass", "Embarked", "Fare"]]
R["fare_zero"] = fare_zero_rows.astype(str).values.tolist()
_fz = raw[raw["Fare"] == 0]
R["fare_zero_detail"] = [int(len(_fz)), bool((_fz["Sex"] == "male").all()),
                         bool((_fz["Embarked"] == "S").all()),
                         int(((_fz["SibSp"] > 0) | (_fz["Parch"] > 0)).sum()),
                         sorted(set(_fz["Ticket"].tolist()))[:4]]
p("     Fare=0 的 %d 条记录：全部为 %s、全部从 %s 登船、有同行家属的 %d 条，票号含 %s 等"
  % (len(_fz), "男性" if (_fz["Sex"] == "male").all() else "混合性别",
     "S" if (_fz["Embarked"] == "S").all() else "多个港口", int(((_fz["SibSp"] > 0) | (_fz["Parch"] > 0)).sum()),
     "、".join(sorted(set(_fz["Ticket"].tolist()))[:3])))

# --- 2.4 缺失值填补 ---
# Embarked：众数填补
emb_mode = df["Embarked"].mode()[0]
emb_fill_idx = df.loc[df["Embarked"].isna(), "PassengerId"].tolist()
df["Embarked"] = df["Embarked"].fillna(emb_mode)
p("2.4a Embarked 缺失 %d 条（PassengerId=%s）以众数 '%s' 填补"
  % (len(emb_fill_idx), emb_fill_idx, emb_mode))

# Age：按 (Pclass, Sex) 分组中位数填补，并与全局均值/中位数对比
grp_med = df.groupby(["Pclass", "Sex"], observed=True)["Age"].median()
age_global_mean = df["Age"].mean()
age_global_med = df["Age"].median()
age_missing_mask = df["Age"].isna()
age_fill_vals = df.loc[age_missing_mask].set_index(["Pclass", "Sex"]).index.map(grp_med)
df.loc[age_missing_mask, "Age"] = np.asarray(age_fill_vals, dtype=float)
df["Age"] = df["Age"].astype(float)
p("2.4b Age 缺失 %d 条：按 (Pclass,Sex) 分组中位数填补（全局均值 %.2f，全局中位数 %.2f）"
  % (int(age_missing_mask.sum()), age_global_mean, age_global_med))
grp_table = [[f"{pc}-{sx}", jnum(v)] for (pc, sx), v in grp_med.items()]
R["age_group_median"] = grp_table
R["age_global_mean"] = jnum(age_global_mean)
R["age_global_median"] = jnum(age_global_med)
R["age_missing_n"] = int(age_missing_mask.sum())
R["emb_mode"] = emb_mode
R["emb_fill_ids"] = emb_fill_idx

# Cabin：缺失 77%，提取甲板层首字母，缺失记为 U，原列删除
df["Deck"] = df["Cabin"].str[0].fillna("U")
n_deck_u = int((df["Deck"] == "U").sum())
df = df.drop(columns=["Cabin"])
p("2.4c Cabin 缺失 %d 条（%.2f%%）：不逐条填补，提取甲板层首字母生成 Deck 特征（U=未知，共 %d 条），删除原列"
  % (miss["Cabin"], missp["Cabin"], n_deck_u))
R["cabin_missing"] = int(miss["Cabin"])
R["cabin_missing_pct"] = float(missp["Cabin"])

# --- 2.5 异常值检测（IQR 与 3σ 对照） ---
num_cols = ["Age", "Fare", "SibSp", "Parch"]
out_rows = []
wins = {}
for c in num_cols:
    s = df[c].astype(float)
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_lo, n_hi = int((s < lo).sum()), int((s > hi).sum())
    mu, sd = s.mean(), s.std(ddof=1)
    n_3s = int(((s < mu - 3 * sd) | (s > mu + 3 * sd)).sum())
    wins[c] = (float(s.quantile(0.01)), float(s.quantile(0.99)))
    out_rows.append([c, jnum(s.min()), jnum(q1), jnum(s.median()), jnum(q3), jnum(s.max()),
                     jnum(iqr), jnum(lo, 3), jnum(hi, 3), n_lo, n_hi, n_lo + n_hi, n_3s])
    p("2.5 %-6s Q1=%.3f 中位=%.3f Q3=%.3f IQR=%.3f 下界=%.3f 上界=%.3f → 离群 %d 低 + %d 高 = %d；3σ 法 %d"
      % (c, q1, s.median(), q3, iqr, lo, hi, n_lo, n_hi, n_lo + n_hi, n_3s))
R["outlier_iqr"] = out_rows
R["outlier_header"] = ["变量", "最小", "Q1", "中位数", "Q3", "最大", "IQR", "下界", "上界", "低端离群", "高端离群", "离群合计", "3σ法"]

# Fare 高分位说明
fare_top = df.nlargest(5, "Fare")[["PassengerId", "Pclass", "Fare", "SibSp", "Parch"]]
R["fare_top5"] = fare_top.astype(str).values.tolist()

# 清洗后缺失
miss_after = df.isna().sum().sum()
p("2.6 清洗后缺失单元格: %d（原 %d）" % (miss_after, miss.sum()))
R["missing_cells_after"] = int(miss_after)
R["shape_after_clean"] = list(df.shape)

# --- 2.7 填补效果与异常值处理影响的量化 ---
obs_age = raw.loc[raw["Age"].notna(), "Age"].to_numpy()
imp_age = df.loc[age_missing_mask, "Age"].to_numpy()
mw = stats.mannwhitneyu(obs_age, imp_age, alternative="two-sided")
ks = stats.ks_2samp(obs_age, imp_age)
p("2.7a 填补效果：观测 Age 均值 %.2f 中位 %.2f 标准差 %.2f；填补 Age 均值 %.2f 中位 %.2f 标准差 %.2f"
  % (obs_age.mean(), np.median(obs_age), obs_age.std(ddof=1), imp_age.mean(), np.median(imp_age), imp_age.std(ddof=1)))
p("     Mann-Whitney U 检验 p=%.4f，KS 检验 p=%.4f → %s（α=0.05）"
  % (mw.pvalue, ks.pvalue, "两组无显著差异，填补未引入系统性偏移" if mw.pvalue > 0.05 else "两组存在显著差异，填补引入偏移，需谨慎"))
R["age_imp_cmp"] = [jnum(obs_age.mean(), 2), jnum(np.median(obs_age), 2), jnum(obs_age.std(ddof=1), 2),
                    jnum(imp_age.mean(), 2), jnum(np.median(imp_age), 2), jnum(imp_age.std(ddof=1), 2)]
R["age_imp_test"] = [jnum(mw.pvalue, 4), jnum(ks.pvalue, 4)]

fare_win = df["Fare"].clip(*wins["Fare"])
r_fare = stats.pearsonr(df["Survived"], df["Fare"])
r_win = stats.pearsonr(df["Survived"], fare_win)
r_log = stats.pearsonr(df["Survived"], np.log1p(df["Fare"]))
p("2.7b 异常值/右偏处理对相关系数的影响：Fare 原始 r=%.4f，1%%-99%% 盖帽后 r=%.4f，log1p 变换后 r=%.4f"
  % (r_fare[0], r_win[0], r_log[0]))
R["fare_corr_variants"] = [["原始 Fare", jnum(r_fare[0], 4)], ["盖帽(1%,99%)后", jnum(r_win[0], 4)], ["log1p 变换后", jnum(r_log[0], 4)]]

# =====================================================================
# 3 数据转换与特征构造
# =====================================================================
p("")
p("=" * 78)
p("3 数据转换与特征构造")
p("=" * 78)

# --- 3.1 派生特征 ---
df["Title"] = df["Name"].str.extract(r" ([A-Za-z]+)\.", expand=False)
title_map = {"Mlle": "Miss", "Ms": "Miss", "Mme": "Mrs",
             "Lady": "Rare", "Countess": "Rare", "Capt": "Rare", "Col": "Rare",
             "Don": "Rare", "Dr": "Rare", "Major": "Rare", "Rev": "Rare",
             "Sir": "Rare", "Jonkheer": "Rare", "Dona": "Rare"}
df["Title"] = df["Title"].replace(title_map)
title_cnt = df["Title"].value_counts()
p("3.1 从 Name 提取称谓 Title（含归并）:", dict(title_cnt))
R["title_counts"] = [[str(k), int(v)] for k, v in title_cnt.items()]

df["FamilySize"] = df["SibSp"] + df["Parch"] + 1
df["IsAlone"] = (df["FamilySize"] == 1).astype(int)
fs_cnt = df["FamilySize"].value_counts().sort_index()
p("    家庭规模 FamilySize = SibSp + Parch + 1:", {int(k): int(v) for k, v in fs_cnt.items()})
R["familysize_counts"] = [[int(k), int(v)] for k, v in fs_cnt.items()]

# --- 3.2 分箱离散化 ---
age_bins = [0, 12, 18, 35, 60, 100]
age_labels = ["儿童(0-12)", "少年(13-18)", "青年(19-35)", "中年(36-60)", "老年(61+)"]
df["AgeGroup"] = pd.cut(df["Age"], bins=age_bins, labels=age_labels, right=True)
ag_cnt = df["AgeGroup"].value_counts().reindex(age_labels)
p("3.2 年龄等宽分箱:", {str(k): int(v) for k, v in ag_cnt.items()})
R["agegroup_counts"] = [[str(k), int(v)] for k, v in ag_cnt.items()]
R["age_bins"] = age_bins

fare_q, fare_edges = pd.qcut(df["Fare"], q=4, retbins=True, duplicates="drop")
df["FareBand"] = fare_q
fare_labels = ["(%.2f,%.2f]" % (fare_edges[i], fare_edges[i + 1]) for i in range(len(fare_edges) - 1)]
p("    票价等频分箱 qcut(4) 边界:", [jnum(e, 3) for e in fare_edges])
R["fare_edges"] = [jnum(e, 4) for e in fare_edges]
fb = df["FareBand"].value_counts().sort_index()
R["fareband_counts"] = [["(%.2f,%.2f]" % (iv.left, iv.right), int(v)] for iv, v in fb.items()]
p("    各票价区间人数:", R["fareband_counts"])

# --- 3.3 右偏变量的对数变换 ---
skew_before = float(df["Fare"].skew())
kurt_before = float(df["Fare"].kurt())
df["FareLog"] = np.log1p(df["Fare"])
skew_after = float(df["FareLog"].skew())
kurt_after = float(df["FareLog"].kurt())
p("3.3 Fare 对数变换 log1p：偏度 %.4f → %.4f，峰度 %.4f → %.4f"
  % (skew_before, skew_after, kurt_before, kurt_after))
R["fare_skew"] = [jnum(skew_before), jnum(skew_after)]
R["fare_kurt"] = [jnum(kurt_before), jnum(kurt_after)]

# --- 3.4 数值无量纲化 ---
scale_cols = ["Age", "Fare", "SibSp", "Parch"]
z = StandardScaler().fit_transform(df[scale_cols].astype(float))
mm = MinMaxScaler().fit_transform(df[scale_cols].astype(float))
scale_tbl = []
for i, c in enumerate(scale_cols):
    scale_tbl.append([c, jnum(df[c].mean()), jnum(df[c].std(ddof=0)),
                      jnum(z[:, i].mean(), 6), jnum(z[:, i].std(ddof=0), 3),
                      jnum(z[:, i].min(), 3), jnum(z[:, i].max(), 3),
                      jnum(mm[:, i].min(), 3), jnum(mm[:, i].max(), 3)])
    p("3.4 %-6s 原始均值=%.3f 标准差=%.3f | z-score 均值≈%.6f 标准差=%.3f 范围[%.2f,%.2f] | min-max 范围[%.2f,%.2f]"
      % (c, df[c].mean(), df[c].std(ddof=0), z[:, i].mean(), z[:, i].std(ddof=0), z[:, i].min(), z[:, i].max(),
         mm[:, i].min(), mm[:, i].max()))
R["scale_tbl"] = scale_tbl
R["scale_header"] = ["变量", "原始均值", "原始标准差", "标准化均值", "标准化标准差", "标准化最小", "标准化最大", "归一化最小", "归一化最大"]

# --- 3.5 类别编码 ---
# 有序编码：Pclass 保持 1/2/3 序号；Deck 按字母序编码；无序类别做独热
onehot_spec = {"Sex": df["Sex"].nunique(), "Embarked": df["Embarked"].nunique(),
               "Title": df["Title"].nunique(), "Deck": df["Deck"].nunique(),
               "AgeGroup": int(df["AgeGroup"].nunique())}
dummies = pd.get_dummies(df[["Sex", "Embarked", "Title", "Deck"]], columns=["Sex", "Embarked", "Title", "Deck"],
                         prefix=["Sex", "Emb", "Title", "Deck"])
p("3.5 独热编码:", {k: int(v) for k, v in onehot_spec.items()}, "→ 生成哑变量 %d 列" % dummies.shape[1])
R["onehot_spec"] = {k: int(v) for k, v in onehot_spec.items()}
R["onehot_cols"] = int(dummies.shape[1])
R["onehot_names"] = list(dummies.columns)

df["PclassOrd"] = df["Pclass"].astype(int)
df["AgeGroupOrd"] = df["AgeGroup"].cat.codes.astype(int)
df["DeckOrd"] = df["Deck"].astype("category").cat.codes.astype(int)
R["final_feature_n"] = int(dummies.shape[1] + 4 + 2 + 1 + 2)  # 哑变量 + 4个标准化数值 + FamilySize/IsAlone + FareLog + Pclass/AgeGroup 有序编码
R["feature_account"] = [
    ["数值型（标准化）", "Age, Fare, SibSp, Parch", len(scale_cols)],
    ["数值型（计数/0-1，不标准化）", "FamilySize, IsAlone", 2],
    ["变换型", "FareLog = log1p(Fare)", 1],
    ["有序编码", "PclassOrd, AgeGroupOrd", 2],
    ["独热编码", "Sex, Embarked, Title, Deck", int(dummies.shape[1])],
    ["标识/文本（剔除）", "PassengerId, Name, Ticket", 3],
]
p("3.6 转换后建模特征矩阵规模：%d 个特征（%d 行）" % (R["final_feature_n"], len(df)))

# --- 3.6 编辑结果落盘 ---
clean_path = os.path.join(BASE, "data", "titanic_clean.csv")
df.to_csv(clean_path, index=False, encoding="utf-8-sig")
p("3.6 转换后的数据集已导出: %s （%d 行 × %d 列）" % (os.path.relpath(clean_path, BASE), *df.shape))
R["shape_clean"] = list(df.shape)
R["clean_cols"] = list(df.columns)

# =====================================================================
# 4 描述性统计
# =====================================================================
p("")
p("=" * 78)
p("4 描述性统计")
p("=" * 78)

num_stat_cols = ["Age", "Fare", "SibSp", "Parch", "FamilySize"]
stat_tbl = []
for c in num_stat_cols:
    s = df[c].astype(float)
    stat_tbl.append([c, int(s.count()), jnum(s.mean(), 3), jnum(s.std(ddof=1), 3),
                     jnum(s.min(), 3), jnum(s.quantile(0.25), 3), jnum(s.median(), 3),
                     jnum(s.quantile(0.75), 3), jnum(s.max(), 3), jnum(s.skew(), 3), jnum(s.kurt(), 3),
                     jnum(s.std(ddof=1) / s.mean(), 3)])
    p("4.1 %-10s 均值=%.3f 标准差=%.3f 中位=%.3f 最小=%.2f 最大=%.2f 偏度=%.3f 峰度=%.3f 变异系数=%.3f"
      % (c, s.mean(), s.std(ddof=1), s.median(), s.min(), s.max(), s.skew(), s.kurt(), s.std(ddof=1) / s.mean()))
R["num_stat"] = stat_tbl
R["num_stat_header"] = ["变量", "计数", "均值", "标准差", "最小", "Q1", "中位数", "Q3", "最大", "偏度", "峰度", "变异系数"]

cat_tbl = []
for c in ["Survived", "Pclass", "Sex", "Embarked", "Deck", "Title", "AgeGroup", "IsAlone", "FareBand"]:
    vc = df[c].value_counts(dropna=False)
    for k, v in vc.items():
        cat_tbl.append([c, str(k), int(v), round(float(v) / len(df) * 100, 2)])
    p("4.2 %-9s 众数=%s（%d 条，占 %.2f%%）；取值数 %d" % (c, vc.index[0], vc.iloc[0], vc.iloc[0] / len(df) * 100, len(vc)))
R["cat_freq"] = cat_tbl

# 分组统计：生存率
def surv_rate(g):
    return round(float(g["Survived"].mean() * 100), 2)

grp = []
for key, sub in df.groupby("Sex", observed=True):
    grp.append(["性别=" + str(key), len(sub), surv_rate(sub), jnum(sub["Age"].mean(), 2), jnum(sub["Fare"].mean(), 2)])
for key, sub in df.groupby("Pclass", observed=True):
    grp.append(["船票等级=%s" % key, len(sub), surv_rate(sub), jnum(sub["Age"].mean(), 2), jnum(sub["Fare"].mean(), 2)])
for key, sub in df.groupby(["Pclass", "Sex"], observed=True):
    grp.append(["%s等舱-%s" % (key[0], key[1]), len(sub), surv_rate(sub), jnum(sub["Age"].mean(), 2), jnum(sub["Fare"].mean(), 2)])
for key, sub in df.groupby("AgeGroup", observed=True):
    grp.append(["年龄组=" + str(key), len(sub), surv_rate(sub), jnum(sub["Age"].mean(), 2), jnum(sub["Fare"].mean(), 2)])
for key, sub in df.groupby("Embarked", observed=True):
    grp.append(["登船港=" + str(key), len(sub), surv_rate(sub), jnum(sub["Age"].mean(), 2), jnum(sub["Fare"].mean(), 2)])
for key, sub in df.groupby("IsAlone", observed=True):
    grp.append(["独自出行=%s" % ("是" if key == 1 else "否"), len(sub), surv_rate(sub), jnum(sub["Age"].mean(), 2), jnum(sub["Fare"].mean(), 2)])
for key, sub in df.groupby("Title", observed=True):
    grp.append(["称谓=" + str(key), len(sub), surv_rate(sub), jnum(sub["Age"].mean(), 2), jnum(sub["Fare"].mean(), 2)])
R["group_stat"] = grp
p("4.3 分组生存率（部分）: 总体=%.2f%% 女性=%.2f%% 男性=%.2f%% 1等=%.2f%% 3等=%.2f%%"
  % (df["Survived"].mean() * 100,
     df.loc[df.Sex == "female", "Survived"].mean() * 100,
     df.loc[df.Sex == "male", "Survived"].mean() * 100,
     df.loc[df.Pclass == 1, "Survived"].mean() * 100,
     df.loc[df.Pclass == 3, "Survived"].mean() * 100))
R["surv_overall"] = round(float(df["Survived"].mean() * 100), 2)

# =====================================================================
# 5 相似性分析
# =====================================================================
p("")
p("=" * 78)
p("5 相似性分析")
p("=" * 78)

sim_cols = ["Age", "Fare", "SibSp", "Parch"]
Xraw = df[sim_cols].astype(float).to_numpy()
Xstd = StandardScaler().fit_transform(Xraw)
pid = df["PassengerId"].to_numpy()
N = len(df)
target = 0          # 相似性分析的示例目标乘客：PassengerId=1 对应的行下标

D_euc = pairwise_distances(Xstd, metric="euclidean")
D_man = pairwise_distances(Xstd, metric="manhattan")
S_cos = 1 - pairwise_distances(Xstd, metric="cosine")
D_raw = pairwise_distances(Xraw, metric="euclidean")

# --- 正向断言：距离矩阵自身的性质 ---
assert np.allclose(D_euc, D_euc.T), "欧氏距离矩阵不对称"
assert np.allclose(np.diag(D_euc), 0), "自距离不为 0"
assert np.allclose(np.diag(D_raw), 0), "未标准化自距离不为 0"
assert np.allclose(Xstd.mean(axis=0), 0, atol=1e-9), "标准化后均值不为 0"
assert np.allclose(Xstd.std(axis=0), 1, atol=1e-9), "标准化后标准差不等于 1"
assert int(df.isna().sum().sum()) == 0, "清洗后仍存在缺失值"
p("5.0 断言通过：距离矩阵对称、自距离为 0、标准化后均值 0 标准差 1、清洗后无缺失")

iu = np.triu_indices(N, 1)          # 上三角索引，天然排除对角线
off_euc = D_euc[iu]
off_raw = D_raw[iu]
off_cos = S_cos[iu]
imin = int(np.argmin(off_euc))
imax = int(np.argmax(off_euc))
p("5.1 标准化后欧氏距离：最小 %.4f（乘客 %d <-> %d），最大 %.4f（乘客 %d <-> %d），均值 %.4f，标准差 %.4f"
  % (off_euc[imin], pid[iu[0][imin]], pid[iu[1][imin]], off_euc[imax], pid[iu[0][imax]], pid[iu[1][imax]],
     off_euc.mean(), off_euc.std(ddof=1)))
R["euc_min"] = [jnum(off_euc[imin]), int(pid[iu[0][imin]]), int(pid[iu[1][imin]])]
R["euc_max"] = [jnum(off_euc[imax]), int(pid[iu[0][imax]]), int(pid[iu[1][imax]])]
R["euc_mean"] = [jnum(off_euc.mean()), jnum(off_euc.std(ddof=1))]

# 最近/最远一对的属性对照
def pair_attrs(i, j):
    return [[c, str(df.iloc[i][c]), str(df.iloc[j][c])] for c in sim_cols] + \
           [["Sex", df.iloc[i]["Sex"], df.iloc[j]["Sex"]],
            ["Pclass", str(df.iloc[i]["Pclass"]), str(df.iloc[j]["Pclass"])],
            ["Title", df.iloc[i]["Title"], df.iloc[j]["Title"]],
            ["Embarked", df.iloc[i]["Embarked"], df.iloc[j]["Embarked"]],
            ["Deck", df.iloc[i]["Deck"], df.iloc[j]["Deck"]]]
R["pair_min_attrs"] = pair_attrs(iu[0][imin], iu[1][imin])
R["pair_max_attrs"] = pair_attrs(iu[0][imax], iu[1][imax])
R["pair_min_ids"] = [int(pid[iu[0][imin]]), int(pid[iu[1][imin]])]
R["pair_max_ids"] = [int(pid[iu[0][imax]]), int(pid[iu[1][imax]])]

# 余弦相似度的整体水平
S_cos_raw = 1 - pairwise_distances(Xraw, metric="cosine")
off_cos_raw = S_cos_raw[iu]
p("5.1b 余弦相似度（标准化后向量）：均值 %.4f，标准差 %.4f，最小 %.4f，最大 %.4f"
  % (off_cos.mean(), off_cos.std(ddof=1), off_cos.min(), off_cos.max()))
p("     标准化使各变量均值为 0，行向量夹角余弦不再落在 [0,1]，其含义退化为行向量间的线性相关程度，故出现负值；"
  "未标准化时余弦相似度均值 %.4f、最小 %.4f，全部为正且高度集中，几乎不具区分能力（被 Fare 量级主导）"
  % (off_cos_raw.mean(), off_cos_raw.min()))
R["cos_stats"] = [jnum(off_cos.mean()), jnum(off_cos.std(ddof=1)), jnum(off_cos.min()), jnum(off_cos.max())]
R["cos_raw_stats"] = [jnum(off_cos_raw.mean()), jnum(off_cos_raw.std(ddof=1)), jnum(off_cos_raw.min()), jnum(off_cos_raw.max())]
R["raw_dist_stats"] = [jnum(off_raw.mean()), jnum(off_raw.std(ddof=1)), jnum(off_raw.max())]

# 目标乘客在“未标准化”尺度下的真实最近邻（须排除自身）
_t0 = D_raw[target].copy()
_t0[target] = np.inf
_raw_nn = int(np.argmin(_t0))
_te = D_euc[target].copy()
_te[target] = np.inf
_std_nn = int(np.argmin(_te))
R["nn_raw_target"] = [int(pid[_raw_nn]), jnum(float(_t0[_raw_nn]), 4)]
p("5.1c 未标准化尺度下，PassengerId=1 的真实最近邻是乘客 %d（欧氏距离 %.4f），标准化后最近邻是乘客 %d（距离 %.4f）"
  % (pid[_raw_nn], _t0[_raw_nn], pid[_std_nn], _te[_std_nn]))

np.fill_diagonal(D_euc, np.inf)
np.fill_diagonal(D_man, np.inf)
np.fill_diagonal(S_cos, -np.inf)
np.fill_diagonal(D_raw, np.inf)

nn_idx = D_euc.argmin(axis=1)
nn_dist = D_euc.min(axis=1)
R["nn_dist_stats"] = [jnum(np.mean(nn_dist), 4), jnum(np.std(nn_dist, ddof=1), 4), jnum(np.min(nn_dist), 4), jnum(np.max(nn_dist), 4)]

# 目标乘客示例：PassengerId = 1（target 已在 5.1 节定义）
order = np.argsort(D_euc[target])[:6]
rows = []
for j in order:
    rows.append([int(pid[target]), int(pid[j]), jnum(D_euc[target, j], 4), jnum(D_man[target, j], 4),
                 jnum(S_cos[target, j], 4), jnum(D_raw[target, j], 4)])
p("5.2 以 PassengerId=1 为目标，标准化欧氏距离最近的 6 位乘客（含原始未标准化距离对照）:")
for r in rows:
    p("    →%s  欧氏=%.4f  曼哈顿=%.4f  余弦相似=%.4f | 未标准化欧氏=%.3f" % (r[1], r[2], r[3], r[4], r[5]))
R["nn_demo"] = rows
R["nn_demo_header"] = ["目标乘客", "近邻乘客", "标准化欧氏距离", "曼哈顿距离", "余弦相似度", "未标准化欧氏距离"]

# 未标准化时最近邻是否变化（量纲影响）
nn_raw = D_raw.argmin(axis=1)
changed = int((nn_raw != nn_idx).sum())
p("5.3 未标准化与标准化下最近邻发生变化的乘客数：%d / %d（%.2f%%）→ 说明量纲对距离结果影响显著"
  % (changed, N, changed / N * 100))
R["nn_changed"] = [changed, N, round(changed / N * 100, 2)]

# --- Gower 距离（混合类型）---
num_g = ["Age", "Fare", "SibSp", "Parch", "FamilySize"]
cat_g = ["Sex", "Embarked", "Pclass", "Title", "Deck"]
Gn = df[num_g].astype(float).to_numpy()
rng = Gn.max(axis=0) - Gn.min(axis=0)
rng[rng == 0] = 1
Gn = (Gn - Gn.min(axis=0)) / rng
Dg = pairwise_distances(Gn, metric="manhattan")
for c in cat_g:
    codes = pd.factorize(df[c])[0]
    Dg += (codes[:, None] != codes[None, :]).astype(float)
Dg /= (len(num_g) + len(cat_g))
np.fill_diagonal(Dg, np.inf)
g_min_i = Dg.argmin()
p("5.4 Gower 距离（5 数值 + 5 类别，混合类型）：全局最小 %.4f（乘客 %d <-> %d），平均最近邻距离 %.4f"
  % (Dg.min(), pid[g_min_i // N], pid[g_min_i % N], Dg.min(axis=1).mean()))
R["gower_min"] = [jnum(Dg.min()), int(pid[g_min_i // N]), int(pid[g_min_i % N])]
R["gower_mean_nn"] = jnum(float(Dg.min(axis=1).mean()))
R["gower_header"] = num_g + cat_g

g_order = np.argsort(Dg[target])[:6]
g_rows = [[int(pid[target]), int(pid[j]), jnum(Dg[target, j], 4)] for j in g_order]
R["gower_demo"] = g_rows

# --- Jaccard 相似度（集合型表示）---
jac_src = ["Sex", "Pclass", "Embarked", "IsAlone", "Deck", "Title", "AgeGroup", "FareBand"]
jac_df = df[jac_src].astype(str)
jac_cols = pd.get_dummies(jac_df, columns=jac_src).astype(bool).to_numpy()
Dj = pairwise_distances(jac_cols, metric="jaccard")
Sj = 1 - Dj
off_j = Sj[np.triu_indices(N, 1)]
p("5.5 Jaccard 相似度（%d 个二元属性构成的属性集合）：全体样本对均值 %.4f，标准差 %.4f，最大 %.4f"
  % (jac_cols.shape[1], off_j.mean(), off_j.std(ddof=1), off_j.max()))
R["jaccard_n_attr"] = int(jac_cols.shape[1])
R["jaccard_stats"] = [jnum(off_j.mean()), jnum(off_j.std(ddof=1)), jnum(off_j.max()), jnum(off_j.min())]
jm = int(np.argmax(off_j)); jn = int(np.argmin(off_j))
p("    最相似一对：乘客 %d <-> %d（Jaccard=%.4f）；最不相似一对：乘客 %d <-> %d（Jaccard=%.4f）"
  % (pid[iu[0][jm]], pid[iu[1][jm]], off_j[jm], pid[iu[0][jn]], pid[iu[1][jn]], off_j[jn]))
R["jaccard_pairs"] = [[int(pid[iu[0][jm]]), int(pid[iu[1][jm]]), jnum(off_j[jm])],
                      [int(pid[iu[0][jn]]), int(pid[iu[1][jn]]), jnum(off_j[jn])]]
# 属性完全一致的一对，在数值距离度量下并不相同
R["jaccard_top_pair_euc"] = [jnum(float(D_euc[iu[0][jm], iu[1][jm]]), 4),
                             jnum(float(D_raw[iu[0][jm], iu[1][jm]]), 4)]
p("    Jaccard=1.0 的乘客 %d 与 %d：标准化欧氏距离 %.4f、未标准化欧氏距离 %.4f（属性全同但数值不同）"
  % (pid[iu[0][jm]], pid[iu[1][jm]], R["jaccard_top_pair_euc"][0], R["jaccard_top_pair_euc"][1]))

np.fill_diagonal(Dj, np.inf)
jac_order = np.argsort(Dj[target])[:6]
j_rows = [[int(pid[target]), int(pid[j]), jnum(Sj[target, j], 4), int(jac_cols[target].sum()), int(jac_cols[j].sum())]
          for j in jac_order]
p("    与乘客 1（属性集合大小 %d）最相似的前 6 位：" % int(jac_cols[target].sum()))
for r in j_rows:
    p("      →%s  Jaccard=%.4f（属性集合大小 %d）" % (r[1], r[2], r[4]))
R["jaccard_demo"] = j_rows
R["jaccard_demo_header"] = ["目标乘客", "近邻乘客", "Jaccard 相似度", "目标属性数", "近邻属性数"]

# =====================================================================
# 6 相关性分析
# =====================================================================
p("")
p("=" * 78)
p("6 相关性分析")
p("=" * 78)

cor_cols = ["Survived", "Pclass", "Age", "SibSp", "Parch", "Fare", "FamilySize", "IsAlone"]
C = df[cor_cols].astype(float)
pear = C.corr(method="pearson")
spear = C.corr(method="spearman")
R["corr_cols"] = cor_cols
R["pearson"] = [[jnum(v, 4) for v in row] for row in pear.to_numpy()]
R["spearman"] = [[jnum(v, 4) for v in row] for row in spear.to_numpy()]

p("6.1 与 Survived 的相关系数（Pearson / Spearman / p 值）:")
corr_with_surv = []
for c in cor_cols[1:]:
    rp, pp_ = stats.pearsonr(C["Survived"], C[c])
    rs, ps_ = stats.spearmanr(C["Survived"], C[c])
    kt, kp = stats.kendalltau(C["Survived"], C[c])
    corr_with_surv.append([c, jnum(rp), jnum(pp_, 6), jnum(rs), jnum(ps_, 6), jnum(kt), jnum(kp, 6)])
    p("    %-11s Pearson=%+.4f (p=%.3g)  Spearman=%+.4f (p=%.3g)  Kendall=%+.4f (p=%.3g)" % (c, rp, pp_, rs, ps_, kt, kp))
R["corr_with_surv"] = corr_with_surv
R["corr_with_surv_header"] = ["变量", "Pearson r", "p 值", "Spearman ρ", "p 值", "Kendall τ", "p 值"]

p("6.2 数值变量之间的强相关对（|r| ≥ 0.3）:")
strong = []
for i in range(len(cor_cols)):
    for j in range(i + 1, len(cor_cols)):
        v = pear.iloc[i, j]
        if abs(v) >= 0.3:
            strong.append([cor_cols[i], cor_cols[j], jnum(v, 4)])
            p("    %-11s <-> %-11s r=%+.4f" % (cor_cols[i], cor_cols[j], v))
R["strong_pairs"] = strong

# 卡方检验 + Cramer's V
def cramers_v(a, b):
    ct = pd.crosstab(a, b)
    chi2 = stats.chi2_contingency(ct, correction=False)[0]
    n = ct.to_numpy().sum()
    r, k = ct.shape
    phi2 = chi2 / n
    phi2corr = max(0, phi2 - (k - 1) * (r - 1) / (n - 1))
    rcorr = r - (r - 1) ** 2 / (n - 1)
    kcorr = k - (k - 1) ** 2 / (n - 1)
    return float(np.sqrt(phi2corr / min(kcorr - 1, rcorr - 1))), float(chi2), float(stats.chi2_contingency(pd.crosstab(a, b), correction=False)[1]), ct.shape

p("6.3 类别变量与 Survived 的卡方检验与 Cramér's V（含自由度）:")
chi_rows = []
for c in ["Sex", "Pclass", "Embarked", "Title", "Deck", "AgeGroup", "IsAlone"]:
    v, chi2, pv, shape = cramers_v(df[c], df["Survived"])
    dof = (shape[0] - 1) * (shape[1] - 1)
    chi_rows.append([c, jnum(chi2, 3), dof, ("<1e-300" if pv == 0 else "%.3g" % pv), jnum(v, 4)])
    p("    %-9s chi2=%9.3f  df=%2d  p=%s  Cramér's V=%.4f" % (c, chi2, dof, ("<1e-300" if pv == 0 else "%.3g" % pv), v))
R["chi_rows"] = chi_rows
R["chi_header"] = ["类别变量", "chi2 统计量", "自由度", "p 值", "Cramér's V"]

# 方差膨胀因子 VIF（分两步：先看不含派生列的集合，再加入 FamilySize 暴露完全共线性）
def vif_of(cols):
    Cm = df[cols].astype(float).corr().to_numpy()
    inv = np.linalg.inv(Cm)
    return [jnum(float(inv[i, i]), 4) for i in range(len(cols))], float(np.linalg.cond(Cm))

vif_cols = ["Age", "Fare", "SibSp", "Parch"]
v_a, cond_a = vif_of(vif_cols)
vif_cols_b = vif_cols + ["FamilySize"]
v_b, cond_b = vif_of(vif_cols_b)
p("6.4 方差膨胀因子 VIF（>10 视为严重共线性）:")
p("    集合A %s → %s，相关矩阵条件数 %.2f" % (vif_cols, v_a, cond_a))
p("    集合B %s → %s，相关矩阵条件数 %.3e ← FamilySize=SibSp+Parch+1 与分量完全共线，矩阵近奇异"
  % (vif_cols_b, ["%.3e" % x for x in v_b], cond_b))
R["vif"] = [[vif_cols[i], v_a[i]] for i in range(len(vif_cols))]
R["vif_b"] = [[vif_cols_b[i], ("%.3e" % v_b[i])] for i in range(len(vif_cols_b))]
R["vif_cond"] = [jnum(cond_a, 3), "%.3e" % cond_b]

# =====================================================================
# 7 图
# =====================================================================
p("")
p("=" * 78)
p("7 绘图")
p("=" * 78)
figs = []

# 图1 缺失值
fig, axes = plt.subplots(1, 2, figsize=(8.2, 2.9))
mc = raw.isna().sum()
mc = mc[mc > 0].sort_values()
axes[0].barh(mc.index, mc.values, color="#c0392b")
for i, v in enumerate(mc.values):
    axes[0].text(v + 8, i, "%d (%.1f%%)" % (v, v / len(raw) * 100), va="center", fontsize=9.8)
axes[0].set_xlim(0, 800)
axes[0].set_title("清洗前各字段缺失值数量", fontsize=12.3)
axes[0].set_xlabel("缺失条数", fontsize=10.4)
axes[0].tick_params(labelsize=7.5)
after = df.isna().sum()
axes[1].bar(["清洗前", "清洗后"], [raw.isna().sum().sum(), after.sum()], color=["#c0392b", "#27ae60"], width=0.5)
for i, v in enumerate([raw.isna().sum().sum(), after.sum()]):
    axes[1].text(i, v + 15, str(v), ha="center", fontsize=11.1)
axes[1].set_ylim(0, 980)
axes[1].set_title("缺失单元格总数：清洗前后", fontsize=12.3)
axes[1].set_ylabel("缺失单元格数", fontsize=10.4)
axes[1].tick_params(labelsize=7.5)
fig.tight_layout()
f1 = os.path.join(OUT, "fig1_missing.png"); fig.savefig(f1); plt.close(fig); figs.append(f1)

# 图2 Age/Fare 分布与变换
fig, axes = plt.subplots(2, 2, figsize=(8.2, 4.8))
axes[0, 0].hist(df["Age"], bins=30, color="#2980b9", edgecolor="white")
axes[0, 0].set_title("Age 分布（填补后）偏度=%.2f" % df["Age"].skew(), fontsize=11.7)
axes[0, 1].hist(df["Fare"], bins=40, color="#c0392b", edgecolor="white")
axes[0, 1].set_title("Fare 原始分布 偏度=%.2f 峰度=%.2f" % (skew_before, kurt_before), fontsize=11.7)
axes[1, 0].hist(df["FareLog"], bins=40, color="#27ae60", edgecolor="white")
axes[1, 0].set_title("Fare 对数变换 log1p 后 偏度=%.2f" % skew_after, fontsize=11.7)
axes[1, 1].hist(df["FamilySize"], bins=range(1, 12), color="#8e44ad", edgecolor="white", align="left")
axes[1, 1].set_title("家庭规模 FamilySize 分布", fontsize=11.7)
for ax, xl in zip(axes.ravel(), ["年龄", "票价(英镑)", "log1p(票价)", "家庭规模（人）"]):
    ax.set_xlabel(xl, fontsize=10.4); ax.tick_params(labelsize=7.5)
fig.tight_layout()
f2 = os.path.join(OUT, "fig2_dist.png"); fig.savefig(f2); plt.close(fig); figs.append(f2)

# 图3 箱线图
fig, axes = plt.subplots(1, 4, figsize=(8.2, 2.9))
for ax, c in zip(axes, ["Age", "Fare", "SibSp", "Parch"]):
    bp = ax.boxplot(df[c].astype(float), patch_artist=True, widths=0.5, flierprops=dict(marker="o", markersize=2.5, markerfacecolor="#c0392b", markeredgecolor="#c0392b"))
    bp["boxes"][0].set_facecolor("#aed6f1")
    ax.set_title(c, fontsize=11.7)
    ax.tick_params(labelsize=7.5)
fig.suptitle("数值变量箱线图（红点为 IQR 准则下的离群点）", fontsize=12.3)
fig.tight_layout()
f3 = os.path.join(OUT, "fig3_box.png"); fig.savefig(f3); plt.close(fig); figs.append(f3)

# 图4 生存率
fig, axes = plt.subplots(1, 3, figsize=(8.4, 2.9))
t = df.groupby(["Pclass", "Sex"], observed=True)["Survived"].mean().unstack() * 100
x = np.arange(len(t.index)); w = 0.36
axes[0].bar(x - w / 2, t["female"], w, label="female", color="#e84393")
axes[0].bar(x + w / 2, t["male"], w, label="male", color="#0984e3")
axes[0].set_xticks(x); axes[0].set_xticklabels(["1等", "2等", "3等"], fontsize=10.4)
axes[0].set_ylabel("生存率 (%)", fontsize=10.4); axes[0].legend(fontsize=9.8)
axes[0].set_title("舱位 × 性别 生存率", fontsize=11.7)
a = df.groupby("AgeGroup", observed=True)["Survived"].mean().reindex(age_labels) * 100
axes[1].bar(range(len(a)), a.values, color="#00b894")
axes[1].set_xticks(range(len(a))); axes[1].set_xticklabels(["0-12", "13-18", "19-35", "36-60", "61+"], fontsize=10.4)
axes[1].set_title("年龄组生存率", fontsize=11.7)
e = df.groupby("Embarked", observed=True)["Survived"].mean() * 100
axes[2].bar(e.index, e.values, color="#fdcb6e")
axes[2].set_title("登船港生存率", fontsize=11.7)
for ax in axes:
    ax.tick_params(labelsize=7.5); ax.grid(axis="y", alpha=0.3, linestyle=":")
for i, v in enumerate(a.values):
    axes[1].text(i, v + 1.5, "%.1f" % v, ha="center", fontsize=8.5)
for i, v in enumerate(e.values):
    axes[2].text(i, v + 1.5, "%.1f" % v, ha="center", fontsize=8.5)
fig.tight_layout()
f4 = os.path.join(OUT, "fig4_survival.png"); fig.savefig(f4); plt.close(fig); figs.append(f4)

# 图5 相关热力图（下三角 Pearson，上三角 Spearman）
fig, ax = plt.subplots(figsize=(6.6, 5.4))
M = pear.to_numpy().copy()
Ms = spear.to_numpy().copy()
mask_low = np.tril(np.ones_like(M, dtype=bool), -1)
M2 = np.where(mask_low, M, np.nan)
M2 = np.where(np.triu(np.ones_like(M, dtype=bool), 1), Ms, M2)
im = ax.imshow(M2, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(cor_cols))); ax.set_xticklabels(cor_cols, rotation=45, ha="right", fontsize=10.4)
ax.set_yticks(range(len(cor_cols))); ax.set_yticklabels(cor_cols, fontsize=10.4)
for i in range(len(cor_cols)):
    for j in range(len(cor_cols)):
        if i != j:
            ax.text(j, i, "%.2f" % M2[i, j], ha="center", va="center", fontsize=8.1,
                    color="white" if abs(M2[i, j]) > 0.55 else "black")
fig.colorbar(im, ax=ax, shrink=0.82)
ax.set_title("相关系数热力图（下三角 Pearson，上三角 Spearman）", fontsize=12.3)
fig.tight_layout()
f5 = os.path.join(OUT, "fig5_corr.png"); fig.savefig(f5); plt.close(fig); figs.append(f5)

# 图6 相似性
fig, axes = plt.subplots(1, 3, figsize=(8.6, 2.9))
sub = D_euc[:80, :80].copy()
sub[np.isinf(sub)] = 0
im = axes[0].imshow(sub, cmap="viridis")
axes[0].set_title("前 80 名乘客标准化欧氏距离矩阵", fontsize=11.1)
fig.colorbar(im, ax=axes[0], shrink=0.85)
axes[1].hist(nn_dist, bins=40, color="#6c5ce7", edgecolor="white")
axes[1].axvline(nn_dist.mean(), color="#e17055", linestyle="--", linewidth=1.2, label="均值 %.3f" % nn_dist.mean())
axes[1].set_title("每位乘客到最近邻的距离分布", fontsize=11.1)
axes[1].set_xlabel("最近邻欧氏距离", fontsize=10.4); axes[1].legend(fontsize=9.1)
axes[2].hist(D_raw[np.isfinite(D_raw)].ravel()[:400000], bins=50, color="#d63031", alpha=0.75, density=True, label="未标准化")
axes[2].hist(D_euc[np.isfinite(D_euc)].ravel()[:400000], bins=50, color="#0984e3", alpha=0.65, density=True, label="标准化后")
axes[2].set_title("距离分布：标准化前后对比", fontsize=11.1)
axes[2].set_xlabel("欧氏距离", fontsize=10.4); axes[2].legend(fontsize=9.1)
for ax in axes:
    ax.tick_params(labelsize=7)
fig.tight_layout()
f6 = os.path.join(OUT, "fig6_similarity.png"); fig.savefig(f6); plt.close(fig); figs.append(f6)

R["figs"] = [os.path.basename(f) for f in figs]
for f in figs:
    p("   已生成:", os.path.basename(f), os.path.getsize(f), "bytes")

# =====================================================================
with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as fh:
    json.dump(R, fh, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "console_report.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(LOG))
p("")
p("完成。results.json 键数 %d" % len(R))
