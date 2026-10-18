# CPIV R10 revision audit — final11

**Audit date:** 10 October 2026 (ICT)  
**Release status:** local proposed revision; not submitted or venue-approved  
**Scope:** the final10 reviewer follow-up, the Appendix B source edit, and the
final11 HTML/DOCX/PDF and companion bundle.

## Change made

Appendix B now distinguishes the version range declared by the project from the
runtime actually checked. `pyproject.toml` declares Python `>=3.12`; final11 was
built and its 30 focused tests were run with Python 3.14.3. No other Python
version was tested for this release. This statement does not claim cross-version
test coverage. No scientific content, data, analysis, or results changed.

## Verification performed

- Companion-bundle tests: 30 passed in 46.89 seconds across the R10 diagnostics,
  review-builder, and educational-demo modules. Tests ran on Python 3.14.3 only.
- Runtime declarations: `pyproject.toml` contains `requires-python = ">=3.12"`;
  the observed tools were `uv 0.11.8` and Python 3.14.3.
- Ruff: all checks passed on the builder, diagnostics, cross-check helpers, and
  relevant tests.
- DOCX: `officecli validate` reported no errors. The DOCX package contains four
  tables, three embedded images, and 136 OMML math nodes.
- PDF: 15 A4 pages. Text extraction found 15 nonempty pages, ranging from 1,085
  to 4,324 characters. The changed Appendix B page and following References page
  (pages 14–15) were rendered and visually inspected; the new version boundary
  is legible and does not clip or disrupt the page break.
- HTML: four tables, three embedded data-URI images, and the labeled R8 baseline
  illustration remain present.
- The final11 HTML/DOCX/PDF in the companion bundle match the local artifacts by
  SHA-256. The package manifest and ZIP members were verified against the
  bundled files. The manifest excludes itself and the enclosing ZIP.

## Deliverables

| Format | Bytes | SHA-256 |
|---|---:|---|
| HTML | 523,458 | `7DFE3E9D5943D7C189EF5DD36BC4120839A0E71C4772C36D79D34D0C801F0FA0` |
| DOCX | 296,677 | `8C534BF04F8E786596CC7BEA24E434872C522D3ED3C24920E640613608C36A07` |
| PDF | 405,381 | `81FD888B6A7989A5D3DB5495C6FF61233E1CB7D05C231D87DB92966232AF0588` |

The outputs are under `dist/cpiv/r10-proposed-2026-10-10-final11/`. The
source-and-output bundle is
`dist/cpiv/quantcorner-cpiv-r10-companion-2026-10-10-final11.zip`.
Final10 remains preserved as the prior release.

## Evidence and scope boundaries

This remains a synthetic numerical/methods note. It contains no live option
quotes, market returns, positions, market-wide coverage census, or CPIV-alpha
evaluation. It makes no profitability, predictive-alpha, market-coverage, or
G5 claim. The identity checker is same-author code, not independent human
replication, a proof, or formal peer review. The release was not submitted to
QuantCorner, is not publicly archived, and has no assigned redistribution
license. Venue fit, source and asset rights, and venue-specific disclosure and
submission requirements remain author checks.

The prior review's optional Gaussian inversion benchmark, non-Gaussian-family
summary, and asymmetric-leg uncertainty case were not added; they were not
conditions for this version-reporting correction.
