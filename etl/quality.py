"""Lightweight data-quality framework. Each check returns a result object;
the pipeline fails fast if any *blocking* check fails."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class CheckResult:
    name: str
    passed: bool
    failing_rows: int
    blocking: bool = True

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name} (failing rows: {self.failing_rows})"


class DataQualityError(Exception):
    pass


def _result(name: str, mask: pd.Series, blocking: bool = True) -> CheckResult:
    n = int(mask.sum())
    return CheckResult(name, n == 0, n, blocking)


def run_checks(df: pd.DataFrame) -> list[CheckResult]:
    return [
        _result("not_null:city,obs_date", df[["city", "obs_date"]].isna().any(axis=1)),
        _result("unique:city+obs_date", df.duplicated(["city", "obs_date"])),
        _result("range:temp_max_c between -60 and 60",
                ~df["temp_max_c"].between(-60, 60) & df["temp_max_c"].notna()),
        _result("logic:temp_min_c <= temp_max_c",
                df["temp_min_c"] > df["temp_max_c"]),
        _result("range:precipitation_mm >= 0", df["precipitation_mm"] < 0),
        # Missing temperatures are tolerated (API gaps) but reported.
        _result("completeness:temp_max_c", df["temp_max_c"].isna(), blocking=False),
    ]


def enforce(df: pd.DataFrame) -> list[CheckResult]:
    results = run_checks(df)
    failures = [r for r in results if r.blocking and not r.passed]
    if failures:
        raise DataQualityError("; ".join(str(f) for f in failures))
    return results
