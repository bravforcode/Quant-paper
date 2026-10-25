from __future__ import annotations

import pytest
from research.cpiv.measurement.errors import ReconciliationError
from research.cpiv.measurement.status import (
    PairRecord,
    ReasonCode,
    Stage,
    TerminalStatus,
    funnel,
    reconcile,
)


def _resolved(pair_id: str) -> PairRecord:
    return PairRecord(
        pair_id=pair_id, terminal=TerminalStatus.RESOLVED_WITHIN_TOLERANCE
    )


def test_terminal_status_must_match_the_failed_stage() -> None:
    with pytest.raises(ReconciliationError, match="not allowed"):
        PairRecord(
            pair_id="p1",
            terminal=TerminalStatus.RESOLVED_WITHIN_TOLERANCE,
            failed_stage=Stage.TIMING,
        )


def test_reached_stages_must_be_a_prefix_of_the_pipeline() -> None:
    with pytest.raises(ReconciliationError, match="do not match"):
        PairRecord(
            pair_id="p1",
            terminal=TerminalStatus.TIMING_MISMATCH,
            failed_stage=Stage.TIMING,
            reached=(Stage.CONTRACT, Stage.TIMING),
        )


def test_reconcile_counts_every_terminal_once() -> None:
    records = [
        _resolved("p1"),
        PairRecord(
            pair_id="p2",
            terminal=TerminalStatus.TIMING_MISMATCH,
            failed_stage=Stage.TIMING,
        ),
        PairRecord(
            pair_id="p3",
            terminal=TerminalStatus.UNRESOLVED,
            failed_stage=Stage.TIME_VALUE,
            reason=ReasonCode.TIME_VALUE_BELOW_SCALE,
        ),
    ]
    summary = reconcile(records)
    assert summary["attempted"] == 3
    assert summary["terminal_counts"][TerminalStatus.UNRESOLVED.value] == 1
    assert summary["stage_counts"][Stage.CONTRACT.value] == 3
    assert summary["stage_counts"][Stage.TIME_VALUE.value] == 1
    assert summary["stage_counts"][Stage.TOLERANCE.value] == 1


def test_a_missing_record_fails_reconciliation() -> None:
    records = [_resolved("p1")]
    with pytest.raises(ReconciliationError, match="attempted 2 pairs"):
        reconcile(records, attempted=2)


def test_funnel_reports_shares_and_the_dominant_reason() -> None:
    records = [
        _resolved("p1"),
        PairRecord(
            pair_id="p2",
            terminal=TerminalStatus.TIMING_MISMATCH,
            failed_stage=Stage.TIMING,
        ),
        PairRecord(
            pair_id="p3",
            terminal=TerminalStatus.UNRESOLVED,
            failed_stage=Stage.TIME_VALUE,
            reason=ReasonCode.TIME_VALUE_BELOW_SCALE,
        ),
    ]
    rows = {row.stage: row for row in funnel(records)}
    assert rows[Stage.CONTRACT].count == 3
    assert rows[Stage.TIMING].count == 2
    assert rows[Stage.TIMING].share_of_attempted == pytest.approx(2 / 3)
    assert rows[Stage.TIMING].share_of_prior == pytest.approx(2 / 3)
    assert rows[Stage.TIME_VALUE].count == 1
    assert (
        rows[Stage.TIME_VALUE].dominant_rejection_reason
        == ReasonCode.TIME_VALUE_BELOW_SCALE.value
    )


def test_funnel_fails_when_a_pair_is_silently_dropped() -> None:
    records = [_resolved("p1")]
    with pytest.raises(ReconciliationError):
        funnel(records, attempted=3)
