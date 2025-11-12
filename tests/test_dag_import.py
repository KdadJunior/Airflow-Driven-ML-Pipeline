import importlib
import pkgutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DAGS_PATH = PROJECT_ROOT / "dags"


def test_dag_imports():
    dag_files = [
        name
        for _, name, is_pkg in pkgutil.iter_modules([str(DAGS_PATH)])
        if not is_pkg
    ]
    assert dag_files, "No DAG modules found in dags/"

    errors = []
    for dag_module in dag_files:
        try:
            importlib.import_module(f"dags.{dag_module}")
        except Exception as exc:  # noqa: BLE001
            errors.append((dag_module, exc))

    assert not errors, f"DAG import failures: {errors}"


