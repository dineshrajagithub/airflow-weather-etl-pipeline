import pytest

from etl.transform import FACT_COLUMNS, classify_heat, payload_to_frame, transform


def test_transform_shape_and_columns(payloads):
    df = transform(payloads)
    assert list(df.columns) == FACT_COLUMNS
    assert len(df) == 6


def test_derived_metrics(payloads):
    df = transform(payloads)
    row = df[(df.city == "Chennai") & (df.obs_date.astype(str) == "2026-09-01")].iloc[0]
    assert row.temp_avg_c == pytest.approx(30.8)
    assert row.temp_range_c == pytest.approx(8.8)
    assert row.heat_category == "very_hot"
    assert not row.is_rainy_day


def test_missing_precip_becomes_zero_and_missing_temp_is_unknown(payloads):
    df = transform(payloads)
    row = df[(df.city == "Chennai") & (df.obs_date.astype(str) == "2026-09-03")].iloc[0]
    assert row.precipitation_mm == 0.0
    assert row.heat_category == "unknown"


def test_duplicates_keep_latest(payloads):
    updated = {**payloads[1], "daily": {**payloads[1]["daily"],
                                         "temperature_2m_max": [99.0, 17.0, 21.3]}}
    df = transform([payloads[1], updated])
    assert len(df) == 3
    assert df.iloc[0].temp_max_c == 99.0


def test_missing_fields_raise():
    with pytest.raises(ValueError):
        payload_to_frame({"daily": {"time": []}, "_city": "x", "_country": "y"})


def test_empty_input():
    assert transform([]).empty


@pytest.mark.parametrize("temp,expected", [(40, "very_hot"), (30, "hot"),
                                           (20, "mild"), (5, "cold")])
def test_classify_heat(temp, expected):
    assert classify_heat(temp) == expected
