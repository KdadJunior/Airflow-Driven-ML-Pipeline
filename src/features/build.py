from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.utils.io import write_csv


@dataclass
class FeatureConfig:
    text_column: str
    label_column: str
    tfidf_max_features: int
    min_df: int
    max_df: float


def build_features(
    df: pd.DataFrame,
    config: FeatureConfig,
    output_features: Path,
    artifacts_dir: Path,
) -> Tuple[Path, Path]:
    """Build deterministic TF-IDF features and persist vectorizer artifacts."""
    vectorizer = TfidfVectorizer(
        max_features=config.tfidf_max_features,
        min_df=config.min_df,
        max_df=config.max_df,
        dtype="float32",
    )
    features = vectorizer.fit_transform(df[config.text_column])
    features_df = pd.DataFrame(
        features.toarray(),
        columns=vectorizer.get_feature_names_out(),
    )
    features_df[config.label_column] = df[config.label_column].values
    features_df["partition_date"] = df["partition_date"].values

    output_features = Path(output_features)
    output_features.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_parquet(output_features, index=False)

    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, artifacts_dir / "tfidf_vectorizer.joblib")
    metadata = {
        "text_column": config.text_column,
        "label_column": config.label_column,
        "tfidf_max_features": config.tfidf_max_features,
    }
    (artifacts_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    return output_features, artifacts_dir


def load_vectorizer(artifacts_dir: Path) -> TfidfVectorizer:
    return joblib.load(Path(artifacts_dir) / "tfidf_vectorizer.joblib")


