"""Build synthetic CPIV examples, model-risk stress tests, and figures.

No market data, network access, or trading result is used by this module.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "generated"
SPOT = 100.0
STRIKE = 100.0
DAYS = 30
RATE = 0.0
DIVIDEND_YIELD = 0.0
PUT_IV = 0.20
QUOTE_HALF_SPREAD = 0.02
MAX_IV = 5.0
SIMULATION_SEED = 20261008
SIMULATION_REPLICATES = 2000
NOISE_CPIV_SD_PPS = (0.0, 0.10, 0.20, 0.35, 0.50, 1.0, 2.0)
NOISE_HALF_SPREAD_USD = 0.05
SPOT_MISMATCH_USD = (0.02, 0.05, 0.10, 0.25)
DTE_TRADEOFF_DAYS = (7, 30, 90, 365)
SCALE_SPOTS = (20.0, 100.0, 500.0)
SCALE_DAYS = (7, 30, 90)
AMERICAN_RATE = 0.05
AMERICAN_STEPS = 800


def _validate_inputs(
    option_type: str,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
    sigma: float,
) -> None:
    if option_type not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'")
    if not all(math.isfinite(value) for value in (spot, strike, rate, dividend_yield, sigma)):
        raise ValueError("numeric inputs must be finite")
    if spot <= 0 or strike <= 0 or days <= 0 or sigma <= 0:
        raise ValueError("spot, strike, days, and sigma must be positive")


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def bs_price(
    option_type: str,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
    sigma: float,
) -> float:
    """Black-Scholes-Merton European option price; rates are decimals."""
    _validate_inputs(option_type, spot, strike, days, rate, dividend_yield, sigma)
    maturity = days / 365.0
    root_t = math.sqrt(maturity)
    d1 = (math.log(spot / strike) + (rate - dividend_yield + 0.5 * sigma * sigma) * maturity) / (
        sigma * root_t
    )
    d2 = d1 - sigma * root_t
    discounted_spot = spot * math.exp(-dividend_yield * maturity)
    discounted_strike = strike * math.exp(-rate * maturity)
    if option_type == "call":
        return discounted_spot * _normal_cdf(d1) - discounted_strike * _normal_cdf(d2)
    return discounted_strike * _normal_cdf(-d2) - discounted_spot * _normal_cdf(-d1)


def bs_vega_per_vol_point(
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
    sigma: float,
) -> float:
    """Return European BSM vega dollars per one volatility percentage point."""
    _validate_inputs("call", spot, strike, days, rate, dividend_yield, sigma)
    maturity = days / 365.0
    d1 = (
        math.log(spot / strike)
        + (rate - dividend_yield + 0.5 * sigma * sigma) * maturity
    ) / (sigma * math.sqrt(maturity))
    normal_density = math.exp(-0.5 * d1 * d1) / math.sqrt(2.0 * math.pi)
    return (
        spot
        * math.exp(-dividend_yield * maturity)
        * normal_density
        * math.sqrt(maturity)
        / 100.0
    )


def parity_residual(
    call_price: float,
    put_price: float,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
) -> float:
    """Return C-P-(S exp(-qT)-K exp(-rT)) in underlying currency units."""
    maturity = days / 365.0
    parity_value = spot * math.exp(-dividend_yield * maturity) - strike * math.exp(
        -rate * maturity
    )
    return call_price - put_price - parity_value


def price_bounds(
    option_type: str,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
) -> tuple[float, float]:
    """European no-arbitrage price bounds used to reject impossible inputs."""
    maturity = days / 365.0
    discounted_spot = spot * math.exp(-dividend_yield * maturity)
    discounted_strike = strike * math.exp(-rate * maturity)
    if option_type == "call":
        return max(discounted_spot - discounted_strike, 0.0), discounted_spot
    if option_type == "put":
        return max(discounted_strike - discounted_spot, 0.0), discounted_strike
    raise ValueError("option_type must be 'call' or 'put'")


def implied_volatility(
    option_type: str,
    market_price: float,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
) -> float:
    """Invert BSM price by bisection, rejecting bounds and unbracketed quotes."""
    if not math.isfinite(market_price) or market_price < 0:
        raise ValueError("market_price must be finite and nonnegative")
    lower_bound, upper_bound = price_bounds(option_type, spot, strike, days, rate, dividend_yield)
    tolerance = 1e-10
    if market_price <= lower_bound + tolerance or market_price >= upper_bound - tolerance:
        raise ValueError("market_price must lie strictly inside European no-arbitrage bounds")

    low, high = 1e-8, MAX_IV
    low_price = bs_price(option_type, spot, strike, days, rate, dividend_yield, low)
    high_price = bs_price(option_type, spot, strike, days, rate, dividend_yield, high)
    if market_price < low_price - tolerance or market_price > high_price + tolerance:
        raise ValueError("implied volatility is outside the configured [0, 500%] bracket")
    for _ in range(64):
        mid = (low + high) / 2.0
        model_price = bs_price(option_type, spot, strike, days, rate, dividend_yield, mid)
        if model_price < market_price:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def build_records() -> list[dict[str, Any]]:
    """Construct ten equally specified fictional option pairs."""
    rows: list[dict[str, Any]] = []
    for index in range(10):
        symbol = f"SIM{index + 1:02d}"
        call_target_iv = 0.16 + 0.01 * index
        call_price = bs_price("call", SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, call_target_iv)
        put_price = bs_price("put", SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV)
        call_iv = implied_volatility("call", call_price, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD)
        put_iv = implied_volatility("put", put_price, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD)
        call_bid_iv = implied_volatility(
            "call", call_price - QUOTE_HALF_SPREAD, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD
        )
        call_ask_iv = implied_volatility(
            "call", call_price + QUOTE_HALF_SPREAD, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD
        )
        put_bid_iv = implied_volatility(
            "put", put_price - QUOTE_HALF_SPREAD, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD
        )
        put_ask_iv = implied_volatility(
            "put", put_price + QUOTE_HALF_SPREAD, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD
        )
        rows.append(
            {
                "symbol": symbol,
                "spot_usd": SPOT,
                "strike_usd": STRIKE,
                "days_to_expiry": DAYS,
                "call_price_usd": call_price,
                "put_price_usd": put_price,
                "call_iv": call_iv,
                "put_iv": put_iv,
                "cpiv": call_iv - put_iv,
                "interval_low": call_bid_iv - put_ask_iv,
                "interval_high": call_ask_iv - put_bid_iv,
            }
        )

    ranked = sorted(rows, key=lambda row: (row["cpiv"], row["symbol"]))
    for rank, row in enumerate(ranked, start=1):
        row["rank_low_to_high"] = rank
        row["illustrative_bucket"] = (
            "short-side candidate"
            if rank <= 2
            else "long-side candidate"
            if rank >= 9
            else "middle"
        )
    return sorted(rows, key=lambda row: row["symbol"])


def american_price(
    option_type: str,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
    sigma: float,
    steps: int = AMERICAN_STEPS,
) -> float:
    """Price an American option with a CRR tree and early exercise at each node."""
    _validate_inputs(option_type, spot, strike, days, rate, dividend_yield, sigma)
    if steps < 1:
        raise ValueError("steps must be positive")
    dt = days / 365.0 / steps
    up = math.exp(sigma * math.sqrt(dt))
    down = 1.0 / up
    growth = math.exp((rate - dividend_yield) * dt)
    probability = (growth - down) / (up - down)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("CRR risk-neutral probability must lie in [0, 1]")
    discount = math.exp(-rate * dt)

    values = []
    for up_moves in range(steps + 1):
        stock = spot * up**up_moves * down ** (steps - up_moves)
        intrinsic = stock - strike if option_type == "call" else strike - stock
        values.append(max(intrinsic, 0.0))

    for time_step in range(steps - 1, -1, -1):
        for up_moves in range(time_step + 1):
            continuation = discount * (
                probability * values[up_moves + 1]
                + (1.0 - probability) * values[up_moves]
            )
            stock = spot * up**up_moves * down ** (time_step - up_moves)
            intrinsic = stock - strike if option_type == "call" else strike - stock
            values[up_moves] = max(continuation, intrinsic, 0.0)
    return values[0]


def _linear_quantile(values: list[float], probability: float) -> float:
    """Return a linearly interpolated sample quantile."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def carry_misspecification() -> list[dict[str, float]]:
    """Generate matched European prices with true q, then invert under q=0."""
    rows = []
    for true_yield in (0.0, 0.01, 0.02, 0.05):
        call_price = bs_price("call", SPOT, STRIKE, DAYS, RATE, true_yield, PUT_IV)
        put_price = bs_price("put", SPOT, STRIKE, DAYS, RATE, true_yield, PUT_IV)
        call_iv = implied_volatility(
            "call", call_price, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD
        )
        put_iv = implied_volatility(
            "put", put_price, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD
        )
        rows.append(
            {
                "true_effective_yield": true_yield,
                "assumed_effective_yield": DIVIDEND_YIELD,
                "true_iv": PUT_IV,
                "call_iv_under_assumed_yield": call_iv,
                "put_iv_under_assumed_yield": put_iv,
        "cpiv_pp": (call_iv - put_iv) * 100.0,
                "parity_residual_usd": parity_residual(
                    call_price,
                    put_price,
                    SPOT,
                    STRIKE,
                    DAYS,
                    RATE,
                    DIVIDEND_YIELD,
                ),
            }
        )
    return rows


def american_model_mismatch() -> dict[str, float | int]:
    """Isolate an American put premium, then invert both legs with European BSM."""
    # With q=0, an American call has no early-exercise premium; use the exact
    # European BSM value rather than retaining a finite-tree call approximation.
    american_call = bs_price(
        "call", SPOT, STRIKE, DAYS, AMERICAN_RATE, 0.0, PUT_IV
    )
    american_put = american_price(
        "put", SPOT, STRIKE, DAYS, AMERICAN_RATE, 0.0, PUT_IV
    )
    call_iv = implied_volatility(
        "call", american_call, SPOT, STRIKE, DAYS, AMERICAN_RATE, 0.0
    )
    put_iv = implied_volatility(
        "put", american_put, SPOT, STRIKE, DAYS, AMERICAN_RATE, 0.0
    )
    european_call = bs_price("call", SPOT, STRIKE, DAYS, AMERICAN_RATE, 0.0, PUT_IV)
    european_put = bs_price("put", SPOT, STRIKE, DAYS, AMERICAN_RATE, 0.0, PUT_IV)
    residual = parity_residual(
        american_call,
        american_put,
        SPOT,
        STRIKE,
        DAYS,
        AMERICAN_RATE,
        0.0,
    )
    return {
        "steps": AMERICAN_STEPS,
        "risk_free_rate": AMERICAN_RATE,
        "dividend_yield": 0.0,
        "true_iv": PUT_IV,
        "american_call_price": american_call,
        "american_put_price": american_put,
        "european_call_price_at_true_iv": european_call,
        "european_put_price_at_true_iv": european_put,
        "call_early_exercise_premium_usd": 0.0,
        "put_early_exercise_premium_usd": american_put - european_put,
        "parity_residual_usd": residual,
        "vega_per_vol_point_usd": bs_vega_per_vol_point(
            SPOT, STRIKE, DAYS, AMERICAN_RATE, 0.0, PUT_IV
        ),
        "local_cpiv_approximation_pp": residual
        / bs_vega_per_vol_point(SPOT, STRIKE, DAYS, AMERICAN_RATE, 0.0, PUT_IV),
        "call_iv_from_european_bsm": call_iv,
        "put_iv_from_european_bsm": put_iv,
        "cpiv_pp_from_european_bsm": (call_iv - put_iv) * 100.0,
    }


def spot_timestamp_mismatch() -> list[dict[str, float]]:
    """Price matched options at one spot, then invert using a stale/misaligned spot."""
    rows = []
    quote_spot = SPOT
    call_price = bs_price("call", quote_spot, STRIKE, DAYS, RATE, 0.0, PUT_IV)
    put_price = bs_price("put", quote_spot, STRIKE, DAYS, RATE, 0.0, PUT_IV)
    for spot_error in SPOT_MISMATCH_USD:
        used_spot = quote_spot + spot_error
        call_iv = implied_volatility(
            "call", call_price, used_spot, STRIKE, DAYS, RATE, 0.0
        )
        put_iv = implied_volatility(
            "put", put_price, used_spot, STRIKE, DAYS, RATE, 0.0
        )
        residual = parity_residual(
            call_price, put_price, used_spot, STRIKE, DAYS, RATE, 0.0
        )
        rows.append(
            {
                "quote_spot_usd": quote_spot,
                "spot_used_usd": used_spot,
                "spot_misalignment_usd": spot_error,
                "parity_residual_usd": residual,
                "vega_per_vol_point_usd": bs_vega_per_vol_point(
                    used_spot, STRIKE, DAYS, RATE, 0.0, PUT_IV
                ),
                "local_cpiv_approximation_pp": residual
                / bs_vega_per_vol_point(used_spot, STRIKE, DAYS, RATE, 0.0, PUT_IV),
                "cpiv_pp": (call_iv - put_iv) * 100.0,
            }
        )
    return rows


def dte_tradeoff_sensitivity() -> list[dict[str, float | int]]:
    """Contrast fixed-dollar quote noise with an omitted 1% effective yield."""
    rows = []
    true_yield = 0.01
    for days in DTE_TRADEOFF_DAYS:
        call_price = bs_price("call", SPOT, STRIKE, days, RATE, true_yield, PUT_IV)
        put_price = bs_price("put", SPOT, STRIKE, days, RATE, true_yield, PUT_IV)
        call_iv = implied_volatility(
            "call", call_price, SPOT, STRIKE, days, RATE, DIVIDEND_YIELD
        )
        put_iv = implied_volatility(
            "put", put_price, SPOT, STRIKE, days, RATE, DIVIDEND_YIELD
        )
        vega = bs_vega_per_vol_point(
            SPOT, STRIKE, days, RATE, DIVIDEND_YIELD, PUT_IV
        )
        rows.append(
            {
                "days_to_expiry": days,
                "true_effective_yield": true_yield,
                "assumed_effective_yield": DIVIDEND_YIELD,
                "quote_noise_half_width_usd_per_leg": NOISE_HALF_SPREAD_USD,
                "quote_noise_cpiv_sd_pp_linearized": (
                    NOISE_HALF_SPREAD_USD * math.sqrt(2.0 / 3.0) / vega
                ),
                "omitted_carry_cpiv_pp": (call_iv - put_iv) * 100.0,
                "vega_per_vol_point_usd": vega,
            }
        )
    return rows


def quote_noise_scale_sensitivity() -> list[dict[str, float | int]]:
    """Show the volatility-point effect of $0.05 noise across spot and maturity."""
    rows = []
    for spot in SCALE_SPOTS:
        for days in SCALE_DAYS:
            vega = bs_vega_per_vol_point(
                spot, spot, days, RATE, DIVIDEND_YIELD, PUT_IV
            )
            rows.append(
                {
                    "spot_usd": spot,
                    "strike_usd": spot,
                    "days_to_expiry": days,
                    "vega_per_vol_point_usd": vega,
                    "noise_half_width_usd_per_leg": NOISE_HALF_SPREAD_USD,
                    "cpiv_noise_sd_pp_at_half_width": (
                        NOISE_HALF_SPREAD_USD * math.sqrt(2.0 / 3.0) / vega
                    ),
                    "half_width_usd_per_leg_for_0_5pp_cpiv_sd": (
                        0.5 * vega * math.sqrt(1.5)
                    ),
                }
            )
    return rows


def rank_noise_summary(
    replicates: int = SIMULATION_REPLICATES,
) -> list[dict[str, Any]]:
    """Measure ranking damage at vega-scaled CPIV-noise levels."""
    if replicates < 1:
        raise ValueError("replicates must be positive")
    call_volatilities = [0.16 + 0.01 * index for index in range(10)]
    call_prices = [
        bs_price("call", SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, sigma)
        for sigma in call_volatilities
    ]
    put_price = bs_price("put", SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV)
    results: list[dict[str, Any]] = []

    for noise_index, target_sd_pp in enumerate(NOISE_CPIV_SD_PPS):
        rng = random.Random(SIMULATION_SEED + noise_index)
        call_half_widths = [
            target_sd_pp
            * bs_vega_per_vol_point(
                SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, sigma
            )
            * math.sqrt(1.5)
            for sigma in call_volatilities
        ]
        put_half_width = (
            target_sd_pp
            * bs_vega_per_vol_point(
                SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV
            )
            * math.sqrt(1.5)
        )
        inversion_counts: list[float] = []
        correlations: list[float] = []
        no_inversion_count = 0
        top_to_bottom_count = 0
        bottom_to_top_count = 0
        extreme_crossover_count = 0
        long_short_membership_change_count = 0
        example_ranked: list[dict[str, float | int | str]] = []
        for _ in range(replicates):
            noisy_cpiv = []
            for index, call_price in enumerate(call_prices):
                call_half_width = call_half_widths[index]
                noisy_call = call_price + rng.uniform(
                    -call_half_width, call_half_width
                )
                noisy_put = put_price + rng.uniform(
                    -put_half_width, put_half_width
                )
                call_iv = implied_volatility(
                    "call", noisy_call, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD
                )
                put_iv = implied_volatility(
                    "put", noisy_put, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD
                )
                noisy_cpiv.append(call_iv - put_iv)

            order = sorted(range(len(noisy_cpiv)), key=lambda index: (noisy_cpiv[index], index))
            ranks = [0] * len(order)
            for rank, index in enumerate(order):
                ranks[index] = rank
            inversions = sum(
                ranks[left] > ranks[right]
                for left in range(len(ranks))
                for right in range(left + 1, len(ranks))
            )
            rank_differences = [ranks[index] - index for index in range(len(ranks))]
            rho = 1.0 - 6.0 * sum(value * value for value in rank_differences) / (
                len(ranks) * (len(ranks) ** 2 - 1)
            )
            inversion_counts.append(float(inversions))
            correlations.append(rho)
            no_inversion_count += inversions == 0
            top_to_bottom = ranks[-1] < 2
            bottom_to_top = ranks[0] >= 8
            top_to_bottom_count += top_to_bottom
            bottom_to_top_count += bottom_to_top
            extreme_crossover_count += top_to_bottom or bottom_to_top
            long_short_membership_change_count += (
                set(order[-2:]) != {8, 9} or set(order[:2]) != {0, 1}
            )
            if not example_ranked:
                example_ranked = [
                    {
                        "symbol": f"SIM{index + 1:02d}",
                        "cpiv_pp": noisy_cpiv[index] * 100.0,
                        "rank_low_to_high": rank + 1,
                    }
                    for rank, index in enumerate(order)
                ]

        results.append(
            {
                "target_cpiv_noise_sd_pp": target_sd_pp,
                "replicates": replicates,
                "rank_inversions_p05": _linear_quantile(inversion_counts, 0.05),
                "rank_inversions_median": _linear_quantile(inversion_counts, 0.50),
                "rank_inversions_p95": _linear_quantile(inversion_counts, 0.95),
                "probability_no_pairwise_inversions": no_inversion_count / replicates,
                "probability_top_true_name_in_bottom_quintile": (
                    top_to_bottom_count / replicates
                ),
                "probability_bottom_true_name_in_top_quintile": (
                    bottom_to_top_count / replicates
                ),
                "probability_any_extreme_quintile_crossover": (
                    extreme_crossover_count / replicates
                ),
                "probability_long_short_membership_change": (
                    long_short_membership_change_count / replicates
                ),
                "spearman_rho_p05": _linear_quantile(correlations, 0.05),
                "spearman_rho_median": _linear_quantile(correlations, 0.50),
                "spearman_rho_p95": _linear_quantile(correlations, 0.95),
                "example_ranked_names": example_ranked,
            }
        )
    return results


def build_stress_results(
    replicates: int = SIMULATION_REPLICATES,
) -> dict[str, Any]:
    """Collect assumptions and results for reproducible synthetic stress tests."""
    return {
        "status": "synthetic_sensitivity_analysis_only",
        "market_data_used": False,
        "network_access_used": False,
        "carry_misspecification": carry_misspecification(),
        "american_model_mismatch": american_model_mismatch(),
        "spot_timestamp_mismatch": spot_timestamp_mismatch(),
        "dte_tradeoff_sensitivity": dte_tradeoff_sensitivity(),
        "quote_noise_scale_sensitivity": quote_noise_scale_sensitivity(),
        "quote_noise_ranking": {
            "seed": SIMULATION_SEED,
            "method": (
                "Each synthetic option price receives an independent uniform "
                "perturbation. Per-leg dollar half-width is calibrated by local "
                "BSM vega so the linearized paired CPIV-noise SD matches the "
                "requested volatility-point level; exact IV is then reinverted."
            ),
            "scale_basis": (
                "target standard deviation of the paired CPIV measurement error, "
                "in volatility percentage points, using local vega"
            ),
            "vega_reference": {
                "spot_usd": SPOT,
                "strike_usd": STRIKE,
                "days_to_expiry": DAYS,
                "rate": RATE,
                "effective_yield": DIVIDEND_YIELD,
                "volatility": PUT_IV,
                "vega_per_vol_point_usd": bs_vega_per_vol_point(
                    SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV
                ),
            },
            "replicates": replicates,
            "true_call_ivs": [0.16 + 0.01 * index for index in range(10)],
            "true_put_iv": PUT_IV,
            "results": rank_noise_summary(replicates),
        },
        "warning": (
            "All scenarios are constructed. They are neither market estimates, "
            "confidence intervals, nor evidence of trading profitability."
        ),
    }


def render_stress_figures(results: dict[str, Any], output_dir: Path) -> dict[str, str]:
    """Render separate, readable sensitivity figures and a self-contained OG card."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Tahoma", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    output_dir.mkdir(parents=True, exist_ok=True)
    carry_png = output_dir / "cpiv_carry_bias.png"
    carry_svg = output_dir / "cpiv_carry_bias.svg"
    american_png = output_dir / "cpiv_american_bias.png"
    american_svg = output_dir / "cpiv_american_bias.svg"
    noise_png = output_dir / "cpiv_quote_noise.png"
    noise_svg = output_dir / "cpiv_quote_noise.svg"
    social_card_png = output_dir / "cpiv_social_card.png"

    carry = results["carry_misspecification"]
    fig, axis = plt.subplots(figsize=(9.2, 5.8), layout="constrained")
    axis.axhline(0.0, color="#596675", linewidth=1.0, linestyle="--")
    axis.plot(
        [row["true_effective_yield"] * 100 for row in carry],
        [row["cpiv_pp"] for row in carry],
        color="#0072B2",
        marker="D",
        linewidth=2.0,
        markersize=6,
    )
    axis.set_title(
        "Omitted effective carry creates a parity residual",
        loc="left",
        weight="bold",
    )
    axis.set_xlabel("True effective yield q (%)")
    axis.set_ylabel("False CPIV when inversion assumes q = 0 (volatility pp)")
    axis.grid(axis="y", color="#dce2e8", linewidth=0.8)
    axis.text(
        0.03,
        0.03,
        "Synthetic European BSM prices; S = K = $100; 30 days; true IV = 20%",
        transform=axis.transAxes,
        fontsize=9,
        color="#596675",
    )
    fig.savefig(carry_png, dpi=220, facecolor="white")
    fig.savefig(carry_svg, facecolor="white")
    plt.close(fig)

    american = results["american_model_mismatch"]
    mismatch = float(american["cpiv_pp_from_european_bsm"])
    fig, axis = plt.subplots(figsize=(9.2, 5.8), layout="constrained")
    axis.axhline(0.0, color="#596675", linewidth=1.0)
    axis.scatter(
        [0, 1],
        [0.0, mismatch],
        marker="o",
        s=72,
        color=["#0072B2", "#D55E00"],
        edgecolor="#253746",
        linewidth=0.7,
        zorder=3,
    )
    axis.set_xticks(
        [0, 1],
        ["European prices\nEuropean BSM IV", "American CRR prices\nEuropean BSM IV"],
    )
    axis.set_ylabel("CPIV (volatility percentage points)")
    axis.set_title(
        "Exercise-style mismatch appears as a parity residual",
        loc="left",
        weight="bold",
    )
    axis.set_ylim(-0.40, 0.15)
    axis.grid(axis="y", color="#dce2e8", linewidth=0.8)
    axis.annotate(
        "+0.000",
        (0, 0),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
    )
    axis.annotate(
        f"{mismatch:+.3f}",
        (1, mismatch),
        xytext=(18, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=10,
    )
    axis.tick_params(axis="x", labelsize=10)
    axis.text(
        0.03,
        0.03,
        f"CRR {AMERICAN_STEPS} steps; S = K = $100; 30 days; r = 5%; q = 0%",
        transform=axis.transAxes,
        fontsize=9,
        color="#596675",
    )
    fig.savefig(american_png, dpi=220, facecolor="white")
    fig.savefig(american_svg, facecolor="white")
    plt.close(fig)

    noise = results["quote_noise_ranking"]["results"]
    x = [float(row["target_cpiv_noise_sd_pp"]) for row in noise]
    no_inversion = [
        float(row["probability_no_pairwise_inversions"]) for row in noise
    ]
    membership_change = [
        float(row["probability_long_short_membership_change"]) for row in noise
    ]
    fig, axis = plt.subplots(figsize=(9.2, 5.8), layout="constrained")
    axis.plot(
        x,
        no_inversion,
        color="#0072B2",
        marker="o",
        markersize=6,
        linewidth=2.2,
        label="No pairwise rank inversions",
    )
    axis.plot(
        x,
        membership_change,
        color="#D55E00",
        marker="s",
        markersize=5.5,
        linewidth=2.0,
        label="Any top/bottom quintile membership change",
    )
    axis.set_xticks(x, [f"{value:g}" for value in x])
    axis.set_ylim(-0.03, 1.03)
    axis.set_xlabel("Target linearized SD of paired CPIV noise (volatility pp)")
    axis.set_ylabel("Fraction of simulated rounds (n = 2,000 per level)")
    axis.set_title(
        "Synthetic rank reliability under vega-scaled quote noise",
        loc="left",
        weight="bold",
    )
    axis.grid(axis="y", color="#dce2e8", linewidth=0.8)
    axis.legend(frameon=False, fontsize=9)
    axis.text(
        0.01,
        -0.18,
        "Top/bottom portfolios use the two highest/lowest of ten synthetic names.",
        transform=axis.transAxes,
        fontsize=8,
        color="#596675",
    )
    fig.savefig(noise_png, dpi=220, facecolor="white", bbox_inches="tight")
    fig.savefig(noise_svg, facecolor="white", bbox_inches="tight")
    plt.close(fig)

    fig = plt.figure(figsize=(12.0, 6.3), dpi=100, facecolor="white")
    fig.text(
        0.07,
        0.78,
        "Call–Put Implied Volatility Spread",
        fontsize=27,
        weight="bold",
        color="#152a3c",
    )
    fig.text(
        0.07,
        0.64,
        "What does the wedge tell us?",
        fontsize=22,
        color="#166b78",
    )
    fig.text(
        0.07,
        0.43,
        "CPIV ≈ 100 × put–call parity residual / vega",
        fontsize=18,
        color="#202936",
    )
    fig.text(
        0.07,
        0.25,
        "Carry · exercise style · timestamp alignment · quote quality",
        fontsize=14,
        color="#596675",
    )
    fig.text(
        0.07,
        0.10,
        "Synthetic sensitivity analysis only — no market prices or returns used",
        fontsize=11,
        color="#596675",
    )
    fig.savefig(social_card_png, facecolor="white")
    plt.close(fig)
    return {
        "carry_png": str(carry_png),
        "carry_svg": str(carry_svg),
        "american_png": str(american_png),
        "american_svg": str(american_svg),
        "noise_png": str(noise_png),
        "noise_svg": str(noise_svg),
        "social_card_png": str(social_card_png),
    }


def render_svg(rows: list[dict[str, Any]]) -> str:
    """Render accessible, deterministic SVG of fictional CPIV values."""
    width, row_height, top = 1000, 42, 110
    height = top + row_height * len(rows) + 90
    left, right = 165, 875
    axis_x = (left + right) / 2
    extent = max(abs(row["interval_low"]) for row in rows)
    extent = max(extent, max(abs(row["interval_high"]) for row in rows)) * 1.12
    scale = (right - left) / (2 * extent)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="title description">',
        '<title id="title">Synthetic call-put implied-volatility spreads</title>',
        '<desc id="description">Ten fictional option pairs. Bars show call implied volatility '
        "minus put implied volatility; whiskers show a quote-width sensitivity interval.</desc>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        "<style>text{font-family:Arial,sans-serif;fill:#17202a}.small{font-size:13px}"
        ".label{font-size:15px}.head{font-size:19px;font-weight:700}</style>",
        '<text x="40" y="42" class="head">Fictional option pairs - CPIV = call IV '
        "minus put IV</text>",
        '<text x="40" y="69" class="small">Bars: point value; whiskers: quote-width',
        " sensitivity, not a confidence interval</text>",
        f'<line x1="{axis_x:.2f}" y1="{top - 10}" x2="{axis_x:.2f}" '
        f'y2="{top + row_height * len(rows) - 4}" stroke="#536273" stroke-width="2"/>',
    ]
    for index, row in enumerate(sorted(rows, key=lambda item: item["cpiv"])):
        y = top + index * row_height
        low_x = axis_x + row["interval_low"] * scale
        high_x = axis_x + row["interval_high"] * scale
        point_x = axis_x + row["cpiv"] * scale
        color = "#bf4b43" if row["cpiv"] < 0 else "#138a72"
        lines.extend(
            [
                f'<text x="40" y="{y + 5}" class="label">{row["symbol"]}</text>',
                f'<line x1="{low_x:.2f}" y1="{y}" x2="{high_x:.2f}" y2="{y}" '
                'stroke="#34495e" stroke-width="2"/>',
                f'<line x1="{low_x:.2f}" y1="{y - 5}" x2="{low_x:.2f}" y2="{y + 5}" '
                'stroke="#34495e" stroke-width="2"/>',
                f'<line x1="{high_x:.2f}" y1="{y - 5}" x2="{high_x:.2f}" y2="{y + 5}" '
                'stroke="#34495e" stroke-width="2"/>',
                f'<line x1="{axis_x:.2f}" y1="{y}" x2="{point_x:.2f}" y2="{y}" '
                f'stroke="{color}" stroke-width="9" stroke-linecap="round"/>',
                f'<text x="900" y="{y + 5}" class="small">{row["cpiv"] * 100:+.2f} pp</text>',
            ]
        )
    lines.extend(
        [
            f'<text x="{left}" y="{height - 25}" class="small">Put IV higher</text>',
            f'<text x="{right - 95}" y="{height - 25}" class="small">Call IV higher</text>',
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def render_png(rows: list[dict[str, Any]], output_path: Path) -> None:
    """Render a high-resolution, Word-compatible chart using Matplotlib."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ordered = sorted(rows, key=lambda item: item["cpiv"])
    fig, axis = plt.subplots(figsize=(10.2, 5.8), layout="constrained")
    y_values = list(range(len(ordered)))
    axis.axvline(0, color="#44515f", linewidth=1.2, zorder=0)
    axis.set_yticks(y_values, [row["symbol"] for row in ordered])
    axis.invert_yaxis()
    for y_value, row in zip(y_values, ordered, strict=True):
        point = row["cpiv"] * 100
        low = row["interval_low"] * 100
        high = row["interval_high"] * 100
        color = "#a8433c" if point < 0 else "#117b69"
        axis.barh(y_value, point, color=color, height=0.5, alpha=0.82, zorder=2)
        axis.errorbar(
            point,
            y_value,
            xerr=[[point - low], [high - point]],
            fmt="o",
            color="#182a3a",
            ecolor="#182a3a",
            elinewidth=1.2,
            capsize=3,
            markersize=3.5,
            zorder=3,
        )
    limit = max(abs(row[key] * 100) for row in ordered for key in ("interval_low", "interval_high"))
    axis.set_xlim(-limit * 1.32, limit * 1.32)
    axis.set_xlabel("Call IV - put IV (percentage points)")
    axis.set_title("Ten fictional, matched option pairs", loc="left", weight="bold", pad=14)
    axis.text(
        0,
        1.015,
        "Bars = synthetic point values; whiskers = assumed quote-width sensitivity",
        transform=axis.transAxes,
        fontsize=9,
        color="#596675",
        va="bottom",
    )
    axis.grid(axis="x", color="#dce2e8", linewidth=0.8, zorder=0)
    axis.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        axis.spines[spine].set_visible(False)
    axis.tick_params(axis="y", length=0, pad=8)
    fig.savefig(output_path, dpi=190, facecolor="white")
    plt.close(fig)


def write_outputs(
    output_dir: Path,
    replicates: int = SIMULATION_REPLICATES,
) -> dict[str, str]:
    rows = build_records()
    stress_results = build_stress_results(replicates)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "synthetic_cpiv_demo.csv"
    json_path = output_dir / "synthetic_cpiv_demo.json"
    svg_path = output_dir / "synthetic_cpiv_demo.svg"
    png_path = output_dir / "synthetic_cpiv_demo.png"
    fields = list(rows[0])
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    metadata = {
        "status": "synthetic_educational_example_only",
        "market_data_used": False,
        "network_access_used": False,
        "parameters": {
            "spot_usd": SPOT,
            "strike_usd": STRIKE,
            "days_to_expiry": DAYS,
            "risk_free_rate": RATE,
            "dividend_yield": DIVIDEND_YIELD,
            "put_iv": PUT_IV,
            "call_iv_range": [0.16, 0.25],
            "quote_half_spread_usd": QUOTE_HALF_SPREAD,
            "bsm_iv_bracket": [1e-8, MAX_IV],
            "ranking": "lowest two short-side candidates; highest two long-side candidates",
        },
        "rows": rows,
        "warning": "No historical sample, backtest, alpha estimate, or trading result is included.",
    }
    json_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    svg_path.write_text(render_svg(rows), encoding="utf-8")
    render_png(rows, png_path)
    stress_path = output_dir / "cpiv_stress_results.json"
    stress_path.write_text(
        json.dumps(stress_results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    figure_paths = render_stress_figures(stress_results, output_dir)
    return {
        "csv": str(csv_path),
        "json": str(json_path),
        "svg": str(svg_path),
        "png": str(png_path),
        "stress_json": str(stress_path),
        **figure_paths,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--replicates", type=int, default=SIMULATION_REPLICATES)
    args = parser.parse_args()
    print(json.dumps(write_outputs(args.output, args.replicates), indent=2))


if __name__ == "__main__":
    main()
