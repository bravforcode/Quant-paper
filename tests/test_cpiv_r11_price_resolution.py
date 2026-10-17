from __future__ import annotations

import csv
import json
import math

import pytest
from research.cpiv import r11_near_bound_audit as boundary_audit
from research.cpiv import r11_price_resolution as r11


def test_review_example_cells_reproduce_with_explicit_units() -> None:
    rows = r11.review_example_cells()
    assert len(rows) == 4
    by_key = {(row["example"], row["option_type"]): row for row in rows}

    atm = by_key[("ATM_30d_iv20", "call")]
    assert math.isclose(atm["vega_currency_per_iv_pp"], 0.11432620400510857)
    assert math.isclose(atm["local_delta_iv_pp"], 0.08746901103751471)
    assert math.isclose(atm["roundoff_delta_iv_pp"], 2.221054490646736e-15)
    assert atm["legacy_absolute_vega_guard_pass"] is True
    assert atm["exact_up_status"] == "inverted"
    assert atm["exact_down_status"] == "inverted"
    assert math.isclose(atm["exact_up_to_local_abs_ratio"], 1.000001799933561)
    assert math.isclose(atm["exact_down_to_local_abs_ratio"], 0.9999982053157599)
    assert atm["finite_shock_status"] == "both_directions_invertible"
    assert atm["otm_equivalent_time_value_below_tick"] is False
    assert atm["identification_status"] == "identified"
    assert atm["within_iv_tolerance"] is True
    assert atm["iv_tolerance_status"] == "within_tau_iv"
    assert math.isclose(atm["iv_tolerance_pp"], 0.10)
    assert math.isclose(atm["max_abs_finite_iv_shift_pp"], 0.0874691685, rel_tol=1e-6)
    tighter = next(
        row
        for row in r11.review_example_cells(iv_tolerance_pp=0.05)
        if row["example"] == "ATM_30d_iv20" and row["option_type"] == "call"
    )
    assert tighter["identification_status"] == "identified"
    assert tighter["within_iv_tolerance"] is False
    assert tighter["iv_tolerance_status"] == "outside_tau_iv"

    half_tick_atm = next(
        row
        for row in r11.review_example_half_tick_cells(iv_tolerance_pp=0.05)
        if row["example"] == "ATM_30d_iv20" and row["option_type"] == "call"
    )
    assert math.isclose(half_tick_atm["price_perturbation_absolute"], 0.005)
    assert math.isclose(half_tick_atm["max_abs_finite_iv_shift_pp"], 0.0437346, rel_tol=1e-5)
    assert half_tick_atm["otm_equivalent_time_value_below_tick"] is False
    assert half_tick_atm["within_iv_tolerance"] is True

    weak_vega = by_key[("spot_ratio_0.8_90d_iv10", "call")]
    assert math.isclose(weak_vega["vega_currency_per_iv_pp"], 7.298911863095962e-6)
    assert math.isclose(weak_vega["local_delta_iv_pp"], 1370.0672357150952)
    assert math.isclose(weak_vega["roundoff_delta_iv_pp"], 4.8339680388723964e-17)
    assert weak_vega["legacy_absolute_vega_guard_pass"] is True
    assert math.isclose(weak_vega["exact_up_delta_iv_pp"], 7.071712574925412)
    assert math.isclose(weak_vega["exact_up_to_local_abs_ratio"], 0.005161580680552798)
    assert weak_vega["exact_down_status"] == "not_invertible_under_configured_bounds"
    assert weak_vega["exact_down_to_local_abs_ratio"] is None
    assert weak_vega["finite_shock_status"] == "up_only_invertible"
    assert weak_vega["otm_equivalent_time_value_below_tick"] is True
    assert weak_vega["identification_status"] == "unresolved_otm_equivalent_below_tick"
    assert weak_vega["within_iv_tolerance"] is False
    assert weak_vega["iv_tolerance_status"] == "unresolved_not_qualified"

    weak_put = by_key[("spot_ratio_0.8_90d_iv10", "put")]
    assert math.isclose(weak_put["roundoff_delta_iv_pp"], 3.0421608641476835e-10)
    assert weak_put["exact_down_status"] == "not_invertible_under_configured_bounds"
    assert math.isclose(
        weak_put["otm_equivalent_time_value_price_units"],
        weak_vega["otm_equivalent_time_value_price_units"],
        rel_tol=1e-8,
    )
    assert weak_put["otm_equivalent_time_value_below_tick"] is True
    assert weak_put["identification_status"] == "unresolved_otm_equivalent_below_tick"
    assert weak_put["within_iv_tolerance"] is False
    assert weak_put["iv_tolerance_status"] == "unresolved_not_qualified"


def test_grid_keeps_tick_spread_and_roundoff_as_distinct_sources() -> None:
    rows = r11.price_resolution_grid(tick_values=(0.001, 0.01), quote_half_spreads=(0.02,))
    assert len(rows) == 120 * 2 * 4
    assert {row["price_perturbation_source"] for row in rows} == {
        "one_full_price_tick",
        "quote_half_spread",
        "floating_point_roundoff_scale",
    }
    config = next(
        row
        for row in rows
        if row["spot_strike_ratio"] == 1.0
        and row["days_to_expiry"] == 30.0
        and row["reference_iv_decimal"] == 0.20
        and row["rate"] == 0.0
        and row["option_type"] == "call"
        and row["price_perturbation_source"] == "one_full_price_tick"
        and row["source_parameter"] == 0.01
    )
    assert math.isclose(
        config["local_delta_iv_pp"],
        config["price_perturbation_absolute"] / config["vega_currency_per_iv_pp"],
    )
    assert config["sensitivity_scope"] == ("local derivative; not a finite uncertainty interval")
    assert config["market_data_used"] is False

    sub_tick_spread = next(
        row
        for row in rows
        if row["spot_strike_ratio"] == 0.8
        and row["days_to_expiry"] == 90.0
        and row["reference_iv_decimal"] == 0.10
        and row["option_type"] == "call"
        and row["price_perturbation_source"] == "quote_half_spread"
        and row["source_parameter"] == 0.02
    )
    assert sub_tick_spread["tick_reference_price_units"] == 0.01
    assert sub_tick_spread["otm_equivalent_time_value_below_tick"] is True
    assert sub_tick_spread["identification_status"] == "unresolved_otm_equivalent_below_tick"

    sub_tick_roundoff = next(
        row
        for row in rows
        if row["spot_strike_ratio"] == 0.8
        and row["days_to_expiry"] == 90.0
        and row["reference_iv_decimal"] == 0.10
        and row["option_type"] == "call"
        and row["price_perturbation_source"] == "floating_point_roundoff_scale"
    )
    assert sub_tick_roundoff["otm_equivalent_time_value_below_tick"] is True
    assert sub_tick_roundoff["identification_status"] == "local_only_roundoff"
    assert sub_tick_roundoff["iv_tolerance_status"] == "not_assessed_local_only"


def test_sub_tick_quote_examples_show_midpoint_ask_and_unresolved_zero_bid() -> None:
    rows = r11.premium_below_tick_quote_examples()
    by_scenario = {row["scenario"]: row for row in rows}
    assert by_scenario["zero_bid"]["status"] == "no_interior_root_at_lower_bound"
    assert by_scenario["zero_to_one_tick_midpoint"]["status"] == "inverted"
    assert math.isclose(
        by_scenario["zero_to_one_tick_midpoint"]["implied_iv_percent"], 15.925481423073318
    )
    assert by_scenario["one_tick_ask"]["status"] == "inverted"
    assert math.isclose(by_scenario["one_tick_ask"]["implied_iv_percent"], 17.071138781027507)
    assert all(row["synthetic_otm_call_premium_below_tick"] for row in rows)
    assert all(row["market_data_used"] is False for row in rows)


@pytest.mark.parametrize(
    ("ticks", "spreads", "roundoff"),
    [
        ((0.0,), (0.01,), r11.UNIT_ROUNDOFF),
        ((0.01,), (-0.1,), r11.UNIT_ROUNDOFF),
        ((0.01, 0.01), (0.1,), r11.UNIT_ROUNDOFF),
        ((0.01,), (0.1,), math.nan),
        ((math.inf,), (0.1,), r11.UNIT_ROUNDOFF),
    ],
)
def test_invalid_resolution_parameters_are_rejected(
    ticks: tuple[float, ...], spreads: tuple[float, ...], roundoff: float
) -> None:
    with pytest.raises(ValueError):
        r11.price_resolution_grid(ticks, spreads, roundoff)


@pytest.mark.parametrize("tolerance", [-0.01, math.nan, math.inf])
def test_invalid_iv_tolerance_is_rejected(tolerance: float) -> None:
    with pytest.raises(ValueError, match="iv_tolerance_pp"):
        r11.price_resolution_grid(iv_tolerance_pp=tolerance)


def test_float_bound_classification_checks_violation_before_near_guard() -> None:
    classify = boundary_audit.classify_float_price
    assert classify(-1e-12, 0.0, 10.0) == "strict_bound_violation"
    assert classify(0.0, 0.0, 10.0) == "exact_bound_guard"
    assert classify(5e-11, 0.0, 10.0) == "interior_near_bound_guard"
    assert classify(1e-5, 0.0, 10.0) == "not_near_bound"


def test_bound_audit_replays_three_groups_from_inversion_csv(tmp_path) -> None:
    from research.cpiv import build_demo as demo

    lower, _ = demo.price_bounds("call", 100.0, 100.0, 30, 0.03, 0.01)
    rows = [
        (lower, "rejected_by_configured_absolute_near_bound_guard"),
        (lower + 5e-11, "rejected_by_configured_absolute_near_bound_guard"),
        (lower - 1e-9, "theoretical_bound_violation"),
    ]
    source_path = tmp_path / "inversion.csv"
    with source_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "status",
                "failure_status",
                "option_type",
                "spot_strike_ratio",
                "days_to_expiry",
                "target_iv",
                "theoretical_price_usd",
            ],
        )
        writer.writeheader()
        for price, status in rows:
            writer.writerow(
                {
                    "status": status,
                    "failure_status": status,
                    "option_type": "call",
                    "spot_strike_ratio": 1.0,
                    "days_to_expiry": 30,
                    "target_iv": 0.2,
                    "theoretical_price_usd": price,
                }
            )

    audited, summary = boundary_audit.audit_rejected_prices(source_path)
    assert summary["group_counts"] == {
        "exact_bound_guard": 1,
        "interior_near_bound_guard": 1,
        "strict_bound_violation": 1,
    }
    assert summary["guard_rejection_count"] == 2
    assert summary["strict_bound_violation_count"] == 1
    assert len(audited) == 3


def test_output_bundle_contains_machine_readable_grid_and_heatmap(tmp_path) -> None:
    summary = r11.write_r11_outputs(tmp_path, tick_values=(0.01,), quote_half_spreads=(0.01,))
    assert summary["market_data_used"] is False
    assert summary["configuration_count"] == 120
    assert summary["leg_source_parameter_rows"] == 720
    assert summary["rows_by_source"] == {
        "one_full_price_tick": 240,
        "quote_half_spread": 240,
        "floating_point_roundoff_scale": 240,
    }
    with (tmp_path / "cpiv_r11_price_resolution.csv").open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 720
    written = json.loads((tmp_path / "cpiv_r11_price_resolution.json").read_text(encoding="utf-8"))
    assert "full-tick sensitivity" in written["tick_interpretation"]
    assert "±t/2" in written["tick_interpretation"]
    assert written["iv_tolerance_pp"] == 0.1
    assert "maximum worst-direction absolute IV displacement" in written["iv_tolerance_rule"]
    assert written["heatmap_display"]["days_to_expiry"] == [30, 90]
    assert written["heatmap_display"]["reference_iv_decimals"] == [0.10, 0.20]
    assert (
        written["heatmap_display"]["spread_panel_otm_equivalent_time_value_tick_reference"]
        == 0.01
    )
    assert written["heatmap_display"]["finite_shock_bands_pp"][-1] == "unresolved"
    assert set(written["identification_status_counts"]) == {
        "identified",
        "unresolved_otm_equivalent_below_tick",
        "unresolved_shock_no_root",
        "local_only_roundoff",
    }
    assert set(written["iv_tolerance_status_counts"]) == {
        "within_tau_iv",
        "outside_tau_iv",
        "unresolved_not_qualified",
        "not_assessed_local_only",
    }
    assert (tmp_path / "cpiv_r11_sub_tick_quote_examples.csv").stat().st_size > 100
    assert (tmp_path / "cpiv_r11_nearest_tick_rounding_examples.csv").stat().st_size > 100
    assert (tmp_path / "cpiv_r11_price_resolution_status_heatmap.png").stat().st_size > 1000
    assert (tmp_path / "cpiv_r11_price_resolution_status_heatmap.svg").stat().st_size > 1000
    assert (tmp_path / "cpiv_r11_finite_shock_change_heatmap.png").stat().st_size > 1000
    assert (tmp_path / "cpiv_r11_finite_shock_change_heatmap.svg").stat().st_size > 1000
