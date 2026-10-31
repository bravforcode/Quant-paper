from __future__ import annotations

from research.cpiv.measurement.verdict import (
    DEVELOPMENT_SEED,
    REPLICATION_SEEDS,
    apply_rules,
    rule_r1,
    rule_r2,
    rule_r4,
    rule_r5,
)


def _draw(seed: int, **overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "seed": seed,
        "mae_raw_pp": 0.5,
        "mae_certified_pp": 0.01,
        "frontier_block_null_mean_pp": 0.5,
        "frontier_p_block_null": 0.001,
        "coverage_at_0.05_pp": 0.0,
        "coverage_at_0.10_pp": 0.08,
        "coverage_at_0.25_pp": 0.30,
        "coverage_primary_period": 0.08,
        "coverage_holdout_period": 0.085,
        "error_reduction_primary_pp": 0.49,
        "error_reduction_holdout_pp": 0.50,
    }
    record.update(overrides)
    return record


def _with(record: dict[str, object], **overrides: object) -> dict[str, object]:
    """Override fields whose names contain characters invalid in identifiers."""
    updated = dict(record)
    updated.update(overrides)
    return updated


def test_the_development_seed_is_excluded_from_the_tally() -> None:
    draws = [_draw(seed) for seed in REPLICATION_SEEDS]
    draws.append(_draw(DEVELOPMENT_SEED))
    verdict = apply_rules(draws, [], {})
    assert verdict["replication_draws_evaluated"] == len(REPLICATION_SEEDS)
    assert DEVELOPMENT_SEED not in REPLICATION_SEEDS


def test_the_declared_replication_seeds_are_the_documented_ones() -> None:
    assert len(REPLICATION_SEEDS) == 23
    assert REPLICATION_SEEDS[0] == DEVELOPMENT_SEED + 7919
    assert REPLICATION_SEEDS[-1] == DEVELOPMENT_SEED + 7919 * 23


def test_r1_passes_when_the_certified_error_is_below_the_block_null() -> None:
    draws = [_draw(seed) for seed in REPLICATION_SEEDS]
    result = rule_r1(draws)
    assert result["passed"] is True
    assert result["draws_below_block_null"] == 23


def test_r1_fails_when_the_null_is_never_beaten() -> None:
    draws = [
        _draw(seed, mae_certified_pp=1.0, frontier_p_block_null=0.9)
        for seed in REPLICATION_SEEDS
    ]
    result = rule_r1(draws)
    assert result["passed"] is False
    assert result["draws_below_block_null"] == 0


def test_r1_is_not_evaluable_when_the_frontier_is_missing() -> None:
    draws = [
        _draw(seed, frontier_block_null_mean_pp=None, frontier_p_block_null=None)
        for seed in REPLICATION_SEEDS
    ]
    result = rule_r1(draws)
    assert result["passed"] is False
    assert result["draws_evaluable"] == 0


def test_r2_compares_the_certified_error_with_the_raw_error() -> None:
    draws = [_draw(seed) for seed in REPLICATION_SEEDS]
    assert rule_r2(draws)["passed"] is True
    worse = [
        _draw(seed, mae_certified_pp=0.9) for seed in REPLICATION_SEEDS
    ]
    assert rule_r2(worse)["passed"] is False


def test_r4_requires_monotone_coverage_in_the_tolerance() -> None:
    draws = [_draw(seed) for seed in REPLICATION_SEEDS]
    assert rule_r4(draws)["passed"] is True
    non_monotone = [
        _with(_draw(seed), **{"coverage_at_0.25_pp": 0.01})
        for seed in REPLICATION_SEEDS
    ]
    assert rule_r4(non_monotone)["passed"] is False


def test_r5_requires_the_sign_and_the_coverage_to_agree() -> None:
    draws = [_draw(seed) for seed in REPLICATION_SEEDS]
    assert rule_r5(draws)["passed"] is True
    flipped = [
        _draw(seed, error_reduction_holdout_pp=-0.5) for seed in REPLICATION_SEEDS
    ]
    assert rule_r5(flipped)["passed"] is False


def test_r5_fails_when_the_period_coverages_diverge() -> None:
    draws = [
        _with(_draw(seed), coverage_holdout_period=0.50)
        for seed in REPLICATION_SEEDS
    ]
    result = rule_r5(draws)
    assert result["passed"] is False
    assert result["draws_coverage_within_tolerance"] == 0


def test_the_verdict_reports_every_rule_and_its_outcome() -> None:
    draws = [_draw(seed) for seed in REPLICATION_SEEDS]
    verdict = apply_rules(draws, [], {"perturbations": []})
    names = {rule["rule"] for rule in verdict["rules"]}
    assert names == {"R1", "R2", "R3", "R4", "R5", "R6"}
    assert verdict["market_data_used"] is False
    assert verdict["rules_passed"] and verdict["rules_failed"] == ["R3", "R6"]


def test_a_failed_rule_is_never_silently_dropped() -> None:
    draws = [_draw(seed) for seed in REPLICATION_SEEDS]
    verdict = apply_rules(draws, [], {"perturbations": []})
    assert len(verdict["rules"]) == 6
    assert verdict["all_rules_passed"] is False
