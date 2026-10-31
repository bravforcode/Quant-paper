"""Contract matching, quote validation and timestamp synchronisation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime

from research.cpiv.measurement.status import (
    PairRecord,
    ReasonCode,
    Stage,
    TerminalStatus,
)

CONTRACT_FIELDS = (
    "underlying",
    "strike",
    "expiry",
    "multiplier",
    "exercise_style",
    "settlement",
)


@dataclass(frozen=True)
class Contract:
    """Terms that must match between the call and the put."""

    underlying: str
    strike: float
    expiry: date
    multiplier: int = 100
    exercise_style: str = "european"
    settlement: str = "cash"


@dataclass(frozen=True)
class Quote:
    bid: float
    ask: float
    timestamp_utc: datetime

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0

    def is_valid(self) -> bool:
        numeric = (self.bid, self.ask)
        if not all(math.isfinite(value) for value in numeric):
            return False
        return self.bid >= 0.0 and self.ask > 0.0 and self.bid <= self.ask


@dataclass(frozen=True)
class PairCheck:
    """Outcome of the contract, timing and quote stages."""

    ok: bool
    failed_stage: Stage | None
    terminal: TerminalStatus | None
    reason: ReasonCode
    detail: str | None
    lags_seconds: dict[str, float | None]

    def to_record(self, pair_id: str) -> PairRecord:
        if self.ok or self.terminal is None:
            raise ValueError("only failed pair checks can be converted to a record")
        return PairRecord(
            pair_id=pair_id,
            terminal=self.terminal,
            failed_stage=self.failed_stage,
            reason=self.reason,
            detail=self.detail,
        )


def _contract_mismatch(call: Contract, put: Contract) -> str | None:
    for field in CONTRACT_FIELDS:
        if getattr(call, field) != getattr(put, field):
            return field
    return None


def _lags(
    call: Quote, put: Quote, spot_timestamp: datetime
) -> dict[str, float | None]:
    aware = {call.timestamp_utc.tzinfo is not None, put.timestamp_utc.tzinfo is not None,
             spot_timestamp.tzinfo is not None}
    if len(aware) != 1:
        return {"call_put": None, "call_spot": None, "put_spot": None}
    return {
        "call_put": (put.timestamp_utc - call.timestamp_utc).total_seconds(),
        "call_spot": (call.timestamp_utc - spot_timestamp).total_seconds(),
        "put_spot": (put.timestamp_utc - spot_timestamp).total_seconds(),
    }


def check_pair(
    call_quote: Quote,
    put_quote: Quote,
    spot: float,
    spot_timestamp_utc: datetime,
    call_contract: Contract,
    put_contract: Contract,
    tolerance_seconds: float,
) -> PairCheck:
    """Run the contract, timing and quote stages in that order."""
    mismatch = _contract_mismatch(call_contract, put_contract)
    if mismatch is not None:
        return PairCheck(
            ok=False,
            failed_stage=Stage.CONTRACT,
            terminal=TerminalStatus.CONTRACT_MISMATCH,
            reason=ReasonCode.NONE,
            detail=mismatch,
            lags_seconds={},
        )
    lags = _lags(call_quote, put_quote, spot_timestamp_utc)
    unusable = any(value is None for value in lags.values())
    if unusable:
        return PairCheck(
            ok=False,
            failed_stage=Stage.TIMING,
            terminal=TerminalStatus.TIMING_MISMATCH,
            reason=ReasonCode.NONE,
            detail="quote and spot timestamps must share one timezone convention",
            lags_seconds=lags,
        )
    worst_lag = max(abs(value) for value in lags.values() if value is not None)
    if worst_lag > tolerance_seconds:
        return PairCheck(
            ok=False,
            failed_stage=Stage.TIMING,
            terminal=TerminalStatus.TIMING_MISMATCH,
            reason=ReasonCode.NONE,
            detail=f"worst lag {worst_lag:.3f}s exceeds {tolerance_seconds:.3f}s",
            lags_seconds=lags,
        )
    for quote in (call_quote, put_quote):
        if not quote.is_valid():
            return PairCheck(
                ok=False,
                failed_stage=Stage.QUOTE,
                terminal=TerminalStatus.INVALID_INPUT,
                reason=ReasonCode.QUOTE_INVALID,
                detail="bid/ask must be finite with 0 <= bid <= ask and ask > 0",
                lags_seconds=lags,
            )
    if not math.isfinite(spot) or spot <= 0:
        return PairCheck(
            ok=False,
            failed_stage=Stage.INPUT,
            terminal=TerminalStatus.INVALID_INPUT,
            reason=ReasonCode.INPUT_INCOMPLETE,
            detail="spot must be finite and positive",
            lags_seconds=lags,
        )
    return PairCheck(
        ok=True,
        failed_stage=None,
        terminal=None,
        reason=ReasonCode.NONE,
        detail=None,
        lags_seconds=lags,
    )
