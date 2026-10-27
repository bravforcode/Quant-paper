"""Apply the pre-registered decision rules to the replication sweep.

The rules are the ones fixed in
``docs/cpiv-jcf/preregistration_addendum_A1_synthetic.md`` §A1.6, written
before any replication output was read. This module only *evaluates* them.
It does not change a threshold, add a seed, drop a draw or reinterpret a
rule; the code is the audit trail for §A1.9.

The development draw (the base seed) is excluded from every tally, as
declared in §A1.1. R3 and R6 are evaluated on replication seeds only. Each
aggregates its replication records before the test: R3 takes the mean
certified coverage of each market specification, and R6 takes the mean
coverage change of each perturbation. Neither rule carries a count, so each
is one number against its bound. Where a rule's replication records are
incomplete, it is reported as not evaluated rather than computed from the
development draw.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_SWEEP_DIR = HERE / "outputs" / "sweep"
DEFAULT_OUTPUT = DEFAULT_SWEEP_DIR / "verdict.json"

DEVELOPMENT_SEED = 20261022
SEED_STRIDE = 7919
REPLICATION_SEEDS: tuple[int, ...] = tuple(
    DEVELOPMENT_SEED + SEED_STRIDE * index for index in range(1, 24)
)

R1_MIN_DRAWS = 16
R2_MIN_DRAWS = 16
R3_MIN_RATIO = 0.5
R4_MIN_DRAWS = 22
R5_MIN_DRAWS = 16
R5_COVERAGE_TOLERANCE = 0.10
R6_MAX_COVERAGE_SHIFT = 0.15

MARKET_SPECIFICATIONS: tuple[str, ...] = (
    "base",
    "low_vol",
    "high_vol",
    "wide_quotes",
    "very_wide_quotes",
    "coarse_tick",
    "no_wide_sessions",
    "wide_strike_grid",
    "short_dated",
    "long_dated",
)

PERTURBATIONS: tuple[str, ...] = (
    "endpoint_outward",
    "spot_shift_1bp",
    "rate_shift_5bp",
    "stale_spot_3s",
    "half_tick_resolution",
    "relaxed_sync_5s",
)


def _number(row: Mapping[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value is None or value == "":
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _replication_draws(
    records: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Replication draws only: the declared seeds, development draw excluded."""
    selected = [
        record
        for record in records
        if int(_number(record, "seed") or -1) in REPLICATION_SEEDS
    ]
    return sorted(selected, key=lambda record: int(_number(record, "seed") or -1))


def _rule(name: str, statement: str, condition: str, **detail: Any) -> dict[str, Any]:
    return {
        "rule": name,
        "statement": statement,
        "condition": condition,
        "evaluated": bool(detail.pop("evaluated", True)),
        "passed": bool(detail.pop("passed", False)),
        **detail,
    }


def rule_r1(draws: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Certified error below the size-matched block null, in most draws."""
    below = 0
    significant = 0
    evaluable = 0
    for draw in draws:
        mae = _number(draw, "mae_certified_pp")
        null_mean = _number(draw, "frontier_block_null_mean_pp")
        p_value = _number(draw, "frontier_p_block_null")
        if mae is None or null_mean is None or p_value is None:
            continue
        evaluable += 1
        if mae < null_mean:
            below += 1
        if p_value < 0.05:
            significant += 1
    passed = evaluable == len(draws) and below >= R1_MIN_DRAWS and significant >= R1_MIN_DRAWS
    return _rule(
        "R1",
        "The abstention rule selects a set that is genuinely easier to measure.",
        (
            f"certified error below the block-null mean in >= {R1_MIN_DRAWS} of "
            f"{len(draws)} draws, and block-null p < 0.05 in >= {R1_MIN_DRAWS}"
        ),
        passed=passed,
        draws_evaluable=evaluable,
        draws_below_block_null=below,
        draws_block_null_p_below_0_05=significant,
        threshold=R1_MIN_DRAWS,
    )


def rule_r2(draws: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The certified subset carries a lower error than the raw midpoint."""
    better = 0
    evaluable = 0
    for draw in draws:
        certified = _number(draw, "mae_certified_pp")
        raw = _number(draw, "mae_raw_pp")
        if certified is None or raw is None:
            continue
        evaluable += 1
        if certified < raw:
            better += 1
    passed = evaluable == len(draws) and better >= R2_MIN_DRAWS
    return _rule(
        "R2",
        "The protocol's own-set error is lower than the raw midpoint's.",
        f"certified error below raw error in >= {R2_MIN_DRAWS} of {len(draws)} draws",
        passed=passed,
        draws_evaluable=evaluable,
        draws_better=better,
        threshold=R2_MIN_DRAWS,
    )


def rule_r3(specifications: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Coverage does not depend on one particular synthetic market.

    Each market specification's coverage is its mean over the replication
    seeds. The rule tests the lowest of those means against half their median.
    Not evaluated until every market specification has a replication record.
    """
    replicates: dict[str, list[float]] = {}
    for record in _replication_draws(specifications):
        name = str(record.get("draw", ""))
        coverage = _number(record, "coverage_certified")
        if name in MARKET_SPECIFICATIONS and coverage is not None:
            replicates.setdefault(name, []).append(coverage)
    coverages = {name: statistics.fmean(values) for name, values in replicates.items()}
    if set(coverages) != set(MARKET_SPECIFICATIONS):
        return _rule(
            "R3",
            "Certification coverage does not depend on one synthetic market.",
            "every market specification needs a replication-seed record",
            evaluated=False,
            passed=False,
            draws_evaluable=len(coverages),
        )
    values = sorted(coverages.values())
    median = statistics.median(values)
    minimum = values[0]
    ratio = minimum / median if median > 0 else 0.0
    passed = ratio >= R3_MIN_RATIO
    return _rule(
        "R3",
        "Certification coverage does not depend on one synthetic market.",
        (
            f"minimum market-specification coverage >= {R3_MIN_RATIO:.0%} of the "
            "median market-specification coverage"
        ),
        passed=passed,
        draws_evaluable=len(coverages),
        replicates_by_specification={
            name: len(values) for name, values in replicates.items()
        },
        coverage_by_specification=coverages,
        median_coverage=median,
        minimum_coverage=minimum,
        minimum_over_median=ratio,
        threshold=R3_MIN_RATIO,
    )


def rule_r4(draws: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Coverage is non-decreasing in the certification tolerance."""
    monotone = 0
    evaluable = 0
    for draw in draws:
        tight = _number(draw, "coverage_at_0.05_pp")
        primary = _number(draw, "coverage_at_0.10_pp")
        loose = _number(draw, "coverage_at_0.25_pp")
        if tight is None or primary is None or loose is None:
            continue
        evaluable += 1
        if tight <= primary + 1e-12 and primary <= loose + 1e-12:
            monotone += 1
    passed = evaluable == len(draws) and monotone >= R4_MIN_DRAWS
    return _rule(
        "R4",
        "Coverage is non-decreasing in the certification tolerance.",
        f"monotone in >= {R4_MIN_DRAWS} of {len(draws)} draws",
        passed=passed,
        draws_evaluable=evaluable,
        draws_monotone=monotone,
        threshold=R4_MIN_DRAWS,
    )


def rule_r5(draws: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The primary and holdout periods agree in direction and in coverage."""
    sign_agrees = 0
    coverage_agrees = 0
    evaluable = 0
    for draw in draws:
        primary = _number(draw, "error_reduction_primary_pp")
        holdout = _number(draw, "error_reduction_holdout_pp")
        primary_coverage = _number(draw, "coverage_primary_period")
        holdout_coverage = _number(draw, "coverage_holdout_period")
        if primary is None or holdout is None:
            continue
        evaluable += 1
        if (primary > 0.0) == (holdout > 0.0):
            sign_agrees += 1
        if (
            primary_coverage is not None
            and holdout_coverage is not None
            and abs(primary_coverage - holdout_coverage) <= R5_COVERAGE_TOLERANCE
        ):
            coverage_agrees += 1
    passed = (
        evaluable == len(draws)
        and sign_agrees >= R5_MIN_DRAWS
        and coverage_agrees >= R5_MIN_DRAWS
    )
    return _rule(
        "R5",
        "The primary and holdout periods agree.",
        (
            f"error-reduction sign agrees in >= {R5_MIN_DRAWS} draws and coverage "
            f"is within {R5_COVERAGE_TOLERANCE:.0%} in >= {R5_MIN_DRAWS}"
        ),
        passed=passed,
        draws_evaluable=evaluable,
        draws_sign_agrees=sign_agrees,
        draws_coverage_within_tolerance=coverage_agrees,
        threshold=R5_MIN_DRAWS,
    )


def rule_r6(perturbations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """No single perturbation dominates the base-market result.

    Each perturbation's change is its mean over the replication seeds, and the
    rule tests the largest absolute mean. The largest single-draw change is
    reported beside it for inspection but is not the tested quantity. Not
    evaluated until every perturbation has a replication record.
    """
    replicates: dict[str, list[float]] = {}
    for perturbation in _replication_draws(perturbations):
        change = _number(perturbation, "coverage_protocol_change")
        name = str(perturbation.get("name", "?"))
        if change is not None and name in PERTURBATIONS:
            replicates.setdefault(name, []).append(change)
    shifts = {name: statistics.fmean(values) for name, values in replicates.items()}
    if set(shifts) != set(PERTURBATIONS):
        return _rule(
            "R6",
            "The perturbation set does not dominate the result.",
            "every perturbation needs a replication-seed record",
            evaluated=False,
            passed=False,
            draws_evaluable=len(shifts),
        )
    worst = max(abs(value) for value in shifts.values())
    passed = worst <= R6_MAX_COVERAGE_SHIFT
    return _rule(
        "R6",
        "The perturbation set does not dominate the result.",
        (
            f"no perturbation moves certified coverage by more than "
            f"{R6_MAX_COVERAGE_SHIFT:.0%} in absolute value"
        ),
        passed=passed,
        draws_evaluable=len(shifts),
        coverage_change_by_perturbation=shifts,
        worst_absolute_coverage_change=worst,
        worst_single_draw_absolute_change=max(
            abs(value) for values in replicates.values() for value in values
        ),
        threshold=R6_MAX_COVERAGE_SHIFT,
    )


def apply_rules(
    seed_records: Sequence[Mapping[str, Any]],
    specification_records: Sequence[Mapping[str, Any]],
    perturbation_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate every pre-registered rule and report the tally."""
    draws = _replication_draws(seed_records)
    rules = [
        rule_r1(draws),
        rule_r2(draws),
        rule_r3(specification_records),
        rule_r4(draws),
        rule_r5(draws),
        rule_r6(perturbation_records),
    ]
    failed = [rule["rule"] for rule in rules if rule["evaluated"] and not rule["passed"]]
    not_evaluated = [rule["rule"] for rule in rules if not rule["evaluated"]]
    return {
        "status": "pre_registered_synthetic_verdict_only",
        "market_data_used": False,
        "development_seed": DEVELOPMENT_SEED,
        "replication_seeds": list(REPLICATION_SEEDS),
        "replication_draws_evaluated": len(draws),
        "rules": rules,
        "rules_passed": [rule["rule"] for rule in rules if rule["passed"]],
        "rules_failed": failed,
        "rules_not_evaluated": not_evaluated,
        "all_rules_passed": not failed and not not_evaluated,
        "consequence_if_r1_or_r2_fails": (
            "The benchmark shows that abstaining on hard pairs does not buy "
            "accuracy, and the paper's central mechanism claim must be reduced "
            "to coverage and stability only."
        ),
        "source": "docs/cpiv-jcf/preregistration_addendum_A1_synthetic.md §A1.6",
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep-dir", type=Path, default=DEFAULT_SWEEP_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    seed_records = _load_csv(args.sweep_dir / "seed_draws.csv")
    specification_records = _load_csv(args.sweep_dir / "specifications_replication.csv")
    perturbation_records = _load_csv(args.sweep_dir / "perturbations_replication.csv")
    verdict = apply_rules(seed_records, specification_records, perturbation_records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(verdict, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
