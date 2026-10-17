"""American-put tree and approximation cross-check (author-run, synthetic, no market data).

Methods: CRR and Jarrow-Rudd trees on 800 to 6,400 steps; a Leisen-Reimer tree on odd grids
801 to 6,401; and the Barone-Adesi-Whaley quadratic approximation, which is an approximation
rather than an exact value. Richardson extrapolation of the CRR and Jarrow-Rudd trees is written
as a diagnostic only: its successive estimates are not monotone, so it is not an end-point.
The end-point for the envelope is the finest grid of each tree (CRR and Jarrow-Rudd at 6,400,
Leisen-Reimer at 6,401). Each price is converted to a BSM implied volatility with the codebase
inverter and to a CPIV-style offset, 100 * (reference vol - put IV).

This is an author-run numerical cross-check. It is not an independent exact benchmark.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np
from research.cpiv import build_demo as demo

STATUS = "author_run_synthetic_numerical_check"
TREE_STEPS = (800, 1600, 3200, 6400)
RICHARDSON_PAIRS = ((800, 1600), (3200, 6400))
LEISEN_REIMER_STEPS = (801, 1601, 3201, 6401)
ENDPOINTS = (("CRR", "6400"), ("Jarrow-Rudd", "6400"), ("Leisen-Reimer", "6401"))

SCENARIOS: tuple[dict[str, Any], ...] = (
    {"name": "atm_30d_base", "spot": 100.0, "strike": 100.0, "days": 30,
     "rate": 0.05, "q": 0.0, "sigma": 0.20},
    {"name": "deep_itm_90d_high_rate", "spot": 100.0, "strike": 120.0, "days": 90,
     "rate": 0.10, "q": 0.0, "sigma": 0.20},
    {"name": "zero_rate_control_30d", "spot": 100.0, "strike": 100.0, "days": 30,
     "rate": 0.0, "q": 0.0, "sigma": 0.20},
    {"name": "dividend_365d_otm_put", "spot": 100.0, "strike": 90.0, "days": 365,
     "rate": 0.03, "q": 0.02, "sigma": 0.25},
)


def _years(days: int) -> float:
    return days / 365.0


def _tree_put(spot: float, strike: float, up: float, down: float, probability: float,
              discount: float, steps: int, exercise: bool) -> float:
    """Backward induction over a recombining tree; vectorised over nodes per time step."""
    if steps < 1:
        raise ValueError("steps must be positive")
    terminal = np.arange(steps + 1)
    values = np.maximum(strike - spot * up**terminal * down**(steps - terminal), 0.0)
    for time_step in range(steps - 1, -1, -1):
        continuation = discount * (probability * values[1:] + (1.0 - probability) * values[:-1])
        if exercise:
            nodes = np.arange(time_step + 1)
            intrinsic = strike - spot * up**nodes * down**(time_step - nodes)
            values = np.maximum(continuation, intrinsic)
        else:
            values = continuation
    return float(values[0])


def crr_put(spot: float, strike: float, days: int, rate: float, q: float, sigma: float,
            steps: int, *, exercise: bool = True) -> float:
    dt = _years(days) / steps
    up = math.exp(sigma * math.sqrt(dt))
    down = 1.0 / up
    probability = (math.exp((rate - q) * dt) - down) / (up - down)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("CRR risk-neutral probability must lie in [0, 1]")
    return _tree_put(spot, strike, up, down, probability, math.exp(-rate * dt), steps, exercise)


def jarrow_rudd_put(spot: float, strike: float, days: int, rate: float, q: float,
                    sigma: float, steps: int, *, exercise: bool = True) -> float:
    dt = _years(days) / steps
    drift = (rate - q - 0.5 * sigma * sigma) * dt
    up = math.exp(drift + sigma * math.sqrt(dt))
    down = math.exp(drift - sigma * math.sqrt(dt))
    return _tree_put(spot, strike, up, down, 0.5, math.exp(-rate * dt), steps, exercise)


def _leisen_reimer_h(z: float, steps: int) -> float:
    sign = 1.0 if z >= 0.0 else -1.0
    scaled = z / (steps + 1.0 / 3.0 + 0.1 / (steps + 1.0))
    return 0.5 + sign * math.sqrt(0.25 - 0.25 * math.exp(-scaled * scaled * (steps + 1.0 / 6.0)))


def leisen_reimer_put(spot: float, strike: float, days: int, rate: float, q: float,
                      sigma: float, steps: int, *, exercise: bool = True) -> float:
    if steps < 1 or steps % 2 == 0:
        raise ValueError("Leisen-Reimer needs an odd number of steps")
    years = _years(days)
    root_t = sigma * math.sqrt(years)
    d1 = (math.log(spot / strike) + (rate - q + 0.5 * sigma * sigma) * years) / root_t
    d2 = d1 - root_t
    p_prime = _leisen_reimer_h(d1, steps)
    probability = _leisen_reimer_h(d2, steps)
    dt = years / steps
    growth = math.exp((rate - q) * dt)
    up = growth * p_prime / probability
    down = growth * (1.0 - p_prime) / (1.0 - probability)
    return _tree_put(spot, strike, up, down, probability, math.exp(-rate * dt), steps, exercise)


def baw_american_put(spot: float, strike: float, days: int, rate: float, q: float,
                     sigma: float) -> float:
    """Barone-Adesi and Whaley (1987) quadratic approximation; not an exact American value."""
    if rate <= 0.0:
        raise ValueError("Barone-Adesi-Whaley needs a positive rate (1 - exp(-rT) > 0)")
    years = _years(days)
    carry = rate - q
    m_coef = 2.0 * rate / (sigma * sigma)
    n_coef = 2.0 * carry / (sigma * sigma)
    k_coef = 1.0 - math.exp(-rate * years)
    q2 = (-(n_coef - 1.0) - math.sqrt((n_coef - 1.0) ** 2 + 4.0 * m_coef / k_coef)) / 2.0
    root_t = sigma * math.sqrt(years)
    normal = NormalDist()

    def d1_at(price: float) -> float:
        return (math.log(price / strike) + (carry + 0.5 * sigma * sigma) * years) / root_t

    def early_term(price: float) -> float:
        return 1.0 - math.exp(-q * years) * normal.cdf(-d1_at(price))

    def residual(price: float) -> float:
        european = demo.bs_price("put", price, strike, days, rate, q, sigma)
        return strike - price - european + early_term(price) * price / q2

    low, high = 1e-9 * strike, strike
    if residual(low) <= 0.0 or residual(high) >= 0.0:
        raise ValueError("no critical-price bracket for Barone-Adesi-Whaley")
    for _ in range(200):
        mid = 0.5 * (low + high)
        if residual(mid) > 0.0:
            low = mid
        else:
            high = mid
    critical = 0.5 * (low + high)
    if spot <= critical:
        return strike - spot
    a2 = -(critical / q2) * early_term(critical)
    european = demo.bs_price("put", spot, strike, days, rate, q, sigma)
    return european + a2 * float((spot / critical) ** q2)


def _richardson(coarse: float, fine: float) -> float:
    return 2.0 * fine - coarse


def _cpiv_pp(price: float, case: dict[str, Any]) -> tuple[float, float]:
    put_iv = demo.implied_volatility("put", price, case["spot"], case["strike"], case["days"],
                                     case["rate"], case["q"])
    return put_iv, 100.0 * (case["sigma"] - put_iv)


def scenario_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in SCENARIOS:
        params = {key: case[key] for key in ("spot", "strike", "days", "rate", "q", "sigma")}
        european = demo.bs_price("put", case["spot"], case["strike"], case["days"],
                                 case["rate"], case["q"], case["sigma"])
        prices: list[tuple[str, str, float]] = []
        for label, pricer in (("CRR", crr_put), ("Jarrow-Rudd", jarrow_rudd_put)):
            tree = {steps: pricer(**params, steps=steps) for steps in TREE_STEPS}
            prices.extend((label, str(steps), tree[steps]) for steps in TREE_STEPS)
            for coarse, fine in RICHARDSON_PAIRS:
                prices.append((f"{label}_Richardson", f"{coarse}/{fine}",
                               _richardson(tree[coarse], tree[fine])))
        for steps in LEISEN_REIMER_STEPS:
            prices.append(("Leisen-Reimer", str(steps),
                           leisen_reimer_put(**params, steps=steps)))
        if case["rate"] > 0.0:
            prices.append(("Barone-Adesi-Whaley", "approximation",
                           baw_american_put(**params)))
        for method, steps_label, price in prices:
            put_iv, cpiv = _cpiv_pp(price, case)
            rows.append({
                "scenario": case["name"],
                "method": method,
                "steps": steps_label,
                "price_usd": price,
                "price_minus_bsm_european_usd": price - european,
                "put_iv": put_iv,
                "cpiv_pp": cpiv,
                "status": STATUS,
            })
    return rows


def envelope_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per scenario: range of the finest-grid CPIVs for CRR, Jarrow-Rudd and Leisen-Reimer.

    Barone-Adesi-Whaley is an approximation and is reported beside the envelope, not in it.
    """
    envelope: list[dict[str, Any]] = []
    for case in SCENARIOS:
        lookup = {(row["method"], row["steps"]): row["cpiv_pp"]
                  for row in rows if row["scenario"] == case["name"]}
        values = [lookup[key] for key in ENDPOINTS]
        reference = lookup[("Leisen-Reimer", "6401")]
        baw = lookup.get(("Barone-Adesi-Whaley", "approximation"))
        envelope.append({
            "scenario": case["name"],
            "methods": len(values),
            "min_cpiv_pp": min(values),
            "max_cpiv_pp": max(values),
            "mean_cpiv_pp": sum(values) / len(values),
            "spread_pp": max(values) - min(values),
            "lr_6401_minus_3201_pp": reference - lookup[("Leisen-Reimer", "3201")],
            "baw_minus_lr_6401_pp": "" if baw is None else baw - reference,
            "status": STATUS,
        })
    return envelope


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = scenario_rows()
    _write_csv(args.output / "american_put_crosscheck.csv", rows)
    _write_csv(args.output / "american_put_envelope.csv", envelope_rows(rows))
    print(f"american_put_crosscheck: {len(rows)} method rows across {len(SCENARIOS)} scenarios")


if __name__ == "__main__":
    main()
