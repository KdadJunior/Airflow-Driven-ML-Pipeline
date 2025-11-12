from __future__ import annotations

from pathlib import Path

import yaml

from src.data.ingest import IngestConfig, ingest_partition


def main() -> None:
    config_path = Path("include/configs/params.yaml")
    config = yaml.safe_load(config_path.read_text())
    ingest_cfg = IngestConfig(
        dataset_name=config["dataset"]["name"],
        split=config["dataset"]["ingest"]["split"],
        sample_size=config["dataset"]["ingest"]["daily_sample_size"],
        seed_offset=config["dataset"]["ingest"]["seed_offset"],
    )
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    ingest_partition("2025-01-01", output_dir / "imdb_2025-01-01.csv", ingest_cfg)
    print("Seeded raw data for 2025-01-01")


if __name__ == "__main__":
    main()


