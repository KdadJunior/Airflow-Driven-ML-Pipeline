from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from great_expectations.dataset import PandasDataset


class ImdbRawDataset(PandasDataset):
    """Embeds our expectation suite directly for lightweight validation."""

    def __init__(self, data: pd.DataFrame, suite_path: Path) -> None:  # type: ignore[override]
        self._suite_path = suite_path
        super().__init__(data)
        self._apply_suite()

    def _apply_suite(self) -> None:
        suite_json = json.loads(Path(self._suite_path).read_text())
        for expectation in suite_json["expectations"]:
            expectation_type = expectation["expectation_type"]
            kwargs = expectation.get("kwargs", {})
            getattr(self, expectation_type)(**kwargs)


@dataclass
class ValidationResult:
    success: bool
    result: dict


def validate_raw(df: pd.DataFrame, suite_path: Path) -> ValidationResult:
    dataset = ImdbRawDataset(df, suite_path=suite_path)
    validation_result = dataset.validate()
    return ValidationResult(success=validation_result["success"], result=validation_result)  # type: ignore[index]


