from pathlib import Path

import pandas as pd

from src.features.build import FeatureConfig, build_features, load_vectorizer


def test_build_features(tmp_path: Path):
    df = pd.DataFrame(
        {
            "text": ["great movie", "bad acting"],
            "label": [1, 0],
            "partition_date": ["2025-01-01", "2025-01-01"],
        }
    )
    config = FeatureConfig(
        text_column="text",
        label_column="label",
        tfidf_max_features=10,
        min_df=1,
        max_df=1.0,
    )
    features_path, artifacts_dir = build_features(
        df,
        config,
        output_features=tmp_path / "features.parquet",
        artifacts_dir=tmp_path / "artifacts",
    )
    assert features_path.exists()
    assert artifacts_dir.exists()
    vectorizer = load_vectorizer(artifacts_dir)
    assert len(vectorizer.get_feature_names_out()) > 0


