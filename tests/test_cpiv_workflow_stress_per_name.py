"""Checks for the per-name quote-midpoint stress used in Section 7.9."""

from __future__ import annotations

from research.cpiv import workflow_comparison as wc
from research.cpiv import workflow_stress_per_name as wsp


def test_wilson_interval_handles_zero_and_full_counts() -> None:
    low, high = wsp.wilson_interval(0, 1000)
    assert low == 0.0
    assert 0.0 < high < 0.005

    low, high = wsp.wilson_interval(1000, 1000)
    assert high == 1.0
    assert 0.995 < low < 1.0

    assert wsp.wilson_interval(0, 0) == (None, None)


def test_per_name_offsets_stay_within_bound_and_are_seeded() -> None:
    first = wsp.draw_offsets(50, 3, 4.0, 0.05)
    assert first == wsp.draw_offsets(50, 3, 4.0, 0.05)
    assert len(first) == 50
    assert all(abs(offset) <= 4.0 * 0.05 for offset in first)
    assert len(set(first)) == len(first)


def test_zero_offsets_reproduce_the_common_scoring_path() -> None:
    draw = wc.draw_cross_section(wc._replicate_rng(10, 0), 10)
    stressed = wsp.score_replicate(draw, tick=0.01, half_spread=0.05, offsets=[0.0] * 10)
    names = [wc.analyse_name(name, tick=0.01, half_spread=0.05) for name in draw]
    assert stressed["E0"] == wc.score_pairs(names, wc.decide_e0)
    assert stressed["E2"] == wc.score_pairs(names, wc.decide_e2)
    assert stressed["quote_misses"] == wsp.quote_miss_count(
        draw, tick=0.01, half_spread=0.05, offsets=[0.0] * 10
    )
