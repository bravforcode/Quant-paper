# CPIV R22 review follow-up — 12 October 2026

## Outcome

The requested R22 revisions were implemented, numerically checked against the supplied checker and the project reproduction pipeline, and packaged as new local HTML, DOCX, and PDF files. The previous v21 package was not overwritten. This remains a synthetic methods note; it does not close G5 or establish empirical market performance.

## Review items checked

1. **Leg-specific OTM-equivalent time value.** The manuscript defines `X_C` and `X_P` separately and states `X_C - X_P = R`; equality is limited to zero-residual cases. The pair screen is `min(X_C, X_P) >= t`, and the finite-shock rule retains leg- and direction-specific inversion requirements. Regression tests cover the definitions and guard against the stale “base premium” wording.
2. **Stale tick wording.** The inconsistent sentence was replaced: tick rows now compare the pair minimum of the leg-specific OTM-equivalent time values with the row's tick; half-spread rows use the declared reference tick.
3. **Cubic scaling and off-centre reference sensitivity.** The project pipeline reproduced its 720-cell grid (624 baseline-guard pass; 96 fail). Across 104 configurations, the median log-log slope is 3.0003 (range 2.8733–3.0441). For absolute target spreads 0.5, 1, and 2 pp, median absolute errors are 8.3875e-6, 6.7119e-5, and 5.3754e-4 pp; nearest-rank p95 values are 0.006630, 0.053070, and 0.425464 pp. With a signed reference offset of +/-1 vol point, the 1,248 evaluations have median absolute error 0.042381 pp, p95 1.476687 pp, and max 32.554749 pp. At +/-2 points, median is 0.082799 pp, p95 5.183761 pp, and max 945.282847 pp. The +/-5 and +/-10 point tails become extremely large under the local-derivative denominator; 168 cases are skipped at +/-10 when the reference volatility is nonpositive. These are conditional synthetic diagnostics, not expected market errors.
4. **Provenance of the attached checker.** `C:\Users\menum\Downloads\cpiv_d3_offcenter_check.py` was treated as an AI-assisted, separately coded numerical cross-check as described by the reviewer, not as independent human replication. Its reported grid results were compared with the project's own output; agreement supports reproducibility of the stated synthetic specification, not external validation.

The revised note explains that midpoint symmetry yields a leading cubic term, `R/nu(sigma_0) = d + (d^3/24) nu''(sigma_0)/nu(sigma_0) + O(d^5)`, while reference-volatility displacement can materially change the approximation. It also says the approximation is diagnostic only when the reference is specified separately; when both leg IV roots are available, CPIV is their direct difference.

## Reproduction and checks

- Fresh generated output: `research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-12_v2/`; its reproduction manifest says `market_data_used: false`, Python 3.12.10.
- `reference_sensitivity_summary.json` records the complete spread and off-centre summaries; its input-grid SHA-256 is `4b778f039d7367f238fd5d711a19926c08be46b1c25380e09111d0243c835b5d`.
- Full tests: 284 passed. After the final manuscript and type-annotation edits, 33 focused CPIV/manuscript/builder tests passed. Ruff passed. Targeted mypy passed on seven relevant source files; this is not a project-wide clean mypy result (the broader checked set still reports existing errors in `research/cpiv/r10_diagnostics.py`).
- HTML: 5 image elements, all with embedded `data:image/` sources; 0 `data-embedded-src`; 10 tables.
- DOCX: ZIP integrity check passed; 10 tables, 5 drawing elements, and 5 media files.
- PDF: 26 pages; extracted text length 62,440 characters; Table 1, Table 5, Table 6B, Table 8, and the 0.042381 offset result are present; 0 U+2010 characters in the text layer.

## Local deliverables

Directory: `dist/cpiv/quantcorner-cpiv-reviewed-2026-10-12-v22/`

| File | Bytes | SHA-256 |
|---|---:|---|
| `quantcorner-cpiv-review-r22-2026-10-12.html` | 1,015,730 | `ED89591C654B914B6D6A30355498D3900193990CE79332C2025046029BC1A6EB` |
| `quantcorner-cpiv-review-r22-2026-10-12.docx` | 631,846 | `9B53CBEC98C499D2966A987671857FF666C0A9DE859C2EAB711FE5969ACD896B` |
| `quantcorner-cpiv-review-r22-2026-10-12.pdf` | 745,194 | `C9349634EFBB51FEE19DEBFB8420DE36658207C8765A0775A7481C956AC179D3` |

## Still open — do not overstate readiness

- No market options or market-wide positions were used; **G5 remains OPEN / NOT MET**. No coverage or cold-start estimate is produced by this methods-only revision.
- No public code archive, reuse license, or DOI-backed deposit exists. The manuscript itself states this limitation.
- The configured cross-platform CI was not run in this pass.
- Analytical ranking/SNR/test-retest benchmarks and an independent American-option/Richardson benchmark remain unimplemented.
- Raw links, provider terms, and publication permissions were not re-audited in this pass.
- No email, provider contact, public deposit, Google Doc edit, or submission was made.
