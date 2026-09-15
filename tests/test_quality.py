import pytest

from etl.quality import DataQualityError, enforce, run_checks
from etl.transform import transform


def test_clean_data_passes_blocking_checks(payloads):
    results = enforce(transform(payloads))
    completeness = next(r for r in results if r.name.startswith("completeness"))
    assert not completeness.passed and not completeness.blocking


def test_min_greater_than_max_fails(payloads):
    df = transform(payloads)
    df.loc[0, "temp_min_c"] = df.loc[0, "temp_max_c"] + 5
    with pytest.raises(DataQualityError, match="temp_min_c <= temp_max_c"):
        enforce(df)


def test_out_of_range_detected(payloads):
    df = transform(payloads)
    df.loc[1, "temp_max_c"] = 75
    failed = [r.name for r in run_checks(df) if not r.passed]
    assert "range:temp_max_c between -60 and 60" in failed
