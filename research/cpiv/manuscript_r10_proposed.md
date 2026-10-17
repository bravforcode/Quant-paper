---
title: "Diagnosing Call–Put Implied-Volatility Spreads: Exact European-BSM Mapping and Synthetic Reliability Tests"
subtitle: "A measurement-focused quantitative methods note"
lang: en-US
date: "10 October 2026"
author: "Phirawit Jitnarong"
description-meta: "A reproducible diagnostic framework for CPIV measurement, European BSM inversion, quote intervals, and synthetic ranking stability."
---

**Affiliation:** Independent researcher  
**ORCID:** [0009-0006-8368-5309](https://orcid.org/0009-0006-8368-5309)  
**Contact:** [email removed]

## Thai summary

บทความนี้ตรวจวิธีวัด call–put implied-volatility spread (CPIV) โดยไม่อ้างว่าเป็นกลยุทธ์ทำกำไร หาก call และ put ถูกแปลงด้วย European BSM ชุดเดียวกัน parity residual เท่ากับอินทิกรัลของ vega ระหว่าง IV ทั้งสอง แม้ราคาต้นทางจะมาจากแบบจำลองอื่น ตราบใดที่ทั้งสองรากยัง invert ได้ด้วย inputs ร่วมกัน งานจำลอง 720 กรณีพบว่า 624 กรณีผ่าน absolute vega guard ที่ผู้เขียนตั้งไว้ และ 96 กรณีไม่ผ่าน guard; เกณฑ์นี้ไม่ใช่มาตรฐานสากลหรือหลักประกันความแม่นยำ การทดสอบอันดับมี 72,000 รอบสังเคราะห์ โดยผลขึ้นกับระยะห่างของสัญญาณและรูปแบบ noise ทั้งหมดเป็นการตรวจเชิงวิธี ไม่มี option-chain จริง ผลตอบแทน การทดสอบ alpha หรือข้อสรุปเชิงตลาด

**คำสำคัญ:** call–put implied-volatility spread; put–call parity; implied volatility; vega; quote uncertainty; numerical stability; synthetic measurement study

\newpage

## Abstract

This methods note specifies a diagnostic workflow for measuring the call–put implied-volatility spread (CPIV). If both observed leg prices admit implied-volatility roots under the same European Black–Scholes–Merton (BSM) map and common inputs, their parity residual equals the integral of BSM vega between those roots, irrespective of the prices’ origin. The residual and CPIV are therefore linked by construction, not independent confirmations. Across 720 synthetic approximation cases, 624 pass the study’s configured absolute-vega guard and 96 do not; the guard is not scale invariant or a general reliability criterion. Among the 624 passing cases, the midpoint linear approximation has median absolute error 0.000079 percentage points, a 95th percentile of 0.0872 points, and a maximum of 1.236 points. A separately specified ranking stress design contains 72,000 synthetic replicates. No historical option quotes, returns, positions, alpha estimates, or investment performance are analyzed; the results are conditional numerical diagnostics, not market estimates.

**Keywords:** call–put implied-volatility spread; put–call parity; implied volatility; vega; quote uncertainty; numerical stability; synthetic measurement study

## 1. Introduction

The call–put implied-volatility spread is often discussed as a measure of relative option richness or as a predictor of returns. Those interpretations concern different objects. CPIV is a difference between two model-implied volatility estimates. A return spread is an outcome measured in a later period. An option-return spread is different again. A measurement study should establish what the input prices and inversion procedure identify before attaching an economic interpretation.

This note makes a narrow operational contribution: it specifies and implements a diagnostic workflow that connects the common-map identity, input validation, inversion statuses, quote-implied ranges, local approximation, and ranking stability. It does not claim a novel parity identity or an empirically superior estimator. Its contribution is the explicit workflow and the accompanying synthetic numerical stress tests; the staged protocol appears in Table 4.

The scope is intentionally limited. The synthetic tests establish properties of the specified pricing map and simulation designs. They do not establish how often these conditions occur in listed markets, whether CPIV forecasts stock or option returns, or whether a CPIV strategy earns returns after costs. No historical option-chain data or market-wide position census is used.

## 2. Related literature and the measurement question

Empirical work gives CPIV-like measures economic interpretations, but it studies outcomes that should not be conflated. Cremers and Weinbaum (2010) use implied-volatility differences between paired calls and puts and report a relation with subsequent stock returns. Their paper also examines stock-lending rebate rates directly; it should not be summarized as ignoring borrow conditions. Doran, Fodor, and Jiang (2013) distinguish stock-return predictability from returns on out-of-the-money call options and interpret option demand using their data. Those are separate outcome variables and empirical designs.

Related cross-market evidence need not be a CPIV result. Goncalves-Pinto et al. (2020) study discrepancies between stock-market prices and option-implied stock values. Their evidence is consistent with stock-price pressure being an important driver in their setting. That finding motivates caution when interpreting option-implied signals; it does not validate the synthetic diagnostics in this note.

Measurement error is central to implied-volatility work. Hentschel (2003) shows that plausible errors in option characteristics can translate into large implied-volatility errors, particularly away from the money, and discusses lower-bound truncation as a source of bias. Muravyev and Pearson (2020) show that option-trading-cost estimates depend on execution timing in their sample. Their estimates are not universal bid–ask discounts and are not applied as corrections here. Sokolov's (2019) doctoral dissertation develops a noisy-price interpretation of implied-volatility spreads and discusses American-option bounds with bid–ask spreads; it is useful background but is a dissertation, not a journal article.

The gap addressed here is narrower than those economic debates: given paired prices and a stated inversion contract, what is algebraically identified, what is numerically resolved, and how sensitive are descriptive rankings to plausible *synthetic* perturbations? The answer is a measurement protocol, not a causal or predictive claim.

## 3. Definitions and units

For a call and put with the same underlying, timestamp, strike \(K\), expiry \(T\), and pricing inputs, define

$$
CPIV_{pp}=100(\sigma_C-\sigma_P)\qquad\text{(1)}
$$

where each \(\sigma\) is an annualized volatility in decimal units. The subscript \(pp\) denotes volatility percentage points: a decimal-volatility difference of 0.01 is one percentage point. It is not a percentage return.

With spot \(S\), continuously compounded rate \(r\), and continuous effective yield \(q\), define the European parity residual

$$
R=C-P-(Se^{-qT}-Ke^{-rT})\qquad\text{(2)}
$$

in underlying-currency units per underlying unit, before applying any option-contract multiplier. If prices are stated per contract, every price and parity term must use that same contract basis; equivalently, \(R_{contract}=M R_{unit}\) for multiplier \(M\). The yield \(q\) is an effective pricing input, not automatically a stock-borrow fee, funding charge, or crypto funding rate.

## 4. Exact identity and local approximation

Let \(C_{BSM}(\sigma)\) and \(P_{BSM}(\sigma)\) be European BSM call and put prices evaluated with the same \((S,K,T,r,q)\). European put–call parity holds at each common volatility, so

$$
\begin{aligned}
R_x
&=C_{BSM}(x,\sigma_C)-P_{BSM}(x,\sigma_P)-A(x) \\
&=C_{BSM}(x,\sigma_C)-C_{BSM}(x,\sigma_P) \\
&=\int_{\sigma_P}^{\sigma_C}\nu(x,u)\,du \\
&=(\sigma_C-\sigma_P)\,\bar{\nu}(x)\qquad\text{(3)},
\end{aligned}
$$

Here \(x=(S,K,T,r,q)\), \(A(x)=Se^{-qT}-Ke^{-rT}\), and \(\nu(x,u)=\partial C_{BSM}(x,u)/\partial u\), in currency units per one full decimal-volatility unit. Define the path-average vega by

$$
\bar{\nu}(x)=\int_0^1\nu\!\left(x,\sigma_P+t(\sigma_C-\sigma_P)\right)dt\qquad\text{(4)}.
$$

This definition also applies when the endpoints coincide: then \(\bar{\nu}=\nu(x,\sigma_C)\). The integral is oriented and changes sign with \(\sigma_C-\sigma_P\). For admissible finite roots with positive average vega, the exact relation is \(CPIV_{pp}=100R_x/\bar{\nu}(x)\), including the zero-spread case, where both numerator and CPIV are zero.

For a selected reference volatility \(\sigma_0\), a local approximation replaces path-average vega with point vega:

$$
CPIV_{pp}\approx \frac{100R_x}{\nu(x,\sigma_0)}\qquad\text{(5)}.
$$

When vega is reported per one volatility percentage point, \(\nu_{pp}=\nu/100\), the approximation is \(CPIV_{pp}\approx R_x/\nu_{pp}(x,\sigma_0)\). The exact identity makes CPIV and the residual algebraically dependent, not independently validating. It does not attribute a market residual to information or trading; synchronization, exercise style, carry inputs, price discreteness, and model mismatch affect economic interpretation.

The BSM formula is used as an inversion map. The identity holds for any admissible input prices that are each inverted through that same European-BSM map with the same \(x\), and whose residual uses that same \(x\); the price origin need not be European BSM. American exercise, a stale source spot, or another pricing model can change the residual’s economic interpretation without breaking this map identity. The identity in this form does not apply when the legs use different contract/market inputs, either IV root fails to exist, or the residual uses inputs different from those used for inversion. European parity remains a separate no-arbitrage statement, not a claim about the origin of observed prices.

## 5. Inversion and numerical contract

For European prices, the admissible intervals used by the implementation are

$$
\max(Se^{-qT}-Ke^{-rT},0)\le C<Se^{-qT},
\qquad
\max(Ke^{-rT}-Se^{-qT},0)\le P<Ke^{-rT}.
$$

The implementation requires a call or put, finite numerical inputs, \(S>0\), \(K>0\), positive days to expiry, and positive volatility for pricing. Its inversion rejects non-finite or negative prices, prices within \(10^{-10}\) currency units of a European bound, and prices outside the configured decimal-IV bracket \([10^{-8},5]\); bisection runs for 64 iterations without quote clipping. Failures are classified as invalid input, theoretical-bound violation, rejection by the configured near-bound guard, outside-bracket, or numerical/unclassified rejection. A configured-bracket rejection is not itself an invalid market quote. Successful roots are repriced; repricing error and IV recovery error are reported separately.

The round-trip design contains 60 contract configurations and 120 option-leg prices (five \(S/K\) ratios × four expiries × three target IVs × two legs). In the recorded run, 104 prices inverted; 15 were rejected by the configured absolute near-bound guard and one double-precision price was outside its computed theoretical bound. The 180-digit Decimal cross-check independently recomputed the 16 intended BSM prices: all 16 lay strictly inside the high-precision bounds, had target IVs inside the solver bracket, and were within the configured \(10^{-10}\) absolute guard. In the double-precision records, only 12/16 remained strictly inside the computed bounds. This supports treating the 16 cases as near-bound limitations of this generated numerical design; it does not establish a general floating-point failure rate. Among the 104 successful inversions, maximum absolute repricing error was \(2.84\times10^{-14}\) currency units and maximum/p95 absolute IV-recovery error was \(1.19\times10^{-11}/5.41\times10^{-13}\) in decimal volatility. Ten deliberately invalid-price probes were rejected and none accepted. These are synthetic outcomes, not market-quote failure rates; the threshold remains an implementation setting, not a universal filter.

\newpage

## 6. Synthetic design

All input prices and signals are generated from fixed formulas. Appendix B gives the commands that regenerate the demonstration and R10 diagnostics. A separate standard-library identity checker (`independent_bsm_crosscheck.py`) imports neither of those implementations. It is a distinct code path by the same author, not an independent human replication or a high-precision oracle. The experiments use a 365-day year, continuous rates and yields, and underlying-currency price units. No network call or external market data is used.

### 6.1 Local-approximation grid

The 720-cell grid fixes \(K=100\) and crosses \(S/K\in\{0.8,0.9,1.0,1.1,1.2\}\), expiries \(T\in\{7,30,90,365\}\) days, midpoint reference volatilities \(\sigma_0\in\{0.10,0.20,0.40\}\), six nonzero target spreads \(d_{pp}\in\{-2,-1,-0.5,0.5,1,2\}\), and carry pairs \((r,q)=(0,0),(0.05,0.02)\). For each cell, \(S=100(S/K)\), \(d=d_{pp}/100\), \(\sigma_C=\sigma_0+d/2\), and \(\sigma_P=\sigma_0-d/2\). Thus the midpoint, rather than one endpoint, is the designated reference; this symmetric construction can cancel the leading odd-order term in the midpoint expansion and may favor the local approximation.

Composite Simpson quadrature uses 2,000 even subintervals as the primary numerical integral; the output also records 1,000-versus-2,000 and 2,000-versus-4,000 differences, plus the gap between direct price residual and integrated vega. These are separate numerical diagnostics. Local-approximation error is separately calculated against the target CPIV spread. It is not a solver or quadrature error. For each cell, midpoint and both endpoint vegas are reported. The legacy guard flags a cell unresolved when absolute midpoint vega is below \(10^{-6}\) currency units per decimal IV. In the nominal-scale experiment, normalized midpoint vega is \(\tilde{\nu}_{mid}=\nu_{mid}/\max(Se^{-qT},Ke^{-rT})\): the numerator is currency units per decimal IV and the denominator is the discounted underlying-currency scale per underlying unit, so this ratio is normalized per decimal-IV unit. Each scale factor is evaluated over 120 baseline configurations (five \(S/K\) ratios × four expiries × three reference-IV levels × two carry pairs). The absolute guard resolves 104/120, 104/120, and 106/120 configurations at nominal scale factors 0.01, 1, and 100, respectively. These are grid diagnostics, not a market-weighted distribution or general reliability rule. In the local-approximation grid, midpoint volatility and the other non-spread inputs stay fixed across each configuration's six spread cells, so normalized midpoint vega is spread-invariant; its summary therefore counts each unique non-spread configuration once.

### 6.2 Carry, spot synchronization, and exercise style

The carry experiment uses \(S=K=100\), 30 days to expiry, \(r=0\), and volatility 20%; it generates matched European BSM prices at effective yields \(q\in\{-2,-1,0,1,2,5\}\%\) and then inverts each pair with \(q=0\). The spot experiment uses the same spot, strike, maturity, and volatility, with \(r=q=0\): prices are generated at spot 100 and inverted with spot displaced by \(-0.25,-0.10,-0.05,-0.02,0.02,0.05,0.10,0.25\) currency units. Neither experiment identifies a borrow fee or an empirical timestamp effect.

The American-put comparison fixes \(S=K=100\), 30 days, \(r=5\%\), \(q=0\), and \(\sigma=20\%\); it pairs a European BSM call with an American put valued by CRR and an equal-probability Jarrow–Rudd tree. CRR uses \(u=e^{\sigma\sqrt{\Delta t}}\), \(d=1/u\), and risk-neutral probability \(p=(e^{(r-q)\Delta t}-d)/(u-d)\), with early exercise at each node. The implemented Jarrow–Rudd variant uses \(u=e^{(r-q-\sigma^2/2)\Delta t+\sigma\sqrt{\Delta t}}\), \(d=e^{(r-q-\sigma^2/2)\Delta t-\sigma\sqrt{\Delta t}}\), and probability 1/2, also with early exercise. Both are compared at 400, 800, 1,600, 3,200, and 6,400 steps. A successive-grid CPIV change below 0.001 percentage points is a descriptive audit threshold, not a formal error bound or preregistered stopping rule; the two schemes are not asserted to be exact American benchmarks (Cox et al., 1979; Jarrow & Rudd, 1983).

### 6.3 Quote-implied intervals

For bid and ask prices that each admit a finite European IV under the same inputs, the quote-implied range is

$$
100\left[IV(C_{bid})-IV(P_{ask}),\;IV(C_{ask})-IV(P_{bid})\right]\quad\text{(6)}.
$$

The output is in volatility percentage points. Endpoints combine quote-side extremes; the interval is not statistical coverage, a confidence interval, probability statement, or arbitrage bound. All ten synthetic pairs use \(S=K=100\), 30 days to expiry, and \(r=q=0\); put IV is 20% and call IVs run from 16% through 25%. A symmetric premium half-spread of USD 0.01, 0.02, 0.05, 0.10, or 0.25 per underlying unit is added/subtracted before inversion. The code reports the four-endpoint-invertible fraction out of 10 pairs, sign-resolved count/fraction among those valid pairs, median interval width in points, and strict non-overlap counts divided both by eligible valid unordered pairs and all 45 possible unordered pairs. Touching endpoints count as overlap. Unresolved pairs are not silently interpreted as ties.

### 6.4 Ranking stress experiment

The ranking experiment crosses \(n\in\{10,50\}\), five signal shapes, eight synthetic noise structures, and three configured scales (0.25, 0.50, 1.00 pp). For \(i=0,\ldots,n-1\), let \(x_i=-1+2i/(n-1)\), in CPIV points. The shapes are: equally spaced \(x_i\); clustered near zero \(x_i^3\); near-tied \(0.03x_i\); two clusters \(-1+0.02i/n\) for \(i<n/2\) and \(1+0.02i/n\) otherwise; and the concave-magnitude transform \(g(x_i)=\operatorname{sign}(x_i)\sqrt{|x_i|}\). This deterministic transform remains supported on \([-1,1]\); it is not a heavy-tailed distribution.

Noise is added directly in CPIV space, not option-price space. The families are: (1) uniform \(U(-\sqrt{3}s,\sqrt{3}s)\); (2) Gaussian \(N(0,s^2)\); (3) a 5% contaminated Gaussian whose contaminant SD is five times the base SD and whose theoretical mixture variance is normalized to \(s^2\); (4–6) Gaussian heteroskedastic noise with factors \(f_i=0.5+i/(n-1)\), normalized by \(\sqrt{n^{-1}\sum_i f_i^2}\), respectively increasing, decreasing, or randomly permuted across names in each replicate; (7) Gaussian call/put leg errors each with marginal SD \(s\) and correlation 0.8, with CPIV noise defined as call error minus put error, giving theoretical paired SD \(s\sqrt{2(1-0.8)}=s\sqrt{0.4}\); and (8) one Gaussian additive CPIV shock shared identically by every name, included as a ranking-invariance control rather than a market-error model. Therefore the same configured scale does not imply the same paired CPIV SD in family 7. Three fixed seeds (20261009, 20261010, 20261011) contribute 100 replicates each. The total is \(2\times5\times8\times3\times300=72{,}000\) synthetic rankings. Within each universe–signal-shape–noise-family design and seed, the same underlying random draws are reused across scale values; results are compared as paired replicate differences.

For a replicate, the inversion fraction is the number of discordant unordered pairs divided by \(n(n-1)/2\), with index order breaking exact ties. Spearman's \(\rho=1-6\sum_i d_i^2/[n(n^2-1)]\) uses the resulting tie-broken ranks. Let \(k=\lfloor n/5\rfloor\); top/bottom turnover is \(1-(|L\cap L'|+|B\cap B'|)/(2k)\), the mean of long- and bottom-set missing-member fractions. Sign accuracy is \(n^{-1}\sum_i\mathbf{1}[(x_i>0)=(y_i>0)]\); exact zero is treated as nonpositive. The code also records exact full-order preservation and any extreme-quintile membership change.

Continuous metric means and their normal Monte Carlo intervals use each replicate as the observation; names and within-replicate pairs are not treated as independent observations. Adjacent noise-scale contrasts use paired replicate differences, with paired MCSE/intervals. Wilson intervals are reported for simulated event rates only. These intervals quantify finite simulation variation conditional on the chosen generator and seeds; they are not market confidence intervals. Per-name inclusion probabilities are supplied for the ten-name universe. None of the vectors or noise distributions is asserted to be market-realistic or calibrated.

## 7. Results

### 7.1 Local approximation and numerical resolution

Of the 720 grid cells, 624 pass the configured absolute midpoint-vega guard and 96 do not. Within those same 624 cells, midpoint-reference absolute error has median 0.0000786 pp, nearest-rank p95 0.0872 pp, and maximum 1.2355 pp. The nearest-rank convention selects the \(\lceil0.95n\rceil\)-th ordered value; for \(n=624\), this is the 593rd observation. Put-endpoint and call-endpoint vega errors are summarized separately, with 624 resolved observations for each endpoint reference; neither summary pools them into 1,248 observations. Their median, p95, and maximum are equal because the absolute call-endpoint error at spread \(+d\) matches the absolute put-endpoint error at spread \(-d\) for each reflected grid configuration: 0.02025 pp, 1.1752 pp, and 32.5547 pp, respectively. This does not imply that the two endpoint errors are equal within the same cell. The midpoint reference is centered by design, so this grid comparison is favorable to it and does not identify a preferred reference for market data. The worst midpoint-reference error occurs at \(S/K=0.8\), 90 days, 10% reference IV, and a two-point spread. Each grid cell is equally weighted; none of these summaries estimates live-chain error.

Normalized midpoint vega is constant across the six spread cells for each non-spread configuration in this design. Among the 120 unique configurations, 16 fail the absolute guard; each contributes six cells. Their normalized midpoint vega has median \(1.40\times10^{-14}\) and maximum \(1.72\times10^{-10}\) per decimal-IV unit. The minimum among the 104 configurations that pass is \(7.30\times10^{-6}\), about \(4.23\times10^4\) times the maximum in the failing group (4.63 orders of magnitude). This separation describes this constructed grid only; it does not validate a normalized cutoff or establish similar separation in market data. The nominal-scale diagnostic preserves normalized vega under multiplication of prices by 0.01, 1, or 100, while the absolute guard resolves 104/120, 104/120, and 106/120 configurations, respectively. That change confirms that the legacy cutoff is scale-dependent, not a universal resolution criterion.

![Absolute error of the midpoint local residual-to-CPIV approximation across resolved synthetic cases. The configured absolute vega guard is applied before plotting; unresolved cells are counted separately.](research/cpiv/generated/r10_release/cpiv_r10_local_approximation_error.png){#fig-local-error}

### 7.2 American-put scheme comparison

The reported statistic is a numerical CPIV generated from an exact European BSM call and a tree-priced American put. At 6,400 steps, each scheme's change from its immediately preceding doubled grid is below the selected 0.001 pp threshold (CRR 0.000502 pp; Jarrow–Rudd 0.000169 pp). The two schemes' CPIV values at 6,400 steps differ by 0.001086 pp (−0.264587 versus −0.265673). This is only a successive-grid change diagnostic: it is not a formal error bound, proof of convergence, or independent exact-price benchmark. No high-resolution external reference is claimed.

**Table 1.** Tree-price and implied-CPIV outputs for one synthetic American-put scenario; change threshold is 0.001 pp between adjacent doubled grids.

| Steps | CRR put | CRR CPIV (pp) | Jarrow–Rudd put | Jarrow–Rudd CPIV (pp) |
|--:|--:|--:|--:|--:|
| 400 | 2.112510 | −0.257018 | 2.114871 | −0.277758 |
| 800 | 2.112971 | −0.261065 | 2.114140 | −0.271341 |
| 1,600 | 2.113200 | −0.263082 | 2.113498 | −0.265699 |
| 3,200 | 2.113315 | −0.264085 | 2.113515 | −0.265841 |
| 6,400 | 2.113372 | −0.264587 | 2.113495 | −0.265673 |

![CRR and equal-probability Jarrow–Rudd American-put synthetic tree comparison.](research/cpiv/generated/r10_release/cpiv_r10_american_convergence.png){#fig-american-convergence width=75%}

### 7.3 Carry and spot mismatch

With true \(q=5\%\) and inversion at \(q=0\), the generated CPIV is \(-3.58725\) points; at \(q=-2\%\), it is \(+1.43903\) points. At zero yield it is zero up to rounding. The direction changes with the omitted yield, as expected under this construction. This demonstrates sensitivity to the effective-yield input, not an empirical relationship between CPIV and stock lending.

When quotes use spot \(100\) and inversion uses stale spot \(100.10\), the synthetic CPIV is \(-0.87439\) points; a stale spot of \(99.90\) produces \(+0.87526\) points. The asymmetry comes from the nonlinear BSM map. These examples reinforce that a quote timestamp and the spot timestamp belong in the data contract.

### 7.4 Quote-implied interval width and rank resolution

All ten synthetic pairs have four invertible quote endpoints at each tested spread. At a USD 0.02 half-spread, median interval width is 0.700 pp, 9/10 pairs exclude zero, and 45/45 unordered pairwise intervals are strictly non-overlapping. At USD 0.10, median width is 3.499 pp, 7/10 pairs exclude zero, and 21/45 pairwise comparisons are non-overlapping. At USD 0.25, median width is 8.747 pp, 1/10 pairs excludes zero, and 1/45 comparison is non-overlapping. A non-overlap result means only that this interval rule orders that constructed pair; overlap means this rule does not resolve its order. These are deterministic properties of ten constructed pairs and chosen premium bands—not statistical coverage, market rank accuracy, or evidence that any unresolved comparison is wrong.

### 7.5 Ranking reliability depends on signal spacing

The stress test does not produce one universal “reliability” number. For ten equally spaced signals and Gaussian noise with target SD 0.50 points, mean pairwise inversion fraction is 17.6%, mean Spearman correlation is 0.797, and top/bottom membership turnover is 36.7%. For ten near-tied signals at the same noise scale, those values are 49.5%, 0.015, and 79.2%. In the 300 draws for each of these cells, no full ordering was preserved; the Wilson 95% upper bound is 1.26%, not zero probability. Near-tied sign accuracy is approximately 50%, as expected when noise dominates the prescribed signal.

**Table 2.** Replicate-level means and Monte Carlo standard errors (in parentheses) for Gaussian CPIV-space noise at configured SD 0.50 pp; each cell has 300 replicates.

| Universe and prescribed signals | Inversion fraction (MCSE) | Spearman \(\rho\) (MCSE) | Top/bottom turnover (MCSE) | Sign accuracy (MCSE) | Exact orders / 300 (Wilson upper 95%) |
|:--|--:|--:|--:|--:|--:|
| 10, equally spaced | 0.1759 (0.0038) | 0.7971 (0.0067) | 0.3667 (0.0122) | 0.8260 (0.0066) | 0 (1.26%) |
| 10, near-tied | 0.4951 (0.0069) | 0.0145 (0.0187) | 0.7917 (0.0111) | 0.5040 (0.0089) | 0 (1.26%) |
| 50, equally spaced | 0.2119 (0.0014) | 0.7710 (0.0029) | 0.4023 (0.0049) | 0.8074 (0.0031) | 0 (1.26%) |
| 50, near-tied | 0.4922 (0.0028) | 0.0227 (0.0081) | 0.7977 (0.0047) | 0.5067 (0.0042) | 0 (1.26%) |

For this metric, a uniformly random ranking gives an exact chance reference. If each tail contains k = n/5 names, expected overlap with either fixed true tail is k²/n; therefore expected top/bottom turnover is 1 − (2k²/n)/(2k) = 1 − k/n = 0.8. The near-tied means, 0.7917 for n = 10 and 0.7977 for n = 50, are respectively 0.75 and 0.49 MCSE below that reference (Table 2). This contextualizes these low-signal synthetic rankings; it does not estimate market turnover.

The comparison changes with signal spacing and error structure. A common additive shock shifts every value equally and therefore leaves ordering unchanged by construction; it is an invariance control, not a market-noise model. Continuous-metric MCSEs are calculated across the 300 replicate-level metric values; names and within-replicate pairs are not counted as independent observations. The Wilson upper bound after 0/300 exact orders is 1.26%; zero observed events is not a zero probability. Full cell-level means/MCSEs, Wilson intervals, paired scale contrasts, and per-name inclusion probabilities are in the companion CSVs.

Numerical cross-check scope and provenance are documented in Section 9; these checks are implementation diagnostics, not independent validation.

### 7.6 Illustrative uncertainty budget

For \(R=C-P-Se^{-qT}+Ke^{-rT}\), the first-order residual perturbation, with \(K,T\) fixed, is

$$
\delta R\approx \delta C-\delta P-e^{-qT}\delta S
 +STe^{-qT}\delta q-KTe^{-rT}\delta r\qquad\text{(7)}.
$$

The residual-based conversion is a local common-volatility case, not a general gradient for two unequal IVs. For the paired estimator, let \(x_j\in\{S,K,T,r,q\}\), and let \(C_{x_j}(x,\sigma_C)\), \(P_{x_j}(x,\sigma_P)\) be each leg's BSM partial derivative at its own root; \(\nu_C=\nu(x,\sigma_C)\) and \(\nu_P=\nu(x,\sigma_P)\) are leg-specific vegas. Implicit differentiation gives

$$
dCPIV_{pp}=100\left[\frac{dC}{\nu_C}-\frac{dP}{\nu_P}
-\sum_j\left(\frac{C_{x_j}}{\nu_C}-\frac{P_{x_j}}{\nu_P}\right)dx_j\right]
=a^{\mathsf T}dz\qquad\text{(8)},
$$

where \(dz=(dC,dP,dS,dK,dT,dr,dq)\). Thus the first-order variance approximation is \(\operatorname{Var}(dCPIV_{pp})\approx a^{\mathsf T}\Sigma a\); when both legs share \(\sigma_0\), parity reduces this expression to the common-vega residual approximation. A numerical central-difference test of the implemented unequal-IV gradient is included in the test suite.

The illustrative perturbation design fixes \(S=K=100\), 30 days, \(r=0.03\), and \(q=0.01\). Gaussian call and put premium errors each have SD USD 0.02 per underlying unit, spot error has SD USD 0.02, and rate and effective-yield errors each have SD 0.001; strike and maturity errors are zero. The covariance matrix is diagonal except for the call–put premium-error covariance, set to \(\rho_{CP}(0.02)^2\) for \(\rho_{CP}\in\{0,0.5,0.9\}\). Thus spot, rate, and yield errors are mutually independent and independent of both premium errors. Each row aggregates 6,000 synthetic draws across seeds 20261012–20261014; all 6,000 inverted in these cases. Table 3 compares the first-order standard deviation from the full paired-IV gradient with the sample standard deviation from direct perturbation/inversion. It also reports an approximate normal-theory Monte Carlo standard error (MCSE) for the simulated sample SD, \(s/\sqrt{2(n-1)}\), with \(n=6{,}000\). This is a finite-draw precision diagnostic, not a formal test of the gradient approximation. These chosen scales are illustrations, not estimated market errors or uncertainty intervals.

**Table 3.** First-order and direct-perturbation CPIV standard deviations and approximate MCSE of the simulated SD under stated synthetic input-error scales (pp; 6,000 resolved draws per row). Difference = direct SD minus gradient SD.

| IV case \((\sigma_C,\sigma_P)\) | Price-error correlation | Gradient SD | Direct simulation SD | Difference | Approx. MCSE† | Resolved |
|:--|--:|--:|--:|--:|--:|--:|
| Equal (0.20, 0.20) | 0.0 | 0.3201 | 0.3242 | 0.0040 | 0.0030 | 6,000 |
| Equal (0.20, 0.20) | 0.5 | 0.2679 | 0.2699 | 0.0021 | 0.0025 | 6,000 |
| Equal (0.20, 0.20) | 0.9 | 0.2172 | 0.2168 | −0.0004 | 0.0020 | 6,000 |
| Unequal (0.24, 0.20) | 0.0 | 0.3201 | 0.3220 | 0.0018 | 0.0029 | 6,000 |
| Unequal (0.24, 0.20) | 0.5 | 0.2678 | 0.2685 | 0.0007 | 0.0025 | 6,000 |
| Unequal (0.24, 0.20) | 0.9 | 0.2172 | 0.2176 | 0.0004 | 0.0020 | 6,000 |

† Approximate normal-theory MCSE, computed as the direct sample SD divided by \(\sqrt{2(n-1)}\). The largest absolute difference is 1.37 times its approximate MCSE; this single simulated gap is not interpreted as a nonlinearity effect.

![Mean replicate-level Spearman rank correlation under synthetic Gaussian CPIV-space noise, by signal shape and universe size.](research/cpiv/generated/r10_release/cpiv_r10_rank_sensitivity.png){#fig-rank-sensitivity}

## 8. Interpretation and limits

**Table 4.** Operational diagnostic protocol proposed by this note; when required inputs or matching checks are unavailable, retain an unresolved status rather than infer a pass.

| Stage | Inputs | Check | Output/status | Action |
|:--|:--|:--|:--|:--|
| Contract matching | Underlying, option type, strike, expiry, exercise style, multiplier | Same pair definition and supported model | Matched / mismatch / unknown | Reject mismatch or analyze separately; do not pair unknown contracts |
| Timestamp validation | Option-leg and underlying timestamps; predeclared tolerance | Quote/spot synchronization | Synchronized / stale / unknown | Flag stale or unknown; do not silently substitute a spot |
| Price validation | Bid/ask or selected price, common inputs, European bounds | Finite inputs and bound admissibility | Valid / theoretical-bound violation / unresolved | Preserve failure status; never clip prices into bounds |
| IV inversion | Price, common contract inputs, solver bracket and iteration rule | Root exists; report convergence and repricing error | IV with solver status / unresolved | Retain status and diagnostics; distinguish bracket rejection from invalid quote |
| CPIV measurement | Paired IVs, units, common inputs, optional quote sides | Compute pp spread and quote-implied range; report leg and average vegas | Point estimate and, when defined, endpoint range | Report contract/multiplier convention and all four-endpoint denominator |
| Rank diagnostics | Cross-sectional CPIV values or intervals, declared universe | Pairwise non-overlap, sign resolution, inversions, membership, denominators | Resolved comparisons / unresolved partial order | Report resolved and unresolved counts; do not treat overlap as a wrong rank |

The exact identity is an algebraic diagnostic under a specified European BSM inversion, not an economic explanation. Since CPIV and \(R\) are linked through the same option prices and common inputs, observing both does not provide two independent signals. A forward inferred from the same call–put pair and then used to force that pair's parity residual toward zero would be circular. Independent synchronized inputs, multiple strikes with leave-one-pair-out checks, or an externally sourced forward are needed for a separate validation design.

Quote intervals are useful for showing whether signs or ranks survive the selected bid–ask endpoints. They do not account automatically for quote dependence, stale legs, discrete ticks, hidden liquidity, transaction costs, exercise features, or model choice. Hentschel (2003) and Muravyev and Pearson (2020) motivate attention to these issues, but their empirical estimates are not transplanted into this synthetic experiment.

The ranking exercise is a controlled stress test. Its signal vectors are prescribed, its noise scales are chosen for illustration, and its distributional assumptions are not calibrated to market data. The Wilson intervals capture finite simulation uncertainty conditional on those choices only. The experiment cannot estimate real-world ranking error, sign error, strategy turnover, profitability, or expected returns.

We do not claim a novel parity identity or an empirically superior estimator. The contribution is the explicit specification and implementation of an integrated diagnostic workflow, together with documented synthetic numerical stress tests. This version does not compare the workflow with raw-midpoint, minimally filtered, or synchronized-input CPIV using calibrated ground truth or market observations. It therefore establishes neither incremental decision value nor superior diagnostic performance. Comparative validation would require a declared target and calibration source, retained-data coverage, false-exclusion analysis, and ranking stability; it is outside this synthetic note.

The study contains no historical option chain, underlying return panel, market-wide positions or liquidation census, out-of-sample test, transaction-cost-adjusted portfolio, or causal design. It therefore makes no alpha claim and does not close an empirical-market-data gate. A market study would need a defined universe, synchronized quotes and underlying observations, contract and exercise-style controls, explicit filters, a held-out time period, and a preregistered analysis plan before its results could support market claims.

## 9. Reproducibility and declarations

The R10 companion package contains the source manuscript and code, tests, machine-readable CSV outputs, JSON run summary, figures, reproduction commands, and SHA-256 manifest. It records seeds, grid definitions, solver bounds, statuses, and denominators. Appendix A labels the HTML-only R8 illustration separately from the R10 results. The package is delivered locally, is not deposited in a public archive, and has no assigned redistribution license. The identity checker is a second code path written by the same author, not an independent replication by another researcher or formal peer review.

The common-map identity checker covers unequal-volatility European prices, an American-tree-origin put, stale source-spot quotes inverted at a different common spot, and admissible premium perturbations. Its recorded maximum residual-versus-integrated-vega gap is below \(1.2\times10^{-14}\) currency units across these four constructed cases. A separate 180-digit standard-library Decimal implementation audits the generated near-bound cases. Neither check is a proof; source, assumptions, inputs, outputs, and invocations are included for inspection and reruns.

**Funding:** No external funding.  
**Competing interests:** None.  
**Data and code availability:** Synthetic inputs and outputs accompany this manuscript in the delivery artifact. No real market data are included. The artifact is not publicly archived and has no reuse license.  
**Acknowledgements:** None declared.

## Appendix A. R8 baseline illustration (not an R10 result)

The HTML edition contains a fixed-seed, precomputed illustration of the earlier ten-name R8 baseline. Its slider selects among seven discrete, unequally spaced noise levels; it does not reprice options, invert implied volatility, or run Monte Carlo in the browser. At each level, the Monte Carlo summary is reported separately from one stored example draw, and all plotted values share one fixed symmetric axis. This presentation aid is not an R10 simulation and is not a substitute for the R10 CSV tables. The interactive widget appears only in the HTML edition.

<!-- CPIV_INTERACTIVE_WIDGET -->

## Appendix B. Reproduction commands

Requirements: Windows PowerShell and `uv` 0.11.8. `pyproject.toml` declares Python 3.12 or newer; this bundle was built and its 30 focused tests were run with Python 3.14.3. No other Python version was tested for this release. Install `uv` and a compatible Python interpreter before proceeding.

Run from the extracted companion-bundle root in Windows PowerShell. First verify the as-shipped package manifest before any commands that regenerate files:

```powershell
$manifestLines = Get-Content .\manifest.sha256
foreach ($line in $manifestLines) {
  $expected, $relative = $line -split '  ', 2
  $actual = (Get-FileHash -LiteralPath (Join-Path (Get-Location) $relative) `
    -Algorithm SHA256).Hash
  if ($actual -ne $expected) { throw "SHA-256 mismatch: $relative" }
}
"Verified $($manifestLines.Count) manifest entries."

uv sync --locked --no-install-project
$cpivOutputDir = "research/cpiv/generated/r10_release"
.\.venv\Scripts\python.exe -m research.cpiv.build_demo `
  --output $cpivOutputDir --replicates 2000
.\.venv\Scripts\python.exe -m research.cpiv.r10_diagnostics `
  --output $cpivOutputDir --replicates-per-seed 100
.\.venv\Scripts\python.exe -m research.cpiv.independent_bsm_crosscheck `
  --output "$cpivOutputDir/separately_coded_bsm_crosscheck.csv"
.\.venv\Scripts\python.exe -m research.cpiv.near_bound_decimal_audit `
  --input "$cpivOutputDir/iv_inversion_roundtrips.csv" `
  --output "$cpivOutputDir/near_bound_decimal_audit.csv" `
  --summary "$cpivOutputDir/near_bound_decimal_audit.json"
.\.venv\Scripts\python.exe -m pytest `
  tests/test_cpiv_r10_diagnostics.py `
  tests/test_cpiv_review_builder.py `
  tests/test_cpiv_educational_demo.py -q
```

## References

Black, F., & Scholes, M. (1973). The pricing of options and corporate liabilities. *Journal of Political Economy, 81*(3), 637–654. <https://doi.org/10.1086/260062>

Cox, J. C., Ross, S. A., & Rubinstein, M. (1979). Option pricing: A simplified approach. *Journal of Financial Economics, 7*(3), 229–263. <https://doi.org/10.1016/0304-405X(79)90015-1>

Cremers, M., & Weinbaum, D. (2010). Deviations from put-call parity and stock return predictability. *Journal of Financial and Quantitative Analysis, 45*(2), 335–367. <https://doi.org/10.1017/S002210901000013X>

Doran, J. S., Fodor, A., & Jiang, D. (2013). Call-put implied volatility spreads and option returns. *The Review of Asset Pricing Studies, 3*(2), 258–290. <https://doi.org/10.1093/rapstu/rat006>

Goncalves-Pinto, L., Grundy, B. D., Hameed, A., van der Heijden, T., & Zhu, Y. (2020). Why do option prices predict stock returns? The role of price pressure in the stock market. *Management Science, 66*(9), 3903–3926. <https://doi.org/10.1287/mnsc.2019.3398>

Hentschel, L. (2003). Errors in implied volatility estimation. *Journal of Financial and Quantitative Analysis, 38*(4), 779–810. <https://doi.org/10.2307/4126743>

Jarrow, R., & Rudd, A. (1983). *Option pricing*. Dow Jones-Irwin.

Merton, R. C. (1973). Theory of rational option pricing. *The Bell Journal of Economics and Management Science, 4*(1), 141–183. <https://doi.org/10.2307/3003143>

Muravyev, D., & Pearson, N. D. (2020). Options trading costs are lower than you think. *The Review of Financial Studies, 33*(11), 4973–5014. <https://doi.org/10.1093/rfs/hhaa010>

Sokolov, M. (2019). *A deeper look at the implied volatility spread as a predictor of stock returns* [Doctoral dissertation, University of Rochester]. University of Rochester Research Repository. <https://urresearch.rochester.edu/fileDownloadForInstitutionalItem.action?itemFileId=188460&itemId=35841>
