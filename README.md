# Bounding the Invisible

Research repository for the QuantCorner series on what public data can and
cannot identify about liquidation exposure in crypto perpetual futures.

## Current scope

This checkout implements the offline Part 1 evidence path and a bounded
Part 2/3 aggregate-data run:

- a dependency-light synthetic population simulator;
- an explicit many-to-one observable map;
- the Part 1 static SVGs and self-contained W1 widget;
- PNG companions for editorial preview;
- an integrated Thai/English research-manuscript draft with source links,
  a project-local, protocol-specified chronological holdout (501/504 hourly
  observations per symbol; no immutable pre-collection record for the complete
  prose protocol), and a labelled exploratory appendix;
- pure Decimal margin/bound helpers and focused tests;
- a read-only Hyperliquid collector for registered candles, funding, and one
  current aggregate context snapshot;
- a no-credential smoke probe for the official trade-address to
  `clearinghouseState` path, with addresses kept in memory only;
- a project-local chronological descriptive holdout audit; the manuscript
  documents protocol-timing and incomplete-window limitations.

Part 2/3 results are limited to real aggregate observations and a mechanical
scenario calculation. They are not a position census, historical OI series,
or ground-truth liquidation-surface validation. The 7-day collector run,
12-month backfill, and true-surface validation remain open gates.

## Quickstart

```powershell
python -m pip install -e ".[dev]"
python scripts/build_part1.py
python scripts/collect_hyperliquid_real.py
python scripts/analyze_part23_real.py
pytest -q
```

The build writes Part 1 artifacts under `site/docs/assets/` and an evidence
summary under `reports/part1_evidence.json`. The simulation has no network
dependency and can be run offline.

## Evidence boundary

The three source documents listed below are project inputs, not
independent evidence. Claims about exchange mechanics are linked to official
documentation; academic claims are linked to the canonical paper or DOI.
News links about the October 10, 2025 event were reviewed but are not used in
the integrated manuscript. CoinGlass dynamic row values were not exposed in
the inspected DOM, and Reuters returned HTTP 401 without an article body; no
claim depends on those pages.

## Gate status

| Gate | Status | Reason |
|---|---|---|
| G1 collector live | UNVERIFIED | No 7-day live run in this checkout |
| G2 public backfill | UNVERIFIED | No 12-month raw dataset committed |
| G3 bound correctness | PARTIAL | First-tier scenario audited; cross-margin/tier distribution remains open |
| G4 Part 1 | PARTIAL | Offline artifacts and draft exist; external editorial review pending |
| G5 true surface | OPEN | No repeated, time-aligned market-wide position/OI series establishes the ≥70% median or measurable cold-start gap |
| G6 models/leakage | PARTIAL | Chronological descriptive audit passes; no predictive model is claimed |
| G7 locked holdout | LOCKED | Holdout is post-registration descriptive-only; no unlock marker exists |

## Verification receipts

- `python -m pytest -q` (28 September 2026): 182 passed.
- `ruff check src scripts tests` (28 September 2026): passed.
- python -m compileall -q src scripts tests: passed.
- Integrated-manuscript export and deterministic disclosure/language audit:
  passed; human source/terms review remains required.
- mypy src/bti --ignore-missing-imports: passed; 25 source files checked.
- import-linter: passed with `lint-imports --config importlinter.ini
  --no-cache` after the editable package install. The contracts cover
  simulation isolation, bounds/I/O separation, and no core-to-viz dependency.
- `python -m mkdocs build -f site/mkdocs.yml`: site build completed; MkDocs
  notes six evidence pages present under `site/docs/` but omitted from `nav`.
- real aggregate run: 8,127 candles and 8,127 funding observations across
  BTC/ETH/SOL; current OI snapshot recorded; receipt in
  `reports/part23_data_receipt.json`.
- public-source probe: HyperPerps discovery/BTC/ETH/SOL endpoints returned
  HTTP 200 without credentials; raw response and hash are in
  `data/raw/hyperperps/public-heatmap-snapshot.json`. The provider schema
  labels the response as anonymized clusters only, so it is not G5 evidence.
- official census-path smoke probe: a public BTC trade subscription exposed
  `users`; five in-memory candidates queried through `clearinghouseState`
  returned HTTP 200 with `assetPositions`. The probe writes no addresses and
  is explicitly `smoke_only`; the latest receipt records a 0.01468% sequential
  sample ratio against current BTC OI, but marks it non-atomic and not a census
  or G5 coverage result. The sanitized receipt is in
  `reports/hyperliquid_census_path_smoke.json`.
- BibTeX citation check: offline parse-only receipt; no DOI/retraction PASS is
  claimed without a contact email and online run.
- Prospective GMX supplemental receipt-binding check: the public Sep 28
  aggregate receipt is reproduced by
  `python -m scripts.check_gmx_g5_supplemental_binding --day 2026-09-28 --receipt receipts/2026-09-28.json`.
  This checks one fixed-time source state and does not close the seven-day GMX
  arm or the original Hyperliquid G5. See
  `reports/g5_prospective_collection_status_2026-09-26.md` for exact scope.

## Source documents

- `hidden-leverage-study.md`
- `BUILD-SPEC.md`
- `PROMPTS.md`

These three files are local working inputs and are not included in this repository.

Source and venue audits:

- `reports/venue_brief_quantcorner.md`
- `reports/g5_access_path_audit.md`

The repository does not copy raw position data, wallet addresses, or API keys.
The local Part 2/3 raw aggregate response is retained under `data/raw/` and is
explicitly labeled as aggregate-only evidence.

## Citing the CPIV review package (v28)

The CPIV review package (v28, r26, dated 18 October 2026) is archived on Zenodo:

- Version DOI: https://doi.org/10.5281/zenodo.23442601
- All versions (concept DOI): https://doi.org/10.5281/zenodo.23442600

Citation metadata is in `CITATION.cff`; the code is licensed under MIT (`LICENSE`).
