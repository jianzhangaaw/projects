"""汇总交叉验证结果：指标表、显著性检验、六张图、submission.csv。

输出 out/results.json 是报告里每一个数字的唯一来源。
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from scipy import stats
from sklearn.calibration import calibration_curve
from sklearn.metrics import roc_curve

LAB = Path(__file__).resolve().parents[1]
OUT = LAB / "out"
PRED = OUT / "preds"
FIG = OUT
SEEDS = [42, 2025, 7]

sys.path.insert(0, str(LAB / "src"))
from models import MODEL_SPECS  # noqa: E402

# 中文字体：显式指定，否则标签会变方框
for cand in ["Microsoft YaHei", "SimHei", "SimSun"]:
    if any(cand.lower() in f.name.lower() for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [cand]
        break
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.bbox"] = "tight"

METRIC_KEYS = ["accuracy", "roc_auc", "f1", "balanced_accuracy", "brier"]

# 图例用短名：不能用 split(" ") 截取，否则 "k 近邻 (kNN)" 会被切成 "k"
SHORT = {"logreg": "逻辑回归", "knn": "kNN", "lightgbm": "LightGBM",
         "mlp": "MLP", "tabpfn": "TabPFN v2"}


def load_cv():
    data = {}
    for f in sorted((OUT / "cv").glob("*.json")):
        m = json.loads(f.read_text(encoding="utf-8"))
        data.setdefault(m["model"], {})[m["seed"]] = m
    return data


def load_preds():
    out = {}
    for f in sorted(PRED.glob("*.npz")):
        name = f.stem.split("__")[0]
        seed = int(f.stem.split("seed")[1])
        d = np.load(f, allow_pickle=True)
        out.setdefault(name, {})[seed] = (d["oof"], d["y"], d["fold_ids"])
    return out


def mcnemar(y, p1, p2):
    """配对 McNemar 检验（连续校正）。"""
    c1 = (p1 == y)
    c2 = (p2 == y)
    b = int(np.sum(c1 & ~c2))
    c = int(np.sum(~c1 & c2))
    if b + c == 0:
        return 1.0, b, c, 0.0
    stat = (abs(b - c) - 1) ** 2 / (b + c)
    p = float(stats.chi2.sf(stat, df=1))
    return p, b, c, float(stat)


def main():
    cv = load_cv()
    preds = load_preds()
    models = [m for m in MODEL_SPECS if m in cv]
    print("模型:", models, "| 覆盖:", {m: sorted(cv[m]) for m in models})

    results = {"models": {}, "comparisons": {}, "meta": {
        "n_train": 8693, "n_test": 4277, "n_folds": 5, "seeds": SEEDS,
        "primary_metric": "accuracy",
        "models_with_all_seeds": [m for m in models if len(cv[m]) == len(SEEDS)],
        "models_partial_seeds": {m: sorted(cv[m]) for m in models if len(cv[m]) != len(SEEDS)},
    }}

    # ---- 指标汇总 ----
    for m in models:
        per_seed = {str(s): cv[m][s]["metrics"] for s in sorted(cv[m])}
        agg = {}
        for k in METRIC_KEYS + ["precision", "recall"]:
            vals = [per_seed[str(s)][k] for s in sorted(cv[m])]
            agg[k] = {"mean": float(np.mean(vals)), "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                      "values": [float(v) for v in vals]}
        agg["confusion_matrix"] = per_seed[str(sorted(cv[m])[0])]["confusion_matrix"]
        agg["fold_acc"] = [f["accuracy"] for f in per_seed[str(sorted(cv[m])[0])]["per_fold"]]
        agg["seconds"] = [cv[m][s]["seconds"] for s in sorted(cv[m])]
        agg["params"] = cv[m][sorted(cv[m])[0]].get("params", {})
        results["models"][m] = {"label": MODEL_SPECS[m]["label"], "per_seed": per_seed, "agg": agg}

    # ---- 显著性检验 ----
    comps = {}
    ref_seed = 42 if 42 in preds.get(models[0], {}) else sorted(preds[models[0]])[0]
    for a, b in combinations(models, 2):
        if ref_seed not in preds.get(a, {}) or ref_seed not in preds.get(b, {}):
            continue
        oa, y, fa = preds[a][ref_seed]
        ob, _, fb = preds[b][ref_seed]
        assert np.array_equal(fa, fb), "两模型的折划分不一致，无法做配对检验"
        pa = (oa >= 0.5).astype(int)
        pb = (ob >= 0.5).astype(int)
        p, n_b, n_c, stat = mcnemar(y, pa, pb)
        acc_a = float((pa == y).mean())
        acc_b = float((pb == y).mean())
        fa_acc = results["models"][a]["agg"]["fold_acc"]
        fb_acc = results["models"][b]["agg"]["fold_acc"]
        w_stat, w_p = stats.wilcoxon(fa_acc, fb_acc) if len(fa_acc) == len(fb_acc) and len(fa_acc) >= 5 \
            else (float("nan"), float("nan"))
        comps[f"{a}_vs_{b}"] = {
            "mcnemar_p": p, "mcnemar_stat": stat, "a_only_correct": n_b, "b_only_correct": n_c,
            "acc_a": acc_a, "acc_b": acc_b, "acc_diff": acc_a - acc_b,
            "wilcoxon_p_folds": float(w_p), "wilcoxon_stat": float(w_stat),
            "significant_at_0.05": bool(p < 0.05),
        }
    # Holm 校正
    if comps:
        ps = sorted([(v["mcnemar_p"], k) for k, v in comps.items()])
        m_tests = len(ps)
        for rank, (p, k) in enumerate(ps):
            comps[k]["holm_adjusted_threshold"] = 0.05 / (m_tests - rank)
            comps[k]["significant_after_holm"] = bool(p < 0.05 / (m_tests - rank))
    results["comparisons"] = comps

    # ---- 图 1：多指标对比 ----
    fig, ax = plt.subplots(figsize=(9, 4.6))
    keys = ["accuracy", "roc_auc", "f1", "balanced_accuracy"]
    x = np.arange(len(models))
    w = 0.2
    for i, k in enumerate(keys):
        vals = [results["models"][m]["agg"][k]["mean"] for m in models]
        errs = [results["models"][m]["agg"][k]["std"] for m in models]
        ax.bar(x + (i - 1.5) * w, vals, w, yerr=errs, capsize=2.5,
               label={"accuracy": "准确率", "roc_auc": "AUC", "f1": "F1",
                      "balanced_accuracy": "平衡准确率"}[k])
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT.get(m, m) for m in models],
                       fontsize=9)
    ax.set_ylim(0.5, 1.0)
    ax.set_ylabel("指标值（OOF，均值±标准差）")
    ax.set_title("五类算法在 Spaceship Titanic 上的性能对比")
    ax.legend(fontsize=8, ncol=4, loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    fig.savefig(FIG / "fig_metrics.png")
    plt.close(fig)
    print("写出 fig_metrics.png")

    # ---- 图 2：ROC ----
    fig, ax = plt.subplots(figsize=(6, 5.4))
    for m in models:
        oof, y, _ = preds[m][ref_seed]
        fpr, tpr, _ = roc_curve(y, oof)
        auc = results["models"][m]["agg"]["roc_auc"]["mean"]
        ax.plot(fpr, tpr, lw=1.6, label=f"{SHORT.get(m, m)} (AUC={auc:.4f})")
    ax.plot([0, 1], [0, 1], "k--", lw=0.8)
    ax.set_xlabel("假正率 (FPR)")
    ax.set_ylabel("真正率 (TPR)")
    ax.set_title(f"OOF ROC 曲线（seed={ref_seed}）")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.3)
    fig.savefig(FIG / "fig_roc.png")
    plt.close(fig)
    print("写出 fig_roc.png")

    # ---- 图 3：混淆矩阵 ----
    n = len(models)
    fig, axes = plt.subplots(1, n, figsize=(3.1 * n, 3.2))
    for ax, m in zip(np.atleast_1d(axes), models):
        cm = np.array(results["models"][m]["agg"]["confusion_matrix"])
        im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max())
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=10,
                        color="white" if cm[i, j] > cm.max() * 0.6 else "black")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["预测否", "预测是"], fontsize=8)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["实际否", "实际是"], fontsize=8)
        ax.set_title(SHORT.get(m, m), fontsize=9)
    fig.suptitle("各算法混淆矩阵（OOF，seed=42）", fontsize=12)
    fig.savefig(FIG / "fig_confusion.png")
    plt.close(fig)
    print("写出 fig_confusion.png")

    # ---- 图 4：概率校准 ----
    fig, ax = plt.subplots(figsize=(6, 5.4))
    for m in models:
        oof, y, _ = preds[m][ref_seed]
        try:
            frac, mean_pred = calibration_curve(y, oof, n_bins=10, strategy="quantile")
            ax.plot(mean_pred, frac, marker="o", ms=3.5, lw=1.3,
                    label=f"{SHORT.get(m, m)} (Brier={results['models'][m]['agg']['brier']['mean']:.4f})")
        except Exception as e:  # noqa: BLE001
            print(f"  校准曲线跳过 {m}: {e}")
    ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="理想校准")
    ax.set_xlabel("预测概率均值")
    ax.set_ylabel("实际正类比例")
    ax.set_title("可靠性曲线（概率校准）")
    ax.legend(fontsize=8, loc="best")
    ax.grid(alpha=0.3)
    fig.savefig(FIG / "fig_calibration.png")
    plt.close(fig)
    print("写出 fig_calibration.png")

    # ---- 图 5：LightGBM 特征重要性 ----
    try:
        import lightgbm as lgb
        import pandas as pd
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler
        from features import CAT_COLS, get_xy

        X, y, _, _ = get_xy(LAB / "raw" / "A-train.csv", LAB / "raw" / "A-test.csv")
        num_cols = [c for c in X.columns if c not in CAT_COLS]
        pre = ColumnTransformer([
            ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num_cols),
            ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                              ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), CAT_COLS),
        ])
        Xe = pre.fit_transform(X)
        names = list(pre.get_feature_names_out())
        params = results["models"]["lightgbm"]["agg"]["params"]
        clf = lgb.LGBMClassifier(random_state=42, n_jobs=6, verbose=-1, **params)
        clf.fit(Xe, y)
        imp = clf.feature_importances_
        idx = np.argsort(imp)[::-1][:20]
        fig, ax = plt.subplots(figsize=(7.5, 5.6))
        ax.barh(range(len(idx))[::-1], imp[idx], color="#3b6ea5")
        ax.set_yticks(range(len(idx))[::-1])
        ax.set_yticklabels([names[i].replace("num__", "").replace("cat__", "") for i in idx], fontsize=8)
        ax.set_xlabel("分裂次数重要性")
        ax.set_title("LightGBM 特征重要性前 20")
        ax.grid(axis="x", alpha=0.3)
        fig.savefig(FIG / "fig_importance.png")
        plt.close(fig)
        top20 = [(names[i].replace("num__", "").replace("cat__", ""), int(imp[i])) for i in idx]
        results["feature_importance_top20"] = top20
        print("写出 fig_importance.png")
    except Exception as e:  # noqa: BLE001
        print("特征重要性图失败:", type(e).__name__, e)
        results["feature_importance_top20"] = []

    # ---- 图 6：误差分析（按预测置信度分箱） ----
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    bins = np.linspace(0.5, 1.0, 11)
    for m in models:
        oof, y, _ = preds[m][ref_seed]
        conf = np.maximum(oof, 1 - oof)
        centers, accs = [], []
        for lo, hi in zip(bins[:-1], bins[1:]):
            sel = (conf >= lo) & (conf < hi)
            if sel.sum() >= 20:
                centers.append((lo + hi) / 2)
                accs.append(float(((oof[sel] >= 0.5).astype(int) == y[sel]).mean()))
        ax.plot(centers, accs, marker="o", ms=4, lw=1.3,
                label=SHORT.get(m, m))
    ax.set_xlabel("预测置信度（max(p, 1-p)）")
    ax.set_ylabel("该置信度区间内的准确率")
    ax.set_title("误差分布：准确率随置信度的变化")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.savefig(FIG / "fig_error.png")
    plt.close(fig)
    print("写出 fig_error.png")

    # ---- 样本效率曲线（若已有 scaling.json）----
    sp = OUT / "scaling.json"
    if sp.exists():
        sc = json.loads(sp.read_text(encoding="utf-8"))
        fig, ax = plt.subplots(figsize=(7.4, 4.8))
        for m in sc.get("models", []):
            ns, accs = [], []
            for n in sorted(sc["data"], key=lambda x: int(x)):
                cell = sc["data"][n].get(m)
                if not cell:
                    continue
                vals = [v["accuracy"] for v in cell.values()]
                ns.append(int(n)); accs.append(float(np.mean(vals)))
            if ns:
                ax.plot(ns, accs, marker="o", ms=4, lw=1.5, label=sc.get("labels", {}).get(m, m))
        ax.set_xscale("log")
        ax.set_xlabel("训练集规模（对数刻度）")
        ax.set_ylabel("验证集准确率")
        ax.set_title("样本效率：各算法在不同训练规模下的表现")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        fig.savefig(FIG / "fig_scaling.png")
        plt.close(fig)
        print("写出 fig_scaling.png")
    else:
        print("out/scaling.json 尚不存在，跳过 fig_scaling.png")

    # ---- submission.csv：用 OOF 准确率最高的模型在全量训练集上重训后预测 test ----
    try:
        import pandas as pd
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder, StandardScaler
        from features import CAT_COLS, get_xy

        X, y, Xte, test_ids = get_xy(LAB / "raw" / "A-train.csv", LAB / "raw" / "A-test.csv")
        num_cols = [c for c in X.columns if c not in CAT_COLS]
        # 选择提交模型：先按 OOF 准确率排序；若前两名的差距小于 0.002
        # （远小于折间波动，属数值噪声级别、统计上不可区分），
        # 则在两者中选择跨随机种子验证更充分的那个——用更多种子验证过的模型对
        # 单次数据划分的依赖更小，是更稳妥的提交选择。
        ranked_sub = sorted(models, key=lambda m: -results["models"][m]["agg"]["accuracy"]["mean"])
        best_model = ranked_sub[0]
        n_seeds = {m: len(cv[m]) for m in ranked_sub}
        if len(ranked_sub) > 1:
            acc0 = results["models"][ranked_sub[0]]["agg"]["accuracy"]["mean"]
            acc1 = results["models"][ranked_sub[1]]["agg"]["accuracy"]["mean"]
            if acc0 - acc1 < 0.002 and n_seeds[ranked_sub[1]] > n_seeds[ranked_sub[0]]:
                best_model = ranked_sub[1]
                print(f"  submission: OOF 前两名差距 {acc0 - acc1:.4f} < 0.002（不可区分），"
                      f"改选种子数更多的 {best_model}（{n_seeds[best_model]} 个种子 vs "
                      f"{n_seeds[ranked_sub[0]]} 个）")
        params = results["models"][best_model]["agg"]["params"]
        pipe = Pipeline([
            ("pre", ColumnTransformer([
                ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num_cols),
                ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                                  ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), CAT_COLS),
            ])),
            ("clf", MODEL_SPECS[best_model]["factory"](rs=42)),
        ])
        try:
            pipe.set_params(**{f"clf__{k}": v for k, v in params.items()})
        except Exception as e:  # noqa: BLE001
            print("  submission: 参数设置告警", e)
        pipe.fit(X, y)
        proba = pipe.predict_proba(Xte)[:, 1]
        sub = pd.DataFrame({"PassengerId": test_ids, "Transported": proba >= 0.5})
        # 与官方样例格式逐项对齐
        sample = pd.read_csv(LAB / "raw" / "A-sample_submission.csv")
        assert list(sub.columns) == list(sample.columns), "提交文件列名与样例不一致"
        assert len(sub) == len(sample), f"提交文件行数 {len(sub)} != 样例 {len(sample)}"
        assert list(sub["PassengerId"]) == list(sample["PassengerId"]), "PassengerId 顺序与样例不一致"
        assert sub["Transported"].dtype == bool, "Transported 不是布尔值"
        sub.to_csv(OUT / "submission.csv", index=False)
        results["submission"] = {
            "model": best_model, "label": results["models"][best_model]["label"],
            "rows": int(len(sub)), "predicted_true": int(sub["Transported"].sum()),
            "predicted_true_ratio": float(sub["Transported"].mean()),
            "trained_on": int(len(X)),
        }
        print(f"写出 out/submission.csv（模型 {best_model}，{len(sub)} 行，"
              f"预测正类 {int(sub['Transported'].sum())} 例 / {sub['Transported'].mean():.2%}）")
    except Exception as e:  # noqa: BLE001
        import traceback
        print("submission 生成失败:", type(e).__name__, e)
        traceback.print_exc()

    OUT.joinpath("results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print("写出 out/results.json（含 submission 信息）")

    # 控制台摘要
    print("\n模型            accuracy          auc            f1     brier   用时(s)")
    for m in models:
        a = results["models"][m]["agg"]
        print(f"{m:12s} {a['accuracy']['mean']:.4f}±{a['accuracy']['std']:.4f}  "
              f"{a['roc_auc']['mean']:.4f}±{a['roc_auc']['std']:.4f}  "
              f"{a['f1']['mean']:.4f}  {a['brier']['mean']:.4f}  "
              f"{np.mean(a['seconds']):.1f}")
    print("\n显著性检验（McNemar，seed=42）：")
    for k, v in sorted(comps.items(), key=lambda x: x[1]["mcnemar_p"]):
        print(f"  {k:24s} p={v['mcnemar_p']:.3e}  Δacc={v['acc_diff']:+.4f}  "
              f"Holm显著={v['significant_after_holm']}")


if __name__ == "__main__":
    main()
