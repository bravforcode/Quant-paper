"""Replication sweep: the study's headline quantities across many draws.

A single generator draw is one number, and one number cannot support a claim
about a protocol. This module repeats the whole study across

* **many seeds** of the same generator, which tests whether the reported
  quantities are a property of the protocol or of one lucky draw;
* **many generator specifications**, which vary volatility, quote width, tick
  size, the sampled strike range and the sampled maturities one factor at a
  time, and so test whether the reported quantities depend on the
  particular synthetic market that was written;
* **many protocol settings**, which vary the analyst's own knobs — the
  tolerance and the resolution scale — and so map the coverage–error frontier
  an analyst would actually face.

Every draw reports the same quantities, so the sweep is read as a
distribution rather than as a point estimate. The sweep contains no market
data and supports no market claim.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

from research.cpiv.measurement.analysis import error_profile
from research.cpiv.measurement.dgp import GeneratorConfig, generate_market
from research.cpiv.measurement.frontier import selection_frontier
from research.cpiv.measurement.manifest import build_manifest, write_manifest
from research.cpiv.measurement.study import (
    StudyRow,
    StudySettings,
    mean_abs_error,
    method_values,
    own_set_error_reduction,
    run_protocol,
    truth_values,
)

HERE = Path(__file__).resolve().parent
RUN_CONFIG = HERE / "configs" / "study.yaml"
DEFAULT_OUTPUT = HERE / "outputs" / "sweep"

BASE_SEED = 20261022
SEED_STRIDE = 7919
DECLARED_SEEDS: tuple[int, ...] = tuple(
    BASE_SEED + SEED_STRIDE * index for index in range(24)
)
FRONTIER_TRIALS = 2000


@dataclass(frozen=True)
class Specification:
    """One declared generator specification and the protocol applied to it."""

    name: str
    description: str
    config: GeneratorConfig
    settings: StudySettings


def _base_specifications() -> tuple[Specification, ...]:
    """One factor at a time away from the declared base market."""
    base_config = GeneratorConfig()
    base_settings = StudySettings()
    variants: list[Specification] = [
        Specification(
            "base",
            "The declared base market and protocol.",
            base_config,
            base_settings,
        ),
        Specification(
            "low_vol",
            "Base volatility lowered from 22% to 15%.",
            replace(base_config, base_vol=0.15),
            base_settings,
        ),
        Specification(
            "high_vol",
            "Base volatility raised from 22% to 35%.",
            replace(base_config, base_vol=0.35),
            base_settings,
        ),
        Specification(
            "wide_quotes",
            "Every quote twice as wide, in ticks.",
            replace(base_config, half_spread_ticks=2, wing_spread_ticks=2),
            base_settings,
        ),
        Specification(
            "very_wide_quotes",
            "Every quote three times as wide, in ticks.",
            replace(base_config, half_spread_ticks=3, wing_spread_ticks=3),
            base_settings,
        ),
        Specification(
            "coarse_tick",
            "Quote tick raised from 0.01 to 0.05.",
            replace(base_config, tick=0.05),
            replace(base_settings, tick=0.05),
        ),
        Specification(
            "no_wide_sessions",
            "The periodic wide-liquidity session removed.",
            replace(base_config, wide_day_period=0),
            base_settings,
        ),
        Specification(
            "wide_strike_grid",
            "Strike grid widened to 85%–115% of spot.",
            replace(
                base_config,
                strike_fractions=(0.85, 0.925, 1.00, 1.075, 1.15),
            ),
            base_settings,
        ),
        Specification(
            "short_dated",
            "Sampled maturities shortened to 7, 14 and 30 days.",
            replace(base_config, expiries=(7, 14, 30)),
            base_settings,
        ),
        Specification(
            "long_dated",
            "Sampled maturities lengthened to 30, 60 and 90 days.",
            replace(base_config, expiries=(30, 60, 90)),
            base_settings,
        ),
    ]
    return tuple(variants)


def _protocol_variants() -> tuple[Specification, ...]:
    """The analyst's own knobs, applied to one fixed market."""
    base_config = GeneratorConfig()
    base_settings = StudySettings()
    variants: list[Specification] = []
    for tolerance in (0.05, 0.10, 0.25, 0.50):
        variants.append(
            Specification(
                f"tolerance_{tolerance:.2f}pp",
                f"Certification tolerance set to {tolerance:.2f} percentage points.",
                base_config,
                replace(base_settings, primary_tolerance_pp=tolerance),
            )
        )
    for resolution in (0.5, 1.0, 2.0):
        variants.append(
            Specification(
                f"resolution_{resolution:g}ticks",
                f"Resolution scale set to {resolution:g} tick(s).",
                base_config,
                replace(base_settings, resolution_ticks=resolution),
            )
        )
    return tuple(variants)


SPECIFICATIONS = _base_specifications() + _protocol_variants()


def _block_index(rows: Sequence[StudyRow]) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    for row in rows:
        blocks.setdefault(row.block, []).append(row.pair_id)
    return blocks


def _coverage_by_tolerance(
    rows: Sequence[StudyRow], tolerance: float
) -> float:
    identified = [row for row in rows if row.displacement_pp is not None]
    resolved = sum(
        1
        for row in identified
        if row.displacement_pp is not None and row.displacement_pp <= tolerance
    )
    return resolved / len(rows) if rows else 0.0


def _common_set_error_reduction(rows: Sequence[StudyRow]) -> float | None:
    """Raw-midpoint error minus certified error on the pairs both can use.

    On the common set the two methods are numerically identical, because the
    certified value *is* the midpoint value of the same pair. The result is
    therefore zero by construction, and it is reported only so that the
    structural identity is visible rather than assumed.
    """
    raw = method_values(rows, "raw_midpoint")
    certified = method_values(rows, "protocol_certified")
    truth = truth_values(rows)
    common = sorted(set(raw) & set(certified) & set(truth))
    if not common:
        return None
    base = sum(abs(raw[key] - truth[key]) for key in common) / len(common)
    method = sum(abs(certified[key] - truth[key]) for key in common) / len(common)
    return base - method


def _draw_record(
    label: str,
    rows: Sequence[StudyRow],
    settings: StudySettings,
    seed: int,
) -> dict[str, object]:
    """Every quantity the sweep reports, for one draw."""
    attempted = len(rows)
    certified = method_values(rows, "protocol_certified")
    identified = method_values(rows, "protocol_identified")
    raw = method_values(rows, "raw_midpoint")
    truth = truth_values(rows)
    profile = error_profile(raw, truth)
    abstained = [row for row in rows if row.protocol_certified_cpiv_pp is None]
    displacement = {
        row.pair_id: row.displacement_pp
        for row in rows
        if row.displacement_pp is not None
    }
    frontier = selection_frontier(
        displacement=displacement,
        values=raw,
        truth=truth,
        blocks=_block_index(rows),
        tolerances=(settings.primary_tolerance_pp,),
        trials=FRONTIER_TRIALS,
        seed=settings.bootstrap_seed,
    )
    point = frontier[0] if frontier else None
    primary = [row for row in rows if row.day_index < settings.primary_day_cut]
    holdout = [row for row in rows if row.day_index >= settings.primary_day_cut]
    return {
        "draw": label,
        "seed": seed,
        "attempted": attempted,
        "n_scored": len(raw),
        "n_certified": len(certified),
        "coverage_certified": len(certified) / attempted if attempted else 0.0,
        "coverage_identified": len(identified) / attempted if attempted else 0.0,
        "mae_raw_pp": mean_abs_error(raw, truth),
        "mae_certified_pp": mean_abs_error(certified, truth),
        "mae_abstained_pp": mean_abs_error(
            method_values(abstained, "raw_midpoint"), truth_values(abstained)
        ),
        "raw_median_abs_error_pp": profile["median_abs_error_pp"],
        "raw_p90_abs_error_pp": profile["p90_abs_error_pp"],
        "raw_p95_abs_error_pp": profile["p95_abs_error_pp"],
        "raw_max_abs_error_pp": profile["max_abs_error_pp"],
        "raw_share_within_0.10_pp": profile["share_within_0.10_pp"],
        "coverage_at_0.05_pp": _coverage_by_tolerance(rows, 0.05),
        "coverage_at_0.10_pp": _coverage_by_tolerance(rows, 0.10),
        "coverage_at_0.25_pp": _coverage_by_tolerance(rows, 0.25),
        "frontier_null_mean_pp": point.null_mean_pp if point else None,
        "frontier_block_null_mean_pp": point.block_null_mean_pp if point else None,
        "frontier_p_pair_null": point.p_value_pair_null if point else None,
        "frontier_p_block_null": point.p_value_block_null if point else None,
        "coverage_primary_period": (
            len(method_values(primary, "protocol_certified")) / len(primary)
            if primary
            else 0.0
        ),
        "coverage_holdout_period": (
            len(method_values(holdout, "protocol_certified")) / len(holdout)
            if holdout
            else 0.0
        ),
        "error_reduction_primary_pp": own_set_error_reduction(primary),
        "error_reduction_holdout_pp": own_set_error_reduction(holdout),
        "common_set_error_reduction_primary_pp": _common_set_error_reduction(primary),
        "common_set_error_reduction_holdout_pp": _common_set_error_reduction(holdout),
    }


def _aggregate(records: Sequence[dict[str, object]]) -> dict[str, object]:
    """The distribution of every reported quantity across draws."""
    summary: dict[str, object] = {}
    numeric = [
        key
        for key, value in records[0].items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ] if records else []
    for key in numeric:
        values = [
            float(record[key])
            for record in records
            if isinstance(record.get(key), (int, float))
            and not isinstance(record.get(key), bool)
        ]
        if not values:
            continue
        summary[key] = {
            "n": len(values),
            "mean": statistics.fmean(values),
            "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "median": statistics.median(values),
            "max": max(values),
        }
    return summary


def run_seed_sweep(
    seeds: Sequence[int] = DECLARED_SEEDS,
    settings: StudySettings | None = None,
) -> list[dict[str, object]]:
    """Repeat the study across seeds and return one record per draw."""
    records: list[dict[str, object]] = []
    for seed in seeds:
        config = GeneratorConfig(seed=seed)
        pairs, _counts = generate_market(config)
        rows = run_protocol(pairs, settings or StudySettings())
        records.append(_draw_record(f"seed_{seed}", rows, settings or StudySettings(), seed))
    return records


def run_specification_sweep() -> list[dict[str, object]]:
    """Run every declared specification and return one record per case."""
    records: list[dict[str, object]] = []
    for specification in SPECIFICATIONS:
        pairs, _counts = generate_market(specification.config)
        rows = run_protocol(pairs, specification.settings)
        record = _draw_record(
            specification.name, rows, specification.settings, specification.config.seed
        )
        record["description"] = specification.description
        records.append(record)
    return records


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sweep_report(
    seed_records: Sequence[dict[str, object]],
    specification_records: Sequence[dict[str, object]],
) -> dict[str, object]:
    """Assemble the sweep's report: distributions, not point estimates."""
    seeds = list(seed_records)
    verdicts = {
        "draws": len(seeds),
        "draws_with_certified_mae_below_random_null": sum(
            1
            for record in seeds
            if isinstance(record["mae_certified_pp"], float)
            and isinstance(record["frontier_null_mean_pp"], float)
            and float(record["mae_certified_pp"]) < float(record["frontier_null_mean_pp"])
        ),
        "draws_with_certified_mae_below_block_null": sum(
            1
            for record in seeds
            if isinstance(record["mae_certified_pp"], float)
            and isinstance(record["frontier_block_null_mean_pp"], float)
            and float(record["mae_certified_pp"])
            < float(record["frontier_block_null_mean_pp"])
        ),
        "draws_with_block_null_p_below_0.05": sum(
            1
            for record in seeds
            if isinstance(record["frontier_p_block_null"], float)
            and float(record["frontier_p_block_null"]) < 0.05
        ),
        "draws_with_certified_coverage_above_zero": sum(
            1
            for record in seeds
            if float(record["coverage_certified"]) > 0.0
        ),
    }
    return {
        "status": "synthetic_replication_sweep_only",
        "market_data_used": False,
        "network_access_used": False,
        "declared_seeds": list(DECLARED_SEEDS),
        "seed_stride": SEED_STRIDE,
        "frontier_trials": FRONTIER_TRIALS,
        "seed_sweep": {
            "summary": _aggregate(seeds),
            "draws": seeds,
            "verdict": verdicts,
        },
        "specification_sweep": {
            "summary": _aggregate(list(specification_records)),
            "cases": list(specification_records),
        },
        "warning": (
            "Synthetic replication of a synthetic market. It bounds how much "
            "the reported quantities depend on one generator draw or one "
            "generator specification. It is not a market estimate and not "
            "evidence of trading profitability."
        ),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--draws", type=int, default=len(DECLARED_SEEDS))
    parser.add_argument(
        "--skip-specifications",
        action="store_true",
        help="run the seed sweep only",
    )
    args = parser.parse_args(argv)
    seeds = DECLARED_SEEDS[: max(1, args.draws)]
    seed_records = run_seed_sweep(seeds)
    specification_records = [] if args.skip_specifications else run_specification_sweep()
    report = sweep_report(seed_records, specification_records)
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "sweep_summary.json"
    summary_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_csv(output_dir / "seed_draws.csv", cast(list[dict[str, Any]], seed_records))
    _write_csv(
        output_dir / "specifications.csv",
        cast(list[dict[str, Any]], specification_records),
    )
    manifest = build_manifest(
        config_path=RUN_CONFIG,
        raw_paths=(RUN_CONFIG,),
        environment_path=HERE.parents[2] / "uv.lock",
        seed=BASE_SEED,
        outputs=(summary_path, output_dir / "seed_draws.csv"),
        licence_mode="synthetic-no-market-data",
        status_counts={"draws": len(seed_records)},
        repo_root=HERE.parents[2],
    )
    write_manifest(output_dir / "manifest.json", manifest)
    print(json.dumps(report["seed_sweep"]["summary"], indent=2, sort_keys=True))
    print(json.dumps(report["seed_sweep"]["verdict"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
