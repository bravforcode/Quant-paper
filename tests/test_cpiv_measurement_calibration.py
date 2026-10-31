from __future__ import annotations

import pytest
from research.cpiv.measurement.calibration import (
    SURFACE_FIT_DESCRIPTION,
    compare_surfaces,
    fit_quadratic,
)


def test_a_quadratic_is_recovered_exactly() -> None:
    points = [(x / 10.0, 1.0 + 2.0 * x / 10.0 + 3.0 * (x / 10.0) ** 2) for x in range(-5, 6)]
    fit = fit_quadratic("30d", points)
    assert fit is not None
    assert fit.contracts == len(points)
    for x, y in points:
        assert fit.evaluate(x) == pytest.approx(y, abs=1e-8)


def test_too_few_points_produce_no_fit() -> None:
    assert fit_quadratic("30d", [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]) is None


def test_degenerate_points_produce_no_fit() -> None:
    assert fit_quadratic("30d", [(1.0, 1.0)] * 6) is None


def test_the_comparison_reports_contracts_forgone_and_a_surface_change() -> None:
    log_moneyness = {f"p{i}": (i - 5) / 10.0 for i in range(12)}
    slice_key = {f"p{i}": "30d" for i in range(12)}
    raw = {f"p{i}": 1.0 + 2.0 * log_moneyness[f"p{i}"] for i in range(12)}
    protocol = {f"p{i}": raw[f"p{i}"] + 0.25 for i in range(6)}
    report = compare_surfaces(raw, protocol, log_moneyness, slice_key)
    assert report["fit"] == SURFACE_FIT_DESCRIPTION
    assert report["raw_contracts"] == 12
    assert report["protocol_contracts"] == 6
    assert report["contracts_forgone"] == 6
    assert report["coverage_retained"] == pytest.approx(0.5)
    assert float(report["max_slice_surface_change_pp"]) == pytest.approx(0.25, abs=1e-6)


def test_the_comparison_ignores_slices_the_protocol_emptied() -> None:
    log_moneyness = {
        "a": -0.2, "b": -0.1, "c": 0.0, "d": 0.1,
        "e": -0.2, "f": -0.1, "g": 0.0, "h": 0.1,
    }
    slice_key = {
        "a": "14d", "b": "14d", "c": "14d", "d": "14d",
        "e": "60d", "f": "60d", "g": "60d", "h": "60d",
    }
    raw = {key: 0.5 for key in log_moneyness}
    protocol = {key: 0.5 for key in ("a", "b", "c", "d")}
    report = compare_surfaces(raw, protocol, log_moneyness, slice_key)
    slices = report["slices"]
    assert isinstance(slices, list)
    assert [row["slice"] for row in slices] == ["14d"]
