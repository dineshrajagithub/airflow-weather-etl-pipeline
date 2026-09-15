"""Turn raw Open-Meteo payloads into a tidy, typed fact table."""
from __future__ import annotations

import pandas as pd

from .config import DAILY_METRICS

FACT_COLUMNS = [
    "city", "country", "obs_date", "temp_max_c", "temp_min_c",
    "temp_avg_c", "temp_range_c", "precipitation_mm", "wind_speed_max_kmh",
    "is_rainy_day", "heat_category",
]

RENAME = {
    "time": "obs_date",
    "temperature_2m_max": "temp_max_c",
    "temperature_2m_min": "temp_min_c",
    "precipitation_sum": "precipitation_mm",
    "wind_speed_10m_max": "wind_speed_max_kmh",
}


def payload_to_frame(payload: dict) -> pd.DataFrame:
    daily = payload.get("daily") or {}
    missing = [m for m in ("time", *DAILY_METRICS) if m not in daily]
    if missing:
        raise ValueError(f"payload missing daily fields: {missing}")
    df = pd.DataFrame({k: daily[k] for k in ("time", *DAILY_METRICS)})
    df["city"] = payload["_city"]
    df["country"] = payload["_country"]
    return df.rename(columns=RENAME)


def classify_heat(temp_max: float) -> str:
    if pd.isna(temp_max):
        return "unknown"
    if temp_max >= 35:
        return "very_hot"
    if temp_max >= 28:
        return "hot"
    if temp_max >= 15:
        return "mild"
    return "cold"


def transform(payloads: list[dict]) -> pd.DataFrame:
    if not payloads:
        return pd.DataFrame(columns=FACT_COLUMNS)
    df = pd.concat([payload_to_frame(p) for p in payloads], ignore_index=True)
    df["obs_date"] = pd.to_datetime(df["obs_date"]).dt.date
    numeric = ["temp_max_c", "temp_min_c", "precipitation_mm", "wind_speed_max_kmh"]
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="coerce")

    # Deduplicate: re-runs / overlapping windows keep the latest record.
    df = df.drop_duplicates(subset=["city", "obs_date"], keep="last")

    df["temp_avg_c"] = ((df["temp_max_c"] + df["temp_min_c"]) / 2).round(2)
    df["temp_range_c"] = (df["temp_max_c"] - df["temp_min_c"]).round(2)
    df["precipitation_mm"] = df["precipitation_mm"].fillna(0.0)
    df["is_rainy_day"] = df["precipitation_mm"] >= 1.0
    df["heat_category"] = df["temp_max_c"].map(classify_heat)
    return df[FACT_COLUMNS].sort_values(["city", "obs_date"]).reset_index(drop=True)
