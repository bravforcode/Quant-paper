"""Exploratory ablation of the time-value and finite-shock refusals.

This is not a pre-registered test. It reruns the declared protocol on the same
synthetic pairs and settings as the primary study, with the time-value and
finite-shock refusals removed one at a time and then together, so the cost of
each refusal can be read against the truth the benchmark holds.

``interval_only`` is an analogue of the interval-only rule in the r31
ablation, not the same rule: it keeps the endpoint-width tolerance test.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from research.cpiv.measurement.analysis import error_profile
from research.cpiv.measurement.dgp import GeneratorConfig, generate_market
from research.cpiv.measurement.manifest import build_manifest, write_manifest
from research.cpiv.measurement.quotes import QuotePair
from research.cpiv.measurement.status import Stage, TerminalStatus
from research.cpiv.measurement.study import (
    RUN_CONFIG,
    StudyRow,
    StudySettings,
    _write_csv,
    run_protocol,
)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
DEFAULT_OUTPUT = HERE / "outputs" / "ablation"

#: The declared variants. The full protocol skips nothing and is the reference
#: against which each variant's added pairs are counted.
VARIANTS: dict[str, frozenset[Stage]] = {
    "full_protocol": frozenset(),
    "without_time_value": frozenset({Stage.TIME_VALUE}),
    "without_finite_shock": frozenset({Stage.FINITE_SHOCK}),
    "interval_only": frozenset({Stage.TIME_VALUE, Stage.FINITE_SHOCK}),
}


def run_ablation(
    pairs: Sequence[QuotePair], settings: StudySettings
) -> dict[str, list[StudyRow]]:
    """Run the protocol once per variant on the same pairs."""
    return {name: run_protocol(pairs, settings, skip) for name, skip in VARIANTS.items()}


def _certified(rows: Sequence[StudyRow]) -> dict[str, float]:
    return {
        row.pair_id: row.protocol_certified_cpiv_pp
        for row in rows
        if row.protocol_certified_cpiv_pp is not None
    }


def _truth(rows: Sequence[StudyRow]) -> dict[str, float]:
    return {row.pair_id: row.true_cpiv_pp for row in rows if row.true_cpiv_pp is not None}


def summarise(results: Mapping[str, Sequence[StudyRow]]) -> dict[str, Any]:
    """Counts per variant, and the error against the truth of the pairs each adds."""
    full_rows = results["full_protocol"]
    full = set(_certified(full_rows))
    truth = _truth(full_rows)
    attempted = len(full_rows)
    variants: dict[str, Any] = {}
    for name, rows in results.items():
        certified = _certified(rows)
        added = sorted(set(certified) - full)
        variants[name] = {
            "skipped_stages": sorted(stage.name for stage in VARIANTS[name]),
            "attempted": attempted,
            "certified": len(certified),
            "certified_share": len(certified) / attempted,
            "added_over_full": len(added),
            "error_certified_pp": error_profile(certified, truth),
            "error_added_pp": error_profile(
                {key: certified[key] for key in added}, truth
            ),
            "terminal_counts": dict(Counter(row.terminal.value for row in rows)),
        }
    return {
        "licence_mode": "synthetic-no-market-data",
        "exploratory": True,
        "pre_registered": False,
        "tolerance_pp": StudySettings().primary_tolerance_pp,
        "refused_at_full_protocol": dict(
            Counter(row.failed_stage.value for row in full_rows if row.failed_stage)
        ),
        "variants": variants,
    }


def write_outputs(
    results: Mapping[str, Sequence[StudyRow]], output_dir: Path
) -> dict[str, Any]:
    """Write the summary, one row per pair per variant, and the run manifest."""
    summary = summarise(results)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "ablation_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    records = [
        {
            "variant": name,
            "pair_id": row.pair_id,
            "terminal": row.terminal.value,
            "failed_stage": row.failed_stage.value if row.failed_stage else "",
            "certified": row.terminal is TerminalStatus.RESOLVED_WITHIN_TOLERANCE,
            "protocol_certified_cpiv_pp": row.protocol_certified_cpiv_pp,
            "true_cpiv_pp": row.true_cpiv_pp,
        }
        for name, rows in results.items()
        for row in rows
    ]
    csv_path = output_dir / "ablation.csv"
    _write_csv(csv_path, records)
    manifest = build_manifest(
        config_path=RUN_CONFIG,
        raw_paths=(RUN_CONFIG,),
        environment_path=REPO_ROOT / "uv.lock",
        seed=GeneratorConfig().seed,
        outputs=(summary_path, csv_path),
        licence_mode="synthetic-no-market-data",
        status_counts=dict(
            Counter(row.terminal.value for row in results["full_protocol"])
        ),
        repo_root=REPO_ROOT,
    )
    write_manifest(output_dir / "manifest.json", manifest)
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    pairs, _counts = generate_market(GeneratorConfig())
    summary = write_outputs(run_ablation(pairs, StudySettings()), args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
