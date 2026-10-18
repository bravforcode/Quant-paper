"""Per-name call-midpoint stress for the Section 7.9 workflow comparison.

Each name's call midpoint is moved by its own draw from U(-k*h, k*h), where h is the
half-spread, so the quote error differs across names instead of sharing one shift. The
cross-sections, put quotes and tie margins are those of workflow_comparison.py. Results go
to a new output folder; workflow_comparison.py and its manifested outputs are not modified.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Any, Sequence

from research.cpiv import workflow_comparison as wc

STRESS_K = (4.0, 8.0)
WILSON_Z = 1.959963984540054
METHOD_E0 = "E0_raw_midpoint"
METHOD_E2 = "E2_table10_workflow"
CLAIM_METRICS = ("wrong_among_decided", "false_exclusion")
POOLED_KEYS = ("ordered", "decided_ordered", "wrong", "undecided_ordered")


def wilson_interval(successes: int, trials: int) -> tuple[float | None, float | None]:
    """Wilson 95% interval for a binomial share; (None, None) when there are no trials."""
    if trials == 0:
        return None, None
    z2 = WILSON_Z**2
    share = successes / trials
    centre = (share + z2 / (2 * trials)) / (1 + z2 / trials)
    half = WILSON_Z * math.sqrt(share * (1 - share) / trials + z2 / (4 * trials**2))
    half /= 1 + z2 / trials
    low = 0.0 if successes == 0 else max(0.0, centre - half)
    high = 1.0 if successes == trials else min(1.0, centre + half)
    return low, high


def draw_offsets(universe_size: int, replicate: int, k: float, half_spread: float) -> list[float]:
    """One call-midpoint shift per name, U(-k*h, k*h); unit draws depend only on design and replicate."""
    rng = random.Random(f"{wc.D_SEED}:shift:{universe_size}:{k}:{replicate}")
    return [k * half_spread * rng.uniform(-1.0, 1.0) for _ in range(universe_size)]


def quote_miss_count(
    draw: Sequence[dict[str, Any]],
    *,
    tick: float,
    half_spread: float,
    offsets: Sequence[float],
) -> int:
    """Names whose observed call or put bid-ask interval misses the true premium."""
    misses = 0
    for name, offset in zip(draw, offsets, strict=True):
        call = wc.observed_quote(name["call_price"], tick, half_spread, offset)
        put = wc.observed_quote(name["put_price"], tick, half_spread)
        covered = call[1] <= name["call_price"] <= call[2] and put[1] <= name["put_price"] <= put[2]
        misses += int(not covered)
    return misses


def score_replicate(
    draw: Sequence[dict[str, Any]],
    *,
    tick: float,
    half_spread: float,
    offsets: Sequence[float],
) -> dict[str, Any]:
    """Score E0 and E2 on one cross-section under per-name call shifts."""
    names = [
        wc.analyse_name(name, tick=tick, half_spread=half_spread, call_offset=offset)
        for name, offset in zip(draw, offsets, strict=True)
    ]
    return {
        "E0": wc.score_pairs(names, wc.decide_e0),
        "E2": wc.score_pairs(names, wc.decide_e2),
        "quote_misses": quote_miss_count(draw, tick=tick, half_spread=half_spread, offsets=offsets),
    }


def run_stress(
    *,
    replicates: int = wc.REPLICATES,
    universe_sizes: Sequence[int] = wc.UNIVERSE_SIZES,
    ticks: Sequence[float] = wc.TICKS,
    half_spreads: Sequence[float] = wc.HALF_SPREADS,
    ks: Sequence[float] = STRESS_K,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (summary rows, claim rows) for every stress cell; claims use the Section 7.9 rule."""
    summary: list[dict[str, Any]] = []
    claim_inputs: dict[float, list[dict[str, Any]]] = {k: [] for k in ks}
    for universe_size in universe_sizes:
        draws = [
            wc.draw_cross_section(wc._replicate_rng(universe_size, replicate), universe_size)
            for replicate in range(replicates)
        ]
        for k in ks:
            for tick in ticks:
                for half_spread in half_spreads:
                    pooled = {method: dict.fromkeys(POOLED_KEYS, 0) for method in (METHOD_E0, METHOD_E2)}
                    per_replicate: dict[str, dict[str, list[float]]] = {
                        method: {metric: [] for metric in CLAIM_METRICS}
                        for method in (METHOD_E0, METHOD_E2)
                    }
                    misses = 0
                    for replicate, draw in enumerate(draws):
                        offsets = draw_offsets(universe_size, replicate, k, half_spread)
                        scored = score_replicate(
                            draw, tick=tick, half_spread=half_spread, offsets=offsets
                        )
                        misses += scored["quote_misses"]
                        for method, label in ((METHOD_E0, "E0"), (METHOD_E2, "E2")):
                            result = scored[label]
                            for field in POOLED_KEYS:
                                pooled[method][field] += result[field]
                            for metric in CLAIM_METRICS:
                                if result[metric] is not None:
                                    per_replicate[method][metric].append(result[metric])

                    names_total = universe_size * replicates
                    row: dict[str, Any] = {
                        "universe_n": universe_size,
                        "stress_k": k,
                        "tick": tick,
                        "half_spread": half_spread,
                        "replicates": replicates,
                        "names": names_total,
                        "quote_miss_share": misses / names_total,
                    }
                    for method, label in ((METHOD_E0, "E0"), (METHOD_E2, "E2")):
                        counts = pooled[method]
                        low, high = wilson_interval(counts["wrong"], counts["decided_ordered"])
                        row.update(
                            {
                                f"{label}_decided_ordered": counts["decided_ordered"],
                                f"{label}_wrong": counts["wrong"],
                                f"{label}_wrong_share": wc._ratio(
                                    counts["wrong"], counts["decided_ordered"]
                                ),
                                f"{label}_wrong_ci_low": low,
                                f"{label}_wrong_ci_high": high,
                                f"{label}_undecided_ordered_share": wc._ratio(
                                    counts["undecided_ordered"], counts["ordered"]
                                ),
                            }
                        )
                    summary.append(row)

                    cell = {"universe_n": universe_size, "tick": tick, "half_spread": half_spread}
                    for method in (METHOD_E0, METHOD_E2):
                        for metric in CLAIM_METRICS:
                            mean, mcse = wc._mean_and_mcse(per_replicate[method][metric])
                            claim_inputs[k].append(
                                {**cell, "method": method, "metric": metric, "mean": mean, "mcse": mcse}
                            )

    claims: list[dict[str, Any]] = []
    for k in ks:
        claims.extend({"stress_k": k, **claim} for claim in wc.claim_rows(claim_inputs[k]))
    return summary, claims


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=wc.REPLICATES)
    args = parser.parse_args()
    if args.replicates < 2:
        parser.error("--replicates must be at least 2")
    args.output.mkdir(parents=True, exist_ok=True)
    summary, claims = run_stress(replicates=args.replicates)
    wc._write_csv(args.output / "workflow_stress_per_name.csv", summary)
    wc._write_csv(args.output / "workflow_stress_per_name_claims.csv", claims)
    credited = sum(1 for claim in claims if claim["benefit_credited"])
    print(
        f"wrote {len(summary)} summary rows, {len(claims)} claim rows; benefits credited: {credited}"
    )


if __name__ == "__main__":
    main()
