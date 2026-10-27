# Pre-registration — CPIV measurement protocol (v0.1-draft)

```
status:            DRAFT — NOT FROZEN
version:           0.1-draft
date:              2026-10-22
freeze_commit:     null
frozen_config_hash: null
blocked_on:        DATA-LICENCE
target_journal:    Journal of Computational Finance (primary)
fallback_journal:  Quantitative Finance
baseline_paper:    research/cpiv/manuscript_r33_proposed.md
```

**This document is not in force.** It records every decision that is already settled and marks every decision that cannot be settled until a licensed dataset exists. A run against this file is exploratory and cannot be reported as a preregistered result. PLAN.md §6 governs the freeze: no primary analysis may be run before this file is completed, frozen, and tagged `v0-preregistered`.

## 1. Claim and scope

**Claim.** A CPIV computed from midpoints is not automatically an identified or stable measurement; a predeclared, abstention-aware protocol can measure the coverage–stability trade-off against declared baselines on real quotes.

**Out of scope.** Return predictability, trading strategies, alpha, causal interpretation via sentiment, demand or borrow, and any claim that a threshold is universal. This file does not authorise any of them.

**Status vocabulary.** "Unresolved" means the data and contract do not support certifying a measurement or ranking. It never means "CPIV equals zero", "bad data", or an implicit abstention that the analysis may ignore.

## 2. Data and the licence gate

- Source: one licensed historical quote product, identified in `DATA_RIGHTS.md` and recorded in the run manifest.
- Mandatory fields: call/put bid, ask, quote timestamp, underlying price, underlying timestamp, strike, expiry, multiplier, exercise style, settlement, corporate-action state.
- Mandatory rights: publication of aggregate results; public deposit of code and aggregate outputs; no raw-quote redistribution.
- **Rule:** the pipeline refuses to run any market-data path unless a licence record exists that names the vendor, the permitted outputs, and the expiry. Absence of a record is a hard failure, not a warning.

`TBD-DATA`: vendor, product, window, and the licence record path.

## 3. Universe

`TBD-DATA`. Options under consideration:

- **U1** — SPX (European, cash-settled) with the Cboe index feed for the underlying. Cleanest match to a European common inversion map.
- **U2** — SPY / QQQ / IWM (American). Underlying quotes arrive with the option quotes, but the European BSM map is then an explicitly declared common inversion map, and the American-pricer robustness section is mandatory.

Whichever is chosen must be stated here before the freeze, together with the minimum cross-sectional universe size per underlying-date and the liquidity filter. The choice may not be revisited after the pilot.

## 4. Sampling and synchronisation

`TBD-DATA`, and `TBD-DECISION` on D3 of `PHASE0.md`.

If an intraday source is licensed:

- Snapshot times sampled on a declared grid; one snapshot per underlying per time.
- Call–put lag, call–spot lag and put–spot lag are recorded for every attempted pair.
- A pair is synchronised only if all three lags are within the declared tolerances; anything else is terminal `TIMING_MISMATCH`, with the lags retained.
- RQ2 perturbations: strict vs relaxed quote tolerance; small observed perturbation of the spot timestamp.

If only an EOD source is licensed, this section must instead declare same-snapshot pairing, delete the timestamp stages from RQ1 and the timestamp perturbation from RQ2, and record the deletion here. That amendment must happen before the freeze, not after the primary run.

## 5. Inputs

`TBD-DATA`: rate curve source, forward/carry construction, dividend or yield convention, and the hierarchy used when more than one input is available. Priority order among sources must be fixed here, not chosen per observation.

Locked conventions (inherited from r33 §5):

- Continuously compounded rates and yields; 365-day year.
- Prices per underlying unit internally; contract multiplier applied consistently at ingestion.
- Volatility decimal internally, percentage points in every reported CPIV.
- No yield is interpreted as a borrow fee or funding charge.

## 6. Eligibility

Locked:

- Paired call and put on the same underlying, strike, expiry and multiplier.
- Positive time to expiry; finite prices; positive spot and strike.
- Moneyness reported as `K/S`, with `S` the synchronised underlying price.
- Pairs failing any structural check are terminal, not dropped.

`TBD-DATA`: maturity bands, minimum OTM-equivalent time value in ticks, bid–ask width buckets, liquidity buckets, price-level buckets.

## 7. Inversion contract

Locked (r33 §5):

- Model: European Black–Scholes–Merton as the **common inversion map**, never as an economic description of an American contract.
- Bracket: decimal IV in `[1e-8, 5]`; bisection, 64 iterations maximum, no quote clipping.
- Near-bound guard: prices within `1e-10` currency units of a European bound are rejected and classified, not silently inverted.
- Every successful root is repriced; repricing error and IV-recovery error are recorded separately.
- Failure classes retained: invalid input, theoretical-bound violation, near-bound guard, outside bracket, numerical/unclassified.

These are implementation settings. They are not market filters and not evidence about how often real quotes fail.

## 8. Resolution protocol and terminal statuses

Locked. A pair is *resolved* only when all of the following hold: contract matched; timestamp synchronised; inputs complete and in the declared units; both midpoint roots finite; every required endpoint invertible or recorded as a one-sided bound; OTM-equivalent time values above the declared resolution scale; a declared finite positive/negative shock yields valid roots; worst-direction IV displacement within tolerance; no imputation.

Every attempted pair receives **exactly one** terminal status:

| Status | Meaning |
|:--|:--|
| `RESOLVED_WITHIN_TOLERANCE` | All conditions hold and displacement is within the primary tolerance |
| `IDENTIFIED_OUTSIDE_TOLERANCE` | Measurement is identified but the displacement exceeds the primary tolerance |
| `PARTIALLY_RESOLVED` | One or more endpoints are one-sided bounds; the pair supports at most a partial order |
| `UNRESOLVED` | The declared contract cannot certify a measurement (e.g. time value below the resolution scale, no finite-shock root) |
| `INVALID_INPUT` | Prices, spot, strike, expiry, units or inputs fail validation |
| `TIMING_MISMATCH` | Synchronisation tolerance exceeded or timestamps unusable |
| `CONTRACT_MISMATCH` | Terms differ: underlying, strike, expiry, multiplier, exercise style, settlement, corporate action |

Cause is recorded as a separate reason code (`QUOTE_INVALID`, `MIDPOINT_NONINVERTIBLE`, `ENDPOINT_INCOMPLETE`, `TIME_VALUE_BELOW_SCALE`, `FINITE_SHOCK_ABSENT`, `INPUT_INCOMPLETE`, …). A terminal status is never inferred from a missing reason code, and a reason code never replaces a terminal status.

**Reconciliation:** counts by terminal status must sum to attempted pairs, and every intermediate stage count must equal the sum of the statuses downstream of it. A non-zero residual is a run failure.

## 9. Tolerance grid

Locked: `[0.05, 0.10, 0.25]` pp, all reported. Primary tolerance `0.10` pp, fixed before the primary run and not selected by inspecting results. Displacement is the worst-direction IV movement of the CPIV estimate under the declared perturbation set.

## 10. Outcomes

Locked definitions:

| Outcome | Definition |
|:--|:--|
| Coverage | Resolved pairs ÷ attempted pairs |
| Sign disagreement | Share of pairs with opposite CPIV sign across a declared perturbation |
| Rank stability | Spearman correlation on the common set |
| Pairwise inversion rate | Share of unordered pairs whose order reverses |
| Tail turnover | Share of top/bottom tail membership that changes |
| Endpoint ambiguity | Share of intervals that overlap |
| Input sensitivity | CPIV change under the declared input perturbation |
| Abstention cost | Coverage forgone, reported beside every stability gain |

Every comparison is reported twice: **own-set** (each method on its own eligible set) and **common-set** (only observations both methods can use). A stability gain that exists only on the own-set comparison is reported as a selection effect, not as an improvement.

### 10.1 Secondary outcome — calibration input set (locked 2026-10-22)

At each declared tolerance, report:

- contracts retained in the calibration input set under raw-midpoint versus protocol resolution;
- the change in the fitted surface between the two input sets, using the fit declared in `secondary_outcome.calibration_fit`;
- the abstention cost, in coverage, beside the change.

Descriptive only. No claim about profitability, forecasting, or which surface is correct. The hedge-ratio alternative was considered and rejected before the freeze. No further computational outcome may be added after the primary run; doing so is a protocol change under §15.

## 11. Baselines

Locked, all four required:

1. Raw midpoint CPIV.
2. Midpoint CPIV after a conventional no-arbitrage/bound filter.
3. Bid–ask endpoint interval, reported as a quote-implied range. Never a confidence interval, coverage statement, probability range or arbitrage bound.
4. Parity-residual diagnostic, labelled in every table as algebraically dependent on CPIV under the common BSM map. It is not independent validation.

Plus the abstention-aware protocol itself.

## 12. Inference

Locked:

- Dependence unit: underlying-day (or underlying-date-sampling-time where an intraday grid is used). Options are not treated as IID.
- Block bootstrap, 2,000+ resamples, resampling baseline and protocol outcomes in the same block.
- Report effect size with interval; p-values are secondary.
- Every table note states the bootstrap unit and the number of resamples.

## 13. Exclusions and missing endpoints

Locked:

- No pair is excluded after its result is known.
- A missing endpoint stays in the denominator and is reported as a one-sided bound or a terminal status.
- No imputation of missing endpoints, no substitution of a last-traded price for a missing quote, no interpolation across strikes or maturities to fill a gap.
- Exclusion rules operate on declared fields only and are applied before inversion.

## 14. Holdout

`TBD-DATA` window, but locked rules: the holdout uses the frozen configuration unchanged — no new thresholds, filters, windows, or narrative revision before seeing the result. If holdout disagrees with primary, it is reported as disagreement and the claim is reduced. The holdout is never used for selection.

## 15. Freeze and change control

1. Complete §2–§6 and §14; replace every `TBD-*`.
2. Record the configuration file hashes in `frozen_config_hash`.
3. Commit and tag `v0-preregistered`.
4. Only then run the primary analysis.
5. A code bug may be fixed after the freeze. A protocol change may not: it requires a new version of this file, a new tag, and a new primary period.
6. Any change made after seeing primary outcomes forces a fresh primary period, not an amended result.

## 16. Open blocks

| Block | Depends on | Owner |
|:--|:--|:--|
| §2 vendor, licence record | written licence | author |
| §3 universe U1 vs U2 | licence scope and underlying fields | author |
| §4 sampling and D3 decision | licence schema | author |
| §5 rate/carry hierarchy | vendor inputs | author |
| §6 maturity/width/liquidity buckets | pilot, but declared before primary | author |
| §14 holdout window | licence window | author |
