# CPIV → Journal of Computational Finance — Phase 0 decision record

**Date:** 2026-10-22
**Baseline manuscript:** `research/cpiv/manuscript_r33_proposed.md` (r33, 20 October 2026)
**Programme under execution:** PLAN.md (supplied 2026-10-22)
**Gate result:** **STOP on market data; PROCEED on the synthetic benchmark.** No licensed historical quote data exists for this project, so the market-data pipeline stays closed. The measurement protocol itself is exercised on a synthetic market with a *known* truth, under a frozen pre-registration addendum.

## Thai summary

- Phase 0 ทำครบทั้งสามส่วนแล้ว: ตรวจ scope วารสาร, ตรวจสิทธิ์ข้อมูล, และเขียน one-page design
- **gate ของ market data ไม่ผ่าน**: ยังไม่มี historical option quote ที่มี timestamp ระดับ quote และมีสิทธิ์เผยแพร่ผล aggregate เป็นลายลักษณ์อักษร — ทุก market-data path ยังปิดอยู่
- **แต่ protocol ไม่จำเป็นต้องรอข้อมูลจริง**: สร้าง synthetic ground-truth benchmark ที่ truth ถูกกำหนดไว้ก่อนที่ quote จะมีอยู่ แล้ว freeze กฎตัดสินไว้ก่อนอ่านผล
- ผลหลักจาก 24 draws: certification เลือกชุดที่วัดแม่นกว่าชุดเดียวกันที่สุ่มมาอย่างมีนัยสำคัญ (23/23) แต่ coverage เพียง ~8% ที่ tolerance 0.10 pp — แลกความแม่นยำกับข้อมูลที่ต้องทิ้ง
- R3 (coverage ไม่ขึ้นกับ synthetic market ที่เลือกเอง) **ไม่ผ่าน** — รายงานเป็นความล้มเหลว ไม่ซ่อน
- แผนเดิมมี 4 จุดที่ต้องแก้ก่อน freeze: word limit, รูปแบบ front matter ของ JCF, ข้อกำหนด timestamp ที่บังคับให้ใช้ข้อมูล intraday, และสมมติฐานว่า "aggregate results" เผยแพร่ได้เอง

---

## 1. Gate decision

PLAN.md §15 sets the first kill criterion: *no licensed data with adequate timestamp quality → stop*. It is met.

| Phase 0 item | Status | Where |
|:--|:--|:--|
| Journal scope check | Done | §3 below |
| Data-rights check | Done — no usable licence today | [DATA_RIGHTS.md](DATA_RIGHTS.md) |
| One-page design | Done | §2 below |
| Preregistration frozen (market data) | **Blocked** | [preregistration.md](preregistration.md) is `v0.1-draft` |
| Preregistration frozen (synthetic benchmark) | **Done** | [preregistration_addendum_A1_synthetic.md](preregistration_addendum_A1_synthetic.md) |
| Stop/go | **STOP on market data; PROCEED on the benchmark** | PLAN.md §15, criterion 1 |

This is the plan working as intended, not a failure. Proceeding to Phase 1 without a licence would produce a pipeline that cannot be run on the data the paper claims, and any synthetic substitute is already covered by r33.

**What flips the gate:** a signed licence or written permission that (a) covers historical paired call/put quotes with quote-level timestamps, (b) allows publication of aggregate tables, figures and derived statistics in a journal article and its supplementary material, and (c) allows depositing code plus aggregate outputs in a public repository without the raw quotes.

### 1.1 The simulation-first decision

A STOP on market data does not have to be a stop on the *method*. The protocol under test is a computational object: given a call–put quote pair, decide whether the call–put implied-volatility spread (CPIV) is identified at a declared tolerance, and say so in a way that a downstream user cannot mistake for a measurement. That object can be exercised without a licence, and it must be exercised before a licence arrives, because a protocol whose thresholds are chosen after the first look at market data is exactly what the pre-registration exists to prevent.

So the programme splits in two:

- **Closed track (market data).** Unchanged. Every market-data entry point still raises `LicenceMissingError` without a written licence record. Nothing in this programme relaxes that.
- **Open track (synthetic benchmark).** A synthetic market whose *true* CPIV is defined before any quote exists, so the benchmark can report **accuracy** — not only coverage and stability. The generator, the protocol settings, the seed list, the specification grid, the null construction and the decision rules were all frozen in a pre-registration addendum written **before** the replication sweep was run.

The benchmark is not a substitute for the licensed run, and the manuscript does not pretend otherwise. It supports one kind of claim: *the measurement machinery behaves as specified, its abstention rule has a quantifiable selection effect, and the protocol's own thresholds can be fixed before any market data is read.* See §A1.8 of the addendum for the explicit non-claims.

---

## 2. One-page design

**Working title:** *When Is a Call–Put Implied-Volatility Spread Measurable? An Abstention-Aware Protocol for Option Quotes*

**Single claim.** A CPIV computed from midpoints is not automatically an identified or stable measurement. A predeclared, abstention-aware protocol can measure the coverage–stability trade-off against declared baselines on real quotes, and report what each abstention costs.

**Not claimed:** alpha, return predictability, sentiment, demand, borrow, arbitrage, profitability, or that any threshold is universal.

**RQ1 — Market coverage.** Among paired call–put quotes, what share survives each stage: raw midpoint IV on both legs, theoretical bounds, timestamp synchronisation, endpoint inversion, OTM-equivalent time-value rule, finite-shock identification, and the declared CPIV tolerance? Report a funnel with explicit denominators.

**RQ2 — Measurement sensitivity.** How far does CPIV move under bid/ask endpoint choice, quote and spot timestamp tolerance, forward/carry input, tick convention (full vs half tick), moneyness, maturity, bid–ask width, and liquidity regime?

**RQ3 — Ranking stability.** Against raw-midpoint CPIV, does the protocol reduce sign disagreement, raise Spearman rank correlation, reduce pairwise inversion rate, and reduce top/bottom tail turnover — and at what abstention cost? Report **own-set** and **common-set** comparisons separately; a gain from discarding hard pairs is not a gain.

**RQ4 — Temporal replication.** Does the primary-period result replicate in a holdout period never used for threshold selection or pipeline repair?

**Design.** One observation is a matched call–put pair: same underlying, strike, expiry, multiplier, exercise style and contract terms, with quotes inside a declared timestamp window. Every attempted pair receives exactly one terminal status; nothing is dropped. Baselines: raw midpoint CPIV; bound-filtered midpoint CPIV; bid–ask endpoint interval; parity residual (labelled algebraically dependent, not independent validation); abstention-aware protocol.

**Outcomes.** Coverage (resolved / attempted), sign disagreement, Spearman rank correlation and pairwise inversion rate on the common set, tail turnover, endpoint ambiguity, input sensitivity. Tolerance grid 0.05 / 0.10 / 0.25 pp, primary 0.10 pp, all thresholds reported.

**Inference.** Block bootstrap on underlying-day (2,000+ resamples), paired across baseline and protocol; effect sizes with intervals; p-values secondary; bootstrap unit stated in every table note.

**Replication.** Pilot (schema and feasibility only, never reported as a main result), primary, holdout. Configuration frozen before the primary run; no retuning on holdout.

**Data.** Licensed historical quotes only. No screenshots, delayed web chains, scraped pages, or last-traded prices used as spot.

---

## 3. Journal scope check — Journal of Computational Finance

Risk.net describes JCF as *"an international peer-reviewed journal dedicated to advancing knowledge in the area of financial mathematics"*, focused on *"the measurement, management and analysis of financial risk"*, and offering *"detailed insight into numerical and computational techniques in the pricing, hedging and risk management of financial instruments."*

| Requirement | Verified detail | Source |
|:--|:--|:--|
| Scope | Financial mathematics; numerical and computational techniques in pricing, hedging and risk management | [JCF landing page](https://www.risk.net/journal-of-computational-finance), [Call for papers](https://www.risk.net/static/call-for-papers) |
| Empirical market-data papers | Yes, when the data test or apply a method — e.g. local-volatility calibration on market data; risk-neutral density applied to DAX options | [Local vol. paper](https://www.risk.net/journal-of-computational-finance/5315561/local-volatility-models-in-commodity-markets-and-online-calibration), [RND paper](https://www.risk.net/journal-of-computational-finance/2160523/arbitrage-free-estimation-of-the-risk-neutral-density-from-the-implied-volatility-smile) |
| Length | Portfolio guidance: research papers should not exceed **10,000 words** ("not a strict policy") | [Risk Journals submission guidelines](https://www.risk.net/static/risk-journals-submission-guidelines) |
| Abstract | One paragraph, **150–200 words** | same |
| Keywords | **4–6** | same |
| Key messages | **3–4 bullets, each ≤85 characters** | same |
| References | Author–date in text, **APA** reference list | same |
| Anonymity | Submitted PDF without author names or affiliations; title page separate | same |
| Artwork | Figures and tables in the PDF **and** as separate editable files | same |
| Required sections | Conclusion with future research; declarations of interest; acknowledgements | same |
| Data and code | Data section describing the dataset and its selection; supplementary data and code **permitted, not mandatory** | same |
| Review | Editor-in-Chief screen, then external single-blind review | same |

**Fit caveat.** JCF's centre of gravity is computational technique with a pricing, hedging or risk-management consequence. A paper that only documents quote defects is a weaker fit than the plan assumes. See §5 for the framing decision this forces.

---

## 4. Four deltas the plan must absorb

**D1 — Word budget.** PLAN.md §13.1 targets 8,000–11,000 words. JCF's guideline is ≤10,000. Set the target at **8,000–9,500 words** of main text and keep references and supplement outside that count. An 11,000-word submission would open with a length objection that is entirely avoidable.

**D2 — Front matter the plan does not mention.** JCF requires a 150–200 word abstract, 4–6 keywords, **3–4 key messages of ≤85 characters**, APA author–date citations, a separate title page, and an anonymised PDF. The plan's manuscript structure (§13.2) has none of these slots. Key messages can only be written after the holdout result, because each must be a claim the evidence supports; they are not a place to pre-commit results.

**D3 — Timestamp requirements force intraday data.** PLAN.md §5.1 requires quote timestamps good enough to test synchronisation, and §9.3/§9.4 make timing a first-class perturbation. End-of-day sources (OptionMetrics IvyDB, HistoricalOptionData) cannot support that: every pair would share a vendor closing snapshot, so the timing stage becomes vacuous and RQ2's timestamp perturbation disappears. Either the study uses intraday NBBO snapshots, or the protocol is re-scoped to same-snapshot pairs and the timing RQ is removed **before** pre-registration. This is a protocol decision, not a data-shopping decision, and it must be recorded in `preregistration.md` §4.

**D4 — "Aggregate results" is not a publication right.** Several vendors treat published charts and tables as redistribution. Polygon/Massive says so explicitly; Cboe DataShop permits external distribution of derived data only with additional licensing fees and approval. The data gate therefore requires **written permission for the specific outputs** — journal tables and figures, supplementary aggregate CSVs, and a code repository — not merely a data licence. See [DATA_RIGHTS.md](DATA_RIGHTS.md) §4 for the request text.

---

## 5. Fit decision — locked 2026-10-22

The plan's claim is measurement validity. JCF's scope is computational technique. The bridge is one predeclared **secondary outcome**, not a new claim:

**Calibration input set (adopted).** At each declared tolerance, report how many contracts remain available to a surface calibration, and how the fitted surface differs between the raw-midpoint input set and the protocol input set. Descriptive only — no claim that either surface is more profitable, better specified, or tradeable.

**Hedge-ratio variant (rejected).** It answers a narrower question, requires a position and hedge convention the paper does not otherwise define, and would add a second object without adding fit.

Locking this before the freeze makes it a declared outcome rather than post-hoc framing. It is recorded in `preregistration.md` §10.1 and reported in one table. Adding any further computational outcome after the primary run is a protocol change under §15, not an extension.

---

## 6. What Phase 0 did not do

- As at 2026-10-22: no data purchase, trial download, or vendor contact was made, and the two vendor letters in `licence_correspondence/drafts/` were unsent. Their status after 2026-10-29 is in §10.
- No market-data pipeline was created. The data-independent measurement core now exists at `research/cpiv/measurement/` (US-001–US-010 in [prd.json](prd.json)) and runs only on synthetic fixtures; every market-data path stays behind the licence gate.
- The main pre-registration was **not** frozen. It cannot be, because universe, windows, sampling rule and tick convention all depend on the vendor's schema.
- No claim was made about any real security, index or option.

## 7. What the benchmark established

The full tally is in `research/cpiv/measurement/outputs/sweep/verdict.json`, produced by `research/cpiv/measurement/verdict.py`, which encodes the rules of addendum §A1.6 and reads only the sweep outputs. The development draw is excluded from every tally, as §A1.1 requires.

| Rule | Statement | Outcome |
|:--|:--|:--|
| R1 | The abstention rule selects a set that is genuinely easier to measure, not merely smaller | **PASS** |
| R2 | The protocol's own-set error is lower than the raw midpoint's | **PASS** |
| R3 | Certification coverage does not depend on one particular synthetic market | **FAIL** |
| R4 | Coverage is non-decreasing in the certification tolerance | **PASS** |
| R5 | The primary and holdout periods agree in direction and coverage | **PASS** |
| R6 | The perturbation set does not dominate the result | **PASS** |

**R1 is the substantive result.** The protocol does not re-estimate CPIV; on the common set it is numerically identical to the raw midpoint, so every own-set difference is a *selection effect*. R1 asks the question a reviewer would ask of such a claim: is the certified subset any better than an arbitrary subset of the same size? The answer is yes, and it survives the conservative null that draws whole underlying-days with replacement, preserving the within-day dependence the study's own intervals respect. The selection is not an artefact of picking a lucky subset.

**R3 failed, and that is a real finding, not a defect to be explained away.** Coverage is highly sensitive to market microstructure: specifications that widen quotes, coarsen the tick or shorten maturities drive certification coverage towards zero, while the base market certifies around eight per cent of attempted pairs at the primary tolerance. The protocol is therefore *not* a portable rule with a fixed coverage; it is a rule whose coverage is a property of the quote micro-structure it meets, and the paper must say so. A protocol that abstains almost everywhere in a coarse market is behaving correctly, and that is precisely the situation a reader needs warned about before applying the protocol to their own data.

**What the benchmark does not establish.** It contains no market data, so it supports no estimate of coverage, error or stability in any real market, and no claim that the certification tolerance is universal or optimal. It does not license a market statement in the manuscript. The licensed run, when it arrives, inherits the settings fixed here only if the vendor's schema permits them.

## 8. Next actions

Items 1 and 2 of the 2026-10-22 list are superseded by §10. Items 3 and 4 still stand, as the conditions for any later market study.

1. ~~Send the §4 request to Cboe DataShop and Databento.~~ Sent 2026-10-29; see §10.
2. ~~Record every answer verbatim in `licence_correspondence/`.~~ Records kept there; see §10.
3. When a written permission arrives, close §4 of `preregistration.md`, freeze it, tag the commit, and only then start Phase 1.
4. Keep the benchmark's public claim narrow. The manuscript's synthetic section is a methods and validation section; it is not an empirical result about markets.

## 9. Manuscript state — 2026-10-23

The submission package is built and checked; the file list, the verified limits and the four author-only fields are in [submission/README.md](submission/README.md). It consists of the anonymised manuscript, a separate title page, supplementary material (Appendices A and B, Table S1 strata, Table S2 declared settings), and one editable CSV per main-text table.

Two things changed in the manuscript relative to the earlier draft, and both are corrections rather than additions. Section 6.1 previously described the tolerance stage as removing pairs; the funnel shows that the stage removes none and separates the resolvable pairs into certified and identified-but-uncertified, so the abstention split is now reported as 719 + 77 + 26 = 822 of 894 attempted pairs, with every term read from the run. And the perturbation discussion previously called the spot and rate sensitivities "an order of magnitude" above the certified error; they are 8 and 6 times it, and the text now says so.

Six references that the list carried but the text never cited are now cited where they belong (Merton 1973 and Figlewski 1989 on bounds, Ofek et al. 2004 and Cremers and Weinbaum 2010 on parity deviations, Politis and Romano 1994 and Efron and Tibshirani 1993 on the resampling, Davison and Hinkley 1997 on the add-one p-value, Longstaff and Schwartz 2001 on the American pricer the benchmark does not use). Patton et al. (2009) was dropped: the day-block null fixes its block by construction and uses no automatic block-length rule. The chapter-and-verse of each limit is in [submission/README.md](submission/README.md).

The paper is submit-ready apart from the four title-page fields only the author can supply. It remains a synthetic benchmark: no licensed quote data was obtained, R3 still fails, and no sentence converts a benchmark number into a market claim.

## 10. Update — 2026-10-29: synthetic-only decision

- **Vendor letters sent 2026-10-29:** Cboe DataShop (Option Quotes, SPX) and Databento (OPRA, SPX), window 2023-04-03 to 2024-12-31. Records are in `licence_correspondence/`. Databento returned an automatic reply only; Cboe has not replied. No purchase was made.
- **Follow-ups unsent:** the drafts in `licence_correspondence/drafts/` are dated for 2026-11-05. They go out only if no substantive reply has arrived, and only with the author's approval.
- **Decision:** the paper stays synthetic-only. It states that no market data was used, licensed or otherwise, and that a market study is future work, conditional on a written licence covering publication of the outputs (DATA_RIGHTS.md §4).
- **Gate unchanged:** §1 stands (STOP on market data; PROCEED on the synthetic benchmark). The market track is not run in this paper.
