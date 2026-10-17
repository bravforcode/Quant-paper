# CPIV R11 review follow-up — 11 October 2026

## Release artifacts

The latest built package is `dist/cpiv/quantcorner-cpiv-r11-reviewed-2026-10-11-v6/`:

| File | Size (bytes) | SHA-256 |
|---|---:|---|
| `quantcorner-cpiv-review-r11-2026-10-11.html` | 953,502 | `3CDA54761651831E36622CB1E05CA2642889E8F6E881CB98A1F28384E1EDF396` |
| `quantcorner-cpiv-review-r11-2026-10-11.docx` | 535,575 | `6BF1818F18E5BE29418E2C1DDB6AA1CDEB31BE7B0A755A6035E11F5FD4016D35` |
| `quantcorner-cpiv-review-r11-2026-10-11.pdf` | 707,995 | `876F920342045D4744B855EAFBF62415EF2DD5906744FFBA15C9A3C2DC1BFEAE` |

This is a locally generated review package, not a submission receipt or acceptance decision. Earlier versioned output directories were left untouched.

## Changes made against the supplied review

- Removed reviewer-facing process commentary, temporary-preview/working-tree wording, and the workstation-specific absolute path from the manuscript. The appendix documents only commands it actually contains; it does not claim a manifest-verification step. The Decimal audit has one invocation.
- Reordered the abstract to lead with the common-map identity, the sub-tick finite-shock example, and the configuration-specific carry sensitivity; the synthetic grid counts now follow those results. The manuscript date is aligned to 11 October 2026.
- Replaced extreme continuous heatmap scales with labeled finite bands and explicit unresolved categories. Figure 4 reports local sensitivities; Figure 5 reports resolved exact finite-shock IV changes capped at the configured 500-point solver bracket. Sub-tick premiums and missing roots remain visibly flagged; neither panel presents local/exact ratios as resolution evidence.
- Added the price-resolution protocol stage and kept tick, spread, and roundoff sources distinct. Every generated row has a reference tick and `premium_below_tick` flag; a premium below the declared/configured reference tick is unresolved even if a separate shocked price has an IV root. The legacy absolute-vega guard is not treated as proof of measurement resolution.
- Added a carry/forward tolerance stated in CPIV points. In the synthetic ATM 30-day, 20%-IV configuration, a 1 bp relative-forward mismatch maps locally to 0.087469 CPIV points; a 1-point tolerance maps to 11.4326 bp. This is an example, not a universal threshold.
- Added a page break after Figure 5 so §7.8 and Tables 6–7 no longer split ahead of the figure. Visual PDF review confirms Figure 4/Table 5B on page 15, Figure 5 on page 16, §7.8/Tables 6–7 on page 17, Table 4 on page 18, and the carry-tolerance discussion on page 19.

## Verification evidence

- Focused suite: **49 passed** on 11 October (`tests/test_cpiv_r10_diagnostics.py`, R11 price-resolution, near-bound crosswalk, carry-forward and manuscript tests, review-builder tests, and educational-demo tests). Correction, 18 October 2026: the same seven files on the current tree give **56 passed**, exit 0 (38.9 s). The 49 figure is kept as the record for the v6 build; it was not re-derived for that build. The v6 artifact hashes in the table above were re-checked on 18 October and match.
- Ruff passed on the touched R11 modules/tests. Targeted mypy passed on `r11_price_resolution.py` and `r11_carry_forward.py`; mypy emitted the existing configuration note that `module = ['bti.bounds.*']` is unused.
- The price-resolution CSV has 2,400 rows: 1,424 `resolved`, 326 `unresolved_premium_below_tick`, 410 `unresolved_shock_no_root`, and 240 `local_only`; `market_data_used=True` occurs zero times. There are 362 rows with `premium_below_tick=True`.
- The PDF has 21 pages; its extracted text contains zero U+2010 characters, includes the finite-shock and carry examples, and has no workstation path, “temporary preview,” or “working tree” wording. The Table 5B/Figure 4/Figure 5/§7.8/Table 4 page order was checked in extracted text and the cited pages were visually rendered.
- The standalone HTML contains five `<img>` elements (six `data:image/` occurrences including its Open Graph image), embeds both new figure captions, and has zero `data-embedded-src` attributes.
- DOCX ZIP integrity passes; XML contains 8 tables, all with border definitions, and 5 media items. A Word/LibreOffice visual render was not available in this session, so DOCX pagination and visual fidelity are not certified here.
- The builder completed with exit code 0. MiKTeX printed update-check notices; no automatic update was run.
- Check, 18 October 2026: the L28 counts match `research/cpiv/generated/r11_price_resolution_20261011/cpiv_r11_price_resolution.csv` exactly (labels `resolved`, `unresolved_premium_below_tick`, `unresolved_shock_no_root`, `local_only`; `premium_below_tick=True` for 362 rows). That CSV is an older schema. The current generator writes `research/cpiv/generated/repro/cpiv_r11_price_resolution.csv` with `identification_status`: 1,424 `identified`, 240 `local_only_roundoff`, 652 `unresolved_otm_equivalent_below_tick`, 84 `unresolved_shock_no_root`; 724 rows have `otm_equivalent_time_value_below_tick=True`. The label `unresolved_premium_below_tick` no longer appears in the code. `market_data_used=True` occurs zero times in both files. The L29 PDF figures were re-checked on the v6 PDF (21 pages; zero U+2010) and match.

## Still open; not established by this revision

- No historical or synchronized market option-chain data was used. All current results are synthetic; there is no alpha, profitability, or market-wide coverage claim. The empirical-data/G5 gate remains **OPEN / NOT MET**.
- The additional proposed analyses—off-midpoint reference-volatility / cubic local-error checks, analytical ranking benchmarks including SNR and test–retest reliability, and an independently benchmarked American-option/Richardson study—remain unimplemented.
- No provider terms or publication rights were assessed in this revision, no external service was called, no email was sent, and no submission was made. QuantCorner's editorial decision is unknown.

