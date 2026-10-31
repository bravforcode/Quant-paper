"""The abstention frontier, tested against size-matched random subsets.

The protocol does not produce a second estimator: it *labels* pairs and
abstains on the rest. Its own-set error is therefore a selection effect, and a
reviewer is entitled to ask whether the certified subset is any better than an
arbitrary subset of the same size.

This module answers that question directly. For each declared tolerance it
compares the certified subset with two nulls of the same size:

* a *pair* null that draws pairs uniformly from the scored universe, and
* a *block* null that draws whole underlying-days, preserving the dependence
  inside a day, which is the dependence the study's own intervals respect.

Both nulls are Monte Carlo with a declared seed, and the reported p-value is
the standard add-one estimator. A small p-value means the abstention rule
selects a set that is genuinely easier to measure, not merely smaller.

The module works on plain mappings so that it stays independent of the study
module that feeds it.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FrontierPoint:
    """One row of the frontier: the certified set against its nulls."""

    tolerance_pp: float
    n_certified: int
    coverage: float
    mae_certified_pp: float | None
    abstained_mae_pp: float | None
    null_mean_pp: float | None
    null_sd_pp: float | None
    null_q05_pp: float | None
    null_q95_pp: float | None
    block_null_mean_pp: float | None
    p_value_pair_null: float | None
    p_value_block_null: float | None
    trials: int

    def to_dict(self) -> dict[str, object]:
        return {
            "tolerance_pp": self.tolerance_pp,
            "n_certified": self.n_certified,
            "coverage": self.coverage,
            "mae_certified_pp": self.mae_certified_pp,
            "abstained_mae_pp": self.abstained_mae_pp,
            "null_mean_pp": self.null_mean_pp,
            "null_sd_pp": self.null_sd_pp,
            "null_q05_pp": self.null_q05_pp,
            "null_q95_pp": self.null_q95_pp,
            "block_null_mean_pp": self.block_null_mean_pp,
            "p_value_pair_null": self.p_value_pair_null,
            "p_value_block_null": self.p_value_block_null,
            "trials": self.trials,
        }


def _mean_abs_error(
    values: np.ndarray, truth: np.ndarray, indices: Sequence[int]
) -> float:
    if not len(indices):
        return float("nan")
    picked = np.asarray(indices, dtype=int)
    return float(np.mean(np.abs(values[picked] - truth[picked])))


def _block_samples(
    blocks: Mapping[str, Sequence[int]],
    size: int,
    trials: int,
    rng: random.Random,
) -> list[list[int]]:
    """Draw whole blocks with replacement until the target size is reached.

    The final block of a draw may be taken in part, because the draw must
    match the certified subset exactly in size; every other block is whole.
    Members of a partially taken block are chosen at random, so the null
    does not systematically favour the earliest pairs of a day.
    """
    keys = list(blocks)
    if not keys:
        return []
    samples: list[list[int]] = []
    for _ in range(trials):
        chosen: list[int] = []
        while len(chosen) < size:
            key = keys[rng.randrange(len(keys))]
            members = blocks[key]
            if not members:
                continue
            take = min(size - len(chosen), len(members))
            if take < len(members):
                chosen.extend(rng.sample(list(members), take))
            else:
                chosen.extend(members)
        samples.append(chosen)
    return samples


def selection_frontier(
    *,
    displacement: Mapping[str, float],
    values: Mapping[str, float],
    truth: Mapping[str, float],
    blocks: Mapping[str, Sequence[str]],
    tolerances: Sequence[float],
    trials: int = 2000,
    seed: int = 20261022,
) -> list[FrontierPoint]:
    """Compare the certified subset with size-matched random subsets."""
    if trials < 1:
        raise ValueError("trials must be positive")
    universe_keys = sorted(set(values) & set(truth))
    value_array = np.asarray([values[key] for key in universe_keys], dtype=float)
    truth_array = np.asarray([truth[key] for key in universe_keys], dtype=float)
    position = {key: index for index, key in enumerate(universe_keys)}
    block_indices = {
        key: [position[pair_id] for pair_id in members if pair_id in position]
        for key, members in blocks.items()
    }
    block_indices = {key: members for key, members in block_indices.items() if members}
    rng = random.Random(seed)
    generator = np.random.default_rng(seed)
    points: list[FrontierPoint] = []
    for tolerance in tolerances:
        certified = [
            key
            for key in universe_keys
            if key in displacement and displacement[key] <= tolerance
        ]
        size = len(certified)
        coverage = size / len(universe_keys) if universe_keys else 0.0
        if size == 0:
            points.append(
                FrontierPoint(
                    tolerance_pp=tolerance,
                    n_certified=0,
                    coverage=coverage,
                    mae_certified_pp=None,
                    abstained_mae_pp=_mean_abs_error(
                        value_array, truth_array, list(range(len(universe_keys)))
                    ),
                    null_mean_pp=None,
                    null_sd_pp=None,
                    null_q05_pp=None,
                    null_q95_pp=None,
                    block_null_mean_pp=None,
                    p_value_pair_null=None,
                    p_value_block_null=None,
                    trials=trials,
                )
            )
            continue
        certified_indices = [position[key] for key in certified]
        mae_certified = _mean_abs_error(value_array, truth_array, certified_indices)
        abstained_indices = [
            index for index in range(len(universe_keys)) if index not in set(certified_indices)
        ]
        abstained_mae = _mean_abs_error(value_array, truth_array, abstained_indices)

        pair_null: list[float] = []
        for _ in range(trials):
            drawn = generator.choice(
                len(universe_keys), size=size, replace=False, shuffle=False
            )
            pair_null.append(_mean_abs_error(value_array, truth_array, drawn.tolist()))
        block_null: list[float] = []
        for sample in _block_samples(block_indices, size, trials, rng):
            block_null.append(_mean_abs_error(value_array, truth_array, sample))

        null_array = np.asarray(pair_null, dtype=float)
        block_array = np.asarray(block_null, dtype=float)
        points.append(
            FrontierPoint(
                tolerance_pp=tolerance,
                n_certified=size,
                coverage=coverage,
                mae_certified_pp=mae_certified,
                abstained_mae_pp=abstained_mae,
                null_mean_pp=float(np.mean(null_array)),
                null_sd_pp=float(np.std(null_array, ddof=1)) if trials > 1 else None,
                null_q05_pp=float(np.quantile(null_array, 0.05)),
                null_q95_pp=float(np.quantile(null_array, 0.95)),
                block_null_mean_pp=float(np.mean(block_array)),
                p_value_pair_null=_p_value(pair_null, mae_certified),
                p_value_block_null=_p_value(block_null, mae_certified),
                trials=trials,
            )
        )
    return points


def _p_value(null: Sequence[float], observed: float) -> float | None:
    """Add-one Monte Carlo p-value for the null being at least as good."""
    if not null:
        return None
    count = sum(1 for value in null if value <= observed)
    return (1.0 + count) / (len(null) + 1.0)
