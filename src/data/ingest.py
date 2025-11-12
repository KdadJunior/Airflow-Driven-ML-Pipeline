from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from src.utils.io import write_csv


@dataclass
class IngestConfig:
    dataset_name: str
    split: str
    sample_size: int
    seed_offset: int


def deterministic_sample_indices(total_size: int, ds: str, sample_size: int, seed_offset: int) -> list[int]:
    seed_bytes = hashlib.sha256(f"{ds}-{seed_offset}".encode("utf-8")).digest()
    seed_int = int.from_bytes(seed_bytes, byteorder="big")
    rng = pd.Series(range(total_size)).sample(
        n=sample_size,
        random_state=seed_int,
        replace=False,
    )
    return rng.tolist()


def ingest_partition(ds: str, output_path: Path, config: IngestConfig) -> Path:
    """Load a deterministic sample of the IMDb dataset and persist it locally."""
    dataset = load_dataset(config.dataset_name, split=config.split)
    total_size = len(dataset)
    if config.sample_size > total_size:
        raise ValueError(f"Sample size {config.sample_size} exceeds dataset size {total_size}")

    indices = deterministic_sample_indices(
        total_size=total_size,
        ds=ds,
        sample_size=config.sample_size,
        seed_offset=config.seed_offset,
    )
    sampled = dataset.select(indices)
    df = sampled.to_pandas()
    df["partition_date"] = ds
    output_path = Path(output_path)
    write_csv(df, output_path)
    return output_path


