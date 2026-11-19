"""五类算法（原理互不相同）的构造与超参数网格。

设计要点：
- 全部实现 sklearn 接口（fit / predict / predict_proba），便于复用同一套交叉验证与指标代码。
- 预处理统一放在 `features` 之外的 Pipeline 里（`run_experiment.build_pipeline`），
  保证每种算法看到同一份编码后的特征矩阵。
- 超参数网格刻意保持"小而有依据"：每个候选值对应一个明确的建模考虑（写进报告）。
"""
from __future__ import annotations

import os

import numpy as np
import torch
import torch.nn as nn
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.utils.validation import check_is_fitted


class TorchMLPClassifier(BaseEstimator, ClassifierMixin):
    """PyTorch 多层感知机（二分类）。

    为什么自己写而不直接用 sklearn 的 MLPClassifier：
    需要精确控制早停、随机种子、权重衰减与训练轮数，并把"训练过程中的验证损失"
    记录下来供报告里的学习曲线使用；sklearn 版本不暴露这些中间量。
    """

    def __init__(
        self,
        hidden=(128, 64),
        dropout=0.2,
        lr=1e-3,
        weight_decay=1e-4,
        batch_size=256,
        max_epochs=200,
        patience=15,
        val_fraction=0.12,
        random_state=0,
        device="cpu",
    ):
        self.hidden = hidden
        self.dropout = dropout
        self.lr = lr
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.max_epochs = max_epochs
        self.patience = patience
        self.val_fraction = val_fraction
        self.random_state = random_state
        self.device = device

    def _build(self, n_features):
        layers, prev = [], n_features
        for h in self.hidden:
            layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(self.dropout)]
            prev = h
        layers += [nn.Linear(prev, 1)]
        return nn.Sequential(*layers)

    def fit(self, X, y):
        X = np.asarray(X, dtype=np.float32)
        y = np.asarray(y, dtype=np.float32).ravel()
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)

        n = len(X)
        rng = np.random.default_rng(self.random_state)
        perm = rng.permutation(n)
        n_val = max(1, int(round(self.val_fraction * n)))
        val_idx, tr_idx = perm[:n_val], perm[n_val:]

        Xtr = torch.from_numpy(X[tr_idx])
        ytr = torch.from_numpy(y[tr_idx]).view(-1, 1)
        Xva = torch.from_numpy(X[val_idx])
        yva = torch.from_numpy(y[val_idx]).view(-1, 1)

        self.model_ = self._build(X.shape[1]).to(self.device)
        opt = torch.optim.Adam(self.model_.parameters(), lr=self.lr,
                               weight_decay=self.weight_decay)
        loss_fn = nn.BCEWithLogitsLoss()

        best_state, best_val, best_epoch, wait = None, float("inf"), 0, 0
        self.history_ = []
        for epoch in range(self.max_epochs):
            self.model_.train()
            g = torch.Generator().manual_seed(self.random_state * 1000 + epoch)
            order = torch.randperm(len(Xtr), generator=g)
            epoch_loss, n_batches = 0.0, 0
            for i in range(0, len(Xtr), self.batch_size):
                idx = order[i:i + self.batch_size]
                opt.zero_grad()
                out = self.model_(Xtr[idx])
                loss = loss_fn(out, ytr[idx])
                loss.backward()
                opt.step()
                epoch_loss += float(loss.item())
                n_batches += 1

            self.model_.eval()
            with torch.no_grad():
                val_loss = float(loss_fn(self.model_(Xva), yva).item())
            self.history_.append({"epoch": epoch + 1,
                                  "train_loss": epoch_loss / max(n_batches, 1),
                                  "val_loss": val_loss})
            if val_loss < best_val - 1e-6:
                best_val, best_epoch, wait = val_loss, epoch + 1, 0
                best_state = {k: v.detach().clone() for k, v in self.model_.state_dict().items()}
            else:
                wait += 1
                if wait >= self.patience:
                    break
        if best_state is not None:
            self.model_.load_state_dict(best_state)
        self.best_epoch_ = best_epoch
        self.best_val_loss_ = best_val
        self.n_features_in_ = X.shape[1]
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, X):
        check_is_fitted(self, "model_")
        X = np.asarray(X, dtype=np.float32)
        self.model_.eval()
        with torch.no_grad():
            logits = self.model_(torch.from_numpy(X)).view(-1)
            p1 = torch.sigmoid(logits).numpy()
        return np.column_stack([1.0 - p1, p1])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


# TabPFN v2 在 CPU 上默认禁止 >1000 训练样本；本任务 8693×28 落在论文的设计范围内
# （≤10000 样本、≤500 特征），因此显式放开限制。耗时见 checks/probe_tabpfn_scaling.py。
os.environ.setdefault("TABPFN_ALLOW_CPU_LARGE_DATASET", "1")
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

TABPFN_MODEL = "tabpfn-v2-classifier-v2_default.ckpt"


def make_tabpfn(n_estimators=8, random_state=0):
    from tabpfn import TabPFNClassifier

    return TabPFNClassifier(
        model_path=TABPFN_MODEL,
        device="cpu",
        n_estimators=n_estimators,
        random_state=random_state,
        ignore_pretraining_limits=True,
    )


MODEL_SPECS = {
    "logreg": {
        "label": "逻辑回归 (L2)",
        "factory": lambda rs=0, **kw: LogisticRegression(
            max_iter=3000, solver="lbfgs", random_state=rs, **kw),
        "grid": {"clf__C": [0.03, 0.1, 0.3, 1.0, 3.0, 10.0]},
    },
    "knn": {
        "label": "k 近邻 (kNN)",
        "factory": lambda rs=0, **kw: KNeighborsClassifier(n_jobs=-1, **kw),
        "grid": {"clf__n_neighbors": [5, 15, 25, 45, 75],
                 "clf__weights": ["uniform", "distance"]},
    },
    "lightgbm": {
        "label": "LightGBM 梯度提升树",
        "factory": lambda rs=0, **kw: __import__("lightgbm").LGBMClassifier(
            random_state=rs, n_jobs=-1, verbose=-1, **kw),
        "grid": {"clf__n_estimators": [300, 600],
                 "clf__learning_rate": [0.03, 0.05],
                 "clf__num_leaves": [15, 31, 63],
                 "clf__min_child_samples": [20, 50]},
    },
    "mlp": {
        "label": "多层感知机 (PyTorch MLP)",
        "factory": lambda rs=0, **kw: TorchMLPClassifier(random_state=rs, **kw),
        "grid": {"clf__hidden": [(64, 32), (128, 64), (256, 128, 64)],
                 "clf__dropout": [0.1, 0.3],
                 "clf__lr": [1e-3, 3e-3]},
    },
    "tabpfn": {
        "label": "TabPFN v2（表格基础模型）",
        "factory": lambda rs=0, **kw: make_tabpfn(random_state=rs, **kw),
        # TabPFN 不做梯度训练，几乎没有传统超参数；集成规模是唯一的"算力-精度"旋钮。
        "grid": {"clf__n_estimators": [8]},
    },
}


def model_label(name: str) -> str:
    return MODEL_SPECS[name]["label"]
