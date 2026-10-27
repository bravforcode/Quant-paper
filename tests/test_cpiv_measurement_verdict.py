"""The pre-registered tally uses the replication seeds only (addendum §A1.1).

R3 and R6 are aggregated over the replication seeds before they are tested:
R3 takes each market specification's mean certified coverage, and R6 takes
each perturbation's mean change in certified coverage. Neither rule has a
count threshold, so each is one number tested against its stated bound.
"""

from __future__ import annotations

import pytest
from research.cpiv.measurement.verdict import (
    DEVELOPMENT_SEED,
    MARKET_SPECIFICATIONS,
    PERTURBATIONS,
    REPLICATION_SEEDS,
    apply_rules,
    rule_r3,
    rule_r6,
)


def _spec_records(
    seed: int, coverage: float, **overrides: float
) -> list[dict[str, object]]:
    return [
        {
            "draw": name,
            "seed": seed,
            "coverage_certified": overrides.get(name, coverage),
        }
        for name in MARKET_SPECIFICATIONS
    ]


def _perturbation_records(seed: int, change: float) -> list[dict[str, object]]:
    return [
        {"name": name, "seed": seed, "coverage_protocol_change": change}
        for name in PERTURBATIONS
    ]


def test_r3_is_not_evaluated_on_the_development_seed_alone() -> None:
    rule = rule_r3(_spec_records(DEVELOPMENT_SEED, 0.08))

    assert rule["evaluated"] is False
    assert rule["passed"] is False


def test_r3_ignores_development_seed_records_when_replication_records_exist() -> None:
    records = _spec_records(DEVELOPMENT_SEED, 0.0) + _spec_records(
        REPLICATION_SEEDS[0], 0.08
    )

    rule = rule_r3(records)

    assert rule["evaluated"] is True
    assert rule["passed"] is True
    assert rule["draws_evaluable"] == len(MARKET_SPECIFICATIONS)


def test_r3_is_not_evaluated_until_every_market_specification_has_a_replication_record() -> None:
    rule = rule_r3(
        [{"draw": "base", "seed": REPLICATION_SEEDS[0], "coverage_certified": 0.10}]
    )

    assert rule["evaluated"] is False


def test_r3_averages_each_specification_over_the_replication_seeds() -> None:
    records = _spec_records(REPLICATION_SEEDS[0], 0.10, low_vol=0.10) + _spec_records(
        REPLICATION_SEEDS[-1], 0.10, low_vol=0.02
    )

    rule = rule_r3(records)

    assert rule["coverage_by_specification"]["low_vol"] == pytest.approx(0.06)
    assert rule["passed"] is True


def test_r3_takes_the_statistical_median_of_the_market_specifications() -> None:
    records = [
        {
            "draw": name,
            "seed": REPLICATION_SEEDS[0],
            "coverage_certified": 0.04 if index < 5 else 0.10,
        }
        for index, name in enumerate(MARKET_SPECIFICATIONS)
    ]

    rule = rule_r3(records)

    assert rule["median_coverage"] == pytest.approx(0.07)
    assert rule["passed"] is True


def test_r6_is_not_evaluated_on_the_development_perturbations() -> None:
    rule = rule_r6(_perturbation_records(DEVELOPMENT_SEED, 0.2))

    assert rule["evaluated"] is False
    assert rule["passed"] is False


def test_r6_passes_when_replication_perturbations_stay_within_fifteen_points() -> None:
    rule = rule_r6(_perturbation_records(REPLICATION_SEEDS[0], 0.10))

    assert rule["evaluated"] is True
    assert rule["passed"] is True


def test_r6_is_not_evaluated_until_every_perturbation_has_a_replication_record() -> None:
    rule = rule_r6(
        [
            {
                "name": "spot_shift_1bp",
                "seed": REPLICATION_SEEDS[0],
                "coverage_protocol_change": 0.0,
            }
        ]
    )

    assert rule["evaluated"] is False


def test_r6_uses_the_replicate_mean_of_each_perturbation() -> None:
    records = _perturbation_records(REPLICATION_SEEDS[0], 0.30) + _perturbation_records(
        REPLICATION_SEEDS[-1], 0.10
    )

    rule = rule_r6(records)

    assert rule["worst_absolute_coverage_change"] == pytest.approx(0.20)
    assert rule["passed"] is False


def test_apply_rules_keeps_the_development_draw_out_of_r3_and_r6() -> None:
    verdict = apply_rules(
        [],
        _spec_records(DEVELOPMENT_SEED, 0.0),
        _perturbation_records(DEVELOPMENT_SEED, 0.2),
    )

    assert verdict["rules_not_evaluated"] == ["R3", "R6"]
    assert "R3" not in verdict["rules_failed"]
    assert "R6" not in verdict["rules_failed"]
    assert verdict["all_rules_passed"] is False
