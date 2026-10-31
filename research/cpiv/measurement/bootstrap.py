"""Block bootstrap for the CPIV measurement study.

The dependence unit is the underlying-day, never the option: options quoted on
one underlying-day share a spot, a volatility surface and a liquidity regime,
so treating them as independent would understate the interval.

Baseline and protocol statistics are recomputed on the *same* resampled blocks,
so every reported difference is paired and the interval reflects the
clustering rather than the per-option noise.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

Statistic = Callable[[Sequence[str]], float | None]
Blocks = Mapping[str, Sequence[str]]


@dataclass(frozen=True)
class BootstrapResult:
    """One bootstrap estimate with its percentile interval and p-value."""

    estimate: float
    lower: float
    upper: float
    p_value: float
    resamples: int
    effective_resamples: int
    unit: str
    seed: int
    null_value: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "estimate": self.estimate,
            "ci_lower": self.lower,
            "ci_upper": self.upper,
            "p_value": self.p_value,
            "resamples": self.resamples,
            "effective_resamples": self.effective_resamples,
            "unit": self.unit,
            "seed": self.seed,
            "null_value": self.null_value,
        }


def percentile(sorted_values: Sequence[float], probability: float) -> float:
    """Linear-interpolated quantile of an already sorted sample."""
    if not sorted_values:
        raise ValueError("percentile of an empty sample")
    position = (len(sorted_values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def _p_value(values: Sequence[float], null: float) -> float:
    """Two-sided bootstrap p-value for a null value, floored at one resample."""
    count = len(values)
    below = sum(1 for value in values if value <= null)
    above = sum(1 for value in values if value >= null)
    probability = 2.0 * min(below, above) / count
    return min(1.0, max(1.0 / count, probability))


def _resample(blocks: Blocks, rng: random.Random) -> list[str]:
    keys = list(blocks)
    if not keys:
        return []
    drawn = rng.choices(keys, k=len(keys))
    return [item for key in drawn for item in blocks[key]]


def _observed(blocks: Blocks) -> list[str]:
    return [item for key in blocks for item in blocks[key]]


def _run(
    blocks: Blocks,
    statistic: Statistic,
    resamples: int,
    seed: int,
    confidence: float,
    unit: str,
    null_value: float,
) -> BootstrapResult:
    if resamples < 1:
        raise ValueError("resamples must be positive")
    observed = statistic(_observed(blocks))
    if observed is None:
        raise ValueError("statistic is undefined on the observed sample")
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(resamples):
        value = statistic(_resample(blocks, rng))
        if value is not None:
            values.append(value)
    if not values:
        raise ValueError("statistic is undefined on every resample")
    values.sort()
    alpha = (1.0 - confidence) / 2.0
    return BootstrapResult(
        estimate=observed,
        lower=percentile(values, alpha),
        upper=percentile(values, 1.0 - alpha),
        p_value=_p_value(values, null_value),
        resamples=resamples,
        effective_resamples=len(values),
        unit=unit,
        seed=seed,
        null_value=null_value,
    )


def block_bootstrap(
    blocks: Blocks,
    statistic: Statistic,
    *,
    resamples: int = 2000,
    seed: int = 20261022,
    confidence: float = 0.95,
    unit: str = "underlying-day",
    null_value: float = 0.0,
) -> BootstrapResult:
    """Bootstrap one statistic by resampling whole blocks with replacement."""
    return _run(blocks, statistic, resamples, seed, confidence, unit, null_value)


def paired_block_bootstrap(
    blocks: Blocks,
    baseline: Statistic,
    protocol: Statistic,
    *,
    resamples: int = 2000,
    seed: int = 20261022,
    confidence: float = 0.95,
    unit: str = "underlying-day",
    null_value: float = 0.0,
) -> BootstrapResult:
    """Bootstrap ``protocol - baseline`` on identical resampled blocks."""
    if baseline is protocol:
        raise ValueError("baseline and protocol statistics must differ")

    def difference(sample: Sequence[str]) -> float | None:
        left = baseline(sample)
        right = protocol(sample)
        if left is None or right is None:
            return None
        return right - left

    return _run(blocks, difference, resamples, seed, confidence, unit, null_value)
