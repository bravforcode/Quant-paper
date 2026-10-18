# CPIV R10 revision audit — final10

**Audit date:** 10 October 2026 (ICT)  
**Release status:** local proposed revision; not submitted or venue-approved  
**Scope:** the supplied final9 review note, the current R10 manuscript and
generated outputs, and the final10 HTML/DOCX/PDF plus companion bundle.

## Changes made

1. Added the missing reproduction prerequisites to Appendix B: Windows
   PowerShell, `uv` 0.11.8, and Python 3.12 or newer, with Python 3.14.3
   identified as the build environment.
2. Consolidated the Section 9 identity-checker caveat. It now says once that
   the checker is a second code path by the same author, not an independent
   replication by another researcher or formal peer review.
3. Added an analytical chance reference for the existing top/bottom turnover
   metric in Section 7.5. For a uniformly random ranking and two fixed tails of
   size `k`, expected overlap with each tail is `k²/n`; hence expected turnover
   is `1 - (2k²/n)/(2k) = 1 - k/n`. With `k = n/5`, this is exactly 0.8.
   The near-tied values 0.7917 (`n = 10`) and 0.7977 (`n = 50`) are 0.75 and
   0.49 of their reported MCSEs below that reference, respectively. This is a
   theoretical reference for the stated synthetic metric, not a market result.
   No simulation was rerun for this algebraic addition.
4. Rebuilt the HTML, DOCX, and PDF as final10; created a separate final10
   companion bundle while preserving the final9 artifacts.

## Verification performed

- Companion-bundle tests: 30 passed across the R10 diagnostics, review-builder,
  and educational-demo test modules (run from the extracted-style final10
  bundle using the local Python 3.14.3 environment).
- Ruff: all checks passed on the builder, diagnostics, cross-check helpers, and
  relevant tests.
- DOCX: `officecli validate` reported no errors. The DOCX package contains four
  tables, three embedded images, and 136 OMML math nodes.
- PDF: 15 A4 pages. Text extraction found 15 nonempty pages; page text lengths
  ranged from 1,062 to 4,267 characters. Contact sheets for all pages and
  full-resolution renders of pages 10, 14, and 15 were visually inspected.
  The new chance-reference paragraph and Appendix B prerequisites are legible
  and not clipped. Appendix B's code block continues across a page break; text
  remains present on both pages.
- HTML: four tables, three embedded data-URI images, and the interactive R8
  baseline illustration remain present and explicitly labeled as not an R10
  result.
- Bundle consistency: the three final10 files in the companion bundle match
  the corresponding local release files by SHA-256. The package manifest and
  ZIP contents were checked against the bundled files; the manifest excludes
  itself and the enclosing ZIP.

## Deliverables

| Format | Bytes | SHA-256 |
|---|---:|---|
| HTML | 523,378 | `6E92E529B5E0CC8888F7A009F28CFA526BD972DBA83EA271AAE58F780E0CE3A3` |
| DOCX | 296,641 | `FA66E30F8F5EBB9EB5534373934432AB02AA8AE20FC4EE89A3636BF7A22CA71E` |
| PDF | 405,304 | `E9EC56B54CFA083C54EE8459CD787BB1C5EA9DDB57317528A8760545690D14BC` |

The outputs are under `dist/cpiv/r10-proposed-2026-10-10-final10/`. The
source-and-output bundle is
`dist/cpiv/quantcorner-cpiv-r10-companion-2026-10-10-final10.zip`.

## Evidence and scope boundaries

This remains a synthetic numerical/methods note. It contains no live option
quotes, market returns, positions, market-wide coverage census, or CPIV-alpha
evaluation. It makes no profitability, predictive-alpha, market-coverage, or
G5 claim. The identity checker is same-author code; it is not independent
human replication, a proof, or formal peer review. The reviewer-supplied
CPython 3.12 bytecode and CSV are not included because their linkage,
execution record, and reuse rights have not been established.

The package is local-only, has no public archive or assigned redistribution
license, and was not submitted to QuantCorner. Before any external submission,
the author still needs to verify venue fit and length, source and asset rights,
and venue-specific disclosure/submission requirements. Optional analytical
extensions mentioned in prior reviews (additional noise-family summaries,
alternative inversion benchmarks, and asymmetric-leg uncertainty cases) were
not added in this revision; they were not required to make the two requested
reproduction disclosures or the exact chance reference.
