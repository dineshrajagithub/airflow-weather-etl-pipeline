"""Runs only where Airflow is installed (CI / Docker)."""
from pathlib import Path

import pytest

airflow = pytest.importorskip("airflow")


def test_dag_imports_without_errors():
    from airflow.models import DagBag

    bag = DagBag(dag_folder=str(Path(__file__).parent.parent / "dags"), include_examples=False)
    assert bag.import_errors == {}
    dag = bag.get_dag("weather_etl_daily")
    assert dag is not None
    assert {"create_tables", "extract", "transform_validate_load", "refresh_marts"} <= set(dag.task_ids)
