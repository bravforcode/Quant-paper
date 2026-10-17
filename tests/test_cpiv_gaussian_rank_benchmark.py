from __future__ import annotations

import math

import numpy as np
import pytest
from research.cpiv import gaussian_rank_benchmark as bench
from research.cpiv import r10_diagnostics as diag
from scipy.stats import multivariate_normal  # type: ignore[import-untyped]


def test_analytic_limits() -> None:
    inv, sign = bench.analytic([0.0, 0.0])
    assert math.isclose(inv, 0.5) and math.isclose(sign, 0.5)
    inv, sign = bench.analytic([-100.0, 100.0])
    assert inv < 1e-12 and sign > 1 - 1e-12


def test_bivariate_cdf_matches_sheppard_and_scipy() -> None:
    assert math.isclose(float(bench.bivariate_normal_cdf(0.0, 0.0, 0.5)), 1.0 / 3.0, abs_tol=1e-12)
    for rho in (0.5, -0.3):
        cov = [[1.0, rho], [rho, 1.0]]
        for a, b in ((-1.3, 0.4), (2.0, -0.7), (0.1, 0.1), (-3.0, -3.0)):
            expected = multivariate_normal.cdf(
                [a, b], mean=[0.0, 0.0], cov=cov, abseps=1e-10, releps=1e-10
            )
            assert math.isclose(float(bench.bivariate_normal_cdf(a, b, rho)), float(expected),
                                abs_tol=1e-8)


def test_expected_spearman_two_names_is_one_minus_two_inversion_probability() -> None:
    signals = [-0.4, 0.3]
    inversion, _ = bench.analytic(signals)
    assert math.isclose(bench.expected_spearman(signals), 1.0 - 2.0 * inversion, abs_tol=1e-12)


def test_expected_spearman_three_names_matches_brute_force() -> None:
    signals = [-0.5, 0.1, 0.6]
    draws = 400_000
    rng = np.random.default_rng(20261017)
    observed_values = np.asarray(signals) + bench.SCALE_PP * rng.standard_normal((draws, 3))
    observed = np.argsort(np.argsort(observed_values, axis=1), axis=1) + 1.0
    truth = np.argsort(np.argsort(signals)) + 1.0
    rho = 1.0 - 6.0 * np.sum((observed - truth) ** 2, axis=1) / (3 * (3 * 3 - 1))
    se = rho.std(ddof=1) / math.sqrt(draws)
    assert abs(float(rho.mean()) - bench.expected_spearman(signals)) < 5.0 * se


def test_expected_spearman_noise_free_limit_is_one() -> None:
    assert math.isclose(
        bench.expected_spearman([-0.3, 0.0, 0.2, 0.9], scale=1e-6), 1.0, abs_tol=1e-9
    )


def test_expected_spearman_rejects_tied_signals() -> None:
    with pytest.raises(ValueError):
        bench.expected_spearman([0.1, 0.1, 0.2])


def test_gaussian_simulator_matches_expected_spearman() -> None:
    signals = diag._signals(10, "equally_spaced")
    spearman_mean, spearman_se = bench.simulate_gaussian(signals, draws=200_000, seed=7)["spearman"]
    assert abs(spearman_mean - bench.expected_spearman(signals)) < 5.0 * spearman_se


def test_gaussian_simulator_matches_analytic_inversion_and_sign() -> None:
    signals = diag._signals(10, "concave_magnitude")
    results = bench.simulate_gaussian(signals, draws=200_000, seed=11)
    analytic_inversion, analytic_sign = bench.analytic(signals)
    inversion_mean, inversion_se = results["inversion"]
    sign_mean, sign_se = results["sign"]
    assert abs(inversion_mean - analytic_inversion) < 5.0 * inversion_se
    assert abs(sign_mean - analytic_sign) < 5.0 * sign_se


def test_holm_adjustment_matches_hand_example() -> None:
    adjusted = bench.holm_adjust([0.01, 0.04, 0.03, 0.005])
    assert adjusted == pytest.approx([0.03, 0.06, 0.06, 0.02])


def test_rank_sensitivity_explicit_defaults_match_module_defaults() -> None:
    implicit, implicit_names, implicit_contrasts = diag.rank_sensitivity(1)
    explicit, explicit_names, explicit_contrasts = diag.rank_sensitivity(
        1,
        seeds=diag.SEEDS,
        noise_sds=diag.NOISE_SDS_PP,
        noise_families=diag.NOISE_FAMILIES,
    )
    assert explicit == implicit
    assert explicit_names == implicit_names
    assert explicit_contrasts == implicit_contrasts


def test_check_handles_zero_standard_error_without_dividing_by_zero() -> None:
    cell = (10, "equally_spaced", "gaussian", 0.5)
    same = bench._check("c", "m", cell, ("ref", 0.2, 0.0), ("est", 0.2, 0.0))
    assert same["z"] == 0.0 and same["p_two_sided"] == 1.0
    different = bench._check("c", "m", cell, ("ref", 0.2, 0.0), ("est", 0.3, 0.0))
    assert math.isinf(different["z"]) and different["p_two_sided"] == 0.0
