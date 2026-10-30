"""Exploratory: R3 and R6 repeated across every replication seed.

Not part of the declared tally. The declared rules R3 and R6 were run on the
development seed alone (``verdict.py``). This module repeats the same two
computations on each of the 23 replication seeds, so the reader can see
whether the development-seed outcome is typical. It changes no threshold,
rule, seed or tally, and it writes to its own directory.

Run with ``python -m research.cpiv.measurement.exploratory_seeds``.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from dataclasses import replace
from pathlib import Path
from typing import Any

from research.cpiv.measurement import verdict
from research.cpiv.measurement.dgp import GeneratorConfig, generate_market
from research.cpiv.measurement.study import (
    StudySettings,
    _perturbation_report,
    method_values,
    run_protocol,
)
from research.cpiv.measurement.sweep import SPECIFICATIONS

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "outputs" / "exploratory_seeds"


def _market_coverages(seed: int) -> dict[str, float]:
    """Certified coverage of each market specification on one seed."""
    coverages: dict[str, float] = {}
    for specification in SPECIFICATIONS:
        if specification.name not in verdict.MARKET_SPECIFICATIONS:
            continue
        config = replace(specification.config, seed=seed)
        pairs, _counts = generate_market(config)
        rows = run_protocol(pairs, specification.settings)
        certified = method_values(rows, "protocol_certified")
        coverages[specification.name] = len(certified) / len(rows) if rows else 0.0
    return coverages


def _r3(coverages: dict[str, float]) -> dict[str, Any]:
    values = sorted(coverages.values())
    median = values[len(values) // 2]
    minimum = values[0]
    ratio = minimum / median if median > 0 else 0.0
    return {
        "median_coverage": median,
        "minimum_coverage": minimum,
        "minimum_over_median": ratio,
        "passed": ratio >= verdict.R3_MIN_RATIO,
    }


def _r6(seed: int) -> dict[str, Any]:
    settings = StudySettings()
    pairs, _counts = generate_market(GeneratorConfig(seed=seed))
    rows = run_protocol(pairs, settings)
    report = _perturbation_report(pairs, settings, rows)
    shifts = {str(item["name"]): float(item["coverage_protocol_change"]) for item in report}
    worst = max(abs(value) for value in shifts.values())
    return {
        "coverage_change_by_perturbation": shifts,
        "worst_absolute_coverage_change": worst,
        "worst_perturbation": max(shifts, key=lambda name: abs(shifts[name])),
        "passed": worst <= verdict.R6_MAX_COVERAGE_SHIFT,
    }


def run(seeds: tuple[int, ...]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for seed in seeds:
        coverages = _market_coverages(seed)
        role = "development" if seed == verdict.DEVELOPMENT_SEED else "replication"
        record: dict[str, Any] = {"seed": seed, "role": role}
        record.update({f"R3_{key}": value for key, value in _r3(coverages).items()})
        record["R3_coverage_by_specification"] = coverages
        record.update({f"R6_{key}": value for key, value in _r6(seed).items()})
        records.append(record)
        print(
            f"seed {seed}: R3 {'pass' if record['R3_passed'] else 'fail'} "
            f"(ratio {record['R3_minimum_over_median']:.3f}); "
            f"R6 {'pass' if record['R6_passed'] else 'fail'} "
            f"(worst {record['R6_worst_absolute_coverage_change']:.4f})",
            flush=True,
        )
    return records


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    replication = [record for record in records if record["role"] == "replication"]
    ratios = [float(record["R3_minimum_over_median"]) for record in replication]
    worst = [float(record["R6_worst_absolute_coverage_change"]) for record in replication]
    return {
        "replication_seeds": len(replication),
        "R3_pass_count": sum(bool(record["R3_passed"]) for record in replication),
        "R3_minimum_over_median_median": statistics.median(ratios),
        "R3_minimum_over_median_min": min(ratios),
        "R3_minimum_over_median_max": max(ratios),
        "R6_pass_count": sum(bool(record["R6_passed"]) for record in replication),
        "R6_worst_change_median": statistics.median(worst),
        "R6_worst_change_max": max(worst),
        "development_seed_reproduces_declared": {
            "R3_minimum_over_median": next(
                record["R3_minimum_over_median"]
                for record in records
                if record["role"] == "development"
            ),
            "R6_worst_absolute_coverage_change": next(
                record["R6_worst_absolute_coverage_change"]
                for record in records
                if record["role"] == "development"
            ),
        },
        "declared_tally_changed": False,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    seeds = (verdict.DEVELOPMENT_SEED,) + verdict.REPLICATION_SEEDS
    records = run(seeds)
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = _summary(records)
    (output_dir / "exploratory_summary.json").write_text(
        json.dumps({"summary": summary, "draws": records}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    flat = [
        {
            key: (json.dumps(value, sort_keys=True) if isinstance(value, dict) else value)
            for key, value in record.items()
        }
        for record in records
    ]
    draws_path = output_dir / "exploratory_seed_draws.csv"
    with draws_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
