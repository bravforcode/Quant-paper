# CPIV R11 review follow-up — 11 October 2026

## Scope and outcome

This follow-up implements the review's distinction between price identification and IV precision, preserves incomplete zero-bid comparisons as partial-order information, cleans the manuscript's user-facing revision labels, and rebuilds the standalone package. The note remains synthetic-only. It contains no historical option quotes, market-wide positions, liquidation census, returns, or alpha estimates; it does not close the separate G5 liquidation-evidence gate.

## Changes made

- **Separate identification from precision.** A leg is `Identified` only when the base premium is not below its declared reference tick and both finite shocks have admissible implied-volatility roots. Conditional on identification, it is `Within τ_IV` only when the maximum one-sided absolute IV displacement from the unshocked base is no greater than the declared threshold. This is a precision convention, not a market-wide standard, and it is not the full interval width.
- **Reported threshold examples.** In the synthetic ATM 30-day, 20%-IV example, the maximum one-sided displacement is 0.087469 pp: within illustrative τ_IV = 0.10 pp, but not 0.05 pp. The deep example has a base premium below the hypothetical tick; its upward shock moves IV by 7.0717 pp and its downward shock has no root, so it is unresolved at either threshold.
- **Retained incomplete rank pairs.** A zero bid/no-root endpoint is not imputed or dropped. The pair remains incomplete with a one-sided bound; it is an unresolved partial-order comparison unless the available bounds establish ordering.
- **Improved DOCX page starts.** The Word builder now derives the expected figure-caption count from the source and applies page-break-before to Table 4, Table 5, and Table 5B captions. A previous builder assumption of three figures was stale; the current source has five. Word opened the final DOCX and reported the Table 5 caption/table on p. 17, Table 5B caption/table on p. 18, and Table 4 caption/table on p. 22.
- **Corrected support disclosure.** The manuscript states no external cash funding, discloses the author's complimentary one-month HyperTracker Surge subscription from CoinMarketMan as in-kind support during the broader project, and states that no HyperTracker data were used in this synthetic note. “No competing interests” remains the author's declared statement and should be personally reconfirmed before submission in light of the in-kind support.
- **Made reproducibility limits explicit.** The manuscript says that source code/input bundles are not embedded or publicly archived and that no reuse license or DOI-backed archive is assigned. It distinguishes local test execution from the configured-but-unexecuted Linux/Windows CI matrix and explicitly says Python 3.12/3.13 and Bash were not locally tested.

## Deliverables

All files are in `dist/cpiv/quantcorner-cpiv-reviewed-2026-10-11-v16/`.

| File | Size | SHA-256 |
|---|---:|---|
| `quantcorner-cpiv-review-r21-2026-10-11.html` | 949,640 B | `EF8BC41D54941AA350272FAB514CAF1B06C74274B3B4872013D417C2BCA12517` |
| `quantcorner-cpiv-review-r21-2026-10-11.docx` | 533,272 B | `80D068E160846D758D128B8FBC64A5E63D1F56A20CA7B3E2A08A78BFD1ABA447` |
| `quantcorner-cpiv-review-r21-2026-10-11.pdf` | 704,864 B | `3053532BBFADAC43F25562B2B9F7D9FACAF7D47E63471CD1BEFFDDBE6AEEBFDC` |

## Verification evidence

- `uv run python -m pytest tests -q`: **278 passed**.
- `uv run ruff check`: passed for the full repository.
- `uv run mypy --explicit-package-bases research/cpiv/r11_price_resolution.py scripts/build_cpiv_review.py scripts/reproduce_cpiv_methods.py`: passed, 3 files.
- The exact appendix entry points were exercised: `uv run python -m scripts.reproduce_cpiv_methods --help` and `uv run python -m pytest ...` without a `PYTHONPATH` override both worked.
- A fresh synthetic reproduction is at `research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-11_v2/`. Its manifest lists 53 generated files plus the manifest itself, records Python 3.14.3 and `market_data_used: false`, and uses τ_IV = 0.10 pp. It contains synthetic assets only.
- **HTML:** standalone file; 5 image elements, 6 embedded PNG payloads, 194 MathML expressions, no `data-embedded-src` attributes. The range-control/JavaScript widget is present. I did not perform a fresh browser click-through in this pass.
- **DOCX:** ZIP integrity check passed; 8 tables, 194 MathML equations, 5 media items, and 3 `pageBreakBefore` tags. Word COM opened and paginated it at 26 pages; caption/table page positions are recorded above. Word's PDF export call timed out after 120 seconds, so this is not claimed as a Word-exported PDF.
- **PDF:** built directly from the manuscript source with the configured XeLaTeX pipeline; 23 A4 pages. Pages 14–17, 19–20 and the declarations page (p. 21) were visually inspected. The text layer contains zero U+2010 and zero U+2011 characters. Figures 4 and 5 appear on pp. 16–17; Table 4 spans pp. 19–20.
- **DOCX schema caveat:** `officecli validate` reports 8 unexpected `m:sty` children inside Office Math run properties. Word opens and paginates the file, but schema validation is not recorded as passing; this needs a validator/schema cross-check before claiming a clean OpenXML validation.
- `.github/workflows/cpiv-repro.yml` was syntax-parsed with PyYAML. `actionlint` was unavailable and the workflow was not executed on GitHub; the workspace has no `.git` repository/remote.

## Remaining gates

1. **Public source archive, license, DOI:** not created. Selecting a reuse license and publishing code/data are author decisions; no public repository or DOI is claimed. The source modules and some generated filenames still carry R10/R11 identifiers and should be normalized before any public code deposit.
2. **Cross-environment execution:** only Python 3.14.3/Windows was locally tested. Python 3.12/3.13, Linux, Bash, and the remote CI matrix remain unverified.
3. **Additional methods analyses:** off-center σ₀ and cubic-order error characterization; analytical ranking benchmarks including SNR and test–retest reliability; and an independent American-option benchmark with Richardson extrapolation remain open.
4. **Author confirmation:** personally reconfirm the in-kind-support and competing-interest wording before sending.
5. **Market evidence/G5:** no market-position or liquidation census was collected or analyzed. This CPIV methods note does not satisfy or reclassify G5.
6. **External actions:** no email, Google Doc, public archive, or QuantCorner submission was changed or sent.

The local manuscript package now represents the synthetic methods note and its stated limitations more faithfully. Submission/readiness is conditional on the venue accepting the disclosed non-archived source status and on the author confirming the declaration; the broader reproducibility and market-evidence gates are not closed.
