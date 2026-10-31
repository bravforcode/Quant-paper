# Claim–evidence matrix — JCF submission

Checked against the rebuilt manuscript (`manuscript_jcf_draft.md`, 9,983 main-text words) on 2026-10-31. Paths are relative to `research/cpiv/measurement/outputs/` unless stated.

Status key: **Supported** = the named artifact shows it. **Open** = a provenance or verification step is still needed before the sentence is safe to submit.

| # | Claim (manuscript location) | Evidence | Status |
|:--|:--|:--|:--|
| 1 | Certified coverage falls towards zero on coarse-quote markets (Abstract; Key message 1; §6.3–6.4) | `sweep/verdict.json` rule R3 = FAIL; `study/study_summary.json` coverage and frontier; `study/perturbations.csv` (`endpoint_outward` coverage 0.0078) | Supported |
| 2 | The certified subset beats size-matched random subsets in every draw (Abstract; §6.5–6.6) | `sweep/verdict.json` rule R1: 23 of 23 draws below the block-null mean, 23 of 23 with block-null p < 0.05 | Supported |
| 3 | Own-set error is lower than the raw midpoint's (§6.2, §6.6) | `sweep/verdict.json` rule R2: 23 of 23 draws | Supported |
| 4 | On the common set the protocol is identical to the raw midpoint (Abstract; Key message 3; §1.3) | By construction (§3); `study/study_summary.json` `common_set_note` | Supported: `tests/test_cpiv_measurement_study.py::test_certified_value_equals_raw_midpoint_on_common_set` asserts equality (passes) |
| 5 | Thresholds were declared in an addendum dated before the sweep, not verified as pre-registered (Key message 4; §5.1) | `docs/cpiv-jcf/preregistration_addendum_A1_synthetic.md` is dated 2026-10-22 and states the freeze as of that date. The sweep manifest records 2026-10-22 11:28 UTC. The branch's history first records the addendum in commit `e34edbe` (2026-10-31 00:00 +0700, i.e. 30 Oct UTC). An earlier commit, `afed677` (2026-10-26), adds the same file on branch `cpiv-r33-m3-licence-limit`, which is not an ancestor of this branch. Its one later edit (2026-10-24) corrects a specification count from 18 to 17 and changes no rule, seed or threshold | Disclosed, not verified from the repository: the order rests on the stated dates. §5.1 says so. No git record predates the sweep manifest |
| 6 | The configuration did not change between the frozen addendum and the sweep (§5.2) | `configs/study.yaml` SHA-256 `0918f7ac…f187a` equals `config_sha256` in `sweep/manifest.json` and `study/manifest.json` | Supported |
| 7 | No market data was used (Abstract; §1.4; §7.2; Data availability) | `sweep/verdict.json` `market_data_used: false`; `manifest.json` `licence_mode: synthetic-no-market-data`; `study_summary.json` `market_data_used` | Supported |
| 8 | Six declared rules were evaluated, one fails (§6.6). R3 and R6 run on the development seed (20261022) only; R1, R2, R4 and R5 span the 23 draws | `sweep/verdict.json`: R1, R2, R4, R5, R6 pass; R3 fails; `all_rules_passed: false`; `specifications.csv` and `study/manifest.json` seed 20261022 | Supported; R3 and R6 are computed on the development seed only, a departure from addendum A1.1 (which requires all rules on the 23 seeds), stated in §6.6. The 23-seed repeat is post hoc |
| 9 | The perturbation set does not dominate the result (§6.7; R6) | `sweep/verdict.json` rule R6 = PASS; `study/perturbations.csv` | Supported |
| 10 | Funnel and abstention split: 894 attempted; 822 abstained (719 + 77 + 26); 72 certified; coverage about 8 per cent (§6.1, §6.3) | `study/funnel.md`: 894 attempted, 791 reach the tolerance stage; 72 = 894 − 822 (8.05 per cent) | Supported |
| 11 | Spot and rate sensitivities are 8 and 6 times the certified error (§6.7) | `study/perturbations.csv` `mae_vs_truth_pp`: spot 0.0664, rate 0.0542; `study/study_summary.json` `error_profile.protocol_certified.mean_abs_error_pp` 0.00873. Ratios 7.6 and 6.2, reported as 8 and 6 | Supported. Ratios 7.6 and 6.2 are rounded to 8 and 6 in §6.7; §6.7 wording checked against the perturbation table |
| 12 | Surface-calibration secondary outcome (§6.9) | `study/study_summary.json` `secondary_outcome`: 296 raw contracts, 72 protocol contracts, 224 forgone, coverage retained 0.243; max slice surface change 2.23 pp | Supported. Numbers and §6.9 wording checked: 296 / 72 / 224 contracts, retained 0.243, slice change 2.23 pp against error 0.009 pp (about 255 times, so "more than two orders of magnitude" holds) |
| 13 | Time-value and finite-shock refusals are exploratory only (§6.10) | `ablation/ablation_summary.json`, `ablation/ablation.csv`; labelled exploratory in the text | Supported (label); numbers not re-read |
| 14 | The benchmark makes no market claim (§7.2 non-claims) | Text review; no market artifact is cited anywhere in the manuscript | Supported |

## Open items before submission

1. **Row 5 — provenance of the freeze.** Disclosed in §5.1 (provenance sentence added 2026-10-30). Repository history cannot show the pre-sweep order; only an external timestamp of the 2026-10-22 state could. Not a blocker for submission, but a reviewer can check it only from the stated dates.
2. **Row 4 — common-set identity test.** Done: `test_certified_value_equals_raw_midpoint_on_common_set` passes.
3. **Rows 11 and 12 — wording.** Checked on 2026-10-31: the numbers match, and §6.7 now separates the quote-side widening from the timing perturbation.
