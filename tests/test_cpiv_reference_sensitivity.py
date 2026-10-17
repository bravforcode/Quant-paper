from __future__ import annotations

import pytest
from research.cpiv import build_demo as demo
from research.cpiv.reference_sensitivity import analyze_rows


def _synthetic_rows(reference_iv: float = 0.10) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    spot = strike = 100.0
    days = 30
    rate = yield_ = 0.0
    for spread_pp in (-2.0, -1.0, -0.5, 0.5, 1.0, 2.0):
        call_iv = reference_iv + spread_pp / 200.0
        put_iv = reference_iv - spread_pp / 200.0
        call = demo.bs_price("call", spot, strike, days, rate, yield_, call_iv)
        put = demo.bs_price("put", spot, strike, days, rate, yield_, put_iv)
        residual = demo.parity_residual(call, put, spot, strike, days, rate, yield_)
        vega = 100.0 * demo.bs_vega_per_vol_point(
            spot, strike, days, rate, yield_, reference_iv
        )
        approximation = 100.0 * residual / vega
        rows.append(
            {
                "spot_strike_ratio": 1.0,
                "spot_usd": spot,
                "strike_usd": strike,
                "days_to_expiry": days,
                "reference_iv_decimal": reference_iv,
                "target_cpiv_pp": spread_pp,
                "rate": rate,
                "effective_yield": yield_,
                "integrated_vega_residual_usd": residual,
                "vega_midpoint_usd_per_decimal_iv": vega,
                "legacy_absolute_vega_guard_usd_per_decimal_iv": 1e-6,
                "local_approximation_pp": approximation,
                "absolute_error_midpoint_pp": abs(approximation - spread_pp),
            }
        )
    return rows


def test_symmetric_midpoint_grid_has_cubic_error_scaling() -> None:
    summary = analyze_rows(_synthetic_rows())
    spread_rows = summary["d_cubic_diagnostic"]["error_by_absolute_target_spread"]

    assert [row["absolute_target_spread_pp"] for row in spread_rows] == [0.5, 1.0, 2.0]
    assert spread_rows[1]["median_growth_vs_previous_spread"] == pytest.approx(8.0, rel=1e-4)
    assert spread_rows[2]["median_growth_vs_previous_spread"] == pytest.approx(8.0, rel=1e-3)
    assert (
        summary["d_cubic_diagnostic"]["per_configuration_log_log_slope"]["median"]
        == pytest.approx(3.0, abs=1e-4)
    )


def test_off_centre_offsets_are_signed_and_nonpositive_reference_is_skipped() -> None:
    summary = analyze_rows(_synthetic_rows(reference_iv=0.10))
    rows = summary["off_centre_reference"]["summaries"]
    by_offset = {row["absolute_reference_offset_vol_points"]: row for row in rows}

    assert by_offset[0.0]["n"] == 6
    assert by_offset[1.0]["n"] == 12
    assert by_offset[1.0]["signed_offsets_evaluated_vol_points"] == [-1.0, 1.0]
    assert by_offset[10.0]["n"] == 6
    assert by_offset[10.0]["skipped_nonpositive_reference_count"] == 6
    assert summary["market_data_used"] is False


def test_unresolved_grid_cells_do_not_enter_reference_summaries() -> None:
    rows = _synthetic_rows()
    rows[0]["vega_midpoint_usd_per_decimal_iv"] = 1e-9
    rows[0]["local_approximation_pp"] = ""
    summary = analyze_rows(rows)

    assert summary["grid"]["cell_n"] == 6
    assert summary["grid"]["baseline_guard_passing_n"] == 5
    assert summary["grid"]["baseline_guard_failing_n"] == 1
    assert summary["off_centre_reference"]["summaries"][0]["n"] == 5
