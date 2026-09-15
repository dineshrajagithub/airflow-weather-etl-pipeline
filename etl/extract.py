"""Extract daily weather from the Open-Meteo archive API and land the raw
payload unchanged in the raw zone (S3 / MinIO, or local disk)."""
from __future__ import annotations

import json
import logging
import time
from datetime import date
from pathlib import Path

import requests

from .config import DAILY_METRICS, City, settings

log = logging.getLogger(__name__)


def build_params(city: City, start: date, end: date) -> dict:
    return {
        "latitude": city.latitude,
        "longitude": city.longitude,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(DAILY_METRICS),
        "timezone": "UTC",
    }


def fetch_city_weather(
    city: City, start: date, end: date, retries: int = 3, backoff: float = 2.0
) -> dict:
    """Call the API with simple exponential backoff on transient errors."""
    params = build_params(city, start, end)
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(settings.api_url, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
            payload["_city"] = city.name
            payload["_country"] = city.country
            return payload
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            wait = backoff ** attempt
            log.warning("Attempt %s for %s failed (%s); retrying in %ss",
                        attempt, city.name, exc, wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def raw_key(city: City, run_date: date) -> str:
    slug = city.name.lower().replace(" ", "_")
    return f"weather/city={slug}/run_date={run_date.isoformat()}/payload.json"


def write_raw(payload: dict, key: str) -> str:
    """Persist the untouched payload. Uses S3 when an endpoint/bucket is
    configured, otherwise the local filesystem (handy for tests and demos)."""
    body = json.dumps(payload).encode("utf-8")
    if settings.s3_endpoint:
        import boto3  # imported lazily so unit tests don't need it

        s3 = boto3.client("s3", endpoint_url=settings.s3_endpoint)
        s3.put_object(Bucket=settings.raw_bucket, Key=key, Body=body)
        return f"s3://{settings.raw_bucket}/{key}"
    path = Path(settings.local_raw_dir) / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return str(path)


def read_raw(uri: str) -> dict:
    if uri.startswith("s3://"):
        import boto3

        bucket, key = uri[5:].split("/", 1)
        s3 = boto3.client("s3", endpoint_url=settings.s3_endpoint)
        return json.loads(s3.get_object(Bucket=bucket, Key=key)["Body"].read())
    return json.loads(Path(uri).read_text())
