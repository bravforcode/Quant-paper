"""The interval-only ablation: an exploratory check on the declared pairs.

The ablation is not pre-registered. It removes resolution stages one at a time
(and then both together) and reports what each removal admits, on the same
synthetic pairs and settings as the primary study.
"""

from __future__ import annotations

import pytest

from research.cpiv import build_demo as bsm
from research.cpiv.measurement.ablation import VARIANTS, run_ablation
from research.cpiv.measurement.dgp import GeneratorConfig, generate_market
from research.cpiv.measurement.resolution import ResolutionInput, resolve
from research.cpiv.measurement.status import Stage, TerminalStatus
from research.cpiv.measurement.study import StudySettings, run_protocol

SMALL = GeneratorConfig(trading_days=4)
SETTINGS = StudySettings(bootstrap_resamples=120, bootstrap_seed=17)
HALF_SPREAD = 0.001


def _pair(strike: float, sigma: float = 0.2, days: int = 30) -> ResolutionInput:
    """A pair at spot 100, flat volatility, and a symmetric spread on each leg."""
    call = bsm.bs_price("call", 100.0, strike, days, 0.0, 0.0, sigma)
    put = bsm.bs_price("put", 100.0, strike, days, 0.0, 0.0, sigma)
    return ResolutionInput(
        pair_id=f"k{strike:g}",
        call_mid=call,
        put_mid=put,
        call_bid=call - HALF_SPREAD,
        call_ask=call + HALF_SPREAD,
        put_bid=put - HALF_SPREAD,
        put_ask=put + HALF_SPREAD,
        spot=100.0,
        strike=strike,
        days=days,
    )


def _certified(rows: list[object]) -> set[str]:
    return {
        row.pair_id
        for row in rows
        if row.terminal is TerminalStatus.RESOLVED_WITHIN_TOLERANCE
    }


def test_the_atm_pair_is_certified_with_no_stage_skipped() -> None:
    outcome = resolve(_pair(100.0))
    assert outcome.terminal is TerminalStatus.RESOLVED_WITHIN_TOLERANCE


@pytest.mark.parametrize("stage", [Stage.MIDPOINT, Stage.ENDPOINT, Stage.TOLERANCE])
def test_only_the_time_value_and_finite_shock_stages_can_be_skipped(stage: Stage) -> None:
    with pytest.raises(ValueError):
        resolve(_pair(100.0), skip=frozenset({stage}))


def test_skipping_both_value_stages_moves_a_deep_otm_refusal_past_them() -> None:
    spec = _pair(120.0)
    assert resolve(spec).failed_stage is Stage.TIME_VALUE
    skipped = resolve(spec, skip=frozenset({Stage.TIME_VALUE, Stage.FINITE_SHOCK}))
    assert skipped.failed_stage not in (Stage.TIME_VALUE, Stage.FINITE_SHOCK)


@pytest.fixture(scope="module")
def market() -> list[object]:
    pairs, _counts = generate_market(SMALL)
    return pairs


@pytest.fixture(scope="module")
def results(market: list[object]) -> dict[str, list[object]]:
    return run_ablation(market, SETTINGS)


def test_the_full_variant_certifies_what_the_declared_protocol_certifies(
    market: list[object], results: dict[str, list[object]]
) -> None:
    protocol = run_protocol(market, SETTINGS)
    expected = {
        row.pair_id for row in protocol if row.protocol_certified_cpiv_pp is not None
    }
    assert _certified(results["full_protocol"]) == expected


def test_every_variant_keeps_every_attempted_pair(
    market: list[object], results: dict[str, list[object]]
) -> None:
    attempted = len(run_protocol(market, SETTINGS))
    assert set(results) == set(VARIANTS)
    for rows in results.values():
        assert len(rows) == attempted


def test_skipping_a_stage_never_removes_a_certification(
    results: dict[str, list[object]],
) -> None:
    full = _certified(results["full_protocol"])
    for rows in results.values():
        assert full <= _certified(rows)


def test_a_variant_only_admits_pairs_refused_at_a_stage_it_skips(
    results: dict[str, list[object]],
) -> None:
    refused_at = {row.pair_id: row.failed_stage for row in results["full_protocol"]}
    full = _certified(results["full_protocol"])
    for name, skip in VARIANTS.items():
        for pair_id in _certified(results[name]) - full:
            assert refused_at[pair_id] in skip
