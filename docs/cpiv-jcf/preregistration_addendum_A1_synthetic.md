# Pre-registration addendum A1 — synthetic ground-truth study

```
status:            FROZEN FOR THE SYNTHETIC INSTRUMENT ONLY
version:           A1
date:              2026-10-22
applies_to:        the synthetic benchmark study and its replication sweep
does_not_apply_to: any market-data run (see preregistration.md, still v0.1-draft)
parent_document:   preregistration.md v0.1-draft
freezes:           research/cpiv/measurement/configs/study.yaml
                   research/cpiv/measurement/{dgp,study,frontier,sweep}.py
evidence_artifact: research/cpiv/measurement/outputs/study/, .../outputs/sweep/
```

## A1.0 Why this addendum exists

`preregistration.md` cannot be frozen, because the licence gate is closed: no
licensed historical quote product exists for this project (PHASE0.md §1). That
would normally leave every threshold — the certification tolerance, the
resolution scale, the synchronisation tolerance, the perturbation set — to be
chosen *after* the first look at market data, which is exactly the practice
the protocol exists to prevent.

This addendum closes that gap for everything that can be closed without market
data. The synthetic benchmark fixes a **known truth** before any quote exists
(see §A1.2), so it can be used to

1. exercise the entire protocol, including its failure paths;
2. fix every analytic knob on a benchmark whose answer is known;
3. state, *in advance*, what the benchmark is allowed to conclude.

The addendum does **not** license any market claim, and it does not make the
main pre-registration frozen. When a licence arrives, `preregistration.md` is
completed and frozen separately, and the market run inherits the settings fixed
here only if the licensed data's schema permits them.

## A1.1 Development draw and replication evidence

The base-market study was run once before this addendum was written, so its
output was visible to the author while these rules were drafted. To keep that
honest, the draws are split:

| Label | Draw | Role |
|:--|:--|:--|
| **Development draw** | seed `20261022` | The base-market study, `outputs/study/`. Reported in full for transparency. **Excluded from every replication tally in §A1.6.** |
| **Replication evidence** | seeds `20261022 + 7919k`, `k = 1 … 23` | The 23 declared replication seeds, run after this addendum was written and before any of their outputs was read. |

Every decision rule in §A1.6 is evaluated on the 23 replication seeds. The
development draw is reported alongside but never counted toward a rule.

## A1.2 The instrument

**Generator** (`research/cpiv/measurement/dgp.py`, spec frozen in
`configs/study.yaml`):

- Two underlyings (`SIM-A` at 100, `SIM-B` at 250), 30 trading days each,
  14/30/60-day expiries, strikes at 90/95/100/105/110 % of spot: 894 attempted
  pairs at the base specification.
- Rate 5 % continuously compounded, dividend yield 0, base volatility 22 %,
  term slope +0.12 pp/day, log-moneyness skew −1.10.
- **American** options. The call leg is worth exactly its European value (no
  early exercise without dividends); the put leg carries a real early-exercise
  premium, priced by an 800-step Cox–Ross–Rubinstein lattice.
- Microstructure: 0.01 tick rounding, half-spread of one tick plus one extra
  tick in the wings (|log-moneyness| ≥ 0.09) and one extra tick at the short
  end, doubled on every seventh session; timestamp jitter of ±0.35 s; injected
  defects at declared rates (stale 1.5 %, crossed 0.8 %, out-of-bounds 0.5 %,
  contract mismatch 0.5 %, missing leg 0.4 %).

**Truth.** The true call–put implied-volatility spread is defined *before* the
quote exists: the unrounded fair values of both legs are inverted under the
same European Black–Scholes–Merton map that the protocol uses. The spread is
therefore non-zero by construction — it is the volatility-equivalent of the
American exercise premium — and it is exactly the quantity a correct
measurement should recover.

**What this makes possible.** A licensed market sample can report coverage and
stability, but it can never report *accuracy*, because the truth is unknown.
The benchmark can. Every accuracy number in the study is against this
defined truth, not against a proxy.

**What it does not make possible.** The truth is a property of a *model* — the
synthetic market and the common European inversion map. It is not a claim
about any real security, and nothing measured here transfers to real quotes
without the licensed run.

## A1.3 Protocol under test (frozen)

The protocol is the one specified in `preregistration.md` §7–§9, with the
settings below. No value in this list may be changed in response to a result.

| Setting | Value |
|:--|:--|
| Inversion map | European Black–Scholes–Merton, common to both legs |
| Root bracket | decimal IV in `[1e-8, 5]`, bisection, ≤64 iterations, no clipping |
| Near-bound guard | prices within `1e-10` of a European bound are rejected, not inverted |
| Resolution scale | 1 tick of OTM-equivalent time value |
| Synchronisation tolerance | 2 s for call–put, call–spot and put–spot lags |
| Tolerance grid | 0.05 / 0.10 / 0.25 pp, all reported |
| Primary tolerance | **0.10 pp**, fixed before any result |
| Sign band | 0.05 pp |
| Perturbation set | endpoint widened by half a tick; spot +1 bp; rate +5 bp; spot timestamp −3 s; resolution scale halved to 0.5 tick; synchronisation tolerance relaxed to 5 s |
| Period split | primary = days 0–14, holdout = days 15–29 |
| Inference unit | underlying-day block bootstrap, 2,000 resamples, seed 20261022 |

Every attempted pair receives exactly one terminal status, and the run fails if
the status counts do not reconcile against the attempted count.

## A1.4 Pre-specified outcomes

1. **Accuracy against truth** — mean absolute error of the raw-midpoint CPIV
   and of the protocol-certified CPIV, in percentage points, on the set each
   method can use (own-set) and on the set both can use (common-set).
2. **Error profile** — median, p90, p95, maximum absolute error, and the share
   of pairs within 0.10 pp, for each method.
3. **Coverage** — resolved ÷ attempted, at every tolerance, with the
   denominators stated.
4. **Selection frontier** — for each tolerance, the certified subset against
   two size-matched nulls: a **pair null** (uniform over scored pairs) and a
   **block null** (whole underlying-days with replacement, preserving the
   within-day dependence). 2,000 Monte Carlo trials, add-one p-values.
5. **Abstention accounting** — the raw-midpoint error on the abstained set,
   the terminal-status mix of the abstentions, and the coverage forgone.
6. **Strata** — coverage and error by moneyness, maturity, spread and truth
   magnitude.
7. **Perturbation response** — coverage change and CPIV change under each of
   the six declared perturbations.
8. **Replication** — primary and holdout periods compared, never merged into a
   single headline number.

## A1.5 Pre-specified replication design

**Seed sweep.** 23 replication seeds, `20261022 + 7919k` for `k = 1 … 23`,
each a complete re-draw of the synthetic market and a complete re-run of the
protocol, reported as a distribution.

**Specification sweep.** 17 declared specifications, one factor at a time
away from the base market, applied to the base seed:

| Group | Cases |
|:--|:--|
| Market | `base`, `low_vol` (15 %), `high_vol` (35 %), `wide_quotes` (2 ticks), `very_wide_quotes` (3 ticks), `coarse_tick` (0.05), `no_wide_sessions`, `wide_strike_grid` (85–115 %), `short_dated` (7/14/30 d), `long_dated` (30/60/90 d) |
| Protocol | `tolerance_0.05pp`, `tolerance_0.10pp`, `tolerance_0.25pp`, `tolerance_0.50pp`, `resolution_0.5ticks`, `resolution_1ticks`, `resolution_2ticks` |

The market group varies the *market*; the protocol group varies the *analyst's
knobs* on one fixed market, which is the coverage–error frontier an analyst
actually faces.

**Count corrected 2026-10-24.** The first version of this addendum said
"18 declared specifications". The enumerated list above — which is the
binding one — contains 17: the base, nine market variants and seven
protocol variants. No specification was added, removed or renamed, and the
sweep output has 17 rows.

## A1.6 Pre-specified decision rules

Each rule is a statement that the benchmark can falsify. A rule that fails is
reported as a failure, in the same prominence as a rule that passes.

| Rule | Statement | Pass condition (on the 23 replication seeds) |
|:--|:--|:--|
| **R1 — selection** | The abstention rule selects a set that is genuinely easier to measure, not merely smaller. | Certified MAE below the block-null mean in **≥ 16 of 23** draws, and block-null p < 0.05 in **≥ 16 of 23** |
| **R2 — own-set accuracy** | The protocol's own-set error is lower than the raw midpoint's own-set error. | Own-set MAE(certified) < own-set MAE(raw) in **≥ 16 of 23** draws |
| **R3 — coverage stability** | The certification coverage does not depend on one particular synthetic market. | Across the 10 market specifications, the minimum certified coverage at the primary tolerance is **≥ 50 %** of the median coverage |
| **R4 — tolerance monotonicity** | Coverage is non-decreasing in the certification tolerance. | Holds in **≥ 22 of 23** draws |
| **R5 — period agreement** | The primary and holdout periods agree in direction. | Coverage sign of the error reduction agrees (both positive or both negative) in **≥ 16 of 23** draws, and holdout coverage is within **10 percentage points** of primary coverage in **≥ 16 of 23** |
| **R6 — perturbation sanity** | The perturbation set does not dominate the result. | No single perturbation changes certified coverage by more than **15 percentage points** in absolute value in the base market |

**Falsification consequence.** If R1 or R2 fails, the benchmark shows that
abstaining on hard pairs does **not** buy accuracy, and the paper's central
mechanism claim must be reduced to coverage and stability only. That
reduction is binding on the manuscript, the key messages and the abstract.

**Prohibited moves.** No rule may be reworded, retuned or dropped after the
sweep output is read. Any change requires a new addendum version, a new
sweep, and a fresh tally. Seeds may not be dropped, added or reordered. A
specification may not be removed because it disagrees with the base case; if a
specification fails, it is reported.

## A1.7 Reporting rules

- The unit of reporting is a **distribution** over draws: median and
  interquartile range as the headline, full range, and every individual draw
  in the released CSV.
- No seed, specification or stratum may be singled out as *the* result. The
  development draw is reported separately (§A1.1), never as the headline.
- The abstention mechanism is described as a **selection effect** wherever an
  own-set comparison is shown, and the frontier p-values are reported beside
  every such comparison.
- The synthetic truth is described as a **model artifact**. No sentence in the
  manuscript may convert a synthetic number into a statement about real
  markets; the words "in the benchmark" are mandatory wherever a number is
  reported.
- A null result is reported with the same prominence as a positive one.

## A1.8 Explicit non-claims

The benchmark does not support, and the manuscript must not assert:

- any estimate of coverage, error or stability in a real market;
- any statement about a real security, index or option;
- any claim of trading profitability, alpha or forecasting value;
- any claim that the certification tolerance is universal or optimal;
- any external-validity claim from the synthetic market to real quotes.

The benchmark supports exactly one kind of claim: **that the measurement
machinery behaves as specified, that its abstention rule has a quantifiable
selection effect, and that the protocol's own thresholds can be fixed before
any market data is read.**

## A1.9 Freeze statement

The generator specification, the protocol settings, the seed list, the
specification grid, the null construction, the trial counts and the decision
rules in this addendum are fixed as of 2026-10-22. They were written before
any replication-sweep output was read; the single base-market study that had
already been run is declared as the development draw and is excluded from every
tally.

The tally that applies these rules to the replication outputs is produced by
`research/cpiv/measurement/verdict.py`, which encodes the rules above and
reads only `outputs/sweep/`. A code bug may be fixed after the freeze; a
change to a rule, a seed, a specification or a threshold may not. Such a
change requires a new addendum version and a fresh sweep.
