# QuantCorner CPIV article — implementation handoff

Updated: 8 October 2026 (Asia/Bangkok)

## Result and scope

Created a separate Thai-language educational quantitative article in response
to QuantCorner's suggestion to focus on call–put implied-volatility spreads
(CPIV) in U.S. single-stock options. It is separate from the previously
submitted R23 manuscript and makes no change to that manuscript or to its G5
status.

The article is suitable for author/editor review as an educational methods
piece. It is **not** an empirical alpha paper: it contains no market options
data, historical return sample, backtest, preregistered holdout, or performance
estimate. Its ten examples are fictional and generated deterministically.
Long/short labels illustrate ranking only and are not investment advice.

## Deliverables

| File | Description | Size | SHA-256 |
|---|---|---:|---|
| `dist/cpiv/quantcorner-cpiv-educational-review-final.pdf` | 8-page A4 PDF, refreshed contents, page numbers, one figure, one data table, live DOI links | 380,938 B | `54D8ACF4FB13719039D44D8E4FC8A292C71F162A1B382894786EE66CB5D5E3AB` |
| `dist/cpiv/quantcorner-cpiv-educational-review-final.docx` | Word version exported from the same A4 layout | 106,127 B | `3AD908E8E5BECC89D84C828A752EC537CEE59D3A09D908CB0CA334527C304084` |
| `dist/cpiv/quantcorner-cpiv-educational-review-final.html` | Standalone full-width HTML; CSS, PNG and MathML embedded | 138,462 B | `A04B804CAB4BB0FF169F714FFF5961BFBEAABA8B83FCDD86BB8CF0D7C35CAC1C` |
| `research/cpiv/manuscript.md` | Canonical Thai/English manuscript source | 37,678 B | `6C6054347C6C4E8CED27884D0A03C969B2D3CEE7CBF636AF4043E9151D045C3A` |

Supporting reproducibility files:

- `research/cpiv/build_demo.py` — BSM prices, bisection IV inversion, synthetic
  ranking, quote-sensitivity intervals, CSV/JSON/SVG/PNG outputs.
- `research/cpiv/generated/synthetic_cpiv_demo.csv` and `.json` — output data
  and explicit assumptions; no market observations.
- `research/cpiv/generated/synthetic_cpiv_demo.png` — chart used in DOCX/PDF.
- `research/cpiv/style.css` — responsive, full-width HTML presentation.
- `research/cpiv/README.md` — build commands and evidence boundary.
- `research/cpiv/render_pdf_preview.py` — PDF contact-sheet helper.
- `scripts/export_cpiv_review.ps1` — task-scoped Word export; operates on a
  temporary copy, refreshes the table of contents, applies A4/page numbering,
  and checks that the source file remains unchanged.
- `tests/test_cpiv_educational_demo.py` — offline synthetic calculation tests.
- `dist/cpiv/qa/final-contact-sheet.png` — visual preview of all 8 PDF pages.

## What the manuscript says

- Defines CPIV as call IV minus put IV for a pair matched on underlying, strike,
  expiry and observation time.
- Distinguishes CPIV from volatility skew/smirk, realized–implied volatility
  spreads, and option-contract returns.
- Uses European Black–Scholes–Merton solely for a controlled teaching example;
  explicitly notes that standard U.S. equity options are generally
  American-style and that live analysis needs appropriate modeling.
- Separates earlier empirical findings from this package's synthetic
  calculations. In particular, an underlying-stock return association is not
  presented as evidence of profitable call-option returns.
- Responds to the editor's OI/OTC concern by restricting the estimand to
  observable listed-option quotes. It makes no claim about market-wide OTC
  coverage, total options flow, OI completeness, or “black-market” share.
- Offers a prospective test checklist (data rights, quote filters, signal and
  portfolio rules, costs, chronological holdout). It explicitly says the plan
  is not registered and no holdout has been run.
- Includes the author's stated affiliation, ORCID and email, plus the previously
  supplied “no external funding” and “no competing interests” declarations.

## Source checks and limits

Checked publication metadata and relevant abstracts/official product
specifications at the publisher or institutional record for the cited sources:

- Cremers & Weinbaum (2010), Cambridge/JFQA:
  <https://doi.org/10.1017/S002210901000013X>
- Doran, Fodor & Jiang (2013), Oxford/RAPS:
  <https://doi.org/10.1093/rapstu/rat006>
- Xing, Zhang & Zhao (2010), Cambridge/JFQA:
  <https://doi.org/10.1017/S0022109010000220>
- Bali & Hovakimian (2009), INFORMS/Management Science:
  <https://doi.org/10.1287/mnsc.1090.1063>
- Black & Scholes (1973), Journal of Political Economy:
  <https://doi.org/10.1086/260062>
- OCC equity-option specifications:
  <https://www.theocc.com/clearance-and-settlement/clearing/equity-options-product-specifications>

The full texts of every cited paper were not independently reviewed in this
turn; claims are kept within the checked bibliographic records and abstracts.
No plagiarism/similarity report was run. No provider terms or market-data
entitlements were needed because no market data was used.

## Verification performed

- Synthetic tests: 5 passed.
- Ruff: passed for the CPIV calculation, preview helper and tests.
- OfficeCLI OpenXML validation: passed; final DOCX reports one table, one
  embedded image and four equations.
- Microsoft Word output: 8 A4 pages; 1 table; 1 inline figure; 4 equations.
- PDF audit: 8 pages, one image, 8 hyperlinks, no local-file links. Page 1
  contains the updated contents list; page contact sheet was visually reviewed.
- Standalone HTML: embedded image, CSS and MathML; no MathJax dependency or
  `file:///` resource reference.
- Existing R23 files were hash-checked and left unchanged.
- No email, Google Doc, QuantCorner message, or submission form was sent.

## Before sending

1. The author should check the byline, affiliation, ORCID, email and disclosure
   statements in the PDF.
2. Ask the editor to confirm that an educational quantitative article with a
   synthetic demonstration (rather than new empirical alpha results) fits the
   requested CPIV topic and expected format.
3. If empirical performance is required, obtain historical U.S. option-chain
   data with documented use/publication rights, freeze the design and holdout
   before examining returns, then add the actual net-of-cost results. Do not
   describe the current synthetic output as a backtest or alpha finding.

The earlier R23 remains a separate manuscript; this CPIV article does not close
or alter its G5 gate.
