from __future__ import annotations

import math

from research.cpiv import r9_diagnostics as r9


def test_integrated_vega_identity_holds_across_contract_grid() -> None:
    rows, maximum_error = r9.bsm_identity_grid()
    assert len(rows) == 24
    assert maximum_error < 1e-10


def test_local_approximation_separates_resolved_from_low_vega_cases() -> None:
    rows, summary = r9.local_approximation_grid()
    assert len(rows) == 720
    assert summary["resolved_n"] == 624
    assert summary["unresolved_low_vega_n"] == 96
    assert summary["median_absolute_error_pp"] < 0.01
    assert summary["p95_absolute_error_pp"] < 0.1
    assert 1.0 < summary["max_absolute_error_pp"] < 2.0
    assert all(
        row["absolute_error_pp"] is not None
        for row in rows
        if row["status"] == "resolved"
    )


def test_inversion_audit_counts_rejected_quotes_without_clipping() -> None:
    rows, summary = r9.inversion_diagnostics()
    assert len(rows) == 120
    assert (
        summary["successfully_inverted_generated_quotes"]
        + summary["rejected_generated_quotes"]
        == 120
    )
    assert summary["rejected_invalid_price_cases"] == 10
    assert summary["unexpectedly_accepted_invalid_price_cases"] == 0
    assert summary["input_clipping"] is False
    assert summary["max_absolute_repricing_error_usd"] < 1e-8


def test_quote_implied_intervals_disclose_coverage_and_widen_with_spread() -> None:
    rows = r9.quote_interval_diagnostics()
    assert len(rows) == 5
    widths = [row["median_quote_implied_interval_width_pp"] for row in rows]
    coverage = [row["valid_pair_coverage"] for row in rows]
    assert widths == sorted(widths)
    assert coverage == sorted(coverage, reverse=True)
    assert all("not CI" in row["interpretation"] for row in rows)


def test_jarrow_rudd_tree_prices_american_put_at_least_intrinsic_value() -> None:
    price = r9.jarrow_rudd_american_put(
        spot=100.0, strike=100.0, days=30, rate=0.05, q=0.0,
        sigma=0.20, steps=200,
    )
    assert math.isfinite(price)
    assert price >= 0.0


def test_inversion_count_and_wilson_helpers() -> None:
    assert r9._inversion_count([0, 1, 2, 3]) == 0
    assert r9._inversion_count([3, 2, 1, 0]) == 6
    low, high = r9._wilson(0, 100)
    assert low == 0.0
    assert low <= high < 0.05


def test_rank_grid_is_labeled_uncalibrated_and_is_seeded() -> None:
    first, name_membership = r9.rank_sensitivity(replicates_per_seed=1)
    second, name_membership_second = r9.rank_sensitivity(replicates_per_seed=1)
    assert len(first) == 2 * 5 * 6 * 3
    assert len(name_membership) == 10 * 5 * 6 * 3
    assert first == second
    assert name_membership == name_membership_second
    assert all(row["replicates_total"] == 3 for row in first)
    assert all("not market estimate" in row["simulation_status"] for row in first)
