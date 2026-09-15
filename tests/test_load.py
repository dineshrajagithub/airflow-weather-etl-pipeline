import sqlite3

from etl.load import load
from etl.transform import transform

DDL = """CREATE TABLE fact_daily_weather (
  city TEXT, country TEXT, obs_date TEXT, temp_max_c REAL, temp_min_c REAL,
  temp_avg_c REAL, temp_range_c REAL, precipitation_mm REAL,
  wind_speed_max_kmh REAL, is_rainy_day INTEGER, heat_category TEXT,
  PRIMARY KEY (city, obs_date))"""


def test_load_is_idempotent(payloads):
    conn = sqlite3.connect(":memory:")
    conn.execute(DDL)
    df = transform(payloads)
    df["obs_date"] = df["obs_date"].astype(str)
    assert load(df, conn, placeholder="?") == 6
    df.loc[0, "temp_max_c"] = 36.0
    load(df, conn, placeholder="?")  # re-run = update, not duplicate
    assert conn.execute("SELECT COUNT(*) FROM fact_daily_weather").fetchone()[0] == 6
    assert conn.execute(
        "SELECT MAX(temp_max_c) FROM fact_daily_weather WHERE city='Chennai'"
    ).fetchone()[0] == 36.0
