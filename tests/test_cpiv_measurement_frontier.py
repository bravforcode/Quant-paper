from __future__ import annotations

import pytest
from research.cpiv.measurement.frontier import selection_frontier


def _universe() -> tuple[dict[str, float], dict[str, float], dict[str, list[str]], dict[str, float]]:
    """A small universe where the first block is easy and the rest are hard.

    Twenty pairs live in two blocks of ten. The first block is measured
    without error and the second carries an error of five units, so a
    selection rule that picks the first block must beat a size-matched
    random subset, and a block null must be *less* significant than the
    pair null, because the first block is one of the null's own draws.
    """
    values: dict[str, float] = {}
    truth: dict[str, float] = {}
    displacement: dict[str, float] = {}
    blocks: dict[str, list[str]] = {"day1": [], "day2": []}
    for index in range(10):
        key = f"a{index}"
        values[key] = 1.0 + index * 0.01
        truth[key] = values[key]
        displacement[key] = 0.01
        blocks["day1"].append(key)
    for index in range(10):
        key = f"b{index}"
        values[key] = 1.0 + index * 0.01
        truth[key] = values[key] + 5.0
        displacement[key] = 1.0
        blocks["day2"].append(key)
    return values, truth, displacement, blocks


def test_a_selection_rule_that_picks_the_easy_block_beats_the_size_matched_null() -> None:
    values, truth, displacement, blocks = _universe()
    points = selection_frontier(
        displacement=displacement,
        values=values,
        truth=truth,
        blocks=blocks,
        tolerances=(0.05,),
        trials=500,
        seed=7,
    )
    assert len(points) == 1
    point = points[0]
    assert point.n_certified == 10
    assert point.coverage == pytest.approx(0.5)
    assert point.mae_certified_pp is not None
    assert point.null_mean_pp is not None
    assert point.mae_certified_pp < point.null_mean_pp
    assert point.p_value_pair_null is not None
    assert point.p_value_pair_null < 0.05


def test_the_block_null_is_more_conservative_than_the_pair_null() -> None:
    """A block-aligned selection is not distinguishable from a lucky day.

    The block null draws whole underlying-days, so when the certified subset
    is exactly one day, that day is one of the null's own draws. The block
    null must therefore be *less* significant than the pair null, which
    ignores the dependence structure entirely. This is the conservative
    direction: it makes a positive result harder to claim, not easier.
    """
    values, truth, displacement, blocks = _universe()
    point = selection_frontier(
        displacement=displacement,
        values=values,
        truth=truth,
        blocks=blocks,
        tolerances=(0.05,),
        trials=500,
        seed=7,
    )[0]
    assert point.block_null_mean_pp is not None
    assert point.null_mean_pp is not None
    assert point.p_value_block_null is not None
    assert point.p_value_pair_null is not None
    assert point.p_value_block_null > point.p_value_pair_null
    # The block null has the wider spread, because whole days move together.
    assert point.null_sd_pp is not None
    assert point.null_sd_pp > 0.0


def test_a_selection_spread_across_days_is_significant_under_both_nulls() -> None:
    """When the certified set is not one day, both nulls reject it."""
    values: dict[str, float] = {}
    truth: dict[str, float] = {}
    displacement: dict[str, float] = {}
    blocks: dict[str, list[str]] = {}
    for day in range(10):
        key_block = f"day{day}"
        blocks[key_block] = []
        for index in range(4):
            key = f"{key_block}_{index}"
            values[key] = 1.0 + index * 0.01
            # Every day carries one easy and three hard pairs, so the
            # certified set spans all ten days.
            easy = index == 0
            displacement[key] = 0.01 if easy else 1.0
            truth[key] = values[key] if easy else values[key] + 5.0
            blocks[key_block].append(key)
    point = selection_frontier(
        displacement=displacement,
        values=values,
        truth=truth,
        blocks=blocks,
        tolerances=(0.05,),
        trials=500,
        seed=3,
    )[0]
    assert point.n_certified == 10
    assert point.mae_certified_pp is not None
    assert point.null_mean_pp is not None
    assert point.mae_certified_pp < point.null_mean_pp
    assert point.p_value_pair_null is not None
    assert point.p_value_block_null is not None
    assert point.p_value_pair_null < 0.05
    assert point.p_value_block_null < 0.05


def test_an_arbitrary_selection_does_not_beat_the_null() -> None:
    """A rule that picks the *hard* block must not look significant."""
    values, truth, displacement, blocks = _universe()
    flipped = {
        key: (5.0 if displacement[key] < 0.05 else 0.01) for key in displacement
    }
    point = selection_frontier(
        displacement=flipped,
        values=values,
        truth=truth,
        blocks=blocks,
        tolerances=(0.05,),
        trials=500,
        seed=7,
    )[0]
    assert point.mae_certified_pp is not None
    assert point.null_mean_pp is not None
    assert point.mae_certified_pp > point.null_mean_pp
    assert point.p_value_pair_null is not None
    assert point.p_value_pair_null > 0.05


def test_a_tolerance_that_certifies_nothing_reports_no_null() -> None:
    values, truth, displacement, blocks = _universe()
    point = selection_frontier(
        displacement=displacement,
        values=values,
        truth=truth,
        blocks=blocks,
        tolerances=(0.0,),
        trials=100,
        seed=7,
    )[0]
    assert point.n_certified == 0
    assert point.coverage == 0.0
    assert point.mae_certified_pp is None
    assert point.null_mean_pp is None
    assert point.p_value_pair_null is None


def test_the_p_value_is_the_add_one_estimator() -> None:
    values, truth, displacement, blocks = _universe()
    point = selection_frontier(
        displacement=displacement,
        values=values,
        truth=truth,
        blocks=blocks,
        tolerances=(0.05,),
        trials=200,
        seed=7,
    )[0]
    assert point.p_value_pair_null is not None
    assert point.p_value_pair_null >= 1.0 / (point.trials + 1.0)


def test_the_frontier_is_deterministic_for_a_given_seed() -> None:
    values, truth, displacement, blocks = _universe()
    kwargs = {
        "displacement": displacement,
        "values": values,
        "truth": truth,
        "blocks": blocks,
        "tolerances": (0.05,),
        "trials": 200,
        "seed": 11,
    }
    first = selection_frontier(**kwargs)[0]
    second = selection_frontier(**kwargs)[0]
    assert first.null_mean_pp == second.null_mean_pp
    assert first.block_null_mean_pp == second.block_null_mean_pp
    assert first.p_value_pair_null == second.p_value_pair_null


def test_a_non_positive_trial_count_is_rejected() -> None:
    values, truth, displacement, blocks = _universe()
    with pytest.raises(ValueError):
        selection_frontier(
            displacement=displacement,
            values=values,
            truth=truth,
            blocks=blocks,
            tolerances=(0.05,),
            trials=0,
        )
