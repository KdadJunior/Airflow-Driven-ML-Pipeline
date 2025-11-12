from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import pandas as pd
from evidently.metrics import ColumnDriftMetric
from evidently.report import Report


@dataclass
class DriftConfig:
    text_column: str
    label_column: str
    psi_warning_threshold: float
    psi_alert_threshold: float


def run_drift_report(
    reference_path: Path,
    current_path: Path,
    config: DriftConfig,
    output_dir: Path,
) -> Dict[str, float]:
    reference_df = pd.read_parquet(reference_path)
    current_df = pd.read_parquet(current_path)

    report = Report(
        metrics=[
            ColumnDriftMetric(column_name=config.label_column),
        ]
    )
    report.run(reference_data=reference_df, current_data=current_df)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "drift_report.html"
    json_path = output_dir / "drift_report.json"
    report.save_html(str(html_path))
    report.save_json(str(json_path))

    payload = json.loads(json_path.read_text())
    psi = payload["metrics"][0]["result"]["drift_score"]

    status = "normal"
    if psi >= config.psi_alert_threshold:
        status = "alert"
    elif psi >= config.psi_warning_threshold:
        status = "warning"

    summary = {"psi": psi, "status": status}
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


