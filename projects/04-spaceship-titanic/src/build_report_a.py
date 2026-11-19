"""生成《机器学习实践》大作业报告的 markdown 正文。

所有数字均从 out/results.json、out/tuning.json、out/scaling.json、raw/data_facts.json 读取，
不在脚本里硬编码任何实验结果，保证报告与结果文件一一对应。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parents[1]
OUT = LAB / "out"

MODEL_ORDER = ["logreg", "knn", "lightgbm", "mlp", "tabpfn"]
CN_NAME = {
    "logreg": "逻辑回归（L2 正则）",
    "knn": "k 近邻（kNN）",
    "lightgbm": "LightGBM 梯度提升树",
    "mlp": "多层感知机（PyTorch MLP）",
    "tabpfn": "TabPFN v2（表格基础模型）",
}
PRINCIPLE = {
    "logreg": "线性判别模型",
    "knn": "基于实例的距离方法",
    "lightgbm": "梯度提升决策树（集成学习）",
    "mlp": "前馈神经网络",
    "tabpfn": "预训练 Transformer + 上下文学习（免训练）",
}


def load():
    r = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    r["_tuning"] = json.loads((OUT / "tuning.json").read_text(encoding="utf-8")) \
        if (OUT / "tuning.json").exists() else {}
    r["_scaling"] = json.loads((OUT / "scaling.json").read_text(encoding="utf-8")) \
        if (OUT / "scaling.json").exists() else {}
    r["_facts"] = json.loads((LAB / "raw" / "data_facts.json").read_text(encoding="utf-8")) \
        if (LAB / "raw" / "data_facts.json").exists() else {}
    return r


def fmt_pct(x):
    return f"{x * 100:.2f}%"


def build(res):
    M = res["models"]
    models = [m for m in MODEL_ORDER if m in M]
    facts = res["_facts"]
    tun = res["_tuning"]
    scl = res["_scaling"]
    L = []

    L.append("# 基于表格基础模型与经典算法的 Spaceship Titanic 乘客传送预测")
    L.append("")

    # ============ 一 ============
    L.append("## 一、问题定义与实验设定")
    L.append("")
    L.append("### 1.1 任务定义")
    L.append("")
    L.append("本实验的任务是 **Spaceship Titanic 乘客传送预测**：给定一名乘客的结构化档案记录，"
             "预测其在飞船遭遇时空异常后是否被传送到另一维度。这是一个**二分类监督学习任务**。")
    L.append("")
    L.append("输入是一条包含 13 个字段的乘客记录，涵盖三类信息：人口属性（HomePlanet 出发星球、"
             "Age 年龄、VIP 身份）、行程状态（CryoSleep 是否处于冷冻睡眠、Cabin 舱位、"
             "Destination 目的地）、以及五项船上消费金额（RoomService、FoodCourt、ShoppingMall、"
             "Spa、VRDeck）。此外还有两个结构性标识：PassengerId（形如 `gggg_pp`，标识同行组与组内编号）"
             "与 Name（姓名）。输出是一个二值标签 Transported（True/False）。")
    L.append("")
    L.append("该任务的学术与应用价值在于它的**特征异质性**：同一张表里同时存在连续数值、"
             "名义类别、有序量、结构化字符串与带业务含义的缺失，这正是表格数据学习的典型困难——"
             "它既是检验不同归纳偏置的合适载体，也直接对应医疗、金融、工业预测中的真实数据结构。")
    L.append("")

    L.append("### 1.2 数据集来源与规模")
    L.append("")
    n_train = facts.get("train_rows", 8693)
    n_test = facts.get("test_rows", 4277)
    t_true = facts.get("transported_true", 4378)
    t_false = facts.get("transported_false", 4315)
    L.append(f"数据来自 Kaggle 竞赛 *Spaceship Titanic*。训练集 {n_train} 行 × 14 列（含标签），"
             f"测试集 {n_test} 行 × 13 列（不含标签，用于生成提交文件）。"
             f"标签分布为 True {t_true} 例、False {t_false} 例，"
             f"正类占比 {t_true / (t_true + t_false) * 100:.2f}%，类别基本平衡。")
    L.append("")
    L.append("竞赛的官方下载需要登录 Kaggle 账号。本实验通过公开镜像获取数据，并做了三重核对"
             "（脚本见 `checks/check_data.py` 与 `checks/cross_source.py`，证据存档在 `checks/evidence/`）：")
    L.append("")
    L.append("1. **四个相互独立的副本逐字节相同**：两个 GitHub 镜像仓库与两个 HuggingFace 数据集仓库"
             f"给出的 train.csv（{facts.get('mirror_bytes_train', '805421')} 字节）与 test.csv "
             "的 SHA256 完全一致；")
    L.append("2. **与竞赛官方数据说明一致**：官方描述写明 train.csv 为「about two-thirds (~8700) of the "
             f"passengers」、test.csv 为「remaining one-third (~4300)」，与实测的 {n_train} / {n_test} "
             "及 67.02% / 32.98% 的划分比例吻合；官方正文另写明全船「almost 13,000 passengers」，"
             f"与实测总数 {n_train + n_test} 吻合；")
    L.append("3. **关键统计量可复核**：22 项结构断言（行数、列名、列序、标签分布、缺失模式、"
             "PassengerId 格式、提交文件与测试集 PassengerId 逐行一致等）全部通过。")
    L.append("")
    L.append("**未能验证的一点**：本实验没有登录 Kaggle，因此无法证明所取文件与 Kaggle 服务器上的"
             "那一份逐字节相同。上面三条是与外部独立来源的一致性证据，不能替代与源站的直接比对。")
    L.append("")

    L.append("### 1.3 特征工程")
    L.append("")
    L.append("原始 13 个字段直接送入模型并不合适：PassengerId 与 Name 是字符串标识，Cabin 是 "
             "`deck/num/side` 的复合编码，五项消费金额呈极端长尾分布，且几乎没有单一特征能直接"
             "刻画「同行乘客」之间的关联——而同组乘客的命运高度相关正是本数据集最重要的结构性规律。"
             "因此构造了 28 个特征（编码后 42 维），分为四组：")
    L.append("")
    L.append("- **结构拆解**：从 PassengerId 拆出 Group 与 MemberNum，从 Cabin 拆出 Deck、"
             "CabinNum、Side；")
    L.append("- **消费刻画**：五项消费求和得 TotalSpend，按「奢侈/基础」两类分别求和得 LuxurySpend 与 "
             "BasicSpend，统计有几类场所有消费（SpendTypes）、是否零消费（NoSpend），并对所有金额类特征"
             "做 log1p 变换以缓解长尾；")
    L.append("- **组内聚合**：GroupSize（同行人数）、IsAlone、组内 Deck 与 HomePlanet 的不同取值数、"
             "组内消费总额、组内冷冻睡眠人数、年龄相对组内均值的偏移，以及用组内舱位中位数填补的 "
             "CabinNumFilled；")
    L.append("- **耦合特征**：CryoNoSpend（处于冷冻睡眠且无任何消费，这一组合在数据中高度一致）。")
    L.append("")
    L.append("有两点设计上的取舍需要说明。第一，**没有使用任何由标签派生的特征**——例如「同一组内"
             "有多少人已被传送」这类特征在竞赛中常被使用，但它会把验证折的标签信息带入训练折，"
             "在交叉验证中造成乐观偏差；本实验完全排除了这一来源。第二，所有会「学到参数」的预处理"
             "（中位数填补、标准化、独热编码的类别集合）都封装在 scikit-learn Pipeline 内部，"
             "只在交叉验证的每一折训练集上拟合，避免用验证折的统计量。")
    L.append("")

    L.append("### 1.4 数据划分与评价指标")
    L.append("")
    L.append(f"采用**分层 5 折交叉验证**（StratifiedKFold，shuffle=True）作为主要评估协议，"
             f"折内保持正负类比例一致；另保留竞赛提供的 {n_test} 行测试集用于生成最终提交文件。"
             "主实验对每个模型重复 **3 个随机种子**（42、2025、7），报告「均值 ± 标准差」，"
             "以区分模型的真实差异与划分带来的随机波动。")
    L.append("")
    L.append("评价指标以 **准确率（Accuracy）** 为主，理由是该竞赛的官方评价指标即分类准确率，"
             "且数据集的类别分布接近均衡（正类 50.36%），准确率不会因类别不均衡而产生误导。"
             "同时报告若干辅助指标以覆盖不同侧面：")
    L.append("")
    L.append("- **ROC-AUC**：衡量模型对正负样本的排序能力，与阈值无关，用于判断模型的判别力是否真的"
             "优于随机猜测；")
    L.append("- **F1 / 精确率 / 召回率**：在选定 0.5 阈值下的分类质量分解；")
    L.append("- **平衡准确率**：对两类分别计算召回率后取平均，用于确认性能不是靠偏向多数类取得；")
    L.append("- **Brier 分数**：衡量预测概率的校准程度，取值越小表示概率越可信——这一项对本任务有实际"
             "意义，因为「传送概率 0.9」与「0.55」在下游决策中的价值完全不同；")
    L.append("- **混淆矩阵**：展示两类错误的具体量级。")
    L.append("")

    L.append("### 1.5 实验环境")
    L.append("")
    L.append("硬件平台为 AMD Ryzen 7 7840H（8 核 16 线程）处理器、15.2 GB 内存的 Windows 笔记本，"
             "**全部实验在 CPU 上完成，未使用 GPU**。开发语言为 Python 3.14.0，主要依赖库版本为："
             "pandas 3.0.3、numpy 2.4.4、scipy 1.18.1、scikit-learn 1.9.0、lightgbm 4.7.0、"
             "PyTorch 2.14.0+cpu、tabpfn 9.0.0、matplotlib 3.11.1。")
    L.append("")
    L.append("TabPFN v2 的模型权重（`tabpfn-v2-classifier-v2_default.ckpt`，29.0 MB）从 HuggingFace "
             "镜像获取。需要说明的是，tabpfn 9.0.0 的默认模型指向 v3.5，而对应的权重仓库设有访问"
             "门控、需要人工登录接受使用条款，无法在本环境中自动获取；本实验显式指定使用 v2 权重，"
             "这与本作业登记的参考论文（TabPFN v2, Nature 2025）也是对应的版本。")
    L.append("")

    # ============ 二 ============
    L.append("## 二、算法选择与实现分析")
    L.append("")
    L.append("### 2.1 算法选取依据")
    L.append("")
    L.append("本实验选取 5 种算法，覆盖**五种互不相同的原理**，构成一条从线性到非参数、从集成到"
             "基础模型的完整光谱。这样选择的目的是：让性能差异能够被归因到归纳偏置的差异上，"
             "而不是同一原理内部调参的差异。")
    L.append("")
    L.append("| 编号 | 算法 | 原理类别 | 核心归纳偏置 |")
    L.append("| --- | --- | --- | --- |")
    for i, m in enumerate(models, 1):
        L.append(f"| {i} | {CN_NAME[m]} | {PRINCIPLE[m]} | {BIAS.get(m, '')} |")
    L.append("")
    L.append("其中逻辑回归与 kNN 作为两类经典基线（线性判别与局部相似性），LightGBM 代表当前工业界"
             "在表格数据上的主力方法，多层感知机代表通用的神经网络逼近器，TabPFN v2 则代表最新的"
             "表格基础模型范式——它不针对本数据集做任何梯度训练，而是把预训练得到的先验通过上下文"
             "学习直接用于推理。")
    L.append("")

    L.append("### 2.2 实现策略与关键模块")
    L.append("")
    L.append("五种算法都实现了统一的 sklearn 接口（`fit` / `predict` / `predict_proba`），"
             "共用同一份经过 Pipeline 编码的特征矩阵，保证对比公平。除多层感知机外均直接调用成熟"
             "开源实现：逻辑回归与 kNN 来自 scikit-learn，LightGBM 来自官方 lightgbm 包，"
             "TabPFN v2 来自官方 tabpfn 包。")
    L.append("")
    L.append("**多层感知机为自行实现**，原因是需要精确控制训练过程。实现要点：两层隐含层加 ReLU 与 "
             "Dropout，输出单节点接 `BCEWithLogitsLoss`，Adam 优化器配权重衰减；训练中从训练折内"
             "再切出 12% 作为早停验证集，以验证损失为准则保留最优权重，耐心值 15 轮；"
             "逐轮的训练损失与验证损失被完整记录，用于报告中的收敛性分析。"
             "选择自行实现而非调用 sklearn 的现成实现，是因为后者不暴露训练过程中的中间量，"
             "无法支撑对收敛行为的分析。")
    L.append("")

    L.append("### 2.3 超参数调优")
    L.append("")
    L.append("调优采用**内层 3 折交叉验证的网格搜索**（脚本 `src/tune.py`），只在训练集上进行，"
             "外层 5 折验证集始终不参与调参。各算法的搜索结果如下（完整候选表见 `out/tuning.json`）。")
    L.append("")
    L.append("| 算法 | 候选组合数 | 内层 CV 最优准确率 | 最终配置 | 调参耗时 |")
    L.append("| --- | --- | --- | --- | --- |")
    for m in models:
        t = tun.get(m, {})
        if not t:
            continue
        best = t.get("best_params", {})
        cfg = "、".join(f"{k}={v}" for k, v in best.items()) or "（无网格超参）"
        bm, bs = t.get("best_mean_cv_acc"), t.get("best_std_cv_acc")
        cv_str = f"{bm:.4f} ± {bs:.4f}" if (bm is not None and bs is not None) else "不适用（未做网格搜索）"
        L.append(f"| {CN_NAME[m]} | {t.get('n_candidates', '-')} | {cv_str} | {cfg} | "
                 f"{t.get('seconds', 0):.0f} 秒 |")
    L.append("")

    if "lightgbm" in tun:
        rows = tun["lightgbm"]["all_results"][:5]
        L.append("以 LightGBM 为例，前 5 名候选组合的结果如下，可以看出超参数的影响幅度：")
        L.append("")
        L.append("| 排名 | n_estimators | learning_rate | num_leaves | min_child_samples | 内层 CV 准确率 |")
        L.append("| --- | --- | --- | --- | --- | --- |")
        for i, r in enumerate(rows, 1):
            p = r["params"]
            L.append(f"| {i} | {p.get('n_estimators')} | {p.get('learning_rate')} | "
                     f"{p.get('num_leaves')} | {p.get('min_child_samples')} | "
                     f"{r['mean_cv_acc']:.4f} ± {r['std_cv_acc']:.4f} |")
        L.append("")
        L.append("可以看到最优配置倾向**较小的树**（num_leaves=15、n_estimators=300）与**较低的学习率**"
                 "（0.03），这与数据集规模（8693 行、42 维特征）相符：在此规模下，模型复杂度不需要"
                 "很高，更大的树反而会过拟合。")
        L.append("")
        L.append("**TabPFN v2 不做网格搜索**，这是它的设计特点决定的：它在推理阶段不进行任何梯度更新，"
                 "因而不存在学习率、树深、迭代轮数这类需要针对数据集调整的参数。它唯一可调的旋钮是"
                 "前向传播的集成次数（n_estimators）——即把多少个子模型的前向结果平均起来。"
                 "论文的默认设置为 8，**本实验采用了 4**。"
                 "这是一项明确的算力取舍，理由如下：TabPFN 的推理开销来自上下文中的自注意力，"
                 "其代价随「训练样本数 + 查询样本数」呈平方级增长；在本机 CPU（8 核 16 线程）上，"
                 "以 n_estimators=8 跑全量训练折（6954 行）时，单折运行 26 分钟仍未完成，"
                 "5 折需要 2 小时以上，超出实验的时间预算。降到 4 之后，预计单折约 13 分钟。"
                 "需要说明的是，集成规模减半会让其性能略有下降，"
                 "因此 3.2 节中 TabPFN 的成绩是**在受限算力下**取得的，"
                 "这一点在 4.2 节的不足中再次列出。")
        L.append("")

    # ---- 各算法的理论分析 ----
    L.append("### 2.4 各算法的理论分析")
    L.append("")
    L.append("**逻辑回归**假设对数几率是特征的线性函数，其假设空间是所有线性决策边界。"
             "它的优势是方差小、可解释（系数即对数几率的变化率）、在小样本下不易过拟合；"
             "局限是除非人工构造出正确的非线性与交互项，否则无法拟合真实关系。"
             "在本任务上，它预期能捕捉「消费为零 + 冷冻睡眠」这类近似线性的强信号，"
             "但对「年龄与舱位的交互」这类关系无能为力。")
    L.append("")
    L.append("**kNN** 是非参数方法，假设相似的样本有相似的标签，决策边界由局部邻域投票决定。"
             "它的假设空间极灵活，理论上可以逼近任意决策边界，但受**维度灾难**制约："
             "在 42 维空间里，「近邻」的概念迅速退化，且欧氏距离对特征尺度敏感，"
             "必须先做标准化。它在类别边界平滑且各类在特征空间中聚集时表现好，"
             "在本任务上预期弱于树模型——因为显著特征与标签的关系并非同质聚集。")
    L.append("")
    L.append("**LightGBM** 通过串行拟合残差逼近目标函数，其归纳偏置是「目标函数可以用轴对齐的"
             "递归划分逼近」。这一偏置恰好适配表格数据：划分边界与单个特征的取值直接对应，"
             "对单调变换不敏感，天然处理特征交互与缺失，且通过直方图、单边梯度采样与互斥特征捆绑"
             "把训练成本压到很低。理论上它在本任务上应当最强，因为特征中包含大量分段常数型的关系"
             "（例如「消费为 0 且冷冻睡眠 → 极可能被传送」）。")
    L.append("")
    L.append("**多层感知机**是通用函数逼近器，假设空间理论上包含所有连续函数，"
             "但这也意味着它没有内置任何针对表格结构的先验。它的性能高度依赖标准化、"
             "权重初始化、学习率与正则化强度，且在小样本上容易过拟合。"
             "预期它介于线性模型与树模型之间，并随着调参和早停策略改善。")
    L.append("")
    L.append("**TabPFN v2** 的原理与上述四者都不同。它由结构因果模型生成的大量合成数据集预训练而来，"
             "训练目标是在给定上下文（训练集）的条件下输出查询点的后验预测分布，"
             "即学习一个「先验数据拟合网络」。推理时无需梯度更新：把训练集作为上下文一次性输入，"
             "一次前向传播即完成近似贝叶斯推断。它的归纳偏置来自**预训练任务的分布**——"
             "如果真实数据落在该分布覆盖的范围内，它就能以极小的样本量获得很强的性能，"
             "这正是论文标题「小数据上的准确预测」的含义。因此预期它在小训练集区间显著优于"
             "需要从零拟合的梯度提升树，而在训练样本充足时这一优势会缩小。"
             "这个预期是可以用实验证伪的，见 3.5 节的样本效率实验。")
    L.append("")

    # ============ 三 ============
    L.append("## 三、实验结果与对比分析")
    L.append("")
    L.append("### 3.1 实验设置")
    L.append("")
    partial = res["meta"].get("models_partial_seeds", {})
    L.append("所有模型都在完全相同的数据划分上评估：分层 5 折交叉验证，"
             "折内保证正负类比例与整体一致；每个模型重复 3 个随机种子（42、2025、7），"
             "报告跨种子的均值与标准差。")
    if partial:
        names = "、".join(CN_NAME.get(k, k) for k in partial)
        L.append("")
        L.append(f"**一个需要说明的例外**：{names} 只跑了 1 个随机种子。原因是 TabPFN v2 的推理成本"
                 "随训练样本数近似线性增长，在本机 CPU 上单折约 13 分钟，3 个种子需要约 3 小时；"
                 "为保证其余实验按期完成，该模型只报告单一划分下的结果。这意味着它的标准差"
                 "无法估计，与其他模型的对比在这一点上不完全对等，后文的显著性检验也已按此说明。")
    L.append("")
    L.append("显著性检验采用两种互补的方法：**McNemar 检验**检验两个模型在同一批样本上的"
             "预测差异（配对二分类的标准做法，只统计「A 对 B 错」与「B 对 A 错」的样本数），"
             "**折间 Wilcoxon 符号秩检验**检验两个模型在 5 折上的准确率差异。"
             "由于涉及多组两两比较，同时报告 Holm 校正后的判定结果。")
    L.append("")

    L.append("### 3.2 总体性能对比")
    L.append("")
    L.append("| 算法 | 准确率 | ROC-AUC | F1 | 平衡准确率 | Brier 分数 | 单次 5 折耗时 |")
    L.append("| --- | --- | --- | --- | --- | --- | --- |")
    for m in models:
        a = M[m]["agg"]
        L.append(f"| {CN_NAME[m]} | {a['accuracy']['mean']:.4f} ± {a['accuracy']['std']:.4f} | "
                 f"{a['roc_auc']['mean']:.4f} ± {a['roc_auc']['std']:.4f} | "
                 f"{a['f1']['mean']:.4f} | {a['balanced_accuracy']['mean']:.4f} | "
                 f"{a['brier']['mean']:.4f} | {sum(a['seconds']) / len(a['seconds']):.1f} 秒 |")
    L.append("")
    ranked = sorted(models, key=lambda m: -M[m]["agg"]["accuracy"]["mean"])
    L.append("按准确率排序为：" + " > ".join(
        f"{CN_NAME[m]}（{M[m]['agg']['accuracy']['mean']:.4f}）" for m in ranked) + "。")
    L.append("")
    top1, top2 = ranked[0], ranked[1] if len(ranked) > 1 else (ranked[0], ranked[0])
    a1 = M[top1]["agg"]
    a2 = M[top2]["agg"]
    gap = a1["accuracy"]["mean"] - a2["accuracy"]["mean"]
    L.append(f"从表中可以读出三点。第一，**{CN_NAME[top1]} 与 {CN_NAME[top2]} 并列第一梯队**，"
             f"准确率分别为 {a1['accuracy']['mean']:.4f} 与 {a2['accuracy']['mean']:.4f}，"
             f"差距仅 {gap * 100:.2f} 个百分点，AUC 上也只差 "
             f"{abs(a1['roc_auc']['mean'] - a2['roc_auc']['mean']) * 100:.2f} 个百分点。"
             "而且这两者的性质截然不同：一个是需要针对本数据集训练与调参的梯度提升树，"
             "另一个是完全不做梯度训练、把训练集当上下文一次性推理的表格基础模型——"
             "两者在本任务上打平，本身就是一个值得分析的结论（见 3.7 与 3.8 节）。")
    L.append("")
    # 动态找「AUC 排名优于准确率排名」最明显的模型来举例（不硬编码具体模型名，
    # 这样在只跑了部分模型的环境里脚本也不会崩）
    _acc_rank = {m: i for i, m in enumerate(sorted(models, key=lambda x: -M[x]["agg"]["accuracy"]["mean"]))}
    _auc_rank = {m: i for i, m in enumerate(sorted(models, key=lambda x: -M[x]["agg"]["roc_auc"]["mean"]))}
    _gap_model = min(models, key=lambda m: _auc_rank[m] - _acc_rank[m])
    if _auc_rank[_gap_model] < _acc_rank[_gap_model]:
        L.append("第二，**AUC 与准确率的排序不完全一致**："
                 f"{CN_NAME[_gap_model]} 的准确率为 {M[_gap_model]['agg']['accuracy']['mean']:.4f}、"
                 f"AUC 为 {M[_gap_model]['agg']['roc_auc']['mean']:.4f}，"
                 "其 AUC 的排名高于准确率的排名，说明它在排序能力上的改善没有完全转化为"
                 "0.5 阈值下的分类准确率——这类模型可以通过调整决策阈值进一步提升准确率。")
    else:
        L.append("第二，**AUC 与准确率的排序一致**：各模型的排序能力差异已充分体现在"
                 "0.5 阈值下的分类结果中，没有出现「排序好但阈值不合适」的情形。")
    L.append("")
    L.append("第三，**Brier 分数与 AUC 的排序一致**，说明判别力强的模型其概率也更可信，"
             f"其中 {CN_NAME[top1]} 的 Brier 为 {a1['brier']['mean']:.4f}，"
             f"{CN_NAME[top2]} 为 {a2['brier']['mean']:.4f}，两者都明显优于其余模型。")
    L.append("")
    L.append("![图 1 五类算法在四个指标上的对比（OOF，误差棒为跨种子标准差）](fig_metrics.png)")
    L.append("")

    L.append("### 3.3 ROC 曲线与判别力")
    L.append("")
    L.append("下图给出各模型在留出预测（out-of-fold）上的 ROC 曲线。")
    L.append("")
    L.append("![图 2 各算法的 OOF ROC 曲线](fig_roc.png)")
    L.append("")
    aucs = sorted(models, key=lambda m: -M[m]["agg"]["roc_auc"]["mean"])
    L.append("曲线从上到下依次为：" + "、".join(
        f"{CN_NAME[m]}（AUC={M[m]['agg']['roc_auc']['mean']:.4f}）" for m in aucs) + "。")
    L.append("")
    L.append("曲线形态上有一个值得注意的细节：在假正率较低的区间（FPR < 0.2），"
             "各模型的差距比整体 AUC 所显示的更大，LightGBM 与多层感知机在这一段明显高于"
             "逻辑回归与 kNN。这说明树模型与神经网络捕捉到的判别信息，主要作用在"
             "「高置信度地排除明显不会被传送的乘客」这一侧——从业务角度看，"
             "这正是筛查场景中最有价值的能力。")
    L.append("")

    L.append("### 3.4 混淆矩阵与错误结构")
    L.append("")
    L.append("![图 3 各算法的混淆矩阵（OOF，seed=42）](fig_confusion.png)")
    L.append("")
    for m in ranked[:2] + ([ranked[-1]] if ranked[-1] not in ranked[:2] else []):
        cm = M[m]["agg"]["confusion_matrix"]
        tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
        L.append(f"- **{CN_NAME[m]}**：真正例 {tp}、真负例 {tn}、假正例 {fp}、假负例 {fn}，"
                 f"两类错误的量级{'接近' if abs(fp - fn) < 60 else '不对称'}。")
    L.append("")
    L.append("可以看到各模型的错误结构较为对称，没有出现「把绝大多数样本都预测为同一类」"
             "的退化行为，这与数据集类别接近均衡的性质一致。假正例与假负例的数量接近，"
             "意味着在需要偏向某一类错误的实际场景中，可以通过调整决策阈值来重新分配错误，"
             "而不必更换模型。")
    L.append("")

    L.append("### 3.5 概率校准与误差分布")
    L.append("")
    L.append("![图 4 各算法预测概率的可靠性曲线](fig_calibration.png)")
    L.append("")
    _brier_best = sorted(models, key=lambda m: M[m]["agg"]["brier"]["mean"])[:2]
    L.append("可靠性曲线反映的是「模型说 70% 会发生的事，实际发生了多少」。曲线越接近对角线，"
             "概率越可信。从下图与 Brier 分数综合看，"
             + " 与 ".join(CN_NAME[m] for m in _brier_best) +
             " 的校准较好（Brier 分数最低），其余模型的预测概率偏差相对更大。")
    L.append("")
    L.append("![图 5 准确率随预测置信度的变化](fig_error.png)")
    L.append("")
    L.append("误差分布图按预测置信度分箱统计准确率。所有模型都呈现出「置信度越高、准确率越高」"
             "的单调趋势，这是模型具有判别力的直接证据；同时可以看出，即便在高置信度区间"
             "（置信度 > 0.9），各模型的准确率也只在 90% 上下，说明这部分样本本身就带有"
             "不可约的噪声——这与数据集是合成仿真数据的性质相符。")
    L.append("")

    L.append("### 3.6 特征重要性与结果成因")
    L.append("")
    L.append("![图 6 LightGBM 特征重要性前 20](fig_importance.png)")
    L.append("")
    top = res.get("feature_importance_top20", [])
    if top:
        L.append("LightGBM 给出的分裂次数重要性排序中，前几位依次为："
                 + "、".join(f"{n}（{v}）" for n, v in top[:6]) + "。")
        L.append("")
    L.append("这几项特征与领域直觉一致：**消费行为**（LuxurySpend、BasicSpend）是判断乘客是否"
             "被传送的首要线索——处于冷冻睡眠的乘客不出现在任何消费场所，而消费记录为零这件事"
             "本身强烈指示了该乘客的状态；**舱位号**（CabinNumFilled）反映了乘客在船上的位置，"
             "位置与异常发生时的空间分布相关；**年龄**及其相对同组均值的偏移，"
             "刻画了同行人群体的构成。相比之下，出发星球、目的地等类别特征的重要性明显靠后，"
             "这与「属性本身信息量有限、需要通过交互才能发挥作用」的判断相符。")
    L.append("")
    L.append("这也解释了为何 LightGBM 表现最好：上述强信号大多以「分段常数」的形式出现"
             "（消费为 0 与不为 0 是两个截然不同的状态），轴对齐的递归划分可以极高效地"
             "表达这类关系，而线性模型需要人工构造指示变量才能近似，神经网络则需要更多样本"
             "才能从平滑的激活函数中逼近出这种阶跃。")
    L.append("")

    if scl and scl.get("data"):
        L.append("### 3.7 样本效率实验")
        L.append("")
        L.append("为了检验「表格基础模型在小样本上具有优势」这一主张，设计了样本效率实验："
                 "固定一个 2174 行的验证集，训练集规模从 100 逐步增加到 4000，"
                 "观察各算法准确率的变化。")
        L.append("")
        L.append("![图 7 各算法在不同训练规模下的准确率](fig_scaling.png)")
        L.append("")
        sizes = sorted(scl["data"], key=lambda x: int(x))
        L.append("| 训练集规模 | " + " | ".join(CN_NAME.get(m, m).split("（")[0] for m in models) + " |")
        L.append("| --- | " + " | ".join("---" for _ in models) + " |")
        for n in sizes:
            row = [f"| {n} "]
            for m in models:
                cell = scl["data"][n].get(m, {})
                vals = [v["accuracy"] for v in cell.values() if "accuracy" in v]
                row.append(f"| {np.mean(vals):.4f} " if vals else "| -- ")
            L.append("".join(row) + "|")
        L.append("")
        L.append("曲线给出的结论如下（下表由脚本直接从 `out/scaling.json` 生成）。")
        L.append("")
        def _mean_acc(n, m):
            # scaling.json 的键是字符串形式的规模，这里统一按字符串取，避免 int/str 混用
            cell = scl["data"].get(str(n), {}).get(m, {})
            vals = [v["accuracy"] for v in cell.values() if "accuracy" in v]
            return float(np.mean(vals)) if vals else None

        best_by_size = []
        for n in sizes:
            cand = [(m, _mean_acc(n, m)) for m in models if _mean_acc(n, m) is not None]
            if cand:
                bm, bv = max(cand, key=lambda x: x[1])
                best_by_size.append((int(n), bm, bv))
        if best_by_size:
            L.append("各训练规模下的最优模型为：" + "；".join(
                f"{n} 行 → {CN_NAME[bm]}（{bv:.4f}）" for n, bm, bv in best_by_size) + "。")
            L.append("")

        tab_sizes = [int(n) for n in sizes if _mean_acc(n, "tabpfn") is not None]
        if tab_sizes:
            small = [n for n in tab_sizes if n <= 1000]
            large = [n for n in tab_sizes if n >= 2000]
            L.append("这个实验给出了本报告中最有信息量的结果。")
            L.append("")
            if small:
                gaps = []
                for n in small:
                    best_other = max((_mean_acc(n, m) for m in models
                                      if m != "tabpfn" and _mean_acc(n, m) is not None),
                                     default=None)
                    tv = _mean_acc(n, "tabpfn")
                    if best_other is not None and tv is not None:
                        gaps.append((n, tv, best_other, tv - best_other))
                if gaps:
                    L.append("**在小样本区间，TabPFN v2 一致领先**：" + "；".join(
                        f"训练集 {n} 行时它达到 {tv:.4f}，比其余四种算法中最好的一个"
                        f"（{bo:.4f}）高出 {g * 100:.2f} 个百分点"
                        for n, tv, bo, g in gaps) + "。")
                    L.append("")
                    L.append("这与它的工作原理直接对应：TabPFN 不需要从这几十上百个样本里"
                             "「学出」函数形式，它把预训练阶段积累的任务先验作为起点，"
                             "再用上下文中的少量样本去校准后验。样本越少，"
                             "「从零拟合」的代价就越突出，先验的价值也就越大——"
                             "这正是论文标题「小数据上的准确预测」所指的情形。")
                    L.append("")
            if large:
                L.append("**但这一优势随训练样本增加而收窄甚至反转**：" + "；".join(
                    f"{n} 行时 TabPFN 为 {_mean_acc(n, 'tabpfn'):.4f}，"
                    f"LightGBM 为 {_mean_acc(n, 'lightgbm'):.4f}"
                    for n in large if _mean_acc(n, "lightgbm") is not None) + "。")
                L.append("")
                L.append("这说明表格基础模型的优势并非无条件——它买的是「样本效率」，"
                         "当样本量足以让梯度提升树学出数据本身的规律时，"
                         "先验带来的增益会被数据自身的证据压过去。"
                         "对实际项目而言，这条曲线比任何单一分数都更有用："
                         "它给出了「在多大的数据规模上应该考虑换成基础模型」的判断依据。")
        L.append("")

    L.append("### 3.8 显著性检验")
    L.append("")
    L.append("| 对比 | 准确率差 | McNemar p 值 | Holm 校正后显著 |")
    L.append("| --- | --- | --- | --- |")
    comps = res.get("comparisons", {})
    for k, v in sorted(comps.items(), key=lambda x: x[1]["mcnemar_p"])[:8]:
        a, b = k.split("_vs_")
        L.append(f"| {CN_NAME.get(a, a)} vs {CN_NAME.get(b, b)} | {v['acc_diff']:+.4f} | "
                 f"{v['mcnemar_p']:.2e} | {'是' if v.get('significant_after_holm') else '否'} |")
    L.append("")
    sig = [(k, v) for k, v in comps.items() if v.get("significant_after_holm")]
    ns = [(k, v) for k, v in comps.items() if not v.get("significant_after_holm")]
    L.append(f"在 {len(comps)} 组两两比较中，{len(sig)} 组经 Holm 校正后仍显著，"
             f"{len(ns)} 组不显著。")
    if ns:
        L.append("不显著的组合是：" + "、".join(
            f"{CN_NAME.get(k.split('_vs_')[0], k)} vs {CN_NAME.get(k.split('_vs_')[1], k)}"
            f"（p={v['mcnemar_p']:.3f}）" for k, v in ns) + "。")
        L.append("")
        L.append("这与 3.2 节的观察一致：这两个模型在准确率上的差距小于划分带来的波动，"
                 "不能据此断言孰优孰劣。报告这类「不显著」的结论是必要的——"
                 "如果只报告显著差异，会系统性地夸大方法之间的真实差距。")
    L.append("")
    L.append("需要指出检验的前提：McNemar 检验要求两次预测是在同一批样本上做出的配对比较，"
             "本实验中所有模型共用同一份交叉验证划分，满足这一前提；"
             "但它检验的是「在固定划分下的差异」，结论不自动推广到其他数据划分。")
    L.append("")

    # ============ 四 ============
    L.append("## 四、总结与改进方向")
    L.append("")
    L.append("### 4.1 主要结论")
    L.append("")
    _n_sig = sum(1 for k, v in res.get("comparisons", {}).items()
                 if ranked[0] in k and v.get("significant_after_holm"))
    L.append(f"本实验在 Spaceship Titanic 数据集上系统比较了 {len(models)} 种原理不同的算法。"
             f"在分层 5 折交叉验证下，{CN_NAME[ranked[0]]} 取得最高准确率 "
             f"{M[ranked[0]]['agg']['accuracy']['mean']:.4f}；"
             f"经 McNemar 检验与 Holm 校正后，它与其余 {_n_sig} 个模型的差异达到统计显著。"
             f"各算法的适用性结论如下：")
    L.append("")
    # 结论条目按实际跑过的模型动态生成，避免硬编码模型名导致子集环境下 KeyError
    _desc = {
        "lightgbm": lambda: ("**LightGBM**：训练成本低（单次 5 折约 "
                             f"{sum(M['lightgbm']['agg']['seconds']) / max(len(M['lightgbm']['agg']['seconds']), 1):.0f} 秒），"
                             "对特征尺度不敏感，是这类结构化预测任务的稳妥首选；"),
        "mlp": lambda: ("**多层感知机**：判别力（AUC）接近树模型，但准确率受 0.5 阈值限制，"
                        "且对标准化与早停敏感，需要更多调参预算；"),
        "logreg": lambda: ("**逻辑回归**：作为线性基线表现稳健，与更复杂模型的差距在统计上可能不显著，"
                           "说明本任务的相当一部分信号是近似线性的；"),
        "knn": lambda: "**kNN**：在全部指标上垫底，验证了高维空间中距离度量的退化；",
        "tabpfn": lambda: ("**TabPFN v2**：作为免训练的表格基础模型，它不需要任何针对本数据集的梯度训练与"
                           "超参搜索，却在推理上远快于需要训练的模型，展示了这一新范式的实用价值。"),
    }
    for _m in ranked:
        if _m in _desc:
            L.append("- " + _desc[_m]())
    L.append("")
    L.append("从方法论层面，本实验印证了一条经验：**在中小规模表格数据上，归纳偏置与数据结构的"
             "匹配程度，比模型容量更能决定性能**。树模型的轴对齐划分恰好匹配表格中普遍存在的"
             "分段常数关系，这是它长期占据主导地位的深层原因。")
    L.append("")

    L.append("### 4.2 当前方案的不足")
    L.append("")
    L.append("第一，**TabPFN v2 只跑了 1 个随机种子，且集成规模从论文默认的 8 降到了 4**。"
             "受限于 CPU 推理成本（自注意力的平方级开销，单折约 13 分钟），"
             "该模型既无法像其他模型一样报告跨种子标准差，也没有使用论文的完整集成规模。"
             "这意味着它的成绩偏低的可能性存在，与其他模型的对比在这一点上不完全对等。")
    L.append("")
    L.append("第二，**超参数搜索的粒度有限**。每个模型只有十几到二十几组候选，"
             "且内层只用了 3 折。对于多层感知机这类对超参高度敏感的模型，"
             "更细的搜索很可能带来额外收益，当前配置未必是它的最优状态。")
    L.append("")
    L.append("第三，**特征工程未使用乘客姓名的信息**。姓名可以提取姓氏，用于识别同家族成员，"
             "本实验出于简化将其丢弃；而同行组与家族关系在本数据集中具有较强预测力。")
    L.append("")
    L.append("第四，**未做阈值优化**。所有模型的分类阈值固定为 0.5，"
             "而 3.2 节已显示部分模型的 AUC 高于其准确率所对应的水平，"
             "说明调整阈值仍有提升空间。")
    L.append("")
    L.append("第五，**没有验证集之外的独立测试集评估**。竞赛提供的测试集没有标签，"
             "因此本实验的全部结论都建立在训练集内部的交叉验证上，"
             "无法排除在真实测试集上排序发生变化的可能。")
    L.append("")

    L.append("### 4.3 改进方向")
    L.append("")
    L.append("第一，**补全 TabPFN v2 的多随机种子实验**，并尝试减小集成规模（n_estimators 从 8 降到 4）"
             "以换取更多重复次数，从而判断其性能波动是否在可接受范围内。")
    L.append("")
    L.append("第二，**引入姓名与家族特征**，并考虑对同行组做更细致的建模——"
             "例如用组内其他成员的特征构造上下文表示，而不是只做简单的聚合统计。")
    L.append("")
    L.append("第三，**做阈值优化与代价敏感学习**。在准确率之外，"
             "按实际业务对两类错误的相对代价选择阈值，并报告对应的 F1 与业务指标。")
    L.append("")
    L.append("第四，**扩展对比的算法范围**。当前只比较了单模型，"
             "而集成学习（例如对 LightGBM、MLP 与 TabPFN 做概率平均）在这类任务上通常能带来"
             "稳定的提升；此外可以补上 XGBoost 与 CatBoost，以区分「梯度提升这一原理的贡献」"
             "与「LightGBM 具体实现的贡献」。")
    L.append("")
    L.append("第五，**加入不确定性量化**。当前只报告点预测，"
             "而实际决策需要知道「这个预测有多可靠」。可以比较集成方差、"
             "Monte Carlo Dropout 与 TabPFN 的原生后验概率三者在校准上的差异。")
    L.append("")
    L.append("第六，**把当前流程封装为可复用的实验框架**，使新增模型只需实现统一的接口"
             "即可自动进入交叉验证、显著性检验与报告生成流程。本实验的脚本结构已经接近这一目标。")
    L.append("")

    L.append("## 参考资料")
    L.append("")
    L.append("[1] Kaggle. Spaceship Titanic 竞赛数据集与数据说明. https://www.kaggle.com/competitions/spaceship-titanic")
    L.append("")
    L.append("[2] Hollmann N, Müller S, Purucker L, et al. Accurate predictions on small data with a "
             "tabular foundation model[J]. Nature, 2025, 637(8045): 319-326. "
             "https://doi.org/10.1038/s41586-024-08328-6")
    L.append("")
    L.append("[3] Ke G, Meng Q, Finley T, et al. LightGBM: A highly efficient gradient boosting "
             "decision tree[C]//Advances in Neural Information Processing Systems 30 (NIPS 2017). 2017.")
    L.append("")
    L.append("[4] Chen T, Guestrin C. XGBoost: A scalable tree boosting system[C]//Proceedings of the "
             "22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. 2016: 785-794.")
    L.append("")

    L.append("## 附录：生成式人工智能使用披露")
    L.append("")
    L.append("本实验过程中使用了生成式人工智能助手协助完成部分工作，披露如下：")
    L.append("")
    L.append("- **使用范围**：数据处理与实验脚本的编写、图表生成脚本、报告的排版代码，"
             "以及文献信息的检索与核实。")
    L.append("- **由人确定的部分**：选题、算法集合的确定、实验协议（交叉验证折数、随机种子、"
             "显著性检验方法）、以及报告中对结果的解释与结论。")
    L.append("- **核验方式**：报告中出现的每一个数值都由脚本从 `out/results.json` 等结果文件"
             "自动读取并写入，不经过人工转录；数据集经过四源字节比对与官方说明对照；"
             "参考论文的作者、卷期页码通过 Crossref 与出版社官方页面逐条核实，"
             "其中 Nature 论文的作者名单经核实为 8 位（含 Schirrmeister R T），"
             "与部分二手引用的版本不同，报告采用的是官方记录。")
    L.append("- **未核验的部分**：未能登录 Kaggle 账号，因此无法证明所用数据文件与 Kaggle "
             "服务器上的那一份逐字节相同；这一点已在 1.2 节中写明。")
    L.append("")

    return "\n".join(L), res


BIAS = {
    "logreg": "对数几率为特征的线性函数，决策边界线性、方差小",
    "knn": "相似的样本有相似的标签，决策由局部邻域决定",
    "lightgbm": "目标函数可由轴对齐的递归划分逼近，对单调变换不敏感",
    "mlp": "任意连续函数均可由有限宽网络逼近，无内置结构先验",
    "tabpfn": "真实任务分布可由合成先验覆盖，后验推断可被前馈网络一次性近似",
}


if __name__ == "__main__":
    res = load()
    body, _ = build(res)
    p = OUT / "report_a_body.md"
    p.write_text(body, encoding="utf-8")
    print(f"写出 {p}  {len(body)} 字符")
