---
title: "Diagnosing Call–Put Implied-Volatility Spreads: Exact European-BSM Mapping and Synthetic Reliability Tests"
subtitle: "A measurement-focused quantitative methods note"
lang: en-US
date: "9 October 2026"
author: "Phirawit Jitnarong"
description-meta: "A reproducible diagnostic framework for CPIV measurement, European BSM inversion, quote intervals, and synthetic ranking stability."
---

**Affiliation:** Independent researcher  
**ORCID:** [0009-0006-8368-5309](https://orcid.org/0009-0006-8368-5309)  
**Contact:** [email removed]

## Thai summary

บทความนี้เสนอกรอบตรวจสอบความน่าเชื่อถือของ call–put implied-volatility spread (CPIV) ในฐานะตัวชี้วัด ไม่ใช่กลยุทธ์สร้างผลตอบแทน ภายใต้ European Black–Scholes–Merton (BSM) ที่ใช้ข้อมูลสัญญาเดียวกัน parity residual เท่ากับอินทิกรัลของ vega ระหว่าง implied volatility ของ call และ put ดังนั้น residual กับ CPIV จึงเป็นข้อมูลเชิงคณิตศาสตร์ที่เชื่อมโยงกัน ไม่ใช่หลักฐานยืนยันอิสระ งานจำลอง 720 กรณีแสดงว่าการประมาณแบบ linear ใช้ได้ดีในกรณีส่วนใหญ่ที่ vega คำนวณได้เสถียร แต่ความคลาดเคลื่อนเพิ่มในบางบริเวณ และ 96 กรณีถูกแยกเป็น unresolved เพราะ vega ต่ำกว่าค่าขั้นต่ำเชิงตัวเลข การทดสอบอันดับ 54,000 รอบใช้รูปแบบสัญญาณและ noise หลายชนิดเพื่อแสดงว่าอันดับขึ้นกับระยะห่างของสัญญาณและโครงสร้างความคลาดเคลื่อน ผลทั้งหมดเป็นข้อมูลสังเคราะห์ ไม่มี option chain, ผลตอบแทนจริง, การทดสอบ alpha หรือข้อสรุปเชิงตลาด

**คำสำคัญ:** call–put implied-volatility spread; put–call parity; implied volatility; vega; quote uncertainty; numerical stability; synthetic measurement study

## Abstract

This methods note specifies and stress-tests a diagnostic workflow for the measurement of the call–put implied-volatility spread (CPIV). For paired European Black–Scholes–Merton (BSM) options evaluated with common contract and market inputs, the put–call-parity residual equals the integral of call vega between the call and put implied volatilities. CPIV and that residual are therefore linked by construction; they are not independent confirmations. The note states price-bound and solver rules, quantifies the error in a local residual-to-CPIV approximation, reports quote-implied intervals, and compares two numerical schemes for an American put. Across 720 synthetic approximation cases, 624 meet a stated vega-resolution threshold; among those, median absolute approximation error is 0.000079 percentage points, the 95th percentile is 0.0872 points, and the maximum is 1.236 points. A separate 54,000-replicate synthetic ranking experiment shows that ranking reliability changes with signal spacing and noise structure. No historical option quotes, stock returns, market-wide positions, alpha estimates, or investment performance are analyzed. The results are methodological diagnostics, not market estimates or evidence of a profitable strategy.

**Keywords:** call–put implied-volatility spread; put–call parity; implied volatility; vega; quote uncertainty; numerical stability; synthetic measurement study

## 1. Introduction

The call–put implied-volatility spread is often discussed as a measure of relative option richness or as a predictor of returns. Those interpretations concern different objects. CPIV is a difference between two model-implied volatility estimates. A return spread is an outcome measured in a later period. An option-return spread is different again. A measurement study should establish what the input prices and inversion procedure identify before attaching an economic interpretation.

This note makes a narrow, operational contribution: it assembles an exact European-BSM identity, explicit inversion/failure rules, quote-implied intervals, input-sensitivity diagnostics, and a ranking stress design in one reproducible local implementation. It does not claim to introduce the parity–implied-volatility relationship or to establish a new economic predictor. Its four components are: (1) the exact identity linking CPIV to a parity residual through average vega; (2) price bounds, solver rules, and failure reporting; (3) synthetic tests of local-approximation error, quote intervals, carry, spot synchronization, and American exercise; and (4) ranking stress tests that vary signal spacing and measurement-noise structure.

The scope is intentionally limited. The synthetic tests establish properties of the specified pricing map and simulation designs. They do not establish how often these conditions occur in listed markets, whether CPIV forecasts stock or option returns, or whether a CPIV strategy earns returns after costs. No historical option-chain data or market-wide position census is used.

## 2. Related literature and the measurement question

Empirical work gives CPIV-like measures economic interpretations, but it studies outcomes that should not be conflated. Cremers and Weinbaum (2010) use implied-volatility differences between paired calls and puts and report a relation with subsequent stock returns. Their paper also examines stock-lending rebate rates directly; it should not be summarized as ignoring borrow conditions. Doran, Fodor, and Jiang (2013) distinguish stock-return predictability from returns on out-of-the-money call options and interpret option demand using their data. Those are separate outcome variables and empirical designs.

Related cross-market evidence need not be a CPIV result. Goncalves-Pinto et al. (2020) study discrepancies between stock-market prices and option-implied stock values. Their evidence is consistent with stock-price pressure being an important driver in their setting. That finding motivates caution when interpreting option-implied signals; it does not validate the synthetic diagnostics in this note.

Measurement error is central to implied-volatility work. Hentschel (2003) shows that plausible errors in option characteristics can translate into large implied-volatility errors, particularly away from the money, and discusses lower-bound truncation as a source of bias. Muravyev and Pearson (2020) show that option-trading-cost estimates depend on execution timing in their sample. Their estimates are not universal bid–ask discounts and are not applied as corrections here. Sokolov's (2019) doctoral dissertation develops a noisy-price interpretation of implied-volatility spreads and discusses American-option bounds with bid–ask spreads; it is useful background but is a dissertation, not a journal article.

The gap addressed here is narrower than those economic debates: given paired prices and a stated inversion contract, what is algebraically identified, what is numerically resolved, and how sensitive are descriptive rankings to plausible *synthetic* perturbations? The answer is a measurement protocol, not a causal or predictive claim.

## 3. Definitions and units

For a call and put with the same underlying, timestamp, strike \(K\), expiry \(T\), and pricing inputs, define

$$
CPIV_{pp}=100(\sigma_C-\sigma_P),
$$

where each \(\sigma\) is an annualized volatility in decimal units. The subscript \(pp\) denotes volatility percentage points: a decimal-volatility difference of 0.01 is one percentage point. It is not a percentage return.

With spot \(S\), continuously compounded rate \(r\), and continuous effective yield \(q\), define the European parity residual

$$
R=C-P-(Se^{-qT}-Ke^{-rT}),
$$

in underlying currency units per option contract, before any contract multiplier. A practical implementation must scale every term consistently by the contract multiplier. The yield \(q\) is an effective pricing input. It is not automatically a stock-borrow fee, funding charge, or crypto funding rate.

## 4. Exact identity and local approximation

Let \(C_{BSM}(\sigma)\) and \(P_{BSM}(\sigma)\) be European BSM call and put prices evaluated with the same \((S,K,T,r,q)\). European put–call parity holds at each common volatility, so

$$
\begin{aligned}
R
&=C_{BSM}(\sigma_C)-P_{BSM}(\sigma_P)
 -(Se^{-qT}-Ke^{-rT}) \\
&=C_{BSM}(\sigma_C)-C_{BSM}(\sigma_P) \\
&=\int_{\sigma_P}^{\sigma_C}\nu(u)\,du \\
&=(\sigma_C-\sigma_P)\,\bar{\nu},
\end{aligned}
$$

where \(\nu(u)=\partial C_{BSM}(u)/\partial u\) is vega per one full decimal-volatility unit and \(\bar{\nu}\) is the average vega over the interval. The integral is oriented: it is negative when \(\sigma_C<\sigma_P\). Consequently, for finite paired BSM inversions with positive vega, \(\operatorname{sign}(R)=\operatorname{sign}(CPIV)\). At equal implied volatilities both quantities are zero; the ratio form below is then undefined, although the integral identity remains valid.

If \(\nu\) is evaluated at a reference volatility \(\bar{\sigma}\), the first-order approximation is

$$
CPIV_{pp}\approx \frac{100R}{\nu(\bar{\sigma})}.
$$

When vega is reported per one volatility percentage point, \(\nu_{pp}=\nu/100\), the same approximation is \(CPIV_{pp}\approx R/\nu_{pp}\). The exact identity makes the connection between CPIV and the residual explicit; it does not make either measure an independent validation of the other. Nor does it say that a market residual must be caused by informational trading: asynchronous quotes, exercise style, carry inputs, price discreteness, and model mismatch can all matter.

The BSM formula is used here as an inversion map. The parity statement is a European no-arbitrage relation under the stated carry assumptions; it is not an assumption that observed prices were generated by BSM dynamics. The exact integral equality applies to BSM-implied prices with common inputs. Applying it to American options, stale spot, mismatched expiries, or different carry conventions requires additional terms and generally breaks this equality.

## 5. Inversion and numerical contract

For European prices, the admissible intervals used by the implementation are

$$
\max(Se^{-qT}-Ke^{-rT},0)\le C<Se^{-qT},
\qquad
\max(Ke^{-rT}-Se^{-qT},0)\le P<Ke^{-rT}.
$$

The implemented solver rejects non-finite or negative prices, prices within \(10^{-10}\) currency units of either relevant bound, and prices outside its configured volatility bracket. It uses bisection on \([10^{-8},5]\) in decimal volatility for 64 iterations. It does not clip a quote into the admissible interval. Outputs are repriced to record numerical error. A rejection is retained as a failure or unresolved case, not silently dropped from a market sample.

In the 120 generated call/put round-trip cases spanning five spot-to-strike ratios, four expiries, and three target volatilities, 104 prices inverted and repriced with maximum absolute repricing error \(2.84\times10^{-14}\) currency units. Sixteen theoretical prices were rejected by the configured near-bound rule because double-precision price values did not remain sufficiently separated from an admissible boundary. These are numerical-resolution failures in this design, not observed market-quote failures. Ten deliberately invalid-price checks were rejected; none was accepted. The threshold is an implementation choice, not a universal market-data filter.

## 6. Synthetic design

All input prices and signals are generated from fixed formulas. The reference implementation is `research/cpiv/build_demo.py`; the expanded R9 diagnostics are in `research/cpiv/r9_diagnostics.py`. The experiments use a 365-day year, continuous rates and yields, and USD-like synthetic price units. No network call or external market data is made.

### 6.1 Local-approximation grid

The grid crosses five \(S/K\) ratios (0.8, 0.9, 1.0, 1.1, 1.2), four maturities (7, 30, 90, 365 days), three reference volatilities (10%, 20%, 40%), six nonzero CPIV spreads (\(\pm0.5\), \(\pm1\), and \(\pm2\) points), and two carry pairs. This gives 720 cases. The residual benchmark is also computed by numerically integrating BSM vega, avoiding the direct price-subtraction cancellation that can occur when an option price is near its lower bound. Cases with reference vega below \(10^{-6}\) currency units per one full decimal-volatility unit are flagged unresolved. Results above that threshold describe a numerical grid, not a market-weighted distribution.

### 6.2 Carry, spot synchronization, and exercise style

The carry experiment generates matched European BSM prices at effective yields \(q\in\{-2,-1,0,1,2,5\}\%\) and then inverts with \(q=0\). This is a yield-misspecification experiment; it does not identify a borrow fee. The spot experiment generates matched ATM prices at \(S=K=100\), then inverts with spot displaced by \(-0.25\) to \(+0.25\) currency units. The American-put experiment fixes \(S=K=100\), 30 days, \(r=5\%\), \(q=0\), and \(\sigma=20\%\). It pairs an exact European BSM call with a numerically priced American put and compares CRR and equal-probability Jarrow–Rudd trees at 400, 800, 1,600, and 3,200 steps. Neither tree output is described as an exact American-option price.

### 6.3 Quote-implied intervals

For bid and ask prices that each admit a finite European IV under the same inputs, the quote-implied range is

$$
[\,IV(C_{bid})-IV(P_{ask}),\;IV(C_{ask})-IV(P_{bid})\,].
$$

The endpoints combine quote-side extremes. This range is not a statistical confidence interval, a probability statement, or an arbitrage bound. It also assumes that the four quotes are meaningfully synchronized and that the underlying, strike, expiry, multiplier, and carry inputs match. The simulation varies a symmetric half-spread over five levels for ten fictional pairs and records pair coverage, sign resolution, and the fraction of pairwise rankings whose intervals do not overlap.

### 6.4 Ranking stress experiment

The ranking experiment crosses universe sizes of 10 and 50, five prescribed signal shapes, six synthetic noise structures, and target CPIV-noise standard deviations of 0.25, 0.50, and 1.00 points. The signal shapes are equally spaced, clustered near zero, near-tied, two-cluster, and wide-tail vectors. Noise structures are bounded uniform, Gaussian, a 5% contaminated Gaussian mixture rescaled to the target variance, rank-dependent heteroskedastic Gaussian, call/put Gaussian errors with correlation 0.8, and a common shock shared across names. Three fixed seeds contribute 100 replicates each, for 300 replicates per cell and 54,000 total simulated rankings. Random draws are paired across noise-scale values within each seed and design cell.

For each replicate the code records pairwise inversion fraction, Spearman rank correlation, top/bottom 20% membership turnover, and sign accuracy. It also records the event rates for an exactly preserved full order and any top/bottom membership change. Wilson intervals summarize Monte Carlo uncertainty in these simulated event rates; they are not confidence intervals for a market population. Per-name top/bottom inclusion frequencies are supplied for the ten-name universe. None of the signal shapes or noise distributions is claimed to be market-realistic or calibrated.

## 7. Results

### 7.1 Local approximation and numerical resolution

Of 720 approximation cases, 624 pass the stated vega threshold and 96 are labeled unresolved. In the resolved subset, median absolute error is \(0.000079\) points, the 95th percentile is \(0.0872\) points, and the maximum is \(1.236\) points. The worst resolved case occurs at \(S/K=0.8\), 90 days, 10% reference volatility, and a two-point spread. These summaries weight grid cells equally by construction. They must not be read as expected error in a live option chain. The unresolved share and the maximum error show why a single local conversion should not be used without a vega and price-bound diagnostic.

![Absolute error of the local residual-to-CPIV approximation across resolved synthetic cases. The vega floor is applied before plotting; unresolved low-vega cases are counted separately.](research/cpiv/generated/revision_20261009_r9_proposed/cpiv_r9_local_approximation_error.png){#fig-local-error}

### 7.2 American-put scheme comparison

The supplied independent audit matches the CRR CPIV values to rounding across 400–3,200 steps. Jarrow–Rudd is a second finite-step scheme, not an exact American benchmark; the two schemes differ at finite resolution.

| Steps | CRR put | CRR CPIV (pp) | Jarrow–Rudd put | Jarrow–Rudd CPIV (pp) |
|--:|--:|--:|--:|--:|
| 400 | 2.112510 | −0.257018 | 2.114871 | −0.277758 |
| 800 | 2.112971 | −0.261065 | 2.114140 | −0.271341 |
| 1,600 | 2.113200 | −0.263082 | 2.113498 | −0.265699 |
| 3,200 | 2.113315 | −0.264085 | 2.113515 | −0.265841 |

![CRR and Jarrow–Rudd American-put synthetic convergence comparison.](research/cpiv/generated/revision_20261009_r9_proposed/cpiv_r9_american_convergence.png){#fig-american-convergence width=75%}

### 7.3 Carry and spot mismatch

With true \(q=5\%\) and inversion at \(q=0\), the generated CPIV is \(-3.58725\) points; at \(q=-2\%\), it is \(+1.43903\) points. At zero yield it is zero up to rounding. The direction changes with the omitted yield, as expected under this construction. This demonstrates sensitivity to the effective-yield input, not an empirical relationship between CPIV and stock lending.

When quotes use spot \(100\) and inversion uses stale spot \(100.10\), the synthetic CPIV is \(-0.87439\) points; a stale spot of \(99.90\) produces \(+0.87526\) points. The asymmetry comes from the nonlinear BSM map. These examples reinforce that a quote timestamp and the spot timestamp belong in the data contract.

### 7.4 Quote-implied interval width and rank resolution

All ten synthetic pairs remain invertible over the selected half-spread grid, but interval widths expand as the quote band widens. At a \$0.02 half-spread the median quote-implied width is 0.700 points and all pairwise interval orders are identified in this toy set. At \$0.10 the median width is 3.499 points and only 46.7% of pairwise interval orders are non-overlapping. At \$0.25, median width is 8.747 points and only 2.2% of pairwise orders are identified. These are properties of the ten constructed pairs and chosen price bands; the percentages are not market coverage estimates.

### 7.5 Ranking reliability depends on signal spacing

The stress test does not produce one universal “reliability” number. For ten equally spaced signals and Gaussian noise with target SD 0.50 points, mean pairwise inversion fraction is 17.6%, mean Spearman correlation is 0.797, and top/bottom membership turnover is 36.7%. For ten near-tied signals at the same noise scale, those values are 49.5%, 0.015, and 79.2%. In the 300 draws for each of these cells, no full ordering was preserved; the Wilson 95% upper bound is 1.26%, not zero probability. Near-tied sign accuracy is approximately 50%, as expected when noise dominates the prescribed signal.

| Universe and prescribed signals | Noise SD (pp) | Mean inversion fraction | Mean Spearman \(\rho\) | Top/bottom turnover | Sign accuracy | Exact orders observed / 300 |
|:--|--:|--:|--:|--:|--:|--:|
| 10, equally spaced | 0.50 | 0.176 | 0.797 | 0.367 | 0.826 | 0 |
| 10, near-tied | 0.50 | 0.495 | 0.015 | 0.792 | 0.504 | 0 |
| 50, equally spaced | 0.50 | 0.212 | 0.771 | 0.402 | 0.807 | 0 |
| 50, near-tied | 0.50 | 0.492 | 0.023 | 0.798 | 0.507 | 0 |

The comparison changes when signals are farther apart or the noise is common to every name. A common additive shock shifts levels but leaves within-sample ordering unchanged by construction. That case is included to make the dependence on error structure visible, not to suggest that market errors are common additive shocks. Full cell-level metrics, Wilson intervals, and per-name inclusion probabilities are in the companion CSV files.

The supplied independent audit also recalculated the original ten-name baseline using a separate implementation. Its no-inversion and membership-change percentages are close to, but not identical to, the R8 results at target noise SDs 0.35, 0.50, 1.00, and 2.00 points. Because RNG and draw ordering differ, this is an independent numerical cross-check rather than an exact replay of the original random stream. The differences are documented in the audit report; they do not establish a code defect or prove equivalence of all implementations.

### 7.6 Illustrative uncertainty budget

For \(R=C-P-Se^{-qT}+Ke^{-rT}\), a first-order input perturbation is

$$
\delta R\approx \delta C-\delta P-e^{-qT}\delta S
 +STe^{-qT}\delta q-KTe^{-rT}\delta r,
\qquad
\operatorname{Var}(\delta R)\approx g^{\mathsf T}\Sigma g,
\qquad
\delta CPIV_{pp}\approx \frac{100\,\delta R}{\nu(\bar{\sigma})}.
$$

The vector \(g\) contains the displayed derivatives and \(\Sigma\) must contain the relevant error variances and covariances. In the companion CSV, price, spot, rate, and yield error scales are illustrative inputs; the call/put quote-error correlation is varied. The resulting delta-method scale is not an estimated standard error, confidence interval, or market uncertainty estimate. Systematic carry or contract mismatch should be reported separately from stochastic quote error and from American-model error.

![Mean Spearman rank correlation under synthetic Gaussian noise, by signal shape and universe size.](research/cpiv/generated/revision_20261009_r9_proposed/cpiv_r9_rank_sensitivity.png){#fig-rank-sensitivity}

## 8. Interpretation and limits

The exact identity is an algebraic diagnostic under a specified European BSM inversion, not an economic explanation. Since CPIV and \(R\) are linked through the same option prices and common inputs, observing both does not provide two independent signals. A forward inferred from the same call–put pair and then used to force that pair's parity residual toward zero would be circular. Independent synchronized inputs, multiple strikes with leave-one-pair-out checks, or an externally sourced forward are needed for a separate validation design.

Quote intervals are useful for showing whether signs or ranks survive the selected bid–ask endpoints. They do not account automatically for quote dependence, stale legs, discrete ticks, hidden liquidity, transaction costs, exercise features, or model choice. Hentschel (2003) and Muravyev and Pearson (2020) motivate attention to these issues, but their empirical estimates are not transplanted into this synthetic experiment.

The ranking exercise is a controlled stress test. Its signal vectors are prescribed, its noise scales are chosen for illustration, and its distributional assumptions are not calibrated to market data. The Wilson intervals capture finite simulation uncertainty conditional on those choices only. The experiment cannot estimate real-world ranking error, sign error, strategy turnover, profitability, or expected returns.

This version does not compare the proposed diagnostics against raw-midpoint CPIV, minimally filtered CPIV, or synchronized-input CPIV using calibrated ground truth or market observations. It therefore does not establish incremental decision value, superior diagnostic performance, or novelty relative to prior work. The contribution claimed here is limited to specifying and implementing the combined diagnostics and exposing their assumptions and outputs. A comparative validation must report both stability and retained-data coverage, define a target and calibration source in advance, and evaluate false exclusions as well as ranking changes; that study is outside this synthetic note.

The study contains no historical option chain, underlying return panel, market-wide positions or liquidation census, out-of-sample test, transaction-cost-adjusted portfolio, or causal design. It therefore makes no alpha claim and does not close an empirical-market-data gate. A market study would need a defined universe, synchronized quotes and underlying observations, contract and exercise-style controls, explicit filters, a held-out time period, and a preregistered analysis plan before its results could support market claims.

## 9. Reproducibility and declarations

The companion artifact contains the source manuscript, diagnostic code, machine-readable CSV outputs, JSON run summary, and figure files. The R8 fixed-seed interactive illustration is separately identified from the R9 54,000-draw sensitivity experiment. The generated files record seeds, grid definitions, solver bounds, and failure counts. The manuscript does not point to a public archive; no redistribution license has been assigned. Reproducibility is therefore local to the delivered artifact and should not be described as public or independently executable until the package is archived with explicit reuse terms.

**Funding:** No external funding.  
**Competing interests:** None.  
**Data and code availability:** Synthetic inputs and outputs accompany this manuscript in the delivery artifact. No real market data are included. The artifact is not publicly archived and has no reuse license.  
**Acknowledgements:** None declared.

The standalone HTML version contains a fixed-seed, precomputed illustration of the earlier ten-name R8 baseline. Its slider selects among seven discrete, unequally spaced noise levels; it does not reprice options, invert implied volatility, or run Monte Carlo in the browser. At each level, the Monte Carlo summary is reported separately from one stored example draw, and all plotted values share one fixed symmetric axis. This presentation aid does not run the R9 simulation and is not a substitute for the attached CSV tables.

<!-- CPIV_INTERACTIVE_WIDGET -->

## References

Black, F., & Scholes, M. (1973). The pricing of options and corporate liabilities. *Journal of Political Economy, 81*(3), 637–654. <https://doi.org/10.1086/260062>

Cox, J. C., Ross, S. A., & Rubinstein, M. (1979). Option pricing: A simplified approach. *Journal of Financial Economics, 7*(3), 229–263. <https://doi.org/10.1016/0304-405X(79)90015-1>

Cremers, M., & Weinbaum, D. (2010). Deviations from put-call parity and stock return predictability. *Journal of Financial and Quantitative Analysis, 45*(2), 335–367. <https://doi.org/10.1017/S002210901000013X>

Doran, J. S., Fodor, A., & Jiang, D. (2013). Call-put implied volatility spreads and option returns. *The Review of Asset Pricing Studies, 3*(2), 258–290. <https://doi.org/10.1093/rapstu/rat006>

Goncalves-Pinto, L., Grundy, B. D., Hameed, A., van der Heijden, T., & Zhu, Y. (2020). Why do option prices predict stock returns? The role of price pressure in the stock market. *Management Science, 66*(9), 3903–3926. <https://doi.org/10.1287/mnsc.2019.3398>

Hentschel, L. (2003). Errors in implied volatility estimation. *Journal of Financial and Quantitative Analysis, 38*(4), 779–810. <https://doi.org/10.2307/4126743>

Merton, R. C. (1973). Theory of rational option pricing. *The Bell Journal of Economics and Management Science, 4*(1), 141–183. <https://doi.org/10.2307/3003143>

Muravyev, D., & Pearson, N. D. (2020). Options trading costs are lower than you think. *The Review of Financial Studies, 33*(11), 4973–5014. <https://doi.org/10.1093/rfs/hhaa010>

Sokolov, M. (2019). *A deeper look at the implied volatility spread as a predictor of stock returns* [Doctoral dissertation, University of Rochester]. University of Rochester Research Repository. <https://urresearch.rochester.edu/fileDownloadForInstitutionalItem.action?itemFileId=188460&itemId=35841>
