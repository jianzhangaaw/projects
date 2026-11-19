# -*- coding: utf-8 -*-
"""按顺序运行全部实验，生成 results/ 与 figures/ 下的全部产物。

运行：python run_all.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    ("算法正确性校验", ROOT / "tests" / "test_algorithms.py"),
    ("实验一：car.data + Apriori", ROOT / "experiments" / "exp1_car_apriori.py"),
    ("实验二：groceries.csv + DHP", ROOT / "experiments" / "exp2_groceries_dhp.py"),
    ("实验三：groceries.csv + FP-Growth", ROOT / "experiments" / "exp3_groceries_fpgrowth.py"),
    ("实验四：三种算法效率对比", ROOT / "experiments" / "exp4_compare.py"),
    ("实验五：绘制结果图", ROOT / "experiments" / "exp5_figures.py"),
]


def main():
    t_all = time.perf_counter()
    for name, script in STEPS:
        print("=" * 78)
        print(f"### {name}：{script.relative_to(ROOT)}")
        print("=" * 78)
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, str(script)], cwd=str(ROOT),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
        log = ROOT / "results" / f"{script.stem}.log"
        log.write_text(out, encoding="utf-8")
        print(out[-2500:] if len(out) > 2500 else out)
        print(f"--- {name} 结束，退出码 {r.returncode}，耗时 {time.perf_counter() - t0:.2f}s")
        if r.returncode != 0:
            print(f"！！！{name} 失败，终止后续步骤")
            return r.returncode
    print(f"\n全部实验完成，总耗时 {time.perf_counter() - t_all:.2f}s")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
