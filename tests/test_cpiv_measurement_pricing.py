from __future__ import annotations

import numpy as np
import pytest
from research.cpiv.measurement.dgp import american_put_price
from research.cpiv.measurement.pricing import american_put_prices

CASES = [
    # spot, strike, days, rate, dividend, sigma
    (100.0, 100.0, 30, 0.05, 0.0, 0.22),
    (100.0, 90.0, 60, 0.05, 0.0, 0.28),
    (100.0, 110.0, 14, 0.05, 0.0, 0.16),
    (250.0, 240.0, 30, 0.05, 0.0, 0.24),
    (60.0, 70.0, 45, 0.03, 0.0, 0.35),
]


def test_the_batch_pricer_agrees_with_the_scalar_reference() -> None:
    spots = [case[0] for case in CASES]
    strikes = [case[1] for case in CASES]
    maturities = [case[2] / 365.0 for case in CASES]
    rates = [case[3] for case in CASES]
    dividends = [case[4] for case in CASES]
    sigmas = [case[5] for case in CASES]
    batch = american_put_prices(
        spots, strikes, maturities, rates, dividends, sigmas, steps=800
    )
    scalar = [
        american_put_price(spot, strike, days, rate, dividend, sigma, 800)
        for spot, strike, days, rate, dividend, sigma in CASES
    ]
    for computed, reference in zip(batch, scalar, strict=True):
        assert float(computed) == pytest.approx(reference, abs=1e-8, rel=1e-10)


def test_the_batch_pricer_is_deterministic() -> None:
    arguments = (
        [case[0] for case in CASES],
        [case[1] for case in CASES],
        [case[2] / 365.0 for case in CASES],
        [case[3] for case in CASES],
        [case[4] for case in CASES],
        [case[5] for case in CASES],
    )
    first = american_put_prices(*arguments, steps=800)
    second = american_put_prices(*arguments, steps=800)
    assert np.array_equal(first, second)


def test_the_reference_price_converges_with_more_tree_steps() -> None:
    """The declared 800-step reference is checked against 400 and 1600 steps."""
    spot, strike, days, rate, dividend, sigma = CASES[0]
    prices = [
        american_put_price(spot, strike, days, rate, dividend, sigma, steps)
        for steps in (200, 400, 800, 1600)
    ]
    assert prices[0] < prices[1] < prices[2] < prices[3]
    coarse = abs(prices[3] - prices[2])
    assert coarse < 1e-3
    assert abs(prices[2] - prices[1]) < 1e-2


def test_the_batch_pricer_rejects_mismatched_arrays() -> None:
    with pytest.raises(ValueError):
        american_put_prices([100.0, 100.0], [100.0], [0.1, 0.1], [0.05, 0.05], [0.0, 0.0], [0.2, 0.2])


def test_the_batch_pricer_rejects_a_non_positive_volatility() -> None:
    with pytest.raises(ValueError):
        american_put_prices([100.0], [100.0], [0.1], [0.05], [0.0], [0.0])


def test_an_empty_batch_returns_an_empty_result() -> None:
    result = american_put_prices([], [], [], [], [], [])
    assert result.size == 0
