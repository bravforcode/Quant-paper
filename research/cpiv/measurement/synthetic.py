"""Synthetic reproduction target for the measurement core.

No market data is read. The three cases are the published examples the paper
keeps in its main text: the exact identity, one tick-convention pair, and one
deep-OTM pair that fails resolution.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import yaml
from research.cpiv import build_demo as bsm
from research.cpiv.measurement.inversion import round_trip_summary
from research.cpiv.measurement.manifest import build_manifest, write_manifest
from research.cpiv.measurement.resolution import (
    ResolutionInput,
    ResolutionOutcome,
    resolve,
)
from research.cpiv.measurement.status import funnel, reconcile

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures" / "synthetic_cases.json"
RUN_CONFIG = HERE / "configs" / "synthetic.yaml"
DEFAULT_OUTPUT = HERE / "outputs"
SIMPSON_INTERVALS = 2000


def load_cases() -> dict[str, dict[str, float]]:
    loaded = json.loads(FIXTURES.read_text(encoding="utf-8"))
    return cast(dict[str, dict[str, float]], loaded)


def _simpson(
    function: Callable[[float], float], low: float, high: float, intervals: int
) -> float:
    if intervals % 2:
        intervals += 1
    width = (high - low) / intervals
    total = function(low) + function(high)
    total += 4.0 * sum(function(low + i * width) for i in range(1, intervals, 2))
    total += 2.0 * sum(function(low + i * width) for i in range(2, intervals, 2))
    return total * width / 3.0


def _vega_decimal(
    spot: float, strike: float, days: int, rate: float, q: float, sigma: float
) -> float:
    return 100.0 * bsm.bs_vega_per_vol_point(spot, strike, days, rate, q, sigma)


def identity_check(case: dict[str, float]) -> dict[str, float]:
    """Exact integral identity plus the local-approximation error."""
    spot = case["spot"]
    strike = case["strike"]
    days = int(case["days"])
    rate = case["rate"]
    q = case["dividend_yield"]
    sigma_call = case["sigma_call"]
    sigma_put = case["sigma_put"]
    call = bsm.bs_price("call", spot, strike, days, rate, q, sigma_call)
    put = bsm.bs_price("put", spot, strike, days, rate, q, sigma_put)
    residual = bsm.parity_residual(call, put, spot, strike, days, rate, q)
    integral = _simpson(
        lambda sigma: _vega_decimal(spot, strike, days, rate, q, sigma),
        sigma_put,
        sigma_call,
        SIMPSON_INTERVALS,
    )
    average_vega = integral / (sigma_call - sigma_put)
    exact_cpiv = 100.0 * (sigma_call - sigma_put)
    local_cpiv = 100.0 * residual / average_vega
    return {
        "parity_residual_usd": residual,
        "integrated_vega_usd": integral,
        "identity_error_usd": abs(residual - integral),
        "average_vega_usd_per_decimal_iv": average_vega,
        "exact_cpiv_pp": exact_cpiv,
        "local_cpiv_pp": local_cpiv,
        "local_error_pp": local_cpiv - exact_cpiv,
    }


def _resolution_input(
    case: dict[str, float], pair_id: str, tick: float
) -> ResolutionInput:
    spot = case["spot"]
    strike = case["strike"]
    days = int(case["days"])
    rate = case["rate"]
    q = case["dividend_yield"]
    call_mid = bsm.bs_price("call", spot, strike, days, rate, q, case["sigma_call"])
    put_mid = bsm.bs_price("put", spot, strike, days, rate, q, case["sigma_put"])
    call_spread = case["call_half_spread"]
    put_spread = case["put_half_spread"]
    return ResolutionInput(
        pair_id=pair_id,
        call_mid=call_mid,
        put_mid=put_mid,
        call_bid=call_mid - call_spread,
        call_ask=call_mid + call_spread,
        put_bid=put_mid - put_spread,
        put_ask=put_mid + put_spread,
        spot=spot,
        strike=strike,
        days=days,
        rate=rate,
        dividend_yield=q,
        tick=tick,
        resolution_ticks=1.0,
        tolerance_pp=0.10,
    )


def run_case(case: dict[str, float], pair_id: str, tick: float) -> ResolutionOutcome:
    return resolve(_resolution_input(case, pair_id, tick))


def run_synthetic() -> dict[str, object]:
    """Run the three fixtures and the solver grid; no market data involved."""
    cases = load_cases()
    tick = cases["tick_convention"]["tick"]
    tick_full = run_case(cases["tick_convention"], "tick-full", tick)
    tick_half = run_case(cases["tick_convention"], "tick-half", tick / 2.0)
    deep = run_case(cases["deep_otm"], "deep-otm", cases["deep_otm"]["tick"])
    outcomes = [tick_full, tick_half, deep]
    records = [outcome.to_record() for outcome in outcomes]
    reconciliation = reconcile(records)
    return {
        "identity": identity_check(cases["identity"]),
        "tick_convention": {
            "full_tick": asdict(tick_full),
            "half_tick": asdict(tick_half),
        },
        "deep_otm": asdict(deep),
        "solver_grid": round_trip_summary(),
        "reconciliation": reconciliation,
        "funnel": [asdict(row) for row in funnel(records)],
    }


def _write_funnel(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_funnel_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "| Stage | Count | Share of attempted | Share of prior | Dominant reason |",
        "|:--|--:|--:|--:|:--|",
    ]
    for row in rows:
        reason = row["dominant_rejection_reason"] or "—"
        lines.append(
            f"| {row['stage']} | {row['count']} | "
            f"{float(row['share_of_attempted']):.3f} | "
            f"{float(row['share_of_prior']):.3f} | {reason} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    summary = run_synthetic()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "synthetic_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    funnel_path = output_dir / "funnel.csv"
    _write_funnel(funnel_path, summary["funnel"])  # type: ignore[arg-type]
    funnel_markdown = output_dir / "funnel.md"
    _write_funnel_markdown(funnel_markdown, summary["funnel"])  # type: ignore[arg-type]
    reconciliation = summary["reconciliation"]
    manifest = build_manifest(
        config_path=RUN_CONFIG,
        environment_path=HERE.parents[2] / "uv.lock",
        seed=yaml.safe_load(RUN_CONFIG.read_text(encoding="utf-8")).get("seed"),
        outputs=(summary_path, funnel_path, funnel_markdown),
        licence_mode="synthetic-no-market-data",
        status_counts=reconciliation["terminal_counts"],  # type: ignore[index]
        repo_root=HERE.parents[2],
    )
    write_manifest(output_dir / "manifest.json", manifest)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
