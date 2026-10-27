"""The sweep's seed design matches the pre-registered design (addendum §A1.5)."""

from __future__ import annotations

from research.cpiv.measurement import sweep
from research.cpiv.measurement.sweep import BASE_SEED, DECLARED_SEEDS
from research.cpiv.measurement.verdict import MARKET_SPECIFICATIONS, REPLICATION_SEEDS


def _record_calls(monkeypatch, seeds: tuple[int, ...]) -> list[tuple[str, int]]:
    calls: list[tuple[str, int]] = []

    def fake(specification, seed):  # type: ignore[no-untyped-def]
        calls.append((specification.name, seed))
        return {"draw": specification.name, "seed": seed}

    monkeypatch.setattr(sweep, "_run_specification", fake)
    sweep.run_specification_sweep(seeds)
    return calls


def test_the_replication_seeds_agree_between_sweep_and_verdict() -> None:
    assert DECLARED_SEEDS[1:] == REPLICATION_SEEDS


def test_the_market_specifications_agree_between_sweep_and_verdict() -> None:
    assert [spec.name for spec in sweep.MARKET_SPECIFICATIONS] == list(
        MARKET_SPECIFICATIONS
    )


def test_replication_seeds_get_every_market_specification_and_no_protocol_variant(
    monkeypatch,
) -> None:
    calls = _record_calls(monkeypatch, REPLICATION_SEEDS)

    assert len(calls) == len(MARKET_SPECIFICATIONS) * len(REPLICATION_SEEDS)
    assert {name for name, _ in calls} == set(MARKET_SPECIFICATIONS)


def test_the_base_seed_also_gets_the_protocol_variants(monkeypatch) -> None:
    calls = _record_calls(monkeypatch, (BASE_SEED,))

    assert len(calls) == len(sweep.SPECIFICATIONS)
    assert all(seed == BASE_SEED for _, seed in calls)
