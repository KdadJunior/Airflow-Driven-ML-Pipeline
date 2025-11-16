from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from great_expectations.dataset import PandasDataset


@dataclass
class ValidationResult:
    success: bool
    result: dict


def validate_raw(df: pd.DataFrame, suite_path: Path) -> ValidationResult:
    """Validate a DataFrame against a Great Expectations suite."""
    # Create PandasDataset directly to avoid recursion issues with pandas 2.2+
    # Convert DataFrame to dict first to avoid attribute access issues
    dataset = PandasDataset(df.copy())
    
    # Load and apply expectations
    suite_json = json.loads(Path(suite_path).read_text())
    for expectation in suite_json["expectations"]:
        expectation_type = expectation["expectation_type"]
        kwargs = expectation.get("kwargs", {})
        expectation_method = getattr(dataset, expectation_type)
        expectation_method(**kwargs)
    
    validation_result = dataset.validate()
    return ValidationResult(success=validation_result["success"], result=validation_result)  # type: ignore[index]


