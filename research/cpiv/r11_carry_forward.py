"""Synthetic carry/forward sensitivity and independent-input consistency checks."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from research.cpiv import build_demo as demo

SECONDS_PER_YEAR = 365.0
BASE_SPOT = 100.0
BASE_STRIKE = 100.0
BASE_DAYS = 30
BASE_RATE = 0.0
BASE_IV = 0.20
CARRY_SCENARIOS = (-0.02, -0.01, 0.0, 0.01, 0.02, 0.05)
SPOT_SCENARIOS = (-0.25, -0.10, -0.05, -0.02, 0.02, 0.05, 0.10, 0.25)


def _d1(spot: float, strike: float, days: int, rate: float, yield_: float, sigma: float) -> float:
    maturity = days / SECONDS_PER_YEAR
    return (math.log(spot / strike) + (rate - yield_ + 0.5 * sigma * sigma) * maturity) / (
        sigma * math.sqrt(maturity)
    )


def common_map_input_gradient(
    call_price: float,
    put_price: float,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    yield_: float,
) -> dict[str, float]:
    """Return exact local spot/yield derivatives for fixed leg prices and common inputs."""
    numeric = (call_price, put_price, spot, strike, rate, yield_)
    if not all(math.isfinite(value) for value in numeric) or days <= 0:
        raise ValueError("prices and inputs must be finite, with positive maturity")
    call_iv = demo.implied_volatility("call", call_price, spot, strike, days, rate, yield_)
    put_iv = demo.implied_volatility("put", put_price, spot, strike, days, rate, yield_)
    maturity = days / SECONDS_PER_YEAR
    discount_spot = math.exp(-yield_ * maturity)
    call_vega = 100.0 * demo.bs_vega_per_vol_point(spot, strike, days, rate, yield_, call_iv)
    put_vega = 100.0 * demo.bs_vega_per_vol_point(spot, strike, days, rate, yield_, put_iv)
    if min(call_vega, put_vega) <= 0.0:
        raise ValueError("both implied roots must have positive vega")
    d1_call = _d1(spot, strike, days, rate, yield_, call_iv)
    d1_put = _d1(spot, strike, days, rate, yield_, put_iv)
    call_delta = discount_spot * demo._normal_cdf(d1_call)
    put_delta = discount_spot * (demo._normal_cdf(d1_put) - 1.0)
    call_yield_derivative = -maturity * spot * discount_spot * demo._normal_cdf(d1_call)
    put_yield_derivative = maturity * spot * discount_spot * demo._normal_cdf(-d1_put)
    return {
        "call_iv_decimal": call_iv,
        "put_iv_decimal": put_iv,
        "cpiv_pp": 100.0 * (call_iv - put_iv),
        "call_vega_currency_per_decimal_iv": call_vega,
        "put_vega_currency_per_decimal_iv": put_vega,
        "d_cpiv_pp_d_spot_per_price_unit": 100.0 * (-call_delta / call_vega + put_delta / put_vega),
        "d_cpiv_pp_d_effective_yield_per_unit": 100.0
        * (-call_yield_derivative / call_vega + put_yield_derivative / put_vega),
    }


def forward_relative_tolerance_for_cpiv(
    call_price: float,
    put_price: float,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    yield_: float,
    cpiv_tolerance_pp: float,
) -> dict[str, float]:
    """Convert a CPIV tolerance to a local relative-forward tolerance."""
    if not math.isfinite(cpiv_tolerance_pp) or cpiv_tolerance_pp < 0.0:
        raise ValueError("cpiv_tolerance_pp must be finite and nonnegative")
    gradient = common_map_input_gradient(call_price, put_price, spot, strike, days, rate, yield_)
    maturity = days / SECONDS_PER_YEAR
    d_cpiv_d_log_forward = -gradient["d_cpiv_pp_d_effective_yield_per_unit"] / maturity
    sensitivity_pp_per_bp = abs(d_cpiv_d_log_forward) * 1e-4
    sensitivity_pp_per_percent = abs(d_cpiv_d_log_forward) * 0.01
    if sensitivity_pp_per_bp == 0.0 or not math.isfinite(sensitivity_pp_per_bp):
        raise ValueError("forward-to-CPIV sensitivity must be finite and nonzero")
    tolerance_bp = cpiv_tolerance_pp / sensitivity_pp_per_bp
    tolerance_fraction = tolerance_bp * 1e-4
    return {
        "cpiv_tolerance_pp": cpiv_tolerance_pp,
        "d_cpiv_pp_d_log_forward": d_cpiv_d_log_forward,
        "sensitivity_pp_per_basis_point_forward": sensitivity_pp_per_bp,
        "sensitivity_pp_per_one_percent_forward": sensitivity_pp_per_percent,
        "forward_relative_tolerance_bp_first_order": tolerance_bp,
        "forward_relative_tolerance_fraction_first_order": tolerance_fraction,
        "forward_relative_tolerance_percent_first_order": tolerance_fraction * 100.0,
    }


def check_forward_consistency(
    spot: float | None,
    observed_forward: float | None,
    rate: float | None,
    effective_yield: float | None,
    days: int | None,
    relative_tolerance: float | None,
) -> dict[str, Any]:
    """Check independently sourced synchronized inputs; missing inputs stay unknown."""
    values = (spot, observed_forward, rate, effective_yield, relative_tolerance)
    if days is None or any(value is None for value in values):
        return {"status": "unknown", "reason": "required synchronized input unavailable"}
    assert spot is not None and observed_forward is not None
    assert rate is not None and effective_yield is not None
    assert relative_tolerance is not None and days is not None
    if not all(
        math.isfinite(value)
        for value in (spot, observed_forward, rate, effective_yield, relative_tolerance)
    ):
        raise ValueError("forward-check inputs must be finite")
    if spot <= 0.0 or observed_forward <= 0.0 or days <= 0 or relative_tolerance < 0.0:
        raise ValueError("spot, forward, maturity, and tolerance must be positive/nonnegative")
    maturity = days / SECONDS_PER_YEAR
    modeled_forward = spot * math.exp((rate - effective_yield) * maturity)
    relative_error = abs(observed_forward - modeled_forward) / modeled_forward
    return {
        "status": "validated" if relative_error <= relative_tolerance else "inconsistent",
        "observed_forward": observed_forward,
        "modeled_forward": modeled_forward,
        "relative_error": relative_error,
        "relative_tolerance": relative_tolerance,
        "effective_yield_implied_by_forward": rate - math.log(observed_forward / spot) / maturity,
        "inputs_must_be_independently_sourced_and_synchronized": True,
    }


def synthetic_sensitivity_cases() -> list[dict[str, Any]]:
    """Reproduce the manuscript's carry/spot perturbations and local tangents."""
    rows: list[dict[str, Any]] = []
    for true_yield in CARRY_SCENARIOS:
        call_price = demo.bs_price(
            "call", BASE_SPOT, BASE_STRIKE, BASE_DAYS, BASE_RATE, true_yield, BASE_IV
        )
        put_price = demo.bs_price(
            "put", BASE_SPOT, BASE_STRIKE, BASE_DAYS, BASE_RATE, true_yield, BASE_IV
        )
        gradient = common_map_input_gradient(
            call_price,
            put_price,
            BASE_SPOT,
            BASE_STRIKE,
            BASE_DAYS,
            BASE_RATE,
            true_yield,
        )
        assumed_yield = 0.0
        assumed_call_iv = demo.implied_volatility(
            "call", call_price, BASE_SPOT, BASE_STRIKE, BASE_DAYS, BASE_RATE, assumed_yield
        )
        assumed_put_iv = demo.implied_volatility(
            "put", put_price, BASE_SPOT, BASE_STRIKE, BASE_DAYS, BASE_RATE, assumed_yield
        )
        input_delta = assumed_yield - true_yield
        exact = 100.0 * (assumed_call_iv - assumed_put_iv)
        local = gradient["d_cpiv_pp_d_effective_yield_per_unit"] * input_delta
        rows.append(
            {
                "perturbed_input": "effective_yield_assumed_for_inversion",
                "quote_generation_spot": BASE_SPOT,
                "quote_generation_effective_yield": true_yield,
                "quote_generation_iv_decimal": BASE_IV,
                "baseline_inversion_spot": BASE_SPOT,
                "perturbed_inversion_spot": BASE_SPOT,
                "base_inversion_effective_yield": true_yield,
                "perturbed_inversion_effective_yield": assumed_yield,
                "input_delta": input_delta,
                "exact_cpiv_pp": exact,
                "local_gradient_prediction_pp": local,
                "exact_over_local_abs_ratio": abs(exact / local) if local else None,
                "status": "resolved",
                "market_data_used": False,
            }
        )

    quote_spot = BASE_SPOT
    call_price = demo.bs_price("call", quote_spot, BASE_STRIKE, BASE_DAYS, BASE_RATE, 0.0, BASE_IV)
    put_price = demo.bs_price("put", quote_spot, BASE_STRIKE, BASE_DAYS, BASE_RATE, 0.0, BASE_IV)
    spot_gradient = common_map_input_gradient(
        call_price, put_price, quote_spot, BASE_STRIKE, BASE_DAYS, BASE_RATE, 0.0
    )
    for spot_delta in SPOT_SCENARIOS:
        used_spot = quote_spot + spot_delta
        call_iv = demo.implied_volatility(
            "call", call_price, used_spot, BASE_STRIKE, BASE_DAYS, BASE_RATE, 0.0
        )
        put_iv = demo.implied_volatility(
            "put", put_price, used_spot, BASE_STRIKE, BASE_DAYS, BASE_RATE, 0.0
        )
        exact = 100.0 * (call_iv - put_iv)
        local = spot_gradient["d_cpiv_pp_d_spot_per_price_unit"] * spot_delta
        rows.append(
            {
                "perturbed_input": "inversion_spot",
                "quote_generation_spot": quote_spot,
                "quote_generation_effective_yield": 0.0,
                "quote_generation_iv_decimal": BASE_IV,
                "baseline_inversion_spot": quote_spot,
                "perturbed_inversion_spot": used_spot,
                "base_inversion_effective_yield": 0.0,
                "perturbed_inversion_effective_yield": 0.0,
                "input_delta": spot_delta,
                "exact_cpiv_pp": exact,
                "local_gradient_prediction_pp": local,
                "exact_over_local_abs_ratio": abs(exact / local) if local else None,
                "status": "resolved",
                "market_data_used": False,
            }
        )
    return rows


def write_outputs(output_dir: Path) -> dict[str, Any]:
    rows = synthetic_sensitivity_cases()
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "cpiv_r11_carry_forward_sensitivity.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    example_call = demo.bs_price("call", 100.0, 100.0, 30, 0.0, 0.0, 0.20)
    example_put = demo.bs_price("put", 100.0, 100.0, 30, 0.0, 0.0, 0.20)
    forward_tolerance_example = forward_relative_tolerance_for_cpiv(
        example_call, example_put, 100.0, 100.0, 30, 0.0, 0.0, 1.0
    )
    summary = {
        "status": "synthetic_carry_forward_sensitivity_only",
        "market_data_used": False,
        "case_count": len(rows),
        "cases_by_input": {
            "effective_yield": sum(
                row["perturbed_input"].startswith("effective_yield") for row in rows
            ),
            "spot": sum(row["perturbed_input"] == "inversion_spot" for row in rows),
        },
        "forward_consistency_formula": "F = S * exp((r - q) * T)",
        "forward_observation_used": False,
        "synthetic_atm_1pp_forward_tolerance_example": forward_tolerance_example,
        "interpretation": (
            "finite examples reproduce synthetic source/assumed-input perturbations; "
            "gradient is an exact local derivative, not a finite-change identity"
        ),
        "csv": csv_path.name,
    }
    (output_dir / "cpiv_r11_carry_forward_sensitivity.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(write_outputs(args.output), indent=2))


if __name__ == "__main__":
    main()
