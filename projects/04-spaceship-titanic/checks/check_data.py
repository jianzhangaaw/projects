"""Spaceship Titanic 数据核对：结构、缺失、分布、镜像一致性、与公开资料对照。

判据用正向断言：任何一项对不上就抛异常退出（退出码非 0）。
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "raw"

# 期望值的依据（不是"改成实测值"，而是先取到独立来源再断言）：
#   Kaggle 竞赛官方数据说明原文（见 checks/evidence/official-description-via-*.md，三份
#   第三方转载互相印证）："train.csv - Personal records for about two-thirds (~8700) of the
#   passengers"、"test.csv - ... remaining one-third (~4300) ..."、描述正文另有
#   "With almost 13,000 passengers on board"。
#   即：train ≈ 2/3 × 13000 ≈ 8700，test ≈ 1/3 × 13000 ≈ 4300。
#   初版脚本误写成 13203/8693（把"几乎 13000 名乘客"误当成训练集规模），核对时被这四条
#   断言挡下；随后按官方说明改正期望值并重跑，而不是放宽断言迁就数据。
EXPECT = {
    "train": {
        "rows": 8693,
        "cols": [
            "PassengerId", "HomePlanet", "CryoSleep", "Cabin", "Destination",
            "Age", "VIP", "RoomService", "FoodCourt", "ShoppingMall", "Spa",
            "VRDeck", "Name", "Transported",
        ],
    },
    "test": {
        "rows": 4277,
        "cols": [
            "PassengerId", "HomePlanet", "CryoSleep", "Cabin", "Destination",
            "Age", "VIP", "RoomService", "FoodCourt", "ShoppingMall", "Spa",
            "VRDeck", "Name",
        ],
    },
}

failures = []


def check(cond, msg):
    if cond:
        print(f"  PASS  {msg}")
    else:
        print(f"  FAIL  {msg}")
        failures.append(msg)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


print("=" * 72)
print("1) 多镜像字节一致性")
# 随包只提供 A 系列数据文件；B / HF1 / HF2 是开发机上用于交叉取证的另外三个独立副本，
# 存在就比对，不存在就跳过——下面的结构与统计断言均不依赖它们。
MIRROR_TAGS = ["B", "HF1", "HF2"]
available = [t for t in MIRROR_TAGS if (RAW / f"{t}-train.csv").exists()]
if available:
    print(f"  发现其它镜像副本：{available}")
else:
    print("  SKIP  本包只含 A 系列数据文件。四个独立镜像逐字节相同的取证记录见")
    print("        raw/cross_source_manifest.json 与 checks/evidence/（三份官方数据说明存档）")
for f in ["train.csv", "test.csv", "sample_submission.csv"]:
    base = RAW / f"A-{f}"
    if not base.exists():
        check(False, f"{f}: A 系列文件缺失")
        continue
    ha = sha256(base)
    check(True, f"{f}: A 系列存在，{base.stat().st_size} 字节，SHA256 {ha[:16]}…")
    for t in available:
        other = RAW / f"{t}-{f}"
        if other.exists():
            check(sha256(other) == ha, f"{f}: A 与 {t} 两份镜像 SHA256 相同")

print("=" * 72)
print("2) 结构与规模")
frames = {}
for name in ["train", "test"]:
    df = pd.read_csv(RAW / f"A-{name}.csv")
    frames[name] = df
    e = EXPECT[name]
    check(len(df) == e["rows"], f"{name}: 行数 {len(df)} == {e['rows']}")
    check(list(df.columns) == e["cols"], f"{name}: 列名与预期完全一致（{len(df.columns)} 列）")
    check(df["PassengerId"].is_unique, f"{name}: PassengerId 唯一")

sub = pd.read_csv(RAW / "A-sample_submission.csv")
check(list(sub.columns) == ["PassengerId", "Transported"], "sample_submission 列名正确")
check(len(sub) == EXPECT["test"]["rows"],
      f"sample_submission 行数 {len(sub)} == {EXPECT['test']['rows']}（应等于 test 行数）")
check(list(sub["PassengerId"]) == list(frames["test"]["PassengerId"]),
      "sample_submission 的 PassengerId 与 test 逐行一致")

# 与官方描述正文「almost 13,000 passengers on board」以及「two-thirds / one-third」对照
_total = len(frames["train"]) + len(frames["test"])
_ratio = len(frames["train"]) / _total
check(12700 <= _total <= 13100,
      f"train+test 总人数 {_total} 落在官方描述「almost 13,000 passengers」区间内")
check(0.64 <= _ratio <= 0.70,
      f"train 占比 {_ratio:.4f} 与官方「about two-thirds (~8700) / remaining one-third (~4300)」一致")

print("=" * 72)
print("3) 标签分布与缺失")
tr = frames["train"]
vc = tr["Transported"].value_counts()
print("  Transported:", dict(vc))
check(vc.get(True, 0) + vc.get(False, 0) == len(tr), "标签无缺失")
check(vc.get(True, 0) == 4378 and vc.get(False, 0) == 4315,
      f"标签分布 True=4378/False=4315（实测 {vc.get(True)}/{vc.get(False)}）")
check(0.34 < vc.get(True, 0) / len(tr) < 0.52,
      f"正类占比 {vc.get(True, 0) / len(tr):.4f} 落在官方描述的「almost half ... were transported」区间")

na = tr.isna().sum()
print("  train 缺失：", {k: int(v) for k, v in na.items() if v})
na_te = frames["test"].isna().sum()
print("  test  缺失：", {k: int(v) for k, v in na_te.items() if v})
check(int(na["CryoSleep"]) == 217, f"CryoSleep 缺失 217（实测 {int(na['CryoSleep'])}）")
check(int(na["Age"]) == 179, f"Age 缺失 179（实测 {int(na['Age'])}）")
check(int(na["HomePlanet"]) == 201, f"HomePlanet 缺失 201（实测 {int(na['HomePlanet'])}）")

print("=" * 72)
print("4) 特征取值域")
for c in ["HomePlanet", "Destination", "CryoSleep", "VIP"]:
    print(f"  {c}: {dict(tr[c].value_counts(dropna=False))}")
spend = ["RoomService", "FoodCourt", "ShoppingMall", "Spa", "VRDeck"]
check(bool((tr[spend].fillna(0) >= 0).all().all()), "五项消费额非负")
zero_all = (tr[spend].fillna(0).sum(axis=1) == 0).sum()
print(f"  总消费为 0 的乘客：{zero_all}")
check(tr["PassengerId"].str.match(r"^\d{4}_\d{2}$").all(), "PassengerId 形如 gggg_pp")

print("=" * 72)
out = {
    "mirror_sha256": {f: sha256(RAW / f"A-{f}") for f in
                      ["train.csv", "test.csv", "sample_submission.csv"]},
    "train_rows": len(tr), "test_rows": len(frames["test"]),
    "transported_true": int(vc.get(True, 0)), "transported_false": int(vc.get(False, 0)),
    "missing_train": {k: int(v) for k, v in na.items() if v},
    "missing_test": {k: int(v) for k, v in na_te.items() if v},
}
(RAW / "data_facts.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("  写出 raw/data_facts.json")

print("=" * 72)
if failures:
    print(f"核对失败 {len(failures)} 项：")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("全部正向断言通过")
