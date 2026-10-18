# CPIV R22 review follow-up — 11 October 2026

## Result

The five concrete wording/method fixes in the R22 review are implemented in the manuscript and synthetic diagnostics. The final local package is **v21**. Use only the v21 files listed below; v18 was an accidental R8 build, v19 preceded the disclosure edit, and v20 contained an empty Word contents field. Those are intermediate outputs, not submission files.

## Review items closed

1. **Tick notation:** the price tick is \(t\); \(\tau_{IV}\) and \(\tau_{carry}\) remain tolerance symbols.
2. **Sub-tick rule:** the screen uses each leg’s premium above its European lower bound (OTM-equivalent time value), not total ITM premium. In the matched deep example, call and put both have approximately \(3.178\times10^{-6}\) price units of OTM-equivalent value, below the hypothetical \(t=0.01\), so both are unresolved.
3. **Table 5B units:** headings distinguish the price-unit shocks (\(\pm0.01\)) from the resulting IV changes in percentage points.
4. **Shock convention:** Table 5C reports full-tick \(\pm t\) and nearest-tick-rounding \(\pm t/2\) side by side. At ATM, the maximum displacement is 0.087469 pp under \(\pm t\) and 0.043735 pp under \(\pm t/2\); therefore the classification at \(\tau_{IV}=0.05\) changes with the convention. In the deep synthetic case the positive half-tick shock changes IV by +5.9264 pp; the negative shock has no root, so the pair remains unresolved. “Worst-direction” replaces the misleading “one-sided displacement” phrasing.
5. **Appendix B:** duplicate shell blocks are removed. One command block is described as usable in PowerShell and Bash; execution was verified in PowerShell only, not Bash.

The vague phrase “broader project” was removed from the funding disclosure. It now identifies the complimentary one-month HyperTracker Surge subscription as in-kind support, and states that this note uses no HyperTracker data and received no provider data or analytical input. The author should personally confirm whether the provider had any other role (for example, study design, interpretation, writing, or submission decision) before making a broader no-role declaration; this report does not infer that fact.

## Build safeguards added

- scripts/build_cpiv_review.py now requires an explicit --source for any non-default revision. --revision otherwise changes only the output filename; it no longer silently produces an R8 paper under a newer revision label.
- The DOCX no longer contains an unpopulated Word table-of-contents field. The standalone HTML and PDF retain their populated contents sections.

## Final local files

Directory: dist/cpiv/quantcorner-cpiv-reviewed-2026-10-11-v21/

| Format | File | SHA-256 |
|---|---|---|
| HTML | quantcorner-cpiv-review-r22-2026-10-11.html | C48A9ECC4B46BB94817FD0B43A14D7CA74D9F4B4D56C147C0508C26C97B1BFBC |
| DOCX | quantcorner-cpiv-review-r22-2026-10-11.docx | 1A609402E6BD2F3BBEEAF89867CDF9F2721B51A474A3916B028C04CA824505F8 |
| PDF | quantcorner-cpiv-review-r22-2026-10-11.pdf | 676422056D23B5BC5BA0B457C7F40D13C5662028137913B36CF0C0C701B3F3BD |

## Verification evidence

- Synthetic reproduction completed with Python 3.14.3; its output declares market_data_used: false.
- Full suite: **281 passed**. Focused CPIV/build tests: **30 passed**. Ruff passed. Targeted mypy passed for five source modules using --explicit-package-bases; mypy emitted only the existing unused-config-section note for bti.bounds.*.
- HTML: 5 image tags, all 5 use embedded data:image sources; no data-embedded-src. Table 5C and the 0.043735-pp half-tick result are present.
- DOCX: opens through the Word refresh backend; 9 tables and 5 drawings; no empty TOC placeholder or TOC field.
- PDF: 24 pages; extracted text contains Table 5C and the half-tick result; extracted text contains zero U+2010 characters. The builder emitted MiKTeX update notices, but exited successfully.
- Full suite initially had one timing-sensitive failure in test_request_pacer_reserves_spaced_slots (279 passed, 1 failed); the isolated test then passed, and the subsequent full rerun passed 281/281. No unrelated pacer code was changed.

## Still open — do not overstate readiness

- The paper remains synthetic-only: no historical options, market-wide position census, holdout, returns, or alpha estimate. **G5 is not closed.**
- The public code/data archive, license, DOI, and actual cross-platform CI run are still absent; Appendix B was run only on Windows PowerShell.
- The review’s further proposed analyses (off-center \(d^3\) convergence, analytical ranking/SNR and test–retest reliability, and independent American-option/Richardson benchmarking) were not added in this follow-up.
- Source/news links and provider terms were not re-audited in this pass. No email, public deposit, or submission was made.
