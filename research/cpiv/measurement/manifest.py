"""Run manifests: every reported table traces to a configuration and inputs."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path

REQUIRED_FIELDS = (
    "git_sha",
    "config_sha256",
    "raw_sha256",
    "environment_sha256",
    "generated_at_utc",
    "seed",
    "os",
    "python",
    "output_sha256",
    "licence_mode",
    "status_counts",
)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_sha(repo_root: str | Path | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _hashes(paths: Iterable[str | Path]) -> dict[str, str]:
    return {str(path): sha256_file(path) for path in paths}


def build_manifest(
    *,
    config_path: str | Path,
    raw_paths: Iterable[str | Path] = (),
    environment_path: str | Path | None = None,
    seed: int | None = None,
    outputs: Iterable[str | Path] = (),
    licence_mode: str,
    status_counts: Mapping[str, int],
    generated_at: datetime | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    """Build a manifest containing every required provenance field."""
    environment = (
        sha256_file(environment_path)
        if environment_path is not None and Path(environment_path).is_file()
        else "absent"
    )
    moment = generated_at or datetime.now(UTC)
    return {
        "git_sha": git_sha(repo_root),
        "config_sha256": sha256_file(config_path),
        "raw_sha256": _hashes(raw_paths),
        "environment_sha256": environment,
        "generated_at_utc": moment.astimezone(UTC).isoformat(),
        "seed": seed,
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "output_sha256": _hashes(outputs),
        "licence_mode": licence_mode,
        "status_counts": dict(status_counts),
    }


def write_manifest(path: str | Path, manifest: Mapping[str, object]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
