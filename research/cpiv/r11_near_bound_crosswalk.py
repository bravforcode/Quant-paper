"""Cross-tab rejected prices under binary64 and 180-digit bound comparisons."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any

FLOAT_GROUPS = (
    "interior_near_bound_guard",
    "exact_bound_guard",
    "strict_bound_violation",
)
DECIMAL_GROUPS = ("inside", "on_boundary", "violation")
_KEY_FIELDS = (
    "option_type",
    "spot_strike_ratio",
    "days_to_expiry",
    "target_iv_decimal",
)


def _decimal(value: str, field: str) -> Decimal:
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"invalid decimal value for {field}: {value!r}") from exc
    if not number.is_finite():
        raise ValueError(f"non-finite decimal value for {field}")
    return number


def _key(row: dict[str, str], price_field: str) -> tuple[Any, ...]:
    try:
        return (
            row["option_type"],
            _decimal(row["spot_strike_ratio"], "spot_strike_ratio"),
            int(row["days_to_expiry"]),
            _decimal(row["target_iv_decimal"], "target_iv_decimal"),
            _decimal(row[price_field], price_field),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("audit row is missing a valid case-join field") from exc


def _unique_index(
    rows: list[dict[str, str]], price_field: str, source_name: str
) -> dict[tuple[Any, ...], dict[str, str]]:
    index: dict[tuple[Any, ...], dict[str, str]] = {}
    for row in rows:
        key = _key(row, price_field)
        if key in index:
            raise ValueError(f"duplicate case key in {source_name}: {key}")
        index[key] = row
    return index


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"audit input is empty: {path}")
    return rows


def _relation_from_distances(lower: Decimal, upper: Decimal) -> str:
    if lower < 0 or upper < 0:
        return "violation"
    if lower == 0 or upper == 0:
        return "on_boundary"
    return "inside"


def _decimal_relation(row: dict[str, str], float_price_text: str) -> tuple[str, str, str, str]:
    """Compare the exact binary64 value and its round-trip text with Decimal bounds."""
    serialized_price = _decimal(row["double_precision_price"], "double_precision_price")
    lower = _decimal(row["double_price_lower_distance"], "double_price_lower_distance")
    upper = _decimal(row["double_price_upper_distance"], "double_price_upper_distance")
    with localcontext() as context:
        context.prec = 220
        lower_bound = serialized_price - lower
        upper_bound = serialized_price + upper
        exact_float_price = Decimal.from_float(float(float_price_text))
        exact_lower_distance = exact_float_price - lower_bound
        exact_upper_distance = upper_bound - exact_float_price
    exact_relation = _relation_from_distances(exact_lower_distance, exact_upper_distance)
    text_relation = _relation_from_distances(lower, upper)
    return exact_relation, text_relation, str(exact_lower_distance), str(exact_upper_distance)


def cross_tab_audits(
    float_audit_csv: Path, decimal_audit_csv: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Join by contract coordinates and stored price, then classify both bounds."""
    float_rows = _read_csv(float_audit_csv)
    decimal_rows = _read_csv(decimal_audit_csv)
    float_index = _unique_index(float_rows, "recorded_price", "binary64 audit")
    decimal_index = _unique_index(decimal_rows, "double_precision_price", "Decimal audit")
    if float_index.keys() != decimal_index.keys():
        missing_decimal = len(float_index.keys() - decimal_index.keys())
        missing_float = len(decimal_index.keys() - float_index.keys())
        raise ValueError(
            "case sets differ between audits "
            f"(missing Decimal rows={missing_decimal}, missing binary64 rows={missing_float})"
        )

    result: list[dict[str, Any]] = []
    for key in sorted(float_index, key=lambda item: tuple(str(value) for value in item)):
        float_row = float_index[key]
        decimal_row = decimal_index[key]
        float_group = float_row.get("bound_group", "")
        if float_group not in FLOAT_GROUPS:
            raise ValueError(f"unexpected binary64 classifier group: {float_group!r}")
        (
            decimal_group,
            serialized_decimal_group,
            exact_lower_distance,
            exact_upper_distance,
        ) = _decimal_relation(decimal_row, float_row["recorded_price"])
        result.append(
            {
                **{field: float_row[field] for field in _KEY_FIELDS},
                "recorded_price": float_row["recorded_price"],
                "binary64_bound_group": float_group,
                "decimal180_stored_price_relation": decimal_group,
                "decimal180_roundtrip_text_relation": serialized_decimal_group,
                "binary64_distance_from_lower_bound": float_row["distance_from_lower_bound"],
                "binary64_distance_from_upper_bound": float_row["distance_from_upper_bound"],
                "decimal180_exact_float_distance_from_lower_bound": exact_lower_distance,
                "decimal180_exact_float_distance_from_upper_bound": exact_upper_distance,
                "recorded_solver_failure_status": float_row["source_failure_status"],
            }
        )

    table = {group: {relation: 0 for relation in DECIMAL_GROUPS} for group in FLOAT_GROUPS}
    float_counts: Counter[str] = Counter()
    decimal_counts: Counter[str] = Counter()
    text_counts: Counter[str] = Counter()
    for row in result:
        float_group = str(row["binary64_bound_group"])
        decimal_group = str(row["decimal180_stored_price_relation"])
        text_group = str(row["decimal180_roundtrip_text_relation"])
        table[float_group][decimal_group] += 1
        float_counts[float_group] += 1
        decimal_counts[decimal_group] += 1
        text_counts[text_group] += 1
    summary = {
        "status": "case_level_cross_tab_complete",
        "case_count": len(result),
        "binary64_group_counts": {group: float_counts[group] for group in FLOAT_GROUPS},
        "decimal180_stored_price_relation_counts": {
            group: decimal_counts[group] for group in DECIMAL_GROUPS
        },
        "decimal180_roundtrip_text_relation_counts": {
            group: text_counts[group] for group in DECIMAL_GROUPS
        },
        "cross_tab_binary64_rows_decimal180_columns": table,
        "decimal_comparison_definition": (
            "exact binary64 numerical value (Decimal.from_float) compared with reconstructed "
            "180-digit bounds; exact Decimal-generated price classification is not substituted"
        ),
        "roundtrip_text_comparison_definition": (
            "the shortest round-trip decimal serialization of the binary64 price compared with "
            "the same 180-digit bounds; reported separately because it can differ at a boundary"
        ),
        "join_definition": (
            "option type, S/K, days, target IV, and stored binary64 price; duplicate or unmatched "
            "case keys are rejected"
        ),
        "scope": "generated synthetic near-bound cases only; not a market failure rate",
    }
    return result, summary


def write_cross_tab(
    float_audit_csv: Path,
    decimal_audit_csv: Path,
    output_csv: Path,
    summary_path: Path,
) -> dict[str, Any]:
    rows, summary = cross_tab_audits(float_audit_csv, decimal_audit_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--float-audit", type=Path, required=True)
    parser.add_argument("--decimal-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            write_cross_tab(args.float_audit, args.decimal_audit, args.output, args.summary),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
