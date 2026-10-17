"""High-precision Decimal audit for generated near-bound BSM round trips.

The implementation uses only the Python standard library and does not import
build_demo, r10_diagnostics, or the separately coded double-precision check.
It is a numerical cross-check, not a proof or an independent human replication.
"""

from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

PRECISION = 180
_D = Decimal


def _atan_reciprocal(denominator: int) -> Decimal:
    x = _D(1) / _D(denominator)
    x_squared = x*x
    term = x
    total = x
    index = 0
    cutoff = _D(1).scaleb(-PRECISION-10)
    while abs(term) > cutoff:
        term *= -x_squared
        index += 1
        total += term / _D(2*index+1)
    return total


with localcontext() as _context:
    _context.prec = PRECISION
    PI = 16*_atan_reciprocal(5)-4*_atan_reciprocal(239)
    SQRT_TWO = _D(2).sqrt()
    SQRT_TWO_PI = (_D(2)*PI).sqrt()


def _normal_cdf(value: Decimal) -> Decimal:
    """Normal CDF from a Decimal erf power series at fixed high precision."""
    with localcontext() as context:
        context.prec = PRECISION
        z = value/SQRT_TWO
        z_squared = z*z
        term = z
        total = term
        cutoff = _D(1).scaleb(-PRECISION-10)
        for index in range(1, 4000):
            term *= -z_squared/_D(index)*_D(2*index-1)/_D(2*index+1)
            total += term
            if abs(term) < cutoff and index > int(z_squared):
                break
        erf_value = _D(2)*total/PI.sqrt()
        return (_D(1)+erf_value)/_D(2)


def _bsm_price(kind: str, spot: Decimal, strike: Decimal, days: Decimal,
               rate: Decimal, yield_: Decimal, volatility: Decimal) -> Decimal:
    years = days/_D(365)
    root_years = years.sqrt()
    d1 = (
        (spot/strike).ln()
        +(rate-yield_+volatility*volatility/_D(2))*years
    )/(volatility*root_years)
    d2 = d1-volatility*root_years
    pv_spot = spot*(-yield_*years).exp()
    pv_strike = strike*(-rate*years).exp()
    if kind == "call":
        return pv_spot*_normal_cdf(d1)-pv_strike*_normal_cdf(d2)
    if kind == "put":
        return pv_strike*_normal_cdf(-d2)-pv_spot*_normal_cdf(-d1)
    raise ValueError("kind must be call or put")


def _price_bounds(kind: str, spot: Decimal, strike: Decimal, days: Decimal,
                  rate: Decimal, yield_: Decimal) -> tuple[Decimal, Decimal]:
    years = days/_D(365)
    pv_spot = spot*(-yield_*years).exp()
    pv_strike = strike*(-rate*years).exp()
    if kind == "call":
        return max(pv_spot-pv_strike, _D(0)), pv_spot
    if kind == "put":
        return max(pv_strike-pv_spot, _D(0)), pv_strike
    raise ValueError("kind must be call or put")


def audit_rejected_rows(input_csv: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with input_csv.open(encoding="utf-8", newline="") as handle:
        source_rows = csv.DictReader(handle)
        for source in source_rows:
            if source["status"] == "ok":
                continue
            with localcontext() as context:
                context.prec = PRECISION
                kind = source["option_type"]
                ratio = _D(source["spot_strike_ratio"])
                spot, strike = ratio*_D(100), _D(100)
                days = _D(source["days_to_expiry"])
                target_iv = _D(source["target_iv"])
                rate, yield_ = _D("0.03"), _D("0.01")
                exact_price = _bsm_price(
                    kind, spot, strike, days, rate, yield_, target_iv
                )
                lower, upper = _price_bounds(
                    kind, spot, strike, days, rate, yield_
                )
                double_price = _D(source["theoretical_price_usd"])
                distance_lower = exact_price-lower
                distance_upper = upper-exact_price
                nearest_distance = min(distance_lower, distance_upper)
                double_distance_lower = double_price-lower
                double_distance_upper = upper-double_price
                rows.append({
                    "option_type": kind,
                    "spot_strike_ratio": source["spot_strike_ratio"],
                    "days_to_expiry": source["days_to_expiry"],
                    "target_iv_decimal": source["target_iv"],
                    "double_precision_failure_status": source["failure_status"],
                    "double_precision_price": str(double_price),
                    "decimal180_bsm_price": str(exact_price),
                    "decimal_minus_double_price": str(exact_price-double_price),
                    "decimal_distance_above_lower_bound": str(distance_lower),
                    "decimal_distance_below_upper_bound": str(distance_upper),
                    "decimal_strictly_inside_bounds": lower < exact_price < upper,
                    "target_root_in_configured_iv_bracket": (
                        _D("1e-8") < target_iv < _D(5)
                    ),
                    "decimal_price_within_1e-10_absolute_guard": (
                        nearest_distance <= _D("1e-10")
                    ),
                    "double_price_strictly_inside_bounds": (
                        lower < double_price < upper
                    ),
                    "double_price_lower_distance": str(double_distance_lower),
                    "double_price_upper_distance": str(double_distance_upper),
                    "precision_digits": PRECISION,
                    "normal_cdf_method": (
                        "Decimal erf power series; pi via Machin arctangent series"
                    ),
                    "interpretation": (
                        "same-author high-precision numerical cross-check; not a proof"
                    ),
                })
    return rows


def write_audit(input_csv: Path, output_csv: Path,
                summary_path: Path) -> dict[str, Any]:
    rows = audit_rejected_rows(input_csv)
    if not rows:
        raise ValueError("input contains no rejected generated-price rows")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    statuses: dict[str, int] = {}
    for row in rows:
        status = str(row["double_precision_failure_status"])
        statuses[status] = statuses.get(status, 0)+1
    summary = {
        "audited_rejected_cases": len(rows),
        "double_precision_failure_status_counts": statuses,
        "decimal_strictly_inside_bound_count": sum(
            bool(row["decimal_strictly_inside_bounds"]) for row in rows
        ),
        "target_root_inside_configured_bracket_count": sum(
            bool(row["target_root_in_configured_iv_bracket"]) for row in rows
        ),
        "decimal_price_within_absolute_guard_count": sum(
            bool(row["decimal_price_within_1e-10_absolute_guard"]) for row in rows
        ),
        "double_price_strictly_inside_bounds_count": sum(
            bool(row["double_price_strictly_inside_bounds"]) for row in rows
        ),
        "decimal_precision_digits": PRECISION,
        "reference": (
            "standard-library Decimal BSM implementation with Decimal normal-CDF series"
        ),
        "scope_limit": (
            "generated near-bound cases only; not a proof or market-data assessment"
        ),
        "csv": str(output_csv),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    summary = write_audit(args.input, args.output, args.summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
