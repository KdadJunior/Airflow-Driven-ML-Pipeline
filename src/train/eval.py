from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import mlflow
import numpy as np
from sklearn.metrics import ConfusionMatrixDisplay


@dataclass
class EvaluationResult:
    metrics: Dict[str, float]
    confusion_matrix_path: Path


def evaluate_run(metrics_artifact: Path, run_id: str) -> EvaluationResult:
    payload = json.loads(Path(metrics_artifact).read_text())
    metrics = payload["metrics"]
    y_test = np.array(payload["y_test"])
    y_proba = np.array(payload["y_proba"])
    y_pred = (y_proba >= 0.5).astype(int)

    cm_display = ConfusionMatrixDisplay.from_predictions(y_test, y_pred)
    figure = cm_display.figure_
    confusion_path = Path(metrics_artifact).parent / "confusion_matrix.png"
    figure.savefig(confusion_path)
    figure.clear()

    with mlflow.start_run(run_id=run_id):
        mlflow.log_metrics(metrics)
        mlflow.log_artifact(str(confusion_path), artifact_path="evaluation")

    return EvaluationResult(metrics=metrics, confusion_matrix_path=confusion_path)


