"""Calibration input set: the declared secondary outcome.

At each declared tolerance the study reports two things only:

1. how many contracts remain available to a surface calibration under the
   raw-midpoint input set and under the protocol's input set; and
2. how the fitted surface differs between those two input sets.

The fit is a quadratic in log-moneyness, fitted separately inside each expiry
slice, on the CPIV surface. It is descriptive: nothing here says which surface
is better specified, tradeable, or profitable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

SURFACE_FIT_DESCRIPTION = "quadratic in log-moneyness, per expiry slice, on the CPIV surface"


@dataclass(frozen=True)
class SurfaceFit:
    """One fitted slice: coefficients, the contracts used, and the slice key."""

    slice_key: str
    coefficients: tuple[float, float, float]
    contracts: int

    def evaluate(self, log_moneyness: float) -> float:
        a0, a1, a2 = self.coefficients
        return a0 + a1 * log_moneyness + a2 * log_moneyness * log_moneyness


def _solve3(matrix: list[list[float]], rhs: list[float]) -> list[float] | None:
    """Gaussian elimination with partial pivoting for a 3x3 system."""
    size = 3
    augmented = [row[:] + [rhs[index]] for index, row in enumerate(matrix)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            return None
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        for row in range(column + 1, size):
            factor = augmented[row][column] / augmented[column][column]
            for col in range(column, size + 1):
                augmented[row][col] -= factor * augmented[column][col]
    solution = [0.0] * size
    for row in range(size - 1, -1, -1):
        total = augmented[row][size]
        for col in range(row + 1, size):
            total -= augmented[row][col] * solution[col]
        solution[row] = total / augmented[row][row]
    return solution


def fit_quadratic(slice_key: str, points: Sequence[tuple[float, float]]) -> SurfaceFit | None:
    """Least-squares fit of a quadratic in log-moneyness, or None if degenerate."""
    if len(points) < 4:
        return None
    matrix = [[0.0] * 3 for _ in range(3)]
    rhs = [0.0] * 3
    for x_value, y_value in points:
        basis = (1.0, x_value, x_value * x_value)
        for i in range(3):
            for j in range(3):
                matrix[i][j] += basis[i] * basis[j]
            rhs[i] += basis[i] * y_value
    solution = _solve3(matrix, rhs)
    if solution is None:
        return None
    return SurfaceFit(
        slice_key=slice_key,
        coefficients=(solution[0], solution[1], solution[2]),
        contracts=len(points),
    )


def _fit_by_slice(
    points: Mapping[str, list[tuple[float, float]]]
) -> dict[str, SurfaceFit]:
    fits: dict[str, SurfaceFit] = {}
    for slice_key, slice_points in points.items():
        fit = fit_quadratic(slice_key, slice_points)
        if fit is not None:
            fits[slice_key] = fit
    return fits


def _points_by_slice(
    values: Mapping[str, float], log_moneyness: Mapping[str, float], slice_key: Mapping[str, str]
) -> dict[str, list[tuple[float, float]]]:
    points: dict[str, list[tuple[float, float]]] = {}
    for pair_id, value in values.items():
        key = slice_key[pair_id]
        points.setdefault(key, []).append((log_moneyness[pair_id], value))
    return points


def compare_surfaces(
    raw_values: Mapping[str, float],
    protocol_values: Mapping[str, float],
    log_moneyness: Mapping[str, float],
    slice_key: Mapping[str, str],
) -> dict[str, object]:
    """Compare the fitted surface from two input sets, slice by slice.

    The two fits are evaluated on the log-moneyness grid that the *raw* input
    set occupies, so the comparison does not depend on which contracts the
    protocol happened to keep.
    """
    raw_points = _points_by_slice(raw_values, log_moneyness, slice_key)
    protocol_points = _points_by_slice(protocol_values, log_moneyness, slice_key)
    raw_fits = _fit_by_slice(raw_points)
    protocol_fits = _fit_by_slice(protocol_points)
    rows: list[dict[str, object]] = []
    raw_total = 0
    protocol_total = 0
    changes: list[float] = []
    for key in sorted(raw_points):
        raw_fit = raw_fits.get(key)
        protocol_fit = protocol_fits.get(key)
        if raw_fit is None or protocol_fit is None:
            continue
        grid = sorted({x for x, _ in raw_points[key]})
        differences = [
            abs(protocol_fit.evaluate(x) - raw_fit.evaluate(x)) for x in grid
        ]
        raw_count = len(raw_points[key])
        protocol_count = len(protocol_points.get(key, []))
        raw_total += raw_count
        protocol_total += protocol_count
        max_change = max(differences) if differences else 0.0
        changes.append(max_change)
        rows.append(
            {
                "slice": key,
                "raw_contracts": raw_count,
                "protocol_contracts": protocol_count,
                "contracts_forgone": raw_count - protocol_count,
                "max_surface_change_pp": max_change,
                "mean_surface_change_pp": (
                    sum(differences) / len(differences) if differences else 0.0
                ),
            }
        )
    return {
        "fit": SURFACE_FIT_DESCRIPTION,
        "slices": rows,
        "raw_contracts": raw_total,
        "protocol_contracts": protocol_total,
        "contracts_forgone": raw_total - protocol_total,
        "coverage_retained": (
            protocol_total / raw_total if raw_total else 0.0
        ),
        "max_slice_surface_change_pp": max(changes) if changes else 0.0,
    }
