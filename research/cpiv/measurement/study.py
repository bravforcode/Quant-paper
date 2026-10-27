"""Ground-truth study for the CPIV measurement protocol.

The study runs the whole protocol on the synthetic market produced by
:mod:`research.cpiv.measurement.dgp`, where the true call-put implied
volatility spread is known before the quote exists. That makes three things
possible that a market sample cannot deliver:

* an accuracy measure against a known target, not only a stability measure;
* an explicit accounting of what each abstention avoided;
* a pre-registration instrument, because thresholds can be fixed on the
  benchmark before any licensed quote is read.

The study is a *benchmark*, not a substitute for market evidence. It contains
no market data and makes no claim about any real security.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

from research.cpiv import build_demo as bsm
from research.cpiv.measurement.analysis import (
    error_profile,
    input_sensitivity,
    pairwise_inversion_rate,
    spearman,
    spearman_pairs,
    tail_turnover,
)
from research.cpiv.measurement.bootstrap import block_bootstrap
from research.cpiv.measurement.calibration import compare_surfaces
from research.cpiv.measurement.dgp import (
    FIRST_SESSION,
    GeneratorConfig,
    generate_market,
)
from research.cpiv.measurement.frontier import selection_frontier
from research.cpiv.measurement.inversion import invert_leg
from research.cpiv.measurement.manifest import build_manifest, write_manifest
from research.cpiv.measurement.pairing import Contract, Quote, check_pair
from research.cpiv.measurement.quotes import QuotePair
from research.cpiv.measurement.resolution import ResolutionInput, resolve
from research.cpiv.measurement.status import (
    PairRecord,
    ReasonCode,
    Stage,
    TerminalStatus,
    funnel,
    reconcile,
)

HERE = Path(__file__).resolve().parent
RUN_CONFIG = HERE / "configs" / "study.yaml"
DEFAULT_OUTPUT = HERE / "outputs" / "study"
USABLE = (
    TerminalStatus.RESOLVED_WITHIN_TOLERANCE,
    TerminalStatus.IDENTIFIED_OUTSIDE_TOLERANCE,
)
METHODS = (
    "raw_midpoint",
    "bound_filtered",
    "protocol_identified",
    "protocol_certified",
)


@dataclass(frozen=True)
class StudySettings:
    """Declared settings of one study run."""

    tick: float = 0.01
    resolution_ticks: float = 1.0
    tolerances_pp: tuple[float, ...] = (0.05, 0.10, 0.25)
    primary_tolerance_pp: float = 0.10
    quote_sync_tolerance_seconds: float = 2.0
    bootstrap_resamples: int = 2000
    bootstrap_seed: int = 20261022
    confidence: float = 0.95
    sign_band_pp: float = 0.05
    primary_day_cut: int = 15
    tail_fraction: float = 0.2
    frontier_trials: int = 2000
    frontier_tolerances: tuple[float, ...] = (
        0.05, 0.075, 0.10, 0.15, 0.20, 0.25, 0.50
    )


@dataclass(frozen=True)
class StudyRow:
    """One attempted pair with its protocol outcome, baselines and truth."""

    pair_id: str
    underlying: str
    day: str
    block: str
    day_index: int
    strike: float
    spot: float
    days: int
    log_moneyness: float
    true_cpiv_pp: float | None
    terminal: TerminalStatus
    reason: ReasonCode
    failed_stage: Stage | None
    protocol_cpiv_pp: float | None
    protocol_certified_cpiv_pp: float | None
    raw_cpiv_pp: float | None
    bound_cpiv_pp: float | None
    interval_low_pp: float | None
    interval_high_pp: float | None
    displacement_pp: float | None
    parity_residual: float | None
    half_spread_ticks: int
    wide_session: bool
    defect: str

    def to_record(self) -> PairRecord:
        return PairRecord(
            pair_id=self.pair_id,
            terminal=self.terminal,
            failed_stage=self.failed_stage,
            reason=self.reason,
        )


def _leg_iv(
    option_type: str, price: float, pair: QuotePair
) -> tuple[float | None, bool]:
    """Invert one leg; return the root and whether the midpoint is inside bounds."""
    outcome = invert_leg(
        option_type, price, pair.spot, pair.strike, pair.days, pair.rate,
        pair.dividend_yield,
    )
    if not outcome.ok or outcome.iv is None:
        return None, False
    lower, upper = bsm.price_bounds(
        option_type, pair.spot, pair.strike, pair.days, pair.rate, pair.dividend_yield
    )
    inside = min(price - lower, upper - price) > 1e-10
    return outcome.iv, inside


def _raw_cpiv(pair: QuotePair) -> tuple[float | None, bool]:
    call_iv, call_inside = _leg_iv("call", pair.call_mid, pair)
    put_iv, put_inside = _leg_iv("put", pair.put_mid, pair)
    if call_iv is None or put_iv is None:
        return None, False
    return 100.0 * (call_iv - put_iv), call_inside and put_inside


def run_protocol(
    pairs: Sequence[QuotePair], settings: StudySettings
) -> list[StudyRow]:
    """Run the declared protocol over every attempted pair."""
    rows: list[StudyRow] = []
    for pair in pairs:
        call_quote = Quote(pair.call_bid, pair.call_ask, pair.call_timestamp_utc)
        put_quote = Quote(pair.put_bid, pair.put_ask, pair.put_timestamp_utc)
        expiry = pair.expiry or (FIRST_SESSION + timedelta(days=pair.days)).date()
        call_contract = Contract(
            underlying=pair.underlying, strike=pair.strike, expiry=expiry,
            multiplier=pair.multiplier, exercise_style=pair.exercise_style,
            settlement=pair.settlement,
        )
        put_contract = Contract(
            underlying=pair.underlying, strike=pair.put_strike, expiry=expiry,
            multiplier=(
                pair.put_multiplier
                if pair.put_multiplier is not None
                else pair.multiplier
            ),
            exercise_style=pair.put_exercise_style or pair.exercise_style,
            settlement=pair.put_settlement or pair.settlement,
        )
        check = check_pair(
            call_quote, put_quote, pair.spot, pair.spot_timestamp_utc,
            call_contract, put_contract, settings.quote_sync_tolerance_seconds,
        )
        raw_cpiv, inside = _raw_cpiv(pair)
        bound_cpiv = raw_cpiv if raw_cpiv is not None and inside else None
        if not check.ok:
            assert check.terminal is not None
            rows.append(
                StudyRow(
                    pair_id=pair.pair_id,
                    underlying=pair.underlying,
                    day=pair.day,
                    block=pair.block,
                    day_index=pair.day_index,
                    strike=pair.strike,
                    spot=pair.spot,
                    days=pair.days,
                    log_moneyness=pair.log_moneyness,
                    true_cpiv_pp=pair.true_cpiv_pp,
                    terminal=check.terminal,
                    reason=check.reason,
                    failed_stage=check.failed_stage,
                    protocol_cpiv_pp=None,
                    protocol_certified_cpiv_pp=None,
                    raw_cpiv_pp=raw_cpiv,
                    bound_cpiv_pp=bound_cpiv,
                    interval_low_pp=None,
                    interval_high_pp=None,
                    displacement_pp=None,
                    parity_residual=None,
                    half_spread_ticks=pair.half_spread_ticks,
                    wide_session=pair.wide_session,
                    defect=pair.defect,
                )
            )
            continue
        spec = ResolutionInput(
            pair_id=pair.pair_id,
            call_mid=pair.call_mid,
            put_mid=pair.put_mid,
            call_bid=pair.call_bid,
            call_ask=pair.call_ask,
            put_bid=pair.put_bid,
            put_ask=pair.put_ask,
            spot=pair.spot,
            strike=pair.strike,
            days=pair.days,
            rate=pair.rate,
            dividend_yield=pair.dividend_yield,
            tick=settings.tick,
            resolution_ticks=settings.resolution_ticks,
            tolerance_pp=settings.primary_tolerance_pp,
        )
        outcome = resolve(spec)
        usable = outcome.terminal in USABLE
        rows.append(
            StudyRow(
                pair_id=pair.pair_id,
                underlying=pair.underlying,
                day=pair.day,
                block=pair.block,
                day_index=pair.day_index,
                strike=pair.strike,
                spot=pair.spot,
                days=pair.days,
                log_moneyness=pair.log_moneyness,
                true_cpiv_pp=pair.true_cpiv_pp,
                terminal=outcome.terminal,
                reason=outcome.reason,
                failed_stage=outcome.failed_stage,
                protocol_cpiv_pp=outcome.cpiv_mid_pp if usable else None,
                protocol_certified_cpiv_pp=(
                    outcome.cpiv_mid_pp
                    if outcome.terminal is TerminalStatus.RESOLVED_WITHIN_TOLERANCE
                    else None
                ),
                raw_cpiv_pp=raw_cpiv,
                bound_cpiv_pp=bound_cpiv,
                interval_low_pp=outcome.interval_low_pp,
                interval_high_pp=outcome.interval_high_pp,
                displacement_pp=outcome.displacement_pp,
                parity_residual=outcome.parity_residual,
                half_spread_ticks=pair.half_spread_ticks,
                wide_session=pair.wide_session,
                defect=pair.defect,
            )
        )
    return rows


# --- value maps and elementary accuracy measures -----------------------------


def method_values(rows: Sequence[StudyRow], method: str) -> dict[str, float]:
    if method == "raw_midpoint":
        return {row.pair_id: row.raw_cpiv_pp for row in rows if row.raw_cpiv_pp is not None}
    if method == "bound_filtered":
        return {
            row.pair_id: row.bound_cpiv_pp
            for row in rows
            if row.bound_cpiv_pp is not None
        }
    if method == "protocol_identified":
        return {
            row.pair_id: row.protocol_cpiv_pp
            for row in rows
            if row.protocol_cpiv_pp is not None
        }
    if method == "protocol_certified":
        return {
            row.pair_id: row.protocol_certified_cpiv_pp
            for row in rows
            if row.protocol_certified_cpiv_pp is not None
        }
    raise ValueError(f"unknown method: {method}")


def truth_values(rows: Sequence[StudyRow]) -> dict[str, float]:
    return {
        row.pair_id: row.true_cpiv_pp
        for row in rows
        if row.true_cpiv_pp is not None
    }


def mean_abs_error(
    values: Mapping[str, float], truth: Mapping[str, float]
) -> float | None:
    """Mean absolute error against the known truth on the common set."""
    common = sorted(set(values) & set(truth))
    if not common:
        return None
    return sum(abs(values[key] - truth[key]) for key in common) / len(common)


def own_set_error_reduction(rows: Sequence[StudyRow]) -> float | None:
    """Own-set error reduction: raw-midpoint error minus certified error.

    Each term is computed on that method's own eligible set, so the
    difference is a *selection effect*: it is what the abstention rule buys
    by labelling pairs, not an improvement in the estimator. On the common
    set the two methods are numerically identical, so the common-set
    difference is zero by construction and carries no information.
    """
    raw_error = mean_abs_error(
        method_values(rows, "raw_midpoint"), truth_values(rows)
    )
    certified_error = mean_abs_error(
        method_values(rows, "protocol_certified"), truth_values(rows)
    )
    if raw_error is None or certified_error is None:
        return None
    return raw_error - certified_error


def bias(values: Mapping[str, float], truth: Mapping[str, float]) -> float | None:
    """Mean signed error against the known truth on the common set."""
    common = sorted(set(values) & set(truth))
    if not common:
        return None
    return sum(values[key] - truth[key] for key in common) / len(common)


def sign_disagreement_vs_truth(
    values: Mapping[str, float], truth: Mapping[str, float], band: float
) -> float | None:
    """Sign disagreement against truth, restricted to pairs the truth resolves."""
    common = [
        key
        for key in sorted(set(values) & set(truth))
        if abs(truth[key]) >= band
    ]
    if not common:
        return None
    disagree = sum(
        1
        for key in common
        if values[key] * truth[key] < 0.0 and values[key] != 0.0 and truth[key] != 0.0
    )
    return disagree / len(common)


def _own_set_metrics(
    rows: Sequence[StudyRow], method: str, band: float
) -> dict[str, object]:
    values = method_values(rows, method)
    truth = truth_values(rows)
    attempted = len(rows)
    return {
        "n": len(values),
        "coverage": len(values) / attempted if attempted else 0.0,
        "mae_vs_truth_pp": mean_abs_error(values, truth),
        "bias_vs_truth_pp": bias(values, truth),
        "sign_disagreement_vs_truth": sign_disagreement_vs_truth(values, truth, band),
        "spearman_vs_truth": spearman(values, truth),
    }


def _common_set_metrics(
    rows: Sequence[StudyRow], baseline: str, method: str, band: float, tail: float
) -> dict[str, object]:
    base_values = method_values(rows, baseline)
    method_map = method_values(rows, method)
    truth = truth_values(rows)
    common = sorted(set(base_values) & set(method_map))
    base_common = {key: base_values[key] for key in common}
    method_common = {key: method_map[key] for key in common}
    truth_common = {key: truth[key] for key in common if key in truth}
    mae_base = mean_abs_error(base_common, truth_common)
    mae_method = mean_abs_error(method_common, truth_common)
    return {
        "n": len(common),
        "mae_baseline_pp": mae_base,
        "mae_method_pp": mae_method,
        "error_reduction_pp": (
            mae_base - mae_method
            if mae_base is not None and mae_method is not None
            else None
        ),
        "spearman_baseline_vs_method": spearman(base_common, method_common),
        "spearman_baseline_vs_truth": spearman(base_common, truth_common),
        "spearman_method_vs_truth": spearman(method_common, truth_common),
        "sign_disagreement_baseline_vs_method": _pair_sign_disagreement(
            base_common, method_common
        ),
        "sign_disagreement_baseline_vs_truth": sign_disagreement_vs_truth(
            base_common, truth_common, band
        ),
        "sign_disagreement_method_vs_truth": sign_disagreement_vs_truth(
            method_common, truth_common, band
        ),
        "pairwise_inversion_baseline_vs_method": pairwise_inversion_rate(
            base_common, method_common
        ),
        "pairwise_inversion_baseline_vs_truth": pairwise_inversion_rate(
            base_common, truth_common
        ),
        "pairwise_inversion_method_vs_truth": pairwise_inversion_rate(
            method_common, truth_common
        ),
        "tail_turnover_baseline_vs_method": tail_turnover(
            base_common, method_common, tail
        ),
        "tail_turnover_baseline_vs_truth": tail_turnover(
            base_common, truth_common, tail
        ),
        "tail_turnover_method_vs_truth": tail_turnover(
            method_common, truth_common, tail
        ),
    }


def _pair_sign_disagreement(
    first: Mapping[str, float], second: Mapping[str, float]
) -> float | None:
    common = sorted(set(first) & set(second))
    if not common:
        return None
    disagree = sum(
        1
        for key in common
        if first[key] * second[key] < 0.0
        and first[key] != 0.0
        and second[key] != 0.0
    )
    return disagree / len(common)


def _abstained_metrics(rows: Sequence[StudyRow], band: float) -> dict[str, object]:
    """What the abstentions cost and what they avoided."""
    abstained = [row for row in rows if row.protocol_certified_cpiv_pp is None]
    values = method_values(abstained, "raw_midpoint")
    truth = truth_values(abstained)
    terminal_counts: dict[str, int] = {}
    for row in abstained:
        terminal_counts[row.terminal.value] = terminal_counts.get(row.terminal.value, 0) + 1
    return {
        "n": len(abstained),
        "share_of_attempted": len(abstained) / len(rows) if rows else 0.0,
        "raw_mae_on_abstained_pp": mean_abs_error(values, truth),
        "raw_sign_disagreement_vs_truth": sign_disagreement_vs_truth(
            values, truth, band
        ),
        "terminal_counts": terminal_counts,
    }


# --- strata -----------------------------------------------------------------


def _bucket_moneyness(row: StudyRow) -> str:
    return f"K/S={row.strike / row.spot:.2f}"


def _bucket_maturity(row: StudyRow) -> str:
    return f"{row.days}d"


def _bucket_spread(row: StudyRow) -> str:
    if row.wide_session:
        return "wide session"
    return f"{row.half_spread_ticks} tick half-spread"


def _bucket_truth(row: StudyRow) -> str:
    if row.true_cpiv_pp is None:
        return "undefined"
    magnitude = abs(row.true_cpiv_pp)
    if magnitude < 0.1:
        return "<0.1 pp"
    if magnitude < 1.0:
        return "0.1-1 pp"
    return ">=1 pp"


def _strata(
    rows: Sequence[StudyRow],
    bucket: Callable[[StudyRow], str],
    band: float,
) -> list[dict[str, object]]:
    groups: dict[str, list[StudyRow]] = {}
    for row in rows:
        groups.setdefault(bucket(row), []).append(row)
    output: list[dict[str, object]] = []
    for key in sorted(groups):
        group = groups[key]
        raw = method_values(group, "raw_midpoint")
        protocol = method_values(group, "protocol_certified")
        truth = truth_values(group)
        abstained = [row for row in group if row.protocol_certified_cpiv_pp is None]
        abstained_raw = method_values(abstained, "raw_midpoint")
        output.append(
            {
                "bucket": key,
                "n": len(group),
                "coverage_protocol": len(protocol) / len(group) if group else 0.0,
                "coverage_raw": len(raw) / len(group) if group else 0.0,
                "mae_raw_pp": mean_abs_error(raw, truth),
                "mae_protocol_pp": mean_abs_error(protocol, truth),
                "raw_mae_on_abstained_pp": mean_abs_error(
                    abstained_raw, truth_values(abstained)
                ),
                "sign_disagreement_raw_vs_truth": sign_disagreement_vs_truth(
                    raw, truth, band
                ),
                "sign_disagreement_protocol_vs_truth": sign_disagreement_vs_truth(
                    protocol, truth, band
                ),
            }
        )
    return output


# --- perturbations ----------------------------------------------------------


def _widen(pair: QuotePair, settings: StudySettings) -> QuotePair:
    half = settings.tick / 2.0
    return replace(
        pair,
        call_bid=pair.call_bid - half,
        call_ask=pair.call_ask + half,
        put_bid=pair.put_bid - half,
        put_ask=pair.put_ask + half,
    )


def _spot_shift(pair: QuotePair, settings: StudySettings) -> QuotePair:
    return replace(pair, spot=pair.spot * 1.0001)


def _rate_shift(pair: QuotePair, settings: StudySettings) -> QuotePair:
    return replace(pair, rate=pair.rate + 0.0005)


def _stale_spot(pair: QuotePair, settings: StudySettings) -> QuotePair:
    return replace(
        pair, spot_timestamp_utc=pair.spot_timestamp_utc - timedelta(seconds=3.0)
    )


@dataclass(frozen=True)
class Perturbation:
    """One declared input perturbation of RQ2."""

    name: str
    description: str
    transform: Callable[[QuotePair, StudySettings], QuotePair]
    settings: Callable[[StudySettings], StudySettings] | None = None


PERTURBATIONS: tuple[Perturbation, ...] = (
    Perturbation(
        "endpoint_outward",
        "Every quote widened by half a tick on both sides.",
        _widen,
    ),
    Perturbation(
        "spot_shift_1bp",
        "Underlying price used for inversion shifted up by one basis point.",
        _spot_shift,
    ),
    Perturbation(
        "rate_shift_5bp",
        "Continuously compounded rate shifted up by five basis points.",
        _rate_shift,
    ),
    Perturbation(
        "stale_spot_3s",
        "Underlying timestamp moved three seconds behind the quote timestamps.",
        _stale_spot,
    ),
    Perturbation(
        "half_tick_resolution",
        "Resolution scale halved from one tick to half a tick.",
        lambda pair, settings: pair,
        lambda settings: replace(settings, resolution_ticks=0.5),
    ),
    Perturbation(
        "relaxed_sync_5s",
        "Quote and spot synchronisation tolerance relaxed to five seconds.",
        lambda pair, settings: pair,
        lambda settings: replace(settings, quote_sync_tolerance_seconds=5.0),
    ),
)


def perturbation_report(
    pairs: Sequence[QuotePair],
    settings: StudySettings,
    base_rows: Sequence[StudyRow],
) -> list[dict[str, object]]:
    base_protocol = method_values(base_rows, "protocol_certified")
    base_coverage = len(base_protocol) / len(base_rows) if base_rows else 0.0
    report: list[dict[str, object]] = []
    for perturbation in PERTURBATIONS:
        run_settings = settings
        if perturbation.settings is not None:
            run_settings = perturbation.settings(settings)
        transformed = [
            perturbation.transform(pair, run_settings) for pair in pairs
        ]
        rows = run_protocol(transformed, run_settings)
        values = method_values(rows, "protocol_certified")
        raw_values = method_values(rows, "raw_midpoint")
        truth = truth_values(rows)
        coverage = len(values) / len(rows) if rows else 0.0
        report.append(
            {
                "name": perturbation.name,
                "description": perturbation.description,
                "n": len(rows),
                "coverage_protocol": coverage,
                "coverage_protocol_change": coverage - base_coverage,
                "mean_abs_cpiv_change_vs_base_pp": input_sensitivity(base_protocol, values),
                "spearman_vs_base_run": spearman(base_protocol, values),
                "mae_vs_truth_pp": mean_abs_error(values, truth),
                "raw_mae_vs_truth_pp": mean_abs_error(raw_values, truth),
            }
        )
    return report


# --- inference --------------------------------------------------------------


def _block_index(rows: Sequence[StudyRow]) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    for row in rows:
        blocks.setdefault(row.block, []).append(row.pair_id)
    return blocks


def _row_index(rows: Sequence[StudyRow]) -> dict[str, StudyRow]:
    return {row.pair_id: row for row in rows}


def _sample_rows(
    sample: Sequence[str], index: Mapping[str, StudyRow]
) -> list[StudyRow]:
    """Rows for a resampled block list, multiplicities preserved."""
    return [index[pair_id] for pair_id in sample]


def _method_value(row: StudyRow, method: str) -> float | None:
    if method == "raw_midpoint":
        return row.raw_cpiv_pp
    if method == "bound_filtered":
        return row.bound_cpiv_pp
    if method == "protocol_identified":
        return row.protocol_cpiv_pp
    if method == "protocol_certified":
        return row.protocol_certified_cpiv_pp
    raise ValueError(f"unknown method: {method}")


def _aligned(
    rows: Sequence[StudyRow], baseline: str, method: str
) -> list[tuple[float, float, float | None]]:
    """Aligned (baseline, method, truth) triples on the common set, in row order."""
    triples: list[tuple[float, float, float | None]] = []
    for row in rows:
        left = _method_value(row, baseline)
        right = _method_value(row, method)
        if left is None or right is None:
            continue
        triples.append((left, right, row.true_cpiv_pp))
    return triples


def _inference(
    rows: Sequence[StudyRow], settings: StudySettings
) -> dict[str, object]:
    blocks = _block_index(rows)
    index = _row_index(rows)
    band = settings.sign_band_pp

    def coverage_statistic(sample: Sequence[str]) -> float | None:
        subset = _sample_rows(sample, index)
        if not subset:
            return None
        values = [_method_value(row, "protocol_certified") for row in subset]
        return sum(1 for value in values if value is not None) / len(values)

    def error_reduction(sample: Sequence[str]) -> float | None:
        subset = _sample_rows(sample, index)
        rows = [
            (base, method, truth)
            for base, method, truth in _aligned(
                subset, "raw_midpoint", "protocol_certified"
            )
            if truth is not None
        ]
        if not rows:
            return None
        base_error = sum(abs(base - truth) for base, _, truth in rows) / len(rows)
        method_error = sum(abs(method - truth) for _, method, truth in rows) / len(rows)
        return base_error - method_error

    def error_avoided(sample: Sequence[str]) -> float | None:
        subset = [
            row
            for row in _sample_rows(sample, index)
            if _method_value(row, "protocol_certified") is None
        ]
        pairs = [
            (value, row.true_cpiv_pp)
            for row in subset
            for value in [_method_value(row, "raw_midpoint")]
            if value is not None and row.true_cpiv_pp is not None
        ]
        if not pairs:
            return None
        return sum(abs(value - truth) for value, truth in pairs) / len(pairs)

    def truth_spearman(sample: Sequence[str]) -> float | None:
        subset = _sample_rows(sample, index)
        rows = [
            (base, method, truth)
            for base, method, truth in _aligned(
                subset, "raw_midpoint", "protocol_certified"
            )
            if truth is not None
        ]
        if len(rows) < 3:
            return None
        left = spearman_pairs([base for base, _, _ in rows], [t for _, _, t in rows])
        right = spearman_pairs([method for _, method, _ in rows], [t for _, _, t in rows])
        if left is None or right is None:
            return None
        return right - left

    def sign_gain(sample: Sequence[str]) -> float | None:
        subset = _sample_rows(sample, index)
        rows = [
            (base, method, truth)
            for base, method, truth in _aligned(
                subset, "raw_midpoint", "protocol_certified"
            )
            if truth is not None and abs(truth) >= band
        ]
        if not rows:
            return None
        base = sum(
            1
            for left, _, truth in rows
            if left * truth < 0.0 and left != 0.0 and truth != 0.0
        ) / len(rows)
        method = sum(
            1
            for _, right, truth in rows
            if right * truth < 0.0 and right != 0.0 and truth != 0.0
        ) / len(rows)
        return base - method

    def run(statistic: Callable[[Sequence[str]], float | None]) -> dict[str, object]:
        return block_bootstrap(
            blocks,
            statistic,
            resamples=settings.bootstrap_resamples,
            seed=settings.bootstrap_seed,
            confidence=settings.confidence,
            unit="underlying-day",
        ).to_dict()

    return {
        "unit": "underlying-day",
        "blocks": len(blocks),
        "resamples": settings.bootstrap_resamples,
        "seed": settings.bootstrap_seed,
        "coverage_protocol": run(coverage_statistic),
        "error_reduction_common_set_pp": run(error_reduction),
        "error_avoided_by_abstention_pp": run(error_avoided),
        "delta_spearman_vs_truth": run(truth_spearman),
        "sign_disagreement_reduction_vs_truth": run(sign_gain),
        "note": (
            "The protocol does not re-estimate CPIV; it labels and abstains. "
            "The three difference statistics are therefore exactly zero on the "
            "common set, where the certified value is the midpoint value. The "
            "informative quantities are the coverage, the error avoided by "
            "abstention, and the own-set comparison."
        ),
    }


# --- report -----------------------------------------------------------------


def _truth_summary(rows: Sequence[StudyRow]) -> dict[str, object]:
    values = sorted(row.true_cpiv_pp for row in rows if row.true_cpiv_pp is not None)
    by_moneyness: list[dict[str, object]] = []
    groups: dict[str, list[float]] = {}
    for row in rows:
        if row.true_cpiv_pp is None:
            continue
        key = f"K/S={row.strike / row.spot:.2f}"
        groups.setdefault(key, []).append(row.true_cpiv_pp)
    for key in sorted(groups):
        group = groups[key]
        by_moneyness.append(
            {
                "bucket": key,
                "n": len(group),
                "median_true_cpiv_pp": sorted(group)[len(group) // 2],
                "min_true_cpiv_pp": min(group),
                "max_true_cpiv_pp": max(group),
            }
        )
    return {
        "n_defined": len(values),
        "n_undefined": len(rows) - len(values),
        "median_true_cpiv_pp": values[len(values) // 2] if values else None,
        "min_true_cpiv_pp": values[0] if values else None,
        "max_true_cpiv_pp": values[-1] if values else None,
        "by_moneyness": by_moneyness,
    }


def _replication(
    rows: Sequence[StudyRow], settings: StudySettings
) -> dict[str, object]:
    primary = [row for row in rows if row.day_index < settings.primary_day_cut]
    holdout = [row for row in rows if row.day_index >= settings.primary_day_cut]
    summary: dict[str, object] = {}
    gains: dict[str, float | None] = {}
    common_gains: dict[str, float | None] = {}
    coverages: dict[str, float | None] = {}
    for name, subset in (("primary", primary), ("holdout", holdout)):
        own_set = {
            method: _own_set_metrics(subset, method, settings.sign_band_pp)
            for method in METHODS
        }
        common = _common_set_metrics(
            subset, "raw_midpoint", "protocol_certified", settings.sign_band_pp,
            settings.tail_fraction,
        )
        summary[name] = {
            "n": len(subset),
            "own_set": own_set,
            "common_set_raw_vs_protocol": common,
        }
        gain = own_set_error_reduction(subset)
        common_gain = common["error_reduction_pp"]
        coverage = own_set["protocol_certified"]["coverage"]
        gains[name] = gain if isinstance(gain, float) else None
        common_gains[name] = common_gain if isinstance(common_gain, float) else None
        coverages[name] = coverage if isinstance(coverage, float) else None
    primary_gain = gains["primary"]
    holdout_gain = gains["holdout"]
    agrees = None
    if primary_gain is not None and holdout_gain is not None:
        agrees = (primary_gain > 0.0) == (holdout_gain > 0.0)
    return {
        "primary_day_cut": settings.primary_day_cut,
        "periods": summary,
        "error_reduction_sign_agrees": agrees,
        "own_set_error_reduction_primary_pp": gains["primary"],
        "own_set_error_reduction_holdout_pp": gains["holdout"],
        "common_set_error_reduction_primary_pp": common_gains["primary"],
        "common_set_error_reduction_holdout_pp": common_gains["holdout"],
        "coverage_primary": coverages["primary"],
        "coverage_holdout": coverages["holdout"],
        "error_reduction_note": (
            "The own-set error reduction is the selection effect the "
            "abstention rule buys; the common-set difference is zero by "
            "construction, because the certified value is the midpoint value "
            "of the same pair."
        ),
    }


def _displacement(row: StudyRow) -> float:
    """The worst-direction IV displacement, or infinity when it is undefined."""
    value = row.displacement_pp
    return value if value is not None else float("inf")


def _coverage_by_tolerance(
    rows: Sequence[StudyRow], tolerances: Sequence[float]
) -> list[dict[str, object]]:
    """Coverage of the declared tolerance grid, with explicit denominators."""
    identified = [row for row in rows if row.displacement_pp is not None]
    output: list[dict[str, object]] = []
    for tolerance in tolerances:
        resolved = sum(1 for row in identified if _displacement(row) <= tolerance)
        output.append(
            {
                "tolerance_pp": tolerance,
                "resolved": resolved,
                "coverage_of_attempted": resolved / len(rows) if rows else 0.0,
                "coverage_of_identified": (
                    resolved / len(identified) if identified else 0.0
                ),
            }
        )
    return output


def _frontier_rows(
    rows: Sequence[StudyRow], settings: StudySettings
) -> list[dict[str, object]]:
    """The abstention frontier against size-matched random subsets."""
    displacement = {
        row.pair_id: row.displacement_pp
        for row in rows
        if row.displacement_pp is not None
    }
    points = selection_frontier(
        displacement=displacement,
        values=method_values(rows, "raw_midpoint"),
        truth=truth_values(rows),
        blocks=_block_index(rows),
        tolerances=settings.frontier_tolerances,
        trials=settings.frontier_trials,
        seed=settings.bootstrap_seed,
    )
    return [point.to_dict() for point in points]


def study_report(
    pairs: Sequence[QuotePair],
    settings: StudySettings,
    config: GeneratorConfig,
) -> dict[str, object]:
    """Run the study and return every reported quantity."""
    rows = run_protocol(pairs, settings)
    records = [row.to_record() for row in rows]
    reconciliation = reconcile(records, attempted=len(rows))
    funnel_rows = [
        {
            "stage": row.stage.value,
            "count": row.count,
            "share_of_attempted": row.share_of_attempted,
            "share_of_prior": row.share_of_prior,
            "dominant_rejection_reason": row.dominant_rejection_reason,
        }
        for row in funnel(records, attempted=len(rows))
    ]
    band = settings.sign_band_pp
    own_set = {method: _own_set_metrics(rows, method, band) for method in METHODS}
    common_set = {
        f"{baseline}_vs_{method}": _common_set_metrics(
            rows, baseline, method, band, settings.tail_fraction
        )
        for baseline in ("raw_midpoint", "bound_filtered")
        for method in ("protocol_identified", "protocol_certified")
    }
    common_set["raw_midpoint_vs_bound_filtered"] = _common_set_metrics(
        rows, "raw_midpoint", "bound_filtered", band, settings.tail_fraction
    )
    log_moneyness = {row.pair_id: row.log_moneyness for row in rows}
    slice_key = {row.pair_id: f"{row.days}d" for row in rows}
    secondary = compare_surfaces(
        method_values(rows, "raw_midpoint"),
        method_values(rows, "protocol_certified"),
        log_moneyness,
        slice_key,
    )
    return {
        "status": "synthetic_ground_truth_study_only",
        "market_data_used": False,
        "network_access_used": False,
        "generator": {
            "seed": config.seed,
            "underlyings": list(config.underlyings),
            "trading_days": config.trading_days,
            "expiries": list(config.expiries),
            "strike_fractions": list(config.strike_fractions),
            "rate": config.rate,
            "dividend_yield": config.dividend_yield,
            "base_vol": config.base_vol,
            "tick": config.tick,
            "tree_steps": config.tree_steps,
        },
        "settings": {
            "tolerances_pp": list(settings.tolerances_pp),
            "primary_tolerance_pp": settings.primary_tolerance_pp,
            "resolution_ticks": settings.resolution_ticks,
            "quote_sync_tolerance_seconds": settings.quote_sync_tolerance_seconds,
            "sign_band_pp": settings.sign_band_pp,
            "frontier_tolerances_pp": list(settings.frontier_tolerances),
            "frontier_trials": settings.frontier_trials,
        },
        "attempted": len(rows),
        "reconciliation": reconciliation,
        "funnel": funnel_rows,
        "truth": _truth_summary(rows),
        "coverage_by_tolerance": _coverage_by_tolerance(rows, settings.tolerances_pp),
        "own_set": own_set,
        "error_profile": {
            method: error_profile(method_values(rows, method), truth_values(rows))
            for method in METHODS
        },
        "selection_frontier": _frontier_rows(rows, settings),
        "common_set": common_set,
        "common_set_note": (
            "The certified value is the midpoint CPIV of the same pair, so on "
            "the common set the protocol and the raw midpoint are numerically "
            "identical. Every own-set difference is a selection effect, and "
            "every common-set difference is zero by construction. The protocol "
            "is a labelling and abstention device, not a second estimator."
        ),
        "frontier_note": (
            "The selection frontier tests whether the abstention rule selects "
            "a set that is genuinely easier to measure. For each tolerance it "
            "compares the certified subset with two nulls of the same size: "
            "pairs drawn uniformly, and whole underlying-days drawn with "
            "replacement. The p-values are add-one Monte Carlo estimates over "
            "the declared number of trials."
        ),
        "abstained": _abstained_metrics(rows, band),
        "strata": {
            "moneyness": _strata(rows, _bucket_moneyness, band),
            "maturity": _strata(rows, _bucket_maturity, band),
            "spread": _strata(rows, _bucket_spread, band),
            "truth_magnitude": _strata(rows, _bucket_truth, band),
        },
        "perturbations": perturbation_report(pairs, settings, rows),
        "inference": _inference(rows, settings),
        "replication": _replication(rows, settings),
        "secondary_outcome": secondary,
        "warning": (
            "Synthetic benchmark with a known truth. It is not a market estimate, "
            "not a confidence statement about any real security, and not evidence "
            "of trading profitability."
        ),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_funnel_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "| Stage | Count | Share of attempted | Share of prior | Dominant reason |",
        "|:--|--:|--:|--:|:--|",
    ]
    for row in rows:
        reason = row["dominant_rejection_reason"] or "—"
        lines.append(
            f"| {row['stage']} | {row['count']} | "
            f"{float(row['share_of_attempted']):.3f} | "
            f"{float(row['share_of_prior']):.3f} | {reason} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_study(
    config: GeneratorConfig, settings: StudySettings
) -> tuple[dict[str, object], list[QuotePair], dict[str, int]]:
    pairs, counts = generate_market(config)
    report = study_report(pairs, settings, config)
    report["defect_counts"] = counts
    return report, pairs, counts


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--resamples", type=int, default=2000)
    args = parser.parse_args(argv)
    config = GeneratorConfig()
    settings = StudySettings(bootstrap_resamples=args.resamples)
    report, _pairs, _counts = run_study(config, settings)
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "study_summary.json"
    summary_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    funnel_rows = cast(list[dict[str, Any]], report["funnel"])
    strata_block = cast(dict[str, list[dict[str, Any]]], report["strata"])
    perturbation_rows = cast(list[dict[str, Any]], report["perturbations"])
    reconciliation = cast(dict[str, Any], report["reconciliation"])
    _write_csv(output_dir / "funnel.csv", funnel_rows)
    _write_funnel_markdown(output_dir / "funnel.md", funnel_rows)
    strata_rows: list[dict[str, Any]] = []
    for family, rows in strata_block.items():
        for row in rows:
            strata_rows.append({"family": family, **row})
    _write_csv(output_dir / "strata.csv", strata_rows)
    _write_csv(output_dir / "perturbations.csv", perturbation_rows)
    manifest = build_manifest(
        config_path=RUN_CONFIG,
        raw_paths=(RUN_CONFIG,),
        environment_path=HERE.parents[2] / "uv.lock",
        seed=config.seed,
        outputs=(summary_path, output_dir / "funnel.csv", output_dir / "strata.csv"),
        licence_mode="synthetic-no-market-data",
        status_counts=cast(dict[str, int], reconciliation["terminal_counts"]),
        repo_root=HERE.parents[2],
    )
    write_manifest(output_dir / "manifest.json", manifest)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
