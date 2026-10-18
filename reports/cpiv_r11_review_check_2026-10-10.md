# CPIV R11 review check — 10 October 2026

## Scope

Checked the review points against the R11 working manuscript, source diagnostics,
and generated synthetic audit files. This is a source/code audit, not an
independent human replication or a market-data review. R11 now includes exact
finite-shock statuses, a case-level near-bound cross-tab, and a carry/forward
protocol gate with synthetic sensitivity checks.

## Point-by-point disposition

1. **Tick is a scenario, not a market fact — verified and implemented.**
   `r11_price_resolution.py` accepts tick values through the function and CLI;
   defaults are explicitly hypothetical. It reports one-full-tick local
   sensitivity separately from exact finite-shock inversion. No venue tick is
   asserted. Results and heatmap are in
   `research/cpiv/generated/r11_price_resolution/`.

2. **Table 4 carry/forward gate — implemented in the R11 working draft.**
   Table 4 now requires independently sourced, synchronized spot, forward, rate,
   maturity, and effective yield, plus a predeclared relative tolerance for
   `F ≈ S exp((r-q)T)`. Missing inputs stay unknown; inconsistent or circularly
   inferred inputs do not pass. The fixed-price local sensitivity proposition
   is implemented and tested against central finite differences. The synthetic
   §7.3 examples reproduce `−3.58725 pp` for the 5% yield mismatch and about
   `±0.875 pp` for ±0.10 spot changes; these are not market observations.

3. **Sixteen near-bound failures — case-level comparison reproduced.** The
   binary64 solver partition is 10 interior guard + 5 exact-bound guard + 1
   strict violation. Joined by option type, S/K, expiry, target IV, and stored
   price, the exact binary64 values compared with 180-digit bounds form a
   `12 inside / 2 boundary / 2 violation` cross-tab; the shortest decimal text
   independently yields the same margins in this set. The full 3×3 table and
   all 16 rows are in `cpiv_r11_near_bound_crosswalk.csv/json`. This explains
   where the Decimal `12` differs from the solver's `10`; it does not replace
   either classifier or estimate a market failure rate.

4. **`δP=max(tick, half-spread, ε·price)` — the review's correction is right:
   no SD term appears in that expression.** The conceptual issue is combining
   unlike sources. R11 now reports `δIV_tick`, `δIV_spread`, and
   `δIV_roundoff` separately; `u=2^-53` is named unit roundoff. The roundoff
   scenario is explicitly not a total-error bound, and the three components are
   not summed or collapsed by a maximum.

5. **American-exercise bias — the exact/approximate distinction is valid, but
   the cited phrase is absent from the inspected R10 source.** R10 §7.2 reports
   tree-derived CPIV convergence and explicitly says it is not a formal error
   bound. The exact common-map average-vega identity and point-vega local
   approximation are already distinguished elsewhere. If an EEP interpretation
   is added later, it must call EEP divided by path-average vega an exact
   identity under the stated common European-BSM inversion, and point vega only
   a first-order approximation.

6. **Manual sensitivity examples — recomputed.** Under `r=q=0`, ATM / 30 days /
   IV 20% gives `ν_pp=0.1143262`, one 0.01 price-unit step gives local
   `0.087469 pp`, and the unit-roundoff sensitivity is `2.22e-15 pp`. At
   `S/K=0.8` / 90 days / IV 10%, `ν_pp=7.29891e-6`; the local one-step result is
   `1,370.07 pp`, not 1,500 under these exact inputs. The exact positive shock
   is `+7.0717 pp`; the negative shock is not invertible under the configured
   bounds. Roundoff local sensitivities differ by leg (`4.83e-17 pp` call;
   `3.04e-10 pp` put). Both examples pass the old absolute-vega guard. R11
   reports all three sources and does not mislabel the local number as a finite
   uncertainty interval.

7. **`[chain]` abstract placeholder — not present in inspected R10 or R11
   abstracts.** Both state explicitly that no historical option quotes or
   option-chain data were analyzed.

8. **Other proposed analyses and data work — open.** No new `d^3` midpoint-error
   experiment or off-center `σ₀` grid; no Gaussian inversion-fraction analytic
   benchmark, SNR, or test–retest reliability; no independent external American
   benchmark/Richardson study; and no market quote collection or provider-rights
   review. Black–Scholes and Merton now have in-text citations and reference
   entries; the bibliographic records were not independently source-checked.
   The strict manifest parser verifies the prior R10 companion's 285 entries.
   This is not an R11 manifest.

9. **PDF text-layer finding — renderer corrected and an R11 preview checked.**
    UTF-8 extraction of the existing R10 final11 PDF returned U+2010 (8208), not
    ASCII hyphen-minus (45), in `Get-Content`, `-split`, and `-Algorithm`; those
    copied commands are unsafe. A minimal PDF comparison showed Cascadia Mono
    and Courier New preserve ASCII 45 while Consolas emits U+2010, so the builder
    now selects Cascadia Mono. A fresh, temporary R11 validation build completed
    (21-page PDF); its Appendix B text layer contains zero U+2010 characters, and
    the Thai summary's Unicode text is present. Pages 1, 19, and 20 were visually
    checked; the commands span pages 19–20, with the page break between complete
    commands. The manifest-verification block was extracted from the PDF text
    layer and executed in PowerShell; all 285 prior R10 entries verified. This is
    not an R11 manifest or full-document visual/DOCX validation. The old R10 PDF
    remains unchanged.

## Files and readiness

- Working manuscript: `research/cpiv/manuscript_r11_proposed.md`.
- Sensitivity code/tests: `research/cpiv/r11_price_resolution.py` and
  `tests/test_cpiv_r11_price_resolution.py`.
- Cross-tab: `research/cpiv/r11_near_bound_crosswalk.py`,
  `research/cpiv/r11_near_bound_audit.py`, and the joined 16-case CSV/JSON in
  `research/cpiv/generated/r11_price_resolution/`.
- Carry/forward: `research/cpiv/r11_carry_forward.py` and its synthetic CSV/JSON
  in `research/cpiv/generated/r11_price_resolution/`.
- Strict manifest verifier: `scripts/verify_sha256_manifest.ps1`; it passed
  against the existing R10 companion bundle (285 entries).
- PDF builder: `scripts/build_cpiv_review.py` now uses Cascadia Mono for code;
  the R10 final11 artifact was preserved and still has the documented text-layer
  issue.
- Verification: 44 focused tests pass; Ruff check passes; Ruff format passes on
  the six R11 modules/tests; targeted mypy passes on the three R11 modules.
  Including the builder in mypy reports three errors at its existing DOCX
  handling and return-typing sites, outside the changed font setting.
- R10 source and `dist/cpiv/r10-proposed-2026-10-10-final11/` remain unchanged.
  Temporary R11 HTML/DOCX/PDF validation outputs were built outside the project
  release tree; no R11 companion ZIP or manifest was generated.
- Current R11 is an incomplete working draft, not a submission-ready package.
  It uses only synthetic BSM inputs and closes no market-data gate. Remaining
  analyses and provider/source-rights review listed above are still open.
