# Cover letter — Journal of Computational Finance

> **No addressee and no reviewer suggestions, by instruction.** The letter
> names no one and carries no suggested reviewers, so there is nothing to
> look up and nothing to invent. The signature block comes from the title
> page; "New submission" is from the package README, which records that
> nothing here has been uploaded; the availability statement is drawn from
> the manuscript's Data and code availability section. Written in the first
> person because the paper is single-authored. Delete this note before
> sending.

---

I am pleased to submit my manuscript, **"When Is a Call–Put Implied-Volatility
Spread Measurable? An Abstention-Aware Protocol Validated Against a Known
Truth,"** for consideration in the *Journal of Computational Finance*.
New submission.

## What the paper does

A call–put implied-volatility spread (CPIV) is often reported as a point
estimate from quote midpoints. I argue that in many markets it is not a
measurement at all — it is an artifact of quote width, tick size, maturity and
moneyness — and that the honest output of a measurement procedure is a label,
not a number.

The paper contributes a pre-registered synthetic validation of an
abstention-aware protocol that, for every call–put pair, either certifies a
CPIV at a declared tolerance or declines to answer. Because the generator
defines a true spread before any quote exists, the study reports **accuracy** —
not only coverage and stability — which is the part existing approaches cannot
supply without licensed market data.

## Why I believe it fits the *Journal*

Three features distinguish this from an estimator-improvement paper, and I
believe all three are of interest to a computational readership:

1. **A size-matched null test for abstention rules.** When a procedure reports
   lower error on the subset it chose, the natural objection is that any
   smaller subset would have done as well. I answer this with two nulls — a
   pair null drawn uniformly over the scored universe, and a day-block null
   that preserves within-day dependence — and report the conservative block
   null as primary. The certified subset beat both nulls in all 23 replication
   draws. The method is general: it applies to any selection rule, not only
   to CPIV.

2. **A pre-registered failure, reported as such.** Six decision rules were
   frozen before the replication sweep ran. Five passed. One failed: coverage
   depends strongly on quote microstructure and falls towards zero on
   coarse-tick markets. I report this with the same prominence as the passes,
   because it is the result with the longest reach — a protocol whose coverage
   is a property of the market it meets is not a portable rule with a fixed
   yield, and a practitioner needs to know that before applying it.

3. **Discipline about the protocol's own advantage.** On the common set of
   pairs, the protocol and the raw midpoint are numerically identical. The
   accuracy gain is entirely a selection effect, and I say so explicitly
   rather than leaving it to be discovered.

## Scope and honesty

This paper contains no market data. It supports no claim about coverage, error
or stability in any real market, and it does not license a market statement.
Section 7.2 states the non-claims, and they bind the abstract and the
conclusion. I regard this boundary as a feature: thresholds chosen after the
first look at market data are exactly what pre-registration exists to prevent,
and the protocol here is a computational object that can be exercised — and
falsified — before a licence arrives.

## Availability

This paper contains no market data; every result comes from a synthetic
instrument defined by the generator before any quote exists. The instrument,
the protocol, the replication sweep, the decision-rule tally and the
manuscript build are all implemented in code, and run manifests record the
configuration, the seed, the environment and the output hashes of every run
reported here. The code and the aggregate run artefacts — the study summary,
the per-draw sweep outputs, the specification grid and the rule tally — are
available from the author for review and will be deposited in a public
repository on acceptance. No licensed market data was used, and no result in
the paper depends on a run that has not been carried out.

I am happy to provide any further material the Journal requires.

Sincerely,

Phirawit Jitnarong
[affiliation removed]
[email removed]
