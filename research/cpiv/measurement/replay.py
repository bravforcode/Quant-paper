"""Vendor-schema replay: the ingestion path, exercised without market data.

Everything else in this package can be right and still fail on a real file,
because the real file is where the assumptions live. The vendor *shape* —
column names, price scale, timestamp format, option-type codes, missing-leg
markers, condition codes, and extra columns that must be ignored — is declared
in a configuration file, and a file with that shape is written and read back.

The loader is the same loader a licensed run would use; only the bytes are
synthetic. A licensed source is refused unless a licence record exists,
exactly as in :mod:`research.cpiv.measurement.config`, so the replay path
cannot become a back door around the gate.

Nothing here is evidence about a market. It is evidence that the ingestion
code reads a file of the expected shape, reports what it cannot read, and
never silently drops a row.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import yaml
from research.cpiv.measurement.config import check_licence
from research.cpiv.measurement.dgp import GeneratorConfig, generate_market
from research.cpiv.measurement.errors import ConfigError
from research.cpiv.measurement.quotes import QuotePair
from research.cpiv.measurement.status import PairRecord, TerminalStatus, funnel, reconcile
from research.cpiv.measurement.study import StudySettings, run_protocol

HERE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = HERE / "configs" / "vendor_replay.yaml"
DEFAULT_FIXTURE = HERE / "fixtures" / "vendor_shape_quotes.csv"
DEFAULT_OUTPUT = HERE / "outputs" / "replay"

REJECT_UNKNOWN_COLUMN = "unknown_option_type"
REJECT_MISSING_FIELD = "missing_required_field"
REJECT_BAD_TIMESTAMP = "unparseable_timestamp"
REJECT_BAD_NUMBER = "unparseable_number"
REJECT_BAD_DATE = "unparseable_expiry"
REJECT_NO_LEG = "leg_not_quoted"
REJECT_DUPLICATE = "duplicate_key"
REJECT_UNPAIRED = "unpaired_leg"
REJECT_SPOT_DISAGREEMENT = "underlying_disagreement"

TIMESTAMP_FORMATS = ("iso8601_utc", "epoch_millis")


@dataclass(frozen=True)
class VendorSchema:
    """The declared shape of a vendor quote file."""

    vendor: str
    columns: Mapping[str, str]
    price_scale: float
    timestamp_format: str
    option_type_codes: Mapping[str, str]
    condition_codes: Mapping[str, str]
    missing_markers: tuple[str, ...]
    rate: float
    dividend_yield: float
    tick: float
    resolution_ticks: float
    primary_tolerance_pp: float
    quote_sync_tolerance_seconds: float
    pairing_skew_seconds: float
    spot_relative_tolerance: float
    days_per_year: int = 365

    def column_for(self, field_name: str) -> str:
        try:
            return self.columns[field_name]
        except KeyError as exc:
            raise ConfigError(
                f"vendor schema has no column mapped to {field_name!r}"
            ) from exc


def load_schema(path: str | Path = DEFAULT_SCHEMA) -> VendorSchema:
    """Read the declared vendor schema from a configuration file."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigError(f"vendor schema not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError(f"vendor schema must be a mapping: {config_path}")
    schema_block = data.get("schema")
    protocol = data.get("protocol")
    if not isinstance(schema_block, dict) or not isinstance(protocol, dict):
        raise ConfigError("vendor schema needs a 'schema' and a 'protocol' block")
    columns = schema_block.get("columns")
    if not isinstance(columns, dict) or not columns:
        raise ConfigError("vendor schema needs a non-empty 'columns' mapping")
    codes = schema_block.get("option_type_codes")
    conditions = schema_block.get("condition_codes", {})
    if not isinstance(codes, dict) or not isinstance(conditions, dict):
        raise ConfigError("option_type_codes and condition_codes must be mappings")
    timestamp_format = str(schema_block.get("timestamp_format", "iso8601_utc"))
    if timestamp_format not in TIMESTAMP_FORMATS:
        raise ConfigError(
            f"timestamp_format must be one of {TIMESTAMP_FORMATS}, "
            f"not {timestamp_format!r}"
        )
    markers = schema_block.get("missing_markers", ["", "NaN", "NULL"])
    if not isinstance(markers, list):
        raise ConfigError("missing_markers must be a list")
    return VendorSchema(
        vendor=str(schema_block.get("vendor", "unnamed")),
        columns={str(key): str(value) for key, value in columns.items()},
        price_scale=float(schema_block.get("price_scale", 1.0)),
        timestamp_format=timestamp_format,
        option_type_codes={str(key): str(value) for key, value in codes.items()},
        condition_codes={str(key): str(value) for key, value in conditions.items()},
        missing_markers=tuple(str(marker) for marker in markers),
        rate=float(protocol.get("rate", 0.0)),
        dividend_yield=float(protocol.get("dividend_yield", 0.0)),
        tick=float(protocol.get("tick", 0.01)),
        resolution_ticks=float(protocol.get("resolution_ticks", 1.0)),
        primary_tolerance_pp=float(protocol.get("primary_tolerance_pp", 0.10)),
        quote_sync_tolerance_seconds=float(
            protocol.get("quote_sync_tolerance_seconds", 2.0)
        ),
        pairing_skew_seconds=float(protocol.get("pairing_skew_seconds", 2.0)),
        spot_relative_tolerance=float(protocol.get("spot_relative_tolerance", 1e-4)),
    )


def assert_source_allowed(
    source_kind: str, config_path: str | Path, today: date | None = None
) -> str:
    """Refuse a licensed source without a licence record; allow a fixture."""
    if source_kind == "fixture":
        return "synthetic-no-market-data"
    if source_kind == "licensed":
        check_licence(_config_mapping(config_path), config_path, today)
        return "licensed"
    raise ConfigError(f"unknown source_kind: {source_kind!r}")


def _config_mapping(config_path: str | Path) -> Mapping[str, object]:
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError(f"configuration must be a mapping: {config_path}")
    return data


# --- row normalisation ------------------------------------------------------


@dataclass
class VendorRow:
    """One normalised quote row from a vendor file."""

    root_id: str
    option_type: str
    underlying: str
    strike: float
    expiry: date
    multiplier: int
    exercise_style: str
    settlement: str
    bid: float
    ask: float
    quote_time: datetime
    spot: float
    spot_time: datetime
    condition: str
    source_row: int


@dataclass
class VendorFrame:
    """The rows that parsed, plus the reason every other row did not."""

    rows: list[VendorRow] = field(default_factory=list)
    rejections: dict[str, int] = field(default_factory=dict)
    rows_read: int = 0

    def reject(self, reason: str) -> None:
        self.rejections[reason] = self.rejections.get(reason, 0) + 1


def _is_missing(value: str | None, markers: Sequence[str]) -> bool:
    if value is None:
        return True
    stripped = value.strip()
    if not stripped:
        return True
    return stripped.upper() in {marker.strip().upper() for marker in markers if marker}


def parse_timestamp(value: str, timestamp_format: str) -> datetime:
    """Parse one timestamp in the declared format, always timezone-aware."""
    text = value.strip()
    if timestamp_format == "epoch_millis":
        return datetime.fromtimestamp(int(text) / 1000.0, tz=UTC)
    normalised = text.replace("Z", "+00:00")
    moment = datetime.fromisoformat(normalised)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def _parse_number(value: str, scale: float, markers: Sequence[str]) -> float | None:
    if _is_missing(value, markers):
        return None
    try:
        return float(value) / scale
    except ValueError:
        return None


def _parse_date(value: str) -> date | None:
    text = value.strip()
    for pattern in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def load_vendor_rows(path: str | Path, schema: VendorSchema) -> VendorFrame:
    """Read and normalise a vendor file; every unreadable row is counted."""
    source = Path(path)
    if not source.is_file():
        raise ConfigError(f"vendor file not found: {source}")
    frame = VendorFrame()
    seen: set[tuple[str, str, str]] = set()
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ConfigError(f"vendor file has no header: {source}")
        absent = sorted(set(schema.columns.values()) - set(reader.fieldnames))
        if absent:
            raise ConfigError(
                f"vendor file is missing declared columns: {', '.join(absent)}"
            )
        for index, raw in enumerate(reader):
            frame.rows_read += 1
            option_type = schema.option_type_codes.get(
                str(raw.get(schema.column_for("option_type"), "")).strip()
            )
            if option_type is None:
                frame.reject(REJECT_UNKNOWN_COLUMN)
                continue
            strike = _parse_number(
                str(raw.get(schema.column_for("strike"), "")), 1.0, schema.missing_markers
            )
            bid = _parse_number(
                str(raw.get(schema.column_for("bid"), "")),
                schema.price_scale,
                schema.missing_markers,
            )
            ask = _parse_number(
                str(raw.get(schema.column_for("ask"), "")),
                schema.price_scale,
                schema.missing_markers,
            )
            spot = _parse_number(
                str(raw.get(schema.column_for("spot"), "")),
                schema.price_scale,
                schema.missing_markers,
            )
            if strike is None or bid is None or ask is None or spot is None:
                frame.reject(REJECT_BAD_NUMBER)
                continue
            if bid <= 0.0 and ask <= 0.0:
                frame.reject(REJECT_NO_LEG)
                continue
            expiry = _parse_date(str(raw.get(schema.column_for("expiry"), "")))
            if expiry is None:
                frame.reject(REJECT_BAD_DATE)
                continue
            try:
                quote_time = parse_timestamp(
                    str(raw.get(schema.column_for("quote_time"), "")),
                    schema.timestamp_format,
                )
                spot_time = parse_timestamp(
                    str(raw.get(schema.column_for("spot_time"), "")),
                    schema.timestamp_format,
                )
            except (ValueError, TypeError, OSError):
                frame.reject(REJECT_BAD_TIMESTAMP)
                continue
            underlying = str(raw.get(schema.column_for("underlying"), "")).strip()
            root_id = str(raw.get(schema.column_for("root_id"), "")).strip()
            if not underlying or not root_id:
                frame.reject(REJECT_MISSING_FIELD)
                continue
            try:
                multiplier = int(
                    float(str(raw.get(schema.column_for("multiplier"), "100")).strip())
                )
            except ValueError:
                frame.reject(REJECT_BAD_NUMBER)
                continue
            identity = (root_id, option_type, quote_time.isoformat())
            if identity in seen:
                frame.reject(REJECT_DUPLICATE)
                continue
            seen.add(identity)
            frame.rows.append(
                VendorRow(
                    root_id=root_id,
                    option_type=option_type,
                    underlying=underlying,
                    strike=strike,
                    expiry=expiry,
                    multiplier=multiplier,
                    exercise_style=str(
                        raw.get(schema.column_for("exercise_style"), "") or ""
                    ).strip(),
                    settlement=str(
                        raw.get(schema.column_for("settlement"), "") or ""
                    ).strip(),
                    bid=bid,
                    ask=ask,
                    quote_time=quote_time,
                    spot=spot,
                    spot_time=spot_time,
                    condition=str(
                        raw.get(schema.column_for("condition"), "") or ""
                    ).strip(),
                    source_row=index,
                )
            )
    return frame


# --- pairing ----------------------------------------------------------------


@dataclass
class ReplayPair:
    """One formed pair, before it enters the protocol."""

    pair: QuotePair
    condition: str
    note: str | None = None


def pair_rows(
    frame: VendorFrame, schema: VendorSchema
) -> tuple[list[ReplayPair], dict[str, int]]:
    """Pair call and put legs on contract identity, keeping every rejection.

    Legs are matched on the vendor's contract root, and each call is matched
    with the nearest put inside the declared pairing skew. A call with no put
    inside the skew, or a put never matched, is counted as an unpaired leg
    rather than dropped.
    """
    by_root: dict[str, list[VendorRow]] = {}
    for row in frame.rows:
        by_root.setdefault(row.root_id, []).append(row)
    counts: dict[str, int] = {}
    pairs: list[ReplayPair] = []
    for root_id in sorted(by_root):
        rows = by_root[root_id]
        calls = [row for row in rows if row.option_type == "call"]
        puts = [row for row in rows if row.option_type == "put"]
        used: set[int] = set()
        for call in calls:
            best: VendorRow | None = None
            best_gap = float("inf")
            for put in puts:
                if put.source_row in used:
                    continue
                gap = abs((put.quote_time - call.quote_time).total_seconds())
                if gap <= schema.pairing_skew_seconds and gap < best_gap:
                    best, best_gap = put, gap
            if best is None:
                counts[REJECT_UNPAIRED] = counts.get(REJECT_UNPAIRED, 0) + 1
                continue
            used.add(best.source_row)
            if abs(best.spot - call.spot) > schema.spot_relative_tolerance * call.spot:
                counts[REJECT_SPOT_DISAGREEMENT] = (
                    counts.get(REJECT_SPOT_DISAGREEMENT, 0) + 1
                )
                continue
            snapshot = max(call.quote_time, best.quote_time)
            days = max((call.expiry - snapshot.date()).days, 0)
            note: str | None = None
            if abs(best.strike - call.strike) > 1e-9:
                note = "put strike differs from call strike"
            elif best.expiry != call.expiry:
                note = "put expiry differs from call expiry"
            elif best.multiplier != call.multiplier:
                note = "put multiplier differs from call multiplier"
            elif best.exercise_style != call.exercise_style:
                note = "put exercise style differs from call exercise style"
            elif best.settlement != call.settlement:
                note = "put settlement differs from call settlement"
            pairs.append(
                ReplayPair(
                    pair=QuotePair(
                        pair_id=f"{root_id}|{snapshot.isoformat()}",
                        underlying=call.underlying,
                        day=snapshot.date().isoformat(),
                        day_index=0,
                        strike=call.strike,
                        put_strike=best.strike,
                        days=days,
                        spot=call.spot,
                        rate=schema.rate,
                        dividend_yield=schema.dividend_yield,
                        snapshot_utc=snapshot,
                        call_bid=call.bid,
                        call_ask=call.ask,
                        put_bid=best.bid,
                        put_ask=best.ask,
                        call_timestamp_utc=call.quote_time,
                        put_timestamp_utc=best.quote_time,
                        spot_timestamp_utc=call.spot_time,
                        defect=note or "none",
                        multiplier=call.multiplier,
                        settlement=call.settlement or "cash",
                        exercise_style=call.exercise_style or "american",
                        put_multiplier=best.multiplier,
                        put_settlement=best.settlement or "cash",
                        put_exercise_style=best.exercise_style or "american",
                        expiry=call.expiry,
                    ),
                    condition=call.condition or best.condition,
                    note=note,
                )
            )
        leftover = len(puts) - len(used)
        if leftover > 0:
            counts[REJECT_UNPAIRED] = counts.get(REJECT_UNPAIRED, 0) + leftover
    return pairs, counts


# --- fixture writer ---------------------------------------------------------


FIXTURE_COLUMNS = [
    "root_symbol",
    "underlying_symbol",
    "option_type",
    "strike_price",
    "expiration",
    "bid_price",
    "ask_price",
    "bid_size",
    "ask_size",
    "quote_timestamp",
    "underlying_last",
    "underlying_timestamp",
    "multiplier",
    "exercise_style",
    "settle_type",
    "condition",
]


def _vendor_timestamp(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# A deterministic fault schedule. Each rule fires on its own stride, so every
# declared failure mode of the ingestion path appears in the fixture at least
# once and the counts are reproducible.
FAULT_SCHEDULE: tuple[tuple[int, str], ...] = (
    (53, "missing_bid"),
    (59, "crossed"),
    (61, "stale"),
    (67, "strike_mismatch"),
    (71, "out_of_bounds"),
    (73, "no_put_leg"),
    (79, "unknown_code"),
    (83, "bad_timestamp"),
    (89, "missing_underlying"),
    (97, "no_quote"),
    (101, "spot_disagreement"),
    (103, "duplicate_put"),
)


def _fault_for(index: int) -> str:
    for stride, name in FAULT_SCHEDULE:
        if index % stride == 0:
            return name
    return "none"


def build_fixture_rows(
    schema: VendorSchema, config: GeneratorConfig | None = None
) -> list[dict[str, str]]:
    """Build the vendor-shaped rows that back the fixture file."""
    pairs, _counts = generate_market(config or GeneratorConfig())
    rows: list[dict[str, str]] = []
    for index, pair in enumerate(pairs):
        fault = _fault_for(index)
        expiry = pair.expiry.isoformat() if pair.expiry else ""
        root_id = f"{pair.underlying}|{expiry}|{pair.strike:.2f}"
        put_strike = pair.put_strike
        if fault == "strike_mismatch":
            put_strike = round(put_strike + schema.tick, 2)
        call_bid, call_ask = pair.call_bid, pair.call_ask
        if fault == "crossed":
            call_bid = call_ask + schema.tick
        put_bid, put_ask = pair.put_bid, pair.put_ask
        if fault == "out_of_bounds":
            call_ask = max(call_ask * 3.0, call_bid + schema.tick)
        put_quote_time = pair.put_timestamp_utc
        if fault == "stale":
            put_quote_time = pair.put_timestamp_utc + timedelta(seconds=2.5)
        for option_type, bid, ask, strike, quote_time in (
            ("C", call_bid, call_ask, pair.strike, pair.call_timestamp_utc),
            ("P", put_bid, put_ask, put_strike, put_quote_time),
        ):
            code = "Z" if fault == "unknown_code" and option_type == "P" else option_type
            ask_text = f"{ask * schema.price_scale:.0f}"
            spot_text = f"{pair.spot * schema.price_scale:.0f}"
            if fault == "missing_bid" and option_type == "P":
                bid_text = ""
            elif fault == "no_quote" and option_type == "P":
                bid_text = "0"
                ask_text = "0"
            else:
                bid_text = f"{bid * schema.price_scale:.0f}"
            if fault == "spot_disagreement" and option_type == "P":
                spot_text = f"{pair.spot * 1.01 * schema.price_scale:.0f}"
            if fault == "bad_timestamp" and option_type == "P":
                quote_text = "not-a-timestamp"
            else:
                quote_text = _vendor_timestamp(quote_time)
            underlying = pair.underlying
            if fault == "missing_underlying" and option_type == "P":
                underlying = ""
            rows.append(
                {
                    "root_symbol": root_id,
                    "underlying_symbol": underlying,
                    "option_type": code,
                    "strike_price": f"{strike:.2f}",
                    "expiration": expiry,
                    "bid_price": bid_text,
                    "ask_price": ask_text,
                    "bid_size": "12",
                    "ask_size": "9",
                    "quote_timestamp": quote_text,
                    "underlying_last": spot_text,
                    "underlying_timestamp": _vendor_timestamp(pair.spot_timestamp_utc),
                    "multiplier": "100",
                    "exercise_style": "AMER",
                    "settle_type": "CASH",
                    "condition": "A",
                }
            )
            if fault == "duplicate_put" and option_type == "P":
                rows.append(dict(rows[-1]))
        if fault == "no_put_leg":
            rows = [
                row
                for row in rows
                if row["root_symbol"] != root_id or row["option_type"] != "P"
            ]
    return rows


def write_vendor_fixture(
    path: str | Path, schema: VendorSchema, config: GeneratorConfig | None = None
) -> int:
    """Write the vendor-shaped fixture and return the number of rows written."""
    rows = build_fixture_rows(schema, config)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIXTURE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# --- report -----------------------------------------------------------------


def replay_report(
    pairs: Sequence[ReplayPair],
    frame_rejections: Mapping[str, int],
    pair_rejections: Mapping[str, int],
    schema: VendorSchema,
    rows_read: int,
    rows_parsed: int,
) -> dict[str, object]:
    """Summarise a replay: what was read, what was rejected, what was formed."""
    settings = _replay_settings(schema)
    rows = run_protocol([item.pair for item in pairs], settings)
    records: list[PairRecord] = [row.to_record() for row in rows]
    reconciliation = reconcile(records, attempted=len(rows))
    counts = dict(frame_rejections)
    for key, value in pair_rejections.items():
        counts[key] = counts.get(key, 0) + value
    identified = sum(
        1
        for row in rows
        if row.terminal
        in (
            TerminalStatus.RESOLVED_WITHIN_TOLERANCE,
            TerminalStatus.IDENTIFIED_OUTSIDE_TOLERANCE,
        )
    )
    certified = sum(
        1 for row in rows if row.terminal is TerminalStatus.RESOLVED_WITHIN_TOLERANCE
    )
    return {
        "status": "vendor_shape_replay_only",
        "market_data_used": False,
        "vendor": schema.vendor,
        "rows_read": rows_read,
        "rows_parsed": rows_parsed,
        "rows_rejected": sum(counts.values()),
        "rejections": dict(sorted(counts.items())),
        "pairs_formed": len(pairs),
        "attempted": len(rows),
        "identified": identified,
        "certified": certified,
        "coverage_identified": identified / len(rows) if rows else 0.0,
        "coverage_certified": certified / len(rows) if rows else 0.0,
        "reconciliation": reconciliation,
        "funnel": [
            {
                "stage": item.stage.value,
                "count": item.count,
                "share_of_attempted": item.share_of_attempted,
                "share_of_prior": item.share_of_prior,
                "dominant_rejection_reason": item.dominant_rejection_reason,
            }
            for item in funnel(records, attempted=len(rows))
        ],
        "warning": (
            "Replay of a synthetic file shaped like a vendor feed. It tests the "
            "ingestion path, not the market, and it supports no market claim."
        ),
    }


def _replay_settings(schema: VendorSchema) -> StudySettings:
    return StudySettings(
        tick=schema.tick,
        resolution_ticks=schema.resolution_ticks,
        primary_tolerance_pp=schema.primary_tolerance_pp,
        quote_sync_tolerance_seconds=schema.quote_sync_tolerance_seconds,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write-fixture", action="store_true")
    parser.add_argument(
        "--source-kind", default="fixture", choices=("fixture", "licensed")
    )
    args = parser.parse_args(argv)
    schema = load_schema(args.schema)
    licence_mode = assert_source_allowed(args.source_kind, args.schema)
    if args.write_fixture:
        written = write_vendor_fixture(args.fixture, schema)
        print(f"wrote {written} rows to {args.fixture}")
    frame = load_vendor_rows(args.fixture, schema)
    pairs, pair_rejections = pair_rows(frame, schema)
    report = replay_report(
        pairs,
        frame.rejections,
        pair_rejections,
        schema,
        frame.rows_read,
        len(frame.rows),
    )
    report["licence_mode"] = licence_mode
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "replay_summary.json"
    summary_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
