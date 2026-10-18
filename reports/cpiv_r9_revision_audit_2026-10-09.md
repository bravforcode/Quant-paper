# CPIV R9 proposed revision: adversarial-review response and audit

**Audit date:** 9 October 2026 (Asia/Bangkok)  
**Status:** proposed methods-note revision; not formally approved, not submitted  
**Empirical gate G5:** OPEN / NOT MET

## Decision and scope

The attached review recommends a major revision and asks for a narrower,
measurement-focused methods note. Because the user's message contained no
separate instruction outside that review, this work treats the review as a
request to implement a proposed revision. R8 was preserved. R9 is a separately
versioned proposal, not an accepted editorial decision or a claim that the
paper is submission-ready.

R9 implements many requested mathematical, numerical, simulation, and artifact
changes. It does **not** establish that this combined diagnostic workflow is
novel or more useful than raw-midpoint, minimally filtered, or synchronized
CPIV. The review's requested baseline/coverage comparison remains open. The
evidence is synthetic; there are no market option quotes, returns, positions,
liquidations, or alpha results. Accordingly, G5 remains OPEN / NOT MET.

## Inputs and provenance

| Input | SHA-256 | Scope note |
|---|---|---|
| `C:\Users\menum\.codex\attachments\b6cd1157-7a55-48d7-9474-43befd3f8df5\Pasted text.txt` | `55A215AE904F91B45B1DA5DD34F75C4A41E12823614911EEFC4BA0E10DE7F8F2` | Review text; treated as requested work, not as independently verified evidence. |
| `C:\Users\menum\Downloads\cpiv_independent_numerical_audit.csv` | `F0018CEEEC435AE78CD27D6420BE26C1B0627112F5B314A1B47FCD4B2FB01120` | 36 supplied numerical rows; copied byte-for-byte into the delivery folder. |

The CSV is an input artifact. Its hash verifies the copy, not the identity,
methods, or execution environment of whoever produced it. Comparisons below
therefore describe the supplied values and the local recalculation; they do not
certify the provenance of the external implementation.

## Review disposition

| Review concern | R9 change / evidence | Remaining qualification |
|---|---|---|
| Contribution indistinct from known CPIV/parity and IV-error literature | Retitled and framed as a measurement-focused methods note; added relevant IV-error, execution-cost, price-pressure, and CPIV references; distinguishes this operational synthesis from a new parity identity or return predictor. | Novelty and incremental usefulness are not established. Baseline comparisons remain undone. Human full-text/source review and venue fit remain open. |
| Exact relation and sign equivalence | States the oriented integral identity `R = ∫[σP,σC] ν(u)du = (σC−σP)ν̄`, its common-input assumptions, sign implication, and why `R` and CPIV are not independent confirmations. | The identity is a mathematical implication of the stated European-BSM setup, not a new market finding. |
| IV existence, bounds, root-solving and silent clipping | Documents European price bounds, IV bracket `[1e−8, 5]`, 64 bisections, `1e−10` tolerance, repricing checks, invalid-price handling, failure reporting, and no clipping. | Numerical thresholds should be reviewed against the eventual venue's methods expectations. |
| Local approximation lacks quantified error | Runs 720 synthetic grid cases; 624 meet the stated vega floor and 96 are unresolved. Resolved-case median absolute error `0.00007858 pp`, p95 `0.08720 pp`, max `1.23552 pp`. | Grid cells are equally weighted by construction; these are not expected live-chain errors. The vega floor is a declared numerical threshold, not empirically calibrated. |
| American-put finite-tree artifact | Compares CRR and equal-probability Jarrow–Rudd at 400, 800, 1,600, and 3,200 steps; uses a closed-form European call; asserts no exact American price. | Two finite schemes are a convergence comparison, not proof of a limiting exact value. |
| Carry and timestamp input ambiguity | Tests effective yields from −2% through +5%, and spot offsets from −0.25 to +0.25; identifies `q` as effective yield rather than a borrow/funding fee. | Does not identify dividend, borrow, financing, or crypto funding mechanisms separately. |
| Quote noise / intervals and uncertainty budget | Adds bid/ask-implied endpoint ranges and a covariance-form delta-method budget; explicitly labels both as conditional diagnostics, not confidence intervals or arbitrage bounds. | Uses ten synthetic quote pairs and illustrative error scales; no market calibration or full dependence model. |
| Ranking experiment too narrow / exact-order metric fragile | Adds five signal shapes, six noise structures, two universe sizes, three target noise scales, three fixed seeds, and 100 draws per seed/cell (54,000 rankings); reports inversion fraction, Spearman correlation, membership turnover, sign accuracy, Wilson Monte Carlo intervals, and per-name inclusion probabilities for `n=10`. | Noise distributions are uncalibrated. Wilson intervals quantify simulation-event uncertainty conditional on the design, not market-population uncertainty. |
| Independent numerical audit differs from R8 | Recomputes supplied carry and CRR cases and compares the supplied independent ranking rows with R8 source values; figures/tables identify non-exact RNG replay. | RNG family/draw ordering differ; no claim of exact reproduction or code defect. |
| Reproducibility claims exceed delivered evidence | Adds source, diagnostic implementation, CSV/JSON outputs, figures, tests, environment lock, and a local reproducibility archive. R8 widget is labeled as a presentation-only baseline, not the R9 simulation. | No public archive or reuse license. Do not call this publicly reproducible. A successful local build is not a public release. |
| Layout and artifact integrity | Rebuilt HTML/DOCX/PDF; visually inspected sampled PDF pages; checked A4/10-page PDF, valid DOCX package, tables/images, embedded HTML images and slider control. | Slider presence was statically checked in this pass; this report does not certify every browser interaction or every editor's rendering. |

## Independent numerical comparison

### Carry and American-put values

The supplied carry rows for `q = 1%, 2%, 5%` agree with the local
recalculation to floating-point precision. Maximum absolute difference is
approximately `2.22e−13` volatility percentage points. The zero-yield case is
zero to rounding. These experiments vary an effective pricing yield; they do
not measure stock-lending or funding costs.

| CRR steps | Supplied CPIV (pp) | Local CPIV (pp) | Absolute difference (pp, approx.) |
|---:|---:|---:|---:|
| 400 | −0.2570181594077431 | −0.2570181594079346 | 1.92e−13 |
| 800 | −0.2610646925829102 | −0.2610646925829574 | 4.72e−14 |
| 1,600 | −0.2630819638360649 | −0.2630819638361537 | 8.88e−14 |
| 3,200 | −0.2640850785613796 | −0.2640850785614601 | 8.05e−14 |

The agreement validates the listed arithmetic to displayed precision for these
cases; it does not prove convergence to an exact American-option value.

### Supplied independent ranking audit vs. R8 baseline

| Noise SD (pp) | R8 no inversion (%) | Supplied audit (%) | R8 membership change (%) | Supplied audit (%) |
|---:|---:|---:|---:|---:|
| 0.35 | 82.95 | 81.85 | 3.80 | 4.50 |
| 0.50 | 43.60 | 45.00 | 15.50 | 15.00 |
| 1.00 | 2.50 | 2.90 | 55.05 | 53.20 |
| 2.00 | 0.10 | 0.10 | 85.45 | 86.15 |

The supplied audit also reports zero observed extreme crossovers in its 2,000
draws per noise level. That is a finite-sample count, not a zero-probability
result. Similar but non-identical estimates are expected when RNG and draw
ordering differ; this is not an exact replay of R8's random stream.

## Local synthetic diagnostics

- **Exact identity grid:** 24 cases; maximum absolute residual `2.4092e−14`
  currency units.
- **Approximation grid:** 720 cases; 624 resolved and 96 below the declared
  vega floor. Resolved absolute-error median `7.8583e−05 pp`, p95 `0.087203 pp`,
  maximum `1.235520 pp`.
- **European IV inversion:** 104 of 120 generated quotes invert within the
  configured bracket; 16 are rejected near/outside the numerical bounds. All
  10 deliberately invalid-price probes are rejected; none is accepted. Maximum
  successful repricing error `2.8422e−14` currency units; no clipping.
- **American put:** CRR and Jarrow–Rudd step comparisons at 400–3,200; no exact
  price or convergence theorem is asserted.
- **Ranking:** 54,000 simulated rankings across the declared factorial design.
  One design example: for ten equally spaced signals under Gaussian noise SD
  `0.50 pp`, mean inversion fraction `0.176`, mean Spearman `0.797`,
  top/bottom-20% turnover `0.367`, and sign accuracy `0.826`. For ten near-tied
  signals at the same noise scale, these are `0.495`, `0.015`, `0.792`, and
  `0.504`, respectively. These are design-conditional simulation results.

## Open gates before any real submission

1. **Baseline validation / contribution:** compare raw-midpoint, minimal-filter,
   synchronized-input, and interval-qualified variants under a declared target;
   report signal stability and retained-data coverage, including false
   exclusions. Do not claim superior usefulness or novelty until this exists.
2. **Market evidence:** obtain lawfully usable, synchronized option/underlying
   data and run a pre-specified measurement study. No real data were obtained or
   analyzed here. G5 remains OPEN / NOT MET.
3. **Human source review:** inspect the cited primary sources and raw links,
   confirm each claim against full text, and confirm reuse/quotation rights.
   Bibliographic metadata was checked with AI-assisted search; this is not a
   human link/content/rights sign-off or exhaustive full-text review.
4. **Author/venue review:** author must approve all numbers, wording, AI-use
   disclosure, declarations, attribution, and final files; obtain QuantCorner's
   current article type, length, format, exclusivity, and reuse requirements.
5. **Public reproducibility:** decide a license, inspect third-party asset/data
   rights, and publish/version the source and outputs to an accessible archive
   before describing the work as publicly reproducible.

Funding and competing interests are stated as “No external funding” and “None”
per the author's prior confirmation. No email, Google Doc, external archive, or
submission form was changed or sent as part of this revision.

## Build and test record

Environment observed locally: Python `3.14.3`, Matplotlib `3.11.2`, Pandoc
`3.11`. MiKTeX emitted a notice that updates had not been checked; the build
completed successfully. `ruff` reported “All checks passed”. The focused suite
reported `21 passed`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cpiv_educational_demo.py tests/test_cpiv_review_builder.py tests/test_cpiv_r9_diagnostics.py -q
.\.venv\Scripts\ruff.exe check research/cpiv/r9_diagnostics.py scripts/build_cpiv_review.py tests/test_cpiv_r9_diagnostics.py tests/test_cpiv_review_builder.py
.\.venv\Scripts\python.exe -m research.cpiv.r9_diagnostics --output research/cpiv/generated/revision_20261009_r9_proposed --replicates-per-seed 100
```

The final build command and full artifact contents are recorded in the package
README/manifest. PDF metadata reports 10 A4 pages; `pdfinfo` and text extraction
found title, author, abstract, results, declarations, and references. DOCX ZIP
integrity passed; it contains two bordered tables and three embedded images.
The standalone HTML has three embedded data-URI figures, a range slider, and no
`file:///` references. PDF pages 1, 5–10 were visually inspected at rendered
resolution; the complete American-put table now stays on one page. No claim is
made that every platform/editor renders identically.

## Delivered files and checksums

Current proposed delivery directory:
`dist/cpiv/quantcorner-r9-proposed-rev3-2026-10-09/`

| Artifact | SHA-256 |
|---|---|
| HTML `quantcorner-cpiv-review-r9-2026-10-09.html` | `51B6E4033EA9155B92D612D570A66B5578644AEA79F53EB4C7247ACFB1F8D1D0` |
| DOCX `quantcorner-cpiv-review-r9-2026-10-09.docx` | `FA815279CF35CD27CAE0C8F8E9B93C18DEAF2A305AAC3C90795A9F344F7DDD82` |
| PDF `quantcorner-cpiv-review-r9-2026-10-09.pdf` | `5735C0D1B18F49C895025AD7B2809B8650DAFE96B827B2DA77FEA7EDB2EBD722` |
| Source `research/cpiv/manuscript_r9_proposed.md` | `DCB6B1BC5913DFCE336F718357D7D35287A4E8460838604996E0FE5CEBC45D6D` |
| Diagnostics `research/cpiv/r9_diagnostics.py` | `4AF52AA8DC30D320FDF3C97FDD3F3516C497697AEF643CDA890D71E70CF380EC` |
| Summary JSON `cpiv_r9_diagnostics.json` | `C007B4DD1ACE878F67987EF321CAD41D2935D188B92C50F8FEC76D7B15DDB843` |
| Copied independent audit CSV | `F0018CEEEC435AE78CD27D6420BE26C1B0627112F5B314A1B47FCD4B2FB01120` |

R8 source `research/cpiv/manuscript_r8.md` was not edited; its observed
SHA-256 is `3514510B4C944AB246512D9399AD7D5596DBB23C4D68DBC60C3524AA0CA4C493`.
The local handoff ZIP is
`dist/cpiv/quantcorner-r9-proposed-rev3-2026-10-09/quantcorner-cpiv-r9-reproducibility-2026-10-09.zip`.
The R9 package is a proposed review response, not a submission authorization or
empirical result.

## Follow-up: adversarial review of the HTML widget (rev4, 9 October 2026)

The attached review of the R9 standalone HTML was treated as a request to fix
the identified widget presentation and interpretation issues. The reviewed
attachment SHA-256 is
`65A3DE0D96A80C1FDB6478D5BFF399F3A5FB50503A8F3FC79D7C829702C3A198`.
Changes were confined to the widget builder, its CSS, its tests, and one
reproducibility clarification in the R9 manuscript. R8 source was not changed;
its observed SHA-256 remains
`3514510B4C944AB246512D9399AD7D5596DBB23C4D68DBC60C3524AA0CA4C493`.

| Review point | Rev4 correction and verification |
|---|---|
| Bar scale changed with the selected noise level | All seven stored examples now share one fixed symmetric axis, ±5.2 pp, calculated from the maximum absolute value across those examples. Tick positions and units are visible. |
| Slider positions could be mistaken for equally spaced numerical values | Seven labels are shown: 0.00, 0.10, 0.20, 0.35, 0.50, 1.00, and 2.00 pp. The accompanying text says the slider selects a stored row at discrete, unequally spaced levels. |
| Default summaries and ranking list were blank without JavaScript | The default 0.20-pp summary and ten example rows are present in the initial HTML before the script; a `<noscript>` notice explains the static default. The no-script fallback is source/unit-test verified; this pass did not claim a separate browser run with JavaScript disabled. |
| Aggregate Monte Carlo measures could be confused with a single example | Separate panels show the 2,000-replicate statistics and metrics computed for the one stored draw relative to the zero-noise baseline. The p05–p95 ranges are labeled empirical replicate quantiles, not confidence intervals. |
| Precomputed viewer could be read as a live simulation | The widget and Section 9 now state that it selects precomputed R8 baseline rows; it does not reprice, reinvert implied volatility, or run R9's 54,000-draw experiment in the browser. |

### Browser and artifact checks

An isolated Chromium session opened the rev4 standalone HTML. The slider was
set to 0.20, 1.00, and 2.00 pp; each selection updated the accessible value,
Monte Carlo summary, single-draw diagnostics, and ten-name ranking list. At
1.00 pp, the displayed draw has 1 pairwise inversion, Spearman ρ 0.988, and
unchanged low/high-20% membership; the aggregate membership-change frequency
is 55.05%. At 2.00 pp, the displayed draw has 8 inversions, Spearman ρ 0.782,
and changed low/high-20% membership, while the aggregate membership-change
frequency is 85.45%. These checks distinguish the one stored realization from
the Monte Carlo frequency; neither is a market estimate. The page reported no
browser errors during this check. The HTML widget was also visually sampled.

The focused tests now report `23 passed`. Ruff reports all checks passed for
the R9 diagnostics, HTML builder, and related tests. The rev4 PDF is 10 A4
pages; its first and last pages were visually sampled. The DOCX package
contains 2 tables, 62 native Word math objects, and 3 embedded images; all 19
ZIP entries were readable. The supplied audit CSV was copied unchanged; both
source and copy have SHA-256
`F0018CEEEC435AE78CD27D6420BE26C1B0627112F5B314A1B47FCD4B2FB01120`.

| Rev4 artifact | Bytes | SHA-256 |
|---|---:|---|
| `quantcorner-cpiv-review-r9-2026-10-09.html` | 470,289 | `E9DF6305CF7261793A2EFB5AA6F7DB7B8F087FD77B7F66EDCFE87629D613022A` |
| `quantcorner-cpiv-review-r9-2026-10-09.docx` | 258,922 | `84ABFBCD311CF8CEF48BCA9994A68D7825916762946D67BDCEEBC424DC2ED881` |
| `quantcorner-cpiv-review-r9-2026-10-09.pdf` | 368,122 | `4CF230B4BD827F4661903E0C0E7D518C5AFBED8190C5A979E4CE6B7DEB4C155E` |

The old rev3 artifacts and their audit record were preserved. This rev4 update
is local only: no email, Google Doc, external archive, or submission form was
changed. G5 remains OPEN / NOT MET; the corrected widget does not add real
market data or close any empirical gate.
