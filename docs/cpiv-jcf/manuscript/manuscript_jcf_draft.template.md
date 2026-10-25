<!--
Anonymised manuscript. The title page is a separate document and the
appendices are separate supplementary material, as the journal requires.
The blocks below follow the journal's compilation order: figure and table
legends, abstract, keywords, key messages, title, main text, declarations,
references.
-->

## Figure and table legends

**Table 1.** Attrition funnel of the development draw, showing the count
surviving each pipeline stage, its share of the attempted pairs and of the
preceding stage, and the dominant rejection reason at that stage.

**Table 2.** Error profile of the raw midpoint, the bound-filtered midpoint,
the identified-but-uncertified set and the certified set against the
benchmark's defined truth, on each method's own set.

**Table 3.** The selection frontier: for each certification tolerance, the
size and coverage of the certified set, its mean absolute error, the error
it abstains from, and the pair-null and day-block-null means with their
add-one p-values.

**Table 4.** The distribution, over the 23 replication draws, of certified
coverage, certified error and raw-midpoint error, reported as median,
interquartile range and full range.

**Table 5.** The pre-registered rule tally over the 23 replication draws,
reporting each of the six rules as passed or failed.

**Table 6.** Certified coverage and certified and raw-midpoint error across
the ten market specifications of the sweep, at the primary tolerance.

**Table 7.** Response of certified coverage, error and mean absolute CPIV
change to each of the six declared perturbations, on the development draw.

**Figure 1.** Two panels: (a) the certified mean absolute error against the
certification tolerance, with the pair-null 5th to 95th percentile band and
the day-block null mean; (b) certified coverage across the ten market
specifications of the sweep.

*Two further tables are supplied as supplementary material: Table S1, the
strata of certified coverage by moneyness, maturity, spread and true
magnitude, and Table S2, the declared settings of the protocol.*

## Abstract
Call–put implied-volatility spreads (CPIV) computed from quote midpoints are
routinely reported as measurements; a midpoint says nothing about whether
the spread is determined by the quotes or by their placement within the
bid–ask spread. This paper describes an abstention-aware protocol that
either certifies a CPIV as identified at a declared tolerance or abstains,
giving
every attempted pair exactly one terminal status so nothing is silently
dropped. The protocol does not re-estimate the spread: where it and the raw
midpoint are both defined they are numerically identical, so every own-set
improvement is a selection effect. The abstention rule is tested against
size-matched random subsets, under a pair null and a day-block null that
preserves within-day dependence. With no licensed quote data available, the
protocol is validated on a synthetic instrument whose true spread is defined
before any quote exists, under a pre-registration frozen beforehand. In the
benchmark the certified subset beats size-matched random subsets in every
draw. One pre-registered rule fails: certification coverage depends strongly
on quote microstructure, falling towards zero on coarse markets. It is a
labelling device whose coverage is a property of the market it meets, not a
rule with a fixed yield.

## Keywords

call–put implied-volatility spread; option-quote measurement;
abstention-aware inference; identification; Black–Scholes–Merton inversion;
numerical validation

## Key messages

- Certified coverage falls towards zero on coarse-quote markets
- Abstention selects a genuinely easier set, not merely a smaller one
- On the common set the protocol is identical to the raw midpoint
- Thresholds were frozen before any replication output was read

# When Is a Call–Put Implied-Volatility Spread Measurable? An Abstention-Aware Protocol Validated Against a Known Truth

---

## 1. Introduction

### 1.1 A number that is not always a measurement
The call–put implied-volatility spread is a natural object to compute from
option market data. For a call and a put on the same underlying with the
same strike and expiry, the two implied volatilities are inverted from their
own quotes under a common pricing map and differenced. The spread is used
as a feature in models of option mispricing (Cremers & Weinbaum, 2010) and
as a diagnostic of the
shape of the volatility surface, and in each use it is treated as a
*quantity* — a number that exists in the data, to be read off and compared
across securities and dates. That treatment is a choice, and not a harmless one. A quote is an interval:
a bid and an ask, separated by a spread that varies with liquidity,
moneyness and maturity (Madhavan, 2000), and carrying a timestamp, and the
midpoint of that interval is a convention, not an observation. That the
spread carries information about informed trading, not merely a liquidity
cost, is the dealer-quote literature's central result (Glosten & Milgrom,
1985); the midpoint discards it. Inverting a midpoint and
differencing two such numbers produces numbers, but neither step says
whether the result is determined by the market or by where the quotes
happened to sit; the error is governed by the width of the two spreads, not
by the surface the analyst believes they are measuring.
The consequence is a common failure. A CPIV table is produced, its
cross-sectional dispersion is studied, and the dispersion is read as a
property of the market. Some of it is. Some of it is the quote
microstructure, amplified by the inversion and re-expressed in volatility
units. The two are not separable afterwards, because the information needed
to separate them was discarded when the midpoint was taken.

### 1.2 What the standard toolkit does and does not do
The measurement literature has a well-developed toolkit for this problem, and
the protocol described here draws on it rather than replacing it. A bound
filter removes pairs whose quotes violate the no-arbitrage relations that
option prices must satisfy (Merton, 1973); such violations are common in
dealer quotes and are informative about the limits to arbitrage rather than
being mere data errors (Figlewski, 1989). A
bound-filtered midpoint replaces the raw midpoint. An endpoint interval
reports the range of CPIV implied by the four bid–ask endpoint
combinations, which is a strictly more honest object than a point. A parity
residual cross-checks the algebra, though one that is algebraically
dependent on the CPIV itself and therefore not an independent validation.
Parity deviations are also studied in their own right, as evidence of
short-sale constraints and segmented markets (Ofek et al., 2004).
Each is a genuine improvement on the raw midpoint, and each is reported here
as a declared baseline.
What none of them does is decline to answer. A bound-filtered midpoint is
still a point estimate of a quantity the quotes may not determine. An
endpoint interval is honest about its own width, but the width is usually
not carried forward. A parity residual checks the algebra, not the
identification of the quantity.

### 1.3 The central claim, and its awkward consequence
The protocol produces a CPIV by taking the midpoint of the same interval the
raw baseline takes the midpoint of. It does not improve the estimator. It
labels pairs.

That has a consequence that is easy to state and easy to avoid stating: on
the set of pairs where the protocol certifies a value and the raw midpoint
also produces one, the two values are *numerically identical*. Every
difference in error between the two methods on that set is exactly zero, by
construction, and not because the two methods happen to agree.

It follows that any apparent improvement the protocol delivers is delivered
by *selection*: by declining to report certain pairs. A reported subset of
the pairs that are actually identified is more useful than a reported set
that silently includes pairs that are not, but an improvement delivered by
selection is not the same kind of claim as an improvement delivered by a
better estimator, and a reader is entitled to know which is on offer: an
effect estimated on the treated group is not an estimate of the effect of
treatment, and the comparison must be made against the right counterfactual
(Imbens & Rubin, 2015).

So the protocol's own-set advantage is stated as what it is — a selection
effect — and the substantive question becomes: *is the certified subset
genuinely easier to measure than an arbitrary subset of the same size?* If
it is, the abstention rule is doing something real. If it is not, the
protocol is discarding hard pairs and paying for the privilege in coverage.
Answering that requires a counterfactual that respects the dependence in the
data, and this paper constructs two size-matched nulls for each tolerance.

### 1.4 Why the validation is synthetic
The obvious way to answer the previous question is with real quotes. That is
not currently possible, and the reason is not a matter of taste or effort.
No licensed product covering the required data was available at the time of
writing, and the data gate for this project is deliberately closed: no
market-data path will run without a written licence record permitting
publication of the aggregate outputs, and the enquiry letters to
the two candidate vendors have been sent, with no licence granted yet. Options market data is not freely
redistributable, and tables derived from quote data one may not redistribute
cannot be published.
The alternative taken here is to make the *method* the object of validation
and to give the method a test a real market could not have provided. A
synthetic market can be constructed in which the true call–put implied
volatility spread is defined *before* any quote exists. The generator draws
fair values, inverts them under the same map the protocol uses, and thereby
knows the truth; only then does it round to a tick, add a spread, jitter the
timestamps and inject defects. In a real market the protocol can be assessed
for coverage and stability, but never for accuracy, because the truth is
unknown; in the benchmark it can be assessed for all three.
This is not a substitute for the licensed run, and the paper does not
present it as one. It supports a narrower claim: that the measurement
machinery behaves as specified. Section 7.2 states the non-claims, and they
bind the abstract and the conclusion.

### 1.5 Contributions
1. **An abstention-aware measurement protocol with a closed status
   taxonomy.** Declining to answer a question the data cannot support, and
   reporting that refusal, is the optimum reject rule of the
   pattern-recognition literature (Chow, 1970) applied to measurement.
   Every attempted quote pair receives exactly one terminal status,
   the counts are reconciled against the attempted total, and a residual fails
   the run. Nothing can be dropped silently.
2. **A size-matched null test for an abstention rule.** A pair null drawn
   uniformly over the scored universe and a day-block null that preserves the
   within-day dependence the study's own intervals respect; the block null is
   the conservative test and is reported as primary.
3. **A discipline for reporting the protocol's own advantage.** The paper
   reports the identity that the protocol and the raw midpoint coincide on the
   common set, and requires every own-set comparison to carry the frontier
   p-values that say whether the selected set beats an arbitrary set of the
   same size.
4. **A pre-registered synthetic ground-truth benchmark with a rule tally in
   which one rule fails.** The generator, settings, seeds, specification grid,
   null construction and decision rules were fixed in a pre-registration
   addendum written before the replication sweep was run, and the tally reports
   which rules passed and which did not, with the same prominence.

## 2. The measurement problem

### 2.1 What a CPIV is made of
Let *C* and *P* denote a call and a put on the same underlying, with the
same strike *K*, expiry *T*, exercise style and contract terms, quoted at a
common time. Write *σ_C* and *σ_P* for the implied volatilities recovered
from the two quotes under a common pricing map, and CPIV = 100 × (σ_C − σ_P)
in percentage points of volatility. For a European pair under the
Black–Scholes–Merton map (Black & Scholes, 1973), both legs are determined
by the same five inputs — spot, strike, maturity, rate and dividend yield —
so *σ_C* and *σ_P* are two noisy readings of the same object, and their
difference measures the *inconsistency* of the two quotes with the model.
Two features matter for what follows. First, the difference is a difference
of inverted quantities, so an error in either leg is amplified by the
inverse of that leg's vega. Second, because both legs are inverted from
intervals rather than points, the CPIV inherits the width of both quote
intervals. Write the two half-spreads in price units as *h_C* and *h_P* and
the two vegas as *v_C* and *v_P*; to first order the CPIV is uncertain by an
amount of the order of 100 × (h_C / v_C + h_P / v_P). A wing option, with a
small vega and a wide spread, contributes a large and roughly constant
uncertainty to the CPIV regardless of the true value. This is the mechanism
behind most of the dispersion in a CPIV table, and it is why that dispersion
is not interpretable as a market quantity.

### 2.2 Identification is not estimation
Two activities are kept separate throughout. *Estimation* is recovering a
value well, given that a value exists. *Identification* is establishing
that a value exists at all, given the data. The raw midpoint pipeline
performs an estimation and silently assumes identification. A midpoint of a
bid and an ask, inverted and differenced, is a well-defined number; nothing
in the operation establishes that the number is close to anything.
The two can come apart badly. Consider a deep out-of-the-money put whose
time value is a few ticks wide but whose vega is tiny. The midpoint of that
put's interval can be inverted to a volatility that is off by a large
relative amount, because the inversion divides a small price error by a
small vega. The resulting CPIV is dominated by the error of the leg that
cannot be measured, and it is reported with the same confidence as every
other number in the table.
The classical response is to declare in advance what would count as a
successful measurement, and to report a null result where the criterion is
not met. That is the structure adopted here: the protocol answers "is this
pair's CPIV identified at tolerance *t*?" for each pair, in a way a
downstream user cannot mistake for a measurement.

### 2.3 The two objects a protocol could produce
A protocol can produce a *second estimator*: a different way of computing
the CPIV, expected to be closer to the truth, whose common-set difference
would be non-trivial and whose fall in common-set error would be evidence
about the estimator.
Or it can produce a *labelling device*: a rule that selects a subset and
declines to speak about the rest, whose output on the selected subset is
whatever the original estimator would have produced there. The common-set
difference is exactly zero, and any advantage is a function of which pairs
were selected.
The protocol here is of the second kind. The problem is not "the midpoint is
the wrong number" but "the midpoint is a number about which nothing can be
asserted without knowing whether it is determined". Its advantage must
therefore be tested against a counterfactual, because the common-set
comparison is vacuous by construction (Section 2.5).

### 2.4 Declared baselines and the comparison that matters
Five baselines are declared in the pre-registration, and each is reported:
the raw midpoint CPIV, with no filter beyond the existence of a finite root;
the bound-filtered midpoint CPIV; the bid–ask endpoint interval, reported as
an interval rather than a point; the parity residual, labelled throughout as
algebraically dependent on the CPIV and so not an independent validation;
and the abstention-aware protocol itself, with its certified subset, its
abstentions and its funnel.
The comparison the paper is built around is between the fifth and the first,
reported in two forms that must not be confused. On the **own set**, each
method is evaluated on the pairs it can use: the protocol's own set is small
and accurate, the raw midpoint's is large and inaccurate, and the difference
is the selection effect. On the **common set**, both are evaluated on the
pairs they can both use, the values are identical, and the difference is
exactly zero — reported as exactly zero rather than as a small number.

### 2.5 The counterfactual: size-matched random subsets
Suppose the protocol certifies *k* of the *n* scored pairs. Its own-set mean
absolute error is the mean absolute error of those *k* pairs. The natural
null is the distribution of that statistic over subsets of size *k* drawn at
random from the same *n* pairs. Two nulls are constructed, and the
difference between them is the point.
The **pair null** draws *k* pairs uniformly without replacement from the
scored universe. It asks whether the certified set is better than a random
selection of the same size, if selections were independent of everything. It
is the natural null, and the one most likely to favour the protocol,
because it ignores that pairs from the same underlying-day are not
independent.
The **day-block null** draws whole underlying-days with replacement until
*k* pairs have been selected, so every draw respects the within-day
dependence of the quotes. It asks the harder question: is the certified set
better than a random selection that respects the same dependence structure
the study's own confidence intervals respect? A protocol that beats a pair
null but not a day-block null has selected a set whose advantage comes from
its correlation with the day's overall quote quality rather than from its
own per-pair criteria.
Both nulls are Monte Carlo with a declared seed and a declared number of
trials. The null distribution is a bootstrap distribution in the sense of
Efron and Tibshirani (1993), the day-block draw is a block resampling
scheme for dependent data of the kind developed by Politis and Romano
(1994), and the reported p-value is the add-one estimator (Davison &
Hinkley, 1997). The
day-block null is the primary test, because it is the conservative one and
because the block resampling is the same device used for the study's own
confidence intervals.
One implementation detail matters, and is stated because it affects the
result. A block draw must match the certified subset exactly in size, so the
final block of a draw may be taken in part, its members chosen at random.
Taking them systematically — always the first *m* members, say — would bias
the null towards the earliest pairs of a day, which are not exchangeable
with the rest, and would make the null artificially easy to beat.

### 2.6 What the microstructure does to the coverage
The protocol's coverage — the share of attempted pairs it certifies — is a
property of the protocol *and* of the market it meets. Two rules control it
directly. The resolution scale requires the option's out-of-the-money-
equivalent time value to exceed a declared multiple of the tick before the
pair is treated as resolvable at all; the tolerance requires the endpoint
interval of the CPIV to be narrower than the declared tolerance.
Both interact with microstructure in a way that is not a matter of degree.
If the tick is coarse relative to the time value of a wing option, the
resolution rule abstains on that option whatever the tolerance. If the
quotes are wide, the endpoint interval is wide, and the tolerance rule
abstains on nearly everything. A protocol that certifies a small,
well-identified fraction of a liquid market may certify almost nothing of an
illiquid or coarsely quoted one, and a reader who carries a coverage figure
from one market to another will be wrong.

## 3. The protocol

### 3.1 Pair construction
An observation is a matched call–put pair. Two quotes are a pair only when
they agree on underlying, strike, expiry, multiplier, exercise style and
settlement convention; a disagreement in any of these fields is recorded as
a contract mismatch, with the offending field named, and the pair is
excluded from measurement without being dropped from the denominator.
Each quote carries a timestamp, and each pair carries three lags: the
call–put lag, the call–spot lag and the put–spot lag. A pair whose lags
exceed the declared synchronisation tolerance is a timing mismatch, and the
lags are retained on the record so the exclusion can be audited rather than
trusted.
The spot used for inversion is the underlying's own quote at its own
timestamp, not a last-traded price or a value carried forward. This rules
out end-of-day files, which give every option the same snapshot and make the
timing stage vacuous.

### 3.2 The inversion contract
Both legs are inverted under the same European Black–Scholes–Merton map
(Black & Scholes, 1973; Merton, 1973), whose state-contingent foundation is
due to Breeden and Litzenberger (1978), with a single declared contract:

* the root bracket is decimal implied volatility in [10⁻⁸, 5];
* the solver is bisection, with at most 64 iterations;
* no price is ever clipped to a bracket, and no root is reported from
   outside it;
* a non-finite or negative price is rejected;
* a price within 10⁻¹⁰ of a European bound is rejected rather than inverted;
* the failure classes are named — invalid input, theoretical-bound
   violation, near-bound guard, outside bracket, numerical — and recorded per
   leg.
The rejection of near-bound prices deserves a note. The classical
approximation that the CPIV is the parity residual divided by the vega is
first-order accurate in the no-arbitrage interior (Hentschel, 2003, analyzes
the implied-volatility error that a price error induces directly); near the
boundary vega approaches zero and the error amplifies without bound. Prices
*on* the bound are therefore precisely those for which the local
approximation is uninformative.
The map is European because it is the map common to both legs, and because
it is the map under which the synthetic truth is defined. Where the
underlying option is American — the case for most listed equity options —
the European map is an approximation for both legs, and the approximation
error is common to the two legs to first order and largely cancels in the
difference. Section 3.6 describes how the American exercise premium is
handled.

### 3.3 The resolution rules
Certification is not a single test. Three rules must all be satisfied, and
each is a rule about whether the *market* says something rather than about
whether the *model* fits.
**The time-value rule.** The out-of-the-money-equivalent time value of each
leg is computed and compared with the declared resolution scale, one tick by
default. The rule separates "the option is too cheap to say anything about"
from "the option says something, and the inversion recovers it".
**The finite-shock rule.** A declared positive shock and a declared negative
shock are applied to the underlying, and the pair must produce valid roots
under both. A pair producing a root under only one sign of shock has not
been shown to be locally invertible, and is treated as unresolved.
**The endpoint rule.** The CPIV implied by the four combinations of bid and
ask endpoints is computed: the lowest from the call bid against the put ask,
the highest from the call ask against the put bid. If an endpoint has no
finite root, the range becomes one-sided and the pair becomes partially
resolved. No endpoint is imputed and no missing endpoint is interpolated.
The fourth rule is the tolerance rule, and it is what makes the abstention
decision rather than merely a resolution decision. The pair is *certified*
when the endpoint range of the CPIV is narrower than the declared tolerance,
*identified but outside tolerance* when the range is finite but wider, and
*unresolved* when the range cannot be formed. A pair identified outside the
tolerance still has a number; the protocol declines to certify that it is
determined to the standard asked for.

### 3.4 The status taxonomy and the reconciliation invariant
Every attempted pair ends in exactly one of seven terminal statuses:
`RESOLVED_WITHIN_TOLERANCE`, `IDENTIFIED_OUTSIDE_TOLERANCE`,
`PARTIALLY_RESOLVED`, `UNRESOLVED`, `INVALID_INPUT`, `TIMING_MISMATCH` and
`CONTRACT_MISMATCH`. Reason codes are stored separately from the terminal
status, so that a diagnostic can never stand in for a status. A terminal
status that contradicts the stage at which the pair failed is a
reconciliation error, and the run fails rather than continuing.
The reconciliation invariant is that the terminal counts sum to the
attempted count, and that each stage's count equals the sum of the terminal
statuses downstream of it. A residual — a pair that entered the pipeline and
left no trace — fails the run. The funnel reports, for every stage, the
count, the share of attempted pairs, the share of the prior stage, and the
dominant rejection reason. Dropping a pair reports coverage conditional on the survivors, and the
survivorship depends on upstream decisions invisible in the final number; a
terminal status for everything gives coverage an unambiguous denominator and
a funnel that says where the pairs went.

### 3.5 Certification and abstention
A pair is certified when all three resolution rules are satisfied and the
endpoint range of the CPIV is narrower than the tolerance. The certified set
is what the protocol reports.
The abstained set is everything else, and it is not empty by construction. In
the development draw of the benchmark,
{{study.terminal.resolved_within_tolerance}} of {{study.attempted}}
attempted pairs were certified, and
{{study.terminal.identified_outside_tolerance}} were identified but outside
the tolerance, with the remainder split across partially resolved, invalid
input, timing mismatch and contract mismatch.
The abstention rate is not a cost to be minimised. It is the price of the
claim being made, and the paper's secondary outcome (Section 6.9) puts a
number on what that price buys in the one place a downstream user needs a
*set* rather than a *number*: the calibration of a volatility surface.

### 3.6 Handling the American exercise premium
Most listed equity options are American, and the European inversion map
ignores the early-exercise premium the put leg carries. If that premium is
material, the two legs are being inverted under a model that is wrong for
one of them, and the resulting CPIV is contaminated.

Two facts limit the damage. The premium is a *common* function of the
underlying's parameters and the contract's moneyness and maturity, so it
does not vary arbitrarily across the strike grid, and a surface fitted to a
contaminated set is biased in a structured rather than a random way. And
its magnitude is small relative to the uncertainty contributed by the quote
spread, for most of the parameter range in which the protocol certifies
anything at all.

The benchmark makes this explicit rather than assuming it away. The
synthetic put leg is genuinely American, priced by an 800-step binomial
lattice (Cox et al., 1979) rather than by a simulation-based American
pricer (Longstaff & Schwartz, 2001), because the premium has to be exact for
the truth to be exact. The call leg is worth exactly its
European value because it carries no early-exercise premium without a
dividend. The true CPIV is therefore non-zero by construction — it is the
volatility-equivalent of the exercise premium — and the protocol's certified
values recover it, with a median absolute error of
{{study.error.protocol_certified.median}} percentage points in the
development draw (Section 6.2).

The alternative treatment, an American fallback for the put leg, is
available and is a protocol change under the pre-registration rather than an
extension of the results. It is not adopted here, because the licensed run
has not fixed the exercise-style convention that would trigger it.

### 3.7 The calibration input set
The protocol's abstention removes pairs from any downstream use that needs a
*set* of CPIV values, most obviously the calibration of a volatility
surface. To make the cost of abstention concrete, one secondary outcome is
declared in advance.
At the primary tolerance, the paper counts how many contracts remain
available to a surface calibration under the raw-midpoint input set and
under the protocol input set, and reports how the fitted surfaces differ.
The fit is a quadratic in log-moneyness, per expiry slice, on the CPIV
surface. The comparison is descriptive: the paper does not claim that either
surface is better specified, better behaved or more profitable. This outcome
was adopted before the freeze as the bridge to the journal's computational
focus: the one place where the protocol's behaviour has a consequence for a
downstream numerical procedure.

## 4. A synthetic instrument with a known truth

### 4.1 What a synthetic market can say that a real one cannot
The advantage of the synthetic instrument is that the truth is defined
before the quote exists, and the paper states what that means and what it
does not.
The generator draws, for each underlying and each trading day, a set of
contracts at declared strikes and maturities. For each contract it computes
the *unrounded fair value* of both legs, inverts those fair values under
the same European map the protocol uses, and takes the difference as the
true CPIV. Only after the truth has been fixed does it produce the
observable quote: the fair value is rounded to a tick, a half-spread is
added, the timestamp is jittered, and defects are injected at declared
rates.
The truth is therefore a property of the model, not of a market: it is the
quantity a perfect measurement of this synthetic market would recover. The
instrument can report *accuracy*, which a real market never can, and it can
probe conditions that are hard to find in real data — wide quotes, coarse
ticks, short maturities, a timing skew — because those can be dialled in
exactly. What it cannot do is support a claim about any real security, index
or option (Section 7.2).

### 4.2 The generator
The base specification, frozen in the pre-registration, is listed in
Supplementary Appendix A. In outline: two underlyings at spot 100 and 250,
30 trading days each, maturities of 14, 30 and 60 days, five strikes from
90 % to 110 % of spot, a continuously compounded rate of 5 % with no
dividend yield, a volatility surface with a term slope and a
log-moneyness skew, a tick of 0.01 and a half-spread that widens in the
wings, at the short end and on every seventh session, sub-second timestamp
jitter, and injected defects at declared rates.
This yields {{study.attempted}} attempted pairs in the development draw, of
which {{study.defect.none}} carried no defect: {{study.defect.stale_quote}}
stale quotes, {{study.defect.crossed_quote}} crossed quotes,
{{study.defect.out_of_bounds_quote}} out-of-bounds quotes and
{{study.defect.contract_mismatch}} contract mismatches, one defect per
remaining pair. The {{study.defect.missing_leg}} contracts with a missing
leg never become pairs and are not among the {{study.attempted}}.
The generator is a pure function of its seed and configuration: the same
seed reproduces the same quotes, pair identifiers and truth values, which is
what makes the replication design of Section 5.3 possible at all.

### 4.3 The truth
The true CPIV is negative for a structural reason: the American put is worth
more than its European value, so the implied volatility recovered from it is
*higher* than that recovered from the call, and the difference is negative.
In the development draw the true spread ranges from {{truth.min}} to
{{truth.max}} percentage points with a median of {{truth.median}}, and it is
defined for all {{truth.n_defined}} attempted pairs.
The magnitude matters. A true spread of a few tenths of a percentage point,
against a quote-induced uncertainty of the same order, is the regime in
which the measurement problem is genuinely hard: signal and noise are the
same size. It is also the regime in which a protocol that reports a number
without saying whether the number is determined is most likely to mislead.

### 4.4 What the instrument is not
The synthetic instrument is a *model artefact*, and three things follow.
It does not license an external-validity claim. A protocol that behaves well
on this instrument may behave differently on a real market, for the reasons
in Section 2.6: coverage is determined by the microstructure of the market
it meets, and the instrument's microstructure is one this study chose.
It does not license a market claim of any kind; Section 7.2 lists the
excluded claims.
It does not license a claim about the optimal tolerance: the specification
sweep varies the tolerance on a synthetic market, which says nothing about
which tolerance an analyst should use on a real one.

## 5. Design and pre-registration

### 5.1 The status of the pre-registration
The project's main pre-registration cannot be frozen, because the data gate
is closed and the universe, the sampling rule and the tick convention all
depend on a vendor's schema that does not yet exist. What *can* be frozen
without a licence is everything about the protocol and the instrument, and
that is what a separate addendum freezes: the generator specification, the
protocol settings, the seed list, the specification grid, the nulls, the
number of trials and the decision rules.
The addendum was written before the replication sweep was run. The one
base-market study that had already been run at that point is declared as the
*development draw*, is reported in full for transparency, and is excluded
from every tally in Section 6.6. The replication seeds were run after the
addendum was written and before any of their outputs was read.
The rules are evaluated by code, not by hand. `verdict.py` encodes the six
rules and reads only the sweep outputs; the tally in Section 6.6 is its
output. A code defect may be fixed after the freeze; a change to a rule, a
seed, a specification or a threshold may not, since that would require a new
addendum version, a fresh sweep and a new tally. This is the discipline the
pre-registration literature argues for in its general form (White, 2000;
Harvey et al., 2016; Nosek et al., 2018), applied at the level of a single
study.

### 5.2 The declared settings
Every setting the protocol uses is a declared quantity, frozen in the
addendum and listed in Supplementary Table S2: the inversion map, the root
bracket, the near-bound guard, the resolution scale, the synchronisation
tolerance, the tolerance grid and primary tolerance, the sign band, the
perturbation set, the period split and the inference unit. No setting is a
free parameter of the analysis.

The inference unit deserves a note. Options on the same underlying and day
share a spot, a session volatility and a set of market-maker quotes, so
treating pairs as independent would understate the uncertainty and would
make the nulls of Section 2.5 too easy to beat. All intervals are therefore
computed by resampling whole underlying-days, and the day-block null is the
primary test.

### 5.3 The replication design
A single draw is one number, and one number cannot support a claim about a
protocol. The design has two arms.
The **seed sweep** repeats the entire study — a fresh market, a fresh
protocol run, a fresh frontier — on 23 declared replication seeds, each a
complete re-draw of the instrument. The seeds are a base seed plus a fixed
stride, so the set is reproducible and cannot be adjusted after the fact.
Each draw reports the same quantities, so the results are read as
distributions rather than point estimates.
The **specification sweep** varies the instrument and the protocol one
factor at a time away from the base market. The market group varies
volatility (low 15 %, high 35 %), quote width (two and three ticks), tick
size (0.05), the wide-session period (removed), the strike grid (85 % to 115
%) and the maturities (7/14/30 days and 30/60/90 days). The protocol group
varies the analyst's own knobs — the tolerance at 0.05, 0.10, 0.25 and 0.50
percentage points (sweep specifications, not the grid), and the resolution
scale at 0.5, 1 and 2 ticks — which maps the coverage–error frontier an
analyst actually faces. The seed sweep asks whether the quantities are a property of the protocol or
of one lucky draw; the market group, whether they are a property of the
protocol or of one synthetic market.

### 5.4 The perturbation set
Six perturbations are declared, each a plausible accident of a real feed
rather than an arbitrary stress: every quote widened by half a tick; the
spot used for inversion shifted up by one basis point; the continuously
compounded rate shifted up by five basis points; the underlying's timestamp
moved three seconds behind the quotes; the resolution scale halved; and the
synchronisation tolerance relaxed to five seconds. Table 7 reports the
response of each, and Section 6.7 says what it means.
The perturbations are diagnostics rather than confidence bounds. They answer
"which parts of the result are load-bearing?", and the answer determines
which components a reader should trust.

### 5.5 The decision rules
Six rules were declared, each a statement the benchmark can falsify.

| Rule | Statement | Pass condition on the replication seeds |
|:--|:--|:--|
| R1 — selection | The abstention rule selects a set that is genuinely easier to measure, not merely smaller. | Certified error below the day-block null mean in ≥ 16 of 23 draws, and day-block p < 0.05 in ≥ 16 of 23 |
| R2 — own-set accuracy | The protocol's own-set error is lower than the raw midpoint's own-set error. | Own-set MAE(certified) < own-set MAE(raw) in ≥ 16 of 23 draws |
| R3 — coverage stability | The certification coverage does not depend on one particular synthetic market. | Across the 10 market specifications, the minimum certified coverage at the primary tolerance is ≥ 50 % of the median coverage |
| R4 — tolerance monotonicity | Coverage is non-decreasing in the certification tolerance. | Holds in ≥ 22 of 23 draws |
| R5 — period agreement | The primary and holdout periods agree. | Sign of the error reduction agrees in ≥ 16 of 23 draws, and holdout coverage is within 10 percentage points of primary coverage in ≥ 16 of 23 |
| R6 — perturbation sanity | The perturbation set does not dominate the result. | No single perturbation changes certified coverage by more than 15 percentage points in absolute value |
Two features of the rules are worth stating. The thresholds are counts of
draws, not effect sizes, so the rules are about *consistency* rather than
magnitude: a rule passes when the phenomenon is present in most independent
re-draws. And R1 and R2 carry a declared consequence. If either fails, the
benchmark shows that abstaining on hard pairs does not buy accuracy, and the
paper's central mechanism claim must be reduced to coverage and stability
only. That reduction would bind the abstract, the key messages and the
conclusion, and could not be renegotiated afterwards.

---

## 6. Results

### 6.1 The funnel
The funnel of the development draw (Table 1) is the first result, because it
establishes what the protocol is actually rejecting.

**Table 1. Attrition funnel, development draw (seed 20261022)**

| Stage | Count | Share of attempted | Share of prior stage | Dominant rejection reason |
|:--|--:|--:|--:|:--|
| Contract | {{study.funnel.contract.count}} | {{study.funnel.contract.share_attempted}} % | {{study.funnel.contract.share_prior}} % | — |
| Timing | {{study.funnel.timing.count}} | {{study.funnel.timing.share_attempted}} % | {{study.funnel.timing.share_prior}} % | — |
| Quote | {{study.funnel.quote.count}} | {{study.funnel.quote.share_attempted}} % | {{study.funnel.quote.share_prior}} % | quote invalid |
| Input | {{study.funnel.input.count}} | {{study.funnel.input.share_attempted}} % | {{study.funnel.input.share_prior}} % | — |
| Midpoint | {{study.funnel.midpoint.count}} | {{study.funnel.midpoint.share_attempted}} % | {{study.funnel.midpoint.share_prior}} % | theoretical bound violation |
| Endpoint | {{study.funnel.endpoint.count}} | {{study.funnel.endpoint.share_attempted}} % | {{study.funnel.endpoint.share_prior}} % | endpoint incomplete |
| Time value | {{study.funnel.time_value.count}} | {{study.funnel.time_value.share_attempted}} % | {{study.funnel.time_value.share_prior}} % | — |
| Finite shock | {{study.funnel.finite_shock.count}} | {{study.funnel.finite_shock.share_attempted}} % | {{study.funnel.finite_shock.share_prior}} % | — |
| Tolerance | {{study.funnel.tolerance.count}} | {{study.funnel.tolerance.share_attempted}} % | {{study.funnel.tolerance.share_prior}} % | — |

*Note: shares are percentages of the attempted total and of the preceding stage. The terminal statuses reconcile to the attempted total of {{study.attempted}} pairs.*

The **endpoint** stage is where the largest single loss occurs, from
{{study.funnel.midpoint.count}} pairs to {{study.funnel.endpoint.count}},
and the dominant reason is an incomplete endpoint. This is the stage at
which the market's own price granularity runs out: an endpoint combination
that asks the inversion for a root on the far side of the no-arbitrage
boundary has no root, and the protocol does not impute one. The
**tolerance** stage removes nothing and separates what it receives: of the
{{study.tolerance.identified_total}} resolvable pairs,
{{study.tolerance.certified}} are certified at the primary tolerance and
{{study.tolerance.outside}} are identified but not certified. Abstention is
therefore {{study.tolerance.outside}} pairs held back by the tolerance,
{{study.terminal.partially_resolved}} lost to an incomplete endpoint, and
{{study.abstained.earlier}} lost to a contract, timing or input defect:
{{study.abstained.total}} of {{study.attempted}} attempted pairs, or
{{study.abstained.share}} %.
The terminal statuses reconcile as
{{study.terminal.resolved_within_tolerance}} resolved within tolerance,
{{study.terminal.identified_outside_tolerance}} identified outside
tolerance, {{study.terminal.partially_resolved}} partially resolved,
{{study.terminal.unresolved}} unresolved,
{{study.terminal.invalid_input}} invalid input,
{{study.terminal.timing_mismatch}} timing mismatch and
{{study.terminal.contract_mismatch}} contract mismatch, summing to the
{{study.attempted}} attempted pairs.

### 6.2 Accuracy, and the error profile
The protocol's advantage in the development draw is large, and it is
important to be clear about what kind of advantage it is. The raw midpoint
achieves a mean absolute error of {{study.error.raw_midpoint.mae}}
percentage points over {{study.error.raw_midpoint.n}} scored pairs; the
protocol's certified subset achieves {{study.error.protocol_certified.mae}}
over {{study.error.protocol_certified.n}} pairs, a factor of
{{study.error.raw_over_certified}} in the benchmark, computed from
unrounded values.
That number is a *selection* number. On the common set of
{{study.own.protocol_certified.n}} pairs the two methods are numerically
identical and the difference in mean absolute error is exactly zero. The
informative comparison is therefore not the one a reader will instinctively
make, and Section 6.4 makes it.
The error profile in Table 2 shows the shape the mean hides. The raw
midpoint's median absolute error is
{{study.error.raw_midpoint.median}} percentage points, so its mean of
{{study.error.raw_midpoint.mae}} is carried by a tail: a minority of pairs
have errors an order of magnitude larger than the typical pair, and they are
exactly the pairs a reader would most want to interrogate. The share of
raw-midpoint pairs inside 0.10 percentage points
is {{study.error.raw_midpoint.within_0.10}} %, against
{{study.error.protocol_certified.within_0.10}} % for the certified subset,
whose maximum absolute error is {{study.error.protocol_certified.max}}. The
tail is not noise smeared around an estimate; it is a set of pairs where the
midpoint is simply not a measurement, and no downstream consumer can tell
which those are.
The identified set, at
{{study.own.protocol_identified.n}} pairs, sits between the two: its mean
absolute error is {{study.error.protocol_identified.mae}}, and its share
inside 0.10 percentage points is
{{study.error.protocol_identified.within_0.10}} %. The protocol produces a
graded statement — certified, identified but imprecise, unresolved — rather
than a binary one, and the grading is informative.

**Table 2. Error profile in the benchmark, development draw**

| Method | n | Mean abs. error | Median | p90 | p95 | Max | Within 0.10 pp |
|:--|--:|--:|--:|--:|--:|--:|--:|
| Raw midpoint | {{study.error.raw_midpoint.n}} | {{study.error.raw_midpoint.mae}} | {{study.error.raw_midpoint.median}} | {{study.error.raw_midpoint.p90}} | {{study.error.raw_midpoint.p95}} | {{study.error.raw_midpoint.max}} | {{study.error.raw_midpoint.within_0.10}} % |
| Bound-filtered | {{study.error.bound_filtered.n}} | {{study.error.bound_filtered.mae}} | {{study.error.bound_filtered.median}} | {{study.error.bound_filtered.p90}} | {{study.error.bound_filtered.p95}} | {{study.error.bound_filtered.max}} | {{study.error.bound_filtered.within_0.10}} % |
| Identified | {{study.error.protocol_identified.n}} | {{study.error.protocol_identified.mae}} | {{study.error.protocol_identified.median}} | {{study.error.protocol_identified.p90}} | {{study.error.protocol_identified.p95}} | {{study.error.protocol_identified.max}} | {{study.error.protocol_identified.within_0.10}} % |
| Certified | {{study.error.protocol_certified.n}} | {{study.error.protocol_certified.mae}} | {{study.error.protocol_certified.median}} | {{study.error.protocol_certified.p90}} | {{study.error.protocol_certified.p95}} | {{study.error.protocol_certified.max}} | {{study.error.protocol_certified.within_0.10}} % |

*Note: all errors are absolute errors in percentage points of volatility against the benchmark's defined truth, on each method's own set. The bound-filtered baseline is numerically identical to the raw midpoint in this draw, because the bound filter removed no pair the raw midpoint could otherwise have used.*

### 6.3 Coverage
The coverage of certification in the development draw is
{{study.coverage.0_10.attempted}} % of attempted pairs at the primary
tolerance of 0.10 percentage points, which is
{{study.coverage.0_10.resolved}} pairs. At the tighter tolerance of 0.05
percentage points the coverage is {{study.coverage.0_05.attempted}} % and no
pair at all is certified; at the looser tolerance of 0.25 percentage points
it is {{study.coverage.0_25.attempted}} %, or
{{study.coverage.0_25.resolved}} pairs.

A coverage of zero at the tightest tolerance is not a degenerate case: the
benchmark's quote widths and its true spread are of comparable size, so the
0.05 pp standard is beyond what the quotes support for essentially every
pair. A practitioner who demands a tighter standard than the market supports
should receive nothing, and does.

The error avoided by abstention — the raw-midpoint error on the pairs the
protocol declined to certify — is
{{study.inference.error_avoided_by_abstention_pp.estimate}} percentage
points in the development draw, with interval
[{{study.inference.error_avoided_by_abstention_pp.ci_low}},
{{study.inference.error_avoided_by_abstention_pp.ci_high}}]. This is the
price of the abstention expressed as an error rather than a coverage: the
protocol declines to certify the pairs that would have been wrong by close
to six tenths of a percentage point on average.

### 6.4 The selection frontier
The frontier (Table 3) is the paper's central result, because it is the only
result that speaks to the question the protocol poses.
At the primary tolerance of 0.10 percentage points, the certified subset in
the development draw has a mean absolute error of
{{study.frontier.0_10.mae}} percentage points, while a pair-null draw of
the same size has a mean of {{study.frontier.0_10.null_mean}} and a
day-block null a mean of {{study.frontier.0_10.block_null_mean}}. The
certified set is far below both nulls, and the add-one p-values are
{{study.frontier.0_10.p_pair}} against the pair null and
{{study.frontier.0_10.p_block}} against the day-block null.

**Table 3. The selection frontier in the benchmark, development draw**

| Tolerance (pp) | Certified | Coverage | MAE certified | MAE abstained | Pair null mean | Block null mean | p (pair) | p (block) |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 0.075 | {{study.frontier.0_075.n}} | {{study.frontier.0_075.coverage}} % | {{study.frontier.0_075.mae}} | {{study.frontier.0_075.abstained_mae}} | {{study.frontier.0_075.null_mean}} | {{study.frontier.0_075.block_null_mean}} | {{study.frontier.0_075.p_pair}} | {{study.frontier.0_075.p_block}} |
| 0.10 | {{study.frontier.0_10.n}} | {{study.frontier.0_10.coverage}} % | {{study.frontier.0_10.mae}} | {{study.frontier.0_10.abstained_mae}} | {{study.frontier.0_10.null_mean}} | {{study.frontier.0_10.block_null_mean}} | {{study.frontier.0_10.p_pair}} | {{study.frontier.0_10.p_block}} |
| 0.15 | {{study.frontier.0_15.n}} | {{study.frontier.0_15.coverage}} % | {{study.frontier.0_15.mae}} | {{study.frontier.0_15.abstained_mae}} | {{study.frontier.0_15.null_mean}} | {{study.frontier.0_15.block_null_mean}} | {{study.frontier.0_15.p_pair}} | {{study.frontier.0_15.p_block}} |
| 0.25 | {{study.frontier.0_25.n}} | {{study.frontier.0_25.coverage}} % | {{study.frontier.0_25.mae}} | {{study.frontier.0_25.abstained_mae}} | {{study.frontier.0_25.null_mean}} | {{study.frontier.0_25.block_null_mean}} | {{study.frontier.0_25.p_pair}} | {{study.frontier.0_25.p_block}} |

*Note: each null draws a subset of exactly the certified size from the same scored universe, over {{sweep.frontier_trials}} Monte Carlo trials. The day-block null draws whole underlying-days with replacement. The p-values are add-one estimates. The 0.05 pp row is omitted because no pair is certified at that tolerance in this draw. Coverage is the scored-universe share; Section 6.3 reports the share of attempted. The rows are grid points plus two intermediate points of the seven-point axis in Supplementary B.3.*

![**Figure 1.** (a) Certified mean absolute error against the certification
tolerance, with the pair-null 5th to 95th percentile band and the day-block
null mean, on a log scale; the nulls sit three orders of magnitude above the
certified error. (b) Certified coverage across the ten market specifications
at the primary tolerance. Benchmark only; development draw
throughout.](figures/figure_1.png)

Two readings are possible. The favourable one: the rule is picking out pairs
that are genuinely easier to measure, which a random selection would not.
The sceptical one: the certified subset is small, and a small subset of a
noisy population tends to have a smaller error even when the selection is
random. The size-matched nulls address the second reading, and the certified
set beats both by a wide margin — in this draw. Section 6.6 reports the same
test across 23.

### 6.5 Replication across draws
The seed sweep repeats the whole study on 23 declared replication seeds. The
headline quantities are reported as distributions (Table 4).

**Table 4. The replication distribution, 23 draws in the benchmark**

| Quantity | Median | IQR | Range |
|:--|--:|--:|:--|
| Certified coverage | {{sweep.coverage_certified.median}} % | {{sweep.coverage_certified.q25}} – {{sweep.coverage_certified.q75}} % | {{sweep.coverage_certified.min}} – {{sweep.coverage_certified.max}} % |
| Certified MAE | {{sweep.mae_certified.median}} pp | {{sweep.mae_certified.q25}} – {{sweep.mae_certified.q75}} | {{sweep.mae_certified.min}} – {{sweep.mae_certified.max}} |
| Raw midpoint MAE | {{sweep.mae_raw.median}} pp | {{sweep.mae_raw.q25}} – {{sweep.mae_raw.q75}} | {{sweep.mae_raw.min}} – {{sweep.mae_raw.max}} |

*Note: each draw is a complete re-draw of the instrument and a complete re-run of the protocol. The development draw is excluded from this table, as the pre-registration requires.*

Median certified coverage is {{sweep.coverage_certified.median}} %, with a full range of {{sweep.coverage_certified.min}} % to {{sweep.coverage_certified.max}} % across the draws: a stable yield in the sense that matters, but a low one. The day-block null p-value has a maximum of {{sweep.p_block.max}}, which is the floor of the test — with {{sweep.frontier_trials}} trials the add-one estimator cannot report less than {{sweep.frontier_p_floor}} — so the reading is that the selection effect is outside the null in every draw, not that its tail probability is known to five decimal places.

### 6.6 The pre-registered tally, including the failure

The tally (Table 5) is the output of `verdict.py`, which applies the rules of the pre-registration addendum to the sweep outputs and to nothing else. The development draw is excluded. 

**Table 5. The pre-registered rule tally, 23 replication draws**

| Rule | Statement | Outcome |
|:--|:--|:--|
| R1 | The abstention rule selects a set that is genuinely easier to measure, not merely smaller | {{verdict.R1.passed}} |
| R2 | The protocol's own-set error is lower than the raw midpoint's | {{verdict.R2.passed}} |
| R3 | Certification coverage does not depend on one particular synthetic market | {{verdict.R3.passed}} |
| R4 | Coverage is non-decreasing in the certification tolerance | {{verdict.R4.passed}} |
| R5 | The primary and holdout periods agree | {{verdict.R5.passed}} |
| R6 | The perturbation set does not dominate the result | {{verdict.R6.passed}} |
**R1 passed.** The certified set's mean absolute error was below the
day-block null mean in {{verdict.R1.below_block_null}} of
{{verdict.R1.evaluable}} draws, and the day-block null p-value was below
0.05 in {{verdict.R1.block_null_p_below}} of them; the rule required 16.
That is the substantive result: against the null that respects the within-day
dependence of the quotes, the certified set is better, not merely smaller.
**R2 passed too**, and it is the weaker, partly redundant companion: the
certified set's own-set error was
below the raw midpoint's in {{verdict.R2.better}} of
{{verdict.R2.evaluable}} draws, against a required 16.
**R3 failed.** This is the paper's most important negative result and it is
reported as prominently as the passes. The rule required the minimum
certified coverage across the ten market specifications to be at least half
the median coverage. The observed ratio is
{{verdict.R3.minimum_over_median}}, with a minimum coverage of
{{verdict.R3.minimum_coverage}} % against a median of
{{verdict.R3.median_coverage}} %.

**Table 6. Certified coverage across the market specifications in the benchmark**

| Specification | Certified coverage | Certified MAE (pp) | Raw midpoint MAE (pp) |
|:--|--:|--:|--:|
| base | {{sweep.spec.base.coverage}} % | {{sweep.spec.base.mae_certified}} | {{sweep.spec.base.mae_raw}} |
| low_vol | {{sweep.spec.low_vol.coverage}} % | {{sweep.spec.low_vol.mae_certified}} | {{sweep.spec.low_vol.mae_raw}} |
| high_vol | {{sweep.spec.high_vol.coverage}} % | {{sweep.spec.high_vol.mae_certified}} | {{sweep.spec.high_vol.mae_raw}} |
| wide_quotes | {{sweep.spec.wide_quotes.coverage}} % | {{sweep.spec.wide_quotes.mae_certified}} | {{sweep.spec.wide_quotes.mae_raw}} |
| very_wide_quotes | {{sweep.spec.very_wide_quotes.coverage}} % | {{sweep.spec.very_wide_quotes.mae_certified}} | {{sweep.spec.very_wide_quotes.mae_raw}} |
| coarse_tick | {{sweep.spec.coarse_tick.coverage}} % | {{sweep.spec.coarse_tick.mae_certified}} | {{sweep.spec.coarse_tick.mae_raw}} |
| no_wide_sessions | {{sweep.spec.no_wide_sessions.coverage}} % | {{sweep.spec.no_wide_sessions.mae_certified}} | {{sweep.spec.no_wide_sessions.mae_raw}} |
| wide_strike_grid | {{sweep.spec.wide_strike_grid.coverage}} % | {{sweep.spec.wide_strike_grid.mae_certified}} | {{sweep.spec.wide_strike_grid.mae_raw}} |
| short_dated | {{sweep.spec.short_dated.coverage}} % | {{sweep.spec.short_dated.mae_certified}} | {{sweep.spec.short_dated.mae_raw}} |
| long_dated | {{sweep.spec.long_dated.coverage}} % | {{sweep.spec.long_dated.mae_certified}} | {{sweep.spec.long_dated.mae_raw}} |
The pattern in Table 6, and in the right-hand panel of Figure 1, is not
noise. The specifications that widen the
quotes or coarsen the tick drive coverage towards zero, because the
endpoint range of the CPIV widens with the quote width and the resolution
rule abstains on options whose time value has fallen below the scale of the
instrument. A protocol whose coverage depends this strongly on the
microstructure is not a portable rule with a fixed yield, and a reader who
carries the development draw's {{study.coverage.0_10.attempted}} % coverage
figure into a different market will be wrong, possibly by a factor of
several.
The honest reading is that this is a *property of the measurement*. A
protocol that certified everything would be certifying pairs whose CPIV is
not determined by the quotes, and one that abstained everywhere would be
useless. The protocol behaves correctly in both extremes; what it cannot do
is promise a yield in advance, and the R3 failure is the evidence for that
statement.
**R4 passed.** Coverage was monotone in the tolerance in
{{verdict.R4.monotone}} of {{verdict.R4.evaluable}} draws, against a
requirement of 22. A weak condition, but the one that would detect a coding
error in the tolerance rule.
**R5 passed.** The sign of the own-set error reduction agreed between the
primary and holdout periods in {{verdict.R5.sign_agrees}} of
{{verdict.R5.evaluable}} draws, and the two periods' certified coverage were
within 10 percentage points in {{verdict.R5.coverage_agrees}} of them,
against a required 16 in both cases. The period split is a weak test, since
the holdout was not used for threshold selection and the two periods share
the same generator, but it does show the result does not depend on the first
half of the sample.
**R6 passed.** The largest absolute change in certified coverage caused by
any single perturbation was {{verdict.R6.worst_coverage_shift}} percentage
points, against a threshold of 15. Section 6.7 discusses the perturbation
response.

### 6.7 The perturbation response

**Table 7. Perturbation response in the benchmark, development draw**

| Perturbation | Coverage change | MAE (pp) | Mean abs. CPIV change (pp) |
|:--|--:|--:|--:|
| Endpoint widened by half a tick | {{study.perturbation.endpoint_outward.coverage_change}} pp | {{study.perturbation.endpoint_outward.mae}} | {{study.perturbation.endpoint_outward.cpiv_change}} |
| Spot +1 bp | {{study.perturbation.spot_shift_1bp.coverage_change}} pp | {{study.perturbation.spot_shift_1bp.mae}} | {{study.perturbation.spot_shift_1bp.cpiv_change}} |
| Rate +5 bp | {{study.perturbation.rate_shift_5bp.coverage_change}} pp | {{study.perturbation.rate_shift_5bp.mae}} | {{study.perturbation.rate_shift_5bp.cpiv_change}} |
| Spot timestamp −3 s | {{study.perturbation.stale_spot_3s.coverage_change}} pp | {{study.perturbation.stale_spot_3s.mae}} | {{study.perturbation.stale_spot_3s.cpiv_change}} |
| Resolution scale halved | {{study.perturbation.half_tick_resolution.coverage_change}} pp | {{study.perturbation.half_tick_resolution.mae}} | {{study.perturbation.half_tick_resolution.cpiv_change}} |
| Synchronisation tolerance relaxed to 5 s | {{study.perturbation.relaxed_sync_5s.coverage_change}} pp | {{study.perturbation.relaxed_sync_5s.mae}} | {{study.perturbation.relaxed_sync_5s.cpiv_change}} |
The perturbations divide cleanly into three groups, and the division is
informative.
The **timing** perturbation is the largest in coverage terms. Moving the
spot's timestamp three seconds behind the quote timestamps exceeds the
synchronisation tolerance, certified coverage falls to zero, and the
protocol reports no measurement at all. This is correct behaviour and worth
pausing on: a stale underlying price, a completely routine feed condition,
does not merely add noise to a CPIV, it destroys the measurement. A pipeline
that does not check timestamps will still report numbers. Widening every
quote by half a tick does comparable but smaller damage: certified coverage
moves by {{study.perturbation.endpoint_outward.coverage_change_abs}}
percentage points, because the endpoint range widens and the tolerance rule
tightens.
The **model-input** perturbations, a one-basis-point spot shift and a
five-basis-point rate shift, leave the coverage untouched but move the CPIV
values: the mean absolute change is
{{study.perturbation.spot_shift_1bp.cpiv_change}} and
{{study.perturbation.rate_shift_5bp.cpiv_change}} percentage points
respectively — {{study.perturbation.spot_shift_1bp.over_certified_error}} and
{{study.perturbation.rate_shift_5bp.over_certified_error}} times the
certified subset's own error of
{{study.error.protocol_certified.mae}}. This is an important and
slightly uncomfortable finding: the protocol certifies a pair as determined
with respect to the *quote* uncertainty and is silent about the
*model-input* uncertainty, which in these units is larger. The certification
is a statement about the quotes, not about the inputs. The
**protocol-setting** perturbations, by contrast, change nothing here: the
resolution scale is not binding at the base market's microstructure,
consistent with the endpoint stage, not the time-value stage, being where
pairs are lost.

### 6.8 Strata
Certification is not spread uniformly across the contract space. In the
development draw it is confined to the 60-day maturity, to pairs quoted at a
single-tick half-spread, and to the three central strikes; it is zero in
every wing bucket, at 14 and 30 days, at half-spreads of two ticks or more,
and among true spreads below 0.1 percentage points. Table S1 in the
supplementary material reports the full cross-tabulation, with the raw
midpoint's error in each cell for comparison.
The strata are also the result most likely to be over-read. They are
computed *in the benchmark*, against a truth defined by the benchmark's
model. A certified set concentrated near the money is evidence that the
protocol's criteria behave as intended; it is not evidence about where
certification would concentrate in a real market, which depends on that
market's own smile, spreads and liquidity calendar.

### 6.9 The secondary outcome: what abstention costs a surface calibration
The secondary outcome is the calibration of a volatility surface, which needs
a *set* of CPIV values rather than a single one.
In the development draw, the raw-midpoint input set contains
{{secondary.raw_contracts}} contracts and the protocol's input set contains
{{secondary.protocol_contracts}}, so the calibration retains
{{secondary.coverage_retained}} % of the raw set and forgoes
{{secondary.contracts_forgone}} contracts. Fitting a quadratic in
log-moneyness per expiry slice, the two surfaces differ by at most
{{secondary.max_slice_surface_change}} percentage points of CPIV, two
orders of magnitude larger than the certified subset's own measurement
error of {{study.error.protocol_certified.mae}}. The comparison is
descriptive only: the paper makes no claim that either surface is better
specified, better behaved or more profitable.
The surface difference is the quantity to keep in view. Abstaining on
{{secondary.coverage_forgone}} % of the contracts moves the fitted surface by
more than the measurement error of either set, and a practitioner who
silently substituted one for the other would not know it.
Abstention is not free in calibration, where the unit is a set; for one pair
the calculus reverses (Section 6.2).

## 7. Discussion

### 7.1 What the benchmark establishes
Three things are established in the benchmark, and a fourth is not.
**The abstention rule selects a set that is genuinely easier to measure.**
This is R1, and it passed in {{verdict.R1.below_block_null}} of
{{verdict.R1.evaluable}} replication draws against the conservative null:
the certified pairs have a lower mean absolute error than a size-matched
random subset of the same scored universe, even when that subset preserves
the within-day dependence of the quotes. The rule is not selecting fewer
pairs, and it is not selecting a lucky day.
**The protocol's own-set advantage is a selection effect, and the paper says
so.** The common-set identity is reported as exactly zero rather than as a
small number, and the frontier p-values sit beside every own-set comparison.
The distinction between "this method is better" and "this method selected
better data" is the difference between a reproducible method and a result
that depends on the analyst's discretion.
**The thresholds can be fixed before any market data is read.** The addendum
froze the generator, the settings, the seeds, the specifications, the nulls
and the rules before the replication outputs were read.
**What is not established is any market claim.** The benchmark contains no
market data and supports no statement about any real security, index or
option.

### 7.2 The non-claims
The following claims are excluded by the design and bind every part of this
paper, including the abstract and the conclusion: any estimate of coverage,
error or stability in a real market; any statement about a real security,
index or option; any claim of trading profitability, alpha or forecasting
value; any claim that the certification tolerance is universal or optimal;
and any external-validity claim from the synthetic market to real quotes.
Wherever a number appears in this paper, it is a number *in the benchmark*.
The largest difference between the benchmark and a licensed run is that the
benchmark's truth is known, and a known truth makes accuracy measurable in a
way that no real market ever permits. A protocol validated on accuracy and
then applied to a market where accuracy is unobservable has inherited its
thresholds but none of its evidence about them.

### 7.3 Threats to validity
**The truth is a model artefact, and the European map is an approximation
for American options.** The benchmark's put leg is American and is inverted
under a European map, and the protocol recovers the truth anyway — but the
cancellation that makes this work depends on the exercise premium being a
smooth function of the contract's parameters. A market in which early
exercise is discontinuous in the strike would break that, and the licensed
run may present departures the benchmark does not.
**The instrument's microstructure was chosen.** The R3 failure is a
statement about the sensitivity of coverage to microstructure, demonstrated
on specifications of *this* instrument. The qualitative finding — that
coverage is a property of the market, not of the protocol — is robust to
this, but the numbers in Table 6 are not.
**The inference is on one instrument with two underlyings.** The
underlying-day block bootstrap treats the underlying-day as the unit, and
there are {{study.inference.blocks}} such blocks in the development draw.
The replication across seeds is the paper's defence against the precision
of any one interval. The primary and holdout periods share the generator and
the underlying paths, so the split tests robustness rather than replication.

### 7.4 What a practitioner should do with this
The operational message is deliberately narrow. A practitioner who wants to
use a CPIV should know three things.
First, a CPIV computed from midpoints is not a measurement, and the
benchmark's raw midpoint has a mean absolute error of
{{study.error.raw_midpoint.mae}} percentage points with a 95th percentile of
{{study.error.raw_midpoint.p95}} and a maximum of
{{study.error.raw_midpoint.max}}. Those are benchmark numbers and transfer
to a real market only as an order of magnitude, but the shape they describe
— a small tail carrying a large mean — is generic.
Second, the errors concentrate in identifiable places: wide quotes, short
maturities, wings, and the ticks on the clock. A pipeline that checks those
four things will abstain on most of what it should, and that is cheaper and
more robust than a full abstention protocol.
Third, and least obvious: model-input sensitivity is larger than quote
sensitivity in these units. A certified CPIV is a statement about the
quotes, not about the spot, the rate or the dividend assumption behind them;
a user who reads "certified" as "correct" has misread it (Section 6.7).

## 8. Conclusion and future research
A call–put implied-volatility spread computed from quote midpoints is
routinely reported as though it were a measurement, and it frequently is
not. This paper describes a protocol that decides, for each quote pair,
whether the spread is determined at a declared tolerance, declines to assert
when it is not, and assigns every attempted pair one terminal status so that
nothing disappears silently.
Because the protocol labels rather than re-estimates, its advantage over the
raw midpoint is a selection effect, and the paper reports it as one: the
common-set difference is exactly zero, and the informative comparison is
against size-matched random subsets. Against a null that resamples whole
underlying-days, and so respects the within-day dependence of the quotes,
the certified subset is easier to measure in {{verdict.R1.below_block_null}}
of {{verdict.R1.evaluable}} replication draws in the benchmark.
One pre-registered rule failed, and it is the result with the longest reach:
certification coverage depends strongly on quote microstructure, falling from
{{verdict.R3.median_coverage}} % at the median market specification to
{{verdict.R3.minimum_coverage}} % at the least favourable one. The protocol
is not a portable rule with a fixed yield. It is a labelling device whose
coverage is a property of the market it meets, and a practitioner who
carries a coverage figure from one market into another will be wrong.
The benchmark supports no market claim, and none is made. What it does
establish is that the machinery behaves as specified, that the abstention
rule has a quantifiable selection effect, and that the thresholds can be
fixed before any market data is read.
The research that follows is of three kinds. **A licensed run**, whose
schema, sampling rule and tick convention must be fixed and frozen first,
and whose primary result will be coverage and stability rather than
accuracy, because no real market permits accuracy to be measured. **An
American fallback for the put leg**, which the benchmark shows the European
map can survive in the tested regime, and which must be adopted on the
strength of the licensed data's exercise-style convention rather than a
synthetic one. And **an independent reimplementation** of the inversion and
the resolution rules, which no single-authored pipeline can supply for
itself.

## Declarations of Interest

**Funding.** This research received no specific grant from any funding
agency in the public, commercial or not-for-profit sectors.

**Competing interests.** The author reports no conflicts of interest. The
author alone is responsible for the content and writing of the paper.

**Ethics approval.** This study uses a synthetic instrument defined by a
released generator, with no human participants, human tissue, personally
identifiable data, or data collected from persons. Ethical review and
informed consent were therefore not required, and no institutional review
board approval applies.

## Data and code availability

This paper contains **no market data**. Every result comes from a synthetic
instrument whose true call–put implied-volatility spread is defined by the
generator before any quote exists. The instrument, the protocol, the
replication sweep, the decision-rule tally and the manuscript build are
implemented in code, and run manifests record the configuration, the seed,
the environment and the output hashes of every run reported here. The code
and the aggregate run artefacts (the study summary, the per-draw sweep
outputs, the specification grid and the rule tally) are available from the
author for review and will be deposited in a public repository on
acceptance.

No licensed market data was used. The licensed run on which the protocol is
intended to be applied has not been carried out, and no result in this paper
depends on one.

## Use of artificial intelligence

The author used Perplexity for deep research. An AI assistant helped draft
the phase-0 design record and the pre-registration, wrote and maintained the
measurement and analysis code and its test suite, the build, rendering and
submission scripts and the manuscript-limits checker, and assisted with the
language and structure of this manuscript. No AI system generated a result,
a number or a table: every number in this paper is produced by the released
code from the released artefacts, and the manuscript build fails if any
numeric slot in the text has no corresponding value in those artefacts. The
author reviewed all assisted work and is responsible for the entire content
of the paper.

## Author contributions

The sole author contributed to every CRediT category: Conceptualization,
Methodology, Software, Validation, Formal analysis, Investigation, Data
curation, Writing – original draft, Writing – review and editing,
Visualization, and Supervision. Author identity is withheld for blind
review; the named author appears on the separate title page. The author
reviewed and approved every AI-assisted task described above and takes
full responsibility for the paper.

## References

Black, F., & Scholes, M. S. (1973). The pricing of options and corporate liabilities. *Journal of Political Economy, 81*(3), 637–654. https://doi.org/10.1086/260062

Breeden, D. T., & Litzenberger, R. H. (1978). Prices of state-contingent claims implicit in option prices. *The Journal of Business, 51*(4), 621–651. https://doi.org/10.1086/296025

Chow, C. K. (1970). On optimum recognition error and reject tradeoff. *IEEE Transactions on Information Theory, 16*(1), 41–46. https://doi.org/10.1109/TIT.1970.1054406

Cox, J. C., Ross, S. A., & Rubinstein, M. (1979). Option pricing: A simplified approach. *Journal of Financial Economics, 7*(3), 229–263. https://doi.org/10.1016/0304-405X(79)90015-1

Cremers, M., & Weinbaum, D. (2010). Deviations from put–call parity and stock return predictability. *Journal of Financial and Quantitative Analysis, 45*(2), 335–367. https://doi.org/10.1017/S002210901000013X

Davison, A. C., & Hinkley, D. V. (1997). *Bootstrap methods and their application*. Cambridge University Press. https://doi.org/10.1017/CBO9780511802843

Efron, B., & Tibshirani, R. J. (1993). *An introduction to the bootstrap*. Chapman & Hall.

Figlewski, S. (1989). Options arbitrage in imperfect markets. *The Journal of Finance, 44*(5), 1289–1311. https://doi.org/10.1111/j.1540-6261.1989.tb02654.x

Glosten, L. R., & Milgrom, P. R. (1985). Bid, ask and transaction prices in a specialist market with heterogeneously informed traders. *Journal of Financial Economics, 14*(1), 71–100. https://doi.org/10.1016/0304-405X(85)90044-3

Harvey, C. R., Liu, Y., & Zhu, H. (2016). … and the cross-section of expected returns. *The Review of Financial Studies, 29*(1), 5–68. https://doi.org/10.1093/rfs/hhv059

Hentschel, L. (2003). Errors in implied volatility estimation. *Journal of Financial and Quantitative Analysis, 38*(4), 779–810. https://doi.org/10.2307/4126743

Imbens, G. W., & Rubin, D. B. (2015). *Causal inference for statistics, social, and biomedical sciences: An introduction*. Cambridge University Press. https://doi.org/10.1017/CBO9781139025751

Longstaff, F. A., & Schwartz, E. S. (2001). Valuing American options by simulation: A simple least-squares approach. *The Review of Financial Studies, 14*(1), 113–147. https://doi.org/10.1093/rfs/14.1.113

Madhavan, A. (2000). Market microstructure: A survey. *Journal of Financial Markets, 3*(3), 205–258. https://doi.org/10.1016/S1386-4181(00)00007-0

Merton, R. C. (1973). Theory of rational option pricing. *The Bell Journal of Economics and Management Science, 4*(1), 141–183. https://doi.org/10.2307/3003143

Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The preregistration revolution. *Proceedings of the National Academy of Sciences, 115*(11), 2600–2606. https://doi.org/10.1073/pnas.1708274114

Ofek, E., Richardson, M., & Whitelaw, R. F. (2004). Limited arbitrage and short sales restrictions: Evidence from the options markets. *Journal of Financial Economics, 74*(2), 305–342. https://doi.org/10.1016/j.jfineco.2003.05.008

Politis, D. N., & Romano, J. P. (1994). The stationary bootstrap. *Journal of the American Statistical Association, 89*(428), 1303–1313. https://doi.org/10.1080/01621459.1994.10476870

White, H. (2000). A reality check for data snooping. *Econometrica, 68*(5), 1097–1126. https://doi.org/10.1111/1468-0262.00152
