"""Batched Cox–Ross–Rubinstein pricing for the ground-truth generator.

The American put leg is the only expensive object in the synthetic market:
one tree per (underlying, day, expiry, strike) combination, and a market of
894 pairs needs 894 trees. The scalar reference in
:func:`research.cpiv.measurement.dgp.american_put_price` evaluates one tree
at a time; this module evaluates the whole market in one pass.

The batching is an algebraic rearrangement, not a different tree. For a
recombining CRR lattice with up factor :math:`u`, down factor :math:`d` and
:math:`d = 1/u`, the stock price at time :math:`t` and node :math:`j` is

.. math:: S(t, j) = S_0 u^{j} d^{\\,t-j} = S_0 d^{\\,t} (u/d)^{j},

so a single precomputed geometric row per option replaces the two power
sequences the scalar version rebuilds at every step. The arithmetic differs
from the scalar version only in the last floating-point bits; the difference
is bounded by the test in ``tests/test_cpiv_measurement_pricing.py`` and is
eleven orders of magnitude below the smallest tolerance the study declares.

The pricer is the *reference* that defines the synthetic truth. It is not a
claim about the price of any real option.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

__all__ = ["american_put_prices"]


def american_put_prices(
    spots: Sequence[float],
    strikes: Sequence[float],
    maturities: Sequence[float],
    rates: Sequence[float],
    dividend_yields: Sequence[float],
    sigmas: Sequence[float],
    steps: int = 800,
) -> np.ndarray:
    """Price a batch of American puts on a CRR lattice.

    Parameters mirror the scalar reference: ``maturities`` is in years, the
    other arrays are per option, and all arrays must share one length.
    """
    if steps < 1:
        raise ValueError("steps must be positive")
    spot = np.asarray(spots, dtype=float)
    strike = np.asarray(strikes, dtype=float)
    maturity = np.asarray(maturities, dtype=float)
    rate = np.asarray(rates, dtype=float)
    dividend = np.asarray(dividend_yields, dtype=float)
    sigma = np.asarray(sigmas, dtype=float)
    count = spot.size
    arrays = (strike, maturity, rate, dividend, sigma)
    if any(array.size != count for array in arrays):
        raise ValueError("every option array must have the same length")
    if count == 0:
        return np.zeros(0, dtype=float)
    if np.any(spot <= 0.0) or np.any(strike <= 0.0):
        raise ValueError("spot and strike must be positive")
    if np.any(sigma <= 0.0):
        raise ValueError("sigma must be positive")

    dt = maturity / steps
    up = np.exp(sigma * np.sqrt(dt))
    down = 1.0 / up
    growth = np.exp((rate - dividend) * dt)
    probability = (growth - down) / (up - down)
    if not np.all((probability >= 0.0) & (probability <= 1.0)):
        raise ValueError("CRR risk-neutral probability must lie in [0, 1]")
    discount = np.exp(-rate * dt)

    exponents = np.arange(steps + 1.0)
    down_pow = down[:, None] ** exponents[None, :]
    ratio_pow = (up / down)[:, None] ** exponents[None, :]

    stock = (spot * down_pow[:, steps])[:, None] * ratio_pow
    values = np.maximum(strike[:, None] - stock, 0.0)
    for time_step in range(steps - 1, -1, -1):
        stock = (spot * down_pow[:, time_step])[:, None] * ratio_pow[
            :, 0 : time_step + 1
        ]
        continuation = discount[:, None] * (
            probability[:, None] * values[:, 1 : time_step + 2]
            + (1.0 - probability)[:, None] * values[:, 0 : time_step + 1]
        )
        values[:, 0 : time_step + 1] = np.maximum(
            continuation, np.maximum(strike[:, None] - stock, 0.0)
        )
    return values[:, 0]
