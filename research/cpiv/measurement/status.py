"""Terminal statuses, reason codes, and count reconciliation for CPIV pairs.

Every attempted pair carries exactly one terminal status. A reason code names
the cause but never replaces the status: "unresolved" is not zero, not bad data,
and not an implicit abstention that an analysis may ignore.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from research.cpiv.measurement.errors import ReconciliationError


class Stage(StrEnum):
    """Ordered pipeline stages; a pair passes them in this order."""

    CONTRACT = "contract"
    TIMING = "timing"
    QUOTE = "quote"
    INPUT = "input"
    MIDPOINT = "midpoint"
    ENDPOINT = "endpoint"
    TIME_VALUE = "time_value"
    FINITE_SHOCK = "finite_shock"
    TOLERANCE = "tolerance"


STAGE_ORDER: tuple[Stage, ...] = tuple(Stage)


class TerminalStatus(StrEnum):
    """The seven declared terminal statuses."""

    RESOLVED_WITHIN_TOLERANCE = "resolved_within_tolerance"
    IDENTIFIED_OUTSIDE_TOLERANCE = "identified_outside_tolerance"
    PARTIALLY_RESOLVED = "partially_resolved"
    UNRESOLVED = "unresolved"
    INVALID_INPUT = "invalid_input"
    TIMING_MISMATCH = "timing_mismatch"
    CONTRACT_MISMATCH = "contract_mismatch"


class ReasonCode(StrEnum):
    """Cause of a terminal status, stored separately from the status."""

    NONE = "none"
    QUOTE_INVALID = "quote_invalid"
    INPUT_INCOMPLETE = "input_incomplete"
    THEORETICAL_BOUND_VIOLATION = "theoretical_bound_violation"
    NEAR_BOUND_GUARD = "near_bound_guard"
    OUTSIDE_BRACKET = "outside_bracket"
    NUMERICAL_FAILURE = "numerical_failure"
    ENDPOINT_INCOMPLETE = "endpoint_incomplete"
    TIME_VALUE_BELOW_SCALE = "time_value_below_scale"
    FINITE_SHOCK_ABSENT = "finite_shock_absent"
    TOLERANCE_EXCEEDED = "tolerance_exceeded"


_ALLOWED_TERMINALS: dict[Stage | None, frozenset[TerminalStatus]] = {
    Stage.CONTRACT: frozenset({TerminalStatus.CONTRACT_MISMATCH}),
    Stage.TIMING: frozenset({TerminalStatus.TIMING_MISMATCH}),
    Stage.QUOTE: frozenset({TerminalStatus.INVALID_INPUT}),
    Stage.INPUT: frozenset({TerminalStatus.INVALID_INPUT}),
    Stage.MIDPOINT: frozenset(
        {TerminalStatus.UNRESOLVED, TerminalStatus.INVALID_INPUT}
    ),
    Stage.ENDPOINT: frozenset(
        {TerminalStatus.PARTIALLY_RESOLVED, TerminalStatus.UNRESOLVED}
    ),
    Stage.TIME_VALUE: frozenset({TerminalStatus.UNRESOLVED}),
    Stage.FINITE_SHOCK: frozenset({TerminalStatus.UNRESOLVED}),
    Stage.TOLERANCE: frozenset(
        {
            TerminalStatus.RESOLVED_WITHIN_TOLERANCE,
            TerminalStatus.IDENTIFIED_OUTSIDE_TOLERANCE,
        }
    ),
    None: frozenset(
        {
            TerminalStatus.RESOLVED_WITHIN_TOLERANCE,
            TerminalStatus.IDENTIFIED_OUTSIDE_TOLERANCE,
        }
    ),
}


def reached_stages(failed_stage: Stage | None) -> tuple[Stage, ...]:
    """Return the stages a pair passed, given where it stopped."""
    if failed_stage is None:
        return STAGE_ORDER
    return STAGE_ORDER[: STAGE_ORDER.index(failed_stage)]


@dataclass(frozen=True)
class PairRecord:
    """One attempted pair with exactly one terminal status."""

    pair_id: str
    terminal: TerminalStatus
    failed_stage: Stage | None = None
    reason: ReasonCode = ReasonCode.NONE
    detail: str | None = None
    reached: tuple[Stage, ...] = ()

    def __post_init__(self) -> None:
        if not self.pair_id:
            raise ReconciliationError("pair_id must be non-empty")
        expected = reached_stages(self.failed_stage)
        if self.reached and tuple(self.reached) != expected:
            raise ReconciliationError(
                f"{self.pair_id}: reached stages {self.reached} do not match "
                f"failed stage {self.failed_stage}"
            )
        object.__setattr__(self, "reached", expected)
        allowed = _ALLOWED_TERMINALS[self.failed_stage]
        if self.terminal not in allowed:
            raise ReconciliationError(
                f"{self.pair_id}: terminal {self.terminal.value} is not allowed "
                f"for failed stage {self.failed_stage}"
            )


def reconcile(
    records: Iterable[PairRecord], attempted: int | None = None
) -> dict[str, object]:
    """Check that statuses reconcile to the attempted total at every stage."""
    items = list(records)
    if attempted is not None and attempted != len(items):
        raise ReconciliationError(
            f"attempted {attempted} pairs but only {len(items)} records exist"
        )
    for stage in STAGE_ORDER:
        passed = sum(1 for record in items if stage in record.reached)
        downstream = sum(
            1
            for record in items
            if record.failed_stage is None
            or STAGE_ORDER.index(record.failed_stage) > STAGE_ORDER.index(stage)
        )
        if passed != downstream:
            raise ReconciliationError(
                f"stage {stage.value}: {passed} passed but {downstream} "
                "records are downstream of it"
            )
    counts = Counter(record.terminal for record in items)
    return {
        "attempted": len(items),
        "terminal_counts": {
            status.value: counts.get(status, 0) for status in TerminalStatus
        },
        "stage_counts": {
            stage.value: sum(1 for record in items if stage in record.reached)
            for stage in STAGE_ORDER
        },
    }


@dataclass(frozen=True)
class FunnelRow:
    stage: Stage
    count: int
    share_of_attempted: float
    share_of_prior: float
    dominant_rejection_reason: str | None


def funnel(
    records: Iterable[PairRecord], attempted: int | None = None
) -> list[FunnelRow]:
    """Return the attrition funnel with per-stage shares and main reason."""
    items = list(records)
    reconcile(items, attempted=attempted)
    total = len(items)
    rows: list[FunnelRow] = []
    prior = total
    for stage in STAGE_ORDER:
        count = sum(1 for record in items if stage in record.reached)
        failures = [
            record.reason.value
            for record in items
            if record.failed_stage is stage and record.reason is not ReasonCode.NONE
        ]
        dominant = Counter(failures).most_common(1)[0][0] if failures else None
        rows.append(
            FunnelRow(
                stage=stage,
                count=count,
                share_of_attempted=count / total if total else 0.0,
                share_of_prior=count / prior if prior else 0.0,
                dominant_rejection_reason=dominant,
            )
        )
        prior = count
    return rows
