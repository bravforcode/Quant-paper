"""Summarize midpoint-reference error and off-centre reference sensitivity.

All inputs are the synthetic local-approximation grid produced by
``research.cpiv.r10_diagnostics``. No market data are read.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.cpiv import build_demo as demo

SPREAD_LEVELS_PP = (0.5, 1.0, 2.0)
REFERENCE_OFFSETS_PP = (0.0, 1.0, 2.0, 5.0, 10.0)
LOG_SLOPE_ERROR_FLOOR_PP = 1e-9
BASELINE_GUARD = 1e-6


def _number(row: dict[str, Any], field: str) -> float:
    value = row.get(field)
    if value is None or value == "":
        raise ValueError(f"missing numeric grid field: {field}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite grid field {field}: {value}")
    return number


def _nearest_rank(values: list[float], probability: float) -> float:
    if not values or not 0.0 < probability <= 1.0:
        raise ValueError("nearest-rank quantile requires values and 0 < p <= 1")
    ordered = sorted(values)
    return ordered[math.ceil(probability * len(ordered)) - 1]


def _summary(values: list[float]) -> dict[str, Any]:
    if not values:
        raise ValueError("cannot summarize an empty sensitivity group")
    return {
        "n": len(values),
        "median_abs_error_pp": statistics.median(values),
        "p95_nearest_rank_abs_error_pp": _nearest_rank(values, 0.95),
        "max_abs_error_pp": max(values),
    }


def _configuration_slope(rows: list[dict[str, Any]]) -> float | None:
    points = sorted(
        (
            abs(_number(row, "target_cpiv_pp")),
            _number(row, "absolute_error_midpoint_pp"),
        )
        for row in rows
        if _number(row, "target_cpiv_pp") > 0.0
    )
    if len(points) != len(SPREAD_LEVELS_PP):
        return None
    if tuple(point[0] for point in points) != SPREAD_LEVELS_PP:
        return None
    if any(error <= LOG_SLOPE_ERROR_FLOOR_PP for _, error in points):
        return None
    log_x = [math.log(spread) for spread, _ in points]
    log_y = [math.log(error) for _, error in points]
    x_bar = statistics.mean(log_x)
    y_bar = statistics.mean(log_y)
    denominator = sum((value - x_bar) ** 2 for value in log_x)
    return sum((x - x_bar) * (y - y_bar) for x, y in zip(log_x, log_y, strict=True)) / denominator


def analyze_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute spread-scaling and signed off-centre-reference summaries."""
    if not rows:
        raise ValueError("local-approximation grid is empty")

    resolved: list[dict[str, Any]] = []
    for row in rows:
        vega = _number(row, "vega_midpoint_usd_per_decimal_iv")
        guard = _number(row, "legacy_absolute_vega_guard_usd_per_decimal_iv")
        approximation = row.get("local_approximation_pp")
        if vega >= guard and approximation not in (None, ""):
            resolved.append(row)

    expected_cell_count = len(rows)
    if not resolved:
        raise ValueError("no cells pass the configured midpoint-vega guard")

    spread_summaries: list[dict[str, Any]] = []
    previous: dict[str, float] | None = None
    for spread in SPREAD_LEVELS_PP:
        errors = [
            _number(row, "absolute_error_midpoint_pp")
            for row in resolved
            if math.isclose(abs(_number(row, "target_cpiv_pp")), spread, abs_tol=1e-12)
        ]
        current = _summary(errors)
        current["absolute_target_spread_pp"] = spread
        if previous is not None:
            current["median_growth_vs_previous_spread"] = (
                float(current["median_abs_error_pp"]) / previous["median_abs_error_pp"]
            )
            current["p95_growth_vs_previous_spread"] = (
                float(current["p95_nearest_rank_abs_error_pp"])
                / previous["p95_nearest_rank_abs_error_pp"]
            )
        spread_summaries.append(current)
        previous = {
            "median_abs_error_pp": float(current["median_abs_error_pp"]),
            "p95_nearest_rank_abs_error_pp": float(
                current["p95_nearest_rank_abs_error_pp"]
            ),
        }

    by_configuration: dict[
        tuple[float, float, float, float, float], list[dict[str, Any]]
    ] = defaultdict(list)
    for row in resolved:
        key = (
            _number(row, "spot_strike_ratio"),
            _number(row, "days_to_expiry"),
            _number(row, "reference_iv_decimal"),
            _number(row, "rate"),
            _number(row, "effective_yield"),
        )
        by_configuration[key].append(row)
    slopes = [
        slope
        for group in by_configuration.values()
        if (slope := _configuration_slope(group)) is not None
    ]
    if not slopes:
        raise ValueError("no configuration has three positive-spread errors above the log floor")

    off_center_summaries: list[dict[str, Any]] = []
    for offset_pp in REFERENCE_OFFSETS_PP:
        offset_errors: list[float] = []
        skipped_nonpositive_reference = 0
        directions = (0.0,) if offset_pp == 0.0 else (-offset_pp, offset_pp)
        for row in resolved:
            midpoint_iv = _number(row, "reference_iv_decimal")
            spot = _number(row, "spot_usd")
            strike = _number(row, "strike_usd")
            days = int(_number(row, "days_to_expiry"))
            rate = _number(row, "rate")
            yield_ = _number(row, "effective_yield")
            residual = _number(row, "integrated_vega_residual_usd")
            target = _number(row, "target_cpiv_pp")
            for signed_offset_pp in directions:
                reference_iv = midpoint_iv + signed_offset_pp / 100.0
                if reference_iv <= 0.0:
                    skipped_nonpositive_reference += 1
                    continue
                vega_decimal = 100.0 * demo.bs_vega_per_vol_point(
                    spot, strike, days, rate, yield_, reference_iv
                )
                if not math.isfinite(vega_decimal) or vega_decimal <= 0.0:
                    skipped_nonpositive_reference += 1
                    continue
                estimate_pp = 100.0 * residual / vega_decimal
                offset_errors.append(abs(estimate_pp - target))
        current = _summary(offset_errors)
        current.update(
            {
                "absolute_reference_offset_vol_points": offset_pp,
                "signed_offsets_evaluated_vol_points": list(directions),
                "skipped_nonpositive_reference_count": skipped_nonpositive_reference,
                "baseline_guard_passing_cell_denominator": len(resolved),
            }
        )
        off_center_summaries.append(current)

    return {
        "schema_version": "cpiv.reference-sensitivity/1.0",
        "status": "synthetic_reference_sensitivity_only",
        "market_data_used": False,
        "trading_or_alpha_claim": False,
        "grid": {
            "cell_n": expected_cell_count,
            "baseline_guard_passing_n": len(resolved),
            "baseline_guard_failing_n": expected_cell_count - len(resolved),
            "baseline_absolute_vega_guard_usd_per_decimal_iv": BASELINE_GUARD,
            "weighting": "each resolved grid cell receives equal weight",
        },
        "d_cubic_diagnostic": {
            "error_by_absolute_target_spread": spread_summaries,
            "per_configuration_log_log_slope": {
                "n": len(slopes),
                "median": statistics.median(slopes),
                "minimum": min(slopes),
                "maximum": max(slopes),
                "error_floor_pp": LOG_SLOPE_ERROR_FLOOR_PP,
                "configuration_keys": [
                    "spot_strike_ratio",
                    "days_to_expiry",
                    "reference_iv_decimal",
                    "rate",
                    "effective_yield",
                ],
                "fit_points": list(SPREAD_LEVELS_PP),
            },
        },
        "off_centre_reference": {
            "definition": (
                "sigma_ref = symmetric midpoint +/- offset; one evaluation at zero, "
                "both signed offsets otherwise"
            ),
            "offset_unit": "volatility percentage points",
            "method": (
                "100 times the integrated-vega residual divided by project BSM vega "
                "at sigma_ref, compared with the generated target CPIV"
            ),
            "nonpositive_reference_policy": "skip; a BSM reference volatility must be positive",
            "denominator": "only cells passing the baseline midpoint absolute-vega guard",
            "summaries": off_center_summaries,
        },
    }


def _read_grid(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"local-approximation grid is empty: {path}")
    return rows


def _write_outputs(grid_path: Path, output_dir: Path) -> dict[str, Any]:
    names = (
        "reference_sensitivity_summary.csv",
        "reference_sensitivity_summary.json",
        "local_approximation_d3_scaling.png",
        "local_approximation_d3_scaling.svg",
    )
    existing = [name for name in names if (output_dir / name).exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite analysis outputs: {', '.join(existing)}")
    rows = _read_grid(grid_path)
    summary = analyze_rows(rows)
    if (
        summary["grid"]["cell_n"] != 720
        or summary["grid"]["baseline_guard_passing_n"] != 624
    ):
        raise ValueError(
            "the declared 720-cell design must resolve 624 cells under its baseline guard"
        )
    summary["input_grid_sha256"] = hashlib.sha256(grid_path.read_bytes()).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_rows: list[dict[str, Any]] = []
    for row in summary["d_cubic_diagnostic"]["error_by_absolute_target_spread"]:
        output_rows.append({"analysis": "spread_scaling", **row})
    for row in summary["off_centre_reference"]["summaries"]:
        output_rows.append({"analysis": "off_centre_reference", **row})
    with (output_dir / names[0]).open("w", newline="", encoding="utf-8") as handle:
        columns = list(dict.fromkeys(key for row in output_rows for key in row))
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(output_rows)
    (output_dir / names[1]).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    render_d3_scaling_figure(summary, output_dir)
    return summary


def render_d3_scaling_figure(summary: dict[str, Any], output_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = summary["d_cubic_diagnostic"]["error_by_absolute_target_spread"]
    spreads = [float(row["absolute_target_spread_pp"]) for row in rows]
    medians = [float(row["median_abs_error_pp"]) for row in rows]
    p95s = [float(row["p95_nearest_rank_abs_error_pp"]) for row in rows]
    reference = [p95s[0] * (spread / spreads[0]) ** 3 for spread in spreads]
    slope = summary["d_cubic_diagnostic"]["per_configuration_log_log_slope"]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    figure, axis = plt.subplots(figsize=(6.8, 4.2), constrained_layout=True)
    axis.loglog(spreads, medians, marker="o", color="#0072B2", label="Median absolute error")
    axis.loglog(spreads, p95s, marker="s", color="#D55E00", label="Nearest-rank p95")
    axis.loglog(
        spreads,
        reference,
        linestyle="--",
        color="#555555",
        label=r"$d^3$ reference (anchored at p95, 0.5 pp)",
    )
    axis.set_xticks(spreads, labels=[f"{spread:g}" for spread in spreads])
    axis.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axis.set_xlabel("Absolute target CPIV spread |d| (pp)")
    axis.set_ylabel("Absolute midpoint-approximation error (pp)")
    axis.set_title("Midpoint-reference error scaling in the synthetic grid")
    axis.grid(which="both", alpha=0.24)
    axis.legend(frameon=False)
    axis.text(
        0.04,
        0.96,
        f"Per-configuration log–log slope: median {slope['median']:.4f}; "
        f"range {slope['minimum']:.3f}–{slope['maximum']:.3f}; n={slope['n']}",
        transform=axis.transAxes,
        va="top",
        fontsize=8,
    )
    for suffix in ("png", "svg"):
        figure.savefig(
            output_dir / f"local_approximation_d3_scaling.{suffix}",
            dpi=220,
            bbox_inches="tight",
        )
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grid", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = _write_outputs(args.grid, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
