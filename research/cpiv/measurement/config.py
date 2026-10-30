"""Configuration, licence gate and freeze guard.

A market-data run is impossible without a written licence record that names the
vendor, permits aggregate publication, and has not expired. Primary and holdout
runs additionally require a frozen preregistration whose recorded config hash
matches the file on disk.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import yaml
from research.cpiv.measurement.errors import (
    ConfigError,
    FreezeError,
    LicenceMissingError,
)

FROZEN_STATUS = "FROZEN"
REQUIRED_PERMISSION = "aggregate_publication"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def load_config(path: str | Path) -> dict[str, object]:
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigError(f"configuration not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError(f"configuration must be a mapping: {config_path}")
    return data


def check_licence(
    config: Mapping[str, object],
    config_path: str | Path,
    today: date | None = None,
) -> dict[str, object]:
    """Return the licence record or raise LicenceMissingError."""
    record_ref = config.get("licence_record")
    if not record_ref:
        raise LicenceMissingError(
            "licence_record is null: market-data runs require a written licence"
        )
    record_path = Path(str(record_ref))
    if not record_path.is_absolute():
        record_path = Path(config_path).parent / record_path
    if not record_path.is_file():
        raise LicenceMissingError(f"licence record not found: {record_path}")
    record = yaml.safe_load(record_path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise LicenceMissingError(f"licence record must be a mapping: {record_path}")
    missing = [
        key for key in ("vendor", "permitted_outputs", "expires") if key not in record
    ]
    if missing:
        raise LicenceMissingError(
            f"licence record missing fields: {', '.join(sorted(missing))}"
        )
    permitted = record["permitted_outputs"]
    if isinstance(permitted, str) or not isinstance(permitted, list):
        raise LicenceMissingError("permitted_outputs must be a list")
    if REQUIRED_PERMISSION not in permitted:
        raise LicenceMissingError(
            f"licence does not permit {REQUIRED_PERMISSION}"
        )
    try:
        expires = date.fromisoformat(str(record["expires"]))
    except ValueError as exc:
        raise LicenceMissingError("licence expires must be ISO YYYY-MM-DD") from exc
    moment = today or date.today()
    if expires < moment:
        raise LicenceMissingError(f"licence expired on {expires.isoformat()}")
    return record


_FRONT_MATTER = re.compile(r"```(?:yaml)?\s*\n(.*?)```", re.DOTALL)


def parse_front_matter(text: str) -> dict[str, object]:
    match = _FRONT_MATTER.search(text)
    if match is None:
        raise ConfigError("preregistration has no fenced metadata block")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ConfigError("preregistration metadata must be a mapping")
    return data


def load_preregistration(path: str | Path) -> dict[str, object]:
    return parse_front_matter(Path(path).read_text(encoding="utf-8"))


def require_frozen(
    config: Mapping[str, object],
    config_path: str | Path,
    preregistration_path: str | Path,
) -> bool:
    """Allow a draft pilot, refuse primary and holdout without a matching freeze."""
    role = config.get("role")
    if role not in ("pilot", "primary", "holdout"):
        raise ConfigError(f"unknown role: {role!r}")
    metadata = load_preregistration(preregistration_path)
    status = metadata.get("status")
    if status != FROZEN_STATUS:
        if role == "pilot" and config.get("report_as_main_result") is not True:
            return False
        raise FreezeError(
            f"preregistration status is {status!r}; {role} runs require {FROZEN_STATUS}"
        )
    recorded = metadata.get("frozen_config_hash")
    actual = sha256_file(config_path)
    if recorded != actual:
        raise FreezeError(
            "configuration hash does not match the frozen preregistration"
        )
    return True
