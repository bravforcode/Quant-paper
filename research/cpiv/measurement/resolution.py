"""Resolution rules for a matched CPIV pair.

The order follows the declared protocol: midpoint roots, endpoint range,
OTM-equivalent time value, finite shock, then tolerance. A later failure
outranks an earlier partial result, so a partially quoted pair that also fails
the time-value rule is `UNRESOLVED`, not `PARTIALLY_RESOLVED`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from research.cpiv import build_demo as bsm
from research.cpiv.measurement.inversion import FailureClass, invert_leg
from research.cpiv.measurement.status import (
    PairRecord,
    ReasonCode,
    Stage,
    TerminalStatus,
)

_LEG_TERMINALS: dict[FailureClass, tuple[TerminalStatus, ReasonCode]] = {
    FailureClass.INVALID_INPUT: (TerminalStatus.INVALID_INPUT, ReasonCode.QUOTE_INVALID),
    FailureClass.THEORETICAL_BOUND_VIOLATION: (
        TerminalStatus.INVALID_INPUT,
        ReasonCode.THEORETICAL_BOUND_VIOLATION,
    ),
    FailureClass.NEAR_BOUND_GUARD: (
        TerminalStatus.UNRESOLVED,
        ReasonCode.NEAR_BOUND_GUARD,
    ),
    FailureClass.OUTSIDE_BRACKET: (
        TerminalStatus.UNRESOLVED,
        ReasonCode.OUTSIDE_BRACKET,
    ),
    FailureClass.NUMERICAL: (TerminalStatus.UNRESOLVED, ReasonCode.NUMERICAL_FAILURE),
}


@dataclass(frozen=True)
class ResolutionInput:
    """One matched pair expressed in prices, with declared resolution settings."""

    pair_id: str
    call_mid: float
    put_mid: float
    call_bid: float
    call_ask: float
    put_bid: float
    put_ask: float
    spot: float
    strike: float
    days: int
    rate: float = 0.0
    dividend_yield: float = 0.0
    tick: float = 0.01
    resolution_ticks: float = 1.0
    shock: float | None = None
    tolerance_pp: float = 0.10


@dataclass(frozen=True)
class ResolutionOutcome:
    pair_id: str
    terminal: TerminalStatus
    failed_stage: Stage | None
    reason: ReasonCode
    cpiv_mid_pp: float | None = None
    interval_low_pp: float | None = None
    interval_high_pp: float | None = None
    displacement_pp: float | None = None
    otm_time_value: float | None = None
    otm_vega: float | None = None
    parity_residual: float | None = None
    mid_inside_bounds: bool = False

    def to_record(self) -> PairRecord:
        return PairRecord(
            pair_id=self.pair_id,
            terminal=self.terminal,
            failed_stage=self.failed_stage,
            reason=self.reason,
        )


def _strictly_inside(option_type: str, price: float, spec: ResolutionInput) -> bool:
    lower, upper = bsm.price_bounds(
        option_type, spec.spot, spec.strike, spec.days, spec.rate, spec.dividend_yield
    )
    return min(price - lower, upper - price) > 1e-10


def _failed(
    spec: ResolutionInput,
    stage: Stage,
    terminal: TerminalStatus,
    reason: ReasonCode,
    **fields: object,
) -> ResolutionOutcome:
    return ResolutionOutcome(
        pair_id=spec.pair_id,
        terminal=terminal,
        failed_stage=stage,
        reason=reason,
        **fields,  # type: ignore[arg-type]
    )


def resolve(spec: ResolutionInput) -> ResolutionOutcome:
    """Apply the declared resolution rules to one pair."""
    call = invert_leg(
        "call", spec.call_mid, spec.spot, spec.strike, spec.days,
        spec.rate, spec.dividend_yield,
    )
    put = invert_leg(
        "put", spec.put_mid, spec.spot, spec.strike, spec.days,
        spec.rate, spec.dividend_yield,
    )
    for leg in (call, put):
        if not leg.ok:
            terminal, reason = _LEG_TERMINALS[leg.failure]
            return _failed(spec, Stage.MIDPOINT, terminal, reason)
    assert call.iv is not None and put.iv is not None
    cpiv = 100.0 * (call.iv - put.iv)

    # Endpoint range: 100 * [IV(C_bid) - IV(P_ask), IV(C_ask) - IV(P_bid)].
    endpoints = {
        "call_bid": invert_leg(
            "call", spec.call_bid, spec.spot, spec.strike, spec.days,
            spec.rate, spec.dividend_yield,
        ),
        "call_ask": invert_leg(
            "call", spec.call_ask, spec.spot, spec.strike, spec.days,
            spec.rate, spec.dividend_yield,
        ),
        "put_bid": invert_leg(
            "put", spec.put_bid, spec.spot, spec.strike, spec.days,
            spec.rate, spec.dividend_yield,
        ),
        "put_ask": invert_leg(
            "put", spec.put_ask, spec.spot, spec.strike, spec.days,
            spec.rate, spec.dividend_yield,
        ),
    }
    lower = None
    if endpoints["call_bid"].ok and endpoints["put_ask"].ok:
        assert endpoints["call_bid"].iv is not None
        assert endpoints["put_ask"].iv is not None
        lower = 100.0 * (endpoints["call_bid"].iv - endpoints["put_ask"].iv)
    upper = None
    if endpoints["call_ask"].ok and endpoints["put_bid"].ok:
        assert endpoints["call_ask"].iv is not None
        assert endpoints["put_bid"].iv is not None
        upper = 100.0 * (endpoints["call_ask"].iv - endpoints["put_bid"].iv)
    if lower is None and upper is None:
        return _failed(
            spec, Stage.ENDPOINT, TerminalStatus.UNRESOLVED,
            ReasonCode.ENDPOINT_INCOMPLETE, cpiv_mid_pp=cpiv,
        )
    partial = lower is None or upper is None
    if lower is not None and upper is not None and lower > upper:
        lower, upper = upper, lower

    intrinsic_call = max(spec.spot - spec.strike, 0.0)
    intrinsic_put = max(spec.strike - spec.spot, 0.0)
    tv_call = max(spec.call_mid - intrinsic_call, 0.0)
    tv_put = max(spec.put_mid - intrinsic_put, 0.0)
    if spec.spot > spec.strike:
        otm_tv, otm_vega = tv_put, put.vega
    elif spec.spot < spec.strike:
        otm_tv, otm_vega = tv_call, call.vega
    else:
        otm_tv = min(tv_call, tv_put)
        otm_vega = min(vega for vega in (call.vega, put.vega) if vega is not None)
    scale = spec.resolution_ticks * spec.tick
    if otm_tv < scale:
        return _failed(
            spec, Stage.TIME_VALUE, TerminalStatus.UNRESOLVED,
            ReasonCode.TIME_VALUE_BELOW_SCALE,
            cpiv_mid_pp=cpiv, interval_low_pp=lower, interval_high_pp=upper,
            otm_time_value=otm_tv, otm_vega=otm_vega,
        )

    shock = spec.tick if spec.shock is None else spec.shock
    for option_type, mid in (("call", spec.call_mid), ("put", spec.put_mid)):
        for shifted in (mid - shock, mid + shock):
            if shifted <= 0.0:
                return _failed(
                    spec, Stage.FINITE_SHOCK, TerminalStatus.UNRESOLVED,
                    ReasonCode.FINITE_SHOCK_ABSENT,
                    cpiv_mid_pp=cpiv, interval_low_pp=lower, interval_high_pp=upper,
                    otm_time_value=otm_tv, otm_vega=otm_vega,
                )
            leg = invert_leg(
                option_type, shifted, spec.spot, spec.strike, spec.days,
                spec.rate, spec.dividend_yield,
            )
            if not leg.ok:
                return _failed(
                    spec, Stage.FINITE_SHOCK, TerminalStatus.UNRESOLVED,
                    ReasonCode.FINITE_SHOCK_ABSENT,
                    cpiv_mid_pp=cpiv, interval_low_pp=lower, interval_high_pp=upper,
                    otm_time_value=otm_tv, otm_vega=otm_vega,
                )

    residual = bsm.parity_residual(
        spec.call_mid, spec.put_mid, spec.spot, spec.strike, spec.days,
        spec.rate, spec.dividend_yield,
    )
    inside = _strictly_inside("call", spec.call_mid, spec) and _strictly_inside(
        "put", spec.put_mid, spec
    )
    if partial:
        return ResolutionOutcome(
            pair_id=spec.pair_id,
            terminal=TerminalStatus.PARTIALLY_RESOLVED,
            failed_stage=Stage.ENDPOINT,
            reason=ReasonCode.ENDPOINT_INCOMPLETE,
            cpiv_mid_pp=cpiv,
            interval_low_pp=lower,
            interval_high_pp=upper,
            otm_time_value=otm_tv,
            otm_vega=otm_vega,
            parity_residual=residual,
            mid_inside_bounds=inside,
        )
    assert lower is not None and upper is not None
    displacement = max(abs(cpiv - lower), abs(upper - cpiv))
    if displacement <= spec.tolerance_pp:
        terminal, reason = TerminalStatus.RESOLVED_WITHIN_TOLERANCE, ReasonCode.NONE
    else:
        terminal, reason = (
            TerminalStatus.IDENTIFIED_OUTSIDE_TOLERANCE,
            ReasonCode.TOLERANCE_EXCEEDED,
        )
    return ResolutionOutcome(
        pair_id=spec.pair_id,
        terminal=terminal,
        failed_stage=None,
        reason=reason,
        cpiv_mid_pp=cpiv,
        interval_low_pp=lower,
        interval_high_pp=upper,
        displacement_pp=displacement,
        otm_time_value=otm_tv,
        otm_vega=otm_vega,
        parity_residual=residual,
        mid_inside_bounds=inside,
    )


def is_finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)
