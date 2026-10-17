"""Separate synthetic tick, quote-spread, and floating-point sensitivities."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from research.cpiv import build_demo as demo

PRICE_TICK_LEVELS = (0.0001, 0.001, 0.01, 0.1)
QUOTE_HALF_SPREAD_LEVELS = (0.01, 0.02, 0.05, 0.1, 0.25)
UNIT_ROUNDOFF = 2.0**-53
RESOLUTION_VEGA_GUARD = 1e-6
EXACT_IV_SHIFT_CAP_PP = 500.0
IV_SHIFT_BANDS_PP = (0.1, 1.0, 10.0)
DEFAULT_IV_TOLERANCE_PP = 0.1


def _iv_shift_band(value_pp: float) -> int:
    """Return the fixed display band: <=0.1, <=1, <=10, or >10 pp."""
    magnitude = abs(value_pp)
    return next(
        (index for index, boundary in enumerate(IV_SHIFT_BANDS_PP) if magnitude <= boundary), 3
    )


def _positive_levels(values: Sequence[float], name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not result:
        raise ValueError(f"{name} must contain at least one positive value")
    if any(not math.isfinite(value) or value <= 0.0 for value in result):
        raise ValueError(f"{name} values must be finite and positive")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} values must be unique")
    return result


def _validate_iv_tolerance(value: float) -> float:
    tolerance = float(value)
    if not math.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("iv_tolerance_pp must be finite and nonnegative")
    return tolerance


def _otm_equivalent_time_value(
    option_type: str,
    price: float,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    yield_: float,
) -> float:
    """Return the leg's price above its European lower bound."""
    time_to_expiry = days / 365.0
    discounted_spot = spot * math.exp(-yield_ * time_to_expiry)
    discounted_strike = strike * math.exp(-rate * time_to_expiry)
    if option_type == "call":
        lower_bound = max(discounted_spot - discounted_strike, 0.0)
    elif option_type == "put":
        lower_bound = max(discounted_strike - discounted_spot, 0.0)
    else:
        raise ValueError(f"unsupported option_type: {option_type}")
    return max(price - lower_bound, 0.0)


def _exact_iv_shift(
    option_type: str,
    shocked_price: float,
    spot: float,
    strike: float,
    days: int,
    rate: float,
    yield_: float,
    reference_iv: float,
) -> tuple[float | None, str]:
    try:
        shocked_iv = demo.implied_volatility(
            option_type, shocked_price, spot, strike, days, rate, yield_
        )
    except ValueError:
        return None, "not_invertible_under_configured_bounds"
    return 100.0 * (shocked_iv - reference_iv), "inverted"


def _configuration_grid() -> list[dict[str, float]]:
    return [
        {
            "spot_strike_ratio": ratio,
            "spot": 100.0 * ratio,
            "strike": 100.0,
            "days_to_expiry": float(days),
            "reference_iv_decimal": sigma,
            "rate": rate,
            "effective_yield": yield_,
        }
        for ratio in (0.8, 0.9, 1.0, 1.1, 1.2)
        for days in (7, 30, 90, 365)
        for sigma in (0.10, 0.20, 0.40)
        for rate, yield_ in ((0.0, 0.0), (0.05, 0.02))
    ]


def _make_row(
    config: dict[str, float],
    option_type: str,
    price: float,
    vega_decimal: float,
    source: str,
    scale: float,
    price_perturbation: float,
    roundoff_unit: float,
    resolution_tick: float,
    iv_tolerance_pp: float,
) -> dict[str, Any]:
    tolerance = _validate_iv_tolerance(iv_tolerance_pp)
    vega_pp = vega_decimal / 100.0
    local_shift = price_perturbation / vega_pp
    tick_reference = scale if source == "one_full_price_tick" else resolution_tick
    otm_equivalent_value = _otm_equivalent_time_value(
        option_type,
        price,
        config["spot"],
        config["strike"],
        int(config["days_to_expiry"]),
        config["rate"],
        config["effective_yield"],
    )
    row: dict[str, Any] = {
        **config,
        "option_type": option_type,
        "synthetic_option_price": price,
        "price_perturbation_source": source,
        "source_parameter": scale,
        "price_perturbation_absolute": price_perturbation,
        "tick_reference_price_units": tick_reference,
        "unit_roundoff": roundoff_unit,
        "vega_currency_per_decimal_iv": vega_decimal,
        "vega_currency_per_iv_pp": vega_pp,
        "local_delta_iv_pp": local_shift,
        "price_perturbation_over_premium": (price_perturbation / abs(price) if price else None),
        "otm_equivalent_time_value_price_units": otm_equivalent_value,
        "otm_equivalent_time_value_below_tick": otm_equivalent_value < tick_reference,
        "legacy_absolute_vega_guard_pass": (vega_decimal >= RESOLUTION_VEGA_GUARD),
        "iv_tolerance_pp": tolerance,
        "sensitivity_scope": "local derivative; not a finite uncertainty interval",
        "market_data_used": False,
    }
    if source == "floating_point_roundoff_scale":
        row["exact_up_delta_iv_pp"] = None
        row["exact_up_status"] = "not_evaluated_at_roundoff_scale"
        row["exact_up_to_local_abs_ratio"] = None
        row["exact_down_delta_iv_pp"] = None
        row["exact_down_status"] = "not_evaluated_at_roundoff_scale"
        row["exact_down_to_local_abs_ratio"] = None
        row["finite_shock_status"] = "not_evaluated_at_roundoff_scale"
        row["max_abs_finite_iv_shift_pp"] = None
        row["identification_status"] = "local_only_roundoff"
        row["within_iv_tolerance"] = False
        row["iv_tolerance_status"] = "not_assessed_local_only"
        return row

    exact_statuses: dict[str, str] = {}
    for direction, suffix in ((1.0, "up"), (-1.0, "down")):
        shift, status = _exact_iv_shift(
            option_type,
            price + direction * price_perturbation,
            config["spot"],
            config["strike"],
            int(config["days_to_expiry"]),
            config["rate"],
            config["effective_yield"],
            config["reference_iv_decimal"],
        )
        row[f"exact_{suffix}_delta_iv_pp"] = shift
        row[f"exact_{suffix}_status"] = status
        row[f"exact_{suffix}_to_local_abs_ratio"] = (
            abs(shift) / abs(local_shift) if shift is not None and local_shift != 0.0 else None
        )
        exact_statuses[suffix] = status
    row["finite_shock_status"] = (
        "both_directions_invertible"
        if all(status == "inverted" for status in exact_statuses.values())
        else "up_only_invertible"
        if exact_statuses["up"] == "inverted"
        else "down_only_invertible"
        if exact_statuses["down"] == "inverted"
        else "neither_direction_invertible"
    )
    finite_shifts = [
        abs(float(row[f"exact_{suffix}_delta_iv_pp"]))
        for suffix in ("up", "down")
        if row[f"exact_{suffix}_delta_iv_pp"] is not None
    ]
    max_finite_shift = max(finite_shifts, default=None)
    row["max_abs_finite_iv_shift_pp"] = max_finite_shift
    if row["otm_equivalent_time_value_below_tick"] is True:
        identification_status = "unresolved_otm_equivalent_below_tick"
    elif row["finite_shock_status"] == "both_directions_invertible":
        identification_status = "identified"
    else:
        identification_status = "unresolved_shock_no_root"
    row["identification_status"] = identification_status
    within_tolerance = (
        identification_status == "identified"
        and max_finite_shift is not None
        and max_finite_shift <= tolerance
    )
    row["within_iv_tolerance"] = within_tolerance
    row["iv_tolerance_status"] = (
        "within_tau_iv"
        if within_tolerance
        else "outside_tau_iv"
        if identification_status == "identified"
        else "unresolved_not_qualified"
    )
    return row


def price_resolution_grid(
    tick_values: Sequence[float] = PRICE_TICK_LEVELS,
    quote_half_spreads: Sequence[float] = QUOTE_HALF_SPREAD_LEVELS,
    roundoff_unit: float = UNIT_ROUNDOFF,
    iv_tolerance_pp: float = DEFAULT_IV_TOLERANCE_PP,
) -> list[dict[str, Any]]:
    """Return leg-level local sensitivities and feasible finite-price checks.

    Tick and half-spread values use price units per underlying unit. A tick is
    interpreted as one full price step; the separate rows prevent the three
    perturbation sources from being collapsed into one threshold.
    """
    ticks = _positive_levels(tick_values, "tick_values")
    half_spreads = _positive_levels(quote_half_spreads, "quote_half_spreads")
    tolerance = _validate_iv_tolerance(iv_tolerance_pp)
    if not math.isfinite(roundoff_unit) or roundoff_unit <= 0.0:
        raise ValueError("roundoff_unit must be finite and positive")
    resolution_tick = 0.01 if 0.01 in ticks else ticks[0]

    rows: list[dict[str, Any]] = []
    for config in _configuration_grid():
        for option_type in ("call", "put"):
            price = demo.bs_price(
                option_type,
                config["spot"],
                config["strike"],
                int(config["days_to_expiry"]),
                config["rate"],
                config["effective_yield"],
                config["reference_iv_decimal"],
            )
            vega_decimal = 100.0 * demo.bs_vega_per_vol_point(
                config["spot"],
                config["strike"],
                int(config["days_to_expiry"]),
                config["rate"],
                config["effective_yield"],
                config["reference_iv_decimal"],
            )
            for tick in ticks:
                rows.append(
                    _make_row(
                        config,
                        option_type,
                        price,
                        vega_decimal,
                        "one_full_price_tick",
                        tick,
                        tick,
                        roundoff_unit,
                        resolution_tick,
                        tolerance,
                    )
                )
            for half_spread in half_spreads:
                rows.append(
                    _make_row(
                        config,
                        option_type,
                        price,
                        vega_decimal,
                        "quote_half_spread",
                        half_spread,
                        half_spread,
                        roundoff_unit,
                        resolution_tick,
                        tolerance,
                    )
                )
            roundoff_scale = roundoff_unit * abs(price)
            rows.append(
                _make_row(
                    config,
                    option_type,
                    price,
                    vega_decimal,
                    "floating_point_roundoff_scale",
                    roundoff_unit,
                    roundoff_scale,
                    roundoff_unit,
                    resolution_tick,
                    tolerance,
                )
            )
    return rows


def _review_example_cells(
    tick: float,
    roundoff_unit: float,
    iv_tolerance_pp: float,
    shock_fraction: float,
    shock_source: str,
) -> list[dict[str, Any]]:
    tick_value = _positive_levels((tick,), "tick")[0]
    if not math.isfinite(roundoff_unit) or roundoff_unit <= 0.0:
        raise ValueError("roundoff_unit must be finite and positive")
    tolerance = _validate_iv_tolerance(iv_tolerance_pp)
    examples = (
        ("ATM_30d_iv20", 100.0, 100.0, 30, 0.20),
        ("spot_ratio_0.8_90d_iv10", 80.0, 100.0, 90, 0.10),
    )
    results: list[dict[str, Any]] = []
    for name, spot, strike, days, sigma in examples:
        config = {
            "spot_strike_ratio": spot / strike,
            "spot": spot,
            "strike": strike,
            "days_to_expiry": float(days),
            "reference_iv_decimal": sigma,
            "rate": 0.0,
            "effective_yield": 0.0,
        }
        for option_type in ("call", "put"):
            price = demo.bs_price(option_type, spot, strike, days, 0.0, 0.0, sigma)
            vega_decimal = 100.0 * demo.bs_vega_per_vol_point(spot, strike, days, 0.0, 0.0, sigma)
            row = _make_row(
                config,
                option_type,
                price,
                vega_decimal,
                shock_source,
                tick_value,
                tick_value * shock_fraction,
                roundoff_unit,
                tick_value,
                tolerance,
            )
            row.update(
                {
                    "example": name,
                    "hypothetical_tick": tick_value,
                    "price_shock_fraction_of_tick": shock_fraction,
                    "premium_tick_ratio": price / tick_value,
                    "roundoff_price_perturbation": roundoff_unit * abs(price),
                    "roundoff_delta_iv_pp": (roundoff_unit * abs(price) / (vega_decimal / 100.0)),
                }
            )
            results.append(row)
    return results


def review_example_cells(
    tick: float = 0.01,
    roundoff_unit: float = UNIT_ROUNDOFF,
    iv_tolerance_pp: float = DEFAULT_IV_TOLERANCE_PP,
) -> list[dict[str, Any]]:
    """Recompute the examples under the full-tick (±t) shock convention."""
    return _review_example_cells(
        tick, roundoff_unit, iv_tolerance_pp, 1.0, "one_full_price_tick"
    )


def review_example_half_tick_cells(
    tick: float = 0.01,
    roundoff_unit: float = UNIT_ROUNDOFF,
    iv_tolerance_pp: float = DEFAULT_IV_TOLERANCE_PP,
) -> list[dict[str, Any]]:
    """Recompute the examples under nearest-tick rounding shocks (±t/2)."""
    return _review_example_cells(
        tick, roundoff_unit, iv_tolerance_pp, 0.5, "nearest_tick_rounding_half_tick"
    )


def premium_below_tick_quote_examples(tick: float = 0.01) -> list[dict[str, Any]]:
    """Show how a sub-tick synthetic call premium maps to discrete quote prices."""
    tick_value = _positive_levels((tick,), "tick")[0]
    spot, strike, days, rate, yield_, reference_iv = 80.0, 100.0, 90, 0.0, 0.0, 0.10
    model_price = demo.bs_price("call", spot, strike, days, rate, yield_, reference_iv)
    scenarios = (
        ("zero_bid", 0.0, "no_interior_root_at_lower_bound"),
        ("zero_to_one_tick_midpoint", tick_value / 2.0, "inverted"),
        ("one_tick_ask", tick_value, "inverted"),
    )
    rows: list[dict[str, Any]] = []
    for scenario, quote_price, expected_status in scenarios:
        try:
            implied_iv = 100.0 * demo.implied_volatility(
                "call", quote_price, spot, strike, days, rate, yield_
            )
            status = "inverted"
        except ValueError:
            implied_iv = None
            status = "no_interior_root_at_lower_bound"
        if status != expected_status:
            raise ArithmeticError(f"unexpected IV inversion status for {scenario}: {status}")
        rows.append(
            {
                "scenario": scenario,
                "option_type": "call",
                "spot": spot,
                "strike": strike,
                "days_to_expiry": days,
                "reference_iv_percent": 100.0 * reference_iv,
                "synthetic_model_premium": model_price,
                "hypothetical_tick": tick_value,
                "synthetic_otm_call_premium_below_tick": model_price < tick_value,
                "scenario_quote_price": quote_price,
                "implied_iv_percent": implied_iv,
                "status": status,
                "market_data_used": False,
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def render_price_resolution_status_heatmap(
    rows: list[dict[str, Any]], output_dir: Path, iv_tolerance_pp: float
) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    selected = [
        row
        for row in rows
        if row["rate"] == 0.0
        and row["effective_yield"] == 0.0
        and row["reference_iv_decimal"] in (0.10, 0.20)
        and int(row["days_to_expiry"]) in (30, 90)
        and row["price_perturbation_source"] in ("one_full_price_tick", "quote_half_spread")
    ]
    if not selected:
        raise ValueError("status heatmap requires zero-carry tick and spread scenarios")

    tick_levels = sorted(
        {
            float(row["source_parameter"])
            for row in rows
            if row["price_perturbation_source"] == "one_full_price_tick"
        }
    )
    if not tick_levels:
        raise ValueError("status heatmap requires at least one tick level")
    tolerance = _validate_iv_tolerance(iv_tolerance_pp)
    labels = ("Unresolved", f"Identified; ≤{tolerance:g} pp", f"Identified; >{tolerance:g} pp")
    cmap = ListedColormap(("#bdbdbd", "#2c7bb6", "#fdae61"))
    norm = BoundaryNorm((-1.5, -0.5, 0.5, 1.5), cmap.N)
    source_specs = (
        ("one_full_price_tick", "Hypothetical full tick"),
        ("quote_half_spread", "Hypothetical quote half-spread"),
    )
    fig, axes = plt.subplots(2, 2, figsize=(8.0, 6.6), constrained_layout=True)
    for column, sigma in enumerate((0.10, 0.20)):
        for row_index, (source, title) in enumerate(source_specs):
            axis = axes[row_index, column]
            panel = [
                item
                for item in selected
                if item["reference_iv_decimal"] == sigma
                and item["price_perturbation_source"] == source
            ]
            levels = sorted({float(item["source_parameter"]) for item in panel})
            configs = sorted(
                {(float(item["spot_strike_ratio"]), int(item["days_to_expiry"])) for item in panel},
                key=lambda item: (item[0], item[1]),
            )
            matrix: list[list[int]] = []
            markers: list[list[str]] = []
            for ratio, days in configs:
                values: list[int] = []
                marker_row: list[str] = []
                for level in levels:
                    matching = [
                        item
                        for item in panel
                        if float(item["spot_strike_ratio"]) == ratio
                        and int(item["days_to_expiry"]) == days
                        and float(item["source_parameter"]) == level
                    ]
                    if not matching:
                        raise ValueError("incomplete price-resolution status cell")
                    below_tick = any(
                        item["identification_status"] == "unresolved_otm_equivalent_below_tick"
                        for item in matching
                    )
                    missing_root = any(
                        item["identification_status"] == "unresolved_shock_no_root"
                        for item in matching
                    )
                    identified = all(
                        item["identification_status"] == "identified" for item in matching
                    )
                    worst_shift = max(
                        (
                            float(item["max_abs_finite_iv_shift_pp"])
                            for item in matching
                            if item["max_abs_finite_iv_shift_pp"] is not None
                        ),
                        default=None,
                    )
                    values.append(
                        -1
                        if not identified or worst_shift is None
                        else 0
                        if worst_shift <= tolerance
                        else 1
                    )
                    marker_row.append(("†" if below_tick else "") + ("×" if missing_root else ""))
                matrix.append(values)
                markers.append(marker_row)
            image = axis.imshow(
                matrix, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm
            )
            for y_index, marker_row in enumerate(markers):
                for x_index, marker in enumerate(marker_row):
                    if marker:
                        axis.text(x_index, y_index, marker, ha="center", va="center", fontsize=7.5)
            axis.set_title(f"{title}; reference IV={sigma:.0%}", fontsize=10.5)
            axis.set_yticks(
                range(len(configs)),
                labels=[f"S/K {ratio:.1f}, {days}d" for ratio, days in configs],
                fontsize=9.5,
            )
            axis.set_xticks(
                range(len(levels)), labels=[f"{level:g}" for level in levels], fontsize=9.5
            )
            axis.set_xlabel("Price units per underlying unit", fontsize=9.5)
    colorbar = fig.colorbar(
        image,
        ax=axes.ravel().tolist(),
        orientation="horizontal",
        fraction=0.06,
        pad=0.16,
    )
    colorbar.set_ticks((-1, 0, 1), labels=labels)
    colorbar.ax.tick_params(labelsize=9)
    colorbar.set_label("Identification and finite-shock tolerance status", fontsize=9.5)
    fig.suptitle(f"Finite-shock price identification (τIV={tolerance:g} pp)", fontsize=13)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    for suffix in ("png", "svg"):
        filename = f"cpiv_r11_price_resolution_status_heatmap.{suffix}"
        fig.savefig(output_dir / filename, dpi=220, bbox_inches="tight")
        generated.append(filename)
    plt.close(fig)
    return generated


def render_finite_shock_change_heatmap(rows: list[dict[str, Any]], output_dir: Path) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    selected = [
        row
        for row in rows
        if row["rate"] == 0.0
        and row["effective_yield"] == 0.0
        and row["reference_iv_decimal"] in (0.10, 0.20)
        and int(row["days_to_expiry"]) in (30, 90)
        and row["price_perturbation_source"] == "one_full_price_tick"
    ]
    if not selected:
        raise ValueError("finite-shock figure requires zero-carry full-tick scenarios")

    labels = ("Unresolved", "≤0.1", ">0.1–1", ">1–10", ">10 (≤500)")
    cmap = ListedColormap(("#bdbdbd", "#2c7bb6", "#abd9e9", "#fdae61", "#d7191c"))
    norm = BoundaryNorm((-1.5, -0.5, 0.5, 1.5, 2.5, 3.5), cmap.N)
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 5.0), constrained_layout=True)
    for column, sigma in enumerate((0.10, 0.20)):
        axis = axes[column]
        panel = [item for item in selected if item["reference_iv_decimal"] == sigma]
        levels = sorted({float(item["source_parameter"]) for item in panel})
        configs = sorted(
            {(float(item["spot_strike_ratio"]), int(item["days_to_expiry"])) for item in panel},
            key=lambda item: (item[0], item[1]),
        )
        matrix: list[list[int]] = []
        markers: list[list[str]] = []
        for ratio, days in configs:
            status_row: list[int] = []
            marker_row: list[str] = []
            for level in levels:
                matching = [
                    item
                    for item in panel
                    if float(item["spot_strike_ratio"]) == ratio
                    and int(item["days_to_expiry"]) == days
                    and float(item["source_parameter"]) == level
                ]
                if not matching:
                    raise ValueError("incomplete finite-shock display cell")
                finite_shifts = [
                    abs(float(item[f"exact_{direction}_delta_iv_pp"]))
                    for item in matching
                    for direction in ("up", "down")
                    if item[f"exact_{direction}_delta_iv_pp"] is not None
                ]
                if any(
                    not math.isfinite(value) or value > EXACT_IV_SHIFT_CAP_PP + 1e-8
                    for value in finite_shifts
                ):
                    raise ValueError("finite IV shock exceeded the configured 500-pp cap")
                status_row.append(_iv_shift_band(max(finite_shifts)) if finite_shifts else -1)
                below_tick = any(
                    item["otm_equivalent_time_value_below_tick"] is True for item in matching
                )
                missing_root = any(
                    item["finite_shock_status"] != "both_directions_invertible" for item in matching
                )
                marker_row.append(("†" if below_tick else "") + ("×" if missing_root else ""))
            matrix.append(status_row)
            markers.append(marker_row)
        image = axis.imshow(matrix, aspect="auto", interpolation="nearest", cmap=cmap, norm=norm)
        for y_index, marker_row in enumerate(markers):
            for x_index, marker in enumerate(marker_row):
                if marker:
                    axis.text(x_index, y_index, marker, ha="center", va="center", fontsize=7.5)
        axis.set_title(f"Reference IV={sigma:.0%}", fontsize=11)
        axis.set_yticks(
            range(len(configs)),
            labels=[f"S/K {ratio:.1f}, {days}d" for ratio, days in configs],
            fontsize=9.5,
        )
        axis.set_xticks(range(len(levels)), labels=[f"{level:g}" for level in levels], fontsize=9.5)
        axis.set_xlabel("Full hypothetical tick (price units)", fontsize=10)
        if math.isclose(sigma, 0.10):
            highlight = next(
                (
                    (row_index, level_index)
                    for row_index, (ratio, days) in enumerate(configs)
                    if ratio == 0.8 and days == 90
                    for level_index, level in enumerate(levels)
                    if math.isclose(level, 0.01)
                ),
                None,
            )
            if highlight is not None:
                y_index, x_index = highlight
                example = next(
                    item
                    for item in panel
                    if float(item["spot_strike_ratio"]) == 0.8
                    and int(item["days_to_expiry"]) == 90
                    and item["option_type"] == "call"
                    and math.isclose(float(item["source_parameter"]), 0.01)
                )
                exact_up = example["exact_up_delta_iv_pp"]
                if exact_up is not None:
                    axis.text(
                        x_index,
                        y_index,
                        f"{abs(float(exact_up)):.1f}†×",
                        ha="center",
                        va="center",
                        fontsize=7.5,
                        fontweight="bold",
                        bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "alpha": 0.9},
                    )
    colorbar = fig.colorbar(
        image,
        ax=axes.ravel().tolist(),
        orientation="horizontal",
        fraction=0.07,
        pad=0.14,
    )
    colorbar.set_ticks((-1, 0, 1, 2, 3), labels=labels)
    colorbar.ax.tick_params(labelsize=9)
    colorbar.set_label("Maximum resolved exact |ΔIV| band (pp)", fontsize=10)
    fig.suptitle("Exact finite-shock changes in implied volatility", fontsize=13)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    for suffix in ("png", "svg"):
        filename = f"cpiv_r11_finite_shock_change_heatmap.{suffix}"
        fig.savefig(output_dir / filename, dpi=220, bbox_inches="tight")
        generated.append(filename)
    plt.close(fig)
    return generated


def write_r11_outputs(
    output_dir: Path,
    tick_values: Sequence[float] = PRICE_TICK_LEVELS,
    quote_half_spreads: Sequence[float] = QUOTE_HALF_SPREAD_LEVELS,
    roundoff_unit: float = UNIT_ROUNDOFF,
    iv_tolerance_pp: float = DEFAULT_IV_TOLERANCE_PP,
) -> dict[str, Any]:
    ticks = _positive_levels(tick_values, "tick_values")
    half_spreads = _positive_levels(quote_half_spreads, "quote_half_spreads")
    tolerance = _validate_iv_tolerance(iv_tolerance_pp)
    rows = price_resolution_grid(ticks, half_spreads, roundoff_unit, tolerance)
    examples = review_example_cells(roundoff_unit=roundoff_unit, iv_tolerance_pp=tolerance)
    half_tick_examples = review_example_half_tick_cells(
        roundoff_unit=roundoff_unit, iv_tolerance_pp=tolerance
    )
    tick_examples = premium_below_tick_quote_examples(0.01 if 0.01 in ticks else ticks[-1])
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "cpiv_r11_price_resolution.csv", rows)
    _write_csv(output_dir / "cpiv_r11_review_example_cells.csv", examples)
    _write_csv(output_dir / "cpiv_r11_nearest_tick_rounding_examples.csv", half_tick_examples)
    _write_csv(output_dir / "cpiv_r11_sub_tick_quote_examples.csv", tick_examples)
    figures = [
        *render_price_resolution_status_heatmap(rows, output_dir, tolerance),
        *render_finite_shock_change_heatmap(rows, output_dir),
    ]
    tick_levels = sorted(
        {
            float(row["source_parameter"])
            for row in rows
            if row["price_perturbation_source"] == "one_full_price_tick"
        }
    )
    spread_reference_tick = 0.01 if 0.01 in tick_levels else tick_levels[0]
    summary = {
        "status": "synthetic_price_resolution_sensitivity_only",
        "market_data_used": False,
        "tick_interpretation": (
            "full-tick sensitivity uses price shocks ±t; nearest-tick rounding sensitivity "
            "uses price shocks ±t/2"
        ),
        "tick_levels_price_units_per_underlying_unit": ticks,
        "quote_half_spread_levels_price_units_per_underlying_unit": half_spreads,
        "roundoff_unit": roundoff_unit,
        "iv_tolerance_pp": tolerance,
        "iv_tolerance_rule": (
            "identified only when OTM-equivalent time value is at least the reference tick "
            "and both finite shocks invert; within tolerance when the maximum worst-direction "
            "absolute IV displacement from the base is no greater than tau_IV"
        ),
        "roundoff_interpretation": (
            "u times absolute premium; illustrative relative perturbation, "
            "not a rigorous floating-point error bound"
        ),
        "sensitivity_interpretation": (
            "local derivative is diagnostic only; finite-shock identification and the "
            "worst-direction displacement tolerance are reported separately"
        ),
        "baseline_absolute_vega_guard_currency_per_decimal_iv": RESOLUTION_VEGA_GUARD,
        "configuration_count": 120,
        "leg_source_parameter_rows": len(rows),
        "rows_by_source": {
            source: sum(row["price_perturbation_source"] == source for row in rows)
            for source in (
                "one_full_price_tick",
                "quote_half_spread",
                "floating_point_roundoff_scale",
            )
        },
        "review_example_cells": examples,
        "nearest_tick_rounding_example_cells": half_tick_examples,
        "sub_tick_quote_examples": tick_examples,
        "identification_status_counts": {
            status: sum(row["identification_status"] == status for row in rows)
            for status in (
                "identified",
                "unresolved_otm_equivalent_below_tick",
                "unresolved_shock_no_root",
                "local_only_roundoff",
            )
        },
        "iv_tolerance_status_counts": {
            status: sum(row["iv_tolerance_status"] == status for row in rows)
            for status in (
                "within_tau_iv",
                "outside_tau_iv",
                "unresolved_not_qualified",
                "not_assessed_local_only",
            )
        },
        "heatmap_aggregation": ("max(call, put) per configuration; leg-level rows retained in CSV"),
        "heatmap_display": {
            "zero_carry_only": True,
            "reference_iv_decimals": [0.10, 0.20],
            "days_to_expiry": [30, 90],
            "spread_panel_otm_equivalent_time_value_tick_reference": spread_reference_tick,
            "identification_and_tolerance_categories": [
                "unresolved",
                f"identified_and_within_{tolerance:g}_pp",
                f"identified_but_outside_{tolerance:g}_pp",
            ],
            "finite_shock_bands_pp": ["<=0.1", ">0.1-1", ">1-10", ">10 through 500", "unresolved"],
        },
        "files": [
            "cpiv_r11_price_resolution.csv",
            "cpiv_r11_review_example_cells.csv",
            "cpiv_r11_nearest_tick_rounding_examples.csv",
            "cpiv_r11_sub_tick_quote_examples.csv",
            *figures,
        ],
    }
    (output_dir / "cpiv_r11_price_resolution.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ticks", type=float, nargs="+", default=PRICE_TICK_LEVELS)
    parser.add_argument("--half-spreads", type=float, nargs="+", default=QUOTE_HALF_SPREAD_LEVELS)
    parser.add_argument("--roundoff-unit", type=float, default=UNIT_ROUNDOFF)
    parser.add_argument("--iv-tolerance-pp", type=float, default=DEFAULT_IV_TOLERANCE_PP)
    args = parser.parse_args()
    summary = write_r11_outputs(
        args.output, args.ticks, args.half_spreads, args.roundoff_unit, args.iv_tolerance_pp
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
