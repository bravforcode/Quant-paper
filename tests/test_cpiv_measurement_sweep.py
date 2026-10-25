from __future__ import annotations

from research.cpiv.measurement.dgp import GeneratorConfig
from research.cpiv.measurement.study import StudySettings, own_set_error_reduction, run_protocol
from research.cpiv.measurement.sweep import (
    DECLARED_SEEDS,
    SPECIFICATIONS,
    _draw_record,
    _protocol_variants,
    run_seed_sweep,
    sweep_report,
)


def test_the_declared_seeds_are_the_documented_sequence() -> None:
    assert len(DECLARED_SEEDS) == 24
    assert DECLARED_SEEDS[0] == 20261022
    assert DECLARED_SEEDS[1] - DECLARED_SEEDS[0] == 7919


def test_the_specification_grid_covers_the_declared_factors() -> None:
    names = {specification.name for specification in SPECIFICATIONS}
    assert {
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
        "tolerance_0.05pp",
        "tolerance_0.10pp",
        "tolerance_0.25pp",
        "tolerance_0.50pp",
        "resolution_0.5ticks",
        "resolution_1ticks",
        "resolution_2ticks",
    } == names


def test_the_protocol_variants_vary_one_knob_at_a_time() -> None:
    variants = _protocol_variants()
    tolerances = {
        variant.settings.primary_tolerance_pp
        for variant in variants
        if variant.name.startswith("tolerance_")
    }
    resolutions = {
        variant.settings.resolution_ticks
        for variant in variants
        if variant.name.startswith("resolution_")
    }
    assert tolerances == {0.05, 0.10, 0.25, 0.50}
    assert resolutions == {0.5, 1.0, 2.0}
    for variant in variants:
        assert variant.config == GeneratorConfig()


def test_a_draw_record_reports_every_declared_quantity() -> None:
    from research.cpiv.measurement.dgp import generate_market

    config = GeneratorConfig(trading_days=3)
    settings = StudySettings()
    pairs, _counts = generate_market(config)
    rows = run_protocol(pairs, settings)
    record = _draw_record("seed_test", rows, settings, config.seed)
    for key in (
        "attempted",
        "n_scored",
        "n_certified",
        "coverage_certified",
        "coverage_identified",
        "mae_raw_pp",
        "mae_certified_pp",
        "mae_abstained_pp",
        "raw_median_abs_error_pp",
        "raw_p95_abs_error_pp",
        "raw_share_within_0.10_pp",
        "coverage_at_0.05_pp",
        "coverage_at_0.10_pp",
        "coverage_at_0.25_pp",
        "frontier_null_mean_pp",
        "frontier_block_null_mean_pp",
        "frontier_p_pair_null",
        "frontier_p_block_null",
        "coverage_primary_period",
        "coverage_holdout_period",
        "error_reduction_primary_pp",
        "error_reduction_holdout_pp",
    ):
        assert key in record, key


def test_the_own_set_error_reduction_is_positive_when_abstention_helps() -> None:
    from research.cpiv.measurement.dgp import generate_market

    config = GeneratorConfig(trading_days=4)
    pairs, _counts = generate_market(config)
    rows = run_protocol(pairs, StudySettings())
    reduction = own_set_error_reduction(rows)
    assert reduction is not None
    assert reduction > 0.0


def test_the_sweep_is_deterministic_for_a_given_seed() -> None:
    from research.cpiv.measurement.dgp import generate_market

    config = GeneratorConfig(trading_days=2)
    pairs, _counts = generate_market(config)
    settings = StudySettings()
    rows = run_protocol(pairs, settings)
    first = _draw_record("seed_x", rows, settings, config.seed)
    second = _draw_record("seed_x", rows, settings, config.seed)
    assert first == second


def test_the_sweep_report_states_that_no_market_data_is_used() -> None:
    report = sweep_report([], [])
    assert report["market_data_used"] is False
    assert report["network_access_used"] is False
    assert "not a market estimate" in report["warning"]


def test_the_seed_sweep_returns_one_record_per_declared_seed() -> None:
    records = run_seed_sweep(DECLARED_SEEDS[:2])
    assert len(records) == 2
    assert [record["seed"] for record in records] == list(DECLARED_SEEDS[:2])
    for record in records:
        assert int(record["attempted"]) > 0
        assert 0.0 <= float(record["coverage_certified"]) <= 1.0
