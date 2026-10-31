from __future__ import annotations

import math

import pytest
from research.cpiv.measurement.bootstrap import (
    block_bootstrap,
    paired_block_bootstrap,
    percentile,
)

BLOCKS: dict[str, list[str]] = {
    "day-1": ["a", "b", "c"],
    "day-2": ["d", "e", "f"],
    "day-3": ["g", "h", "i"],
    "day-4": ["j", "k", "l"],
}


def test_percentile_interpolates_between_observations() -> None:
    assert percentile([0.0, 10.0], 0.0) == 0.0
    assert percentile([0.0, 10.0], 0.5) == pytest.approx(5.0)
    assert percentile([0.0, 10.0], 1.0) == 10.0


def test_percentile_of_an_empty_sample_is_an_error() -> None:
    with pytest.raises(ValueError, match="empty"):
        percentile([], 0.5)


def test_a_constant_statistic_has_a_degenerate_interval() -> None:
    result = block_bootstrap(
        BLOCKS, lambda sample: 1.0, resamples=200, seed=7, unit="underlying-day"
    )
    assert result.estimate == 1.0
    assert result.lower == 1.0
    assert result.upper == 1.0
    assert result.effective_resamples == 200
    assert result.unit == "underlying-day"


def test_the_interval_brackets_the_estimate() -> None:
    def mean(sample: list[str]) -> float:
        return sum(len(item) for item in sample) / len(sample)

    result = block_bootstrap(BLOCKS, mean, resamples=500, seed=11)
    assert result.lower <= result.estimate <= result.upper
    assert 0.0 < result.p_value <= 1.0


def test_the_same_seed_reproduces_the_same_interval() -> None:
    def mean(sample: list[str]) -> float:
        return sum(len(item) for item in sample) / len(sample)

    first = block_bootstrap(BLOCKS, mean, resamples=300, seed=3)
    second = block_bootstrap(BLOCKS, mean, resamples=300, seed=3)
    assert (first.lower, first.upper) == (second.lower, second.upper)


def test_blocks_are_resampled_whole_not_item_by_item() -> None:
    def block_size(sample: list[str]) -> float:
        # Every block contributes exactly three items, so a block bootstrap
        # always returns a multiple of three.
        return float(len(sample))

    result = block_bootstrap(BLOCKS, block_size, resamples=200, seed=5)
    assert result.estimate == 12.0
    assert result.lower == 12.0
    assert result.upper == 12.0


def test_a_statistic_undefined_on_the_observed_sample_is_an_error() -> None:
    with pytest.raises(ValueError, match="undefined on the observed sample"):
        block_bootstrap(BLOCKS, lambda sample: None, resamples=10, seed=1)


def test_paired_bootstrap_reports_the_difference() -> None:
    def low(sample: list[str]) -> float:
        return 1.0

    def high(sample: list[str]) -> float:
        return 3.0

    result = paired_block_bootstrap(BLOCKS, low, high, resamples=100, seed=2)
    assert result.estimate == pytest.approx(2.0)
    assert result.lower == pytest.approx(2.0)
    assert result.upper == pytest.approx(2.0)


def test_paired_bootstrap_refuses_identical_statistics() -> None:
    def same(sample: list[str]) -> float:
        return 1.0

    with pytest.raises(ValueError, match="must differ"):
        paired_block_bootstrap(BLOCKS, same, same, resamples=10, seed=1)


def test_the_p_value_is_never_zero() -> None:
    def always_positive(sample: list[str]) -> float:
        return 5.0

    result = block_bootstrap(
        BLOCKS, always_positive, resamples=50, seed=4, null_value=0.0
    )
    assert result.p_value > 0.0
    assert not math.isnan(result.p_value)
