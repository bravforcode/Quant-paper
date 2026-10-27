# DRAFT — not sent

**Status:** prepared 2026-10-22, not sent. No reply has been received.
**Route:** DATA_RIGHTS.md §3 Route B.
**Send to:** Databento sales/support (licensing team).
**Alternative to send:** the same text through the in-app Databento console
messaging, which produces a written record with a message identifier.

---

**Subject:** Publication and redistribution rights for historical OPRA data — research licence inquiry

Dear Databento team,

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

Three product-specific questions for the OPRA dataset:

5. Your documentation notes that OPRA data before **2023-03-28** is subsampled
   and that the best available BBO granularity before that date is one minute,
   with timestamps that differ from the later packet capture. Please confirm
   whether the historical file I would receive for, say, 2023-04-03 to
   2024-12-31 carries **per-message `ts_event` and `ts_recv` nanosecond
   timestamps** for both MBBO and MBO messages, and whether a BBO-only
   subscription is sufficient for a bid/ask study.
6. The options feed does not carry the underlying price. Which underlying
   dataset and symbology would you recommend for a US equity underlying
   (e.g. IEX or consolidated top-of-book), and can the underlying and the
   options be subscribed together under one agreement?
7. Your licensing FAQ states that a licence is not needed to access historical
   (T+1) data, with redistribution as an exception that may require a licence.
   Please state explicitly whether the outputs I described in points 1–3
   above — journal tables and figures, a public code-and-aggregate deposit,
   and co-author or reviewer access — count as redistribution requiring a
   licence, and which licence tier covers them.

Please also confirm the permitted number of saved derived rows and whether a
one-off historical purchase is available without a recurring subscription.

If a pilot purchase of a small slice is the fastest way to answer points 5–7,
I am ready to buy a pilot for the stated dates; please tell me the smallest
slice that would settle them.

I would also be glad to receive the OPRA schema reference and the licence
schedule, so that I can confirm the required fields against a real
specification rather than against the product page.

Thank you for your time.

Sincerely,
[Author name]
[Affiliation or "independent researcher"]
[Contact email]
