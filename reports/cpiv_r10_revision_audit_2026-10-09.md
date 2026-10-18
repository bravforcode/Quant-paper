# CPIV R10 proposed revision — review disposition and audit

**Audit date:** 9 October 2026 (Asia/Bangkok)  
**Release identifier:** `CPIV-R10-PROPOSED-2026-10-09`  
**Status:** local proposed revision; not submitted and not editor-approved  
**Evidence scope:** synthetic numerical diagnostics only; no market-data or alpha test

## Scope and provenance

The input was the user-provided R9 major-revision review at
`C:\Users\menum\.codex\attachments\3f2a09e8-f2e3-42b0-8a35-dce61a4c8b6c\Pasted text.txt`.
Its SHA-256 is `067556C9B1E9751428375E0C2B4FCF3936C1596C7667D1D13F0B994BC397F7E5`.
The review was treated as a set of requested checks, not as verified evidence
or authority to make claims beyond the files and runs inspected here.

R10 preserves the R8/R9 artifacts and creates a separate proposed manuscript,
diagnostics, and deliverables. It does not establish that the paper is novel,
that CPIV predicts returns, or that a strategy is profitable. Since no market
quotes, returns, positions, or liquidation census were analyzed, any empirical
market-data gate remains **OPEN / NOT MET**.

## Review disposition

| Review concern | R10 response and evidence | Remaining limitation |
|---|---|---|
| Common-map identity incorrectly said to fail for American-origin or stale-input prices | Section 4 now separates the algebraic inversion-map identity from the economic interpretation of the residual. It states the common-input and root-existence conditions and identifies the cases where the displayed identity does not apply. | The identity is not a new parity theorem or empirical result. |
| Zero-spread case called a ratio undefined | Section 4 defines path-average vega on a unit interval, including coincident IV endpoints, and gives the zero-spread case when average vega is positive. | The formula remains conditional on admissible roots and positive average vega. |
| Quote interval missing conversion to volatility percentage points | Section 6.3 applies the factor 100 to decimal-IV endpoints and labels the result in percentage points; eligibility and non-overlap denominators are specified. | Synthetic bands are not statistical coverage or market confidence intervals. |
| Residual price units and contract multiplier ambiguous | Section 3 uses currency per underlying unit before multiplier and states the conversion to per-contract amounts. | A market implementation must confirm vendor quote conventions and multiplier per contract. |
| 720-cell design could not be reconstructed | Section 6.1 gives absolute spot/strike construction, carry pairs, midpoint reference IV, symmetric IV endpoints, spread grid, Simpson quadrature, and separate numerical-error quantities. | The fixed grid is not market weighted; symmetric construction can favor midpoint approximation. |
| Approximation, solver error, and numerical-bound behavior conflated | Sections 5–7 separate target-spread approximation error, quadrature/residual gaps, repricing error, IV-recovery error, configured-bracket status, and near-bound diagnostics. Output denominators are supplied. | Thresholds are implementation settings, not universal quality criteria. |
| Double-precision near-bound failures attributed too broadly | R10 includes a separately coded 180-digit Decimal audit with generated inputs, outputs, and status counts. The manuscript narrows interpretation to this generated design. | Same project author; not an independent human replication or proof. |
| General paired-IV uncertainty gradient missing | Section 7.6 gives leg-specific vegas and price Greeks for unequal IVs, the covariance form, and six synthetic cases comparing gradient SD with direct perturbation/inversion SD. A central-difference implementation test is included. | Perturbation scales and covariance choices are illustrative, not estimated from market quotes. |
| Scale sensitivity and threshold stability were omitted | R10 reports normalized-vega scale checks and threshold sensitivity alongside the configured absolute guard. | No threshold is calibrated to live quote data. |
| Ranking experiment was under-specified | Section 6.4 states the signal vectors, CPIV-space noise, eight noise families, correlation construction, heteroskedastic normalization/permutation, seeds, replicate counts, tie handling, and common-random-number contrasts. It defines pairwise inversion, Spearman, turnover, sign accuracy, and event denominators. | The generators are explicit stress designs, not calibrated models of market microstructure. |
| Simulation uncertainty and dependence were overstated | R10 reports replicate-level MCSE/intervals, paired scale contrasts, Wilson intervals for event rates, and says names/pairs are not independent observations. | Intervals quantify simulation variation conditional on the chosen design, not market-population uncertainty. |
| American trees described as exact benchmark validation | R10 compares CRR and equal-probability Jarrow–Rudd at 400–6,400 steps and declares the 0.001 pp successive-grid threshold descriptive, not a formal error bound or exact-price benchmark. The Jarrow–Rudd reference is included. | No high-resolution external American-option benchmark is claimed. |
| “Invalid price” and “outside solver support” conflated | Section 5 distinguishes invalid inputs, theoretical-bound violation, configured near-bound rejection, outside-bracket, and numerical/unclassified rejection; no clipping is used. | These are the implementation’s current status classes, not a universal data-quality taxonomy. |
| Workflow contribution lacked executable protocol | Table 4 specifies stages, inputs, checks, statuses, and actions for contract, timestamp, price, inversion, CPIV, and rank diagnostics. Section 8 narrows contribution to implemented workflow plus synthetic tests. | No comparative validation against raw-midpoint or synchronized market baselines; incremental decision value remains unestablished. |
| R9 reproducibility/audit claims exceeded supplied package | R10 source, diagnostic code, tests, CSV/JSON outputs, figures, reference template, environment files, commands, SHA-256 manifest, and final formats are included in the local companion ZIP. Detailed cross-check provenance is placed in Section 9. | Local package only: no public archive, VCS commit identifier, or redistribution license is assigned. The identity checker is same-author code. |
| R9 HTML did not substantiate its claims | The R10 HTML was checked for embedded images, the slider/range control, absence of local `file:///` URIs, and the manuscript text clearly calls the widget a fixed-seed R8 illustration rather than an R10 simulation. | This is a static artifact check, not certification across every browser/device or exhaustive interaction testing. |
| Abstract and Thai summary encouraged a general stability interpretation | Both summaries now bind numbers to the stated grid and configured guard and explicitly say the work is synthetic and does not test alpha or markets. | Author should still proofread Thai and English in the target submission interface. |
| Figure 2 caption and Table 2 caption were separated from their visuals in PDF | PDF-only source starts the American-tree figure and ranking table on fresh pages. Rendered page 8 shows Figure 2 with its single caption; page 9 starts with Table 2 caption and the full table. | The final visual check covers the generated target formats on this workstation only. |

## Verification record

- Full project tests: **252 passed**.
- Focused tests run from the companion source tree: **27 passed**; targeted Ruff checks also passed there.
- SHA-256 manifest entries were recomputed from the final companion ZIP with **0 mismatches**.
- Ruff on the R10 scripts and tests: **passed**.
- DOCX package validation: **passed; no validation errors**.
- DOCX content findings: **0**; formatting findings: **0**; structure findings: **9 empty paragraphs**, corresponding to document spacing/equation layout, not reported content or style errors.
- DOCX repagination: **16 pages**, 4,316 words; Word TOC refreshed.
- PDF: **13 A4 pages**. Text extraction finds Figures 1–3 and Table 4; rendered Figure 2 caption is visible on page 8.
- HTML static checks: slider/range present; 4 embedded PNG data URIs (3 manuscript figures plus social-card asset); no local `file:///` reference.
- Build emitted MiKTeX “not checked for updates” notices but returned exit code 0 and produced all three formats.

## Files and next gate

Primary deliverables are in
`dist/cpiv/quantcorner-r10-proposed-2026-10-09-final4/`.
The source-and-evidence companion archive is
`dist/cpiv/quantcorner-cpiv-r10-companion-2026-10-09-final4.zip`; its README
gives reproduction commands and its manifest hashes the included files.

Before any external submission, the author still needs to verify cited sources
against original publications, check QuantCorner's current scope/format rules,
proofread the exported files, decide on redistribution terms, and make the
submission decision. None of those actions was performed by this audit. R10
should be described as a proposed synthetic methods note, not as a validated
CPIV alpha strategy or a closed empirical-data gate.
