# Supplementary material

*For "When Is a Call–Put Implied-Volatility Spread Measurable? An
Abstention-Aware Protocol Validated Against a Known Truth". These appendices
are not typeset with the article; they are published online alongside it.*

## Table S1. Certified coverage by strata, development draw

{{supplementary.strata_table}}

*Note: n is the number of attempted pairs in the bucket. Coverage is the share of the bucket the protocol certifies at 0.10 percentage points. MAE is the mean absolute error against the benchmark's defined truth, in percentage points of volatility, computed on the pairs each method can use; a dash means the method certified nothing in that bucket. The rightmost column is the raw midpoint's error on the pairs the protocol declined to certify.*

```{=openxml}
<w:p><w:r></w:r></w:p>
```

## Table S2. The declared settings

| Setting | Value |
|:--|:--|
| Inversion map | European Black–Scholes–Merton, common to both legs |
| Root bracket | decimal IV in [10⁻⁸, 5], bisection, ≤ 64 iterations, no clipping |
| Near-bound guard | prices within 10⁻¹⁰ of a European bound are rejected, not inverted |
| Resolution scale | 1 tick of out-of-the-money-equivalent time value |
| Synchronisation tolerance | 2 s for call–put, call–spot and put–spot lags |
| Tolerance grid | 0.05 / 0.10 / 0.25 percentage points, all reported |
| Primary tolerance | 0.10 percentage points, fixed before any result |
| Sign band | 0.05 percentage points |
| Perturbation set | endpoint widened by half a tick; spot +1 bp; rate +5 bp; spot timestamp −3 s; resolution scale halved to 0.5 tick; synchronisation tolerance relaxed to 5 s |
| Period split | primary = days 0–14, holdout = days 15–29 |
| Inference unit | underlying-day block, 2 000 resamples, seed 20261022 |

*Note: every value was fixed in the pre-registration addendum before the replication sweep was run.*

## Appendix A. The protocol and the instrument in one page

**A.1 Stages.** Contract match → timing check → quote validity → input
validity → midpoint bounds → endpoint inversion → time-value resolution →
finite-shock resolution → tolerance certification.

**A.2 Statuses.** Seven terminal statuses, mutually exclusive, summing to
the attempted count. Reason codes stored separately and never substituted
for a status.

**A.3 Inversion.** European Black–Scholes–Merton for both legs, decimal IV
in [10⁻⁸, 5], bisection with at most 64 iterations, no clipping, near-bound
guard at 10⁻¹⁰.

**A.4 Resolution.** Time value of at least the resolution scale; valid roots
under both declared shocks; a finite endpoint range over the four bid–ask
combinations, one-sided where an endpoint has no root, never imputed.

**A.5 Certification.** The endpoint range of the CPIV is narrower than the
declared tolerance.

**A.6 Inference.** Underlying-day block bootstrap, 2 000 resamples, seed
20261022. The same block device is used for the null in the selection
frontier.

**A.7 Generator.** Two underlyings at spot 100 and 250; 30 trading days
each; maturities of 14, 30 and 60 days; strikes at 90 %, 95 %, 100 %, 105 %
and 110 % of spot; a continuously compounded rate of 5 % and no dividend
yield; base volatility of 22 % with a term slope of +0.12 percentage points
per day and a log-moneyness skew of −1.10; a tick of 0.01, a half-spread of
one tick, one extra tick in the wings and at the short end, doubled on every
seventh session; timestamp jitter of ±0.35 s; and injected defects at
declared rates — stale quotes 1.5 %, crossed quotes 0.8 %, out-of-bounds
quotes 0.5 %, contract mismatches 0.5 % and missing legs 0.4 %. The put leg
is priced on an 800-step binomial lattice, so the truth carries a genuine
early-exercise premium.

## Appendix B. The replication design in one page

**B.1 Seeds.** 23 replication seeds, 20261022 + 7919k for k = 1 … 23, plus
the development draw at k = 0 which is excluded from every tally.

**B.2 Specifications.** 17, one factor at a time from the base market: nine
market specifications, seven protocol specifications and the base itself.

**B.3 Frontier.** 2 000 Monte Carlo trials at each of seven evaluation points
— 0.05, 0.075, 0.10, 0.15, 0.20, 0.25 and 0.50 percentage points — against
a pair null (uniform without replacement) and a day-block null (whole
underlying-days with replacement, partial final block taken at random).
Add-one p-values. That axis contains the protocol tolerance grid of Table S2
plus intermediate points so the curve can be drawn; it is an evaluation
axis, not the grid. The grid itself is 0.05, 0.10 and 0.25 percentage points,
and the 0.50-point evaluation is an additional tolerance specification used
in the sweep (Section 5.3), not part of the grid. Certification and
the reported coverages are governed by the grid alone, and the decision
rules of the pre-registration addendum read the frontier at the primary
tolerance only, 0.10 pp. Table 3 shows the grid points that certify plus two
intermediate points; the other rows are in the released artefact.

**B.4 Tally.** `verdict.py` encodes the six rules of the pre-registration
addendum and reads only the sweep and study outputs.

**B.5 Artefacts.** The run manifests record the configuration, the seed, the
environment and the output hashes of every run reported in the article. The
per-draw sweep outputs, the specification grid and the rule tally are
released as aggregate CSV and JSON files; no market data is included because
none was used.
