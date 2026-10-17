from __future__ import annotations

import random

import pytest
from research.cpiv import workflow_comparison as wc


def _record(tau: float, *, cpiv: float | None = None, e2_pass: bool = False,
            lo: float = 0.0, hi: float = 0.0, vega_ok: bool = False) -> dict[str, object]:
    return {"tau": tau, "cpiv_mid": cpiv if cpiv is not None else tau, "e2_pass": e2_pass,
            "lo": lo, "hi": hi, "vega_ok": vega_ok}


def test_observed_quote_rounds_to_nearest_tick_and_clips_bid_at_zero() -> None:
    mid, bid, ask = wc.observed_quote(0.123, 0.01, 0.05)
    assert mid == pytest.approx(0.12)
    assert bid == pytest.approx(0.07)
    assert ask == pytest.approx(0.17)
    mid, bid, ask = wc.observed_quote(0.01, 0.05, 0.25)
    assert mid == pytest.approx(0.0)
    assert bid == 0.0
    assert ask == pytest.approx(0.25)


def test_cross_section_is_seeded_and_within_declared_ranges() -> None:
    first = wc.draw_cross_section(random.Random(7), 25)
    second = wc.draw_cross_section(random.Random(7), 25)
    assert first == second
    assert all(-wc.TAU_PP_RANGE <= name["tau_pp"] <= wc.TAU_PP_RANGE for name in first)
    assert {name["days"] for name in first} <= set(wc.DAYS)
    assert all(name["sigma_call"] > 0.0 for name in first)


def test_truth_treats_gaps_below_margin_as_ties() -> None:
    assert wc.truth_decision(_record(0.2), _record(0.0)) is None
    assert wc.truth_decision(_record(3.0), _record(0.0)) == 1
    assert wc.truth_decision(_record(-1.0), _record(2.0)) == -1


def test_score_pairs_hand_example() -> None:
    names = [_record(3.0), _record(0.0), _record(1.0)]

    def decide(a: dict[str, object], b: dict[str, object]) -> int:
        pair = (a["tau"], b["tau"])
        return {(3.0, 0.0): 1, (3.0, 1.0): 0, (0.0, 1.0): -1}[pair]  # type: ignore[index]

    scored = wc.score_pairs(names, decide)
    assert scored["ordered"] == 3
    assert scored["decided_ordered"] == 2
    assert scored["wrong"] == 0
    assert scored["false_exclusion"] == pytest.approx(1 / 3)


def test_tie_pairs_do_not_enter_wrong_order_denominators() -> None:
    names = [_record(0.2), _record(0.0)]
    scored = wc.score_pairs(names, lambda a, b: 1)
    assert scored["ordered"] == 0
    assert scored["decided_tie"] == 1
    assert scored["wrong_among_decided"] is None
    assert scored["false_resolution"] is None


def test_e2_requires_both_names_to_pass_and_strict_non_overlap() -> None:
    passing = _record(2.0, e2_pass=True, lo=1.0, hi=1.5)
    higher = _record(0.0, e2_pass=True, lo=-1.5, hi=-1.0)
    overlapping = _record(0.5, e2_pass=True, lo=0.8, hi=1.2)
    failing = _record(3.0, e2_pass=False, lo=2.5, hi=3.5)
    assert wc.decide_e2(passing, higher) == 1
    assert wc.decide_e2(higher, passing) == -1
    assert wc.decide_e2(passing, overlapping) == 0
    assert wc.decide_e2(passing, failing) == 0


def test_e0_and_e1_return_undecided_when_midpoint_cpiv_is_missing() -> None:
    missing = _record(1.0, cpiv=None)
    missing["cpiv_mid"] = None
    present = _record(0.0, vega_ok=True)
    assert wc.decide_e0(missing, present) == 0
    assert wc.decide_e1(present, missing) == 0


def test_tick_to_infinity_leaves_every_method_unresolved() -> None:
    rng = random.Random(17)
    names = [wc.analyse_name(name, tick=1000.0, half_spread=0.0)
             for name in wc.draw_cross_section(rng, 10)]
    for decide in (wc.decide_e0, wc.decide_e1, wc.decide_e2):
        assert wc.score_pairs(names, decide)["decided_total"] == 0


def test_zero_spread_fine_tick_e2_decisions_are_a_subset_of_raw_midpoint() -> None:
    rng = random.Random(11)
    e2_decided = 0
    e2_wrong = 0
    for _ in range(20):
        names = [wc.analyse_name(name, tick=1e-6, half_spread=0.0)
                 for name in wc.draw_cross_section(rng, 10)]
        for i, first in enumerate(names):
            for second in names[i + 1:]:
                decision = wc.decide_e2(first, second)
                if decision == 0:
                    continue
                e2_decided += 1
                assert wc.decide_e0(first, second) == decision
                truth = wc.truth_decision(first, second)
                e2_wrong += int(truth is not None and truth != decision)
    assert e2_decided > 0
    assert e2_wrong == 0


def test_coarse_tick_and_wide_spread_leave_e2_with_fewer_decisions_than_e0() -> None:
    rng = random.Random(13)
    e0_decided = e2_decided = 0
    for _ in range(20):
        names = [wc.analyse_name(name, tick=0.05, half_spread=0.25)
                 for name in wc.draw_cross_section(rng, 10)]
        e0_decided += wc.score_pairs(names, wc.decide_e0)["decided_ordered"]
        e2_decided += wc.score_pairs(names, wc.decide_e2)["decided_ordered"]
    assert e2_decided < e0_decided


def test_run_comparison_is_deterministic_for_a_small_replicate_count() -> None:
    first = wc.run_comparison(replicates=2, universe_sizes=(10,), ticks=(0.01,),
                              half_spreads=(0.05,))
    second = wc.run_comparison(replicates=2, universe_sizes=(10,), ticks=(0.01,),
                               half_spreads=(0.05,))
    assert first == second
    methods = {row["method"] for row in first}
    assert set(wc.METHODS) <= methods
    assert {"E1_vs_E0", "universe_diagnostic", "matched_E0_on_E2_pairs"} <= methods
    assert all(row["status"] == wc.STATUS for row in first)


def test_quote_interval_covers_true_price_when_half_spread_is_at_least_half_tick() -> None:
    draws = [wc.draw_cross_section(wc._replicate_rng(10, rep), 10) for rep in range(20)]
    for draw in draws:
        assert wc.coverage_failure_share(draw, 0.005, 0.01, 0.0) == 0.0
        assert wc.coverage_failure_share(draw, 0.05, 0.25, 0.0) == 0.0
    # Tick 0.05 with half-spread 0.01 is below half a tick: coverage is not guaranteed.
    assert any(wc.coverage_failure_share(draw, 0.05, 0.01, 0.0) > 0.0 for draw in draws)
