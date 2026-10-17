"""Classify rejected R10 IV prices against the bounds used by its float solver."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from research.cpiv import build_demo as demo

ABSOLUTE_NEAR_BOUND_GUARD = 1e-10


def classify_float_price(
    price: float,
    lower: float,
    upper: float,
    tolerance: float = ABSOLUTE_NEAR_BOUND_GUARD,
) -> str:
    """Apply strict-bound checks before the exact/near-bound guard split."""
    if not all(math.isfinite(value) for value in (price, lower, upper, tolerance)):
        raise ValueError("price, bounds, and tolerance must be finite")
    if lower > upper or tolerance < 0.0:
        raise ValueError("bounds must be ordered and tolerance nonnegative")
    if price < lower or price > upper:
        return "strict_bound_violation"
    if price in (lower, upper):
        return "exact_bound_guard"
    if min(price - lower, upper - price) <= tolerance:
        return "interior_near_bound_guard"
    return "not_near_bound"


def audit_rejected_prices(input_csv: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    audit_rows: list[dict[str, Any]] = []
    with input_csv.open(encoding="utf-8", newline="") as handle:
        for source in csv.DictReader(handle):
            if source.get("status") == "ok":
                continue
            try:
                option_type = source["option_type"]
                ratio = float(source["spot_strike_ratio"])
                days = int(source["days_to_expiry"])
                price = float(source["theoretical_price_usd"])
                rate, yield_ = 0.03, 0.01
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("input CSV lacks required inversion fields") from exc
            spot, strike = 100.0 * ratio, 100.0
            lower, upper = demo.price_bounds(option_type, spot, strike, days, rate, yield_)
            group = classify_float_price(price, lower, upper)
            replayed_status = (
                "theoretical_bound_violation"
                if group == "strict_bound_violation"
                else "rejected_by_configured_absolute_near_bound_guard"
                if group in {"exact_bound_guard", "interior_near_bound_guard"}
                else source.get("failure_status", "unknown")
            )
            if replayed_status != source.get("failure_status"):
                raise ValueError("classification differs from recorded solver failure status")
            audit_rows.append(
                {
                    "option_type": option_type,
                    "spot_strike_ratio": ratio,
                    "days_to_expiry": days,
                    "target_iv_decimal": float(source["target_iv"]),
                    "recorded_price": price,
                    "float_lower_bound": lower,
                    "float_upper_bound": upper,
                    "distance_from_lower_bound": price - lower,
                    "distance_from_upper_bound": upper - price,
                    "classification_order": (
                        "strict bound check; exact bound; interior near-bound guard"
                    ),
                    "bound_group": group,
                    "source_failure_status": source.get("failure_status", "unknown"),
                    "tolerance": ABSOLUTE_NEAR_BOUND_GUARD,
                    "source": "synthetic BSM price; binary64 solver bounds",
                }
            )

    counts = Counter(str(row["bound_group"]) for row in audit_rows)
    summary = {
        "audited_rejected_price_count": len(audit_rows),
        "group_counts": dict(sorted(counts.items())),
        "guard_rejection_count": (
            counts["exact_bound_guard"] + counts["interior_near_bound_guard"]
        ),
        "strict_bound_violation_count": counts["strict_bound_violation"],
        "near_bound_tolerance": ABSOLUTE_NEAR_BOUND_GUARD,
        "classification_order": (
            "test strict violation first; then exact-bound guard; "
            "then strictly-interior near-bound guard"
        ),
        "scope": "replay of the generated synthetic R10 failures; not market data",
    }
    return audit_rows, summary


def write_audit(input_csv: Path, output_csv: Path, summary_path: Path) -> dict[str, Any]:
    rows, summary = audit_rejected_prices(input_csv)
    if not rows:
        raise ValueError("input CSV has no rejected-price rows")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(write_audit(args.input, args.output, args.summary), indent=2))


if __name__ == "__main__":
    main()
