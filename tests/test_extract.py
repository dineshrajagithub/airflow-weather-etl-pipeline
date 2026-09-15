from datetime import date

from etl.config import City
from etl.extract import build_params, raw_key, read_raw, write_raw


def test_build_params():
    p = build_params(City("New York", "US", 1.0, 2.0), date(2026, 9, 1), date(2026, 9, 7))
    assert p["start_date"] == "2026-09-01" and p["end_date"] == "2026-09-07"
    assert "precipitation_sum" in p["daily"]


def test_raw_key_is_partitioned():
    key = raw_key(City("New York", "US", 1.0, 2.0), date(2026, 9, 8))
    assert key == "weather/city=new_york/run_date=2026-09-08/payload.json"


def test_local_raw_roundtrip(tmp_path, monkeypatch):
    from etl import extract
    from etl.config import Settings

    monkeypatch.setattr(extract, "settings", Settings(s3_endpoint=None, local_raw_dir=str(tmp_path)))
    uri = write_raw({"a": 1}, "x/y.json")
    assert read_raw(uri) == {"a": 1}
