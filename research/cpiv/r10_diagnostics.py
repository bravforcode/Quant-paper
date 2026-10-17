"""Reproducible synthetic diagnostics for proposed CPIV methods note R10.

All experiments are synthetic. No network access, historical quotes, or
investment outcomes are used. The simulation is a measurement stress test,
not a calibrated model of market quote errors.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any

from research.cpiv import build_demo as demo

SEEDS = (20261009, 20261010, 20261011)
REPLICATES_PER_SEED = 100
UNCERTAINTY_SEEDS = (20261012, 20261013, 20261014)
UNCERTAINTY_REPLICATES_PER_SEED = 2000
UNCERTAINTY_PRICE_SDS = (0.02, 0.02)
UNCERTAINTY_SPOT_SD = 0.02
UNCERTAINTY_RATE_SD = 0.001
UNCERTAINTY_YIELD_SD = 0.001
HETERO_ASSIGNMENT_SEED = 20261015
AMERICAN_STEPS = (400, 800, 1600, 3200, 6400)
AMERICAN_SUCCESSIVE_CPIV_TOLERANCE_PP = 0.001
UNIVERSE_SIZES = (10, 50)
SIGNAL_FAMILIES = (
    "equally_spaced",
    "clustered_near_zero",
    "near_ties",
    "two_clusters_cutoff",
    "concave_magnitude",
)
NOISE_FAMILIES = (
    "bounded_uniform",
    "gaussian",
    "contaminated_gaussian",
    "heteroskedastic_increasing",
    "heteroskedastic_decreasing",
    "heteroskedastic_random_assignment",
    "call_put_correlated_rho_0.8_fixed_leg_sd",
    "common_additive_cpiv_shock",
)
NOISE_SDS_PP = (0.25, 0.50, 1.00)
VEGA_FLOOR_USD_PER_DECIMAL_IV = 1e-6
NORMALIZED_VEGA_THRESHOLDS = (1e-8, 1e-7, 1e-6)
LOCAL_GRID_CARRY_PAIRS = ((0.00, 0.00), (0.05, 0.02))
LOCAL_GRID_SPREADS_PP = (-2.0, -1.0, -0.5, 0.5, 1.0, 2.0)
LOCAL_GRID_QUADRATURE_INTERVALS = 2000
LOCAL_GRID_QUADRATURE_CHECKS = (1000, 2000, 4000)
RANKING_METRICS = (
    "mean_pairwise_inversion_fraction",
    "mean_spearman_rank_correlation",
    "mean_top_bottom_membership_turnover",
    "mean_sign_accuracy",
)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _simpson(function: Any, low: float, high: float, intervals: int = 2000) -> float:
    if intervals < 2 or intervals % 2:
        raise ValueError("Simpson interval count must be a positive even integer")
    if low == high:
        return 0.0
    sign = 1.0 if high > low else -1.0
    a, b = (low, high) if high > low else (high, low)
    width = (b - a) / intervals
    total = function(a) + function(b)
    total += 4.0 * sum(function(a + i * width) for i in range(1, intervals, 2))
    total += 2.0 * sum(function(a + i * width) for i in range(2, intervals, 2))
    return sign * total * width / 3.0


def _vega_decimal(spot: float, strike: float, days: int, rate: float,
                  dividend_yield: float, sigma: float) -> float:
    return 100.0 * demo.bs_vega_per_vol_point(
        spot, strike, days, rate, dividend_yield, sigma
    )


def average_vega(spot: float, strike: float, days: int, rate: float,
                dividend_yield: float, sigma_put: float,
                sigma_call: float) -> float:
    """Average vega along the IV segment, including its zero-width limit."""
    if sigma_put <= 0 or sigma_call <= 0:
        raise ValueError("both implied volatilities must be positive")
    if sigma_put == sigma_call:
        return _vega_decimal(
            spot, strike, days, rate, dividend_yield, sigma_put
        )
    return _simpson(
        lambda t: _vega_decimal(
            spot, strike, days, rate, dividend_yield,
            sigma_put+t*(sigma_call-sigma_put),
        ),
        0.0,
        1.0,
        intervals=LOCAL_GRID_QUADRATURE_INTERVALS,
    )


def bsm_identity_grid() -> tuple[list[dict[str, float]], float]:
    rows: list[dict[str, float]] = []
    for spot_ratio in (0.8, 1.0, 1.2):
        for days in (7, 30, 90, 365):
            for rate, q in ((0.00, 0.00), (0.05, 0.02)):
                strike, spot = 100.0, 100.0 * spot_ratio
                sigma_put, sigma_call = 0.20, 0.235
                call = demo.bs_price("call", spot, strike, days, rate, q, sigma_call)
                put = demo.bs_price("put", spot, strike, days, rate, q, sigma_put)
                residual = demo.parity_residual(call, put, spot, strike, days, rate, q)
                mean_vega = average_vega(
                    spot, strike, days, rate, q, sigma_put, sigma_call
                )
                integral = _simpson(
                    lambda sigma, spot=spot, strike=strike, days=days, rate=rate, q=q:
                        _vega_decimal(spot, strike, days, rate, q, sigma),
                    sigma_put,
                    sigma_call,
                )
                rows.append({
                    "spot_strike_ratio": spot_ratio,
                    "days_to_expiry": days,
                    "rate": rate,
                    "effective_yield": q,
                    "sigma_put": sigma_put,
                    "sigma_call": sigma_call,
                    "residual_usd": residual,
                    "integrated_vega_usd": integral,
                    "average_vega_usd_per_decimal_iv": mean_vega,
                    "residual_from_average_vega_usd":
                        (sigma_call-sigma_put)*mean_vega,
                    "absolute_identity_error_usd": abs(residual - integral),
                })
    return rows, max(row["absolute_identity_error_usd"] for row in rows)


def local_approximation_grid() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ratio in (0.8, 0.9, 1.0, 1.1, 1.2):
        for days in (7, 30, 90, 365):
            for sigma_bar in (0.10, 0.20, 0.40):
                for spread_pp in LOCAL_GRID_SPREADS_PP:
                    for rate, q in LOCAL_GRID_CARRY_PAIRS:
                        spot, strike = 100.0 * ratio, 100.0
                        call_iv = sigma_bar + spread_pp / 200.0
                        put_iv = sigma_bar - spread_pp / 200.0
                        if min(call_iv, put_iv) <= 0:
                            continue
                        call = demo.bs_price("call", spot, strike, days, rate, q, call_iv)
                        put = demo.bs_price("put", spot, strike, days, rate, q, put_iv)
                        direct_residual = demo.parity_residual(
                            call, put, spot, strike, days, rate, q
                        )
                        quadrature = {
                            intervals: _simpson(
                                lambda sigma, spot=spot, strike=strike, days=days,
                                rate=rate, q=q: _vega_decimal(
                                    spot, strike, days, rate, q, sigma
                                ),
                                put_iv,
                                call_iv,
                                intervals=intervals,
                            )
                            for intervals in LOCAL_GRID_QUADRATURE_CHECKS
                        }
                        integrated_residual = quadrature[LOCAL_GRID_QUADRATURE_INTERVALS]
                        normalized_scale = max(
                            spot * math.exp(-q * days / 365.0),
                            strike * math.exp(-rate * days / 365.0),
                        )
                        vegas = {
                            "midpoint": _vega_decimal(
                                spot, strike, days, rate, q, sigma_bar
                            ),
                            "put_endpoint": _vega_decimal(
                                spot, strike, days, rate, q, put_iv
                            ),
                            "call_endpoint": _vega_decimal(
                                spot, strike, days, rate, q, call_iv
                            ),
                        }
                        approximations_by_reference = {
                            key: (100.0 * integrated_residual / value if value > 0 else None)
                            for key, value in vegas.items()
                        }
                        errors_by_reference = {
                            key: (abs(value-spread_pp) if value is not None else None)
                            for key, value in approximations_by_reference.items()
                        }
                        normalized_vega = vegas["midpoint"] / normalized_scale
                        row_base = {
                            "spot_strike_ratio": ratio,
                            "spot_usd": spot,
                            "strike_usd": strike,
                            "days_to_expiry": days,
                            "reference_iv_decimal": sigma_bar,
                            "sigma_call_decimal": call_iv,
                            "sigma_put_decimal": put_iv,
                            "target_cpiv_pp": spread_pp,
                            "rate": rate,
                            "effective_yield": q,
                            "carry_pair_id": f"r{rate:.2f}_q{q:.2f}",
                            "quadrature_rule": "composite Simpson",
                            "quadrature_intervals": LOCAL_GRID_QUADRATURE_INTERVALS,
                            "direct_price_residual_usd": direct_residual,
                            "integrated_vega_residual_usd": integrated_residual,
                            "direct_residual_numerical_gap_usd": abs(
                                direct_residual-integrated_residual
                            ),
                            "quadrature_1000_vs_2000_gap_usd": abs(
                                quadrature[1000]-quadrature[2000]
                            ),
                            "quadrature_2000_vs_4000_gap_usd": abs(
                                quadrature[2000]-quadrature[4000]
                            ),
                            "vega_midpoint_usd_per_decimal_iv": vegas["midpoint"],
                            "vega_put_endpoint_usd_per_decimal_iv": vegas["put_endpoint"],
                            "vega_call_endpoint_usd_per_decimal_iv": vegas["call_endpoint"],
                            "normalized_midpoint_vega": normalized_vega,
                            "local_approximation_midpoint_pp":
                                approximations_by_reference["midpoint"],
                            "local_approximation_put_endpoint_pp":
                                approximations_by_reference["put_endpoint"],
                            "local_approximation_call_endpoint_pp":
                                approximations_by_reference["call_endpoint"],
                            "absolute_error_midpoint_pp": errors_by_reference["midpoint"],
                            "absolute_error_put_endpoint_pp":
                                errors_by_reference["put_endpoint"],
                            "absolute_error_call_endpoint_pp":
                                errors_by_reference["call_endpoint"],
                            "legacy_absolute_vega_guard_usd_per_decimal_iv":
                                VEGA_FLOOR_USD_PER_DECIMAL_IV,
                        }
                        if vegas["midpoint"] < VEGA_FLOOR_USD_PER_DECIMAL_IV:
                            rows.append({**row_base,
                                "local_approximation_pp": None,
                                "absolute_error_pp": None,
                                "status": "unresolved_by_configured_absolute_vega_guard",
                            })
                            continue
                        rows.append({**row_base,
                            "local_approximation_pp":
                                row_base["local_approximation_midpoint_pp"],
                            "absolute_error_pp":
                                row_base["absolute_error_midpoint_pp"],
                            "status": "resolved_by_configured_absolute_vega_guard",
                        })
    errors = [row["absolute_error_pp"] for row in rows
              if row["absolute_error_pp"] is not None]
    normalized = [row["normalized_midpoint_vega"] for row in rows]
    configuration_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        configuration_key = (
            row["spot_strike_ratio"],
            row["days_to_expiry"],
            row["reference_iv_decimal"],
            row["rate"],
            row["effective_yield"],
        )
        configuration_groups.setdefault(configuration_key, []).append(row)

    resolved_configuration_vegas: list[float] = []
    unresolved_configuration_vegas: list[float] = []
    for configuration_rows in configuration_groups.values():
        if len(configuration_rows) != len(LOCAL_GRID_SPREADS_PP):
            raise ValueError("unexpected spread-cell count for grid configuration")
        statuses = {row["status"] for row in configuration_rows}
        values = {row["normalized_midpoint_vega"] for row in configuration_rows}
        if len(statuses) != 1 or len(values) != 1:
            raise ValueError("normalized midpoint vega must be spread-invariant")
        value = float(next(iter(values)))
        if not math.isfinite(value):
            raise ValueError("normalized midpoint vega is non-finite")
        status = next(iter(statuses))
        if status == "resolved_by_configured_absolute_vega_guard":
            resolved_configuration_vegas.append(value)
        elif status == "unresolved_by_configured_absolute_vega_guard":
            unresolved_configuration_vegas.append(value)
        else:
            raise ValueError(f"unexpected grid status: {status}")

    resolved_configuration_vegas.sort()
    unresolved_configuration_vegas.sort()
    if not resolved_configuration_vegas or not unresolved_configuration_vegas:
        raise ValueError("grid must contain resolved and unresolved configurations")
    endpoint_errors = {
        name: [row[key] for row in rows]
        for name, key in (
            ("midpoint", "absolute_error_midpoint_pp"),
            ("put_endpoint", "absolute_error_put_endpoint_pp"),
            ("call_endpoint", "absolute_error_call_endpoint_pp"),
        )
    }
    summary: dict[str, Any] = {
        "n": len(rows),
        "configuration_n": len(configuration_groups),
        "spread_cells_per_configuration": len(LOCAL_GRID_SPREADS_PP),
        "resolved_n": len(errors),
        "unresolved_low_vega_n": len(rows)-len(errors),
        "p95_quantile_method": "nearest_rank",
        "p95_order_statistic_index_1_based": math.ceil(0.95 * len(errors)),
        "endpoint_error_aggregation": "separate_by_reference_not_pooled",
        "legacy_absolute_vega_guard_usd_per_decimal_iv":
            VEGA_FLOOR_USD_PER_DECIMAL_IV,
        "max_absolute_error_pp": max(errors),
        "median_absolute_error_pp": statistics.median(errors),
        "p95_absolute_error_pp": sorted(errors)[math.ceil(0.95 * len(errors)) - 1],
        "midpoint_reference_is_symmetric_by_design": True,
        "reference_error_summary_pp": {},
        "reference_error_summary_resolved_pp": {},
        "max_direct_residual_vs_integral_gap_usd": max(
            row["direct_residual_numerical_gap_usd"] for row in rows
        ),
        "max_simpson_1000_vs_2000_gap_usd": max(
            row["quadrature_1000_vs_2000_gap_usd"] for row in rows
        ),
        "max_simpson_2000_vs_4000_gap_usd": max(
            row["quadrature_2000_vs_4000_gap_usd"] for row in rows
        ),
        "normalized_vega_threshold_cell_counts": {
            str(threshold): sum(value >= threshold for value in normalized)
            for threshold in NORMALIZED_VEGA_THRESHOLDS
        },
        "unresolved_normalized_midpoint_vega": {
            "configuration_n": len(unresolved_configuration_vegas),
            "spread_cells_per_configuration": len(LOCAL_GRID_SPREADS_PP),
            "median": statistics.median(unresolved_configuration_vegas),
            "maximum": unresolved_configuration_vegas[-1],
        },
        "normalized_vega_guard_separation": {
            "resolved_configuration_n": len(resolved_configuration_vegas),
            "unresolved_configuration_n": len(unresolved_configuration_vegas),
            "minimum_resolved": resolved_configuration_vegas[0],
            "maximum_unresolved": unresolved_configuration_vegas[-1],
            "min_resolved_to_max_unresolved_ratio": (
                resolved_configuration_vegas[0]
                / unresolved_configuration_vegas[-1]
            ),
            "log10_separation": math.log10(
                resolved_configuration_vegas[0]
                / unresolved_configuration_vegas[-1]
            ),
        },
    }
    for name, values in endpoint_errors.items():
        finite = sorted(
            value for value in values
            if value is not None and math.isfinite(value)
        )
        summary["reference_error_summary_pp"][name] = {
            "n": len(finite),
            "p95_quantile_method": "nearest_rank",
            "p95_order_statistic_index_1_based": math.ceil(0.95*len(finite)),
            "median_abs_error": statistics.median(finite),
            "p95_abs_error": finite[math.ceil(0.95*len(finite))-1],
            "max_abs_error": max(finite),
        }
        resolved_values = sorted(
            row[{
                "midpoint": "absolute_error_midpoint_pp",
                "put_endpoint": "absolute_error_put_endpoint_pp",
                "call_endpoint": "absolute_error_call_endpoint_pp",
            }[name]]
            for row in rows
            if row["status"] == "resolved_by_configured_absolute_vega_guard"
            and row[{
                "midpoint": "absolute_error_midpoint_pp",
                "put_endpoint": "absolute_error_put_endpoint_pp",
                "call_endpoint": "absolute_error_call_endpoint_pp",
            }[name]] is not None
        )
        summary["reference_error_summary_resolved_pp"][name] = {
            "n": len(resolved_values),
            "p95_quantile_method": "nearest_rank",
            "p95_order_statistic_index_1_based": math.ceil(
                0.95*len(resolved_values)
            ),
            "median_abs_error": statistics.median(resolved_values),
            "p95_abs_error": resolved_values[
                math.ceil(0.95*len(resolved_values))-1
            ],
            "max_abs_error": max(resolved_values),
        }
    return rows, summary


def vega_scale_sensitivity() -> list[dict[str, Any]]:
    """Show nominal-scale dependence of the legacy guard and invariant ratios."""
    rows: list[dict[str, Any]] = []
    for ratio in (0.8, 0.9, 1.0, 1.1, 1.2):
        for days in (7, 30, 90, 365):
            for sigma in (0.10, 0.20, 0.40):
                for rate, q in LOCAL_GRID_CARRY_PAIRS:
                    spot, strike = 100.0*ratio, 100.0
                    vega = _vega_decimal(spot, strike, days, rate, q, sigma)
                    price_scale = max(
                        spot*math.exp(-q*days/365.0),
                        strike*math.exp(-rate*days/365.0),
                    )
                    for scale in (0.01, 1.0, 100.0):
                        scaled_vega = scale*vega
                        scaled_price_scale = scale*price_scale
                        rows.append({
                            "spot_strike_ratio": ratio,
                            "days_to_expiry": days,
                            "reference_iv_decimal": sigma,
                            "rate": rate,
                            "effective_yield": q,
                            "nominal_price_scale_factor": scale,
                            "absolute_vega_usd_per_decimal_iv": scaled_vega,
                            "price_scale_usd": scaled_price_scale,
                            "normalized_vega_per_decimal_iv":
                                scaled_vega/scaled_price_scale,
                            "legacy_absolute_guard_resolves":
                                scaled_vega >= VEGA_FLOOR_USD_PER_DECIMAL_IV,
                            "not_a_universal_resolution_threshold": True,
                        })
    return rows


def _classify_inversion_failure(option_type: str, price: float, spot: float,
                               strike: float, days: int, rate: float,
                               q: float) -> str:
    numeric = (price, spot, strike, rate, q)
    if not all(math.isfinite(value) for value in numeric) or spot <= 0 or strike <= 0 or days <= 0:
        return "invalid_inputs"
    lower, upper = demo.price_bounds(option_type, spot, strike, days, rate, q)
    if price < lower or price > upper:
        return "theoretical_bound_violation"
    if min(price-lower, upper-price) <= 1e-10:
        return "rejected_by_configured_absolute_near_bound_guard"
    low_iv, high_iv = 1e-8, demo.MAX_IV
    low_price = demo.bs_price(option_type, spot, strike, days, rate, q, low_iv)
    high_price = demo.bs_price(option_type, spot, strike, days, rate, q, high_iv)
    if price < low_price-1e-10 or price > high_price+1e-10:
        return "outside_configured_solver_bracket"
    return "numerical_nonconvergence_or_unclassified_solver_rejection"


def inversion_diagnostics() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rejected_generated_quotes = 0
    unexpectedly_accepted_invalid_prices = 0
    max_repricing_error = 0.0
    absolute_iv_errors: list[float] = []
    failure_counts: dict[str, int] = {}
    lower_bound_guard_usd = 1e-10
    for ratio in (0.8, 0.9, 1.0, 1.1, 1.2):
        for days in (7, 30, 90, 365):
            for sigma in (0.10, 0.20, 0.40):
                for option_type in ("call", "put"):
                    spot, strike, rate, q = ratio * 100.0, 100.0, 0.03, 0.01
                    price = demo.bs_price(option_type, spot, strike, days, rate, q, sigma)
                    lower_bound, upper_bound = demo.price_bounds(
                        option_type, spot, strike, days, rate, q
                    )
                    try:
                        recovered = demo.implied_volatility(
                            option_type, price, spot, strike, days, rate, q
                        )
                    except ValueError as exc:
                        rejected_generated_quotes += 1
                        failure_status = _classify_inversion_failure(
                            option_type, price, spot, strike, days, rate, q
                        )
                        failure_counts[failure_status] = (
                            failure_counts.get(failure_status, 0)+1
                        )
                        rows.append({
                            "option_type": option_type,
                            "spot_strike_ratio": ratio,
                            "days_to_expiry": days,
                            "target_iv": sigma,
                            "theoretical_price_usd": price,
                            "lower_bound_distance_usd": price-lower_bound,
                            "upper_bound_distance_usd": upper_bound-price,
                            "recovered_iv": math.nan,
                            "absolute_iv_error": math.nan,
                            "absolute_repricing_error_usd": math.nan,
                            "failure_status": failure_status,
                            "solver_message": str(exc),
                            "configured_absolute_near_bound_guard_usd":
                                lower_bound_guard_usd,
                            "status": failure_status,
                        })
                        continue
                    repriced = demo.bs_price(
                        option_type, spot, strike, days, rate, q, recovered
                    )
                    error = abs(repriced - price)
                    iv_error = abs(recovered-sigma)
                    absolute_iv_errors.append(iv_error)
                    max_repricing_error = max(max_repricing_error, error)
                    rows.append({
                        "option_type": option_type,
                        "spot_strike_ratio": ratio,
                        "days_to_expiry": days,
                        "target_iv": sigma,
                        "theoretical_price_usd": price,
                        "lower_bound_distance_usd": price-lower_bound,
                        "upper_bound_distance_usd": upper_bound-price,
                        "recovered_iv": recovered,
                        "absolute_iv_error": iv_error,
                        "absolute_repricing_error_usd": error,
                        "failure_status": "none",
                        "configured_absolute_near_bound_guard_usd":
                            lower_bound_guard_usd,
                        "status": "ok",
                    })
    rejected = 0
    for option_type in ("call", "put"):
        low, high = demo.price_bounds(option_type, 100.0, 100.0, 30, 0.03, 0.01)
        for invalid_price in (low, high, low - 0.01, high + 0.01, math.nan):
            try:
                demo.implied_volatility(option_type, invalid_price, 100.0, 100.0,
                                        30, 0.03, 0.01)
            except ValueError:
                rejected += 1
            else:
                unexpectedly_accepted_invalid_prices += 1
    summary = {
        "generated_quote_cases": len(rows),
        "contract_configurations": 60,
        "option_leg_prices": 120,
        "successfully_inverted_generated_quotes": sum(row["status"] == "ok" for row in rows),
        "rejected_generated_quotes": rejected_generated_quotes,
        "rejected_by_status": failure_counts,
        "failure_denominator": len(rows),
        "configured_iv_bracket": [1e-8, demo.MAX_IV],
        "bisection_iterations": 64,
        "rejected_invalid_price_cases": rejected,
        "unexpectedly_accepted_invalid_price_cases": unexpectedly_accepted_invalid_prices,
        "max_absolute_repricing_error_usd": max_repricing_error,
        "max_absolute_iv_recovery_error_decimal": max(absolute_iv_errors),
        "p95_absolute_iv_recovery_error_decimal": sorted(absolute_iv_errors)[
            math.ceil(0.95*len(absolute_iv_errors))-1
        ],
        "absolute_iv_recovery_error_denominator": len(absolute_iv_errors),
        "near_bound_failure_attribution": (
            "configured absolute guard; not attributed to floating-point resolution"
        ),
        "input_clipping": False,
    }
    return rows, summary


def jarrow_rudd_american_put(spot: float, strike: float, days: int,
                            rate: float, q: float, sigma: float,
                            steps: int) -> float:
    """American put under equal-probability Jarrow-Rudd binomial tree."""
    if steps < 1:
        raise ValueError("steps must be positive")
    maturity = days / 365.0
    dt = maturity / steps
    up = math.exp((rate - q - 0.5 * sigma * sigma) * dt + sigma * math.sqrt(dt))
    down = math.exp((rate - q - 0.5 * sigma * sigma) * dt - sigma * math.sqrt(dt))
    discount = math.exp(-rate * dt)
    values = [
        max(strike - spot * up**j * down ** (steps - j), 0.0)
        for j in range(steps + 1)
    ]
    for time_step in range(steps - 1, -1, -1):
        for up_moves in range(time_step + 1):
            continuation = discount * 0.5 * (values[up_moves] + values[up_moves + 1])
            node_spot = spot * up**up_moves * down ** (time_step - up_moves)
            values[up_moves] = max(continuation, strike - node_spot, 0.0)
    return values[0]


def american_convergence() -> list[dict[str, Any]]:
    rows = []
    steps_grid = AMERICAN_STEPS
    reference_call = demo.bs_price("call", 100.0, 100.0, 30, 0.05, 0.0, 0.20)
    for method in ("CRR", "Jarrow-Rudd"):
        previous_cpiv: float | None = None
        for steps in steps_grid:
            put = (
                demo.american_price("put", 100.0, 100.0, 30, 0.05, 0.0, 0.20, steps)
                if method == "CRR"
                else jarrow_rudd_american_put(100.0, 100.0, 30, 0.05, 0.0,
                                              0.20, steps)
            )
            put_iv = demo.implied_volatility("put", put, 100.0, 100.0, 30, 0.05, 0.0)
            cpiv = 100.0 * (0.20 - put_iv)
            change = None if previous_cpiv is None else abs(cpiv-previous_cpiv)
            rows.append({
                "method": method,
                "steps": steps,
                "american_put_usd": put,
                "european_call_usd": reference_call,
                "implied_cpiv_pp": cpiv,
                "absolute_change_from_previous_doubled_grid_pp": change,
                "meets_selected_successive_change_threshold": (
                    None if change is None else
                    change < AMERICAN_SUCCESSIVE_CPIV_TOLERANCE_PP
                ),
                "successive_change_tolerance_pp":
                    AMERICAN_SUCCESSIVE_CPIV_TOLERANCE_PP,
                "note": "numerical American put; exact BSM European call",
            })
            previous_cpiv = cpiv
    return rows


def carry_and_spot_diagnostics() -> tuple[list[dict[str, float]], list[dict[str, float]]]:
    carry_rows: list[dict[str, float]] = []
    for q_true in (-0.02, -0.01, 0.0, 0.01, 0.02, 0.05):
        call = demo.bs_price("call", 100, 100, 30, 0.0, q_true, 0.20)
        put = demo.bs_price("put", 100, 100, 30, 0.0, q_true, 0.20)
        call_iv = demo.implied_volatility("call", call, 100, 100, 30, 0.0, 0.0)
        put_iv = demo.implied_volatility("put", put, 100, 100, 30, 0.0, 0.0)
        carry_rows.append({
            "true_effective_yield": q_true,
            "assumed_effective_yield": 0.0,
            "cpiv_pp": 100.0 * (call_iv - put_iv),
        })
    spot_rows: list[dict[str, float]] = []
    for offset in (-0.25, -0.10, -0.05, -0.02, 0.02, 0.05, 0.10, 0.25):
        # Quotes use S=100. Inversion uses a stale spot 100+offset.
        call = demo.bs_price("call", 100, 100, 30, 0.0, 0.0, 0.20)
        put = demo.bs_price("put", 100, 100, 30, 0.0, 0.0, 0.20)
        stale_spot = 100.0 + offset
        try:
            call_iv = demo.implied_volatility("call", call, stale_spot, 100, 30, 0.0, 0.0)
            put_iv = demo.implied_volatility("put", put, stale_spot, 100, 30, 0.0, 0.0)
            cpiv = 100.0 * (call_iv - put_iv)
            status = "ok"
        except ValueError:
            cpiv, status = math.nan, "outside_strict_bounds_or_bracket"
        spot_rows.append({
            "stale_spot_minus_quote_spot_usd": offset,
            "quote_spot_usd": 100.0,
            "inversion_spot_usd": stale_spot,
            "cpiv_pp": cpiv,
            "status": status,
        })
    return carry_rows, spot_rows


def quote_interval_diagnostics() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for half_spread in (0.01, 0.02, 0.05, 0.10, 0.25):
        intervals: list[tuple[float, float]] = []
        valid = 0
        for index in range(10):
            call_sigma = 0.16 + 0.01 * index
            put_sigma = 0.20
            call = demo.bs_price("call", 100, 100, 30, 0, 0, call_sigma)
            put = demo.bs_price("put", 100, 100, 30, 0, 0, put_sigma)
            try:
                lo = demo.implied_volatility("call", call-half_spread, 100, 100, 30, 0, 0) - (
                    demo.implied_volatility("put", put+half_spread, 100, 100, 30, 0, 0)
                )
                hi = demo.implied_volatility("call", call+half_spread, 100, 100, 30, 0, 0) - (
                    demo.implied_volatility("put", put-half_spread, 100, 100, 30, 0, 0)
                )
                intervals.append((lo, hi))
                valid += 1
            except ValueError:
                continue
        eligible_pair_count = len(intervals) * (len(intervals) - 1) // 2
        all_pair_count = 10*9//2
        nonoverlap_count = sum(
            1 for i in range(len(intervals)) for j in range(i + 1, len(intervals))
            if intervals[i][1] < intervals[j][0] or intervals[j][1] < intervals[i][0]
        )
        sign_resolved_count = sum(1 for lo, hi in intervals if lo > 0 or hi < 0)
        widths = [hi - lo for lo, hi in intervals]
        rows.append({
            "quote_half_spread_usd_per_underlying_unit": half_spread,
            "synthetic_pairs_total": 10,
            "four_endpoint_invertible_pair_count": valid,
            "four_endpoint_invertible_pair_fraction": valid / 10.0,
            "sign_resolved_pair_count": sign_resolved_count,
            "sign_resolution_denominator_valid_pairs": valid,
            "sign_resolved_pair_fraction":
                sign_resolved_count/valid if valid else math.nan,
            "median_quote_implied_interval_width_pp":
                100.0 * statistics.median(widths) if widths else math.nan,
            "nonoverlapping_unordered_pair_count": nonoverlap_count,
            "nonoverlap_eligible_pair_denominator": eligible_pair_count,
            "nonoverlap_all_possible_pair_denominator": all_pair_count,
            "nonoverlap_fraction_of_eligible_pairs": (
                nonoverlap_count/eligible_pair_count if eligible_pair_count else math.nan
            ),
            "nonoverlap_fraction_of_all_possible_pairs": nonoverlap_count/all_pair_count,
            "interval_comparison_rule": "strict non-overlap; touching endpoints count as overlap",
            "interpretation": (
                "synthetic quote-implied endpoint range; not statistical coverage, "
                "a confidence interval, or an arbitrage bound"
            ),
        })
    return rows


def _bsm_input_gradient(option_type: str, spot: float, strike: float, days: int,
                        rate: float, q: float, sigma: float) -> dict[str, float]:
    t = days/365.0
    root_t = math.sqrt(t)
    d1 = (math.log(spot/strike)+(rate-q+0.5*sigma*sigma)*t)/(sigma*root_t)
    d2 = d1-sigma*root_t
    pdf1 = math.exp(-0.5*d1*d1)/math.sqrt(2.0*math.pi)
    pdf2 = math.exp(-0.5*d2*d2)/math.sqrt(2.0*math.pi)
    cdf1, cdf2 = demo._normal_cdf(d1), demo._normal_cdf(d2)
    disc_s, disc_k = spot*math.exp(-q*t), strike*math.exp(-rate*t)
    d1_dt = (
        -math.log(spot/strike)+(rate-q+0.5*sigma*sigma)*t
    )/(2.0*sigma*t**1.5)
    d2_dt = d1_dt-sigma/(2.0*root_t)
    if option_type == "call":
        d_t = (-q*disc_s*cdf1 + disc_s*pdf1*d1_dt
               + rate*disc_k*cdf2-disc_k*pdf2*d2_dt)
        return {
            "spot": math.exp(-q*t)*cdf1,
            "strike": -math.exp(-rate*t)*cdf2,
            "maturity": d_t,
            "rate": strike*t*math.exp(-rate*t)*cdf2,
            "effective_yield": -spot*t*math.exp(-q*t)*cdf1,
        }
    d_t = (-rate*disc_k*demo._normal_cdf(-d2)-disc_k*pdf2*d2_dt
           + q*disc_s*demo._normal_cdf(-d1)+disc_s*pdf1*d1_dt)
    return {
        "spot": math.exp(-q*t)*(cdf1-1.0),
        "strike": math.exp(-rate*t)*demo._normal_cdf(-d2),
        "maturity": d_t,
        "rate": -strike*t*math.exp(-rate*t)*demo._normal_cdf(-d2),
        "effective_yield": spot*t*math.exp(-q*t)*demo._normal_cdf(-d1),
    }


def paired_cpiv_input_gradient(spot: float, strike: float, days: int,
                               rate: float, q: float,
                               sigma_call: float,
                               sigma_put: float) -> dict[str, float]:
    """First-order CPIV gradient using each leg's own IV and Greeks."""
    vega_call = _vega_decimal(spot, strike, days, rate, q, sigma_call)
    vega_put = _vega_decimal(spot, strike, days, rate, q, sigma_put)
    if min(vega_call, vega_put) <= 0:
        raise ValueError("paired IV sensitivity is unresolved at zero leg vega")
    call_gradient = _bsm_input_gradient(
        "call", spot, strike, days, rate, q, sigma_call
    )
    put_gradient = _bsm_input_gradient(
        "put", spot, strike, days, rate, q, sigma_put
    )
    result = {
        "call_price": 100.0/vega_call,
        "put_price": -100.0/vega_put,
    }
    for name in ("spot", "strike", "maturity", "rate", "effective_yield"):
        result[name] = -100.0*(
            call_gradient[name]/vega_call-put_gradient[name]/vega_put
        )
    return result


def uncertainty_scenarios() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    spot, strike, days, rate, q = 100.0, 100.0, 30, 0.03, 0.01
    sd_call, sd_put = UNCERTAINTY_PRICE_SDS
    input_sds = {
        "call_price": sd_call,
        "put_price": sd_put,
        "spot": UNCERTAINTY_SPOT_SD,
        "strike": 0.0,
        "maturity": 0.0,
        "rate": UNCERTAINTY_RATE_SD,
        "effective_yield": UNCERTAINTY_YIELD_SD,
    }
    for iv_case, (sigma_call, sigma_put) in enumerate(((0.20, 0.20), (0.24, 0.20))):
        call0 = demo.bs_price("call", spot, strike, days, rate, q, sigma_call)
        put0 = demo.bs_price("put", spot, strike, days, rate, q, sigma_put)
        gradient = paired_cpiv_input_gradient(
            spot, strike, days, rate, q, sigma_call, sigma_put
        )
        for rho_cp in (0.0, 0.5, 0.9):
            variance = sum((gradient[key]*sd)**2 for key, sd in input_sds.items())
            variance += 2.0*rho_cp*gradient["call_price"]*gradient["put_price"]*sd_call*sd_put
            delta_sd = math.sqrt(max(0.0, variance))
            simulated: list[float] = []
            unresolved = 0
            for seed in UNCERTAINTY_SEEDS:
                rng = random.Random(seed+100*iv_case)
                for _ in range(UNCERTAINTY_REPLICATES_PER_SEED):
                    z_call, z_independent = rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0)
                    error_call = sd_call*z_call
                    error_put = sd_put*(rho_cp*z_call+math.sqrt(1.0-rho_cp*rho_cp)*z_independent)
                    spot_obs = spot+rng.gauss(0.0, UNCERTAINTY_SPOT_SD)
                    rate_obs = rate+rng.gauss(0.0, UNCERTAINTY_RATE_SD)
                    q_obs = q+rng.gauss(0.0, UNCERTAINTY_YIELD_SD)
                    try:
                        call_iv_obs = demo.implied_volatility(
                            "call", call0+error_call, spot_obs, strike, days,
                            rate_obs, q_obs,
                        )
                        put_iv_obs = demo.implied_volatility(
                            "put", put0+error_put, spot_obs, strike, days,
                            rate_obs, q_obs,
                        )
                    except ValueError:
                        unresolved += 1
                        continue
                    simulated.append(100.0*(call_iv_obs-put_iv_obs))
            simulation_sd = statistics.stdev(simulated) if len(simulated) > 1 else math.nan
            simulation_sd_mcse = (
                simulation_sd / math.sqrt(2.0 * (len(simulated) - 1))
                if len(simulated) > 1 else math.nan
            )
            rows.append({
                "iv_case": "equal_iv" if iv_case == 0 else "unequal_iv",
                "sigma_call_decimal": sigma_call,
                "sigma_put_decimal": sigma_put,
                "call_vega_usd_per_decimal_iv":
                    _vega_decimal(spot, strike, days, rate, q, sigma_call),
                "put_vega_usd_per_decimal_iv":
                    _vega_decimal(spot, strike, days, rate, q, sigma_put),
                "call_put_price_error_correlation": rho_cp,
                "first_order_cpiv_sd_pp": delta_sd,
                "direct_perturbation_cpiv_sd_pp": simulation_sd,
                "direct_perturbation_sd_mcse_normal_theory_pp": simulation_sd_mcse,
                "direct_perturbation_sd_mcse_method": (
                    "s/sqrt(2*(n-1)); normal-theory approximation"
                ),
                "direct_perturbation_mean_cpiv_pp":
                    statistics.fmean(simulated) if simulated else math.nan,
                "baseline_cpiv_pp": 100.0*(sigma_call-sigma_put),
                "simulation_vs_delta_sd_difference_pp": simulation_sd-delta_sd,
                "replicate_seed_set": ";".join(map(str, UNCERTAINTY_SEEDS)),
                "replicates_per_seed": UNCERTAINTY_REPLICATES_PER_SEED,
                "replicates_total": len(simulated)+unresolved,
                "resolved_replicates": len(simulated),
                "unresolved_replicates": unresolved,
                "gradient_inputs": "C,P,S,K,T,r,q; K and T held fixed in this scenario",
                "status": (
                    "illustrative synthetic perturbations; not a market SE or CI"
                ),
            })
    return rows


def _signals(n: int, family: str) -> list[float]:
    x = [-1.0 + 2.0*i/(n-1) for i in range(n)]
    if family == "equally_spaced":
        return x
    if family == "clustered_near_zero":
        return [value**3 for value in x]
    if family == "near_ties":
        return [value * 0.03 for value in x]
    if family == "two_clusters_cutoff":
        midpoint = n // 2
        return [(-1.0 + 0.02*i/n) if i < midpoint else (1.0 + 0.02*i/n)
                for i in range(n)]
    if family == "concave_magnitude":
        return [math.copysign(math.sqrt(abs(value)), value) for value in x]
    raise ValueError(f"unknown signal family: {family}")


def _noises(rng: random.Random, signals: list[float], sd: float,
            family: str) -> list[float]:
    n = len(signals)
    if family == "bounded_uniform":
        bound = math.sqrt(3.0) * sd
        return [rng.uniform(-bound, bound) for _ in signals]
    if family == "gaussian":
        return [rng.gauss(0.0, sd) for _ in signals]
    if family == "contaminated_gaussian":
        base = sd / math.sqrt(0.95 + 0.05 * 25.0)
        return [rng.gauss(0.0, base * (5.0 if rng.random() < 0.05 else 1.0))
                for _ in signals]
    if family in {
        "heteroskedastic_increasing",
        "heteroskedastic_decreasing",
        "heteroskedastic_random_assignment",
    }:
        factors = [0.5 + i / max(1, n-1) for i in range(n)]
        if family == "heteroskedastic_decreasing":
            factors.reverse()
        elif family == "heteroskedastic_random_assignment":
            rng.shuffle(factors)
        rms = math.sqrt(sum(f*f for f in factors) / n)
        return [rng.gauss(0.0, sd * factor/rms) for factor in factors]
    if family == "call_put_correlated_rho_0.8_fixed_leg_sd":
        rho = 0.8
        result = []
        for _ in signals:
            call_z = rng.gauss(0.0, 1.0)
            independent_z = rng.gauss(0.0, 1.0)
            put_z = rho * call_z + math.sqrt(1.0-rho*rho) * independent_z
            result.append(sd * (call_z-put_z))
        return result
    if family == "common_additive_cpiv_shock":
        common = rng.gauss(0.0, sd)
        return [common] * n
    raise ValueError(f"unknown noise family: {family}")


def _inversion_count(permutation: list[int]) -> int:
    tree = [0] * (len(permutation) + 1)
    inversions = 0
    for value in reversed(permutation):
        index = value + 1
        smaller = 0
        cursor = index - 1
        while cursor:
            smaller += tree[cursor]
            cursor -= cursor & -cursor
        inversions += smaller
        cursor = index
        while cursor < len(tree):
            tree[cursor] += 1
            cursor += cursor & -cursor
    return inversions


def _wilson(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    p = successes/n
    denom = 1.0 + z*z/n
    center = (p + z*z/(2*n))/denom
    radius = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))/denom
    low = 0.0 if successes == 0 else max(0.0, center-radius)
    high = 1.0 if successes == n else min(1.0, center+radius)
    return low, high


def _mean_se_ci(values: list[float]) -> tuple[float, float, float]:
    mean = statistics.fmean(values)
    se = statistics.stdev(values)/math.sqrt(len(values)) if len(values) > 1 else math.nan
    return mean, se, (mean-1.959963984540054*se, mean+1.959963984540054*se)


def rank_sensitivity(
    replicates_per_seed: int = REPLICATES_PER_SEED,
    *,
    seeds: tuple[int, ...] = SEEDS,
    noise_sds: tuple[float, ...] = NOISE_SDS_PP,
    noise_families: tuple[str, ...] = NOISE_FAMILIES,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if replicates_per_seed < 1:
        raise ValueError("replicates_per_seed must be positive")
    output: list[dict[str, Any]] = []
    name_output: list[dict[str, Any]] = []
    contrast_output: list[dict[str, Any]] = []
    for n in UNIVERSE_SIZES:
        k = max(1, n//5)
        for signal_family in SIGNAL_FAMILIES:
            signals = _signals(n, signal_family)
            true_order = sorted(range(n), key=lambda i: (signals[i], i))
            true_rank = [0] * n
            for rank, index in enumerate(true_order):
                true_rank[index] = rank
            true_top = set(true_order[-k:])
            true_bottom = set(true_order[:k])
            for noise_family in noise_families:
                metrics_by_scale: dict[
                    float, list[tuple[float, float, float, float, bool, bool]]
                ] = {}
                for sd in noise_sds:
                    metrics: list[tuple[float, float, float, float, bool, bool]] = []
                    top_hits = [0] * n
                    bottom_hits = [0] * n
                    sign_hits = [0] * n
                    for seed in seeds:
                        rng = random.Random(seed + n*1000 + SIGNAL_FAMILIES.index(signal_family)*100
                                            + NOISE_FAMILIES.index(noise_family)*10)
                        for _ in range(replicates_per_seed):
                            noise = _noises(rng, signals, sd, noise_family)
                            observed = [
                                value + error
                                for value, error in zip(signals, noise, strict=True)
                            ]
                            noisy_order = sorted(range(n), key=lambda i: (observed[i], i))
                            permutation = [true_rank[i] for i in noisy_order]
                            inversion_fraction = _inversion_count(permutation) / (n*(n-1)/2)
                            squared_rank_diff = sum((rank-true_rank[index])**2
                                                    for rank, index in enumerate(noisy_order))
                            spearman = 1.0 - 6.0*squared_rank_diff/(n*(n*n-1))
                            observed_top = set(noisy_order[-k:])
                            observed_bottom = set(noisy_order[:k])
                            turnover = 1.0 - (len(true_top & observed_top) +
                                              len(true_bottom & observed_bottom))/(2.0*k)
                            signs_correct = sum(
                                (signals[i] > 0) == (observed[i] > 0) for i in range(n)
                            )/n
                            for index in observed_top:
                                top_hits[index] += 1
                            for index in observed_bottom:
                                bottom_hits[index] += 1
                            for index in range(n):
                                sign_hits[index] += int(
                                    (signals[index] > 0) == (observed[index] > 0)
                                )
                            metrics.append((inversion_fraction, spearman, turnover, signs_correct,
                                            inversion_fraction == 0.0, turnover > 0.0))
                    n_draws = len(metrics)
                    metrics_by_scale[sd] = metrics
                    exact_count = sum(item[4] for item in metrics)
                    changed_count = sum(item[5] for item in metrics)
                    exact_lo, exact_hi = _wilson(exact_count, n_draws)
                    changed_lo, changed_hi = _wilson(changed_count, n_draws)
                    noise_scale_semantics = (
                        "marginal standard deviation per call and put leg"
                        if noise_family == "call_put_correlated_rho_0.8_fixed_leg_sd"
                        else "target marginal CPIV-space standard deviation"
                    )
                    theoretical_cpiv_sd = (
                        sd*math.sqrt(2.0*(1.0-0.8))
                        if noise_family == "call_put_correlated_rho_0.8_fixed_leg_sd"
                        else sd
                    )
                    result_row: dict[str, Any] = {
                        "universe_n": n,
                        "signal_family": signal_family,
                        "noise_family": noise_family,
                        "configured_noise_scale_pp": sd,
                        "noise_scale_semantics": noise_scale_semantics,
                        "theoretical_marginal_cpiv_noise_sd_pp": theoretical_cpiv_sd,
                        "seeds": ";".join(map(str, seeds)),
                        "replicates_per_seed": replicates_per_seed,
                        "replicates_total": n_draws,
                        "mean_pairwise_inversion_fraction": statistics.fmean(x[0] for x in metrics),
                        "mean_spearman_rank_correlation": statistics.fmean(x[1] for x in metrics),
                        "mean_top_bottom_membership_turnover": statistics.fmean(
                            x[2] for x in metrics
                        ),
                        "mean_sign_accuracy": statistics.fmean(x[3] for x in metrics),
                        "exact_full_order_count": exact_count,
                        "event_rate_denominator_replicates": n_draws,
                        "probability_exact_full_order": exact_count/n_draws,
                        "exact_order_wilson95_low": exact_lo,
                        "exact_order_wilson95_high": exact_hi,
                        "probability_any_extreme_membership_change": changed_count/n_draws,
                        "membership_change_wilson95_low": changed_lo,
                        "membership_change_wilson95_high": changed_hi,
                        "simulation_status": (
                            "synthetic uncalibrated stress test; not market estimate"
                        ),
                    }
                    metric_fields = (
                        ("mean_pairwise_inversion_fraction", 0),
                        ("mean_spearman_rank_correlation", 1),
                        ("mean_top_bottom_membership_turnover", 2),
                        ("mean_sign_accuracy", 3),
                    )
                    for field, metric_index in metric_fields:
                        mean, se, (low, high) = _mean_se_ci(
                            [item[metric_index] for item in metrics]
                        )
                        result_row[field] = mean
                        result_row[f"{field}_mcse"] = se
                        result_row[f"{field}_mc95_low"] = low
                        result_row[f"{field}_mc95_high"] = high
                    output.append(result_row)
                    if n == 10:
                        for index, signal in enumerate(signals):
                            top_lo, top_hi = _wilson(top_hits[index], n_draws)
                            bottom_lo, bottom_hi = _wilson(bottom_hits[index], n_draws)
                            name_output.append({
                                "signal_family": signal_family,
                                "noise_family": noise_family,
                                "configured_noise_scale_pp": sd,
                                "noise_scale_semantics": noise_scale_semantics,
                                "theoretical_marginal_cpiv_noise_sd_pp": theoretical_cpiv_sd,
                                "synthetic_name_id": f"S{index+1:02d}",
                                "prescribed_signal_pp": signal,
                                "top_20pct_inclusion_probability": top_hits[index]/n_draws,
                                "top_20pct_wilson95_low": top_lo,
                                "top_20pct_wilson95_high": top_hi,
                                "bottom_20pct_inclusion_probability": bottom_hits[index]/n_draws,
                                "bottom_20pct_wilson95_low": bottom_lo,
                                "bottom_20pct_wilson95_high": bottom_hi,
                                "sign_accuracy_probability": sign_hits[index]/n_draws,
                                "replicates_total": n_draws,
                                "simulation_status": "synthetic uncalibrated; not market estimate",
                            })
                for lower_sd, upper_sd in zip(
                    noise_sds, noise_sds[1:], strict=False
                ):
                    lower_metrics = metrics_by_scale[lower_sd]
                    upper_metrics = metrics_by_scale[upper_sd]
                    if len(lower_metrics) != len(upper_metrics):
                        raise RuntimeError("paired scale draws do not share a denominator")
                    for field, metric_index in metric_fields:
                        differences = [
                            upper[metric_index]-lower[metric_index]
                            for lower, upper in zip(
                                lower_metrics, upper_metrics, strict=True
                            )
                        ]
                        mean, se, (low, high) = _mean_se_ci(differences)
                        contrast_output.append({
                            "universe_n": n,
                            "signal_family": signal_family,
                            "noise_family": noise_family,
                            "metric": field,
                            "lower_configured_scale_pp": lower_sd,
                            "upper_configured_scale_pp": upper_sd,
                            "paired_mean_difference_upper_minus_lower": mean,
                            "paired_difference_mcse": se,
                            "paired_difference_mc95_low": low,
                            "paired_difference_mc95_high": high,
                            "paired_replicate_denominator": len(differences),
                            "paired_seed_set": ";".join(map(str, seeds)),
                            "comparison_method": "within-seed common-random-number paired draws",
                            "status": "conditional synthetic contrast; not a market inference",
                        })
    return output, name_output, contrast_output


def render_r10_figures(output_dir: Path, approximation: list[dict[str, Any]],
                      ranking: list[dict[str, Any]],
                      american: list[dict[str, Any]]) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    generated: list[str] = []
    grouped: dict[float, list[float]] = {}
    for row in approximation:
        if row["absolute_error_pp"] is None:
            continue
        grouped.setdefault(abs(row["target_cpiv_pp"]), []).append(
            row["absolute_error_pp"]
        )
    spreads = sorted(grouped)
    medians = [statistics.median(grouped[value]) for value in spreads]
    p95 = [sorted(grouped[value])[math.ceil(0.95*len(grouped[value]))-1]
           for value in spreads]
    fig, axis = plt.subplots(figsize=(6.4, 3.6), constrained_layout=True)
    axis.plot(spreads, medians, marker="o", label="Median absolute error")
    axis.plot(spreads, p95, marker="s", label="95th percentile absolute error")
    axis.set_xlabel("Absolute CPIV spread (volatility percentage points)")
    axis.set_ylabel("Absolute error in local approximation (pp)")
    axis.set_title("Linearized residual-to-CPIV mapping: synthetic grid")
    axis.grid(alpha=0.25)
    axis.legend(frameon=False)
    for suffix in ("png", "svg"):
        path = output_dir / f"cpiv_r10_local_approximation_error.{suffix}"
        fig.savefig(path, dpi=180, bbox_inches="tight")
        generated.append(path.name)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.4), sharey=True,
                             constrained_layout=True)
    for axis, n in zip(axes, UNIVERSE_SIZES, strict=True):
        for family in SIGNAL_FAMILIES:
            selected = sorted(
                (row for row in ranking
                 if row["universe_n"] == n and row["signal_family"] == family
                  and row["noise_family"] == "gaussian"),
                key=lambda row: row["configured_noise_scale_pp"],
            )
            axis.plot(
                [row["configured_noise_scale_pp"] for row in selected],
                [row["mean_spearman_rank_correlation"] for row in selected],
                marker="o", label=family.replace("_", " "),
            )
        axis.set_title(f"Synthetic universe n={n}")
        axis.set_xlabel("Target Gaussian measurement-noise SD (pp)")
        axis.set_ylim(-0.05, 1.05)
        axis.set_xticks(NOISE_SDS_PP)
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Mean Spearman rank correlation")
    axes[1].legend(frameon=False, fontsize=7, loc="best")
    fig.suptitle("Rank concordance depends on signal spacing and noise")
    for suffix in ("png", "svg"):
        path = output_dir / f"cpiv_r10_rank_sensitivity.{suffix}"
        fig.savefig(path, dpi=180, bbox_inches="tight")
        generated.append(path.name)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(6.4, 3.6), constrained_layout=True)
    for method in ("CRR", "Jarrow-Rudd"):
        selected = sorted((row for row in american if row["method"] == method),
                          key=lambda row: row["steps"])
        axis.plot([row["steps"] for row in selected],
                  [row["implied_cpiv_pp"] for row in selected],
                  marker="o", label=method)
    axis.set_xscale("log", base=2)
    axis.set_xlabel("Tree steps (log scale)")
    axis.set_xticks(AMERICAN_STEPS, labels=[str(step) for step in AMERICAN_STEPS])
    axis.set_ylabel("Implied CPIV (pp)")
    axis.set_title("American-put numerical scheme comparison")
    axis.grid(alpha=0.25)
    axis.legend(frameon=False)
    for suffix in ("png", "svg"):
        path = output_dir / f"cpiv_r10_american_convergence.{suffix}"
        fig.savefig(path, dpi=180, bbox_inches="tight")
        generated.append(path.name)
    plt.close(fig)
    return generated


def write_r10_outputs(output_dir: Path, replicates_per_seed: int = REPLICATES_PER_SEED
                      ) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    identity, identity_error = bsm_identity_grid()
    approximation, approximation_summary = local_approximation_grid()
    inversion, inversion_summary = inversion_diagnostics()
    american = american_convergence()
    carry, spot = carry_and_spot_diagnostics()
    quote_intervals = quote_interval_diagnostics()
    uncertainty = uncertainty_scenarios()
    vega_scales = vega_scale_sensitivity()
    from research.cpiv.independent_bsm_crosscheck import run_checks

    independent_identity = run_checks()
    ranking, name_membership, paired_contrasts = rank_sensitivity(replicates_per_seed)
    figures = render_r10_figures(output_dir, approximation, ranking, american)
    scale_guard_summary = {
        str(scale): {
            "resolved_n": sum(
                row["legacy_absolute_guard_resolves"]
                for row in vega_scales
                if row["nominal_price_scale_factor"] == scale
            ),
            "configuration_denominator": sum(
                row["nominal_price_scale_factor"] == scale for row in vega_scales
            ),
        }
        for scale in (0.01, 1.0, 100.0)
    }
    file_rows = {
        "bsm_identity_grid.csv": identity,
        "local_approximation_grid.csv": approximation,
        "iv_inversion_roundtrips.csv": inversion,
        "american_put_convergence.csv": american,
        "carry_sensitivity.csv": carry,
        "spot_mismatch_sensitivity.csv": spot,
        "quote_implied_intervals.csv": quote_intervals,
        "illustrative_uncertainty_budget.csv": uncertainty,
        "vega_scale_sensitivity.csv": vega_scales,
        "rank_noise_sensitivity.csv": ranking,
        "rank_per_name_membership.csv": name_membership,
        "rank_scale_paired_contrasts.csv": paired_contrasts,
        "separately_coded_bsm_crosscheck.csv": independent_identity,
    }
    for filename, rows in file_rows.items():
        _write_csv(output_dir / filename, rows)
    from research.cpiv.near_bound_decimal_audit import write_audit

    near_bound_audit = write_audit(
        output_dir / "iv_inversion_roundtrips.csv",
        output_dir / "near_bound_decimal_audit.csv",
        output_dir / "near_bound_decimal_audit.json",
    )
    summary = {
        "status": "synthetic_methods_diagnostics_only",
        "market_data_used": False,
        "trading_or_alpha_claim": False,
        "seeds": SEEDS,
        "replicates_per_seed": replicates_per_seed,
        "ranking_total_replicates": (
            replicates_per_seed*len(SEEDS)*len(UNIVERSE_SIZES)
            *len(SIGNAL_FAMILIES)*len(NOISE_FAMILIES)*len(NOISE_SDS_PP)
        ),
        "identity_grid": {"cases": len(identity), "max_abs_error_usd": identity_error},
        "local_approximation_grid": approximation_summary,
        "absolute_vega_guard_nominal_scale_sensitivity": scale_guard_summary,
        "iv_inversion": inversion_summary,
        "american_put": {
            "steps": AMERICAN_STEPS,
            "methods": ["CRR", "Jarrow-Rudd"],
            "successive_cpiv_change_tolerance_pp":
                AMERICAN_SUCCESSIVE_CPIV_TOLERANCE_PP,
            "claim": (
                "successive-grid change diagnostic; not a formal error bound "
                "or exact American price"
            ),
        },
        "quote_interval": {
            "interpretation": (
                "quote-implied endpoint range, not confidence interval or arbitrage bound"
            ),
            "spread_scenarios_usd": [0.01, 0.02, 0.05, 0.10, 0.25],
        },
        "ranking_families": {
            "signals": SIGNAL_FAMILIES,
            "noise": NOISE_FAMILIES,
            "target_noise_sd_pp": NOISE_SDS_PP,
            "universe_sizes": UNIVERSE_SIZES,
            "seed_set": SEEDS,
            "replicates_per_seed_cell": replicates_per_seed,
            "common_shock_is_invariance_control": True,
            "correlated_leg_noise_sd_semantics": (
                "fixed marginal call/put leg SD; paired CPIV SD is "
                "sqrt(0.4) times leg SD"
            ),
            "uncalibrated": True,
        },
        "uncertainty_budget": "illustrative input-error scales; not a confidence interval",
        "separately_coded_identity_check": {
            "cases": len(independent_identity),
            "max_absolute_gap": max(
                float(row["absolute_identity_gap"]) for row in independent_identity
            ),
            "scope": (
                "separate code path by same author; not independent human "
                "replication or high-precision oracle"
            ),
        },
        "near_bound_decimal_audit": near_bound_audit,
        "files": list(file_rows)+[
            "near_bound_decimal_audit.csv",
            "near_bound_decimal_audit.json",
        ],
        "figures": figures,
    }
    summary_path = output_dir / "cpiv_r10_diagnostics.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates-per-seed", type=int, default=REPLICATES_PER_SEED)
    args = parser.parse_args()
    summary = write_r10_outputs(args.output, args.replicates_per_seed)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
