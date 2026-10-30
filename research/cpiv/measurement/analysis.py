"""Baselines and stability metrics for the CPIV measurement comparison.

Stability is always reported twice: on each method's own eligible set, and on
the common set both methods can use. A gain that exists only on the own-set
comparison is a selection effect, not an improvement.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence

from research.cpiv.measurement.resolution import ResolutionOutcome
from research.cpiv.measurement.status import TerminalStatus

USABLE_TERMINALS = frozenset(
    {
        TerminalStatus.RESOLVED_WITHIN_TOLERANCE,
        TerminalStatus.IDENTIFIED_OUTSIDE_TOLERANCE,
    }
)


def is_usable(outcome: ResolutionOutcome) -> bool:
    return outcome.terminal in USABLE_TERMINALS and outcome.cpiv_mid_pp is not None


def raw_midpoint_values(
    outcomes: Sequence[ResolutionOutcome],
) -> dict[str, float]:
    """CPIV from midpoint IVs, with no filter beyond a finite root."""
    return {
        outcome.pair_id: outcome.cpiv_mid_pp
        for outcome in outcomes
        if outcome.cpiv_mid_pp is not None
    }


def bound_filtered_values(
    outcomes: Sequence[ResolutionOutcome],
) -> dict[str, float]:
    """CPIV after the conventional no-arbitrage/bound filter."""
    return {
        outcome.pair_id: outcome.cpiv_mid_pp
        for outcome in outcomes
        if outcome.cpiv_mid_pp is not None and outcome.mid_inside_bounds
    }


def protocol_values(outcomes: Sequence[ResolutionOutcome]) -> dict[str, float]:
    """CPIV on pairs the protocol certifies as identified."""
    values: dict[str, float] = {}
    for outcome in outcomes:
        if outcome.cpiv_mid_pp is not None and is_usable(outcome):
            values[outcome.pair_id] = outcome.cpiv_mid_pp
    return values


def parity_residual_values(
    outcomes: Sequence[ResolutionOutcome],
) -> dict[str, float]:
    """Parity residuals; algebraically dependent on CPIV under the same map."""
    values: dict[str, float] = {}
    for outcome in outcomes:
        if outcome.parity_residual is not None:
            values[outcome.pair_id] = outcome.parity_residual
    return values


def coverage(
    outcomes: Sequence[ResolutionOutcome],
    selector: Callable[[ResolutionOutcome], bool] = is_usable,
) -> float:
    if not outcomes:
        return 0.0
    return sum(1 for outcome in outcomes if selector(outcome)) / len(outcomes)


def sign_disagreement(
    first: Mapping[str, float], second: Mapping[str, float]
) -> float:
    """Share of common pairs with opposite, non-zero signs."""
    common = sorted(set(first) & set(second))
    if not common:
        return 0.0
    disagree = sum(
        1
        for key in common
        if first[key] * second[key] < 0.0
        and first[key] != 0.0
        and second[key] != 0.0
    )
    return disagree / len(common)


def _average_ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index
        while end + 1 < len(order) and values[order[end + 1]] == values[order[index]]:
            end += 1
        average = (index + end) / 2.0 + 1.0
        for position in range(index, end + 1):
            ranks[order[position]] = average
        index = end + 1
    return ranks


def spearman_pairs(first: Sequence[float], second: Sequence[float]) -> float | None:
    """Spearman correlation of two aligned sequences, ties averaged.

    Unlike :func:`spearman` this keeps multiplicities, which is what a block
    bootstrap needs: a block drawn twice contributes its pairs twice.
    """
    if len(first) != len(second) or len(first) < 2:
        return None
    left = _average_ranks(list(first))
    right = _average_ranks(list(second))
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    covariance = sum(
        (a - mean_left) * (b - mean_right) for a, b in zip(left, right, strict=True)
    )
    variance_left = sum((a - mean_left) ** 2 for a in left)
    variance_right = sum((b - mean_right) ** 2 for b in right)
    if variance_left == 0.0 or variance_right == 0.0:
        return None
    return covariance / math.sqrt(variance_left * variance_right)


def spearman(first: Mapping[str, float], second: Mapping[str, float]) -> float | None:
    """Spearman rank correlation on the common set, with average ranks for ties."""
    common = sorted(set(first) & set(second))
    if len(common) < 2:
        return None
    return spearman_pairs([first[key] for key in common], [second[key] for key in common])


def pairwise_inversion_rate(
    first: Mapping[str, float], second: Mapping[str, float]
) -> float:
    """Share of comparable unordered pairs whose order reverses."""
    common = sorted(set(first) & set(second))
    total = 0
    inversions = 0
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            left = first[common[i]] - first[common[j]]
            right = second[common[i]] - second[common[j]]
            if left == 0.0 or right == 0.0:
                continue
            total += 1
            if left * right < 0.0:
                inversions += 1
    return inversions / total if total else 0.0


def tail_turnover(
    first: Mapping[str, float], second: Mapping[str, float], fraction: float = 0.2
) -> float:
    """Share of top/bottom tail membership that changes between two rankings."""
    common = sorted(set(first) & set(second))
    size = max(1, int(round(fraction * len(common))))
    if len(common) < 2 * size:
        size = max(1, len(common) // 2)
    turnovers: list[float] = []
    for reverse in (False, True):
        left = sorted(common, key=lambda key: first[key], reverse=reverse)[:size]
        right = sorted(common, key=lambda key: second[key], reverse=reverse)[:size]
        turnovers.append(len(set(left) ^ set(right)) / (2 * size))
    return sum(turnovers) / len(turnovers)


def endpoint_ambiguity(outcomes: Sequence[ResolutionOutcome]) -> float:
    """Share of pairs whose CPIV interval contains zero (sign ambiguous)."""
    intervals = [
        (outcome.interval_low_pp, outcome.interval_high_pp)
        for outcome in outcomes
        if outcome.interval_low_pp is not None
        and outcome.interval_high_pp is not None
    ]
    if not intervals:
        return 0.0
    ambiguous = sum(1 for low, high in intervals if low <= 0.0 <= high)
    return ambiguous / len(intervals)


def input_sensitivity(
    base: Mapping[str, float], perturbed: Mapping[str, float]
) -> float | None:
    """Mean absolute CPIV change on the common set."""
    common = sorted(set(base) & set(perturbed))
    if not common:
        return None
    return sum(abs(base[key] - perturbed[key]) for key in common) / len(common)


def error_profile(
    values: Mapping[str, float],
    truth: Mapping[str, float],
    thresholds: Sequence[float] = (0.05, 0.10, 0.25, 1.00),
) -> dict[str, object]:
    """The distribution of the error against a known truth.

    A mean absolute error alone hides the shape of the distribution: a few
    pairs with a very large error can carry the mean while most pairs are
    measured well. The profile therefore reports quantiles of the absolute
    error and the share of pairs inside each declared tolerance.
    """
    common = sorted(set(values) & set(truth))
    if not common:
        return {"n": 0}
    errors = sorted(abs(values[key] - truth[key]) for key in common)
    signed = [values[key] - truth[key] for key in common]
    count = len(errors)
    profile: dict[str, object] = {
        "n": count,
        "mean_abs_error_pp": sum(errors) / count,
        "median_abs_error_pp": _quantile(errors, 0.50),
        "p75_abs_error_pp": _quantile(errors, 0.75),
        "p90_abs_error_pp": _quantile(errors, 0.90),
        "p95_abs_error_pp": _quantile(errors, 0.95),
        "p99_abs_error_pp": _quantile(errors, 0.99),
        "max_abs_error_pp": errors[-1],
        "mean_signed_error_pp": sum(signed) / count,
    }
    for threshold in thresholds:
        inside = sum(1 for error in errors if error <= threshold)
        profile[f"share_within_{threshold:.2f}_pp"] = inside / count
    return profile


def _quantile(sorted_values: Sequence[float], probability: float) -> float:
    """Linear-interpolated quantile of an already sorted sequence."""
    if not sorted_values:
        raise ValueError("quantile of an empty sequence")
    position = (len(sorted_values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return (
        sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight
    )


def compare(
    baseline: Mapping[str, float], protocol: Mapping[str, float]
) -> dict[str, object]:
    """Report the own-set and common-set comparison side by side."""
    common = sorted(set(baseline) & set(protocol))
    return {
        "own_set": {
            "baseline_n": len(baseline),
            "protocol_n": len(protocol),
        },
        "common_set": {
            "n": len(common),
            "spearman": spearman(baseline, protocol),
            "sign_disagreement": sign_disagreement(baseline, protocol),
            "pairwise_inversion_rate": pairwise_inversion_rate(baseline, protocol),
            "tail_turnover": tail_turnover(baseline, protocol),
        },
        "labels": {
            "parity_residual": "algebraically dependent; not independent validation",
        },
    }
