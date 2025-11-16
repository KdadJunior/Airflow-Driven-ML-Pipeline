from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import mlflow
from mlflow.exceptions import RestException, MlflowException


@dataclass
class PromotionDecision:
    promoted: bool
    version: int | None
    reason: str
    challenger_metrics: Dict[str, float]
    production_metrics: Dict[str, float] | None


def fetch_production_metrics(model_name: str) -> Dict[str, float] | None:
    client = mlflow.MlflowClient()
    stages = client.get_latest_versions(model_name, stages=["Production"])
    if not stages:
        return None
    run_id = stages[0].run_id
    data = client.get_run(run_id).data.metrics
    return dict(data)


def evaluate_promotion(
    model_name: str,
    run_id: str,
    metrics: Dict[str, float],
    promotion_rules: Dict[str, float],
) -> PromotionDecision:
    client = mlflow.MlflowClient()
    try:
        client.get_registered_model(model_name)
    except (RestException, MlflowException) as e:
        # Model doesn't exist, create it
        # Check if it's a "not found" error
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not exist" in error_msg:
            client.create_registered_model(model_name)
        else:
            # Re-raise if it's a different error
            raise

    production_metrics = fetch_production_metrics(model_name)

    run_info = client.get_run(run_id).info
    model_source = f"{run_info.artifact_uri}/model_artifacts"

    if production_metrics is None:
        meets_baseline = metrics["pr_auc"] >= promotion_rules["baseline_pr_auc"]
        if not meets_baseline:
            return PromotionDecision(
                promoted=False,
                version=None,
                reason="Challenger did not meet baseline PR-AUC threshold",
                challenger_metrics=metrics,
                production_metrics=None,
            )
        model_version = client.create_model_version(
            name=model_name,
            source=model_source,
            run_id=run_id,
        )
        client.transition_model_version_stage(
            name=model_name,
            version=model_version.version,
            stage="Production",
        )
        return PromotionDecision(
            promoted=True,
            version=model_version.version,
            reason="Baseline satisfied, first Production model created",
            challenger_metrics=metrics,
            production_metrics=None,
        )

    pr_auc_improvement = metrics["pr_auc"] - production_metrics.get("pr_auc", 0.0)
    roc_auc_delta = metrics["roc_auc"] - production_metrics.get("roc_auc", 0.0)
    if (
        pr_auc_improvement >= promotion_rules["pr_auc_delta"]
        and roc_auc_delta >= promotion_rules["roc_auc_floor_delta"]
    ):
        model_version = client.create_model_version(
            name=model_name,
            source=model_source,
            run_id=run_id,
        )
        client.transition_model_version_stage(
            name=model_name,
            version=model_version.version,
            stage="Production",
            archive_existing_versions=True,
        )
        return PromotionDecision(
            promoted=True,
            version=model_version.version,
            reason="Challenger satisfied promotion rules",
            challenger_metrics=metrics,
            production_metrics=production_metrics,
        )

    return PromotionDecision(
        promoted=False,
        version=None,
        reason="Challenger did not meet promotion thresholds",
        challenger_metrics=metrics,
        production_metrics=production_metrics,
    )


