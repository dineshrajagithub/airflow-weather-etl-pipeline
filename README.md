# 🌦️ Airflow Weather ETL Pipeline

![CI](https://github.com/dineshrajagithub/airflow-weather-etl-pipeline/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.10-017CEE?logo=apacheairflow&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-S3%20compatible-C72E49?logo=minio&logoColor=white)

A daily batch pipeline built with Apache Airflow. It pulls weather history for several cities from the public
[Open-Meteo](https://open-meteo.com/) API and saves each raw response unchanged in an S3-compatible
storage area (the raw zone). It then checks the data quality and loads a typed fact table, plus a monthly
summary table (a "mart"), into a PostgreSQL warehouse.

## Architecture

```mermaid
flowchart LR
    A[Open-Meteo API] -->|extract, one task per city| B[(MinIO / S3<br/>raw zone, partitioned JSON)]
    B --> C[Transform<br/>pandas]
    C --> D{Data quality<br/>checks}
    D -->|pass| E[(Postgres<br/>fact_daily_weather)]
    D -->|fail| X[Task fails and Airflow retries / alerts]
    E --> F[(mart_city_monthly_weather)]
    F --> G[BI / SQL analysis]
```

| Task | What it does |
|------|--------------|
| `create_tables` | Creates the warehouse tables if they don't exist yet (safe to run repeatedly) |
| `extract` | Fetches each city in parallel (one mapped task per city), retrying with exponential backoff, and writes the raw response to `weather/city=…/run_date=…/payload.json` |
| `transform_validate_load` | Removes duplicates, adds derived columns (average temperature, daily range, rainy-day flag, heat category), runs blocking quality checks, then upserts into the fact table |
| `refresh_marts` | Rebuilds the monthly city summary table |

## Engineering highlights

- **Safe to re-run:** loads use `INSERT … ON CONFLICT DO UPDATE` on `(city, obs_date)`, so re-running a day or backfilling older dates never creates duplicate rows.
- **Raw data can be replayed:** raw responses are stored exactly as received, so the transform step can be run again without calling the API.
- **Data quality checks:** not-null, unique, value-range and min ≤ max rules stop the load when they fail. Missing values are reported without stopping the pipeline.
- **Parallel extraction:** Airflow's dynamic task mapping (`.expand()`) creates one extract task per city, with a limit on how many run at once.
- **Config through environment variables:** the same code runs on a laptop, in Docker, or on a managed service such as MWAA or Cloud Composer.
- **CI:** GitHub Actions runs linting and unit tests, plus a DAG import test against a real Airflow install.

## Project structure

```
├── dags/weather_etl_dag.py     # Airflow DAG (TaskFlow API)
├── etl/
│   ├── config.py               # cities, metrics, env-driven settings
│   ├── extract.py              # API client with retries + raw-zone writer
│   ├── transform.py            # pandas transformations
│   ├── quality.py              # data-quality checks
│   └── load.py                 # idempotent upsert loader
├── sql/
│   ├── schema.sql              # warehouse DDL
│   ├── marts.sql               # monthly aggregate mart
│   └── analysis_queries.sql    # window functions, gaps & islands
├── tests/                      # pytest suite (fixtures, no network needed)
└── docker-compose.yml          # Airflow + Postgres + MinIO
```

## Run it locally

```bash
git clone https://github.com/dineshrajagithub/airflow-weather-etl-pipeline.git
cd airflow-weather-etl-pipeline
make up          # starts Airflow, Postgres and MinIO
```

1. Open http://localhost:8080. The `admin` password is printed in the log of the `airflow` container.
2. Turn on the `weather_etl_daily` DAG and trigger a run.
3. Query the warehouse:

```bash
psql postgresql://warehouse:warehouse@localhost:5433/warehouse \
  -c "SELECT * FROM mart_city_monthly_weather ORDER BY month DESC, city;"
```

Run the tests (no Docker or network needed):

```bash
make install && make test
```

## Sample analysis (`sql/analysis_queries.sql`)

- Rolling 7-day average temperature per city (window functions)
- Longest streak of consecutive rainy days per city (the "gaps and islands" SQL pattern)
- Ranking of cities by monthly temperature variability (`RANK()` over `STDDEV`)

## Possible extensions

- Send alerts to Slack or email when a task fails (`on_failure_callback`)
- Replace the custom quality checks with Great Expectations or Soda
- Deploy to AWS MWAA with the raw zone on S3 and the warehouse on Redshift
