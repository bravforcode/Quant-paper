"""Regenerate the synthetic CPIV methods-note outputs from a project checkout."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GENERATED_ROOT = ROOT / "research" / "cpiv" / "generated"
DEFAULT_OUTPUT = GENERATED_ROOT / "cpiv_methods_note_reproduction"
DEFAULT_IV_TOLERANCE_PP = 0.10


def _resolve_output(path: Path) -> Path:
    output = path if path.is_absolute() else ROOT / path
    output = output.resolve()
    generated_root = GENERATED_ROOT.resolve()
    if output == generated_root or not output.is_relative_to(generated_root):
        raise ValueError("output must be a child directory of research/cpiv/generated")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"output directory is not empty; choose a fresh path: {output}")
    return output


def _run_module(module: str, *arguments: str) -> None:
    command = [sys.executable, "-m", module, *arguments]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        raise subprocess.CalledProcessError(result.returncode, command)
    print(f"completed {module}")


def reproduce(
    output_path: Path, iv_tolerance_pp: float = DEFAULT_IV_TOLERANCE_PP
) -> dict[str, Any]:
    output = _resolve_output(output_path)
    output.mkdir(parents=True, exist_ok=True)
    output_arg = str(output)

    _run_module("research.cpiv.build_demo", "--output", output_arg, "--replicates", "2000")
    _run_module(
        "research.cpiv.r10_diagnostics",
        "--output",
        output_arg,
        "--replicates-per-seed",
        "100",
    )
    _run_module(
        "research.cpiv.gaussian_rank_benchmark",
        "--output",
        output_arg,
        "--stored",
        str(output / "rank_noise_sensitivity.csv"),
    )
    _run_module("research.cpiv.american_put_crosscheck", "--output", output_arg)
    _run_module("research.cpiv.workflow_comparison", "--output", output_arg)
    _run_module(
        "research.cpiv.reference_sensitivity",
        "--grid",
        str(output / "local_approximation_grid.csv"),
        "--output-dir",
        output_arg,
    )
    _run_module(
        "research.cpiv.r11_near_bound_audit",
        "--input",
        str(output / "iv_inversion_roundtrips.csv"),
        "--output",
        str(output / "near_bound_classification.csv"),
        "--summary",
        str(output / "near_bound_classification.json"),
    )
    _run_module(
        "research.cpiv.r11_near_bound_crosswalk",
        "--float-audit",
        str(output / "near_bound_classification.csv"),
        "--decimal-audit",
        str(output / "near_bound_decimal_audit.csv"),
        "--output",
        str(output / "near_bound_crosswalk.csv"),
        "--summary",
        str(output / "near_bound_crosswalk.json"),
    )
    _run_module("research.cpiv.r11_carry_forward", "--output", output_arg)
    _run_module(
        "research.cpiv.r11_price_resolution",
        "--output",
        output_arg,
        "--ticks",
        "0.0001",
        "0.001",
        "0.01",
        "0.1",
        "--half-spreads",
        "0.01",
        "0.02",
        "0.05",
        "0.1",
        "0.25",
        "--iv-tolerance-pp",
        str(iv_tolerance_pp),
    )
    _run_module(
        "research.cpiv.independent_bsm_crosscheck",
        "--output",
        str(output / "separately_coded_bsm_crosscheck.csv"),
    )

    price_summary = json.loads(
        (output / "cpiv_r11_price_resolution.json").read_text(encoding="utf-8")
    )
    diagnostics = json.loads(
        (output / "cpiv_r10_diagnostics.json").read_text(encoding="utf-8")
    )
    if price_summary.get("market_data_used") is not False:
        raise ValueError("price-resolution output is not marked synthetic-only")
    if diagnostics.get("market_data_used") is not False:
        raise ValueError("diagnostic output is not marked synthetic-only")
    if price_summary.get("iv_tolerance_pp") != iv_tolerance_pp:
        raise ValueError("generated output does not record the requested IV tolerance")

    figure_aliases = {
        "local_approximation_d3_scaling.png": "local_approximation_error.png",
        "cpiv_r10_american_convergence.png": "american_tree_convergence.png",
        "cpiv_r10_rank_sensitivity.png": "rank_sensitivity.png",
        "cpiv_r11_price_resolution_status_heatmap.png": "price_resolution_status_heatmap.png",
        "cpiv_r11_finite_shock_change_heatmap.png": "finite_shock_change_heatmap.png",
    }
    for source_name, release_name in figure_aliases.items():
        source = output / source_name
        if not source.is_file():
            raise FileNotFoundError(f"required generated figure is missing: {source.name}")
        shutil.copyfile(source, output / release_name)

    files = sorted(path.name for path in output.iterdir() if path.is_file())
    manifest = {
        "status": "synthetic_cpiv_reproduction_outputs",
        "market_data_used": False,
        "python_version": sys.version.split()[0],
        "iv_tolerance_pp": iv_tolerance_pp,
        "iv_tolerance_rule": price_summary["iv_tolerance_rule"],
        "figure_aliases": figure_aliases,
        "files": files,
    }
    (output / "reproduction_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--iv-tolerance-pp", type=float, default=DEFAULT_IV_TOLERANCE_PP)
    args = parser.parse_args()
    if args.iv_tolerance_pp < 0:
        parser.error("--iv-tolerance-pp must be nonnegative")
    result = reproduce(args.output, args.iv_tolerance_pp)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
