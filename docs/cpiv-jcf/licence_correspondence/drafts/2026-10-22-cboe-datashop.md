# DRAFT — not sent

**Status:** prepared 2026-10-22, not sent. No reply has been received.
**Route:** DATA_RIGHTS.md §3 Route A.
**Send to:** Cboe DataShop sales/support (order form and licence schedule).

---

**Subject:** Publication rights and field scope for Option Quotes (NBBO snapshots) — research licence inquiry

Dear Cboe DataShop team,

I am an independent researcher preparing a journal article for the *Journal of
Computational Finance* on the measurability of call–put implied-volatility
spreads from paired option quotes. The article studies a measurement protocol:
when a call–put implied-volatility spread computed from bid/ask midpoints is
identifiable at a declared tolerance, and when it is not. The study reports
coverage, rank stability and abstention accounting for a set of paired
call/put quotes. It does not use the data for trading, signal construction, or
price prediction, and it reports no security-level or contract-level results.

Before I purchase, I need written confirmation on four points:

1. The licence permits publication of **aggregate results** — tables, figures
   and summary statistics — in a peer-reviewed journal article and its
   supplementary material.
2. The licence permits depositing **analysis code and aggregate outputs** in a
   public repository (e.g. Zenodo), with no raw quotes redistributed.
3. Co-authors and journal reviewers who are not licensees may read the
   aggregate outputs in the manuscript; raw records stay inside the licensed
   environment.
4. The licensed fields include bid, ask, quote timestamp, underlying price,
   underlying timestamp, strike, expiry, multiplier and exercise style for
   the window [DATES] and universe [SYMBOLS].

Two product-specific questions for Option Quotes:

5. The Option Quotes page describes NBBO snapshots at 1-minute intervals. Do
   the delivered files carry a **quote-level timestamp per record** (not only
   the snapshot interval label), and what timestamp fields are present for the
   option bid/ask and for the underlying bid/ask? My synchronisation stage
   requires a timestamp per quote and a separate timestamp for the underlying
   price.
6. The Option Quotes page states that the underlying bid/ask is included for
   equities and ETFs, and that the SPX/OEX underlying requires an active Cboe
   Global Indices Feed licence. Please confirm (a) whether an **SPX** universe
   would require that separate feed licence in addition to Option Quotes, and
   its cost, and (b) whether an **SPY / QQQ / IWM** universe is covered by
   Option Quotes alone, with the underlying bid/ask included in the same
   files.

Please also confirm the permitted number of saved derived rows and whether a
one-off historical purchase is available without a recurring subscription.

One further point, taken from the Cboe Open/Close Volume Summary product terms
("raw data is licensed for internal use only … external distribution of derived
data is permitted subject to additional licensing fees and approval"): please
confirm in writing whether that clause applies to Option Quotes as well, and
what "external distribution of derived data" means for journal tables and
figures. If it means that published tables built from the data require a
separate approval or fee, I need to know that before purchase, because the
article's central output is a table of aggregate results.

I would be glad to receive the sample file format for Option Quotes and the
licence schedule, so that I can confirm the required fields against a real
specification rather than against the product page.

Thank you for your time.

Sincerely,
[Author name]
[Affiliation or "independent researcher"]
[Contact email]
