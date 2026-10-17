from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from research.cpiv.build_demo import (
    DAYS,
    DIVIDEND_YIELD,
    PUT_IV,
    RATE,
    SPOT,
    STRIKE,
    american_model_mismatch,
    american_price,
    bs_price,
    bs_vega_per_vol_point,
    build_records,
    carry_misspecification,
    dte_tradeoff_sensitivity,
    implied_volatility,
    parity_residual,
    quote_noise_scale_sensitivity,
    rank_noise_summary,
    spot_timestamp_mismatch,
    write_outputs,
)


class CPIVEducationalDemoTests(unittest.TestCase):
    def test_inverse_recovers_synthetic_call_and_put_volatility(self) -> None:
        for option_type, sigma in (("call", 0.16), ("put", PUT_IV), ("call", 0.25)):
            price = bs_price(option_type, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, sigma)
            recovered = implied_volatility(
                option_type, price, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD
            )
            self.assertAlmostEqual(recovered, sigma, places=8)

    def test_equal_volatility_produces_zero_cpiv(self) -> None:
        call = bs_price("call", SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV)
        put = bs_price("put", SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV)
        call_iv = implied_volatility("call", call, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD)
        put_iv = implied_volatility("put", put, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD)
        self.assertAlmostEqual(call_iv - put_iv, 0.0, places=8)

    def test_parity_residual_and_vega_units(self) -> None:
        call = bs_price("call", SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV)
        put = bs_price("put", SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV)
        residual = parity_residual(
            call, put, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD
        )
        vega_pp = bs_vega_per_vol_point(
            SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV
        )
        self.assertAlmostEqual(residual, 0.0, places=10)
        self.assertGreater(vega_pp, 0.0)
        self.assertAlmostEqual(
            vega_pp * 100.0,
            SPOT
            * (1.0 / (2.0 * 3.141592653589793) ** 0.5)
            * (DAYS / 365.0) ** 0.5,
            delta=0.01,
        )

    def test_sign_and_sorted_rank_are_consistent(self) -> None:
        rows = build_records()
        self.assertEqual(len(rows), 10)
        by_rank = sorted(rows, key=lambda row: row["rank_low_to_high"])
        self.assertLess(by_rank[0]["cpiv"], 0)
        self.assertGreater(by_rank[-1]["cpiv"], 0)
        self.assertEqual(by_rank[0]["illustrative_bucket"], "short-side candidate")
        self.assertEqual(by_rank[-1]["illustrative_bucket"], "long-side candidate")
        self.assertTrue(
            all(row["interval_low"] <= row["cpiv"] <= row["interval_high"] for row in rows)
        )

    def test_invalid_inputs_and_impossible_prices_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            bs_price("straddle", SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV)
        with self.assertRaises(ValueError):
            bs_price("call", 0, STRIKE, DAYS, RATE, DIVIDEND_YIELD, PUT_IV)
        with self.assertRaises(ValueError):
            implied_volatility("call", 100.0, SPOT, STRIKE, DAYS, RATE, DIVIDEND_YIELD)

    def test_carry_misspecification_creates_a_false_spread(self) -> None:
        rows = carry_misspecification()
        expected = [0.0, -0.7186, -1.4367, -3.5872]
        self.assertEqual(len(rows), 4)
        for row, target in zip(rows, expected, strict=True):
            self.assertAlmostEqual(row["cpiv_pp"], target, places=3)

    def test_american_put_early_exercise_changes_european_bsm_iv(self) -> None:
        european_put = bs_price("put", SPOT, STRIKE, DAYS, 0.05, 0.0, PUT_IV)
        american_put = american_price("put", SPOT, STRIKE, DAYS, 0.05, 0.0, PUT_IV)
        self.assertGreater(american_put, european_put)
        result = american_model_mismatch()
        self.assertAlmostEqual(result["cpiv_pp_from_european_bsm"], -0.261, places=3)
        self.assertAlmostEqual(
            result["local_cpiv_approximation_pp"],
            result["cpiv_pp_from_european_bsm"],
            places=4,
        )
        self.assertEqual(result["call_early_exercise_premium_usd"], 0.0)
        self.assertGreaterEqual(result["steps"], 500)

    def test_spot_timestamp_mismatch_is_mapped_by_parity_residual(self) -> None:
        rows = spot_timestamp_mismatch()
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertLess(row["cpiv_pp"], 0.0)
            self.assertAlmostEqual(
                row["cpiv_pp"],
                row["local_cpiv_approximation_pp"],
                delta=0.001,
            )

    def test_dte_and_spot_scale_sensitivities_have_expected_direction(self) -> None:
        dte_rows = dte_tradeoff_sensitivity()
        self.assertEqual([row["days_to_expiry"] for row in dte_rows], [7, 30, 90, 365])
        self.assertGreater(
            dte_rows[0]["quote_noise_cpiv_sd_pp_linearized"],
            dte_rows[-1]["quote_noise_cpiv_sd_pp_linearized"],
        )
        self.assertLess(
            abs(dte_rows[0]["omitted_carry_cpiv_pp"]),
            abs(dte_rows[-1]["omitted_carry_cpiv_pp"]),
        )
        scale_rows = quote_noise_scale_sensitivity()
        same_maturity = [row for row in scale_rows if row["days_to_expiry"] == 30]
        self.assertGreater(
            same_maturity[0]["cpiv_noise_sd_pp_at_half_width"],
            same_maturity[-1]["cpiv_noise_sd_pp_at_half_width"],
        )
        self.assertTrue(
            all(
                row["half_width_usd_per_leg_for_0_5pp_cpiv_sd"] > 0.0
                for row in scale_rows
            )
        )

    def test_quote_noise_summary_is_seeded_and_has_exact_zero_noise(self) -> None:
        first = rank_noise_summary(replicates=12)
        second = rank_noise_summary(replicates=12)
        self.assertEqual(first, second)
        self.assertEqual(first[0]["rank_inversions_median"], 0.0)
        self.assertEqual(first[0]["spearman_rho_median"], 1.0)
        self.assertEqual(len(first), 7)
        self.assertEqual(first[0]["probability_no_pairwise_inversions"], 1.0)
        self.assertEqual(first[0]["probability_long_short_membership_change"], 0.0)
        self.assertEqual(len(first[0]["example_ranked_names"]), 10)
        self.assertEqual(
            [
                item["rank_low_to_high"]
                for item in first[0]["example_ranked_names"]
            ],
            list(range(1, 11)),
        )

    def test_generated_assets_are_labeled_synthetic_and_complete(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            paths = write_outputs(Path(temporary_directory), replicates=12)
            self.assertEqual(
                set(paths),
                {
                    "csv",
                    "json",
                    "svg",
                    "png",
                    "stress_json",
                    "carry_png",
                    "carry_svg",
                    "american_png",
                    "american_svg",
                    "noise_png",
                    "noise_svg",
                    "social_card_png",
                },
            )
            self.assertTrue(all(Path(path).is_file() for path in paths.values()))
            manifest = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "synthetic_educational_example_only")
            self.assertFalse(manifest["market_data_used"])
            self.assertFalse(manifest["network_access_used"])
            stress = json.loads(Path(paths["stress_json"]).read_text(encoding="utf-8"))
            self.assertEqual(stress["status"], "synthetic_sensitivity_analysis_only")
            self.assertEqual(stress["quote_noise_ranking"]["replicates"], 12)
            self.assertFalse(stress["market_data_used"])


if __name__ == "__main__":
    unittest.main()
