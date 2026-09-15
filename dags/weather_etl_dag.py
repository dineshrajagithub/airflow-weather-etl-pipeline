"""
Daily weather ETL.

    create_tables -> extract (mapped per city) -> transform_validate_load -> refresh_marts

* Dynamic task mapping fans extraction out per city.
* Raw payloads are stored untouched (replayable), only URIs travel via XCom.
* Loads are idempotent UPSERTs, so `airflow dags backfill` is safe.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
WAREHOUSE_CONN_ID = "warehouse_postgres"
# The Open-Meteo archive lags a few days behind real time.
LAG_DAYS = 5
WINDOW_DAYS = 7

default_args = {
    "owner": "dinesh",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
}


@dag(
    dag_id="weather_etl_daily",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["etl", "weather", "postgres"],
    doc_md=__doc__,
)
def weather_etl():
    @task
    def create_tables() -> None:
        PostgresHook(WAREHOUSE_CONN_ID).run((SQL_DIR / "schema.sql").read_text())

    @task
    def list_cities() -> list[dict]:
        from etl.config import settings

        return [c.__dict__ for c in settings.cities]

    @task(max_active_tis_per_dag=3)
    def extract(city: dict, data_interval_end=None) -> str:
        from etl.config import City
        from etl.extract import fetch_city_weather, raw_key, write_raw

        end = (data_interval_end - timedelta(days=LAG_DAYS)).date()
        start = end - timedelta(days=WINDOW_DAYS - 1)
        c = City(**city)
        payload = fetch_city_weather(c, start, end)
        return write_raw(payload, raw_key(c, data_interval_end.date()))

    @task
    def transform_validate_load(raw_uris: list[str]) -> int:
        from etl.extract import read_raw
        from etl.load import load
        from etl.quality import enforce
        from etl.transform import transform

        df = transform([read_raw(u) for u in raw_uris])
        for result in enforce(df):
            print(result)
        conn = PostgresHook(WAREHOUSE_CONN_ID).get_conn()
        try:
            return load(df, conn)
        finally:
            conn.close()

    @task
    def refresh_marts() -> None:
        PostgresHook(WAREHOUSE_CONN_ID).run((SQL_DIR / "marts.sql").read_text())

    uris = extract.expand(city=list_cities())
    loaded = transform_validate_load(uris)
    create_tables() >> uris
    loaded >> refresh_marts()


weather_etl()
