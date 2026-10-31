"""The numbers the manuscript is allowed to say, loaded from the run outputs.

The manuscript is rendered from a template whose numeric slots are filled from
this module, and the module reads only the artefacts a run produced. Nothing
here computes a statistic: every value is copied from

* ``outputs/study/study_summary.json`` — the development draw;
* ``outputs/sweep/seed_draws.csv`` — the 24 declared seed draws;
* ``outputs/sweep/specifications.csv`` — the 18 declared specifications;
* ``outputs/sweep/sweep_summary.json`` — their distributions;
* ``outputs/sweep/verdict.json`` — the pre-registered rule tally;
* ``outputs/ablation/ablation_summary.json`` — the exploratory ablation, which
  is not pre-registered.

The module contains no market data and supports no market claim.
"""

from __future__ import annotations

import csv
import json
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_STUDY_DIR = HERE / "outputs" / "study"
DEFAULT_SWEEP_DIR = HERE / "outputs" / "sweep"
DEFAULT_ABLATION_DIR = HERE / "outputs" / "ablation"

#: Methods reported side by side, in the order the paper reports them.
METHODS: tuple[str, ...] = (
    "raw_midpoint",
    "bound_filtered",
    "protocol_identified",
    "protocol_certified",
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class BenchmarkOutputs:
    """Every artefact a manuscript number may be drawn from."""

    study: Mapping[str, Any]
    sweep: Mapping[str, Any]
    verdict: Mapping[str, Any]
    seed_rows: Sequence[Mapping[str, str]]
    specification_rows: Sequence[Mapping[str, str]]
    ablation: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def load(
        cls,
        study_dir: Path = DEFAULT_STUDY_DIR,
        sweep_dir: Path = DEFAULT_SWEEP_DIR,
        ablation_dir: Path = DEFAULT_ABLATION_DIR,
    ) -> BenchmarkOutputs:
        return cls(
            study=_read_json(study_dir / "study_summary.json"),
            sweep=_read_json(sweep_dir / "sweep_summary.json"),
            verdict=_read_json(sweep_dir / "verdict.json"),
            seed_rows=_read_csv(sweep_dir / "seed_draws.csv"),
            specification_rows=_read_csv(sweep_dir / "specifications.csv"),
            ablation=_read_json(ablation_dir / "ablation_summary.json"),
        )

    # -- convenience accessors -------------------------------------------

    @property
    def replication_rows(self) -> list[Mapping[str, str]]:
        """The replication seeds, development draw excluded."""
        development = int(self.verdict.get("development_seed", 20261022))
        rows = [
            row
            for row in self.seed_rows
            if (seed := _as_float(row.get("seed"))) is not None and int(seed) != development
        ]
        return sorted(rows, key=lambda row: int(float(row["seed"])))

    def rule(self, name: str) -> Mapping[str, Any]:
        for rule in self.verdict.get("rules", []):
            if rule.get("rule") == name:
                return rule
        return {}

    def column(self, rows: Sequence[Mapping[str, str]], key: str) -> list[float]:
        values = [_as_float(row.get(key)) for row in rows]
        return [value for value in values if value is not None]

    def distribution(self, key: str) -> dict[str, float]:
        """Median, IQR, range and mean of one sweep column."""
        values = sorted(self.column(self.replication_rows, key))
        if not values:
            return {}
        count = len(values)
        lower = values[: count // 2]
        upper = values[(count + 1) // 2 :]
        return {
            "n": count,
            "min": values[0],
            "q25": statistics.median(lower) if lower else values[0],
            "median": statistics.median(values),
            "q75": statistics.median(upper) if upper else values[-1],
            "max": values[-1],
            "mean": statistics.fmean(values),
        }


# -- formatting ----------------------------------------------------------


def pp(value: float | None, digits: int = 3) -> str:
    """Format a percentage-point quantity, or an em dash when absent."""
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def pct(value: float | None, digits: int = 1) -> str:
    """Format a share as a percentage."""
    if value is None:
        return "—"
    return f"{100.0 * value:.{digits}f}"


def sci(value: float | None, digits: int = 2) -> str:
    """Format a probability, keeping the small p-values legible."""
    if value is None:
        return "—"
    if value < 0.01:
        return f"{value:.4f}"
    return f"{value:.{digits}f}"


def integer(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{int(round(value))}"


def thousands(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{int(round(value)):,}"


#: Display names and order for the strata families of Table S1.
STRATA_FAMILIES: tuple[tuple[str, str], ...] = (
    ("moneyness", "Moneyness"),
    ("maturity", "Maturity"),
    ("spread", "Half-spread"),
    ("truth_magnitude", "True magnitude"),
)


def _strata_table(study: Mapping[str, Any]) -> str:
    """Table S1, rendered from the study's strata block.

    The table is data-shaped (four families, thirteen buckets, and the
    bucket labels are values rather than prose), so its rows are rendered
    here rather than in the template. The template supplies the caption and
    the note; this function supplies only cells whose numbers come from the
    run.
    """
    strata = study.get("strata", {})
    groups: list[Mapping[str, Any]] = []
    if isinstance(strata, Mapping):
        for family, _ in STRATA_FAMILIES:
            groups.append({family: strata.get(family, [])})
    lines = [
        "| Family | Bucket | n | Certified coverage (%) | Certified MAE (pp) | "
        "Raw-midpoint MAE (pp) | Raw MAE on abstained (pp) |",
        "|:--|:--|--:|--:|--:|--:|--:|",
    ]
    for group in groups:
        for family, rows in group.items():
            label = dict(STRATA_FAMILIES).get(family, family)
            for row in rows or []:
                cells = [
                    label,
                    str(row.get("bucket", "—")),
                    integer(row.get("n")),
                    pct(row.get("coverage_protocol")),
                    pp(row.get("mae_protocol_pp")),
                    pp(row.get("mae_raw_pp")),
                    pp(row.get("raw_mae_on_abstained_pp")),
                ]
                lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


# -- the flat context the template is rendered from ----------------------


def _frontier_row(
    frontier: Sequence[Mapping[str, Any]], tolerance: float
) -> Mapping[str, Any]:
    for row in frontier:
        if abs(float(row.get("tolerance_pp", -1.0)) - tolerance) < 1e-12:
            return row
    return {}


def _tolerance_key(tolerance: float) -> str:
    """A stable slot name for a tolerance, keeping 0.075 distinct from 0.08."""
    two = f"{tolerance:.2f}"
    if abs(float(two) - tolerance) > 1e-12:
        two = f"{tolerance:.3f}"
    return two.replace(".", "_")


def build_context(outputs: BenchmarkOutputs) -> dict[str, str]:
    """Every number the manuscript may cite, as a flat mapping of strings.

    Keys are namespaced by artefact. A template slot that is not in this
    mapping is a build error, not a silent blank.
    """
    study = outputs.study
    sweep = outputs.sweep
    verdict = outputs.verdict
    context: dict[str, str] = {}

    def put(key: str, value: object) -> None:
        context[key] = str(value)

    # -- study: shape of the run ----------------------------------------
    put("study.attempted", thousands(study.get("attempted")))
    put("study.market_data_used", str(bool(study.get("market_data_used"))).lower())
    reconciliation = study.get("reconciliation", {})
    for name, count in reconciliation.get("terminal_counts", {}).items():
        put(f"study.terminal.{name}", integer(count))
    for name, count in study.get("defect_counts", {}).items():
        put(f"study.defect.{name}", integer(count))
    for row in study.get("funnel", []):
        stage = str(row.get("stage", ""))
        put(f"study.funnel.{stage}.count", integer(row.get("count")))
        put(f"study.funnel.{stage}.share_attempted", pct(row.get("share_of_attempted")))
        put(
            f"study.funnel.{stage}.share_prior",
            pct(row.get("share_of_prior")),
        )
    # The funnel's stage counts are survivors, so the abstention split has to be
    # read off the terminal counts rather than inferred from a stage difference.
    stage_counts = reconciliation.get("stage_counts", {})
    terminal = reconciliation.get("terminal_counts", {})
    attempted = study.get("attempted")
    certified = terminal.get("resolved_within_tolerance")
    identified = stage_counts.get("endpoint")
    if isinstance(attempted, int) and isinstance(certified, int):
        put("study.abstained.total", integer(attempted - certified))
        put("study.abstained.share", pct((attempted - certified) / attempted))
        put("study.coverage.certified_share", pct(certified / attempted))
        other = attempted - certified
        for status in ("identified_outside_tolerance", "partially_resolved"):
            value = terminal.get(status)
            if isinstance(value, int):
                other -= value
        # Everything abstained before the tolerance stage: contract, timing and
        # input defects, plus pairs with no root on one side.
        put("study.abstained.earlier", integer(other))
    if isinstance(identified, int):
        put("study.tolerance.identified_total", integer(identified))
        put("study.tolerance.certified", integer(certified))
        put(
            "study.tolerance.outside",
            integer(terminal.get("identified_outside_tolerance")),
        )
    midpoint = stage_counts.get("midpoint")
    if isinstance(midpoint, int) and isinstance(identified, int):
        put("study.funnel.endpoint.removed", integer(midpoint - identified))

    for row in study.get("coverage_by_tolerance", []):
        key = _tolerance_key(float(row["tolerance_pp"]))
        put(f"study.coverage.{key}.attempted", pct(row["coverage_of_attempted"]))
        put(f"study.coverage.{key}.identified", pct(row["coverage_of_identified"]))
        put(f"study.coverage.{key}.resolved", integer(row["resolved"]))

    # -- study: error profile and own-set outcomes -----------------------
    for method, profile in study.get("error_profile", {}).items():
        put(f"study.error.{method}.n", integer(profile.get("n")))
        put(f"study.error.{method}.mae", pp(profile.get("mean_abs_error_pp")))
        put(f"study.error.{method}.median", pp(profile.get("median_abs_error_pp")))
        put(f"study.error.{method}.p90", pp(profile.get("p90_abs_error_pp")))
        put(f"study.error.{method}.p95", pp(profile.get("p95_abs_error_pp")))
        put(f"study.error.{method}.max", pp(profile.get("max_abs_error_pp")))
        put(
            f"study.error.{method}.within_0.10",
            pct(profile.get("share_within_0.10_pp")),
        )
    raw_mae = (
        study.get("error_profile", {}).get("raw_midpoint", {}).get("mean_abs_error_pp")
    )
    certified_mae = (
        study.get("error_profile", {})
        .get("protocol_certified", {})
        .get("mean_abs_error_pp")
    )
    if raw_mae and certified_mae:
        put("study.error.raw_over_certified", integer(round(raw_mae / certified_mae)))
    for method, own in study.get("own_set", {}).items():
        put(f"study.own.{method}.n", integer(own.get("n")))
        put(f"study.own.{method}.coverage", pct(own.get("coverage")))
        put(f"study.own.{method}.mae", pp(own.get("mae_vs_truth_pp")))
        put(f"study.own.{method}.bias", pp(own.get("bias_vs_truth_pp")))
        put(f"study.own.{method}.spearman", pp(own.get("spearman_vs_truth"), 4))

    # -- study: inference ------------------------------------------------
    inference = study.get("inference", {})
    for name, block in inference.items():
        if not isinstance(block, Mapping):
            continue
        put(f"study.inference.{name}.estimate", pp(block.get("estimate")))
        put(f"study.inference.{name}.ci_low", pp(block.get("ci_lower")))
        put(f"study.inference.{name}.ci_high", pp(block.get("ci_upper")))
        put(f"study.inference.{name}.p", sci(block.get("p_value")))
    put("study.inference.resamples", integer(inference.get("resamples")))
    put("study.inference.blocks", integer(inference.get("blocks")))

    # -- study: replication, perturbations, frontier ---------------------
    replication = study.get("replication", {})
    put("study.replication.primary.coverage", pct(replication.get("coverage_primary")))
    put("study.replication.holdout.coverage", pct(replication.get("coverage_holdout")))
    put(
        "study.replication.primary.error_reduction",
        pp(replication.get("own_set_error_reduction_primary_pp")),
    )
    put(
        "study.replication.holdout.error_reduction",
        pp(replication.get("own_set_error_reduction_holdout_pp")),
    )
    for row in study.get("perturbations", []):
        name = str(row.get("name", ""))
        change = _as_float(row.get("coverage_protocol_change"))
        put(f"study.perturbation.{name}.coverage_change", pct(change))
        if change is not None:
            put(f"study.perturbation.{name}.coverage_change_abs", pct(abs(change)))
        put(f"study.perturbation.{name}.mae", pp(row.get("mae_vs_truth_pp")))
        put(
            f"study.perturbation.{name}.cpiv_change",
            pp(row.get("mean_abs_cpiv_change_vs_base_pp")),
        )
        shift = _as_float(row.get("mean_abs_cpiv_change_vs_base_pp"))
        if shift is not None and certified_mae:
            put(
                f"study.perturbation.{name}.over_certified_error",
                integer(round(shift / certified_mae)),
            )
    for row in study.get("selection_frontier", []):
        key = _tolerance_key(float(row["tolerance_pp"]))
        put(f"study.frontier.{key}.n", integer(row.get("n_certified")))
        put(f"study.frontier.{key}.coverage", pct(row.get("coverage")))
        put(f"study.frontier.{key}.mae", pp(row.get("mae_certified_pp")))
        put(f"study.frontier.{key}.abstained_mae", pp(row.get("abstained_mae_pp")))
        put(f"study.frontier.{key}.null_mean", pp(row.get("null_mean_pp")))
        put(f"study.frontier.{key}.block_null_mean", pp(row.get("block_null_mean_pp")))
        put(f"study.frontier.{key}.p_pair", sci(row.get("p_value_pair_null")))
        put(f"study.frontier.{key}.p_block", sci(row.get("p_value_block_null")))
    secondary = study.get("secondary_outcome", {})
    retained = secondary.get("coverage_retained")
    if isinstance(retained, (int, float)):
        put("secondary.coverage_forgone", pct(1.0 - float(retained)))
    put("secondary.protocol_contracts", integer(secondary.get("protocol_contracts")))
    put("secondary.raw_contracts", integer(secondary.get("raw_contracts")))
    put("secondary.contracts_forgone", integer(secondary.get("contracts_forgone")))
    put("secondary.coverage_retained", pct(secondary.get("coverage_retained")))
    put(
        "secondary.max_slice_surface_change",
        pp(secondary.get("max_slice_surface_change_pp")),
    )
    put("supplementary.strata_table", _strata_table(study))
    truth = study.get("truth", {})
    put("study.common_set_note", str(study.get("common_set_note", "")))
    put("truth.median", pp(truth.get("median_true_cpiv_pp")))
    put("truth.min", pp(truth.get("min_true_cpiv_pp")))
    put("truth.max", pp(truth.get("max_true_cpiv_pp")))
    put("truth.n_defined", integer(truth.get("n_defined")))

    # -- sweep: distributions over the replication draws ------------------
    rows = outputs.replication_rows
    put("sweep.draws", integer(len(rows)))
    put("sweep.seeds_declared", integer(len(outputs.seed_rows)))
    for label, key in (
        ("coverage_certified", "coverage_certified"),
        ("coverage_identified", "coverage_identified"),
        ("mae_certified", "mae_certified_pp"),
        ("mae_raw", "mae_raw_pp"),
        ("mae_abstained", "mae_abstained_pp"),
        ("p_block", "frontier_p_block_null"),
        ("p_pair", "frontier_p_pair_null"),
    ):
        distribution = outputs.distribution(key)
        for statistic, value in distribution.items():
            if statistic == "n":
                continue
            if key.startswith("frontier_p"):
                rendered = sci(value)
            elif "mae" in key:
                rendered = pp(value)
            else:
                rendered = pct(value)
            put(f"sweep.{label}.{statistic}", rendered)
    trials = sweep.get("frontier_trials")
    put("sweep.frontier_trials", integer(trials))
    if isinstance(trials, int) and trials > 0:
        # An add-one p-value cannot fall below 1/(B+1); a reported value at the
        # floor is a bound, and the prose has to say so rather than quote it as
        # an exact tail probability.
        put("sweep.frontier_p_floor", sci(1.0 / (trials + 1)))

    # -- sweep: specification coverages ----------------------------------
    for row in outputs.specification_rows:
        name = str(row.get("draw", ""))
        coverage = _as_float(row.get("coverage_certified"))
        put(f"sweep.spec.{name}.coverage", pct(coverage))
        put(
            f"sweep.spec.{name}.mae_certified",
            pp(_as_float(row.get("mae_certified_pp"))),
        )
        put(f"sweep.spec.{name}.mae_raw", pp(_as_float(row.get("mae_raw_pp"))))

    # -- verdict: the pre-registered tally --------------------------------
    put("verdict.replication_draws", integer(verdict.get("replication_draws_evaluated")))
    put("verdict.passed", ", ".join(verdict.get("rules_passed", [])) or "none")
    put("verdict.failed", ", ".join(verdict.get("rules_failed", [])) or "none")
    for rule in verdict.get("rules", []):
        name = str(rule.get("rule", ""))
        put(f"verdict.{name}.passed", "PASS" if rule.get("passed") else "FAIL")
        put(f"verdict.{name}.evaluable", integer(rule.get("draws_evaluable")))
        put(f"verdict.{name}.below_block_null", integer(rule.get("draws_below_block_null")))
        put(
            f"verdict.{name}.block_null_p_below",
            integer(rule.get("draws_block_null_p_below_0_05")),
        )
        put(f"verdict.{name}.better", integer(rule.get("draws_better")))
        put(f"verdict.{name}.monotone", integer(rule.get("draws_monotone")))
        put(f"verdict.{name}.sign_agrees", integer(rule.get("draws_sign_agrees")))
        put(
            f"verdict.{name}.coverage_agrees",
            integer(rule.get("draws_coverage_within_tolerance")),
        )
        put(
            f"verdict.{name}.minimum_over_median",
            pp(rule.get("minimum_over_median")),
        )
        put(f"verdict.{name}.median_coverage", pct(rule.get("median_coverage")))
        put(f"verdict.{name}.minimum_coverage", pct(rule.get("minimum_coverage")))
        put(
            f"verdict.{name}.worst_coverage_shift",
            pct(rule.get("worst_absolute_coverage_change")),
        )

    # -- ablation: exploratory, not pre-registered ----------------------
    ablation = outputs.ablation
    if not ablation:
        raise ValueError(
            "the ablation summary is missing; run research.cpiv.measurement.ablation"
        )
    refused = ablation.get("refused_at_full_protocol", {})
    put("ablation.refused_time_value", integer(refused.get("time_value", 0)))
    put("ablation.refused_finite_shock", integer(refused.get("finite_shock", 0)))
    for name, variant in ablation["variants"].items():
        put(f"ablation.{name}.attempted", integer(variant.get("attempted")))
        put(f"ablation.{name}.certified", integer(variant.get("certified")))
        put(f"ablation.{name}.share", pct(variant.get("certified_share")))
        put(f"ablation.{name}.added", integer(variant.get("added_over_full")))
        put(
            f"ablation.{name}.mae_certified",
            pp(variant.get("error_certified_pp", {}).get("mean_abs_error_pp")),
        )
    return context
