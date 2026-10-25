from __future__ import annotations

import pytest
from research.cpiv import build_demo as bsm
from research.cpiv.measurement.dgp import (
    DEFECT_CROSSED,
    DEFECT_NONE,
    GeneratorConfig,
    american_put_price,
    generate_market,
)

SMALL = GeneratorConfig(trading_days=2)


def test_the_market_is_deterministic_for_a_given_seed() -> None:
    first, first_counts = generate_market(SMALL)
    second, second_counts = generate_market(SMALL)
    assert first_counts == second_counts
    assert [pair.pair_id for pair in first] == [pair.pair_id for pair in second]
    assert [pair.call_bid for pair in first] == [pair.call_bid for pair in second]


def test_a_different_seed_produces_a_different_market() -> None:
    first, _ = generate_market(SMALL)
    second, _ = generate_market(GeneratorConfig(trading_days=2, seed=99))
    assert [pair.call_bid for pair in first] != [pair.call_bid for pair in second]


def test_the_american_put_is_never_worth_less_than_the_european_put() -> None:
    european = bsm.bs_price("put", 100.0, 100.0, 60, 0.05, 0.0, 0.22)
    american = american_put_price(100.0, 100.0, 60, 0.05, 0.0, 0.22, 400)
    assert american >= european - 1e-12
    assert american > european


def test_the_true_cpiv_is_negative_because_the_put_carries_exercise_premium() -> None:
    pairs, _counts = generate_market(SMALL)
    defined = [pair for pair in pairs if pair.true_cpiv_pp is not None]
    assert defined
    assert all(pair.true_cpiv_pp is not None and pair.true_cpiv_pp <= 0.0 for pair in defined)
    assert any(pair.true_cpiv_pp < -0.1 for pair in defined)


def test_the_true_cpiv_is_recovered_from_the_unrounded_fair_values() -> None:
    pairs, _counts = generate_market(SMALL)
    pair = next(p for p in pairs if p.true_cpiv_pp is not None and p.days == 30)
    call = bsm.bs_price(
        "call", pair.spot, pair.strike, pair.days, pair.rate, pair.dividend_yield, 0.22
    )
    put = american_put_price(
        pair.spot, pair.strike, pair.days, pair.rate, pair.dividend_yield, 0.22, 400
    )
    lower, upper = bsm.price_bounds(
        "call", pair.spot, pair.strike, pair.days, pair.rate, pair.dividend_yield
    )
    assert lower < call < upper
    assert put > 0.0


def test_quotes_are_wider_for_wings_and_short_dated_options() -> None:
    pairs, _counts = generate_market(SMALL)
    sixty = [p for p in pairs if p.days == 60 and not p.wide_session]
    day = sixty[0].day
    same_day = [p for p in sixty if p.day == day]
    atm = min(same_day, key=lambda p: abs(p.strike / p.spot - 1.0))
    wing = min(same_day, key=lambda p: abs(p.strike / p.spot - 1.10))
    assert abs(wing.strike / wing.spot - 1.10) < 0.02
    assert wing.half_spread_ticks > atm.half_spread_ticks


def test_bids_never_exceed_asks_except_for_an_injected_crossed_quote() -> None:
    pairs, counts = generate_market(SMALL)
    for pair in pairs:
        if pair.defect == DEFECT_CROSSED:
            continue
        assert pair.call_bid <= pair.call_ask
        assert pair.put_bid <= pair.put_ask
    assert counts.get(DEFECT_CROSSED, 0) > 0
    assert counts.get(DEFECT_NONE, 0) > 0


def test_every_pair_carries_a_block_and_a_consistent_log_moneyness() -> None:
    pairs, _counts = generate_market(SMALL)
    for pair in pairs:
        assert pair.block == f"{pair.underlying}|{pair.day}"
        assert pair.log_moneyness == pytest.approx(
            pair.log_moneyness_checked, rel=1e-9, abs=1e-12
        )
