# CPIV research-note workspace

## R11 working revision (2026-10-10; price-resolution and bound-audit tracks)

- Working manuscript: `research/cpiv/manuscript_r11_proposed.md`.
- Added diagnostic: `research/cpiv/r11_price_resolution.py`; outputs are in
  `research/cpiv/generated/r11_price_resolution/`.
- Bound-first replay: `research/cpiv/r11_near_bound_audit.py`; it separates
  exact-bound guard cases from interior near-bound cases and strict violations.
- Focused tests: `tests/test_cpiv_r11_price_resolution.py`.
- This revision implements separate tick / quote half-spread / roundoff
  sensitivities and corrects the near-bound group counts. The Table 4
  carry/forward stage and other R11 review items remain open; this is not a
  submission-ready package.
- R10 final11 files and source remain preserved. R11 uses only synthetic BSM
  inputs and makes no market-data or alpha claim.

## R10 proposed measurement note (2026-10-10; final11)

- Manuscript source: `research/cpiv/manuscript_r10_proposed.md`.
- Diagnostics: `research/cpiv/r10_diagnostics.py`; generated CSV/JSON/PNG/SVG
  evidence: `research/cpiv/generated/r10_release/`.
- Local HTML/DOCX/PDF: `dist/cpiv/r10-proposed-2026-10-10-final11/`.
- Audit disposition: `reports/cpiv_r10_revision_audit_2026-10-10-final11.md`.
- Source-and-output companion ZIP:
  `dist/cpiv/quantcorner-cpiv-r10-companion-2026-10-10-final11.zip`.
- Final10 and earlier artifacts remain preserved for comparison.
- R10 is a proposed synthetic measurement note, not an empirical CPIV-alpha
  study. No market quotes, returns, positions, or liquidation census are used;
  no market-data or alpha gate is closed. The package is local-only, has no
  public archive, and has no assigned reuse license.
- The precomputed R8 widget is labeled and moved to Appendix A; it does not
  execute R10. Appendix B lists the diagnostic regeneration commands. R10
  results are supplied as machine-readable data/static figures. The R10
  identity countercheck is same-author code, not independent human replication.
- Final11 carries forward final10's normalized-vega summary for 16 unique
  failing configurations (six spread cells each), the grid-only pass/fail
  separation, stable `r10_release` output path, and reproduction commands for
  the identity check, Decimal audit, and package-manifest verification.
  Appendix B declares Python >=3.12 in `pyproject.toml` and states that final11
  was built and its 30 focused tests were run on Python 3.14.3 only; no other
  version was tested. Section 9 combines the authorship/reproduction limitation.
  Section 7.5 adds the exact 0.8 uniform-random-ranking reference for
  top/bottom quintile turnover. Final10 and earlier corrections remain intact.

R8/R9 files below are historical versions and remain preserved.

This is a new, separate article following QuantCorner's suggestion to focus on
call–put implied-volatility spreads in U.S. single-stock options. It does not
replace or revise R23 and does not change the status of the earlier G5 work.

## R9 proposed methods note (2026-10-09)

- Source: `research/cpiv/manuscript_r9_proposed.md`.
- Diagnostics: `research/cpiv/r9_diagnostics.py`.
- Generated inputs/results: `research/cpiv/generated/revision_20261009_r9_proposed/`.
- HTML/DOCX/PDF: `dist/cpiv/quantcorner-r9-proposed-final-2026-10-09/`.
- Build command is recorded in the revision audit report. The standalone HTML
  contains the separate R8 fixed-seed widget; it does not run the R9 simulation.
- R9 is a separately versioned proposed technical note, not an empirically
  validated CPIV/alpha paper. The original R8 source and delivery remain intact.
- No public archive or reuse license is assigned. Do not describe the package
  as a public release until access and terms are resolved.

R8 is a separately versioned source at research/cpiv/manuscript_r8.md. It
reframes CPIV as a local put–call-parity-residual/vega mapping and adds
recomputed synthetic carry, exercise-style, timestamp, and vega-scaled noise
experiments while preserving the R7 deliverables.

## Evidence boundary

- The included ten-pair example is synthetic and deterministic.
- No market quote, historical options chain, API key, provider export, return,
  backtest, alpha estimate, or holdout result is included.
- The named long/short buckets illustrate ranking only; they are not advice.
- Empirical claims are attributed to the cited studies; they are not results
  from this package.
- R8 uses a local European-BSM parity-residual/vega approximation; R9 derives
  the exact average-vega identity for paired European BSM inversions and keeps
  the local conversion explicitly approximate.
- Simulated quote noise and rankings do not estimate market quote quality or
  expected trading costs.
- No file is sent to QuantCorner, Google Docs, or email by the build process.

## Build and verify

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe research\cpiv\build_demo.py
.\.venv\Scripts\python.exe -m pytest tests\test_cpiv_educational_demo.py -q
.\.venv\Scripts\ruff.exe check research\cpiv\build_demo.py tests\test_cpiv_educational_demo.py
```

The generated CSV, JSON, SVG, and high-resolution PNG live in
`research/cpiv/generated/`. The calculation uses the standard library; chart
exports use Matplotlib, already declared in the project's notebook dependency
group. All numeric assumptions are declared in the Python source and JSON
metadata.

The R8 HTML/DOCX/PDF build uses research/cpiv/manuscript_r8.md. The final
reviewed deliverables are in dist/cpiv/quantcorner-r8-final-delivery-2026-10-08/;
the builder refuses to overwrite an existing output folder, so use a fresh
`--output` path for another build. Generated assets are isolated in
research/cpiv/generated/revision_20261008_r8/.

## Editorial status

The manuscript is a polished author-review draft, not an empirically tested
research paper. Before presenting it as a quantitative alpha study, acquire
historical option-chain data with documented access and redistribution rights,
freeze a prospective design and timestamped holdout, then run and report the
test. QuantCorner's current formatting and length requirements should be
confirmed with its editor; no acceptance or venue-compliance claim is made.
