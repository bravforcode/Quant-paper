from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from research.cpiv.measurement.manifest import (
    REQUIRED_FIELDS,
    build_manifest,
    sha256_file,
    write_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    config = tmp_path / "config.yaml"
    config.write_text("role: synthetic\n", encoding="utf-8")
    raw = tmp_path / "raw.csv"
    raw.write_text("strike,expiry\n100,2026-01-01\n", encoding="utf-8")
    environment = tmp_path / "environment.lock"
    environment.write_text("python==3.14\n", encoding="utf-8")
    return config, raw, environment


def test_manifest_contains_every_required_field(tmp_path: Path) -> None:
    config, raw, environment = _fixture(tmp_path)
    manifest = build_manifest(
        config_path=config,
        raw_paths=[raw],
        environment_path=environment,
        seed=7,
        outputs=[raw],
        licence_mode="synthetic-no-market-data",
        status_counts={"resolved_within_tolerance": 2},
        generated_at=datetime(2026, 10, 22, tzinfo=UTC),
        repo_root=ROOT,
    )
    for field in REQUIRED_FIELDS:
        assert field in manifest
    assert manifest["config_sha256"] == sha256_file(config)
    assert manifest["raw_sha256"][str(raw)] == sha256_file(raw)
    assert manifest["output_sha256"][str(raw)] == sha256_file(raw)
    assert manifest["environment_sha256"] == sha256_file(environment)
    assert manifest["generated_at_utc"] == "2026-10-22T00:00:00+00:00"


def test_same_inputs_produce_the_same_output_hashes(tmp_path: Path) -> None:
    config, raw, environment = _fixture(tmp_path)
    first = build_manifest(
        config_path=config,
        raw_paths=[raw],
        environment_path=environment,
        seed=7,
        outputs=[raw],
        licence_mode="synthetic-no-market-data",
        status_counts={"resolved_within_tolerance": 2},
        generated_at=datetime(2026, 10, 22, tzinfo=UTC),
        repo_root=ROOT,
    )
    second = build_manifest(
        config_path=config,
        raw_paths=[raw],
        environment_path=environment,
        seed=7,
        outputs=[raw],
        licence_mode="synthetic-no-market-data",
        status_counts={"resolved_within_tolerance": 2},
        generated_at=datetime(2026, 10, 23, tzinfo=UTC),
        repo_root=ROOT,
    )
    assert first["output_sha256"] == second["output_sha256"]
    assert first["config_sha256"] == second["config_sha256"]
    assert first["generated_at_utc"] != second["generated_at_utc"]


def test_missing_environment_lock_is_recorded_as_absent(tmp_path: Path) -> None:
    config, raw, _ = _fixture(tmp_path)
    manifest = build_manifest(
        config_path=config,
        raw_paths=[raw],
        environment_path=tmp_path / "does-not-exist.lock",
        seed=None,
        outputs=[],
        licence_mode="synthetic-no-market-data",
        status_counts={},
        repo_root=ROOT,
    )
    assert manifest["environment_sha256"] == "absent"


def test_manifest_is_written_as_json(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    write_manifest(path, {"seed": 7, "status_counts": {}})
    assert json.loads(path.read_text(encoding="utf-8"))["seed"] == 7


def test_makefile_exposes_the_synthetic_reproduction_target() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "reproduce-synthetic:" in makefile
    assert "research.cpiv.measurement.synthetic" in makefile
