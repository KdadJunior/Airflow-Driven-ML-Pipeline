from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import yaml
from airflow import Dataset
from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException
from airflow.models import Variable

from src.data.ingest import IngestConfig, ingest_partition
from src.data.validate import validate_raw
from src.features.build import FeatureConfig, build_features
from src.monitor.drift_job import DriftConfig, run_drift_report
from src.train.eval import evaluate_run
from src.train.register import PromotionDecision, evaluate_promotion
from src.train.train import TrainingConfig, train_model
from src.utils.io import load_csv

CONFIG_PATH = Path("/opt/airflow/include/configs/params.yaml")
EXPECTATION_PATH = Path("/opt/airflow/include/expectations/imdb_reviews.json")
DATA_DIR = Path("/opt/airflow/data")


def load_config() -> Dict[str, Dict]:
    with CONFIG_PATH.open() as fp:
        return yaml.safe_load(fp)


@dag(
    dag_id="mlops_imdb",
    schedule="0 2 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=True,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["mlops", "imdb"],
)
def mlops_imdb_dag():
    config = load_config()
    raw_bucket = Variable.get("RAW_BUCKET", default_var="mlops-raw")
    feature_bucket = Variable.get("FEATURE_BUCKET", default_var="mlops-features")
    monitor_bucket = Variable.get("MONITOR_BUCKET", default_var="mlops-monitor")
    promotion_rules = yaml.safe_load(Variable.get("PROMOTION_RULES", default_var="")) or config["promotion"]
    model_name = Variable.get("MODEL_NAME", default_var="imdb_sentiment")

    @task(outlets=[Dataset(f"s3://{raw_bucket}/imdb/{{{{ ds }}}}.csv")])
    def ingest(ds: str) -> str:
        ingest_cfg = IngestConfig(
            dataset_name=config["dataset"]["name"],
            split=config["dataset"]["ingest"]["split"],
            sample_size=config["dataset"]["ingest"]["daily_sample_size"],
            seed_offset=config["dataset"]["ingest"]["seed_offset"],
        )
        output = DATA_DIR / "raw" / f"imdb_{ds}.csv"
        ingest_partition(ds=ds, output_path=output, config=ingest_cfg)
        return str(output)

    @task()
    def validate(raw_path: str) -> str:
        df = load_csv(Path(raw_path))
        result = validate_raw(df, EXPECTATION_PATH)
        if not result.success:
            raise AirflowFailException("Validation failed; blocking downstream tasks")
        return raw_path

    @task(outlets=[Dataset(f"s3://{feature_bucket}/imdb/{{{{ ds }}}}.parquet")])
    def build(raw_path: str, ds: str) -> Dict[str, str]:
        feature_cfg = FeatureConfig(
            text_column=config["features"]["text_column"],
            label_column=config["features"]["label_column"],
            tfidf_max_features=config["features"]["tfidf_max_features"],
            min_df=config["features"]["min_df"],
            max_df=config["features"]["max_df"],
        )
        raw_df = load_csv(Path(raw_path))
        features_path, artifacts_dir = build_features(
            df=raw_df,
            config=feature_cfg,
            output_features=DATA_DIR / "features" / f"imdb_{ds}.parquet",
            artifacts_dir=DATA_DIR / "artifacts" / ds,
        )
        return {"features_path": str(features_path), "artifacts_dir": str(artifacts_dir)}

    @task
    def train(feature_outputs: Dict[str, str]) -> Dict[str, str]:
        train_cfg = TrainingConfig(
            label_column=config["features"]["label_column"],
            test_size=config["training"]["test_size"],
            random_state=config["training"]["random_state"],
            class_weight=config["training"]["class_weight"],
        )
        model_path, run_id = train_model(
            features_path=Path(feature_outputs["features_path"]),
            config=train_cfg,
            artifacts_dir=Path(feature_outputs["artifacts_dir"]),
        )
        metrics_artifact = Path(feature_outputs["artifacts_dir"]) / "metrics.json"
        return {
            "run_id": run_id,
            "metrics_artifact": str(metrics_artifact),
            "model_path": str(model_path),
        }

    @task
    def evaluate(train_outputs: Dict[str, str]) -> Dict[str, str]:
        evaluation = evaluate_run(
            metrics_artifact=Path(train_outputs["metrics_artifact"]),
            run_id=train_outputs["run_id"],
        )
        return {
            "run_id": train_outputs["run_id"],
            "metrics": evaluation.metrics,
        }

    @task
    def register(evaluation_payload: Dict[str, str]) -> Dict[str, str | int | bool | Dict]:
        decision = evaluate_promotion(
            model_name=model_name,
            run_id=evaluation_payload["run_id"],
            metrics=evaluation_payload["metrics"],
            promotion_rules=promotion_rules,
        )
        return {
            "promoted": decision.promoted,
            "version": decision.version,
            "reason": decision.reason,
            "challenger_metrics": decision.challenger_metrics,
            "production_metrics": decision.production_metrics,
        }

    @task
    def deploy(decision_payload: Dict[str, str | int | bool | Dict]) -> str:
        if not decision_payload["promoted"]:
            return str(decision_payload["reason"])
        from src.serve.deploy import trigger_fastapi_reload

        trigger_fastapi_reload(environment={})
        return f"Deployment triggered for version {decision_payload['version']}"

    @task(outlets=[Dataset(f"s3://{monitor_bucket}/imdb/{{{{ ds }}}}.json")])
    def monitor(feature_outputs: Dict[str, str], ds: str) -> Dict[str, str]:
        config_data = DriftConfig(
            text_column=config["features"]["text_column"],
            label_column=config["features"]["label_column"],
            psi_warning_threshold=config["monitoring"]["psi_warning_threshold"],
            psi_alert_threshold=config["monitoring"]["psi_alert_threshold"],
        )
        current_path = Path(feature_outputs["features_path"])
        reference_days = config["monitoring"]["drift_reference_days"]
        reference_date = (datetime.strptime(ds, "%Y-%m-%d") - timedelta(days=reference_days)).strftime(
            "%Y-%m-%d"
        )
        reference_path = DATA_DIR / "features" / f"imdb_{reference_date}.parquet"
        if not reference_path.exists():
            reference_path = current_path
        summary = run_drift_report(
            reference_path=reference_path,
            current_path=current_path,
            config=config_data,
            output_dir=DATA_DIR / "monitor" / ds,
        )
        return summary

    raw_file = ingest()
    validated = validate(raw_file)
    features = build(validated)
    training_outputs = train(features)
    evaluation = evaluate(training_outputs)
    decision = register(evaluation)
    deploy(decision)
    monitor(features)


mlops_imdb_dag()


