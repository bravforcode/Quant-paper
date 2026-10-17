from __future__ import annotations

import math

from research.cpiv import build_demo as demo
from research.cpiv import independent_bsm_crosscheck as independent
from research.cpiv import near_bound_decimal_audit as decimal_audit
from research.cpiv import r10_diagnostics as r10


def test_common_bsm_mapping_identity_and_zero_spread_limit() -> None:
    rows, maximum_error = r10.bsm_identity_grid()
    assert len(rows) == 24
    assert maximum_error < 1e-10
    assert all(math.isclose(
        row["residual_from_average_vega_usd"], row["integrated_vega_usd"],
        rel_tol=1e-13, abs_tol=1e-13,
    ) for row in rows)

    average = r10.average_vega(100.0, 100.0, 30, 0.03, 0.01, 0.2, 0.2)
    point = r10._vega_decimal(100.0, 100.0, 30, 0.03, 0.01, 0.2)
    assert math.isclose(average, point, rel_tol=0.0, abs_tol=0.0)
    assert 100.0 * 0.0 / average == 0.0


def test_separate_implementation_checks_non_european_price_origins() -> None:
    rows = independent.run_checks()
    assert len(rows) == 4
    assert {row["case"] for row in rows} == {
        "european_bsm_unequal_iv",
        "american_origin_put_common_bsm_inversion",
        "stale_source_spot_common_inversion_inputs",
        "admissible_arbitrary_price_perturbation",
    }
    assert max(row["absolute_identity_gap"] for row in rows) < 1e-8
    assert all("not independent human replication" in row["interpretation"]
               for row in rows)


def test_decimal_reference_resolves_a_double_precision_bound_ambiguity() -> None:
    assert str(decimal_audit.PI).startswith(
        "3.1415926535897932384626433832795028841971"
    )
    assert decimal_audit._normal_cdf(decimal_audit._D(0)) == decimal_audit._D("0.5")
    spot, strike, days = decimal_audit._D(80), decimal_audit._D(100), decimal_audit._D(7)
    rate, yield_ = decimal_audit._D("0.03"), decimal_audit._D("0.01")
    target_iv = decimal_audit._D("0.2")
    exact_price = decimal_audit._bsm_price(
        "put", spot, strike, days, rate, yield_, target_iv
    )
    lower, upper = decimal_audit._price_bounds(
        "put", spot, strike, days, rate, yield_
    )
    double_price = demo.bs_price("put", 80.0, 100.0, 7, 0.03, 0.01, 0.2)
    float_lower, _ = demo.price_bounds("put", 80.0, 100.0, 7, 0.03, 0.01)
    assert lower < exact_price < upper
    assert exact_price-lower < decimal_audit._D("1e-10")
    assert decimal_audit._D(str(double_price)) < decimal_audit._D(str(float_lower))


def test_paired_iv_gradient_matches_central_finite_differences() -> None:
    spot, strike, days, rate, q = 100.0, 100.0, 30.0, 0.03, 0.01
    sigma_call, sigma_put = 0.24, 0.20
    call = demo.bs_price("call", spot, strike, days, rate, q, sigma_call)
    put = demo.bs_price("put", spot, strike, days, rate, q, sigma_put)
    analytic = r10.paired_cpiv_input_gradient(
        spot, strike, int(days), rate, q, sigma_call, sigma_put
    )

    def cpiv(c: float, p: float, s: float, k: float, t: float,
             r: float, y: float) -> float:
        call_iv = demo.implied_volatility("call", c, s, k, t*365.0, r, y)
        put_iv = demo.implied_volatility("put", p, s, k, t*365.0, r, y)
        return 100.0*(call_iv-put_iv)

    base = {
        "call_price": call, "put_price": put, "spot": spot,
        "strike": strike, "maturity": days/365.0,
        "rate": rate, "effective_yield": q,
    }
    argument_names = {
        "call_price": "c", "put_price": "p", "spot": "s",
        "strike": "k", "maturity": "t", "rate": "r",
        "effective_yield": "y",
    }
    steps = {
        "call_price": 1e-4, "put_price": 1e-4, "spot": 1e-4,
        "strike": 1e-4, "maturity": 1e-5, "rate": 1e-6,
        "effective_yield": 1e-6,
    }
    for key, h in steps.items():
        plus, minus = base.copy(), base.copy()
        plus[key] += h
        minus[key] -= h
        plus_args = {argument_names[k]: value for k, value in plus.items()}
        minus_args = {argument_names[k]: value for k, value in minus.items()}
        finite_difference = (cpiv(**plus_args)-cpiv(**minus_args))/(2.0*h)
        assert math.isclose(analytic[key], finite_difference,
                            rel_tol=2e-6, abs_tol=1e-5), key


def test_local_approximation_reports_full_grid_and_separate_errors() -> None:
    rows, summary = r10.local_approximation_grid()
    assert len(rows) == 720
    assert summary["configuration_n"] == 120
    assert summary["spread_cells_per_configuration"] == 6
    assert summary["resolved_n"] == 624
    assert summary["unresolved_low_vega_n"] == 96
    assert summary["p95_quantile_method"] == "nearest_rank"
    assert summary["p95_order_statistic_index_1_based"] == 593
    assert summary["endpoint_error_aggregation"] == (
        "separate_by_reference_not_pooled"
    )
    assert summary["max_simpson_2000_vs_4000_gap_usd"] >= 0.0
    assert all("direct_residual_numerical_gap_usd" in row for row in rows)
    assert all("normalized_midpoint_vega" in row for row in rows)
    normalized_unresolved = summary["unresolved_normalized_midpoint_vega"]
    assert normalized_unresolved["configuration_n"] == 16
    assert normalized_unresolved["spread_cells_per_configuration"] == 6
    assert "p95" not in normalized_unresolved
    assert math.isclose(
        normalized_unresolved["median"], 1.4039327684551616e-14,
        rel_tol=1e-12,
    )
    assert math.isclose(
        normalized_unresolved["maximum"], 1.7239174110291308e-10,
        rel_tol=1e-12,
    )
    separation = summary["normalized_vega_guard_separation"]
    assert separation["resolved_configuration_n"] == 104
    assert separation["unresolved_configuration_n"] == 16
    assert math.isclose(
        separation["minimum_resolved"], 7.29891186309596e-06,
        rel_tol=1e-12,
    )
    assert math.isclose(
        separation["maximum_unresolved"], normalized_unresolved["maximum"],
        rel_tol=1e-12,
    )
    assert math.isclose(
        separation["min_resolved_to_max_unresolved_ratio"],
        42339.104045238,
        rel_tol=1e-12,
    )
    endpoint_summaries = summary["reference_error_summary_resolved_pp"]
    assert endpoint_summaries["put_endpoint"]["n"] == 624
    assert endpoint_summaries["call_endpoint"]["n"] == 624
    assert endpoint_summaries["put_endpoint"]["p95_order_statistic_index_1_based"] == 593
    assert endpoint_summaries["put_endpoint"]["p95_abs_error"] == (
        endpoint_summaries["call_endpoint"]["p95_abs_error"]
    )
    design_fields = (
        "spot_strike_ratio", "days_to_expiry", "reference_iv_decimal",
        "rate", "effective_yield", "target_cpiv_pp",
    )
    by_design = {
        tuple(row[field] for field in design_fields): row for row in rows
    }
    for row in rows:
        if row["target_cpiv_pp"] <= 0:
            continue
        mirrored_key = tuple(row[field] for field in design_fields[:-1]) + (
            -row["target_cpiv_pp"],
        )
        mirrored = by_design[mirrored_key]
        for left, right in (
            (row["absolute_error_call_endpoint_pp"],
             mirrored["absolute_error_put_endpoint_pp"]),
            (row["absolute_error_put_endpoint_pp"],
             mirrored["absolute_error_call_endpoint_pp"]),
        ):
            if left is None or right is None:
                assert left is right
            else:
                assert math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)
    assert any(
        row["absolute_error_put_endpoint_pp"]
        != row["absolute_error_call_endpoint_pp"]
        for row in rows
        if row["absolute_error_put_endpoint_pp"] is not None
        and row["absolute_error_call_endpoint_pp"] is not None
    )


def test_uncertainty_reports_normal_theory_mcse_for_direct_sd() -> None:
    rows = r10.uncertainty_scenarios()
    assert len(rows) == 6
    for row in rows:
        n = row["resolved_replicates"]
        expected = row["direct_perturbation_cpiv_sd_pp"] / math.sqrt(
            2.0 * (n - 1)
        )
        assert row["direct_perturbation_sd_mcse_method"] == (
            "s/sqrt(2*(n-1)); normal-theory approximation"
        )
        assert math.isclose(
            row["direct_perturbation_sd_mcse_normal_theory_pp"], expected
        )


def test_concave_magnitude_signal_is_bounded_not_heavy_tailed() -> None:
    assert r10.SIGNAL_FAMILIES[-1] == "concave_magnitude"
    signal = r10._signals(50, "concave_magnitude")
    assert min(signal) == -1.0
    assert max(signal) == 1.0
    assert all(-1.0 <= value <= 1.0 for value in signal)


def test_quote_interval_outputs_use_pp_and_explicit_denominators() -> None:
    rows = r10.quote_interval_diagnostics()
    assert len(rows) == 5
    assert all(row["four_endpoint_invertible_pair_count"] == 10 for row in rows)
    assert all(row["nonoverlap_all_possible_pair_denominator"] == 45 for row in rows)
    assert all("not statistical coverage" in row["interpretation"] for row in rows)
    assert [row["median_quote_implied_interval_width_pp"] for row in rows] == sorted(
        row["median_quote_implied_interval_width_pp"] for row in rows
    )


def test_rank_specification_reports_paired_mc_uncertainty_and_denominators() -> None:
    rows, names, contrasts = r10.rank_sensitivity(replicates_per_seed=1)
    assert len(rows) == 2*5*8*3
    assert len(names) == 5*8*3*1*10
    assert len(contrasts) == 2*5*8*4*2
    assert all(row["replicates_total"] == 3 for row in rows)
    assert all(math.isfinite(row["mean_spearman_rank_correlation_mcse"])
               for row in rows)
    assert all(row["paired_replicate_denominator"] == 3 for row in contrasts)
    correlated = next(row for row in rows
                      if row["noise_family"] ==
                      "call_put_correlated_rho_0.8_fixed_leg_sd")
    assert math.isclose(
        correlated["theoretical_marginal_cpiv_noise_sd_pp"],
        correlated["configured_noise_scale_pp"]*math.sqrt(0.4),
    )


def test_american_comparison_uses_explicit_successive_grid_rule() -> None:
    rows = r10.american_convergence()
    assert len(rows) == 2*len(r10.AMERICAN_STEPS)
    assert {row["steps"] for row in rows} == set(r10.AMERICAN_STEPS)
    assert all(row["successive_change_tolerance_pp"] ==
               r10.AMERICAN_SUCCESSIVE_CPIV_TOLERANCE_PP for row in rows)
    assert all(row["meets_selected_successive_change_threshold"] is None
               for row in rows if row["steps"] == r10.AMERICAN_STEPS[0])
