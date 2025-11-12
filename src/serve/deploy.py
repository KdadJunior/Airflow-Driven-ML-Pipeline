from __future__ import annotations

import logging
import shutil
import subprocess
from typing import Dict

logger = logging.getLogger(__name__)


def trigger_fastapi_reload(environment: Dict[str, str]) -> None:
    """Simple deployment hook to restart FastAPI container via docker compose."""
    docker_command = shutil.which("docker")
    if docker_command is None:
        logger.warning("Docker not available in environment; skipping restart")
        return
    try:
        subprocess.run(
            [
                docker_command,
                "compose",
                "-f",
                "docker/docker-compose.yaml",
                "restart",
                "fastapi",
            ],
            check=True,
            env=environment,
        )
    except subprocess.CalledProcessError as exc:
        logger.exception("Failed to restart FastAPI service")
        raise RuntimeError("FastAPI restart failed") from exc


