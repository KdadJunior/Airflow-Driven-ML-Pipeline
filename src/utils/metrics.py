from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
from sklearn import metrics


@dataclass
class BinaryMetrics:
    pr_auc: float
    roc_auc: float
    f1: float
    log_loss: float

    @property
    def as_dict(self) -> Dict[str, float]:
        return {
            "pr_auc": self.pr_auc,
            "roc_auc": self.roc_auc,
            "f1": self.f1,
            "log_loss": self.log_loss,
        }


def compute_binary_metrics(y_true: np.ndarray, y_proba: np.ndarray) -> BinaryMetrics:
    precision, recall, _ = metrics.precision_recall_curve(y_true, y_proba)
    pr_auc = metrics.auc(recall, precision)
    roc_auc = metrics.roc_auc_score(y_true, y_proba)
    log_loss = metrics.log_loss(y_true, y_proba)
    preds = (y_proba >= 0.5).astype(int)
    f1 = metrics.f1_score(y_true, preds)
    return BinaryMetrics(pr_auc=pr_auc, roc_auc=roc_auc, f1=f1, log_loss=log_loss)


