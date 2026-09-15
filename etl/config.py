"""Central configuration, driven by environment variables so the same code
runs locally, in Docker Compose and in a managed Airflow environment."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class City:
    name: str
    country: str
    latitude: float
    longitude: float


DEFAULT_CITIES: tuple[City, ...] = (
    City("Chennai", "IN", 13.0827, 80.2707),
    City("Bengaluru", "IN", 12.9716, 77.5946),
    City("Mumbai", "IN", 19.0760, 72.8777),
    City("New York", "US", 40.7128, -74.0060),
    City("London", "GB", 51.5072, -0.1276),
)

DAILY_METRICS: tuple[str, ...] = (
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
)


@dataclass(frozen=True)
class Settings:
    api_url: str = os.getenv(
        "WEATHER_API_URL", "https://archive-api.open-meteo.com/v1/archive"
    )
    raw_bucket: str = os.getenv("RAW_BUCKET", "weather-raw")
    s3_endpoint: str | None = os.getenv("S3_ENDPOINT_URL")  # MinIO locally
    local_raw_dir: str = os.getenv("LOCAL_RAW_DIR", "/tmp/weather-raw")
    warehouse_dsn: str = os.getenv(
        "WAREHOUSE_DSN", "postgresql://warehouse:warehouse@postgres-dw:5432/warehouse"
    )
    cities: tuple[City, ...] = field(default=DEFAULT_CITIES)


settings = Settings()
