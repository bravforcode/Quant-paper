"""Reproducible synthetic diagnostics for proposed CPIV methods note R9.

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
UNIVERSE_SIZES = (10, 50)
SIGNAL_FAMILIES = (
    "equally_spaced",
    "clustered_near_zero",
    "near_ties",
    "two_clusters_cutoff",
    "wide_tails",
)
NOISE_FAMILIES = (
    "bounded_uniform",
    "gaussian",
    "contaminated_gaussian",
    "heteroskedastic_gaussian",
    "call_put_correlated_rho_0.8",
    "common_input_shock",
)
NOISE_SDS_PP = (0.25, 0.50, 1.00)
VEGA_FLOOR_USD_PER_DECIMAL_IV = 1e-6


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
                    "absolute_identity_error_usd": abs(residual - integral),
                })
    return rows, max(row["absolute_identity_error_usd"] for row in rows)


def local_approximation_grid() -> tuple[list[dict[str, Any]], dict[str, float | int]]:
    rows: list[dict[str, Any]] = []
    for ratio in (0.8, 0.9, 1.0, 1.1, 1.2):
        for days in (7, 30, 90, 365):
            for sigma_bar in (0.10, 0.20, 0.40):
                for spread_pp in (-2.0, -1.0, -0.5, 0.5, 1.0, 2.0):
                    for rate, q in ((0.00, 0.00), (0.05, 0.02)):
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
                        integrated_residual = _simpson(
                            lambda sigma, spot=spot, strike=strike, days=days,
                            rate=rate, q=q: _vega_decimal(
                                spot, strike, days, rate, q, sigma
                            ),
                            put_iv,
                            call_iv,
                        )
                        exact_pp = 100.0 * (call_iv - put_iv)
                        vega = _vega_decimal(spot, strike, days, rate, q, sigma_bar)
                        if vega < VEGA_FLOOR_USD_PER_DECIMAL_IV:
                            rows.append({
                                "spot_strike_ratio": ratio,
                                "days_to_expiry": days,
                                "reference_iv": sigma_bar,
                                "target_cpiv_pp": exact_pp,
                                "rate": rate,
                                "effective_yield": q,
                                "direct_price_residual_usd": direct_residual,
                                "integrated_vega_residual_usd": integrated_residual,
                                "direct_residual_numerical_gap_usd": abs(
                                    direct_residual-integrated_residual
                                ),
                                "vega_usd_per_decimal_iv": vega,
                                "local_approximation_pp": None,
                                "absolute_error_pp": None,
                                "status": "unresolved_below_vega_floor",
                            })
                            continue
                        approx_pp = 100.0 * integrated_residual / vega
                        rows.append({
                            "spot_strike_ratio": ratio,
                            "days_to_expiry": days,
                            "reference_iv": sigma_bar,
                            "target_cpiv_pp": exact_pp,
                            "rate": rate,
                            "effective_yield": q,
                            "direct_price_residual_usd": direct_residual,
                            "integrated_vega_residual_usd": integrated_residual,
                            "direct_residual_numerical_gap_usd": abs(
                                direct_residual-integrated_residual
                            ),
                            "vega_usd_per_decimal_iv": vega,
                            "local_approximation_pp": approx_pp,
                            "absolute_error_pp": abs(approx_pp - exact_pp),
                            "status": "resolved",
                        })
    errors = [row["absolute_error_pp"] for row in rows
              if row["absolute_error_pp"] is not None]
    return rows, {
        "n": len(rows),
        "resolved_n": len(errors),
        "unresolved_low_vega_n": len(rows)-len(errors),
        "vega_floor_usd_per_decimal_iv": VEGA_FLOOR_USD_PER_DECIMAL_IV,
        "max_absolute_error_pp": max(errors),
        "median_absolute_error_pp": statistics.median(errors),
        "p95_absolute_error_pp": sorted(errors)[math.ceil(0.95 * len(errors)) - 1],
    }


def inversion_diagnostics() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rejected_generated_quotes = 0
    unexpectedly_accepted_invalid_prices = 0
    max_repricing_error = 0.0
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
                            "status": f"rejected_near_bound_or_bracket: {exc}",
                        })
                        continue
                    repriced = demo.bs_price(
                        option_type, spot, strike, days, rate, q, recovered
                    )
                    error = abs(repriced - price)
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
                        "absolute_iv_error": abs(recovered - sigma),
                        "absolute_repricing_error_usd": error,
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
        "successfully_inverted_generated_quotes": sum(row["status"] == "ok" for row in rows),
        "rejected_generated_quotes": rejected_generated_quotes,
        "configured_iv_bracket": [1e-8, demo.MAX_IV],
        "bisection_iterations": 64,
        "rejected_invalid_price_cases": rejected,
        "unexpectedly_accepted_invalid_price_cases": unexpectedly_accepted_invalid_prices,
        "max_absolute_repricing_error_usd": max_repricing_error,
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


def american_convergence() -> list[dict[str, float | int]]:
    rows = []
    steps_grid = (400, 800, 1600, 3200)
    reference_call = demo.bs_price("call", 100.0, 100.0, 30, 0.05, 0.0, 0.20)
    for method in ("CRR", "Jarrow-Rudd"):
        for steps in steps_grid:
            put = (
                demo.american_price("put", 100.0, 100.0, 30, 0.05, 0.0, 0.20, steps)
                if method == "CRR"
                else jarrow_rudd_american_put(100.0, 100.0, 30, 0.05, 0.0,
                                              0.20, steps)
            )
            put_iv = demo.implied_volatility("put", put, 100.0, 100.0, 30, 0.05, 0.0)
            rows.append({
                "method": method,
                "steps": steps,
                "american_put_usd": put,
                "european_call_usd": reference_call,
                "implied_cpiv_pp": 100.0 * (0.20 - put_iv),
                "note": "numerical American put; exact BSM European call",
            })
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
        pair_count = len(intervals) * (len(intervals) - 1) // 2
        ordered = sum(
            1 for i in range(len(intervals)) for j in range(i + 1, len(intervals))
            if intervals[i][1] < intervals[j][0] or intervals[j][1] < intervals[i][0]
        )
        sign_resolved = sum(1 for lo, hi in intervals if lo > 0 or hi < 0)
        widths = [hi - lo for lo, hi in intervals]
        rows.append({
            "quote_half_spread_usd": half_spread,
            "pairs_total": 10,
            "pairs_valid": valid,
            "valid_pair_coverage": valid / 10.0,
            "median_quote_implied_interval_width_pp":
                100.0 * statistics.median(widths) if widths else math.nan,
            "pairwise_order_identified_fraction": ordered / pair_count if pair_count else math.nan,
            "cpiv_sign_identified_fraction": sign_resolved / valid if valid else math.nan,
            "interpretation": "quote-implied interval; not CI or arbitrage bound",
        })
    return rows


def uncertainty_scenarios() -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    # All input error scales and the quote-error correlation are illustrative.
    for rho_cp in (0.0, 0.5, 0.9):
        spot, strike, days, r, q = 100.0, 100.0, 30, 0.03, 0.01
        t = days / 365.0
        gradient = [
            1.0, -1.0, -math.exp(-q*t), spot*t*math.exp(-q*t),
            -strike*t*math.exp(-r*t),
        ]
        sd = [0.02, 0.02, 0.02, 0.001, 0.001]
        variance = sum((g*s)**2 for g, s in zip(gradient, sd, strict=True))
        variance += 2.0 * rho_cp * gradient[0] * gradient[1] * sd[0] * sd[1]
        residual_sd = math.sqrt(max(0.0, variance))
        vega = _vega_decimal(spot, strike, days, r, q, 0.20)
        rows.append({
            "call_put_error_correlation": rho_cp,
            "illustrative_residual_sd_usd": residual_sd,
            "vega_usd_per_decimal_iv": vega,
            "first_order_cpiv_sd_pp": 100.0 * residual_sd / vega,
            "status": "illustrative independent input scales; not a confidence interval",
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
    if family == "wide_tails":
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
    if family == "heteroskedastic_gaussian":
        factors = [0.5 + i / max(1, n-1) for i in range(n)]
        rms = math.sqrt(sum(f*f for f in factors) / n)
        return [rng.gauss(0.0, sd * factor/rms) for factor in factors]
    if family == "call_put_correlated_rho_0.8":
        rho = 0.8
        leg_sd = sd / math.sqrt(2.0 * (1.0-rho))
        result = []
        for _ in signals:
            call_z = rng.gauss(0.0, 1.0)
            independent_z = rng.gauss(0.0, 1.0)
            put_z = rho * call_z + math.sqrt(1.0-rho*rho) * independent_z
            result.append(leg_sd * (call_z-put_z))
        return result
    if family == "common_input_shock":
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


def rank_sensitivity(replicates_per_seed: int = REPLICATES_PER_SEED
                     ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if replicates_per_seed < 1:
        raise ValueError("replicates_per_seed must be positive")
    output: list[dict[str, Any]] = []
    name_output: list[dict[str, Any]] = []
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
            for noise_family in NOISE_FAMILIES:
                for sd in NOISE_SDS_PP:
                    metrics: list[tuple[float, float, float, float, bool, bool]] = []
                    top_hits = [0] * n
                    bottom_hits = [0] * n
                    sign_hits = [0] * n
                    for seed in SEEDS:
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
                    exact_count = sum(item[4] for item in metrics)
                    changed_count = sum(item[5] for item in metrics)
                    exact_lo, exact_hi = _wilson(exact_count, n_draws)
                    changed_lo, changed_hi = _wilson(changed_count, n_draws)
                    output.append({
                        "universe_n": n,
                        "signal_family": signal_family,
                        "noise_family": noise_family,
                        "target_noise_sd_pp": sd,
                        "seeds": ";".join(map(str, SEEDS)),
                        "replicates_per_seed": replicates_per_seed,
                        "replicates_total": n_draws,
                        "mean_pairwise_inversion_fraction": statistics.fmean(x[0] for x in metrics),
                        "mean_spearman_rank_correlation": statistics.fmean(x[1] for x in metrics),
                        "mean_top_bottom_membership_turnover": statistics.fmean(
                            x[2] for x in metrics
                        ),
                        "mean_sign_accuracy": statistics.fmean(x[3] for x in metrics),
                        "probability_exact_full_order": exact_count/n_draws,
                        "exact_order_wilson95_low": exact_lo,
                        "exact_order_wilson95_high": exact_hi,
                        "probability_any_extreme_membership_change": changed_count/n_draws,
                        "membership_change_wilson95_low": changed_lo,
                        "membership_change_wilson95_high": changed_hi,
                        "simulation_status": (
                            "synthetic uncalibrated stress test; not market estimate"
                        ),
                    })
                    if n == 10:
                        for index, signal in enumerate(signals):
                            top_lo, top_hi = _wilson(top_hits[index], n_draws)
                            bottom_lo, bottom_hi = _wilson(bottom_hits[index], n_draws)
                            name_output.append({
                                "signal_family": signal_family,
                                "noise_family": noise_family,
                                "target_noise_sd_pp": sd,
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
    return output, name_output


def render_r9_figures(output_dir: Path, approximation: list[dict[str, float]],
                      ranking: list[dict[str, Any]],
                      american: list[dict[str, float | int]]) -> list[str]:
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
        path = output_dir / f"cpiv_r9_local_approximation_error.{suffix}"
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
                key=lambda row: row["target_noise_sd_pp"],
            )
            axis.plot(
                [row["target_noise_sd_pp"] for row in selected],
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
        path = output_dir / f"cpiv_r9_rank_sensitivity.{suffix}"
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
    axis.set_xticks([400, 800, 1600, 3200], labels=["400", "800", "1,600", "3,200"])
    axis.set_ylabel("Implied CPIV (pp)")
    axis.set_title("American-put numerical scheme comparison")
    axis.grid(alpha=0.25)
    axis.legend(frameon=False)
    for suffix in ("png", "svg"):
        path = output_dir / f"cpiv_r9_american_convergence.{suffix}"
        fig.savefig(path, dpi=180, bbox_inches="tight")
        generated.append(path.name)
    plt.close(fig)
    return generated


def write_r9_outputs(output_dir: Path, replicates_per_seed: int = REPLICATES_PER_SEED
                     ) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    identity, identity_error = bsm_identity_grid()
    approximation, approximation_summary = local_approximation_grid()
    inversion, inversion_summary = inversion_diagnostics()
    american = american_convergence()
    carry, spot = carry_and_spot_diagnostics()
    quote_intervals = quote_interval_diagnostics()
    uncertainty = uncertainty_scenarios()
    ranking, name_membership = rank_sensitivity(replicates_per_seed)
    figures = render_r9_figures(output_dir, approximation, ranking, american)
    file_rows = {
        "bsm_identity_grid.csv": identity,
        "local_approximation_grid.csv": approximation,
        "iv_inversion_roundtrips.csv": inversion,
        "american_put_convergence.csv": american,
        "carry_sensitivity.csv": carry,
        "spot_mismatch_sensitivity.csv": spot,
        "quote_implied_intervals.csv": quote_intervals,
        "illustrative_uncertainty_budget.csv": uncertainty,
        "rank_noise_sensitivity.csv": ranking,
        "rank_per_name_membership.csv": name_membership,
    }
    for filename, rows in file_rows.items():
        _write_csv(output_dir / filename, rows)
    summary = {
        "status": "synthetic_methods_diagnostics_only",
        "market_data_used": False,
        "trading_or_alpha_claim": False,
        "seeds": SEEDS,
        "replicates_per_seed": replicates_per_seed,
        "ranking_total_replicates_per_scenario": replicates_per_seed*len(SEEDS),
        "identity_grid": {"cases": len(identity), "max_abs_error_usd": identity_error},
        "local_approximation_grid": approximation_summary,
        "iv_inversion": inversion_summary,
        "american_put": {
            "steps": [400, 800, 1600, 3200],
            "methods": ["CRR", "Jarrow-Rudd"],
            "claim": "numerical convergence comparison; no exact American price asserted",
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
            "uncalibrated": True,
        },
        "uncertainty_budget": "illustrative input-error scales; not a confidence interval",
        "files": list(file_rows),
        "figures": figures,
    }
    summary_path = output_dir / "cpiv_r9_diagnostics.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates-per-seed", type=int, default=REPLICATES_PER_SEED)
    args = parser.parse_args()
    summary = write_r9_outputs(args.output, args.replicates_per_seed)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
