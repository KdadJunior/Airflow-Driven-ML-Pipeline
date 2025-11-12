from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from src.utils.metrics import compute_binary_metrics


@dataclass
class TrainingConfig:
    label_column: str
    test_size: float
    random_state: int
    class_weight: str | None = None


def split_features(df: pd.DataFrame, label_column: str) -> Tuple[np.ndarray, np.ndarray]:
    y = df[label_column].values
    X = df.drop(columns=[label_column, "partition_date"]).values
    return X, y


def train_model(
    features_path: Path,
    config: TrainingConfig,
    artifacts_dir: Path,
) -> Tuple[Path, str]:
    df = pd.read_parquet(features_path)
    X, y = split_features(df, config.label_column)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.test_size,
        random_state=config.random_state,
        stratify=y,
    )

    clf = LogisticRegression(
        max_iter=200,
        random_state=config.random_state,
        class_weight=config.class_weight,
    )
    clf.fit(X_train, y_train)
    y_proba = clf.predict_proba(X_test)[:, 1]
    metrics = compute_binary_metrics(y_test, y_proba)

    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifacts_dir / "model.joblib"
    joblib.dump(clf, model_path)

    metrics_path = artifacts_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                "y_test": y_test.tolist(),
                "y_proba": y_proba.tolist(),
                "metrics": metrics.as_dict,
            }
        )
    )

    with mlflow.start_run() as run:
        mlflow.log_params(
            {
                "model_type": "logistic_regression",
                "test_size": config.test_size,
                "random_state": config.random_state,
            }
        )
        mlflow.log_artifact(str(model_path), artifact_path="model_artifacts")
        mlflow.log_artifact(str(metrics_path), artifact_path="evaluation")
        run_id = run.info.run_id

    return model_path, run_id


