"""Idempotent load into the warehouse using an UPSERT, so any day can be
re-processed (backfills) without creating duplicates."""
from __future__ import annotations

from typing import Any

import pandas as pd

TABLE = "fact_daily_weather"
KEY = ("city", "obs_date")


def upsert_sql(columns: list[str], placeholder: str = "%s") -> str:
    cols = ", ".join(columns)
    values = ", ".join([placeholder] * len(columns))
    updates = ", ".join(f"{c} = excluded.{c}" for c in columns if c not in KEY)
    return (
        f"INSERT INTO {TABLE} ({cols}) VALUES ({values}) "
        f"ON CONFLICT ({', '.join(KEY)}) DO UPDATE SET {updates}"
    )


def _py(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):  # numpy scalar -> python
        return value.item()
    return value


def load(df: pd.DataFrame, conn, placeholder: str = "%s") -> int:
    """Works with any DB-API connection (psycopg2 in prod, sqlite in tests)."""
    if df.empty:
        return 0
    columns = list(df.columns)
    rows = [tuple(_py(v) for v in row) for row in df.itertuples(index=False)]
    cur = conn.cursor()
    cur.executemany(upsert_sql(columns, placeholder), rows)
    conn.commit()
    return len(rows)
