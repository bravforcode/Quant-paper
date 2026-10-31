from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml
from research.cpiv.measurement.errors import ConfigError, LicenceMissingError
from research.cpiv.measurement.replay import (
    DEFAULT_FIXTURE,
    DEFAULT_SCHEMA,
    REJECT_BAD_TIMESTAMP,
    REJECT_MISSING_FIELD,
    REJECT_UNPAIRED,
    REJECT_UNKNOWN_COLUMN,
    assert_source_allowed,
    load_schema,
    load_vendor_rows,
    pair_rows,
    parse_timestamp,
    replay_report,
    write_vendor_fixture,
)


@pytest.fixture(scope="module")
def schema() -> object:
    return load_schema(DEFAULT_SCHEMA)


def test_the_schema_declares_the_vendor_shape(schema: object) -> None:
    assert schema.vendor == "SYNTHETIC-SHAPE-0"
    assert schema.price_scale == 100.0
    assert schema.timestamp_format == "iso8601_utc"
    assert schema.option_type_codes["C"] == "call"


def test_timestamps_are_always_timezone_aware() -> None:
    moment = parse_timestamp("2026-01-05T15:55:00.123456Z", "iso8601_utc")
    assert moment.tzinfo is not None
    assert moment.microsecond == 123456
    epoch = parse_timestamp("1767621300000", "epoch_millis")
    assert epoch.tzinfo is not None


def test_the_fixture_is_written_and_read_back(schema: object, tmp_path: Path) -> None:
    target = tmp_path / "fixture.csv"
    written = write_vendor_fixture(target, schema)
    assert written > 0
    frame = load_vendor_rows(target, schema)
    assert frame.rows_read == written
    assert len(frame.rows) + sum(frame.rejections.values()) == written


def test_the_committed_fixture_is_readable(schema: object) -> None:
    frame = load_vendor_rows(DEFAULT_FIXTURE, schema)
    assert frame.rows_read > 0
    assert len(frame.rows) > 0


def test_unreadable_rows_are_counted_not_dropped(schema: object) -> None:
    frame = load_vendor_rows(DEFAULT_FIXTURE, schema)
    assert frame.rejections.get(REJECT_UNKNOWN_COLUMN, 0) > 0
    assert frame.rejections.get(REJECT_BAD_TIMESTAMP, 0) > 0
    assert frame.rejections.get(REJECT_MISSING_FIELD, 0) > 0
    assert len(frame.rows) + sum(frame.rejections.values()) == frame.rows_read
    _pairs, pair_rejections = pair_rows(frame, schema)
    assert pair_rejections.get(REJECT_UNPAIRED, 0) > 0


def test_a_file_missing_a_declared_column_is_refused(schema: object, tmp_path: Path) -> None:
    target = tmp_path / "thin.csv"
    target.write_text("root_symbol,option_type\nA,C\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="missing declared columns"):
        load_vendor_rows(target, schema)


def test_the_replay_reaches_every_terminal_status(schema: object) -> None:
    frame = load_vendor_rows(DEFAULT_FIXTURE, schema)
    pairs, pair_rejections = pair_rows(frame, schema)
    report = replay_report(
        pairs, frame.rejections, pair_rejections, schema, frame.rows_read, len(frame.rows)
    )
    counts = report["reconciliation"]["terminal_counts"]
    assert isinstance(counts, dict)
    for status in (
        "resolved_within_tolerance",
        "identified_outside_tolerance",
        "partially_resolved",
        "unresolved",
        "invalid_input",
        "timing_mismatch",
        "contract_mismatch",
    ):
        assert counts.get(status, 0) > 0, status
    assert report["market_data_used"] is False


def test_a_fixture_source_needs_no_licence(tmp_path: Path) -> None:
    assert assert_source_allowed("fixture", DEFAULT_SCHEMA) == "synthetic-no-market-data"


def test_a_licensed_source_without_a_record_is_refused(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        yaml.safe_dump({"role": "primary", "licence_record": None}), encoding="utf-8"
    )
    with pytest.raises(LicenceMissingError, match="licence_record is null"):
        assert_source_allowed("licensed", config, today=date(2026, 10, 22))


def test_an_unknown_source_kind_is_refused(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump({"role": "primary"}), encoding="utf-8")
    with pytest.raises(ConfigError, match="unknown source_kind"):
        assert_source_allowed("scrape", config)
