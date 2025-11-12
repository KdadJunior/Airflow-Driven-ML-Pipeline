from __future__ import annotations

from pathlib import Path
from typing import Any

import boto3
import pandas as pd
from botocore.client import Config as BotoConfig


class S3Client:
    """Thin wrapper around boto3 S3 client for MinIO interactions."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region_name: str = "us-east-1",
    ) -> None:
        self._client = boto3.resource(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            config=BotoConfig(signature_version="s3v4"),
        )

    def upload_file(self, local_path: Path, bucket: str, key: str) -> None:
        local_path = Path(local_path)
        local_path = local_path.resolve()
        self._client.Bucket(bucket).upload_file(str(local_path), key)

    def download_file(self, bucket: str, key: str, local_path: Path) -> None:
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self._client.Bucket(bucket).download_file(key, str(local_path))

    def object_exists(self, bucket: str, key: str) -> bool:
        try:
            self._client.Object(bucket, key).load()
        except self._client.meta.client.exceptions.NoSuchKey:
            return False
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Unable to check {bucket}/{key}") from exc
        return True

    def put_json(self, bucket: str, key: str, data: Any) -> None:
        import json

        json_bytes = json.dumps(data).encode("utf-8")
        self._client.Object(bucket, key).put(Body=json_bytes)

    def get_json(self, bucket: str, key: str) -> Any:
        import json

        obj = self._client.Object(bucket, key).get()
        return json.loads(obj["Body"].read().decode("utf-8"))


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


