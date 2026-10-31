from __future__ import annotations

import math

import pytest
from research.cpiv.measurement import synthetic
from research.cpiv.measurement.inversion import (
    IV_HIGH,
    FailureClass,
    classify_failure,
    invert_leg,
    round_trip_summary,
)
from research.cpiv.measurement.resolution import ResolutionInput, resolve
from research.cpiv.measurement.status import ReasonCode, Stage, TerminalStatus


def test_solver_grid_replays_the_published_counts() -> None:
    summary = round_trip_summary()
    assert summary["contract_configurations"] == 60
    assert summary["option_leg_prices"] == 120
    assert summary["inverted"] == 104
    assert summary["rejected"] == 16
    assert summary["failures_by_class"] == {
        "near_bound_guard": 15,
        "theoretical_bound_violation": 1,
    }
    assert summary["max_repricing_error_usd"] < 1e-12


def test_repricing_and_recovery_errors_are_separate_fields() -> None:
    outcome = invert_leg(
        "call", 2.0, 100.0, 100.0, 30, 0.03, 0.01, target_iv=0.2
    )
    assert outcome.ok
    assert outcome.repricing_error is not None
    assert outcome.iv_recovery_error is not None
    assert outcome.repricing_error != outcome.iv_recovery_error
    assert outcome.vega is not None and outcome.vega > 0.0


def test_non_finite_and_negative_prices_are_invalid_input() -> None:
    assert (
        classify_failure("call", math.nan, 100.0, 100.0, 30, 0.0, 0.0)
        is FailureClass.INVALID_INPUT
    )
    assert (
        classify_failure("call", -1.0, 100.0, 100.0, 30, 0.0, 0.0)
        is FailureClass.INVALID_INPUT
    )


def test_exact_bound_is_classified_as_the_guard() -> None:
    assert (
        classify_failure("put", 0.0, 100.0, 100.0, 30, 0.0, 0.0)
        is FailureClass.NEAR_BOUND_GUARD
    )


def test_price_above_the_configured_bracket_is_classified() -> None:
    assert IV_HIGH == 5.0
    assert (
        classify_failure("put", 90.0, 100.0, 100.0, 30, 0.0, 0.0)
        is FailureClass.OUTSIDE_BRACKET
    )


def test_invert_leg_reports_failure_without_raising() -> None:
    outcome = invert_leg("put", 0.0, 100.0, 100.0, 30, 0.0, 0.0)
    assert not outcome.ok
    assert outcome.iv is None
    assert outcome.failure is FailureClass.NEAR_BOUND_GUARD


def test_identity_fixture_matches_the_integral_identity() -> None:
    case = synthetic.load_cases()["identity"]
    result = synthetic.identity_check(case)
    assert result["identity_error_usd"] < 1e-10
    assert result["local_error_pp"] == pytest.approx(0.0, abs=1e-9)
    assert result["exact_cpiv_pp"] == pytest.approx(4.0)


def test_tick_convention_changes_resolution_but_not_the_pair() -> None:
    case = synthetic.load_cases()["tick_convention"]
    tick = case["tick"]
    full = synthetic.run_case(case, "full", tick)
    half = synthetic.run_case(case, "half", tick / 2.0)
    assert full.terminal is TerminalStatus.UNRESOLVED
    assert full.failed_stage is Stage.TIME_VALUE
    assert full.reason is ReasonCode.TIME_VALUE_BELOW_SCALE
    assert half.terminal is TerminalStatus.IDENTIFIED_OUTSIDE_TOLERANCE
    assert half.cpiv_mid_pp == pytest.approx(full.cpiv_mid_pp)


def test_deep_otm_pair_passes_vega_but_fails_the_time_value_scale() -> None:
    case = synthetic.load_cases()["deep_otm"]
    outcome = synthetic.run_case(case, "deep", case["tick"])
    assert outcome.terminal is TerminalStatus.UNRESOLVED
    assert outcome.reason is ReasonCode.TIME_VALUE_BELOW_SCALE
    assert outcome.otm_time_value is not None
    assert outcome.otm_time_value < case["tick"]
    assert outcome.otm_vega is not None
    assert outcome.otm_vega > 1e-6
    assert outcome.cpiv_mid_pp is not None


def test_missing_endpoint_becomes_a_one_sided_bound() -> None:
    spec = ResolutionInput(
        pair_id="partial",
        call_mid=2.087,
        put_mid=0.025,
        call_bid=2.077,
        call_ask=2.097,
        put_bid=0.0,
        put_ask=0.05,
        spot=100.0,
        strike=100.0,
        days=30,
    )
    outcome = resolve(spec)
    assert outcome.terminal is TerminalStatus.PARTIALLY_RESOLVED
    assert outcome.failed_stage is Stage.ENDPOINT
    assert outcome.interval_low_pp is not None
    assert outcome.interval_high_pp is None


def test_no_invertible_endpoint_is_unresolved() -> None:
    spec = ResolutionInput(
        pair_id="no-endpoints",
        call_mid=2.087,
        put_mid=2.087,
        call_bid=2.077,
        call_ask=2.097,
        put_bid=1000.0,
        put_ask=1000.0,
        spot=100.0,
        strike=100.0,
        days=30,
    )
    outcome = resolve(spec)
    assert outcome.terminal is TerminalStatus.UNRESOLVED
    assert outcome.reason is ReasonCode.ENDPOINT_INCOMPLETE


def test_narrow_spread_resolves_within_tolerance() -> None:
    spec = ResolutionInput(
        pair_id="narrow",
        call_mid=2.5945715308485694,
        put_mid=1.974094354530422,
        call_bid=2.5935715308485694,
        call_ask=2.5955715308485694,
        put_bid=1.973094354530422,
        put_ask=1.975094354530422,
        spot=100.0,
        strike=100.0,
        days=30,
        rate=0.03,
        dividend_yield=0.01,
        tick=0.01,
    )
    outcome = resolve(spec)
    assert outcome.terminal is TerminalStatus.RESOLVED_WITHIN_TOLERANCE
    assert outcome.displacement_pp is not None
    assert outcome.displacement_pp <= 0.10
