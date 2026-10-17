"""Separately coded standard-library check of the common-map identity.

This module intentionally does not import build_demo or r10_diagnostics.
It is a second implementation by the same project author, not an independent
human replication or a high-precision numerical oracle.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any


def _cdf(value: float) -> float:
    return (1.0 + math.erf(value / math.sqrt(2.0))) / 2.0


def _price(kind: str, spot: float, strike: float, years: float,
           rate: float, yield_: float, volatility: float) -> float:
    d1 = (
        math.log(spot / strike)
        + (rate - yield_ + volatility * volatility / 2.0) * years
    ) / (volatility * math.sqrt(years))
    d2 = d1 - volatility * math.sqrt(years)
    pv_spot = spot * math.exp(-yield_ * years)
    pv_strike = strike * math.exp(-rate * years)
    if kind == "call":
        return pv_spot * _cdf(d1) - pv_strike * _cdf(d2)
    if kind == "put":
        return pv_strike * _cdf(-d2) - pv_spot * _cdf(-d1)
    raise ValueError("kind must be call or put")


def _vega(spot: float, strike: float, years: float, rate: float,
          yield_: float, volatility: float) -> float:
    d1 = (
        math.log(spot / strike)
        + (rate - yield_ + volatility * volatility / 2.0) * years
    ) / (volatility * math.sqrt(years))
    return (
        spot * math.exp(-yield_ * years)
        * math.exp(-d1 * d1 / 2.0) / math.sqrt(2.0 * math.pi)
        * math.sqrt(years)
    )


def _bounds(kind: str, spot: float, strike: float, years: float,
            rate: float, yield_: float) -> tuple[float, float]:
    pv_spot = spot * math.exp(-yield_ * years)
    pv_strike = strike * math.exp(-rate * years)
    if kind == "call":
        return max(pv_spot - pv_strike, 0.0), pv_spot
    if kind == "put":
        return max(pv_strike - pv_spot, 0.0), pv_strike
    raise ValueError("kind must be call or put")


def _invert(kind: str, market_price: float, spot: float, strike: float,
            years: float, rate: float, yield_: float) -> float:
    lower, upper = _bounds(kind, spot, strike, years, rate, yield_)
    if (not math.isfinite(market_price) or market_price <= lower + 1e-10
            or market_price >= upper - 1e-10):
        raise ValueError("price outside strict European inversion bounds")
    lo, hi = 1e-8, 5.0
    if not (_price(kind, spot, strike, years, rate, yield_, lo) <= market_price
            <= _price(kind, spot, strike, years, rate, yield_, hi)):
        raise ValueError("price outside independent volatility bracket")
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if _price(kind, spot, strike, years, rate, yield_, mid) < market_price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _integral_vega(spot: float, strike: float, years: float,
                   rate: float, yield_: float, low: float, high: float,
                   intervals: int = 4000) -> float:
    if low == high:
        return 0.0
    direction = 1.0 if high > low else -1.0
    a, b = (low, high) if high > low else (high, low)
    step = (b-a)/intervals
    values = [_vega(spot, strike, years, rate, yield_, a+i*step)
              for i in range(intervals+1)]
    total = values[0]+values[-1]
    total += 4.0*sum(values[i] for i in range(1, intervals, 2))
    total += 2.0*sum(values[i] for i in range(2, intervals, 2))
    return direction*step*total/3.0


def _crr_american_put(spot: float, strike: float, years: float,
                      rate: float, yield_: float, volatility: float,
                      steps: int = 800) -> float:
    dt = years/steps
    up = math.exp(volatility*math.sqrt(dt))
    down = 1.0/up
    probability = (math.exp((rate-yield_)*dt)-down)/(up-down)
    discount = math.exp(-rate*dt)
    values = [
        max(strike-spot*up**j*down**(steps-j), 0.0)
        for j in range(steps+1)
    ]
    for time in range(steps-1, -1, -1):
        for j in range(time+1):
            continuation = discount*(probability*values[j+1]
                                     +(1.0-probability)*values[j])
            node = spot*up**j*down**(time-j)
            values[j] = max(continuation, strike-node, 0.0)
    return values[0]


def run_checks() -> list[dict[str, Any]]:
    strike, years, rate, yield_ = 100.0, 30.0/365.0, 0.05, 0.0
    source_spot = 100.0
    cases: list[dict[str, Any]] = []

    # Same-map European prices with unequal leg volatilities.
    cases.append({
        "case": "european_bsm_unequal_iv",
        "price_origin": "European BSM",
        "spot": 100.0,
        "call_price": _price("call", 100.0, strike, years, rate, yield_, 0.23),
        "put_price": _price("put", 100.0, strike, years, rate, yield_, 0.20),
    })

    # A price from an American exercise model, then both legs use one BSM map.
    cases.append({
        "case": "american_origin_put_common_bsm_inversion",
        "price_origin": "European BSM call plus CRR American put",
        "spot": 100.0,
        "call_price": _price("call", 100.0, strike, years, rate, yield_, 0.20),
        "put_price": _crr_american_put(100.0, strike, years, rate, yield_, 0.20),
    })

    # Source quotes use one spot; both legs are inverted at a stale common spot.
    cases.append({
        "case": "stale_source_spot_common_inversion_inputs",
        "price_origin": "European BSM quotes formed at source spot 100",
        "spot": 100.10,
        "source_spot": source_spot,
        "call_price": _price("call", source_spot, strike, years, rate, yield_, 0.23),
        "put_price": _price("put", source_spot, strike, years, rate, yield_, 0.20),
    })

    # Small arbitrary premium perturbations preserve admissible common-map roots.
    cases.append({
        "case": "admissible_arbitrary_price_perturbation",
        "price_origin": "BSM prices plus fixed synthetic premium perturbations",
        "spot": 100.0,
        "call_price": _price("call", 100.0, strike, years, rate, yield_, 0.23)+0.002,
        "put_price": _price("put", 100.0, strike, years, rate, yield_, 0.20)-0.002,
    })

    rows: list[dict[str, Any]] = []
    for case in cases:
        spot = float(case["spot"])
        call_price = float(case["call_price"])
        put_price = float(case["put_price"])
        call_iv = _invert("call", call_price, spot, strike, years, rate, yield_)
        put_iv = _invert("put", put_price, spot, strike, years, rate, yield_)
        parity = spot*math.exp(-yield_*years)-strike*math.exp(-rate*years)
        residual = call_price-put_price-parity
        integral = _integral_vega(
            spot, strike, years, rate, yield_, put_iv, call_iv
        )
        rows.append({
            "case": case["case"],
            "price_origin": case["price_origin"],
            "source_spot_if_different": case.get("source_spot", ""),
            "common_inversion_spot": spot,
            "strike": strike,
            "maturity_years": years,
            "rate": rate,
            "yield": yield_,
            "call_price": call_price,
            "put_price": put_price,
            "call_iv": call_iv,
            "put_iv": put_iv,
            "parity_residual": residual,
            "integrated_vega": integral,
            "absolute_identity_gap": abs(residual-integral),
            "interpretation": (
                "separately coded common-map check; not independent human replication"
            ),
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = run_checks()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} separately coded cases to {args.output}")


if __name__ == "__main__":
    main()
