from __future__ import annotations

import csv

from research.cpiv.r11_near_bound_crosswalk import cross_tab_audits


def _write(path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_cross_tab_joins_each_price_and_keeps_three_relation_classes(tmp_path) -> None:
    cases = (
        ("0.00000000005", "interior_near_bound_guard", "0.00000000005"),
        ("0", "exact_bound_guard", "0"),
        ("-0.000000000001", "strict_bound_violation", "-0.000000000001"),
    )
    float_rows = []
    decimal_rows = []
    for index, (price, group, lower_distance) in enumerate(cases):
        float_rows.append(
            {
                "option_type": "call",
                "spot_strike_ratio": "1.0",
                "days_to_expiry": "30",
                "target_iv_decimal": f"0.{index + 1}",
                "recorded_price": price,
                "bound_group": group,
                "distance_from_lower_bound": lower_distance,
                "distance_from_upper_bound": "1",
                "source_failure_status": "synthetic_rejection",
            }
        )
        decimal_rows.append(
            {
                "option_type": "call",
                "spot_strike_ratio": "1.0",
                "days_to_expiry": "30",
                "target_iv_decimal": f"0.{index + 1}",
                "double_precision_price": price,
                "double_price_lower_distance": lower_distance,
                "double_price_upper_distance": "1",
            }
        )
    float_path = tmp_path / "float.csv"
    decimal_path = tmp_path / "decimal.csv"
    _write(float_path, float_rows)
    _write(decimal_path, decimal_rows)

    rows, summary = cross_tab_audits(float_path, decimal_path)

    assert len(rows) == 3
    assert summary["binary64_group_counts"] == {
        "interior_near_bound_guard": 1,
        "exact_bound_guard": 1,
        "strict_bound_violation": 1,
    }
    assert summary["decimal180_stored_price_relation_counts"] == {
        "inside": 1,
        "on_boundary": 1,
        "violation": 1,
    }
