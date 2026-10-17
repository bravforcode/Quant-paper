"""Synthetic comparison of three CPIV ranking workflows against known truth.

Author-run synthetic check. The constants below and the claim rule in ``claim_rows`` are fixed
in this file; no separate time-stamped pre-registration is part of the package. It is not
independent replication and carries no market-data evidence.

E0 ranks names by raw-midpoint CPIV. E1 adds the absolute-vega guard. E2 applies the
Table 10 identification screen and keeps unresolved pairs undecided.

Stress scenario: the call quote is centred on the true price plus ``multiple * h``. Rows with
multiple 0.0 are the baseline design and the only rows that enter the claim rule.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from research.cpiv import build_demo as demo
from research.cpiv.r11_price_resolution import (
    RESOLUTION_VEGA_GUARD,
    _exact_iv_shift,
    _otm_equivalent_time_value,
)

D_SEED = 20261018
SPOT = 100.0
RATE = 0.05
DIVIDEND_YIELD = 0.02
MONEYNESS_RATIOS = (0.8, 0.9, 1.0, 1.1, 1.2)
DAYS = (30, 90)
PUT_SIGMAS = (0.10, 0.20, 0.40)
TAU_PP_RANGE = 5.0
TIE_MARGIN_PP = 0.5
TAU_IV_PP = 0.10
UNIVERSE_SIZES = (10, 50)
TICKS = (0.005, 0.01, 0.05)
HALF_SPREADS = (0.01, 0.05, 0.25)
REPLICATES = 200
METHODS = ("E0_raw_midpoint", "E1_vega_guard", "E2_table10_workflow")
METRICS = (
    "decided_fraction",
    "wrong_among_decided",
    "false_exclusion",
    "false_resolution",
    "decided_tie_share",
)
CALL_OFFSET_MULTIPLES = (0.0, 1.5)
OUTCOME_KEYS = (
    "ordered",
    "e2_decided",
    "e0_undecided_on_e2",
    "e0_wrong_on_e2",
    "e0_correct_on_e2_undecided",
    "e0_wrong_all",
)
STATUS = "author_run_synthetic_workflow_comparison"

Record = dict[str, Any]
Quote = tuple[float, float, float]


def observed_quote(price: float, tick: float, half_spread: float, offset: float = 0.0) -> Quote:
    """Return (midpoint, bid, ask): price plus offset, rounded to a tick; bid floored at zero."""
    mid = tick * math.floor((price + offset) / tick + 0.5)
    return mid, max(mid - half_spread, 0.0), mid + half_spread


def draw_cross_section(rng: random.Random, universe_size: int) -> list[dict[str, Any]]:
    """Draw true-priced names with CPIV tau = 100 (sigma_C - sigma_P) uniform on (-5, 5) pp."""
    names: list[dict[str, Any]] = []
    for _ in range(universe_size):
        ratio = rng.choice(MONEYNESS_RATIOS)
        days = rng.choice(DAYS)
        sigma_put = rng.choice(PUT_SIGMAS)
        tau_pp = rng.uniform(-TAU_PP_RANGE, TAU_PP_RANGE)
        sigma_call = sigma_put + tau_pp / 100.0
        strike = SPOT / ratio
        names.append(
            {
                "tau_pp": tau_pp,
                "ratio": ratio,
                "days": days,
                "strike": strike,
                "sigma_put": sigma_put,
                "sigma_call": sigma_call,
                # The BSM formula can return about -1e-15 for deep out-of-the-money legs;
                # a true premium is non-negative, so floor the numerical residue at zero.
                "call_price": max(
                    0.0,
                    demo.bs_price("call", SPOT, strike, days, RATE, DIVIDEND_YIELD, sigma_call),
                ),
                "put_price": max(
                    0.0,
                    demo.bs_price("put", SPOT, strike, days, RATE, DIVIDEND_YIELD, sigma_put),
                ),
            }
        )
    return names


def _safe_iv(option_type: str, price: float, strike: float, days: int) -> float | None:
    try:
        return demo.implied_volatility(
            option_type, price, SPOT, strike, days, RATE, DIVIDEND_YIELD
        )
    except ValueError:
        return None


def _quote_ivs(
    option_type: str, quote: Quote, strike: float, days: int
) -> tuple[float, float] | None:
    bid_iv = _safe_iv(option_type, quote[1], strike, days)
    ask_iv = _safe_iv(option_type, quote[2], strike, days)
    if bid_iv is None or ask_iv is None:
        return None
    return bid_iv, ask_iv


def _e2_range(
    name: dict[str, Any],
    tick: float,
    call_quote: Quote,
    put_quote: Quote,
    iv_call: float,
    iv_put: float,
) -> tuple[bool, float, float]:
    """Table 10 screen: OTM value >= tick, shocks invert within TAU_IV_PP, bid/ask IVs finite.

    Returns (passes, lower_pp, upper_pp) for the quote-implied CPIV range.
    """
    strike = name["strike"]
    days = name["days"]
    failed = (False, 0.0, 0.0)
    worst_shift_pp = 0.0
    for option_type, quote, iv_mid in (("call", call_quote, iv_call), ("put", put_quote, iv_put)):
        mid = quote[0]
        otm_value = _otm_equivalent_time_value(
            option_type, mid, SPOT, strike, days, RATE, DIVIDEND_YIELD
        )
        if otm_value < tick:
            return failed
        for shocked in (mid - tick, mid + tick):
            shift_pp, _status = _exact_iv_shift(
                option_type, shocked, SPOT, strike, days, RATE, DIVIDEND_YIELD, iv_mid
            )
            if shift_pp is None:
                return failed
            worst_shift_pp = max(worst_shift_pp, abs(shift_pp))
    if worst_shift_pp > TAU_IV_PP:
        return failed
    call_bid_ask = _quote_ivs("call", call_quote, strike, days)
    put_bid_ask = _quote_ivs("put", put_quote, strike, days)
    if call_bid_ask is None or put_bid_ask is None:
        return failed
    spreads = [100.0 * (call_iv - put_iv) for call_iv in call_bid_ask for put_iv in put_bid_ask]
    return True, min(spreads), max(spreads)


def analyse_name(
    name: dict[str, Any], *, tick: float, half_spread: float, call_offset: float = 0.0
) -> Record:
    """Return the observed-quote summary each workflow uses for one name."""
    strike = name["strike"]
    days = name["days"]
    call_quote = observed_quote(name["call_price"], tick, half_spread, call_offset)
    put_quote = observed_quote(name["put_price"], tick, half_spread)
    record: Record = {
        "tau": name["tau_pp"],
        "cpiv_mid": None,
        "vega_ok": False,
        "e2_pass": False,
        "lo": 0.0,
        "hi": 0.0,
    }
    iv_call = _safe_iv("call", call_quote[0], strike, days)
    iv_put = _safe_iv("put", put_quote[0], strike, days)
    if iv_call is None or iv_put is None:
        return record
    record["cpiv_mid"] = 100.0 * (iv_call - iv_put)
    vega_call = demo.bs_vega_per_vol_point(SPOT, strike, days, RATE, DIVIDEND_YIELD, iv_call)
    vega_put = demo.bs_vega_per_vol_point(SPOT, strike, days, RATE, DIVIDEND_YIELD, iv_put)
    record["vega_ok"] = min(vega_call, vega_put) * 100.0 >= RESOLUTION_VEGA_GUARD
    passes, lower, upper = _e2_range(name, tick, call_quote, put_quote, iv_call, iv_put)
    record.update(e2_pass=passes, lo=lower, hi=upper)
    return record


def truth_decision(first: Record, second: Record) -> int | None:
    """Return +1 or -1 for a true ordering with margin, or None for a tie."""
    gap = first["tau"] - second["tau"]
    if abs(gap) < TIE_MARGIN_PP:
        return None
    return 1 if gap > 0 else -1


def _sign(first: float, second: float) -> int:
    if first > second:
        return 1
    if first < second:
        return -1
    return 0


def decide_e0(first: Record, second: Record) -> int:
    if first["cpiv_mid"] is None or second["cpiv_mid"] is None:
        return 0
    return _sign(first["cpiv_mid"], second["cpiv_mid"])


def decide_e1(first: Record, second: Record) -> int:
    if not (first["vega_ok"] and second["vega_ok"]):
        return 0
    return decide_e0(first, second)


def decide_e2(first: Record, second: Record) -> int:
    if not (first["e2_pass"] and second["e2_pass"]):
        return 0
    if first["lo"] > second["hi"]:
        return 1
    if first["hi"] < second["lo"]:
        return -1
    return 0


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def score_pairs(names: Sequence[Record], decide: Callable[[Record, Record], int]) -> dict[str, Any]:
    """Score every unordered pair against truth; ties are excluded from ordered metrics."""
    pairs = ordered = decided_total = decided_ordered = decided_tie = wrong = undecided = 0
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            pairs += 1
            truth = truth_decision(first, second)
            if truth is not None:
                ordered += 1
            decision = decide(first, second)
            if decision != 0:
                decided_total += 1
                if truth is None:
                    decided_tie += 1
                else:
                    decided_ordered += 1
                    wrong += int(decision != truth)
            elif truth is not None:
                undecided += 1
    return {
        "pairs": pairs,
        "ordered": ordered,
        "decided_total": decided_total,
        "decided_ordered": decided_ordered,
        "decided_tie": decided_tie,
        "wrong": wrong,
        "undecided_ordered": undecided,
        "decided_fraction": _ratio(decided_total, pairs),
        "wrong_among_decided": _ratio(wrong, decided_ordered),
        "false_exclusion": _ratio(undecided, ordered),
        "false_resolution": _ratio(wrong, ordered),
        "decided_tie_share": _ratio(decided_tie, decided_total),
    }


def pair_outcomes(names: Sequence[Record]) -> dict[str, int]:
    """Tally truly ordered pairs by E2 status and E0 outcome, for the matched comparison."""
    counts = dict.fromkeys(OUTCOME_KEYS, 0)
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            truth = truth_decision(first, second)
            if truth is None:
                continue
            counts["ordered"] += 1
            e0 = decide_e0(first, second)
            if e0 != 0 and e0 != truth:
                counts["e0_wrong_all"] += 1
            if decide_e2(first, second) != 0:
                counts["e2_decided"] += 1
                if e0 == 0:
                    counts["e0_undecided_on_e2"] += 1
                elif e0 != truth:
                    counts["e0_wrong_on_e2"] += 1
            elif e0 == truth:
                counts["e0_correct_on_e2_undecided"] += 1
    return counts


def differing_share(names: Sequence[Record]) -> float:
    """Share of all pairs on which E1 and E0 give different decisions."""
    pairs = differing = 0
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            pairs += 1
            differing += int(decide_e1(first, second) != decide_e0(first, second))
    return differing / pairs


def coverage_failure_share(
    draw: Sequence[dict[str, Any]], tick: float, half_spread: float, call_offset: float
) -> float:
    """Share of names whose observed call or put bid-ask interval misses the true premium."""
    misses = 0
    for name in draw:
        call = observed_quote(name["call_price"], tick, half_spread, call_offset)
        put = observed_quote(name["put_price"], tick, half_spread)
        call_covered = call[1] <= name["call_price"] <= call[2]
        put_covered = put[1] <= name["put_price"] <= put[2]
        misses += int(not (call_covered and put_covered))
    return misses / len(draw)


def _mean_and_mcse(values: Sequence[float]) -> tuple[float | None, float | None]:
    count = len(values)
    if count == 0:
        return None, None
    mean = sum(values) / count
    if count < 2:
        return mean, None
    variance = sum((value - mean) ** 2 for value in values) / (count - 1)
    return mean, math.sqrt(variance / count)


def _replicate_rng(universe_size: int, replicate: int) -> random.Random:
    return random.Random(f"{D_SEED}:{universe_size}:{replicate}")


def run_comparison(
    *,
    replicates: int = REPLICATES,
    universe_sizes: Sequence[int] = UNIVERSE_SIZES,
    ticks: Sequence[float] = TICKS,
    half_spreads: Sequence[float] = HALF_SPREADS,
    call_offset_multiples: Sequence[float] = CALL_OFFSET_MULTIPLES,
) -> list[dict[str, Any]]:
    """Return one row per (cell, offset, method, metric); cross-sections are shared across cells.

    Besides E0, E1 and E2, the rows carry diagnostics: the E0 outcome on the pairs E2 decides
    (matched comparison), the correct E0 orders E2 abstains on per E0 error, the share of names
    without a usable midpoint IV, the share whose vega guard fails despite a midpoint IV, and the
    share whose observed bid-ask interval misses the true premium.
    """
    deciders: dict[str, Callable[[Record, Record], int]] = {
        "E0_raw_midpoint": decide_e0,
        "E1_vega_guard": decide_e1,
        "E2_table10_workflow": decide_e2,
    }
    rows: list[dict[str, Any]] = []
    for universe_size in universe_sizes:
        draws = [
            draw_cross_section(_replicate_rng(universe_size, replicate), universe_size)
            for replicate in range(replicates)
        ]
        for tick in ticks:
            for half_spread in half_spreads:
                for multiple in call_offset_multiples:
                    values: dict[str, dict[str, list[float]]] = {
                        method: {metric: [] for metric in METRICS} for method in METHODS
                    }
                    values["E1_vs_E0"] = {"differing_pairs_share": []}
                    values["universe_diagnostic"] = {
                        "no_midpoint_iv_share": [],
                        "e2_screen_fail_share": [],
                        "vega_fail_with_midpoint_share": [],
                        "quote_coverage_failure_share": [],
                    }
                    values["matched_E0_on_E2_pairs"] = {
                        "wrong_among_decided": [],
                        "undecided_share": [],
                    }
                    totals = dict.fromkeys(OUTCOME_KEYS, 0)
                    for draw in draws:
                        names = [
                            analyse_name(
                                name,
                                tick=tick,
                                half_spread=half_spread,
                                call_offset=multiple * half_spread,
                            )
                            for name in draw
                        ]
                        for method, decide in deciders.items():
                            scored = score_pairs(names, decide)
                            for metric in METRICS:
                                if scored[metric] is not None:
                                    values[method][metric].append(scored[metric])
                        values["E1_vs_E0"]["differing_pairs_share"].append(differing_share(names))
                        values["universe_diagnostic"]["no_midpoint_iv_share"].append(
                            sum(record["cpiv_mid"] is None for record in names) / len(names)
                        )
                        values["universe_diagnostic"]["e2_screen_fail_share"].append(
                            sum(not record["e2_pass"] for record in names) / len(names)
                        )
                        values["universe_diagnostic"]["vega_fail_with_midpoint_share"].append(
                            sum(
                                not record["vega_ok"] and record["cpiv_mid"] is not None
                                for record in names
                            )
                            / len(names)
                        )
                        values["universe_diagnostic"]["quote_coverage_failure_share"].append(
                            coverage_failure_share(draw, tick, half_spread, multiple * half_spread)
                        )
                        outcome = pair_outcomes(names)
                        for key in OUTCOME_KEYS:
                            totals[key] += outcome[key]
                        if outcome["e2_decided"]:
                            matched = values["matched_E0_on_E2_pairs"]
                            matched["wrong_among_decided"].append(
                                outcome["e0_wrong_on_e2"] / outcome["e2_decided"]
                            )
                            matched["undecided_share"].append(
                                outcome["e0_undecided_on_e2"] / outcome["e2_decided"]
                            )
                    cell = {
                        "universe_n": universe_size,
                        "tick": tick,
                        "half_spread": half_spread,
                        "call_offset_multiple": multiple,
                    }
                    for method, metrics in values.items():
                        for metric, samples in metrics.items():
                            mean, mcse = _mean_and_mcse(samples)
                            rows.append(
                                {
                                    **cell,
                                    "method": method,
                                    "metric": metric,
                                    "mean": mean,
                                    "mcse": mcse,
                                    "replicates_used": len(samples),
                                    "replicates": replicates,
                                    "status": STATUS,
                                }
                            )
                    # Ratio of totals: E0 correct orders on pairs E2 abstains on, per E0 error.
                    cost = (
                        totals["e0_correct_on_e2_undecided"] / totals["e0_wrong_all"]
                        if totals["e0_wrong_all"]
                        else None
                    )
                    rows.append(
                        {
                            **cell,
                            "method": "E2_abstention_cost",
                            "metric": "e0_correct_on_abstained_per_e0_error",
                            "mean": cost,
                            "mcse": None,
                            "replicates_used": replicates,
                            "replicates": replicates,
                            "status": STATUS,
                        }
                    )
    return rows


def universe_breakdown(universe_sizes: Sequence[int] = UNIVERSE_SIZES) -> list[dict[str, Any]]:
    """Share of names without a midpoint IV, by tick, S/K ratio, tenor and leg (no spread)."""
    rows: list[dict[str, Any]] = []
    for universe_size in universe_sizes:
        draws = [
            draw_cross_section(_replicate_rng(universe_size, replicate), universe_size)
            for replicate in range(REPLICATES)
        ]
        for tick in TICKS:
            tally: dict[tuple[float, int, str], list[int]] = {}
            for draw in draws:
                for name in draw:
                    for leg, price in (("call", name["call_price"]), ("put", name["put_price"])):
                        mid = observed_quote(price, tick, 0.0)[0]
                        iv = _safe_iv(leg, mid, name["strike"], name["days"])
                        cell = tally.setdefault((name["ratio"], name["days"], leg), [0, 0])
                        cell[0] += int(iv is None)
                        cell[1] += 1
            for (ratio, days, leg), (missing, total) in sorted(tally.items()):
                rows.append(
                    {
                        "universe_n": universe_size,
                        "tick": tick,
                        "spot_over_strike": ratio,
                        "days": days,
                        "leg": leg,
                        "no_midpoint_iv": missing,
                        "names": total,
                        "share": missing / total,
                    }
                )
    return rows


def _stat(
    index: dict[tuple[Any, ...], dict[str, Any]], key: tuple[Any, ...]
) -> tuple[float | None, float | None]:
    row = index[key]
    return row["mean"], row["mcse"]


def claim_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply the claim rule to each baseline cell (E2 vs E0 wrong-order rate)."""
    index = {
        (row["universe_n"], row["tick"], row["half_spread"], row["method"], row["metric"]): row
        for row in rows
    }
    cells = sorted({(row["universe_n"], row["tick"], row["half_spread"]) for row in rows})
    claims: list[dict[str, Any]] = []
    for universe_size, tick, half_spread in cells:
        cell = (universe_size, tick, half_spread)
        e0_wrong, e0_wrong_mcse = _stat(index, (*cell, "E0_raw_midpoint", "wrong_among_decided"))
        e2_wrong, e2_wrong_mcse = _stat(
            index, (*cell, "E2_table10_workflow", "wrong_among_decided")
        )
        e0_excl, e0_excl_mcse = _stat(index, (*cell, "E0_raw_midpoint", "false_exclusion"))
        e2_excl, e2_excl_mcse = _stat(index, (*cell, "E2_table10_workflow", "false_exclusion"))
        reduction: float | None = None
        combined: float | None = None
        credited = False
        if (
            e0_wrong is not None
            and e2_wrong is not None
            and e0_wrong_mcse is not None
            and e2_wrong_mcse is not None
        ):
            reduction = e0_wrong - e2_wrong
            combined = math.sqrt(e0_wrong_mcse**2 + e2_wrong_mcse**2)
            credited = e0_wrong > 0 and reduction > 2.0 * combined
        exclusion_increase: float | None = None
        exclusion_mcse: float | None = None
        if (
            e0_excl is not None
            and e2_excl is not None
            and e0_excl_mcse is not None
            and e2_excl_mcse is not None
        ):
            exclusion_increase = e2_excl - e0_excl
            exclusion_mcse = math.sqrt(e0_excl_mcse**2 + e2_excl_mcse**2)
        claims.append(
            {
                "universe_n": universe_size,
                "tick": tick,
                "half_spread": half_spread,
                "e0_wrong_rate": e0_wrong,
                "e0_wrong_mcse": e0_wrong_mcse,
                "e2_wrong_rate": e2_wrong,
                "e2_wrong_mcse": e2_wrong_mcse,
                "wrong_reduction": reduction,
                "combined_mcse": combined,
                "benefit_credited": credited,
                "e0_false_exclusion": e0_excl,
                "e2_false_exclusion": e2_excl,
                "false_exclusion_increase": exclusion_increase,
                "false_exclusion_increase_mcse": exclusion_mcse,
            }
        )
    return claims


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    args = parser.parse_args()
    if args.replicates < 2:
        parser.error("--replicates must be at least 2")
    args.output.mkdir(parents=True, exist_ok=True)
    rows = run_comparison(replicates=args.replicates)
    baseline = [row for row in rows if row["call_offset_multiple"] == 0.0]
    claims = claim_rows(baseline)
    breakdown = universe_breakdown()
    _write_csv(args.output / "workflow_comparison.csv", rows)
    _write_csv(args.output / "workflow_comparison_claims.csv", claims)
    _write_csv(args.output / "workflow_universe_diagnostics.csv", breakdown)
    benefits = sum(1 for claim in claims if claim["benefit_credited"])
    print(f"wrote {len(rows)} metric rows, {len(claims)} claim rows; benefits credited: {benefits}")


if __name__ == "__main__":
    main()
