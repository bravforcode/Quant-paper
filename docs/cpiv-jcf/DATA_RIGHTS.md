# Data-rights check — historical option quotes for CPIV

**Checked:** 2026-10-22. Prices and terms change; every entry below is a public-page reading, not a contract. Nothing here is legal advice.

**Verdict:** no source checked today is usable as-is. The closest routes require a written publication permission that none of their public pages grants.

## 1. What the study needs

PLAN.md §5.1, restated as pass/fail requirements:

| ID | Requirement |
|:--|:--|
| R1 | Call and put **bid and ask**, paired by underlying, strike and expiry |
| R2 | Quote-level **timestamps** precise enough to test call–put and quote–spot synchronisation |
| R3 | Underlying price with its own timestamp |
| R4 | Strike, expiry, multiplier, exercise style, settlement, corporate-action state |
| R5 | Rate and forward/carry inputs, or enough data to construct them |
| R6 | Licence for scholarly research **and** publication of aggregate results |
| R7 | Permission to deposit **code + aggregate outputs** publicly, with no raw quotes |
| R8 | Terms that do not require an institutional affiliation the author does not have |

R2 is the binding constraint. It eliminates every end-of-day product, because a vendor closing snapshot makes the synchronisation stage vacuous and removes the RQ2 timestamp perturbation (PHASE0.md D3).

R6 and R7 are where most retail licences fail, including ones that look permissive.

## 2. Provider comparison

"Not stated" means the public page does not say; it does not mean the vendor refuses. All of these are negotiable in principle — the question is what is in writing before purchase.

| Provider / product | Fields and timestamps | Publication and academic terms | Public price |
|:--|:--|:--|:--|
| **Cboe DataShop — Option Quotes** | NBBO snapshots at 1-minute or custom N-minute intervals, from Jan 2012. Quote datetime, root, expiration, strike, type, interval OHLC, bid/ask and sizes, optional OI/Greeks/IV. Underlying bid/ask included for equities and ETFs; **SPX/OEX underlying requires an active Cboe Global Indices Feed licence**, other indices' underlying not included. | Option Quotes page states no academic licence. A related DataShop product states: *"Raw data is licensed for internal use only and may not be redistributed externally in any form. External distribution of derived data is permitted subject to additional licensing fees and approval."* That clause must be confirmed for this specific product. Price not stated. | Not public; order-based |
| **Databento — OPRA** | OPRA history since 2013; trades plus BBO/NBBO and instrument definitions, `ts_event` and `ts_recv` at nanosecond precision. **Before 2023-03-28 data is subsampled; best available BBO granularity is one minute** and timestamps differ from later packet capture. No spot price in the options feed — join a separate underlying feed. | Licensing FAQ: *"You do NOT need a license to access historical (T+1) data"*, but redistribution is an exception that may require a licence. Aggregate academic publication not specifically resolved. | Historical from **$0.04/GB**; total depends on scope |
| **OptionMetrics — IvyDB US** | EOD from Jan 1996: closing bid/ask, volume, OI, strike, expiry, call/put, underlying high/low/close, IV and Greeks. **No intraday quote timestamps and no intraday spot.** | Academic licence exists, *"significantly discounted rate to academic institutions"*; commonly delivered through a subscribing WRDS institution. WRDS guidance says materially transformed or aggregated results are commonly acceptable, but that is not an IvyDB-specific publication grant. | Not public |
| **HistoricalOptionData.com (DeltaNeutral)** | EOD OPRA NBBO, underlying price, strike, expiry, bid/ask/last, volume, OI, optional Greeks/IV. Field docs say most quotes are timestamped 4:00 p.m. while trading can run to 4:15 p.m. | Advertises academic pricing and site licences; **publication clause not published**. | Individual 24-year history: **$1,150 / $1,495 / $2,035** by level; academic by inquiry |
| **ThetaData** | Retail tiers advertise full OPRA NBBO tick history, 6/10/14 years; exact timestamp convention and spot fields not established from the fetched pages. | Terms limit use to *"personal, non-commercial"* and prohibit publishing or creating derivative works. Commercial plan is a commercial-use licence, not an academic publication licence. | Retail **$40 / $80 / $160 per month**; commercial **$1,600/month** |
| **ORATS** | Near-EOD full-chain NBBO snapshot about 14 minutes before close (≈3:46 p.m. ET). Underlying value derived from put–call parity, stated as internal use only. | Terms bar distributing or redistributing the service or materials *"including the publications"*. | **$599** one-time + **$99/month** |
| **Polygon / Massive** | OPRA-sourced quotes and trades, nanosecond timestamps claimed; field-level options schema not independently verified here. | Individual terms are personal, non-business. Redistribution FAQ is explicit: **publishing charts or tables built from the data counts as redistribution**; the individual plan does not cover it. Business plan may, but that is not an academic right. | Plan prices not verified |
| **Intrinio** | EOD opra-sourced chains (close bid/ask, IV, Greeks); intraday historical ticks and bars from 2022-12-08, enterprise only. | Terms permit no display, publication or distribution **unless expressly authorised in an executed order form**. | EOD from **$150/month**; intraday enterprise, price not public |
| **ICE Data Services** | OPRA composite BBO and trades, native exchange timestamps plus ICE UTC timestamps; history from Feb 2010; Consolidated History up to 15 years tick-level. | No academic or publication grant on the public page. | Not stated |
| **LSEG / Refinitiv** | OPRA NBBO, exchange BBO, contract specs, EOD and Tick History from 1997. | Redistribution is a separate product line; no academic publication term verified. | Not stated |
| **Bloomberg** | B-PIPE and Data License exist, but the accessible pages did not establish a research-suitable historical options quote archive. | Do not assume Terminal access includes a right to publish derived figures. | Not stated |
| **OptionsDX** | Intraday "up to minutely" quotes for selected US equity/index options; fields include quote timestamps, underlying last, bid/ask and sizes. **NBBO status not established.** | Free subset exists; paid full-history price and publication rights not established. | Not stated |

Sources: [Cboe Option Quotes](https://datashop.cboe.com/option-quote-intervals), [Cboe derived-data clause](https://datashop.cboe.com/cboe-options-open-close-volume-summary), [Databento options](https://databento.com/options), [Databento OPRA specs](https://databento.com/docs/datasets/opra-pillar), [Databento licensing FAQ](https://databento.com/blog/introduction-market-data-licensing), [OptionMetrics US](https://optionmetrics.com/united-states/), [WRDS OptionMetrics](https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/optionmetrics/), [WRDS co-authorship guidance](https://wrds-www.wharton.upenn.edu/pages/about/navigating-co-authorship-across-institutions-a-guide-to-data-sharing-and-compliance/), [HistoricalOptionData](https://historicaloptiondata.com/), [its field docs](https://historicaloptiondata.com/data-structure/), [ThetaData terms](https://thetadata.net/terms-and-conditions), [ORATS terms](https://orats.com/terms-conditions), [Massive redistribution FAQ](https://massive.com/knowledge-base/article/how-can-i-redistribute-massives-market-data), [Intrinio terms](https://about.intrinio.com/terms), [ICE OPRA](https://developer.ice.com/fixed-income-data-services/catalog/opra-options-price-reporting-authority), [LSEG OPRA](https://www.lseg.com/en/data-catalogue/derivatives/pricing/exchange-derivatives-options-price-reporting-authority-opra), [OptionsDX fields](https://www.optionsdx.com/option-chain-field-definitions/).

## 3. Ranked routes

**Route A — Cboe DataShop Option Quotes.** The only verified product that gives 1-minute NBBO snapshots with quote timestamps *and* an underlying bid/ask for equities and ETFs without a second vendor. Two sub-options:

- **A1 (cleaner model):** SPX options, European exercise, cash settled — the plan's preferred universe. Requires the Cboe Global Indices Feed licence for the SPX underlying, so price the bundle.
- **A2 (simpler licence):** SPY/QQQ/IWM, American exercise. Underlying quotes come with the option quotes, but the European BSM map becomes a declared common inversion map rather than an economic description, and the American pricer robustness section is mandatory. r33 already quantifies how large that bias can be (up to 51.79 pp deep ITM in the synthetic grid), so A2 is not a free shortcut.

**Route B — Databento OPRA.** Event-level timestamps and the strongest documentation, but three costs: a separate underlying feed, a window after 2023-03-28 for full granularity (about 3.5 years at the time of writing), and an unresolved publication question. Usage pricing makes a pilot cheap enough to test the water.

**Route C — OptionMetrics IvyDB.** Best long history and the normal academic route, but EOD only. Choosing it means amending the protocol to same-snapshot pairs and deleting the timing stages of RQ1/RQ2 before the freeze. It also normally requires a subscribing institution, which the author does not have.

**Excluded for publication use without a negotiated order form:** ThetaData retail, ORATS, Polygon/Massive individual, Intrinio standard. Their standard terms do not permit publishing the outputs this paper requires.

## 4. Written request to send

Send this verbatim, adapted only for the vendor's product name. Keep the reply.

> I am an independent researcher preparing a journal article on the measurability of call–put implied-volatility spreads. I would like to license [PRODUCT] for a defined historical window and need written confirmation on four points before purchase:
>
> 1. The licence permits publication of **aggregate results** — tables, figures and summary statistics — in a peer-reviewed journal article and its supplementary material.
> 2. The licence permits depositing **analysis code and aggregate outputs** in a public repository (e.g. Zenodo), with no raw quotes redistributed.
> 3. Co-authors and journal reviewers who are not licensees may read the aggregate outputs in the manuscript; raw records stay inside the licensed environment.
> 4. The licensed fields include bid, ask, quote timestamp, underlying price, underlying timestamp, strike, expiry, multiplier and exercise style for the window [DATES] and universe [SYMBOLS].
>
> Please also confirm the permitted number of saved derived rows and whether a one-off historical purchase is available without a recurring subscription.

If a vendor says "aggregate is fine" verbally, ask for the sentence in the order form or the licence schedule. A support email is weaker evidence than the contract, but it is still evidence; record both.

## 5. Red lines

- No scraped chains, screenshots, delayed web chains, or vendor pages without an explicit right to publish.
- No "free" dataset whose upstream rights are unverified — the r33 Section 9 note already records why this fails.
- No last-traded price used as spot without reporting staleness.
- No pair selected because its midpoint inverted; selection must precede inversion.
- No purchase before the four answers in §4 arrive in writing.

## 6. What would change the verdict

- A Cboe order confirmation that includes external distribution of derived data for this product.
- A Databento written confirmation covering journal tables/figures and a public code+aggregate deposit.
- A university or library that offers WRDS access, which would reopen OptionMetrics under Route C.
- An academic licence from HistoricalOptionData with a publication clause — cheap, but EOD only, so Route C's protocol amendment applies.
