from __future__ import annotations

from typing import Any

import pytest
from research.cpiv import american_put_crosscheck as xc
from research.cpiv import build_demo as demo

BASE: dict[str, Any] = {"spot": 100.0, "strike": 100.0, "days": 30, "rate": 0.05, "q": 0.0,
                        "sigma": 0.20}
PARAMS = ("spot", "strike", "days", "rate", "q", "sigma")


def _params(case: dict[str, Any]) -> dict[str, Any]:
    return {key: case[key] for key in PARAMS}


def test_crr_tree_matches_existing_codebase_tree() -> None:
    existing = demo.american_price("put", 100.0, 100.0, 30, 0.05, 0.0, 0.20, 800)
    assert xc.crr_put(**BASE, steps=800) == pytest.approx(existing, abs=1e-9)


def test_leisen_reimer_european_limit_is_within_1e6_at_6401_steps() -> None:
    european_tree = xc.leisen_reimer_put(**BASE, steps=6401, exercise=False)
    bsm = demo.bs_price("put", 100.0, 100.0, 30, 0.05, 0.0, 0.20)
    assert abs(european_tree - bsm) < 1e-6


def test_crr_european_limit_is_within_1e4_at_6400_steps() -> None:
    european_tree = xc.crr_put(**BASE, steps=6400, exercise=False)
    bsm = demo.bs_price("put", 100.0, 100.0, 30, 0.05, 0.0, 0.20)
    assert abs(european_tree - bsm) < 1e-4


def test_zero_rate_put_has_no_early_exercise_premium() -> None:
    zero_rate = dict(BASE, rate=0.0)
    american = xc.crr_put(**zero_rate, steps=800)
    european = xc.crr_put(**zero_rate, steps=800, exercise=False)
    assert american == pytest.approx(european, abs=1e-9)


@pytest.mark.parametrize("case", xc.SCENARIOS, ids=lambda case: case["name"])
def test_american_put_dominates_european_and_intrinsic(case: dict[str, Any]) -> None:
    params = _params(case)
    american = xc.crr_put(**params, steps=800)
    european = xc.crr_put(**params, steps=800, exercise=False)
    intrinsic = max(params["strike"] - params["spot"], 0.0)
    assert american >= european - 1e-12
    assert american >= intrinsic - 1e-12


def test_leisen_reimer_is_stable_under_refinement() -> None:
    coarse = xc.leisen_reimer_put(**BASE, steps=801)
    fine = xc.leisen_reimer_put(**BASE, steps=1601)
    assert abs(fine - coarse) < 1e-3


def test_leisen_reimer_requires_odd_steps() -> None:
    with pytest.raises(ValueError):
        xc.leisen_reimer_put(**BASE, steps=800)


@pytest.mark.parametrize("case", [c for c in xc.SCENARIOS if c["rate"] > 0],
                         ids=lambda case: case["name"])
def test_baw_is_bounded_below_by_european_and_close_to_tree(case: dict[str, Any]) -> None:
    params = _params(case)
    baw = xc.baw_american_put(**params)
    european = demo.bs_price("put", params["spot"], params["strike"], params["days"],
                             params["rate"], params["q"], params["sigma"])
    tree = xc.leisen_reimer_put(**params, steps=1601)
    assert baw >= european - 1e-9
    assert abs(baw - tree) <= 0.01 * tree


def test_baw_rejects_zero_rate() -> None:
    with pytest.raises(ValueError):
        xc.baw_american_put(**dict(BASE, rate=0.0))


def test_scenario_rows_carry_all_methods_and_no_market_data() -> None:
    rows = xc.scenario_rows()
    methods = {row["method"] for row in rows}
    assert methods == {"CRR", "CRR_Richardson", "Jarrow-Rudd", "Jarrow-Rudd_Richardson",
                       "Leisen-Reimer", "Barone-Adesi-Whaley"}
    assert all(row["status"] == "author_run_synthetic_numerical_check" for row in rows)


def test_envelope_uses_only_finest_crr_jarrow_rudd_and_leisen_reimer() -> None:
    rows = xc.scenario_rows()
    envelope = xc.envelope_rows(rows)
    assert len(envelope) == len(xc.SCENARIOS)
    assert all(row["methods"] == 3 for row in envelope)
    assert all(row["spread_pp"] >= 0.0 for row in envelope)
    for row in envelope:
        assert abs(row["lr_6401_minus_3201_pp"]) < 1e-3
    atm = next(row for row in envelope if row["scenario"] == "atm_30d_base")
    assert atm["spread_pp"] == pytest.approx(0.001086, abs=1e-6)
    assert atm["baw_minus_lr_6401_pp"] != ""
