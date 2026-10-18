# CPIV R11 review follow-up — final local package, 11 October 2026

This report supersedes the local-package references in follow-up v3. The work addresses the review's price-identification/precision distinction, incomplete quote-pair handling, internal-label cleanup, build pagination, Appendix B command clipping, and support disclosure. It remains a synthetic methods note; it does not close the separate market-position/liquidation G5 gate.

## Final files and checksums

Directory: `dist/cpiv/quantcorner-cpiv-reviewed-2026-10-11-v17/`

| File | Size | SHA-256 |
|---|---:|---|
| `quantcorner-cpiv-review-r22-2026-10-11.html` | 949,512 B | `4A524FCE941BBF4AD0DB2A23B63294F7AEF455DC660F315403778C3E5EEA2096` |
| `quantcorner-cpiv-review-r22-2026-10-11.docx` | 533,248 B | `54450F40D251E945D5C481163BEA39D2E5978A4D65E99EAFFFE4B6C011D22A14` |
| `quantcorner-cpiv-review-r22-2026-10-11.pdf` | 704,650 B | `45E775388B2C3DC56D4A28C5A1211A945BC9A9D4F952404DC77D0C8410BBCA71` |

## Review points implemented

- **Identification vs. precision:** “Identified” requires a base premium at or above its declared reference tick and finite IV roots for both price shocks. “Within τ_IV” is a separate qualification requiring the maximum one-sided absolute IV displacement from the base to be at most τ_IV; it is not full interval width and τ_IV is not presented as a market standard.
- **Illustrative outcomes:** the synthetic ATM 30-day, 20%-IV case moves 0.087469 pp at the largest one-sided shock, passing τ_IV = 0.10 pp but failing 0.05 pp. The deep case has a sub-tick base premium; the upward shock moves IV 7.0717 pp and the downward shock has no root, so the case is unresolved at either threshold.
- **Zero bid / missing endpoint:** one-sided bounds are retained; the pair is not imputed or dropped. It remains an unresolved partial-order comparison unless the observed bounds establish the ordering.
- **Support disclosure:** no external cash funding; the author received a complimentary one-month HyperTracker Surge subscription from CoinMarketMan as in-kind support during the broader project; this note uses no HyperTracker data and reports only synthetic results. The author declares no competing interests; the author should reconfirm that declaration before sending given the in-kind support.
- **Word pagination/build defects:** the figure count is source-derived rather than hard-coded; the builder applies page breaks to Table 4, Table 5, and Table 5B. A clipped long reproduction-output path in Appendix B was replaced with `out/cpiv-repro`; final PDF p. 22 was visually checked and both PowerShell and Bash commands fit.
- User-facing manuscript text contains no R8/R10/R11 labels or machine-local paths. Internal source module/test filenames still carry R10/R11 names; normalize them before any public source deposit.

## Verification evidence

- `uv run python -m pytest tests -q`: **278 passed**.
- Test-stability note: one earlier full run had 277 passes and a single timing-sensitive failure in the unrelated `RequestPacer` spacing test (one measured delay differed from 1 ms by 0.0001435 s). That test passed in isolation and the subsequent full rerun passed 278/278; no test or pacer code was changed.
- `uv run ruff check`: passed for the repository.
- `uv run mypy --explicit-package-bases research/cpiv/r11_price_resolution.py scripts/build_cpiv_review.py scripts/reproduce_cpiv_methods.py`: passed for all 3 specified files.
- Exact appendix entry points were checked. `uv run python -m scripts.reproduce_cpiv_methods --help` and module-form pytest run without a `PYTHONPATH` override.
- Fresh synthetic reproduction: `research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-11_v2/`; manifest records Python 3.14.3, `market_data_used: false`, τ_IV = 0.10 pp, and 53 generated files plus the manifest. No market quotes or HyperTracker data were used.
- **HTML:** 5 image elements, 6 embedded PNG payloads, 194 MathML expressions, range-control script present, and zero `data-embedded-src` attributes.
- **DOCX:** ZIP integrity passed; 8 tables, 194 MathML expressions, 5 media assets, 3 `pageBreakBefore` tags. Word opened and paginated it at 26 pages: Table 5 caption/table p. 17; Table 5B caption/table p. 18; Table 4 caption/table p. 22.
- **PDF:** direct XeLaTeX build from the manuscript source, 23 A4 pages; Figures 4–5 on pp. 16–17; Table 4 on pp. 19–20. Pages 14–17, 19–23 were visually inspected, including the funding statement and Appendix B commands. Text-layer scans found zero U+2010/U+2011.
- **Limitations of format validation:** Word `ExportAsFixedFormat` timed out after 120 seconds, so the delivered PDF is not claimed to be exported from the DOCX. `officecli validate` reports 8 unexpected `m:sty` children in Office Math run properties; validation is therefore not claimed clean. Word opened and paginated the DOCX, but a second independent OpenXML-schema validation is still needed.
- `.github/workflows/cpiv-repro.yml` parses as YAML. `actionlint` is unavailable, no `.git` repository/remote exists in the workspace, and GitHub CI was not run.

## Still open; not represented as complete

1. No public source repository, reuse license, or DOI-backed archive exists. Public release is an author decision; the manuscript discloses this and does not claim publicly reproducible code availability.
2. Only Windows/Python 3.14.3 was locally tested. Python 3.12/3.13, Linux, Bash, and the remote CI matrix are unverified.
3. Additional analyses remain: off-center σ₀ / cubic-order error characterization; analytical ranking benchmarks including SNR and test–retest reliability; an independent American-option benchmark with Richardson extrapolation.
4. No historical options, market positions, liquidation census, returns, or alpha data were analyzed. The CPIV note does not satisfy or reclassify liquidation G5.
5. No email, Google Doc, public repository/archive, or QuantCorner submission was changed or sent. Raw-source/venue terms and final author declarations need the author's own sign-off.

The local manuscript files now implement the reviewed methods-only corrections. Whether the version is acceptable to QuantCorner remains conditional on the venue's preference about code archiving and the author's final confirmation of the disclosure; public reproducibility and market-evidence gates remain open.
