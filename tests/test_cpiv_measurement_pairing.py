from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from research.cpiv.measurement.analysis import (
    bound_filtered_values,
    compare,
    coverage,
    input_sensitivity,
    pairwise_inversion_rate,
    raw_midpoint_values,
    sign_disagreement,
    spearman,
    tail_turnover,
)
from research.cpiv.measurement.pairing import Contract, Quote, check_pair
from research.cpiv.measurement.resolution import ResolutionOutcome
from research.cpiv.measurement.status import (
    ReasonCode,
    Stage,
    TerminalStatus,
)

STAMP = datetime(2026, 1, 5, 15, 30, tzinfo=UTC)
TERMS = Contract(
    underlying="SPX",
    strike=5000.0,
    expiry=date(2026, 2, 20),
    multiplier=100,
    exercise_style="european",
    settlement="cash",
)


def _quote(bid: float, ask: float, lag: float = 0.0) -> Quote:
    return Quote(bid=bid, ask=ask, timestamp_utc=STAMP.replace(second=int(lag)))


def test_matched_pair_records_all_three_lags() -> None:
    check = check_pair(
        _quote(10.0, 10.2, lag=0.0),
        _quote(9.0, 9.2, lag=2.0),
        5000.0,
        STAMP,
        TERMS,
        TERMS,
        tolerance_seconds=5.0,
    )
    assert check.ok
    assert check.lags_seconds["call_put"] == pytest.approx(2.0)
    assert check.lags_seconds["call_spot"] == pytest.approx(0.0)
    assert check.lags_seconds["put_spot"] == pytest.approx(2.0)


def test_strike_mismatch_is_a_contract_mismatch() -> None:
    other = Contract(**{**TERMS.__dict__, "strike": 5050.0})
    check = check_pair(
        _quote(10.0, 10.2), _quote(9.0, 9.2), 5000.0, STAMP, TERMS, other, 5.0
    )
    assert not check.ok
    assert check.terminal is TerminalStatus.CONTRACT_MISMATCH
    assert check.failed_stage is Stage.CONTRACT
    assert check.detail == "strike"


def test_lag_beyond_tolerance_keeps_the_lags() -> None:
    check = check_pair(
        _quote(10.0, 10.2),
        _quote(9.0, 9.2, lag=7.0),
        5000.0,
        STAMP,
        TERMS,
        TERMS,
        tolerance_seconds=5.0,
    )
    assert not check.ok
    assert check.terminal is TerminalStatus.TIMING_MISMATCH
    assert check.lags_seconds["call_put"] == pytest.approx(7.0)


def test_mixed_timezone_conventions_are_a_timing_mismatch() -> None:
    naive = Quote(bid=1.0, ask=1.1, timestamp_utc=datetime(2026, 1, 5, 15, 30))
    check = check_pair(
        _quote(10.0, 10.2), naive, 5000.0, STAMP, TERMS, TERMS, 5.0
    )
    assert not check.ok
    assert check.terminal is TerminalStatus.TIMING_MISMATCH


def test_crossed_quote_is_invalid_input() -> None:
    check = check_pair(
        _quote(10.2, 10.0), _quote(9.0, 9.2), 5000.0, STAMP, TERMS, TERMS, 5.0
    )
    assert not check.ok
    assert check.terminal is TerminalStatus.INVALID_INPUT
    assert check.reason is ReasonCode.QUOTE_INVALID


def test_spearman_detects_monotone_and_reversed_orders() -> None:
    left = {"a": 1.0, "b": 2.0, "c": 3.0}
    assert spearman(left, {"a": 2.0, "b": 4.0, "c": 9.0}) == pytest.approx(1.0)
    assert spearman(left, {"a": 9.0, "b": 4.0, "c": 2.0}) == pytest.approx(-1.0)


def test_sign_disagreement_uses_only_opposite_non_zero_signs() -> None:
    first = {"a": 1.0, "b": -1.0, "c": 2.0, "d": 0.0}
    second = {"a": 2.0, "b": -2.0, "c": -3.0, "d": 1.0}
    assert sign_disagreement(first, second) == pytest.approx(1 / 4)


def test_pairwise_inversion_rate_counts_reversals() -> None:
    first = {"a": 1.0, "b": 2.0, "c": 3.0}
    second = {"a": 3.0, "b": 2.0, "c": 1.0}
    assert pairwise_inversion_rate(first, second) == pytest.approx(1.0)


def test_tail_turnover_counts_membership_change() -> None:
    first = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0}
    second = {"a": 4.0, "b": 3.0, "c": 2.0, "d": 1.0}
    assert tail_turnover(first, second, fraction=0.25) == pytest.approx(1.0)


def test_coverage_and_own_common_set_comparison_labels() -> None:
    outcomes = [
        ResolutionOutcome(
            pair_id="a",
            terminal=TerminalStatus.RESOLVED_WITHIN_TOLERANCE,
            failed_stage=None,
            reason=ReasonCode.NONE,
            cpiv_mid_pp=1.0,
            mid_inside_bounds=True,
        ),
        ResolutionOutcome(
            pair_id="b",
            terminal=TerminalStatus.UNRESOLVED,
            failed_stage=Stage.TIME_VALUE,
            reason=ReasonCode.TIME_VALUE_BELOW_SCALE,
            cpiv_mid_pp=2.0,
            mid_inside_bounds=True,
        ),
        ResolutionOutcome(
            pair_id="c",
            terminal=TerminalStatus.RESOLVED_WITHIN_TOLERANCE,
            failed_stage=None,
            reason=ReasonCode.NONE,
            cpiv_mid_pp=3.0,
            mid_inside_bounds=False,
        ),
    ]
    assert coverage(outcomes) == pytest.approx(2 / 3)
    assert raw_midpoint_values(outcomes) == {"a": 1.0, "b": 2.0, "c": 3.0}
    assert bound_filtered_values(outcomes) == {"a": 1.0, "b": 2.0}
    result = compare(raw_midpoint_values(outcomes), {"a": 1.0, "b": 2.0})
    assert set(result) == {"own_set", "common_set", "labels"}
    assert result["own_set"] == {"baseline_n": 3, "protocol_n": 2}
    assert result["common_set"]["n"] == 2
    assert "algebraically dependent" in result["labels"]["parity_residual"]


def test_input_sensitivity_is_mean_absolute_change() -> None:
    base = {"a": 1.0, "b": 2.0}
    perturbed = {"a": 1.5, "b": 2.0}
    assert input_sensitivity(base, perturbed) == pytest.approx(0.25)
