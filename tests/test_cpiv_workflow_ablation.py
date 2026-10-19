from __future__ import annotations

import pytest

from research.cpiv import workflow_ablation as ab
from research.cpiv import workflow_comparison as wc


def _interval(lo: float, hi: float, ok: bool = True) -> dict[str, float | bool]:
    return {"e3_ok": ok, "e3_lo": lo, "e3_hi": hi}


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        (_interval(1.0, 2.0), _interval(-1.0, 0.5), 1),
        (_interval(-3.0, -1.0), _interval(0.0, 2.0), -1),
        (_interval(0.0, 2.0), _interval(1.0, 3.0), 0),
        (_interval(0.0, 0.0, ok=False), _interval(-5.0, -4.0), 0),
        (_interval(5.0, 6.0), _interval(0.0, 0.0, ok=False), 0),
    ],
)
def test_decide_e3_orders_only_disjoint_intervals(first, second, expected) -> None:
    assert ab.decide_e3(first, second) == expected


def test_e3_interval_matches_e2_interval_when_screens_pass() -> None:
    name = next(
        candidate
        for candidate in wc.draw_cross_section(wc._replicate_rng(10, 0), 10)
        if wc.analyse_name(candidate, tick=0.005, half_spread=0.01)["e2_pass"]
    )
    record = wc.analyse_name(name, tick=0.005, half_spread=0.01)
    fields = ab.e3_fields(name, 0.005, 0.01, 0.0)
    assert fields["e3_ok"]
    assert fields["e3_lo"] == pytest.approx(record["lo"])
    assert fields["e3_hi"] == pytest.approx(record["hi"])


def test_run_design_smoke_and_restores_settings() -> None:
    original = (wc.TAU_PP_RANGE, wc.TAU_IV_PP)
    rows = ab.run_design(
        "per_name",
        replicates=2,
        stresses=(4.0,),
        universe_sizes=(10,),
        ticks=(0.005,),
        half_spreads=(0.25,),
    )
    assert {row["method"] for row in rows} == {"E0", "E2", "E3"}
    assert {row["metric"] for row in rows} == set(ab.METRICS)
    assert all(row["replicates"] <= 2 for row in rows)
    assert (wc.TAU_PP_RANGE, wc.TAU_IV_PP) == original
