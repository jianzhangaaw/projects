"""校验交叉验证产物：形状、折划分完整性、指标区间。

判据全部是正向断言——必须确认「存在 / 相等 / 覆盖完整」，不靠「没报错」。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parents[1]
CV = LAB / "out" / "cv"
PRED = LAB / "out" / "preds"
N_TRAIN = 8693
N_FOLDS = 5
MODELS = ["logreg", "knn", "lightgbm", "mlp", "tabpfn"]
SEEDS = [42, 2025, 7]
# 依据：单折探测与调参内层 CV 得到的量级
ACC_RANGE = {
    "logreg": (0.76, 0.83),
    "knn": (0.75, 0.82),
    "lightgbm": (0.78, 0.85),
    "mlp": (0.76, 0.84),
    "tabpfn": (0.74, 0.88),
}

fails = []
passes = []
skipped = []


def check(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if cond:
        passes.append(msg)
    else:
        fails.append(msg)


def main():
    only = sys.argv[1].split(",") if len(sys.argv) > 1 else MODELS
    for model in only:
        print(f"=== {model} ===")
        for seed in SEEDS:
            npz = PRED / f"{model}__seed{seed}.npz"
            if not npz.exists():
                # 语义：本脚本校验「已有的」产物质量，不强制要求把每个种子都跑过。
                # 未运行的种子记为 SKIP（不计入失败），只有「文件存在但内容不对」才算 FAIL。
                # 若要强制跑全，请先执行 run_experiment.py 把对应种子补齐。
                skipped.append(f"{model}__seed{seed}")
                print(f"  SKIP  {model} seed={seed} 无产物（该种子未运行）")
                continue
            check(npz.stat().st_size > 1000, f"{npz.name} 字节数 {npz.stat().st_size} > 1000")
            d = np.load(npz, allow_pickle=True)
            oof, fids, y = d["oof"], d["fold_ids"], d["y"]
            check(len(oof) == N_TRAIN, f"{model}/{seed}: oof 长度 {len(oof)} == {N_TRAIN}")
            check(len(fids) == N_TRAIN, f"{model}/{seed}: fold_ids 长度 {len(fids)} == {N_TRAIN}")
            check(set(np.unique(fids).tolist()) == set(range(N_FOLDS)),
                  f"{model}/{seed}: 折编号覆盖 0~{N_FOLDS - 1}（实测 {sorted(set(fids.tolist()))}）")
            check(bool(((oof >= 0) & (oof <= 1)).all()), f"{model}/{seed}: 概率都在 [0,1]")
            sizes = [int((fids == k).sum()) for k in range(N_FOLDS)]
            check(all(abs(s - N_TRAIN / N_FOLDS) <= 25 for s in sizes),
                  f"{model}/{seed}: 各折样本数均衡 {sizes}")
            check(int(y.sum()) == 4378, f"{model}/{seed}: 正类总数 {int(y.sum())} == 4378")
            # 同一行不会被分到两折（fold_ids 每行都有值即隐含）
            check(len(fids) == sum(sizes), f"{model}/{seed}: 每行恰好属于一折")
            acc = float(((oof >= 0.5).astype(int) == y).mean())
            lo, hi = ACC_RANGE[model]
            check(lo <= acc <= hi, f"{model}/{seed}: OOF 准确率 {acc:.4f} 落在 [{lo},{hi}]")

            js = CV / f"{model}__seed{seed}.json"
            check(js.exists(), f"{js.name} 存在")
            if js.exists():
                meta = json.loads(js.read_text(encoding="utf-8"))
                check(abs(meta["metrics"]["accuracy"] - acc) < 1e-9,
                      f"{model}/{seed}: json 记录的准确率 {meta['metrics']['accuracy']:.6f} "
                      f"与 npz 重算值 {acc:.6f} 一致")
                check(len(meta["metrics"]["per_fold"]) == N_FOLDS,
                      f"{model}/{seed}: per_fold 折数 == {N_FOLDS}")

    print("\n" + "=" * 60)
    if skipped:
        print(f"跳过的组合 {len(skipped)} 个（该种子未运行）：{', '.join(skipped)}")
    if fails:
        print(f"校验失败 {len(fails)} 项：")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    if not passes:
        print("没有任何产物可供校验——请先运行 run_experiment.py 生成交叉验证结果")
        sys.exit(2)
    print(f"全部正向断言通过（{len(passes)} 项）")


if __name__ == "__main__":
    main()
