"""Figure 1: the selection frontier, and the coverage the sweep destroys.

Panel (a) plots the certified mean absolute error against the certification
tolerance on a log scale, with the pair-null 5th to 95th percentile band and
the day-block null mean beside it. Panel (b) plots certified coverage across
the ten market specifications; it is the picture of the R3 failure.

Both panels read the artefacts a run produced and nothing else. The file is
written twice, as a 300 dpi PNG for the Word source and as a vector PDF for
the typesetter, and the drawing is deterministic: fixed size, fixed colours,
no timestamp and no random layout.

Usage::

    .venv/Scripts/python.exe -m research.cpiv.measurement.figure_frontier
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
DEFAULT_STUDY = HERE / "outputs" / "study"
DEFAULT_SWEEP = HERE / "outputs" / "sweep"
DEFAULT_DIR = REPO_ROOT / "docs" / "cpiv-jcf" / "manuscript" / "figures"

#: Okabe-Ito palette: distinguishable in greyscale and for colour-vision
#: deficiency, which is what the publisher asks of submitted figures.
BLUE = "#0072B2"
VERMILLION = "#D55E00"
GREY = "#7A7A7A"

#: The order the paper discusses the specifications in.
SPECIFICATIONS = (
    ("base", "base"),
    ("low_vol", "low volatility"),
    ("high_vol", "high volatility"),
    ("no_wide_sessions", "no wide sessions"),
    ("wide_strike_grid", "wide strike grid"),
    ("long_dated", "long dated"),
    ("short_dated", "short dated"),
    ("wide_quotes", "wide quotes"),
    ("very_wide_quotes", "very wide quotes"),
    ("coarse_tick", "coarse tick"),
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _measurements(path: Path) -> dict[str, float]:
    import csv

    with path.open(newline="", encoding="utf-8") as handle:
        return {row["draw"]: float(row["coverage_certified"]) for row in csv.DictReader(handle)}


def draw(
    study_dir: Path = DEFAULT_STUDY,
    sweep_dir: Path = DEFAULT_SWEEP,
    directory: Path = DEFAULT_DIR,
) -> list[Path]:
    """Render the figure and return the files written."""
    study = _read(study_dir / "study_summary.json")
    frontier = [
        row
        for row in study.get("selection_frontier", [])
        if row.get("mae_certified_pp") is not None
        and row.get("null_q05_pp") is not None
    ]
    coverage = _measurements(sweep_dir / "specifications.csv")

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.linewidth": 0.6,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "legend.frameon": False,
            "figure.dpi": 300,
        }
    )
    figure, (left, right) = plt.subplots(1, 2, figsize=(7.0, 2.9))
    figure.subplots_adjust(left=0.085, right=0.985, top=0.93, bottom=0.21, wspace=0.28)

    # -- panel (a): the frontier ------------------------------------------
    tolerances = np.array([row["tolerance_pp"] for row in frontier], dtype=float)
    certified = np.array([row["mae_certified_pp"] for row in frontier], dtype=float)
    low = np.array([row["null_q05_pp"] for row in frontier], dtype=float)
    high = np.array([row["null_q95_pp"] for row in frontier], dtype=float)
    block = np.array([row["block_null_mean_pp"] for row in frontier], dtype=float)

    left.fill_between(
        tolerances, low, high, color=GREY, alpha=0.22, linewidth=0,
        label="pair null, 5th–95th percentile",
    )
    left.plot(tolerances, block, color=GREY, linestyle="--", linewidth=1.0,
              label="day-block null mean")
    left.plot(tolerances, certified, color=BLUE, marker="o", markersize=3.5,
              linewidth=1.3, label="certified subset")
    left.set_yscale("log")
    left.set_xscale("log")
    left.set_xlabel("certification tolerance (percentage points)")
    left.set_ylabel("mean absolute error (percentage points)")
    # A log x-axis would otherwise label its minor ticks inside the axis.
    left.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    left.set_xticks(list(tolerances))
    left.set_xticklabels([f"{value:g}" for value in tolerances])
    left.set_xlim(min(tolerances) * 0.82, max(tolerances) * 1.18)
    left.set_ylim(top=2.4)
    left.set_title("(a) the selection frontier", loc="left", fontsize=8)
    left.grid(axis="y", color="#DDDDDD", linewidth=0.5)
    left.set_axisbelow(True)
    left.legend(
        loc="upper left",
        handlelength=1.6,
        borderaxespad=0.2,
        frameon=True,
        framealpha=0.92,
        edgecolor="none",
    )
    primary = min(range(len(tolerances)), key=lambda i: abs(tolerances[i] - 0.10))
    left.annotate(
        f"n = {int(frontier[primary]['n_certified'])}",
        xy=(tolerances[primary], certified[primary]),
        xytext=(8, 6),
        textcoords="offset points",
        fontsize=7,
        color=BLUE,
    )

    # -- panel (b): coverage by specification ------------------------------
    labels = [label for key, label in SPECIFICATIONS if key in coverage]
    values = [100.0 * coverage[key] for key, _ in SPECIFICATIONS if key in coverage]
    positions = np.arange(len(labels))

    right.barh(positions, values, color=BLUE, height=0.62)
    right.set_yticks(positions)
    right.set_yticklabels(labels)
    right.invert_yaxis()
    right.set_xlabel("certified coverage (% of attempted pairs)")
    right.set_title("(b) coverage by market specification", loc="left", fontsize=8)
    right.grid(axis="x", color="#DDDDDD", linewidth=0.5)
    right.set_axisbelow(True)
    right.set_xlim(0, max(values) * 1.28)
    for position, value in zip(positions, values, strict=True):
        right.text(
            value + max(values) * 0.025,
            position,
            f"{value:.1f}",
            va="center",
            fontsize=6.5,
        )

    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for suffix, options in (("png", {"dpi": 300}), ("pdf", {})):
        path = directory / f"figure_1.{suffix}"
        figure.savefig(path, **options)
        written.append(path)
    plt.close(figure)
    return written


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-dir", type=Path, default=DEFAULT_STUDY)
    parser.add_argument("--sweep-dir", type=Path, default=DEFAULT_SWEEP)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args(argv)
    for path in draw(args.study_dir, args.sweep_dir, args.directory):
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
