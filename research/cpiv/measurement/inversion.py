"""European BSM inversion contract.

The contract is inherited from :mod:`research.cpiv.build_demo` so that the
measurement core and the published synthetic note share one solver: decimal-IV
bracket [1e-8, 5], 64 bisection iterations, no quote clipping, and rejection of
prices within 1e-10 currency units of a European bound.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from research.cpiv import build_demo as bsm

NEAR_BOUND_GUARD_USD = 1e-10
IV_LOW = 1e-8
IV_HIGH = bsm.MAX_IV
MAX_ITERATIONS = 64


class FailureClass(StrEnum):
    """Named failure classes; a configured rejection is not an invalid quote."""

    OK = "ok"
    INVALID_INPUT = "invalid_input"
    THEORETICAL_BOUND_VIOLATION = "theoretical_bound_violation"
    NEAR_BOUND_GUARD = "near_bound_guard"
    OUTSIDE_BRACKET = "outside_bracket"
    NUMERICAL = "numerical"


@dataclass(frozen=True)
class InversionOutcome:
    """One leg's inversion result with separately reported errors."""

    ok: bool
    price: float
    iv: float | None
    failure: FailureClass
    repricing_error: float | None = None
    iv_recovery_error: float | None = None
    vega: float | None = None


def classify_failure(
    option_type: str,
    price: float,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
) -> FailureClass:
    """Classify a rejected price in the order used by the solver."""
    numeric = (price, spot, strike, rate, dividend_yield)
    if option_type not in ("call", "put"):
        return FailureClass.INVALID_INPUT
    if not all(math.isfinite(value) for value in numeric):
        return FailureClass.INVALID_INPUT
    if price < 0 or spot <= 0 or strike <= 0 or days <= 0:
        return FailureClass.INVALID_INPUT
    lower, upper = bsm.price_bounds(option_type, spot, strike, days, rate, dividend_yield)
    if price < lower or price > upper:
        return FailureClass.THEORETICAL_BOUND_VIOLATION
    if min(price - lower, upper - price) <= NEAR_BOUND_GUARD_USD:
        return FailureClass.NEAR_BOUND_GUARD
    low_price = bsm.bs_price(
        option_type, spot, strike, days, rate, dividend_yield, IV_LOW
    )
    high_price = bsm.bs_price(
        option_type, spot, strike, days, rate, dividend_yield, IV_HIGH
    )
    if price < low_price - NEAR_BOUND_GUARD_USD or price > high_price + NEAR_BOUND_GUARD_USD:
        return FailureClass.OUTSIDE_BRACKET
    return FailureClass.OK  # no configured rejection; hand the price to the solver


def invert_leg(
    option_type: str,
    price: float,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
    target_iv: float | None = None,
) -> InversionOutcome:
    """Invert one leg, recording repricing and IV-recovery error separately."""
    failure = classify_failure(
        option_type, price, spot, strike, days, rate, dividend_yield
    )
    if failure is not FailureClass.OK:
        return InversionOutcome(ok=False, price=price, iv=None, failure=failure)
    try:
        iv = bsm.implied_volatility(
            option_type, price, spot, strike, days, rate, dividend_yield
        )
    except ValueError:
        return InversionOutcome(
            ok=False, price=price, iv=None, failure=FailureClass.NUMERICAL
        )
    repriced = bsm.bs_price(option_type, spot, strike, days, rate, dividend_yield, iv)
    recovery = abs(iv - target_iv) if target_iv is not None else None
    vega = 100.0 * bsm.bs_vega_per_vol_point(
        spot, strike, days, rate, dividend_yield, iv
    )
    return InversionOutcome(
        ok=True,
        price=price,
        iv=iv,
        failure=FailureClass.OK,
        repricing_error=abs(repriced - price),
        iv_recovery_error=recovery,
        vega=vega,
    )


ROUND_TRIP_RATIOS = (0.8, 0.9, 1.0, 1.1, 1.2)
ROUND_TRIP_DAYS = (7, 30, 90, 365)
ROUND_TRIP_IVS = (0.10, 0.20, 0.40)


def round_trip_summary() -> dict[str, object]:
    """Replay the 60-configuration, 120-leg grid recorded in the note."""
    total = 0
    inverted = 0
    failures: dict[str, int] = {}
    max_repricing = 0.0
    max_recovery = 0.0
    for ratio in ROUND_TRIP_RATIOS:
        for days in ROUND_TRIP_DAYS:
            for sigma in ROUND_TRIP_IVS:
                for option_type in ("call", "put"):
                    spot, strike, rate, q = 100.0 * ratio, 100.0, 0.03, 0.01
                    price = bsm.bs_price(
                        option_type, spot, strike, days, rate, q, sigma
                    )
                    outcome = invert_leg(
                        option_type, price, spot, strike, days, rate, q,
                        target_iv=sigma,
                    )
                    total += 1
                    if not outcome.ok:
                        failures[outcome.failure.value] = (
                            failures.get(outcome.failure.value, 0) + 1
                        )
                        continue
                    inverted += 1
                    assert outcome.repricing_error is not None
                    assert outcome.iv_recovery_error is not None
                    max_repricing = max(max_repricing, outcome.repricing_error)
                    max_recovery = max(max_recovery, outcome.iv_recovery_error)
    return {
        "contract_configurations": 60,
        "option_leg_prices": total,
        "inverted": inverted,
        "rejected": total - inverted,
        "failures_by_class": failures,
        "max_repricing_error_usd": max_repricing,
        "max_iv_recovery_error_decimal": max_recovery,
    }
