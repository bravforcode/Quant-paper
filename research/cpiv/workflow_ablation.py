"""Interval-only ablation and sensitivity sweep for the Section 7.9 workflow comparison.

E3 keeps only the bid/ask implied-CPIV interval that E2 uses. It drops the OTM-value, shock-
inversion and tau_IV screens and decides a pair only when the two intervals are disjoint. E0 and
E2 are scored exactly as in workflow_comparison.py, on the same draws, quotes and tie margins.

Two stress designs are run, each with the same cross-sections as Section 7.9:
  call_offset  one shift of the call midpoint equal to a multiple of the half-spread
  per_name     each call midpoint shifted by its own draw from U(-k*h, k*h), as in
               workflow_stress_per_name.py, which Section 7.9 relies on

The sweep varies the true-CPIV range and tau_IV. Module constants are restored after each
setting. The output is author-run diagnostic evidence; the Section 7.9 claim rule is unchanged.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from research.cpiv import workflow_comparison as wc
from research.cpiv import workflow_stress_per_name as wsp

SWEEP_SETTINGS: tuple[tuple[float, float], ...] = (
    (5.0, 0.10),  # Section 7.9 values
    (1.0, 0.10),
    (2.5, 0.10),
    (10.0, 0.10),
    (5.0, 0.05),
    (5.0, 0.20),
)
DEFAULT_SETTING = SWEEP_SETTINGS[0]
METRICS = ("wrong_among_decided", "decided_fraction", "false_exclusion")
METHODS = ("E0", "E2", "E3")
DESIGN_STRESS = {
    "call_offset": wc.CALL_OFFSET_MULTIPLES,
    "per_name": wsp.STRESS_K,
}


def e3_fields(name: dict[str, Any], tick: float, half_spread: float, offset: float) -> dict[str, Any]:
    """Bid/ask implied-CPIV interval of one name, with no screen applied."""
    call_quote = wc.observed_quote(name["call_price"], tick, half_spread, offset)
    put_quote = wc.observed_quote(name["put_price"], tick, half_spread)
    call_ivs = wc._quote_ivs("call", call_quote, name["strike"], name["days"])
    put_ivs = wc._quote_ivs("put", put_quote, name["strike"], name["days"])
    if call_ivs is None or put_ivs is None:
        return {"e3_ok": False, "e3_lo": 0.0, "e3_hi": 0.0}
    spreads = [100.0 * (call_iv - put_iv) for call_iv in call_ivs for put_iv in put_ivs]
    return {"e3_ok": True, "e3_lo": min(spreads), "e3_hi": max(spreads)}


def decide_e3(first: dict[str, Any], second: dict[str, Any]) -> int:
    """Order a pair only when both intervals exist and do not overlap."""
    if not (first["e3_ok"] and second["e3_ok"]):
        return 0
    if first["e3_lo"] > second["e3_hi"]:
        return 1
    if first["e3_hi"] < second["e3_lo"]:
        return -1
    return 0


DECIDERS = {"E0": wc.decide_e0, "E2": wc.decide_e2, "E3": decide_e3}


def _offsets(design: str, universe_size: int, replicate: int, stress: float, half_spread: float) -> list[float]:
    if design == "call_offset":
        return [stress * half_spread] * universe_size
    if design == "per_name":
        return wsp.draw_offsets(universe_size, replicate, stress, half_spread)
    raise ValueError(f"unknown design: {design}")


def run_design(
    design: str,
    *,
    replicates: int,
    stresses: Sequence[float] | None = None,
    universe_sizes: Sequence[int] = wc.UNIVERSE_SIZES,
    ticks: Sequence[float] = wc.TICKS,
    half_spreads: Sequence[float] = wc.HALF_SPREADS,
) -> list[dict[str, Any]]:
    """Replicate-level mean and MCSE of each metric for every method and cell of one design."""
    stress_levels = DESIGN_STRESS[design] if stresses is None else stresses
    rows: list[dict[str, Any]] = []
    for universe_size in universe_sizes:
        draws = [
            wc.draw_cross_section(wc._replicate_rng(universe_size, replicate), universe_size)
            for replicate in range(replicates)
        ]
        for stress in stress_levels:
            for tick in ticks:
                for half_spread in half_spreads:
                    samples: dict[tuple[str, str], list[float]] = {
                        (method, metric): [] for method in METHODS for metric in METRICS
                    }
                    for replicate, draw in enumerate(draws):
                        offsets = _offsets(design, universe_size, replicate, stress, half_spread)
                        names = []
                        for name, offset in zip(draw, offsets, strict=True):
                            record = wc.analyse_name(
                                name, tick=tick, half_spread=half_spread, call_offset=offset
                            )
                            record.update(e3_fields(name, tick, half_spread, offset))
                            names.append(record)
                        for method, decide in DECIDERS.items():
                            scored = wc.score_pairs(names, decide)
                            for metric in METRICS:
                                if scored[metric] is not None:
                                    samples[(method, metric)].append(scored[metric])
                    for (method, metric), values in samples.items():
                        mean, mcse = wc._mean_and_mcse(values)
                        rows.append(
                            {
                                "design": design,
                                "universe_n": universe_size,
                                "tick": tick,
                                "half_spread": half_spread,
                                "stress": stress,
                                "method": method,
                                "metric": metric,
                                "mean": mean,
                                "mcse": mcse,
                                "replicates": len(values),
                            }
                        )
    return rows


def run_all(replicates: int, settings: Sequence[tuple[float, float]] = SWEEP_SETTINGS) -> list[dict[str, Any]]:
    """Run both designs under every (true-CPIV range, tau_IV) setting."""
    original = (wc.TAU_PP_RANGE, wc.TAU_IV_PP)
    rows: list[dict[str, Any]] = []
    try:
        for tau_range, tau_iv in settings:
            wc.TAU_PP_RANGE = tau_range
            wc.TAU_IV_PP = tau_iv
            for design in DESIGN_STRESS:
                for row in run_design(design, replicates=replicates):
                    rows.append({"tau_range_pp": tau_range, "tau_iv_pp": tau_iv, **row})
    finally:
        wc.TAU_PP_RANGE, wc.TAU_IV_PP = original
    return rows


def sweep_summary(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Unweighted mean of the cell means for each setting, design and stress level.

    Cells without a defined share (no decided pairs) are skipped; the cell count is reported.
    """
    grouped: dict[tuple[Any, ...], dict[str, list[float]]] = {}
    for row in rows:
        if row["mean"] is None:
            continue
        key = (row["tau_range_pp"], row["tau_iv_pp"], row["design"], row["stress"])
        bucket = grouped.setdefault(key, {})
        bucket.setdefault(f"{row['method']}_{row['metric']}", []).append(row["mean"])
    summary: list[dict[str, Any]] = []
    for (tau_range, tau_iv, design, stress), bucket in grouped.items():
        out: dict[str, Any] = {
            "tau_range_pp": tau_range,
            "tau_iv_pp": tau_iv,
            "design": design,
            "stress": stress,
        }
        for field, values in sorted(bucket.items()):
            out[field] = sum(values) / len(values)
            out[f"{field}_cells"] = len(values)
        summary.append(out)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=wc.REPLICATES)
    args = parser.parse_args()
    if args.replicates < 2:
        parser.error("--replicates must be at least 2")
    args.output.mkdir(parents=True, exist_ok=True)
    rows = run_all(args.replicates)
    wc._write_csv(args.output / "workflow_ablation.csv", rows)
    wc._write_csv(args.output / "workflow_ablation_sweep_summary.csv", sweep_summary(rows))
    default = [r for r in rows if (r["tau_range_pp"], r["tau_iv_pp"]) == DEFAULT_SETTING]
    print(f"wrote {len(rows)} rows ({len(default)} at the Section 7.9 setting)")


if __name__ == "__main__":
    main()
