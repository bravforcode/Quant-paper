# CPIV R10 revision and release audit — final7, 9 October 2026

## Status and scope

This is a local proposed revision, not a submission, acceptance, or venue
approval. The work addressed the supplied R10 review, checked the supplied
approximation-grid CSV against the generated grid, rebuilt the manuscript as
HTML/DOCX/PDF, and assembled a reproducibility companion package. The study
remains synthetic: it uses no historical option-chain data, positions,
market-wide census, or return/alpha test.

Review input: `C:/Users/menum/.codex/attachments/3de73c4c-3368-40a2-bce2-d6bfcdd28852/Pasted text.txt`.

## Review items addressed

- Corrected the introduction's protocol cross-reference to Table 4.
- Defined the reported p95 as the nearest-rank quantile. For 624 resolved
  observations, this is the 593rd ordered value.
- Stated that call- and put-endpoint errors are summarized separately, not
  pooled into one 1,248-observation sample. The two endpoint grids are
  symmetric by construction.
- Defined normalized midpoint vega, including the discounted-underlying scale
  denominator and units; documented the 120-case scale experiment and its
  guard-resolution counts.
- Added explicit spot, carry, quote, and American-put experiment defaults.
- Specified the uncertainty-budget covariance matrix: diagonal except for the
  stated call–put premium-error covariance; spot, rate, and yield errors are
  mutually independent and independent of premium errors; strike and maturity
  are fixed.
- Replaced the mismatched Jarrow–Rudd 1982 higher-moment citation with the
  bibliographic entry for Jarrow and Rudd (1983), *Option Pricing*. This checks
  citation/source fit; it is not a fresh derivation of the tree from the book.
- Clarified the cross-scheme American-put difference at 6,400 steps and the
  common-random-number design without upgrading either diagnostic into a
  convergence proof or market estimate.
- Shortened an overlong inline source path after visual inspection showed the
  PDF clipped its ending on page 4. The final7 layout moves the full paragraph
  to page 5; extracted page text and the rendered page show the complete name.
- Moved the English abstract to a fresh PDF page so it no longer breaks across
  pages 1–2 mid-sentence. The Thai summary and front matter remain on page 1.
- Started Section 6 on a fresh PDF page after the abstract page break exposed a
  one-line heading/paragraph split at the bottom of page 4.
- Added a companion package with source, generated inputs/outputs, commands,
  tests, review notes, visual QA captures, and a SHA-256 manifest.

The review's optional additional experiments—such as an analytical-inversion
baseline, random-turnover baseline, more noise families, unequal-vega stress,
and MCSE for the SD comparison—were not added. They are new analyses, not
editorial corrections, and remain outside this revision. No empirical or
predictive claim is added.

## Supplied CSV cross-match

External file:
`C:/Users/menum/Downloads/r10_independent_approximation_grid_audit.csv`  
SHA-256: `3959A1E9FEBC888C589226ED86498BD0E02EF00D9E822384B9EB1D722D01C060`

Compared with
`research/cpiv/generated/revision_20261009_r10_proposed_final5/local_approximation_grid.csv`
(SHA-256 `4B778F039D7367F238FD5D711A19926C08BE46B1C25380E09111D0243C835B5D`).
All 720 six-field design keys matched one-to-one. Field mapping was: `ratio`,
`days`, `v`, `dpp`, `r`, and `q` to spot/strike ratio, days to expiry,
reference IV, target CPIV, rate, and effective yield; `vega` to midpoint vega;
the three `error_*` fields to midpoint, put-endpoint, and call-endpoint
absolute errors.

Among the 624 cells resolved by the configured absolute-vega guard, maximum
absolute differences were `1.33e-15 pp` for midpoint error, `7.11e-15 pp` for
each endpoint error, and `1.07e-14` in midpoint-vega units. The remaining 96
cells are explicitly unresolved. Their extreme raw approximation magnitudes
produce absolute cross-file differences up to 13,631,488 pp, while the maximum
relative difference is about `6.7e-15`; they are excluded from the reported
resolved-grid summaries.

This is a row-wise numerical consistency check only. The supplied CSV has no
verifiable author, generation record, or method metadata here, so its
provenance and claimed independence are not established. It is not redistributed
in the companion package because source and reuse rights are unverified.

## Reported grid summaries

For the 624 resolved cases, midpoint absolute error has median `0.00007858 pp`,
nearest-rank p95 `0.08720301 pp`, and maximum `1.23551964 pp`. Each endpoint
summary is reported separately: median `0.02024694 pp`, p95 `1.17522948 pp`,
and maximum `32.55474925 pp`. The identical endpoint summaries follow from the
constructed symmetry; they are not pooled and are not market-weighted.

## Build and verification

- Final artifacts built successfully with exit code 0. XeLaTeX/MiKTeX printed
  update-check notices (“not checked for MiKTeX updates”); they did not fail
  the build.
- Full project test suite before final layout corrections: **252 passed**.
  For final7, focused diagnostic/builder tests passed **16 tests in 29.35
  seconds**, and Ruff reported “All checks passed” for the changed R10
  diagnostic/test files.
- `officecli validate` passed for the rebuilt DOCX.
- The final7 companion ZIP passed an independent integrity check: 151 manifest
  entries all match, all archive CRCs pass, there are no unlisted files, and
  the user-supplied CSV and JWT-like credentials are absent. A first packaging
  attempt used a .NET path API unavailable in the PowerShell host; that
  malformed generated archive was removed and replaced before delivery.
- Visual QA checked the DOCX contact sheet and PDF pages covering the title
  and summary, changed numerical sections, figures, protocol table, declarations,
  and references. The final7 PDF is 14 A4 pages; the DOCX is 16 pages and
  4,481 words. The English abstract starts on PDF page 2; Section 6 starts with
  its opening paragraph on page 5; the full source-checker name is visible.
- HTML inspection found four embedded PNG data images, no `file://` references,
  and no `data-embedded-src` image attributes. HTML math rendering may still
  depend on the configured browser/runtime resources; this check does not
  claim offline behavior for every browser.
- No external email, form, Google Doc, public archive, or submission was sent
  or changed in this work.

## Final local artifacts

Files are under
`dist/cpiv/r10-proposed-2026-10-09-final7/`:

| Format | File | Bytes | SHA-256 |
|---|---|---:|---|
| HTML | `quantcorner-cpiv-review-r10-2026-10-09.html` | 507,398 | `11FA6D79EA6569FB38508E360AF62BA7450ECFB3A0CB436483B737B6B82D9BC4` |
| DOCX | `quantcorner-cpiv-review-r10-2026-10-09.docx` | 293,662 | `87F8F06BC5022FCA99152B774762B78B8E8A12FCE221F78AB839B621F28E6760` |
| PDF | `quantcorner-cpiv-review-r10-2026-10-09.pdf` | 383,965 | `BA5F48CC7231034285467365472E54E8BF2DF78E1D16A50CFB2C2BBA3D891C29` |

The package manifest records the exact companion-bundle files. Local hashes
identify bytes; they do not confer a license or establish publication rights.
The author must still verify source/data permissions and venue requirements
before public release.
