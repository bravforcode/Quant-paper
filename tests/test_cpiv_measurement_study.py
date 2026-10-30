from __future__ import annotations

import pytest
from research.cpiv.measurement.dgp import GeneratorConfig, generate_market
from research.cpiv.measurement.status import TerminalStatus
from research.cpiv.measurement.study import (
    StudySettings,
    mean_abs_error,
    run_protocol,
    study_report,
)

SMALL = GeneratorConfig(trading_days=4)
SETTINGS = StudySettings(bootstrap_resamples=120, bootstrap_seed=17)


@pytest.fixture(scope="module")
def rows() -> list[object]:
    pairs, _counts = generate_market(SMALL)
    return run_protocol(pairs, SETTINGS)


def test_every_attempted_pair_receives_exactly_one_terminal_status(rows: list[object]) -> None:
    assert rows
    for row in rows:
        assert isinstance(row.terminal, TerminalStatus)


def test_certification_selects_the_pairs_the_midpoint_measures_well(
    rows: list[object],
) -> None:
    certified = {
        row.pair_id
        for row in rows
        if row.protocol_certified_cpiv_pp is not None
    }
    raw = {row.pair_id: row.raw_cpiv_pp for row in rows if row.raw_cpiv_pp is not None}
    truth = {row.pair_id: row.true_cpiv_pp for row in rows if row.true_cpiv_pp is not None}
    assert certified
    common_all = sorted(set(raw) & set(truth))
    common_certified = sorted(certified & set(raw) & set(truth))
    assert common_certified
    error_all = mean_abs_error(
        {key: raw[key] for key in common_all}, {key: truth[key] for key in common_all}
    )
    error_certified = mean_abs_error(
        {key: raw[key] for key in common_certified},
        {key: truth[key] for key in common_certified},
    )
    assert error_all is not None and error_certified is not None
    assert error_certified < error_all


def test_the_abstained_pairs_carry_the_error_the_protocol_refused(
    rows: list[object],
) -> None:
    abstained = [row for row in rows if row.protocol_certified_cpiv_pp is None]
    certified = [row for row in rows if row.protocol_certified_cpiv_pp is not None]
    assert abstained
    assert certified

    def error(group: list[object]) -> float | None:
        values = {row.pair_id: row.raw_cpiv_pp for row in group if row.raw_cpiv_pp is not None}
        truth = {row.pair_id: row.true_cpiv_pp for row in group if row.true_cpiv_pp is not None}
        return mean_abs_error(values, truth)

    abstained_error = error(abstained)
    certified_error = error(certified)
    assert abstained_error is not None and certified_error is not None
    assert abstained_error > certified_error


def test_the_report_reconciles_and_reports_a_tolerance_grid() -> None:
    pairs, _counts = generate_market(SMALL)
    report = study_report(pairs, SETTINGS, SMALL)
    reconciliation = report["reconciliation"]
    assert isinstance(reconciliation, dict)
    assert reconciliation["attempted"] == len(pairs)
    counts = reconciliation["terminal_counts"]
    assert isinstance(counts, dict)
    assert sum(counts.values()) == len(pairs)
    grid = report["coverage_by_tolerance"]
    assert isinstance(grid, list)
    coverages = [float(row["coverage_of_attempted"]) for row in grid]
    assert coverages == sorted(coverages)
    assert report["market_data_used"] is False


def test_the_replication_split_reports_two_periods() -> None:
    pairs, _counts = generate_market(SMALL)
    report = study_report(pairs, SETTINGS, SMALL)
    replication = report["replication"]
    assert isinstance(replication, dict)
    periods = replication["periods"]
    assert isinstance(periods, dict)
    assert set(periods) == {"primary", "holdout"}


def test_the_perturbations_cover_the_declared_set() -> None:
    pairs, _counts = generate_market(SMALL)
    report = study_report(pairs, SETTINGS, SMALL)
    perturbations = report["perturbations"]
    assert isinstance(perturbations, list)
    names = {row["name"] for row in perturbations}
    assert "endpoint_outward" in names
    assert "stale_spot_3s" in names
    assert "half_tick_resolution" in names
