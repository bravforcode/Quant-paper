from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml
from research.cpiv.measurement.config import (
    check_licence,
    require_frozen,
    sha256_file,
)
from research.cpiv.measurement.errors import FreezeError, LicenceMissingError


def _write(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def _config(tmp_path: Path, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "role": "primary",
        "report_as_main_result": True,
        "licence_record": "licence.yaml",
    }
    payload.update(overrides)
    return _write(tmp_path / "config.yaml", payload)


def test_missing_licence_record_blocks_a_market_data_run(tmp_path: Path) -> None:
    config = _config(tmp_path, licence_record=None)
    with pytest.raises(LicenceMissingError, match="licence_record is null"):
        check_licence(yaml.safe_load(config.read_text()), config)


def test_licence_record_path_must_exist(tmp_path: Path) -> None:
    config = _config(tmp_path)
    with pytest.raises(LicenceMissingError, match="not found"):
        check_licence(yaml.safe_load(config.read_text()), config)


def test_incomplete_licence_record_is_rejected(tmp_path: Path) -> None:
    _write(
        tmp_path / "licence.yaml",
        {"vendor": "example", "permitted_outputs": ["aggregate_publication"]},
    )
    config = _config(tmp_path)
    with pytest.raises(LicenceMissingError, match="missing fields: expires"):
        check_licence(yaml.safe_load(config.read_text()), config)


def test_licence_must_permit_aggregate_publication(tmp_path: Path) -> None:
    _write(
        tmp_path / "licence.yaml",
        {
            "vendor": "example",
            "permitted_outputs": ["internal_research"],
            "expires": "2099-01-01",
        },
    )
    config = _config(tmp_path)
    with pytest.raises(LicenceMissingError, match="aggregate_publication"):
        check_licence(yaml.safe_load(config.read_text()), config)


def test_expired_licence_is_rejected(tmp_path: Path) -> None:
    _write(
        tmp_path / "licence.yaml",
        {
            "vendor": "example",
            "permitted_outputs": ["aggregate_publication"],
            "expires": "2020-01-01",
        },
    )
    config = _config(tmp_path)
    with pytest.raises(LicenceMissingError, match="expired"):
        check_licence(yaml.safe_load(config.read_text()), config, today=date(2026, 10, 22))


def test_valid_licence_returns_the_record(tmp_path: Path) -> None:
    _write(
        tmp_path / "licence.yaml",
        {
            "vendor": "example",
            "permitted_outputs": ["aggregate_publication"],
            "expires": "2027-01-01",
        },
    )
    config = _config(tmp_path)
    record = check_licence(
        yaml.safe_load(config.read_text()), config, today=date(2026, 10, 22)
    )
    assert record["vendor"] == "example"


def _prereg(tmp_path: Path, status: str, config_hash: str) -> Path:
    text = (
        "# Pre-registration\n\n"
        "```yaml\n"
        f"status: {status}\n"
        f'frozen_config_hash: "{config_hash}"\n'
        "```\n"
    )
    path = tmp_path / "preregistration.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_primary_run_is_refused_while_the_protocol_is_a_draft(tmp_path: Path) -> None:
    config = _config(tmp_path)
    prereg = _prereg(tmp_path, "DRAFT — NOT FROZEN", sha256_file(config))
    with pytest.raises(FreezeError, match="FROZEN"):
        require_frozen(yaml.safe_load(config.read_text()), config, prereg)


def test_pilot_run_is_allowed_while_the_protocol_is_a_draft(tmp_path: Path) -> None:
    config = _config(tmp_path, role="pilot", report_as_main_result=False)
    prereg = _prereg(tmp_path, "DRAFT — NOT FROZEN", "unused")
    assert require_frozen(yaml.safe_load(config.read_text()), config, prereg) is False


def test_frozen_protocol_requires_the_matching_config_hash(tmp_path: Path) -> None:
    config = _config(tmp_path)
    prereg = _prereg(tmp_path, "FROZEN", "0" * 64)
    with pytest.raises(FreezeError, match="does not match"):
        require_frozen(yaml.safe_load(config.read_text()), config, prereg)


def test_frozen_protocol_with_matching_hash_is_allowed(tmp_path: Path) -> None:
    config = _config(tmp_path)
    prereg = _prereg(tmp_path, "FROZEN", sha256_file(config))
    assert require_frozen(yaml.safe_load(config.read_text()), config, prereg) is True
