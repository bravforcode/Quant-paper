# CPIV R10 revision audit — final9

**Audit date:** 10 October 2026 (ICT)  
**Release status:** local proposed revision; not submitted and not venue-approved  
**Scope:** the supplied 10 October review, the current manuscript source, generated
synthetic outputs, and the final9 HTML/DOCX/PDF artifacts.

## Changes made

1. Corrected the normalized-vega denominator. The 720 rows are six spread cells
   for each of 120 configurations; normalized midpoint vega is spread-invariant.
   Its failure-group summary now uses the 16 unique configurations, not 96
   repeated rows, and reports the median and maximum without a redundant p95.
2. Added the separation visible in this synthetic grid: 104 configurations
   passed the configured absolute-vega guard; their minimum normalized vega is
   `7.2989e-6`. The 16 unresolved configurations have a maximum of
   `1.7239e-10`. The ratio is about 42,339 (4.63 orders of magnitude). The
   manuscript explicitly limits this result to the specified grid; it does not
   validate a market-data threshold or generalize to market observations.
3. Changed the generated-output path to the stable
   `research/cpiv/generated/r10_release/` and refreshed all three documents.
4. Expanded Appendix B with the separately coded BSM check, the Decimal
   near-bound audit, and a command to check the as-shipped SHA-256 manifest
   before any regeneration command.

## Numerical evidence

The local generated grid and the regenerated diagnostic summary contain 720
spread cells, 120 unique configurations, and six spread cells per
configuration. There are 624 resolved spread cells (104 configurations) and
96 unresolved spread cells (16 configurations). For the 16 unique unresolved
configurations, normalized midpoint vega has median `1.4039327684551616e-14`
and maximum `1.7239174110291308e-10`. The minimum among the 104 resolved
configurations is `7.298911863095962e-06`; the ratio is `42339.1040`, or
`4.62674` log10 orders. These figures were read from the generated grid and
reproduced by the project diagnostic run; the attached `.pyc` was not run.

The separation is descriptive of the specified synthetic grid and its guard.
It is not evidence of a universal or market-validated cutoff, and this release
contains no live option quotes, market returns, or CPIV-alpha evaluation.

## Verification performed

- Focused tests: 30 passed across the R10 diagnostics, review builder, and
  educational-demo test modules.
- Ruff: all checks passed for the changed implementation and test files.
- DOCX: `officecli validate` reported “Validation passed: no errors found.”
  The DOCX package contains four tables, three embedded images, and OMML math.
- PDF: 15 A4 pages. Page text extraction found no blank/short pages. A contact
  sheet of all pages and full-resolution renders of pages 14–15 were visually
  reviewed; Appendix B commands are legible and not clipped. Three figures are
  embedded in the PDF.
- HTML: 4 tables and 3 embedded data-URI figures; the separate R8 widget remains
  identified as a baseline illustration, not an R10 result.
- Reproduction smoke checks: the Appendix B BSM cross-check wrote four cases;
  the Decimal audit processed 16 generated near-bound cases.
- The repository's `audit_pdf_delivery.py --check-delivery` was also run, but
  it is a legacy G5/Hyperliquid-specific gate: it expects G5 phrases and
  evidence links that do not belong in this CPIV note and failed those checks.
  It is not represented as a passing CPIV PDF test.

## Supplied bytecode and CSV provenance

The newly attached file
`C:/Users/menum/Downloads/cpiv_grid_crosscheck.cpython-312.pyc` is 4,497 bytes
with SHA-256
`FFB6E1FDFDFDBF8D64024E8B56C3609F27D9821045D797EC6A21C3AB728AA6D4`.
It was inspected as compiled CPython 3.12 bytecode without executing it. Its
embedded docstring describes it as an AI-reviewer cross-check based on the
manuscript specification and says it is not a human replication; its embedded
source filename is `/home/user/output/cpiv_grid_crosscheck.py`. Those embedded
strings are not independently authenticated provenance. Static inspection
does not establish who authored the file, how it was run, or that a particular
CSV came from it.

A separate 720-row CSV already present in Downloads,
`r10_independent_approximation_grid_audit.csv`, has SHA-256
`3959A1E9FEBC888C589226ED86498BD0E02EF00D9E822384B9EB1D722D01C060`.
Its linkage to the newly attached bytecode and execution environment is not
established. Neither file is included in the companion bundle. No claim of
independent human replication is made; obtain source, run instructions, and
reuse/redistribution permission before treating either as a release artifact.

## Deliverables

| Format | Path | SHA-256 |
|---|---|---|
| HTML | `dist/cpiv/r10-proposed-2026-10-10-final9/quantcorner-cpiv-review-r10-2026-10-10.html` | `D4942FC4AA8551488E9CE7C2241E8DCE2A3D8B5EAC322A2BB870AC763F94087E` |
| DOCX | `dist/cpiv/r10-proposed-2026-10-10-final9/quantcorner-cpiv-review-r10-2026-10-10.docx` | `6FFE7B0773227C8AE23FAA21BA8CC6A809A2DC1733593741E9C9CCC6B67ED929` |
| PDF | `dist/cpiv/r10-proposed-2026-10-10-final9/quantcorner-cpiv-review-r10-2026-10-10.pdf` | `4DE846BE3D54EB0A09DE64BA8937DBF128F0F286FDFC7B754FDB6844F224AE48` |

Final8 was not edited. The companion ZIP is assembled and verified separately;
its manifest contains 236 file entries, all of which were checked against the
extracted bundle; all 237 ZIP members (including the manifest) were read and
verified against the package contents. The manifest excludes itself and the
enclosing ZIP.

## Remaining author/venue gates

This is a synthetic measurement/methods note, not a market-validated CPIV
strategy or investment-performance study. It makes no profitability, alpha,
market-wide coverage, or G5 claim. Before external submission, the author must
check venue fit and length, verify source and rights for all cited material and
assets, and satisfy the venue's disclosure and submission requirements. No
email, form, Google Doc, or external submission was sent or changed in this
work.
