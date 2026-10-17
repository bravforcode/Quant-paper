"""Gaussian benchmarks and multiplicity-adjusted checks for the ranking stress test.

For signals x and iid N(0, s^2) noise, the closed forms are:

* a pair with gap Delta is inverted with probability Phi(-Delta / (s*sqrt(2)));
* name i has the correct sign with probability Phi(|x_i| / s);
* expected Spearman correlation follows from pairwise and bivariate-orthant
  probabilities (see ``expected_spearman``).

Turnover and exact-order probability have no closed form here; they are estimated
with ``MC_DRAWS`` draws and reported with Monte Carlo standard errors.

Holm family (declared before any output was inspected): every row of
``ranking_benchmark.csv`` -- 90 Gaussian closed-form-versus-Monte-Carlo comparisons
(10 cells x 3 scales x {inversion, sign accuracy, Spearman}) and 960 fresh-versus-stored
comparisons (240 cells x 4 metrics) -- 1,050 two-sided tests at alpha 0.05.

Everything here is an author-run synthetic check. It is not an independent replication,
and the non-Gaussian comparisons are simulation against simulation.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np
from research.cpiv import r10_diagnostics as diag

FRESH_SEEDS = (31415926, 27182818, 16180339)
SCALE_PP = 0.5
MC_DRAWS = 1_000_000
MC_SEED = 20261017
ALPHA = 0.05
_PHI = NormalDist().cdf
_ERFC = np.vectorize(math.erfc, otypes=[float])
_GL_NODES, _GL_WEIGHTS = np.polynomial.legendre.leggauss(40)
_FRESH_STORED_METRICS = (
    ("inversion", "mean_pairwise_inversion_fraction"),
    ("spearman", "mean_spearman_rank_correlation"),
    ("turnover", "mean_top_bottom_membership_turnover"),
    ("sign_accuracy", "mean_sign_accuracy"),
)
_STATUS = "author-run synthetic check; not independent replication"


def _ndtr(x: Any) -> Any:
    return 0.5 * _ERFC(-np.asarray(x, dtype=float) / math.sqrt(2.0))


def analytic(signals: list[float], scale: float = SCALE_PP) -> tuple[float, float]:
    n = len(signals)
    pairs = n * (n - 1) / 2
    inversion = (
        sum(
            _PHI(-abs(signals[i] - signals[j]) / (scale * math.sqrt(2.0)))
            for i in range(n)
            for j in range(i + 1, n)
        )
        / pairs
    )
    sign = sum(_PHI(abs(v) / scale) for v in signals) / n
    return inversion, sign


def bivariate_normal_cdf(a: Any, b: Any, rho: float) -> Any:
    """P(Z1 <= a, Z2 <= b) for standard normals with correlation rho, |rho| < 1.

    Plackett's identity Phi2(a, b; rho) = Phi(a)Phi(b) + int_0^rho phi2(a, b; r) dr,
    with the integral evaluated by 40-node Gauss-Legendre quadrature. Broadcasts over a and b.
    """
    if not -1.0 < rho < 1.0:
        raise ValueError("rho must lie strictly inside (-1, 1)")
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    r = 0.5 * rho * (_GL_NODES + 1.0)
    weights = 0.5 * rho * _GL_WEIGHTS
    a_col = a_arr[..., None]
    b_col = b_arr[..., None]
    exponent = -(a_col * a_col - 2.0 * r * a_col * b_col + b_col * b_col) / (2.0 * (1.0 - r * r))
    density = np.exp(exponent) / (2.0 * np.pi * np.sqrt(1.0 - r * r))
    return _ndtr(a_arr) * _ndtr(b_arr) + density @ weights


def expected_spearman(signals: list[float], scale: float = SCALE_PP) -> float:
    """Exact E[Spearman] between observed and true ranks under iid Gaussian noise.

    With S_i the true rank and R_i the observed rank of name i, E[R_i] = 1 + A_i and
    E[R_i^2] = 1 + 3A_i + Q_i, where A_i = sum_{j!=i} Phi(g_ij) and
    Q_i = sum_{j!=k, both != i} Phi2(g_ij, g_ik; 1/2), with g_ij = (x_i - x_j)/(s*sqrt(2)).
    The correlation 1/2 is the covariance of y_i - y_j and y_i - y_k divided by 2s^2.
    Then E[rho] = 1 - 6 E[sum (R_i - S_i)^2] / (n (n^2 - 1)).
    """
    x = np.asarray(signals, dtype=float)
    n = x.size
    if n < 2:
        raise ValueError("at least two names are required")
    if np.unique(x).size != n:
        raise ValueError("signals must be distinct")
    true_rank = np.argsort(np.argsort(x)) + 1.0
    g = (x[:, None] - x[None, :]) / (scale * math.sqrt(2.0))
    off_diagonal = ~np.eye(n, dtype=bool)
    a_term = np.where(off_diagonal, _ndtr(g), 0.0).sum(axis=1)
    q_term = np.zeros(n)
    for i in range(n):
        others = np.flatnonzero(off_diagonal[i])
        g_i = g[i, others]
        pair = bivariate_normal_cdf(g_i[:, None], g_i[None, :], 0.5)
        np.fill_diagonal(pair, 0.0)
        q_term[i] = pair.sum()
    expected_sum_sq = np.sum(
        1.0 + 3.0 * a_term + q_term - 2.0 * true_rank * (1.0 + a_term) + true_rank**2
    )
    return float(1.0 - 6.0 * expected_sum_sq / (n * (n * n - 1)))


def simulate_gaussian(
    signals: list[float],
    scale: float = SCALE_PP,
    draws: int = MC_DRAWS,
    seed: int = MC_SEED,
    chunk: int = 10_000,
) -> dict[str, tuple[float, float]]:
    """Vectorised Gaussian simulation returning (mean, MC standard error) per metric."""
    x = np.asarray(signals, dtype=float)
    n = x.size
    k = max(1, n // 5)
    rng = np.random.default_rng(seed)
    true_order = np.argsort(x)
    true_rank = np.argsort(true_order)
    true_top = np.zeros(n, dtype=bool)
    true_top[true_order[n - k:]] = True
    true_bottom = np.zeros(n, dtype=bool)
    true_bottom[true_order[:k]] = True
    positions = np.arange(n)
    true_sign = x > 0
    collected: dict[str, list[np.ndarray]] = {
        key: [] for key in ("inversion", "spearman", "turnover", "sign", "exact")
    }
    for start in range(0, draws, chunk):
        m = min(chunk, draws - start)
        y = x + scale * rng.standard_normal((m, n))
        order = np.argsort(y, axis=1)
        perm = true_rank[order]
        inversions = np.triu(perm[:, :, None] > perm[:, None, :], k=1).sum(axis=(1, 2))
        collected["inversion"].append(inversions / (n * (n - 1) / 2))
        squared = np.sum((positions - perm) ** 2, axis=1)
        collected["spearman"].append(1.0 - 6.0 * squared / (n * (n * n - 1)))
        hits = true_top[order[:, n - k:]].sum(axis=1) + true_bottom[order[:, :k]].sum(axis=1)
        collected["turnover"].append(1.0 - hits / (2.0 * k))
        collected["sign"].append(np.mean((y > 0) == true_sign, axis=1))
        collected["exact"].append(np.all(perm == positions, axis=1).astype(float))
    result: dict[str, tuple[float, float]] = {}
    for key, parts in collected.items():
        values = np.concatenate(parts)
        result[key] = (float(values.mean()), float(values.std(ddof=1) / math.sqrt(values.size)))
    return result


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, returned in the input order."""
    m = len(p_values)
    order = sorted(range(m), key=lambda index: p_values[index])
    adjusted = [0.0] * m
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p_values[index]))
        adjusted[index] = running
    return adjusted


def exact_gaussian_rows(draws: int = MC_DRAWS) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scale_index, scale in enumerate(diag.NOISE_SDS_PP):
        for n in diag.UNIVERSE_SIZES:
            for family in diag.SIGNAL_FAMILIES:
                signals = diag._signals(n, family)
                inversion, sign = analytic(signals, scale)
                seed = MC_SEED + 1000 * n + diag.SIGNAL_FAMILIES.index(family) * 10 + scale_index
                mc = simulate_gaussian(signals, scale, draws=draws, seed=seed)
                rows.append({
                    "universe_n": n,
                    "signal_family": family,
                    "noise_family": "gaussian",
                    "configured_noise_scale_pp": scale,
                    "mc_draws": draws,
                    "mc_seed": seed,
                    "inversion_analytic": inversion,
                    "inversion_mc": mc["inversion"][0],
                    "inversion_mcse": mc["inversion"][1],
                    "sign_accuracy_analytic": sign,
                    "sign_accuracy_mc": mc["sign"][0],
                    "sign_accuracy_mcse": mc["sign"][1],
                    "spearman_exact": expected_spearman(signals, scale),
                    "spearman_mc": mc["spearman"][0],
                    "spearman_mcse": mc["spearman"][1],
                    "turnover_mc": mc["turnover"][0],
                    "turnover_mcse": mc["turnover"][1],
                    "exact_order_probability_mc": mc["exact"][0],
                    "exact_order_mcse": mc["exact"][1],
                    "status": _STATUS,
                })
    return rows


def _check(
    comparison: str,
    metric: str,
    cell: tuple[int, str, str, float],
    reference: tuple[str, float, float],
    estimate: tuple[str, float, float],
) -> dict[str, Any]:
    n, signal_family, noise_family, scale = cell
    reference_source, reference_value, reference_se = reference
    estimate_source, estimate_value, estimate_se = estimate
    denominator = math.hypot(reference_se, estimate_se)
    difference = estimate_value - reference_value
    if denominator == 0.0:
        # Both sides are constant across replicates: equal values agree exactly,
        # unequal values are a deterministic difference (infinite z).
        z = 0.0 if difference == 0.0 else math.copysign(math.inf, difference)
    else:
        z = difference / denominator
    return {
        "comparison": comparison,
        "metric": metric,
        "universe_n": n,
        "signal_family": signal_family,
        "noise_family": noise_family,
        "configured_noise_scale_pp": scale,
        "reference_source": reference_source,
        "reference_value": float(reference_value),
        "reference_mcse": float(reference_se),
        "estimate_source": estimate_source,
        "estimate_value": float(estimate_value),
        "estimate_mcse": float(estimate_se),
        "z": float(z),
        "p_two_sided": float(2.0 * _PHI(-abs(z))),
    }


def ranking_rows(
    exact_rows: list[dict[str, Any]],
    fresh_rows: list[dict[str, Any]],
    stored_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for row in exact_rows:
        cell = (row["universe_n"], row["signal_family"], row["noise_family"],
                row["configured_noise_scale_pp"])
        for metric, reference, estimate, estimate_se in (
            ("inversion", row["inversion_analytic"], row["inversion_mc"], row["inversion_mcse"]),
            ("sign_accuracy", row["sign_accuracy_analytic"], row["sign_accuracy_mc"],
             row["sign_accuracy_mcse"]),
            ("spearman", row["spearman_exact"], row["spearman_mc"], row["spearman_mcse"]),
        ):
            checks.append(_check(
                "gaussian_closed_form_vs_mc",
                metric,
                cell,
                ("closed_form", reference, 0.0),
                ("mc_draws", estimate, estimate_se),
            ))
    stored_index = {
        (int(row["universe_n"]), row["signal_family"], row["noise_family"],
         float(row["configured_noise_scale_pp"])): row
        for row in stored_rows
    }
    if len(stored_index) != len(stored_rows):
        raise ValueError("stored rank table has duplicate cells")
    if len(fresh_rows) != len(stored_rows):
        raise ValueError("fresh and stored rank tables cover different cell counts")
    for row in fresh_rows:
        key = (int(row["universe_n"]), row["signal_family"], row["noise_family"],
               float(row["configured_noise_scale_pp"]))
        stored = stored_index.get(key)
        if stored is None:
            raise ValueError(f"no stored cell for {key}")
        for metric, field in _FRESH_STORED_METRICS:
            checks.append(_check(
                "fresh_vs_stored_simulation",
                metric,
                key[:3] + (key[3],),
                ("stored_r10_simulation", float(stored[field]), float(stored[field + "_mcse"])),
                ("fresh_simulation", float(row[field]), float(row[field + "_mcse"])),
            ))
    p_adjusted = holm_adjust([check["p_two_sided"] for check in checks])
    for check, adjusted in zip(checks, p_adjusted, strict=True):
        check["holm_adjusted_p"] = adjusted
        check["reject_holm_0_05"] = adjusted < ALPHA
        check["family_size"] = len(checks)
        check["status"] = _STATUS
    return checks


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stored", type=Path, required=True,
                        help="rank_noise_sensitivity.csv from the stored r10 run")
    parser.add_argument("--replicates-per-seed", type=int, default=1000)
    parser.add_argument("--mc-draws", type=int, default=MC_DRAWS)
    args = parser.parse_args()
    exact = exact_gaussian_rows(args.mc_draws)
    fresh, _, _ = diag.rank_sensitivity(args.replicates_per_seed, seeds=FRESH_SEEDS)
    with args.stored.open(encoding="utf-8", newline="") as handle:
        stored = list(csv.DictReader(handle))
    checks = ranking_rows(exact, fresh, stored)
    _write_csv(args.output / "gaussian_rank_benchmark.csv", exact)
    _write_csv(args.output / "ranking_benchmark.csv", checks)
    rejected = sum(bool(check["reject_holm_0_05"]) for check in checks)
    print(f"ranking_benchmark: {len(checks)} tests, {rejected} rejected after Holm at {ALPHA}")


if __name__ == "__main__":
    main()
