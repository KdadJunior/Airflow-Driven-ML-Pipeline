from pathlib import Path

import numpy as np
import pandas as pd

from src.train.eval import evaluate_run
from src.train.train import TrainingConfig, train_model


def test_train_and_evaluate(tmp_path: Path, monkeypatch):
    df = pd.DataFrame(
        {
            "f1": np.random.randn(200),
            "f2": np.random.randn(200),
            "label": np.random.randint(0, 2, size=200),
            "partition_date": ["2025-01-01"] * 200,
        }
    )
    features_path = tmp_path / "features.parquet"
    df.to_parquet(features_path, index=False)
    config = TrainingConfig(
        label_column="label",
        test_size=0.2,
        random_state=42,
        class_weight="balanced",
    )

    class DummyRun:
        def __init__(self) -> None:
            self.info = type("info", (), {"run_id": "123"})()

        def __enter__(self) -> "DummyRun":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    from src.train import train as train_module

    def dummy_start_run():
        return DummyRun()

    monkeypatch.setattr(train_module.mlflow, "start_run", dummy_start_run)
    monkeypatch.setattr(train_module.mlflow, "log_params", lambda *args, **kwargs: None)
    monkeypatch.setattr(train_module.mlflow, "log_artifact", lambda *args, **kwargs: None)
    monkeypatch.setattr(train_module.mlflow, "log_metrics", lambda *args, **kwargs: None)

    model_path, run_id = train_model(features_path, config, artifacts_dir=tmp_path / "artifacts")
    assert model_path.exists()
    assert run_id == "123"

    metrics_path = tmp_path / "artifacts" / "metrics.json"

    from src.train import eval as eval_module

    monkeypatch.setattr(eval_module, "mlflow", train_module.mlflow)

    result = evaluate_run(metrics_path, run_id)
    assert "pr_auc" in result.metrics
    assert result.confusion_matrix_path.exists()


