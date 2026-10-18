---
title: "Diagnosing Call–Put Implied-Volatility Spreads: Exact European-BSM Mapping and Synthetic Reliability Tests"
subtitle: "A measurement-focused quantitative methods note"
lang: en-US
date: "18 October 2026"
author: "Phirawit Jitnarong"
description-meta: "A reproducible diagnostic framework for CPIV measurement, European BSM inversion, quote intervals, and synthetic ranking stability."
---

**Affiliation:** Independent researcher  
**ORCID:** [0009-0006-8368-5309](https://orcid.org/0009-0006-8368-5309)  
**Contact:** nxme176@gmail.com

## Thai summary

บทความนี้เสนอขั้นตอนตรวจวัด call–put implied-volatility spread (CPIV) โดยเริ่มจากอัตลักษณ์ภายใต้ European BSM: parity residual เท่ากับอินทิกรัลของ vega ระหว่าง implied volatility สองขาเมื่อใช้ inputs ร่วมกันและทั้งสองรากมีอยู่ อัตลักษณ์นี้เชื่อม CPIV กับ residual โดยโครงสร้าง ไม่ใช่หลักฐานยืนยันอิสระ ในตัวอย่างสังเคราะห์ที่กำหนด tick สมมติ \(t=0.01\) การช็อกราคาแบบเต็ม tick \((\pm t)\) ทำให้ ATM IV เปลี่ยนสูงสุด 0.087469 จุดเปอร์เซ็นต์ ส่วนการช็อกครึ่ง tick \((\pm t/2)\) ให้ 0.043735 จุด ดังนั้นที่ tolerance 0.05 จุด ผลจึงต่างกันตาม convention ทั้งสองขาในกรณี deep มี OTM-equivalent time value ประมาณ \(3.178\times10^{-6}\) ซึ่งต่ำกว่า tick; ช็อกราคาเพิ่ม \(t\) และ \(t/2\) ทำให้ IV เปลี่ยนด้านที่มีรากประมาณ 7.0717 และ 5.9264 จุดตามลำดับ ขณะที่ช็อกด้านลบไม่มีราก กรณีนี้จึง unresolved ทั้งสอง convention การคลาดเคลื่อนของ carry/spot ในกรณีสังเคราะห์สร้าง CPIV ที่เปลี่ยนได้หลายจุดเปอร์เซ็นต์ การประมาณ local รอบจุดกึ่งกลางมี error เพิ่มใกล้กำลังสามของขนาด spread ในกริดที่ออกแบบให้สมมาตร แต่เมื่อเลื่อน reference volatility เพียง 1 จุด volatility ค่า median error เพิ่มจาก 0.0000786 เป็น 0.04238 pp และ p95 เป็น 1.4767 pp การเปรียบเทียบเวิร์กโฟลว์แบบสังเคราะห์ที่ผู้เขียนรันเองพบว่า identification screen ไม่ให้การจัดลำดับผิดในคู่ที่ตัดสินได้ แต่ทิ้งคู่ที่มีลำดับจริงจำนวนมากไว้โดยไม่ตัดสิน การลดลงของการจัดลำดับผิดเทียบกับการจัดอันดับจาก midpoint ดิบมีขนาดเล็ก (0.08–0.18 จุดเปอร์เซ็นต์ของคู่ที่ตัดสินได้) จึงเป็นการแลกระหว่างความครอบคลุมกับความผิดพลาด ไม่ใช่หลักฐานว่าดีกว่าบนใบเสนอราคาจริง ผลทั้งหมดมาจากการทดลองสังเคราะห์ ไม่ใช่ข้อมูล option-chain จริง ผลตอบแทน การทดสอบ alpha หรือข้อสรุปเชิงตลาด

**คำสำคัญ:** call–put implied-volatility spread; put–call parity; implied volatility; vega; quote uncertainty; numerical stability; synthetic measurement study

\newpage

## Abstract

This methods note specifies a diagnostic workflow for the call–put implied-volatility spread (CPIV). Under a common European Black–Scholes–Merton (BSM) map, the parity residual equals the integral of vega between the two leg-specific implied-volatility roots, so CPIV and the residual are linked by construction and do not provide independent confirmation. For a hypothetical price tick of 0.01, the synthetic at-the-money, 30-day, 20%-volatility example has a worst-direction IV displacement of 0.087 percentage points under full-tick shocks and 0.044 pp under half-tick shocks. At an illustrative 0.05-point threshold, the first is outside and the second within tolerance, so the classification depends on the declared shock convention. A deep synthetic pair, whose OTM-equivalent time values lie below the tick, remains unresolved under both conventions. A one-basis-point forward mismatch corresponds locally to 0.087469 CPIV points in the ATM example; this conversion is configuration-specific. Carry and spot-mismatch scenarios move CPIV by several points, and a centered approximation grid shows error growing roughly as the cube of the displacement. In an author-run synthetic cross-section with known truth, an identification screen made no wrong-order decisions where it decided, but left most truly ordered pairs undecided; its reduction in wrong-order decisions relative to raw-midpoint ranking was 0.08–0.18 percentage points of decided pairs in the cells where the claim rule credits a benefit. These are synthetic numerical and design checks, not independent replication, and they contain no market quotes, returns, or investment performance.

**Keywords:** call–put implied-volatility spread; put–call parity; implied volatility; vega; quote uncertainty; numerical stability; synthetic measurement study

## 1. Introduction

The call–put implied-volatility spread is often discussed as a measure of relative option richness or as a predictor of returns. Those interpretations concern different objects. CPIV is a difference between two model-implied volatility estimates. A return spread is an outcome measured in a later period. An option-return spread is different again. A measurement study should establish what the input prices and inversion procedure identify before attaching an economic interpretation.

This note makes a narrow operational contribution: it specifies and implements a diagnostic workflow that connects the common-map identity, input validation, inversion statuses, quote-implied ranges, separately reported price-resolution sensitivities, local approximation, and ranking stability. It does not claim a novel parity identity or an empirically superior estimator. Its contribution is the explicit workflow, the accompanying synthetic numerical stress tests, and a synthetic comparison that shows a coverage–error trade-off for the identification screen (Section 7.9); the staged protocol appears in Table 10.

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

Let \(C_{BSM}(\sigma)\) and \(P_{BSM}(\sigma)\) be European BSM call and put prices evaluated with the same \((S,K,T,r,q)\) (Black & Scholes, 1973; Merton, 1973). European put–call parity holds at each common volatility, so

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
\bar{\nu}(x)=\int_0^1\nu\!\left(x,\sigma_P+\lambda(\sigma_C-\sigma_P)\right)d\lambda\qquad\text{(4)}.
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

The round-trip design contains 60 contract configurations and 120 option-leg prices (five \(S/K\) ratios × four expiries × three target IVs × two legs). In the recorded run, 104 prices inverted; 15 were rejected by the configured absolute near-bound guard and one binary64 price fell outside the bounds computed by the binary64 solver. A separate 180-digit Decimal code path recomputed the 16 intended BSM prices: all 16 exact prices lie strictly inside the high-precision bounds, their target roots lie inside the solver bracket, and all are within the configured \(10^{-10}\) absolute guard. Comparing the stored binary64 prices against those 180-digit bounds gives 12/16 strictly inside; this is a different comparison from the solver's binary64-bound classifier and must not be labeled as its strict-inside count. Replaying the solver-bound classification yields 10 strictly interior near-bound guard cases, five prices exactly equal to a binary64 bound and caught by the guard, and one strict binary64-bound violation. The three mutually exclusive groups are tabulated in Section 7.8. This is a classification of this generated numerical design, not a general floating-point failure rate. Among the 104 successful inversions, maximum absolute repricing error was \(2.84\times10^{-14}\) currency units and maximum/p95 absolute IV-recovery error was \(1.19\times10^{-11}/5.41\times10^{-13}\) in decimal volatility. Ten deliberately invalid-price probes were rejected and none accepted. These are synthetic outcomes, not market-quote failure rates; the threshold remains an implementation setting, not a universal filter.

\newpage

## 6. Synthetic design

All input prices and signals are generated from fixed formulas. Appendix B gives project-checkout commands for regenerating the synthetic demonstration and diagnostic analyses. A separate standard-library identity checker imports neither of the primary implementations. It is a distinct code path by the same author, not an independent human replication or a high-precision oracle. The experiments use a 365-day year, continuous rates and yields, and underlying-currency price units. No network call or external market data is used.

### 6.1 Local-approximation grid

The 720-cell grid fixes \(K=100\) and crosses \(S/K\in\{0.8,0.9,1.0,1.1,1.2\}\), expiries \(T\in\{7,30,90,365\}\) days, midpoint reference volatilities \(\sigma_0\in\{0.10,0.20,0.40\}\), six nonzero target spreads \(d_{pp}\in\{-2,-1,-0.5,0.5,1,2\}\), and carry pairs \((r,q)=(0,0),(0.05,0.02)\). For each cell, \(S=100(S/K)\), \(d=d_{pp}/100\), \(\sigma_C=\sigma_0+d/2\), and \(\sigma_P=\sigma_0-d/2\). Thus the midpoint, rather than one endpoint, is the designated reference. For smooth vega \(\nu\), symmetric integration around \(\sigma_0\) gives \(R/\nu(\sigma_0)=d+(d^3/24)\nu''(\sigma_0)/\nu(\sigma_0)+O(d^5)\), with \(d\) measured in decimal-volatility units. Odd derivatives cancel, leaving a leading cubic approximation error; this design therefore evaluates the local approximation at its stipulated midpoint rather than at an arbitrary reference.

Composite Simpson quadrature uses 2,000 even subintervals as the primary numerical integral; the output also records 1,000-versus-2,000 and 2,000-versus-4,000 differences, plus the gap between direct price residual and integrated vega. These are separate numerical diagnostics. Local-approximation error is separately calculated against the target CPIV spread. It is not a solver or quadrature error. For each cell, midpoint and both endpoint vegas are reported. The baseline absolute-vega guard flags a cell when absolute midpoint vega is below \(10^{-6}\) currency units per decimal IV; it is a numerical filter, not a measurement-resolution tolerance. In the nominal-scale experiment, normalized midpoint vega is \(\tilde{\nu}_{mid}=\nu_{mid}/\max(Se^{-qT},Ke^{-rT})\): the numerator is currency units per decimal IV and the denominator is the discounted underlying-currency scale per underlying unit, so this ratio is normalized per decimal-IV unit. Each scale factor is evaluated over 120 baseline configurations (five \(S/K\) ratios × four expiries × three reference-IV levels × two carry pairs). The absolute guard resolves 104/120, 104/120, and 106/120 configurations at nominal scale factors 0.01, 1, and 100, respectively. These are grid diagnostics, not a market-weighted distribution or general reliability rule. In the local-approximation grid, midpoint volatility and the other non-spread inputs stay fixed across each configuration's six spread cells, so normalized midpoint vega is spread-invariant; its summary therefore counts each unique non-spread configuration once.

### 6.2 Carry, spot synchronization, and exercise style

The carry experiment uses \(S=K=100\), 30 days to expiry, \(r=0\), and volatility 20%; it generates matched European BSM prices at effective yields \(q\in\{-2,-1,0,1,2,5\}\%\) and then inverts each pair with \(q=0\). The spot experiment uses the same spot, strike, maturity, and volatility, with \(r=q=0\): prices are generated at spot 100 and inverted with spot displaced by \(-0.25,-0.10,-0.05,-0.02,0.02,0.05,0.10,0.25\) currency units. Neither experiment identifies a borrow fee or an empirical timestamp effect.

**Proposition (fixed-price common-map input sensitivity).** Hold observed call and put prices \(C^*,P^*\) fixed and suppose both have finite European-BSM implied-volatility roots \(\sigma_C(x),\sigma_P(x)\) under common inputs \(x=(S,K,T,r,q)\), with positive leg vegas \(\nu_C,\nu_P\) per decimal-volatility unit. Implicit differentiation gives the exact local derivatives

$$
\frac{\partial CPIV_{pp}}{\partial S}
=100e^{-qT}\left[-\frac{N(d_{1C})}{\nu_C}
+\frac{N(d_{1P})-1}{\nu_P}\right],
$$

$$
\frac{\partial CPIV_{pp}}{\partial q}
=100TS e^{-qT}\left[\frac{N(d_{1C})}{\nu_C}
+\frac{N(-d_{1P})}{\nu_P}\right],
$$

where \(d_{1C}\) and \(d_{1P}\) are evaluated at their respective implied-volatility roots and \(T\) is in years. These are local derivatives for fixed premiums, not finite-change identities. Under the same continuous-carry convention, an independently observed forward implies \(q=r-\log(F/S)/T\), equivalently \(F=S\exp((r-q)T)\). The forward and spot must be synchronized and independently sourced; inferring a forward from the same call–put pair would make this check circular.

For a predeclared CPIV tolerance \(\tau\) in percentage points, the local conversion is \(\partial CPIV_{pp}/\partial\log F=-(1/T)\partial CPIV_{pp}/\partial q\). In the synthetic ATM, 30-day, 20%-IV example, a 1-basis-point relative-forward discrepancy corresponds to 0.087469 CPIV points; equivalently, a 1% forward discrepancy corresponds locally to 8.7469 CPIV points. Thus a 1-point CPIV tolerance maps to approximately 11.4326 basis points, or 0.114326% of the forward. This conversion depends on moneyness, maturity, and both implied roots; it is a local diagnostic, not a universal acceptance threshold. Larger discrepancies should be evaluated by exact re-inversion rather than extrapolating the tangent.

The American-put comparison fixes \(S=K=100\), 30 days, \(r=5\%\), \(q=0\), and \(\sigma=20\%\); it pairs a European BSM call with an American put valued by CRR and an equal-probability Jarrow–Rudd tree. CRR uses \(u=e^{\sigma\sqrt{\Delta t}}\), \(d=1/u\), and risk-neutral probability \(p=(e^{(r-q)\Delta t}-d)/(u-d)\), with early exercise at each node. The implemented Jarrow–Rudd variant uses \(u=e^{(r-q-\sigma^2/2)\Delta t+\sigma\sqrt{\Delta t}}\), \(d=e^{(r-q-\sigma^2/2)\Delta t-\sigma\sqrt{\Delta t}}\), and probability 1/2, also with early exercise. Both are compared at 400, 800, 1,600, 3,200, and 6,400 steps. A successive-grid CPIV change below 0.001 percentage points is a descriptive audit threshold, not a formal error bound or preregistered stopping rule; the two schemes are not asserted to be exact American benchmarks (Cox et al., 1979; Jarrow & Rudd, 1983).

### 6.3 Quote-implied intervals

When all four bid/ask endpoint prices admit finite European IVs under the same inputs, the quote-implied range is

$$
100\left[IV(C_{bid})-IV(P_{ask}),\;IV(C_{ask})-IV(P_{bid})\right]\quad\text{(6)}.
$$

The output is in volatility percentage points. Endpoints combine quote-side extremes; the interval is not statistical coverage, a confidence interval, probability statement, or arbitrage bound. If a quote endpoint lies at a pricing boundary and has no finite positive-IV root (as can happen with a zero bid), retain any valid endpoint as a one-sided bound, mark the pair incomplete, and do not impute a missing endpoint or discard the pair. Such observations contribute unresolved partial-order comparisons unless their one-sided bounds alone establish an order. All ten synthetic pairs use \(S=K=100\), 30 days to expiry, and \(r=q=0\); put IV is 20% and call IVs run from 16% through 25%. A symmetric premium half-spread of USD 0.01, 0.02, 0.05, 0.10, or 0.25 per underlying unit is added/subtracted before inversion. The code reports the four-endpoint-invertible fraction out of 10 pairs, sign-resolved count/fraction among those valid pairs, median interval width in points, and strict non-overlap counts divided both by eligible valid unordered pairs and all 45 possible unordered pairs. Touching endpoints count as overlap. Incomplete pairs remain in the total denominator and are not silently interpreted as ties.

### 6.4 Ranking stress experiment

The ranking experiment crosses \(n\in\{10,50\}\), five signal shapes, eight synthetic noise structures, and three configured scales (0.25, 0.50, 1.00 pp). For \(i=0,\ldots,n-1\), let \(x_i=-1+2i/(n-1)\), in CPIV points. The shapes are: equally spaced \(x_i\); clustered near zero \(x_i^3\); near-tied \(0.03x_i\); two clusters \(-1+0.02i/n\) for \(i<n/2\) and \(1+0.02i/n\) otherwise; and the concave-magnitude transform \(g(x_i)=\operatorname{sign}(x_i)\sqrt{|x_i|}\). This deterministic transform remains supported on \([-1,1]\); it is not a heavy-tailed distribution.

Noise is added directly in CPIV space, not option-price space. The families are: (1) uniform \(U(-\sqrt{3}s,\sqrt{3}s)\); (2) Gaussian \(N(0,s^2)\); (3) a 5% contaminated Gaussian whose contaminant SD is five times the base SD and whose theoretical mixture variance is normalized to \(s^2\); (4–6) Gaussian heteroskedastic noise with factors \(f_i=0.5+i/(n-1)\), normalized by \(\sqrt{n^{-1}\sum_i f_i^2}\), respectively increasing, decreasing, or randomly permuted across names in each replicate; (7) Gaussian call/put leg errors each with marginal SD \(s\) and correlation 0.8, with CPIV noise defined as call error minus put error, giving theoretical paired SD \(s\sqrt{2(1-0.8)}=s\sqrt{0.4}\); and (8) one Gaussian additive CPIV shock shared identically by every name, included as a ranking-invariance control rather than a market-error model. Therefore the same configured scale does not imply the same paired CPIV SD in family 7. Three fixed seeds (20261009, 20261010, 20261011) contribute 100 replicates each. The total is \(2\times5\times8\times3\times300=72{,}000\) synthetic rankings. Within each universe–signal-shape–noise-family design and seed, the same underlying random draws are reused across scale values; results are compared as paired replicate differences.

For a replicate, the inversion fraction is the number of discordant unordered pairs divided by \(n(n-1)/2\), with index order breaking exact ties. Spearman's \(\rho=1-6\sum_i d_i^2/[n(n^2-1)]\) uses the resulting tie-broken ranks. Let \(k=\lfloor n/5\rfloor\); top/bottom turnover is \(1-(|L\cap L'|+|B\cap B'|)/(2k)\), the mean of long- and bottom-set missing-member fractions. Sign accuracy is \(n^{-1}\sum_i\mathbf{1}[(x_i>0)=(y_i>0)]\); exact zero is treated as nonpositive. The code also records exact full-order preservation and any extreme-quintile membership change.

Continuous metric means and their normal Monte Carlo intervals use each replicate as the observation; names and within-replicate pairs are not treated as independent observations. Adjacent noise-scale contrasts use paired replicate differences, with paired MCSE/intervals. Wilson intervals are reported for simulated event rates only. These intervals quantify finite simulation variation conditional on the chosen generator and seeds; they are not market confidence intervals. Per-name inclusion probabilities are supplied for the ten-name universe. None of the vectors or noise distributions is asserted to be market-realistic or calibrated.

### 6.5 Price identification and tolerance by source

Price discretization, quote width, and floating-point scale are distinct inputs and are not combined into one \(\delta P\) or treated as a standard deviation. For one option leg, let \(P\) be its synthetic premium, \(\nu_{dec}\) its BSM vega per decimal IV, and \(\nu_{pp}=\nu_{dec}/100\) its vega per IV percentage point. The reported first-order sensitivities are

$$
\delta IV_{tick,pp}\approx\frac{t}{\nu_{pp}},\qquad
\delta IV_{spread,pp}\approx\frac{h}{\nu_{pp}},\qquad
\delta IV_{roundoff,pp}\approx\frac{u|P|}{\nu_{pp}},
\qquad u=2^{-53}.
$$

Here \(t\) is a parameterized full price-tick step and \(h\) is a quote half-spread, both in price units per underlying unit. Their numerical levels are hypothetical scenarios, not claims about any market. A full-tick sensitivity applies price shocks \(\pm t\); a nearest-tick rounding-error sensitivity applies \(\pm t/2\). The half-tick results are reported separately and do not silently replace the full-tick convention. The roundoff row uses the IEEE-754 binary64 unit roundoff as an illustrative relative price perturbation; it is not a rigorous bound on total pricing or inversion error. The three sensitivities remain separate; they are neither summed nor collapsed by a maximum rule.

These derivatives are local. For tick and half-spread scenarios, the output also attempts exact IV inversion for both legs under positive and negative price shocks when each shocked price remains inside the configured European bounds. Define the leg-specific OTM-equivalent time values as \(X_C=C-\max(Se^{-qT}-Ke^{-rT},0)\) and \(X_P=P-\max(Ke^{-rT}-Se^{-qT},0)\). With \(A=Se^{-qT}-Ke^{-rT}\), the parity residual defined in Section 4 satisfies \(X_C-X_P=C-P-A=R\); the two values are equal only when \(R=0\), not in general when CPIV is nonzero. The pair-level screen is therefore \(\min(X_C,X_P)\ge t\), rather than assuming equal leg values or screening the in-the-money premium. Define the pair as **identified** under the full-tick finite-shock design only when this minimum reaches the declared tick \(t\) and all four shocked prices \(C\pm t\) and \(P\pm t\) have finite roots. For quote half-spread scenarios, the declared 0.01 reference tick is used for the same minimum-value screen; the exact shocks are applied separately to each leg. This is distinct from precision. For a predeclared tolerance \(\tau_{IV}\) in volatility percentage points, define the maximum available absolute IV displacement across legs and shock directions; an identified pair is **within \(\tau_{IV}\)** only if every required finite-shock displacement is no greater than \(\tau_{IV}\). This is the worst-direction displacement from the base IV, not the full two-sided interval width. A missing root or a pair minimum below the applicable reference tick is unresolved and does not qualify as within any tolerance. Nearest-tick rounding results use shocks of half a declared tick on each leg and are reported as a separate sensitivity; they do not alter the full-tick screen. Failed inversions are not clipped or converted into finite intervals. Roundoff-scale exact inversion is omitted because it is below the meaningful resolution of this solver. The baseline absolute-vega guard (\(\nu_{dec}\ge10^{-6}\)) is reported separately and is not used to certify identification or precision.

The synthetic grid reuses the 120 combinations of \(S/K\), expiry, reference IV, and carry specified in Section 6.1. Each call and put is priced at the same reference IV to isolate price-to-IV sensitivity, so \(R=0\) and \(X_C=X_P\) in these particular base cases. Default tick scenarios are 0.0001, 0.001, 0.01, and 0.1 price units; half-spread scenarios are 0.01, 0.02, 0.05, 0.10, and 0.25. The source code accepts other positive tick and half-spread values. Tick rows compare \(\min(X_C,X_P)\) with the row-specific tick; half-spread and roundoff rows compare the same minimum with the 0.01 reference tick (or the smallest configured tick if 0.01 is absent). The CSV keeps call and put legs separate. Figure 4 reports identification and whether the maximum worst-direction absolute finite-shock displacement is within the illustrative \(\tau_{IV}=0.10\) pp threshold; Figure 5 reports the magnitude of exact finite changes. Both figures preserve leg-level machine-readable rows in the generated output.

## 7. Results

### 7.1 Local approximation and numerical resolution

Of the 720 grid cells, 624 pass the configured absolute midpoint-vega guard and 96 do not. The midpoint-reference approximation is evaluated only on the 624 passing cells, with each cell equally weighted. Put-endpoint and call-endpoint vega errors remain separate, each with 624 observations; their median, nearest-rank p95, and maximum are equal because the absolute call-endpoint error at spread \(+d\) matches the absolute put-endpoint error at spread \(-d\) for each reflected configuration, not because the two endpoint errors match within a cell. The midpoint is specified by construction and makes this a favorable centered-reference diagnostic, not evidence that a market-observed reference will be centered. The worst centered-grid error occurs at \(S/K=0.8\), 90 days, 10% reference IV, and a two-point spread. Table 1 reports the error by spread and under deliberately shifted reference volatilities; these are equally weighted synthetic diagnostics, not estimates of live-chain error.

For a smooth vega function, midpoint symmetry removes odd-derivative terms from the integral, leaving the leading local-approximation error proportional to \(d^3\), as shown in Section 6.1. In the three-point spread grid, median absolute error grows by about eightfold when \(|d|\) doubles; the median per-configuration log-log slope is 3.0003 across 104 configurations (range 2.8733–3.0441), excluding errors below \(10^{-9}\) pp. The centered values are not robust to reference misspecification: a synthetic one-volatility-point offset raises the median absolute error from 0.0000786 to 0.04238 pp and the nearest-rank p95 from 0.0872 to 1.4767 pp. These offsets are sensitivity scenarios, not estimates of errors in an independently observed ATM IV. If both leg IV roots are available, CPIV is their direct difference; the local approximation is relevant only as a diagnostic around a separately specified reference.

Figure 1 visualizes the approximately cubic increase in centered-grid error as the target spread grows; Table 1 reports the corresponding summaries and the sensitivity to deliberately shifted reference volatilities.

**Table 1.** Synthetic midpoint-approximation error by absolute spread and sensitivity to signed offsets from the midpoint reference; all errors are absolute and in volatility percentage points.

| Reference design | Evaluations (skipped) | Median | Nearest-rank p95 | Maximum |
|:--|--:|--:|--:|--:|
| Centered, \(|d|=0.5\) pp | 208 (0) | 0.00000839 | 0.006630 | 0.01816 |
| Centered, \(|d|=1.0\) pp | 208 (0) | 0.00006712 | 0.053070 | 0.14712 |
| Centered, \(|d|=2.0\) pp | 208 (0) | 0.00053754 | 0.425464 | 1.23552 |
| Offset magnitude \(0\) vol pp | 624 (0) | 0.00007858 | 0.087203 | 1.23552 |
| Offsets \(\pm1\) vol pp | 1,248 (0) | 0.042381 | 1.476687 | 32.55475 |
| Offsets \(\pm2\) vol pp | 1,248 (0) | 0.082799 | 5.183761 | 945.28285 |
| Offsets \(\pm5\) vol pp | 1,248 (0) | 0.222381 | 857.846918 | \(4.6234\times10^{13}\) |
| Offsets \(\pm10\) vol pp | 1,080 (168) | 0.301074 | 1,185.613325 | \(1.5828\times10^{10}\) |

*Notes:* Centered rows contain 208 cells per spread among the 624 cells that pass the baseline absolute-vega guard. Offset rows use those same 624 base cells, evaluating both signs for each nonzero offset; nonpositive reference volatilities are skipped. The p95 is nearest-rank. Offset errors use the project’s integrated-vega residual divided by point vega at the shifted reference; very large maxima arise when this denominator is small and should not be read as market-scale errors. The offset experiment is a deterministic stress test, not a calibration of an independent reference-volatility source.

Normalized midpoint vega is constant across the six spread cells for each non-spread configuration in this design. Among the 120 unique configurations, 16 fail the absolute guard; each contributes six cells. Their normalized midpoint vega has median \(1.40\times10^{-14}\) and maximum \(1.72\times10^{-10}\) per decimal-IV unit. The minimum among the 104 configurations that pass is \(7.30\times10^{-6}\), about \(4.23\times10^4\) times the maximum in the failing group (4.63 orders of magnitude). This separation describes this constructed grid only; it does not validate a normalized cutoff or establish similar separation in market data. The nominal-scale diagnostic preserves normalized vega under multiplication of prices by 0.01, 1, or 100, while the absolute guard resolves 104/120, 104/120, and 106/120 configurations, respectively. That change confirms that the baseline absolute-vega guard is scale-dependent, not a universal resolution criterion.

![Log-log synthetic diagnostic of local-approximation error against absolute CPIV spread, with a cubic-scaling reference. Points summarize the median and nearest-rank p95 across equally weighted guard-passing cells.](research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-12_v2/local_approximation_error.png){#fig-local-error}

### 7.2 American-put scheme comparison

The reported statistic is a numerical CPIV generated from an exact European BSM call and a tree-priced American put. At 6,400 steps, each scheme's change from its immediately preceding doubled grid is below the selected 0.001 pp threshold (CRR 0.000502 pp; Jarrow–Rudd 0.000169 pp). The two schemes' CPIV values at 6,400 steps differ by 0.001086 pp (−0.264587 versus −0.265673). This is only a successive-grid change diagnostic: it is not a formal error bound, proof of convergence, or independent exact-price benchmark. A separate European-limit check, with early exercise switched off, compares each tree with the closed-form BSM put. At 6,400 steps the CRR tree differs from BSM by \(8.9\times10^{-5}\) USD, so the 0.001 pp successive-change threshold does not imply \(10^{-6}\) accuracy; the Leisen–Reimer tree at 6,401 steps differs by \(3\times10^{-9}\) USD. These limits check the lattice implementation, not the early-exercise premium. No high-resolution American reference is claimed.

Table 2 lists the tree prices and implied-CPIV values across step counts, while Figure 2 visualizes their successive-grid changes. Table 2 shows one synthetic case as a numerical sensitivity check, not an independent American-option benchmark. Across the four scenarios in Appendix Table C2, the range of finest-grid CPIVs across CRR, Jarrow–Rudd and Leisen–Reimer is 0.0008 pp (zero-rate control), 0.0011 pp (ATM, 30 days), and 0.0009 pp (OTM put, 365 days). Barone–Adesi–Whaley lies 0.04–0.05 pp from the Leisen–Reimer reference in the ATM and OTM cases; it is reported beside the range, not in it. The deep in-the-money case shows zero spread only because every method returns intrinsic value.

**Table 2.** Tree-price and implied-CPIV outputs for one synthetic American-put scenario; change threshold is 0.001 pp between adjacent doubled grids. Appendix Table C2 gives the scenario envelope.

| Steps | CRR put | CRR CPIV (pp) | Jarrow–Rudd put | Jarrow–Rudd CPIV (pp) |
|--:|--:|--:|--:|--:|
| 400 | 2.112510 | −0.257018 | 2.114871 | −0.277758 |
| 800 | 2.112971 | −0.261065 | 2.114140 | −0.271341 |
| 1,600 | 2.113200 | −0.263082 | 2.113498 | −0.265699 |
| 3,200 | 2.113315 | −0.264085 | 2.113515 | −0.265841 |
| 6,400 | 2.113372 | −0.264587 | 2.113495 | −0.265673 |

![CRR and equal-probability Jarrow–Rudd American-put synthetic tree comparison.](research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-12_v2/american_tree_convergence.png){#fig-american-convergence width=75%}

### 7.3 Carry and spot mismatch

With true \(q=5\%\) and inversion at \(q=0\), the generated CPIV is \(-3.58725\) points; at \(q=-2\%\), it is \(+1.43903\) points. At zero yield it is zero up to rounding. Around the correctly specified input, the proposition's local yield-gradient predicts −3.59646 pp for the +5-point yield misspecification and +1.43962 pp for the −2-point case; these tangents are close to, but are not substituted for, the exact finite-inversion results. This demonstrates sensitivity to the effective-yield input, not an empirical relationship between CPIV and stock lending.

When quotes use spot \(100\) and inversion uses spot \(100.10\), the synthetic CPIV is \(-0.87439\) points; using \(99.90\) produces \(+0.87526\) points. The local spot-gradient predicts −0.87469 and +0.87469 pp, respectively. The asymmetry comes from the nonlinear BSM map. These examples reinforce that a quote timestamp and the spot timestamp belong in the data contract.

### 7.4 Quote-implied interval width and rank resolution

All ten synthetic pairs have four invertible quote endpoints at each tested spread; this design contains no one-sided endpoint cases. At a USD 0.02 half-spread, median interval width is 0.700 pp, 9/10 pairs exclude zero, and 45/45 unordered pairwise intervals are strictly non-overlapping. At USD 0.10, median width is 3.499 pp, 7/10 pairs exclude zero, and 21/45 pairwise comparisons are non-overlapping. At USD 0.25, median width is 8.747 pp, 1/10 pairs excludes zero, and 1/45 comparison is non-overlapping. A non-overlap result means only that this interval rule orders that constructed pair; overlap means this rule does not resolve its order. In an application with a missing finite endpoint (for example, a zero bid at the lower pricing bound), retain the one-sided bound and count comparisons not resolved by that bound as unresolved partial-order cases; do not drop the pair. These are deterministic properties of ten constructed pairs and chosen premium bands—not statistical coverage, market rank accuracy, or evidence that any unresolved comparison is wrong.

### 7.5 Ranking reliability depends on signal spacing

The stress test does not produce one universal “reliability” number. For ten equally spaced signals and Gaussian noise with target SD 0.50 points, mean pairwise inversion fraction is 17.6%, mean Spearman correlation is 0.797, and top/bottom membership turnover is 36.7%. For ten near-tied signals at the same noise scale, those values are 49.5%, 0.015, and 79.2%. In the 300 draws for each of these cells, no full ordering was preserved; the Wilson 95% upper bound is 1.26%, not zero probability. Near-tied sign accuracy is approximately 50%, as expected when noise dominates the prescribed signal.

**Table 3.** Replicate-level means and Monte Carlo standard errors (in parentheses) for Gaussian CPIV-space noise at configured SD 0.50 pp; each cell has 300 replicates.

| Universe and prescribed signals | Inversion fraction (MCSE) | Spearman \(\rho\) (MCSE) | Top/bottom turnover (MCSE) | Sign accuracy (MCSE) | Exact orders / 300 (Wilson upper 95%) |
|:--|--:|--:|--:|--:|--:|
| 10, equally spaced | 0.1759 (0.0038) | 0.7971 (0.0067) | 0.3667 (0.0122) | 0.8260 (0.0066) | 0 (1.26%) |
| 10, near-tied | 0.4951 (0.0069) | 0.0145 (0.0187) | 0.7917 (0.0111) | 0.5040 (0.0089) | 0 (1.26%) |
| 50, equally spaced | 0.2119 (0.0014) | 0.7710 (0.0029) | 0.4023 (0.0049) | 0.8074 (0.0031) | 0 (1.26%) |
| 50, near-tied | 0.4922 (0.0028) | 0.0227 (0.0081) | 0.7977 (0.0047) | 0.5067 (0.0042) | 0 (1.26%) |

For this metric, a uniformly random ranking gives an exact chance reference. If each tail contains k = n/5 names, expected overlap with either fixed true tail is k²/n; therefore expected top/bottom turnover is 1 − (2k²/n)/(2k) = 1 − k/n = 0.8. The near-tied means, 0.7917 for n = 10 and 0.7977 for n = 50, are respectively 0.75 and 0.49 MCSE below that reference (Table 3). This contextualizes these low-signal synthetic rankings; it does not estimate market turnover.

The comparison changes with signal spacing and error structure. A common additive shock shifts every value equally and therefore leaves ordering unchanged by construction; it is an invariance control, not a market-noise model. Continuous-metric MCSEs are calculated across the 300 replicate-level metric values; names and within-replicate pairs are not counted as independent observations. The Wilson upper bound after 0/300 exact orders is 1.26%; zero observed events is not a zero probability. Full cell-level means/MCSEs, Wilson intervals, paired scale contrasts, and per-name inclusion probabilities are in the companion CSVs.

For Gaussian CPIV-space noise only, Appendix Table C1 compares the simulator with a closed-form benchmark for expected inversion fraction, sign accuracy, and Spearman correlation. A pair with prescribed gap \(\Delta\) is inverted with probability \(\Phi(-\Delta/(s\sqrt{2}))\), name \(i\) has the correct sign with probability \(\Phi(|x_i|/s)\), and the expected Spearman correlation follows from bivariate-normal probabilities. Top/bottom turnover has no closed form and is checked only against the stored run. The 90 closed-form comparisons and 960 fresh-versus-stored simulation comparisons form one 1,050-test Holm family; none is rejected at 0.05 (Table C1). The stored 300-replicate concave-magnitude inversion cell at \(s=0.50\) is \(0.1746\), 2.71 combined Monte Carlo standard errors above the fresh 3,000-replicate value of \(0.1647\); its Holm-adjusted p is 1.000. These are author-run consistency checks of the simulator, not independent replication; the script is research/cpiv/gaussian_rank_benchmark.py. Non-Gaussian families have no closed form and are compared only simulation against simulation.

Numerical cross-check scope and provenance are documented in Section 9; these checks are implementation diagnostics, not independent validation.

The simulated rank-correlation patterns across signal shapes and universe sizes are plotted in Figure 3, complementing the replicate summaries in Table 3.

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

The illustrative perturbation design fixes \(S=K=100\), 30 days, \(r=0.03\), and \(q=0.01\). Gaussian call and put premium errors each have SD USD 0.02 per underlying unit, spot error has SD USD 0.02, and rate and effective-yield errors each have SD 0.001; strike and maturity errors are zero. The covariance matrix is diagonal except for the call–put premium-error covariance, set to \(\rho_{CP}(0.02)^2\) for \(\rho_{CP}\in\{0,0.5,0.9\}\). Thus spot, rate, and yield errors are mutually independent and independent of both premium errors. Each row aggregates 6,000 synthetic draws across seeds 20261012–20261014; all 6,000 inverted in these cases. Table 4 compares the first-order standard deviation from the full paired-IV gradient with the sample standard deviation from direct perturbation/inversion. It also reports an approximate normal-theory Monte Carlo standard error (MCSE) for the simulated sample SD, \(s/\sqrt{2(n-1)}\), with \(n=6{,}000\). This is a finite-draw precision diagnostic, not a formal test of the gradient approximation. These chosen scales are illustrations, not estimated market errors or uncertainty intervals.

**Table 4.** First-order and direct-perturbation CPIV standard deviations and approximate MCSE of the simulated SD under stated synthetic input-error scales (pp; 6,000 resolved draws per row). Difference = direct SD minus gradient SD.

| IV case \((\sigma_C,\sigma_P)\) | Price-error correlation | Gradient SD | Direct simulation SD | Difference | Approx. MCSE† | Resolved |
|:--|--:|--:|--:|--:|--:|--:|
| Equal (0.20, 0.20) | 0.0 | 0.3201 | 0.3242 | 0.0040 | 0.0030 | 6,000 |
| Equal (0.20, 0.20) | 0.5 | 0.2679 | 0.2699 | 0.0021 | 0.0025 | 6,000 |
| Equal (0.20, 0.20) | 0.9 | 0.2172 | 0.2168 | −0.0004 | 0.0020 | 6,000 |
| Unequal (0.24, 0.20) | 0.0 | 0.3201 | 0.3220 | 0.0018 | 0.0029 | 6,000 |
| Unequal (0.24, 0.20) | 0.5 | 0.2678 | 0.2685 | 0.0007 | 0.0025 | 6,000 |
| Unequal (0.24, 0.20) | 0.9 | 0.2172 | 0.2176 | 0.0004 | 0.0020 | 6,000 |

† Approximate normal-theory MCSE, computed as the direct sample SD divided by \(\sqrt{2(n-1)}\). The largest absolute difference is 1.37 times its approximate MCSE; this single simulated gap is not interpreted as a nonlinearity effect.

![Mean replicate-level Spearman rank correlation under synthetic Gaussian CPIV-space noise, by signal shape and universe size.](research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-12_v2/rank_sensitivity.png){#fig-rank-sensitivity}

### 7.7 Price identification and tolerance

At a hypothetical full tick \(t=0.01\) price units, the ATM, 30-day, 20%-IV example has vega 0.114326 currency units per IV point, giving a local full-tick shift of 0.087469 pp; exact shocks \(P\pm t\) change IV by approximately +0.087469 and −0.087469 pp. Under the illustrative worst-direction tolerance \(\tau_{IV}=0.10\) pp, the ATM case is identified and within tolerance; at \(\tau_{IV}=0.05\) pp it is identified but outside tolerance. Under nearest-tick rounding shocks \(P\pm t/2\), its maximum displacement is 0.043735 pp, so it is within both illustrative thresholds, including 0.05 pp. These are convention-dependent sensitivity classifications, not market defaults. At \(S/K=0.8\), 90 days, and 10% IV, the synthetic pair has \(R=0\), so \(X_C=X_P=3.177984\times10^{-6}\) price units and their minimum is below the hypothetical 0.01 tick. Vega is 7.2989×10⁻⁶ currency units per IV point, so the first-order full-tick quotient is 1,370.07 pp. This quotient is not a finite uncertainty interval: adding \(t\) yields a +7.0717-pp IV change, while subtracting \(t\) has no admissible root under the configured bounds. With the half-tick convention, adding \(t/2\) yields +5.9264 pp and subtracting \(t/2\) also has no root. The pair is below the \(\min(X_C,X_P)\) tick screen and has a missing negative-shock root, so it remains unresolved under both conventions and does not qualify as within either \(\tau_{IV}\), despite passing the baseline absolute-vega guard.

The deep call is out of the money and its model premium is below the hypothetical 0.01 tick; for this zero-residual synthetic pair, the put's premium above its European lower bound is equal, so \(\min(X_C,X_P)\) is also below tick. If the displayed call quote is bid 0 and ask 0.01, its midpoint 0.005 maps to a synthetic IV of 15.92548%; the ask price 0.01 maps to 17.07114%, while a zero bid has no interior positive-IV root. Under this European BSM example, the quote endpoints therefore give only a one-sided, boundary-limited IV range from the limiting lower bound 0 to about 17.07114%, not a uniquely identified latent premium or point IV. The quote pair remains in the analysis as an unresolved partial-order observation unless its available bound alone proves an order; the missing endpoint is neither imputed nor used to drop the pair. The midpoint conversion is a quote convention, not a transaction or market observation. By definition, a pair whose minimum leg-specific OTM-equivalent time value is below the declared hypothetical tick is not identified under the finite-shock rule even when an individual shocked price has a BSM root.

With \(u=2^{-53}\), the roundoff-scale local shifts at the same examples are 2.22×10⁻¹⁵ pp at the money; for the 10%-IV \(S/K=0.8\) cell they are 4.83×10⁻¹⁷ pp for the call and 3.04×10⁻¹⁰ pp for the put. The leg difference arises because the roundoff-scale price perturbation is proportional to each premium. These are illustrative local perturbations, not bounds on numerical error. Figure 4 shows only tick and quote-half-spread scenarios; the single-column roundoff diagnostic remains numerical in Table 5 and the accompanying CSV rather than receiving an otherwise empty heatmap panel.

The leg-level base values and local diagnostics are in Table 5. Exact IV changes under full-tick shocks are in Table 6, and Table 7 compares full-tick and nearest-tick rounding conventions.

**Table 5.** Local synthetic sensitivities at \(r=q=0\). The full tick \(t\) and quote half-spread are separate hypothetical 0.01 price perturbations. OTM-equivalent time value is each leg's premium above its European lower bound; the pair screen uses \(\min(X_C,X_P)\), since \(X_C-X_P=R\) and they coincide only in the displayed zero-residual cases. The guard column reports the baseline absolute-vega check. Roundoff is a separate local diagnostic. Vega is in price units per IV percentage point; roundoff is in pp.

| Leg | Leg premium | OTM-equivalent time value (below \(t\)?) | Vega/pp | Local tick / spread (pp) | Roundoff (pp) | Guard |
|:--|--:|--:|--:|--:|--:|:--:|
| ATM 30d/20% call | 2.287151 | 2.287151 (no) | 0.1143262 | 0.087469 / 0.087469 | 2.22e-15 | Pass |
| ATM 30d/20% put | 2.287151 | 2.287151 (no) | 0.1143262 | 0.087469 / 0.087469 | 2.22e-15 | Pass |
| \(S/K=0.8\), 90d/10% call | 3.178e-6 | 3.178e-6 (yes) | 7.2989e-6 | 1,370.07 / 1,370.07 | 4.83e-17 | Pass |
| \(S/K=0.8\), 90d/10% put | 20.000003 | 3.178e-6 (yes) | 7.2989e-6 | 1,370.07 / 1,370.07 | 3.04e-10 | Pass |

\newpage

**Table 6.** Exact IV changes under full-tick price shocks of \(\pm0.01\) price units (\(\pm t\)); the displayed changes are in volatility percentage points (pp), not price units. The maximum is over directions with finite roots; it is partial when a direction has no root and does not qualify the case as identified.

| Synthetic leg | \(\Delta IV\) for +0.01 price-unit shock (pp) | \(\Delta IV\) for −0.01 price-unit shock (pp) | Max \(|\Delta IV|\)* (pp) | Identified? | Within \(\tau_{IV}=0.10\) pp? | Within \(\tau_{IV}=0.05\) pp? |
|:--|--:|--:|--:|:--:|:--:|:--:|
| ATM 30d/20% call | +0.0875 | −0.0875 | 0.0875 | Yes | Yes | No |
| ATM 30d/20% put | +0.0875 | −0.0875 | 0.0875 | Yes | Yes | No |
| \(S/K=0.8\), 90d/10% call | +7.0717 | No root | Partial: 7.0717 | No: OTM-equivalent value below tick | Unresolved | Unresolved |
| \(S/K=0.8\), 90d/10% put | +7.0717 | No root | Partial: 7.0717 | No: OTM-equivalent value below tick | Unresolved | Unresolved |

**Table 7.** Sensitivity to the price-shock convention for matched call–put pairs. Full-tick shocks are \(\pm t\); nearest-tick rounding shocks are \(\pm t/2\). Price changes are in price units and IV changes in pp. Call and put results coincide in these parity-matched examples. For unresolved cases, the maximum is partial and neither tolerance is certified.

| Matched call–put case | Price-shock convention | \(\Delta IV\) after positive price shock (pp) | \(\Delta IV\) after negative price shock (pp) | Maximum available \(|\Delta IV|\) (pp) | Within \(\tau_{IV}=0.10 / 0.05\) pp? |
|:--|:--|--:|--:|--:|:--:|
| ATM 30d/20% | \(\pm t=\pm0.01\) | +0.087469 | −0.087469 | 0.087469 | Yes / No |
| ATM 30d/20% | \(\pm t/2=\pm0.005\) | +0.043735 | −0.043735 | 0.043735 | Yes / Yes |
| \(S/K=0.8\), 90d/10% | \(\pm t=\pm0.01\) | +7.0717 | No root | Partial: 7.0717 | Unresolved / Unresolved |
| \(S/K=0.8\), 90d/10% | \(\pm t/2=\pm0.005\) | +5.9264 | No root | Partial: 5.9264 | Unresolved / Unresolved |

![Finite-shock identification and illustrative precision status for hypothetical full ticks and quote half-spreads. Panels show zero-carry configurations at 10% and 20% reference IV across all five moneyness ratios and 30/90-day expiries. Gray is unresolved, blue is identified within the illustrative 0.10-pp worst-direction-displacement tolerance, and orange is identified but outside that tolerance. In tick panels the dagger marks the pair minimum OTM-equivalent time value below the displayed tick; in spread panels it marks that minimum below the 0.01 reference tick. The cross marks a missing leg-specific shock root; roundoff remains a separate local diagnostic in Table 5.](research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-12_v2/price_resolution_status_heatmap.png){#fig-price-resolution}

![Exact finite-shock IV changes for zero-carry configurations at 10% and 20% reference IV, all five moneyness ratios, and 30/90-day expiries; the full grid is in the CSV. Colors show maximum available absolute changes in bands through the configured 500-pp solver cap; a marked pair may still be unidentified because its minimum OTM-equivalent time value is below tick or one leg/direction has no root. The dagger marks a below-tick pair minimum and the cross a missing shock-direction root; machine-readable rows retain each leg and direction.](research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-12_v2/finite_shock_change_heatmap.png){#fig-finite-shock-change}

\newpage

### 7.8 Bound-first classification of inversion failures

The 16 rejected synthetic prices are classified using the same binary64 bounds and tolerance as the IV solver. The ordering is material: strict bound violations are identified first, then exact-bound prices are counted under the guard, then strictly interior prices within the absolute near-bound tolerance are counted as guard rejections. The separate Decimal comparison in Section 5 uses high-precision bounds and therefore does not supply these three classifier groups.

**Table 8.** Mutually exclusive replay of the 16 generated rejected prices against the binary64 bounds used by the solver.

| Group | Classification rule | Count | Recorded solver status |
|:--|:--|--:|:--|
| Strict bound violation | \(P<L\) or \(P>U\), checked first | 1 | Theoretical-bound violation |
| Exact-bound guard | \(P=L\) or \(P=U\) | 5 | Absolute near-bound guard |
| Interior near-bound guard | \(L<P<U\) and \(\min(P-L,U-P)\le10^{-10}\) | 10 | Absolute near-bound guard |
| **Total** | Disjoint groups; exact-bound prices belong to guard | **16** | **15 guard + 1 violation** |

The binary64 solver classification is 10 interior near-bound guards, 5 exact-bound guards, and 1 strict bound violation; Table 8 gives the mutually exclusive groups. Under the separate comparison with reconstructed 180-digit bounds, the same 16 stored prices classify as 12 inside, 2 on a boundary, and 2 outside. Table 9 cross-tabulates the two definitions; all counts describe these generated cases and do not estimate a market failure rate.

**Table 9.** Case-level cross-tab of the binary64 solver classifier against the exact numerical binary64 prices compared with reconstructed 180-digit bounds. Boundary means equality at either high-precision bound; shortest round-trip decimal text is audited separately in the machine-readable output.

| Binary64 solver group | 180-digit inside | 180-digit on boundary | 180-digit violation | Total |
|:--|--:|--:|--:|--:|
| Interior near-bound guard | 10 | 0 | 0 | 10 |
| Exact-bound guard | 2 | 2 | 1 | 5 |
| Strict bound violation | 0 | 0 | 1 | 1 |
| **Total** | **12** | **2** | **2** | **16** |

The high-precision comparison uses the exact rational value represented by each binary64 price (`Decimal.from_float`), not its shortest round-trip text alone. The 12/2/2 split therefore differs from the solver's 10/5/1 groups; the cross-tab localizes that difference rather than reconciling it by aggregate arithmetic. Both classifications concern these 16 generated cases only.

### 7.9 Synthetic workflow comparison

This section asks one narrow question: does the identification screen of Table 10 convert unresolved rank pairs into fewer wrong-order decisions than ranking by raw-midpoint CPIV? The truth is known only inside the simulator, so the result is an author-run design check. It is not market evidence and not independent replication. The design constants, seeds, and claim rule are defined in `research/cpiv/workflow_comparison.py`. No separate time-stamped pre-registration exists, so the claim rule is a stated decision rule, not a registered test.

Each replicate draws a universe of 10 or 50 names with spot \(S=100\), rate \(r=0.05\), and dividend yield \(q=0.02\). For each name, the moneyness ratio \(S/K\) is drawn uniformly from \(\{0.8,0.9,1.0,1.1,1.2\}\), the tenor from \(\{30,90\}\) days, and the put volatility \(\sigma_P\) from \(\{10\%,20\%,40\%\}\). The true CPIV \(\tau\) is drawn uniformly on \((-5,5)\) pp, and the call volatility is \(\sigma_C=\sigma_P+\tau/100\). True premiums are European Black–Scholes–Merton prices. A truly ordered pair has a true CPIV gap of at least 0.5 pp; smaller gaps are ties. Replicate \(k\) of a universe of size \(n\) is seeded from the string `20261018:n:k`. Each cell uses 200 replicates, and the same draws are reused across tick and spread cells.

Observed prices are the true premium rounded to the nearest tick \(t\in\{0.005,0.01,0.05\}\), with a symmetric half-spread \(h\in\{0.01,0.05,0.25\}\), both in price units. The quote is \(\text{bid}=\max(\text{mid}-h,0)\) and \(\text{ask}=\text{mid}+h\). The zero floor is the only truncation; because a premium is non-negative, the floor cannot exclude it. The quoted interval contains the true premium whenever \(h\ge t/2\). Of the nine \((t,h)\) cells, only \((0.05,0.01)\) violates this condition. There a name's quoted call or put interval misses the true premium for 70.3% of names at \(n=10\) and 71.7% at \(n=50\). In every other baseline cell the miss share is zero.

Three rules are compared on the same names:

- **E0** ranks by raw-midpoint CPIV and decides each pair whose two midpoint IVs exist.
- **E1** adds the absolute-vega guard from the price-resolution module (threshold \(10^{-6}\)) and leaves a pair undecided when either name fails it.
- **E2** applies the Table 10 identification screen. Each leg's OTM-equivalent time value must be at least the tick; the \(\pm t\) price shocks must invert to IV displacements of at most \(\tau_{IV}=0.10\) pp; and bid and ask IVs must be finite. A pair is ordered only when both names pass and their quote-implied CPIV intervals do not overlap. Otherwise the pair stays undecided.

Three metrics are reported per cell: the decided fraction (share of all pairs given an order), the wrong-order share among decided truly ordered pairs, and the false-exclusion share (truly ordered pairs left undecided). Standard errors are replicate-level, \(\mathrm{sd}/\sqrt{200}\). The claim rule credits a benefit only when E0's wrong-order share exceeds E2's by more than twice their combined Monte Carlo standard error. Table C3 in Appendix C gives all 18 baseline cells.

At baseline, 26–31% of names lack a midpoint IV in at least one leg. At ticks 0.005 and 0.01 the shortfall sits at \(S/K=0.8\) and \(1.2\): at 30 days, both legs at 0.8 (67–71% of names) and the put at 1.2 (65–69%); at 90 days, both legs at 0.8 and the put at 1.2 (25–34%). The 30-day call at 0.9 (21–27%) and put at 1.1 (33–34%) are missing less often, and the 30-day call at 1.2 depends on the tick. No leg is missing at \(S/K=1.0\). E0 leaves a pair undecided only when one of its names lacks a midpoint IV, so its decided fraction is about \((1-0.27)^2\approx0.53\), matching the 51.9–54.5% reported above for ticks 0.005 and 0.01.

The stress scenario shifts each call midpoint by \(1.5h\) before rounding and quoting, so the call quote is biased by more than its half-spread. The offset is a design choice, not a calibrated market effect; the scenario tests misspecification of the quote midpoint. Table C4 in Appendix C gives its rows.

- E1 produced exactly the same decisions as E0 in every cell, so the vega check changed no order in this design. The diagnostics explain why: every name that fails the vega check already lacks a midpoint IV.
- E2 made no wrong-order decision in any baseline cell where it decided. In the baseline this zero follows from the quote model rather than from the screen: where \(h\ge t/2\) both quoted intervals contain the true premium, so non-overlapping CPIV intervals order the pair correctly. Its zero standard error reflects zero observed errors, not a bound on the error rate.
- In each of the 12 baseline cells where E2 decides any pair, E0 is also correct on every pair E2 orders. The E2 advantage therefore comes from the pairs it leaves undecided, not from E0 erring on the pairs E2 orders.
- At tick 0.05, E2 decided no pairs, because the identification screen fails for every name: a \(\pm0.05\) price shock moves the 30-day at-the-money IV by 0.439 pp, more than four times \(\tau_{IV}\). Every truly ordered pair is therefore left undecided. E0 erred on 1.89–1.95% of its decided truly ordered pairs.
- At ticks 0.005 and 0.01, E0 erred on 0.06–0.18% of its decided truly ordered pairs and decided 51.9–54.5% of all pairs. E2 decided 1.3–20.3% of all pairs and left 78.3–98.5% of truly ordered pairs undecided, against 45.5–48.2% for E0.
- The claim rule credits a benefit in 9 of 18 baseline cells. The nine credits come from three distinct \((n,t)\) comparisons: \(n=10\) at \(t=0.005\) (reduction 0.126 pp), \(n=50\) at \(t=0.005\) (0.175 pp), and \(n=50\) at \(t=0.01\) (0.079 pp). E0 does not depend on \(h\), so each comparison gives one reduction, repeated across three spreads. The rule fails at \(n=10\), \(t=0.01\), where the reduction is 0.057 pp against a threshold of 0.068 pp.
- Under stress, E0's wrong-order share rises to 3.4–29.0% of decided truly ordered pairs, while E2 still made no wrong-order decision. E2's false-exclusion share stays at 78–100%. In every stress cell except \((0.05,0.01)\), the quoted call or put interval misses the true premium for every name; there the miss share is 70.3% at \(n=10\) and 71.7% at \(n=50\), as in the baseline. Because coverage fails, the argument for zero errors does not apply under stress. E2 still made no wrong-order decision in any stress cell where it decided, so that zero is an observed result for this design.

In the nine credited cells the wrong-order share falls by 0.08–0.18 percentage points of decided pairs, an absolute reduction. It is bought with 32–53 percentage points more truly ordered pairs left undecided. Relative to E0's error share the reduction looks large, because E2 made no observed wrong decision, but that zero is an observation, not an estimate of E2's error rate.

The cost of abstention is the ratio of totals: correct E0 orders on pairs E2 leaves undecided, per E0 error avoided. In the baseline this ratio is 340–1,360 at ticks 0.005 and 0.01 and 51–56 at tick 0.05, because E0 errors are rare. Under stress it falls to 2.3–28.7.

In this synthetic design the identification screen trades coverage for an absolute reduction of 0.08–0.18 pp in the wrong-order share. The result does not show that the screen improves decisions on real quotes. The truth, the quote and spread model, the stress offset, the tie margin, and the universe are design choices, and no market quote was used.

## 8. Interpretation and limits

For carry screening, the local rule is \(|\Delta CPIV_{pp}|\approx|\partial CPIV_{pp}/\partial\log F|\,|\Delta\log F|\le\tau_{carry}\), followed by exact re-inversion for finite discrepancies. In the synthetic ATM, 30-day, 20%-IV example, 1 basis point of relative-forward mismatch corresponds locally to 0.087469 CPIV points; a 1-point tolerance therefore corresponds to about 11.4326 basis points. This conversion is specific to that configuration, not a default market tolerance.

The exact identity is an algebraic diagnostic under a specified European BSM inversion, not an economic explanation. Since CPIV and \(R\) are linked through the same option prices and common inputs, observing both does not provide two independent signals. A forward inferred from the same call–put pair and then used to force that pair's parity residual toward zero would be circular. Independent synchronized inputs, multiple strikes with leave-one-pair-out checks, or an externally sourced forward are needed for a separate validation design.

Quote intervals are useful for showing whether signs or ranks survive the selected bid–ask endpoints. They do not account automatically for quote dependence, stale legs, discrete ticks, hidden liquidity, transaction costs, exercise features, or model choice. Hentschel (2003) and Muravyev and Pearson (2020) motivate attention to these issues, but their empirical estimates are not transplanted into this synthetic experiment.

The ranking exercise is a controlled stress test. Its signal vectors are prescribed, its noise scales are chosen for illustration, and its distributional assumptions are not calibrated to market data. The Wilson intervals capture finite simulation uncertainty conditional on those choices only. The experiment cannot estimate real-world ranking error, sign error, strategy turnover, profitability, or expected returns.

We do not claim a novel parity identity or an empirically superior estimator. The contribution is the explicit specification and implementation of an integrated diagnostic workflow, together with documented synthetic numerical stress tests. The only workflow comparison in this version is the synthetic study of Section 7.9, which contrasts the Table 10 screen with raw-midpoint CPIV and the baseline vega check against the simulator's own truth. It does not compare minimally filtered or synchronized-input CPIV, and it uses no calibrated ground truth or market observations. Its credited benefits are absolute reductions of 0.08–0.18 percentage points in the wrong-order share of decided pairs, from three distinct \((n,t)\) comparisons, obtained by leaving far more truly ordered pairs undecided. It therefore establishes a coverage–error trade-off in a synthetic design, not incremental decision value or superior diagnostic performance. Comparative validation on market quotes would additionally require a declared target and calibration source, real retained-data coverage, and ranking-stability checks; it is outside this synthetic note.

The study contains no historical option chain, underlying return panel, market-wide positions or liquidation census, out-of-sample test, transaction-cost-adjusted portfolio, or causal design. It therefore makes no alpha claim and does not close an empirical-market-data gate. A market study would need a defined universe, synchronized quotes and underlying observations, contract and exercise-style controls, explicit filters, a held-out time period, and a preregistered analysis plan before its results could support market claims.

The proposed staged checklist for future paired-option work is summarized in Table 10. It is an operational protocol, not market validation of the synthetic results.

**Table 10.** Operational diagnostic protocol proposed by this note; when required inputs or matching checks are unavailable, retain an unresolved status rather than infer a pass.

| Stage | Inputs | Check | Output/status | Action |
|:--|:--|:--|:--|:--|
| Contract matching | Underlying, option type, strike, expiry, exercise style, multiplier | Same pair definition and supported model | Matched / mismatch / unknown | Reject mismatch or analyze separately; do not pair unknown contracts |
| Timestamp validation | Option-leg and underlying timestamps; predeclared tolerance | Quote/spot synchronization | Synchronized / stale / unknown | Flag stale or unknown; do not silently substitute a spot |
| Carry/forward validation | Independently sourced synchronized spot, forward, rate, maturity; predeclared carry tolerance \(\tau_{carry}\) pp | Check \(F\approx S\exp((r-q)T)\); translate mismatch with the local gradient and re-invert finite mismatches | Validated / inconsistent / unknown | State tolerance in CPIV points; never infer the forward from the same option pair |
| Price validation | Bid/ask or selected price, common inputs, European bounds | Finite inputs and bound admissibility | Valid / theoretical-bound violation / unresolved | Preserve failure status; never clip prices into bounds |
| IV inversion | Price, common contract inputs, solver bracket and iteration rule | Root exists; report convergence and repricing error | IV with solver status / unresolved | Retain status and diagnostics; distinguish bracket rejection from invalid quote |
| Price identification and precision | Declared tick, \(X_C\), \(X_P\), bid/ask, common inputs, predeclared \(\tau_{IV}\) in pp | Compare \(\min(X_C,X_P)\) with the applicable tick; test all leg-specific finite-shock roots; report worst-direction displacement | Identified / identified within \(\tau_{IV}\) / identified outside \(\tau_{IV}\) / unresolved / local-only | Identification is not precision; only an identified case can pass \(\tau_{IV}\); the baseline absolute-vega guard or local derivative alone is insufficient |
| CPIV measurement | Paired IVs, units, common inputs, optional quote sides | Compute pp spread and quote-implied range; report leg and average vegas | Point estimate and, when defined, endpoint range | Report contract/multiplier convention and all four-endpoint denominator |
| Rank diagnostics | Cross-sectional CPIV values or intervals, declared universe | Pairwise non-overlap, sign resolution, inversions, membership, denominators; retain one-sided bounds | Resolved comparisons / unresolved partial order, including incomplete endpoint cases | Keep pairs with bid = 0 or another non-invertible endpoint; use one-sided bounds only where they establish order, otherwise count unresolved rather than dropping or imputing |

## 9. Reproducibility and declarations

The common-map identity checker covers unequal-volatility European prices, an American-tree-origin put, stale source-spot quotes inverted at a different common spot, and admissible premium perturbations. Its maximum residual-versus-integrated-vega gap is below \(1.2\times10^{-14}\) currency units across these four constructed cases. A separate 180-digit standard-library Decimal implementation audits the generated near-bound cases. Both are numerical consistency checks maintained by the same author, not an independent replication, proof, or formal peer review. A user-supplied auxiliary checker authored with AI assistance from the written specification was run against the fixed grid and matched the project pipeline to the reported precision; this is an implementation cross-check, not independent human replication. This note reports selected assumptions and outputs but does not contain the analysis source or complete machine-readable input bundle.

The supplemental checker matched the project pipeline to the reported precision for the 624/96 pass/fail counts in the 720-cell grid; the centered error median/p95/maximum (0.00007858/0.087203/1.23552 pp); the cubic-scaling slope (median 3.0003, range 2.8733–3.0441, \(n=104\)); and every signed reference-offset summary in Table 1, including 168 skipped evaluations at the 10-volatility-point offset. Both implementations used the same written grid specification, so specification errors may be shared. These matches support implementation reproducibility conditional on that specification, not independent replication or external validation.

**Funding and in-kind support:** No external cash funding was received. The author received a complimentary one-month HyperTracker Surge subscription from CoinMarketMan as in-kind support. The provider supplied no data or analytical input for this note: no HyperTracker data are used, and all reported results are synthetic.  
**Competing interests:** The author declares no competing interests.  
**Data and code availability:** No market data or external quote dataset are used. The results are synthetic. The analysis code and full generated inputs are not publicly archived with this note, no DOI has been assigned, and this manuscript alone does not contain all files required to rerun the analyses.  
**Acknowledgements:** None declared.

## Appendix A. Supplemental fixed-seed illustration

This supplemental fixed-seed, precomputed ten-name illustration is a presentation aid, not a result of the analyses in this note. Its slider selects among seven discrete, unequally spaced noise levels; it does not reprice options, invert implied volatility, or run Monte Carlo in the browser. At each level, the stored Monte Carlo summary is separate from one example draw, and plotted values share a fixed symmetric axis. The browser version is interactive; print formats show a static rendering.

<!-- CPIV_INTERACTIVE_WIDGET -->

## Appendix B. Reproduction commands

Requirements: `uv` 0.11.8 and Python 3.12 or newer, as declared in `pyproject.toml`. On 18 October 2026 the three documented `uv` commands below were executed verbatim in PowerShell on Windows, in two clean copies of the sources from which generated outputs, `dist/`, `site/`, and virtual environments had been removed. Each copy used the locked environment with Python 3.14.3. The reproduction command was run once in each copy and exited with status 0 both times. The two runs produced identical CSV and PNG files and identical manifests. The SVG files differed only in an embedded timestamp and generated element identifiers, and two JSON files differed only in the recorded output path. The test command, run once in the first copy, reported 316 passed, 10 skipped and 7 failed. All seven failures are in tests of other deliverables (the combined manuscript and the submission bundle) that read build outputs excluded from the copy; no CPIV test failed. The full suite passed in the source checkout, where built outputs are present, under Python 3.14.3. Three further clean copies were then run with the same commands, except that the environment's Python was invoked directly in place of `uv run`. On Windows, Python 3.12 and Python 3.13 each completed the reproduction with exit status 0 and reported 313 passed, 10 skipped and 10 failed; all ten failures are in non-CPIV modules that read files absent from the copy, and the CPIV modules passed. In WSL Ubuntu under Bash, Python 3.12.3 completed the reproduction with exit status 0, and the CPIV test modules reported 105 passed and 10 skipped, the skips being browser tests that need a built HTML file. Between the Windows Python 3.14.3 output and the WSL Python 3.12.3 output, CSV text fields match exactly and numeric fields differ by at most 3.34e-10. The JSON files differ only in recorded paths, the Python version, and the recorded hash of the local approximation grid, whose numeric residuals differ in the last digits. PNG files and SVG files, apart from the timestamp, are not byte-identical across these platforms, so byte identity across platforms is not claimed. A Linux/Windows CI matrix for Python 3.12–3.14 is configured in the source checkout but has not been executed, so it is not evidence of cross-platform success. Repeating the run on one machine with the same code establishes determinism, not independent correctness. The shell-neutral commands below are intended for both PowerShell and Bash. The source code is not embedded in this note; no public repository, reuse license, or DOI-backed archive is assigned. Public release remains a separate author decision.

Run from a source checkout of the project root. The commands regenerate the synthetic design and diagnostics in the stated output directory. Use a fresh output directory for a subsequent run; the source package and code archive are not part of this standalone manuscript.

```text
uv sync --locked --no-install-project
uv run python -m scripts.reproduce_cpiv_methods --output research/cpiv/generated/repro
uv run python -m pytest tests -q
```


## Appendix C. Supplementary benchmark and cross-check tables

The tables below are author-run synthetic checks. They are not independent replication, and the closed-form benchmark covers only Gaussian CPIV-space noise.

**Table C1.** Holm–Bonferroni family for the ranking-stress checks (one family of 1,050 tests, alpha 0.05). Closed-form comparisons use the Gaussian benchmark in Section 7.5. Fresh-versus-stored comparisons use three seeds not used for Table 3 (31415926, 27182818, 16180339), with 1,000 replicates per seed, against the stored 300-replicate run (three seeds of 100 replicates). The same seeds and 1,000 replicates per seed were used in an earlier draft of this benchmark, which reported standardised differences of −2.73 and −2.20 and a fresh concave-magnitude n=10 inversion value of 0.1640. This version gives 0.1647 for that cell and does not reproduce the earlier standardised differences. The current diagnostics code gives 0.1647 for that cell in the committed run, which uses the full noise-family list. The earlier value 0.1640 is reproduced exactly, cell for cell, when the Gaussian family is given seed offset 0 instead of 1, which is what the one-off driver produced by filtering the family list. The difference is therefore a choice of random stream within the same design (0.0007, about 0.6 Monte Carlo standard errors), not a code or data error. The earlier standardised differences of −2.73 and −2.20 come from the offset-0 stream and do not hold on the stream used here. The one-off driver is not part of the repository. Per-test rows are in the companion CSV.

| Comparison | Tests | Metrics | Max abs. z | Min Holm-adjusted p | Rejected |
|:--|--:|:--|--:|--:|--:|
| Closed form vs Monte Carlo (Gaussian noise) | 90 | inversion, sign accuracy, Spearman | 2.105 | 1.000 | 0 |
| Fresh simulation vs stored run (all families) | 960 | inversion, sign accuracy, Spearman, turnover | 3.47 | 0.546 | 0 |
| Total | 1,050 | | 3.47 | 0.546 | 0 |

**Table C2.** American-put cross-check: CPIV (pp) at the finest grid of each method, for four synthetic scenarios. Leisen–Reimer (6,401 steps) is the reference. The change column is the Leisen–Reimer difference between 3,201 and 6,401 steps. Barone–Adesi–Whaley is a quadratic approximation, not an exact American value, and is not computed at zero rate. Spread is the range across CRR, Jarrow–Rudd and Leisen–Reimer at the finest grid; Barone–Adesi–Whaley is excluded from the spread. Richardson-extrapolated values are in the companion CSV and are not used as end-points.

| Scenario | CRR (6,400) | Jarrow–Rudd (6,400) | Leisen–Reimer (6,401) | LR change, 3,201 to 6,401 | BAW (approx.) − LR | Spread (pp) |
|:--|--:|--:|--:|--:|--:|--:|
| ATM put, K 100, 30 days, r 5%, q 0%, σ 20% | −0.264587 | −0.265673 | −0.265150 | +0.000061 | +0.043599 | 0.0011 |
| Deep in-the-money put, K 120, 90 days, r 10%, q 0%, σ 20% | −22.015132 | −22.015132 | −22.015132 | 0.000000 | 0.000000 | 0.0000 |
| Zero-rate control, K 100, 30 days, r 0%, q 0%, σ 20% | 0.000781 | 0.000000 | 0.000000 | 0.000000 | not computed | 0.0008 |
| OTM put, K 90, 365 days, r 3%, q 2%, σ 25% | −0.156204 | −0.157134 | −0.156229 | +0.000092 | −0.046946 | 0.0009 |

In the deep in-the-money row, all methods return the intrinsic value of 20.000000 USD. The inverted CPIV of −22.015 pp is therefore a boundary outcome of the implied-volatility inverter, and the zero spread reflects identical prices, not validated volatility.

Richardson extrapolation of the CRR and Jarrow–Rudd trees is not used as an end-point, because its value depends on the grid pair. For the 365-day OTM put, the CRR estimate ranges over 0.017 pp across the 800/1,600 and 3,200/6,400 pairs. For the zero-rate control, the Jarrow–Rudd estimate changes sign between the first two pairs. In the ATM case the CRR pairs agree to 0.00001 pp, while the Jarrow–Rudd 800/1,600 pair lies 0.005 pp from its 3,200/6,400 value. The Leisen–Reimer tree moves monotonically with step count (ATM: 0.00012 pp from 1,601 to 3,201 steps, then 0.00006 pp to 6,401), so it is the reference. These checks do not establish a convergence order or an error bound.

**Table C3.** Synthetic workflow comparison under the design of Section 7.9: 200 replicates per cell, with seeded draws shared across tick and spread cells. Decided is the share of all pairs given an order. Wrong among decided is the wrong-order share of decided truly ordered pairs. False exclusion is the share of truly ordered pairs left undecided. Parentheses give replicate-level MCSE. The pooled count column sums, over the 200 replicates, the wrong E0 orders and the E0 decided truly ordered pairs. Pooled denominators are 9,000 pairs of which 8,136 are truly ordered at n=10, and 245,000 pairs of which 220,871 are truly ordered at n=50. Table rates are means of replicate-level shares, so a pooled ratio can differ from the table: 7 / 4,340 is 0.16%, against 0.13% at n=10, tick 0.005. At n=10 the wrong-order counts are small (3 to 69 across all replicates). The credit at n=10, tick 0.005 rests on seven wrong orders and clears the claim threshold by 0.015 percentage points; at tick 0.01 the rule is not met. Tick and half-spread are in price units. E1 equals E0 in every cell and is omitted. Credited applies the claim rule in Section 7.9; a dash marks a method that made no decisions.

| n | Tick | Half-spread | Decided, E0 / E2 | Wrong among decided, E0 (MCSE) | E0 wrong / decided ordered (pooled) | Wrong among decided, E2 (MCSE) | False exclusion, E0 / E2 | Credited |
|:--|--:|--:|--:|--:|--:|--:|--:|:--|
| 10 | 0.005 | 0.01 | 53.7% / 20.2% | 0.13% (0.06) | 7 / 4,340 | 0.00% (0.00) | 46.5% / 78.3% | Yes |
| 10 | 0.005 | 0.05 | 53.7% / 15.5% | 0.13% (0.06) | 7 / 4,340 | 0.00% (0.00) | 46.5% / 82.9% | Yes |
| 10 | 0.005 | 0.25 | 53.7% / 1.4% | 0.13% (0.06) | 7 / 4,340 | 0.00% (0.00) | 46.5% / 98.4% | Yes |
| 10 | 0.01 | 0.01 | 51.9% / 13.1% | 0.06% (0.03) | 3 / 4,204 | 0.00% (0.00) | 48.2% / 86.0% | No |
| 10 | 0.01 | 0.05 | 51.9% / 10.4% | 0.06% (0.03) | 3 / 4,204 | 0.00% (0.00) | 48.2% / 88.6% | No |
| 10 | 0.01 | 0.25 | 51.9% / 1.3% | 0.06% (0.03) | 3 / 4,204 | 0.00% (0.00) | 48.2% / 98.5% | No |
| 10 | 0.05 | 0.01 | 48.2% / 0.0% | 1.89% (0.28) | 69 / 3,914 | — | 51.8% / 100.0% | No |
| 10 | 0.05 | 0.05 | 48.2% / 0.0% | 1.89% (0.28) | 69 / 3,914 | — | 51.8% / 100.0% | No |
| 10 | 0.05 | 0.25 | 48.2% / 0.0% | 1.89% (0.28) | 69 / 3,914 | — | 51.8% / 100.0% | No |
| 50 | 0.005 | 0.01 | 54.5% / 20.3% | 0.18% (0.02) | 213 / 120,367 | 0.00% (0.00) | 45.5% / 78.3% | Yes |
| 50 | 0.005 | 0.05 | 54.5% / 15.3% | 0.18% (0.02) | 213 / 120,367 | 0.00% (0.00) | 45.5% / 83.1% | Yes |
| 50 | 0.005 | 0.25 | 54.5% / 1.5% | 0.18% (0.02) | 213 / 120,367 | 0.00% (0.00) | 45.5% / 98.3% | Yes |
| 50 | 0.01 | 0.01 | 52.7% / 13.6% | 0.08% (0.01) | 95 / 116,526 | 0.00% (0.00) | 47.2% / 85.5% | Yes |
| 50 | 0.01 | 0.05 | 52.7% / 10.6% | 0.08% (0.01) | 95 / 116,526 | 0.00% (0.00) | 47.2% / 88.3% | Yes |
| 50 | 0.01 | 0.25 | 52.7% / 1.4% | 0.08% (0.01) | 95 / 116,526 | 0.00% (0.00) | 47.2% / 98.5% | Yes |
| 50 | 0.05 | 0.01 | 48.3% / 0.0% | 1.95% (0.08) | 2,063 / 106,794 | — | 51.6% / 100.0% | No |
| 50 | 0.05 | 0.05 | 48.3% / 0.0% | 1.95% (0.08) | 2,063 / 106,794 | — | 51.6% / 100.0% | No |
| 50 | 0.05 | 0.25 | 48.3% / 0.0% | 1.95% (0.08) | 2,063 / 106,794 | — | 51.6% / 100.0% | No |

**Table C4.** Stress scenario in the design of Section 7.9: the call midpoint is shifted by 1.5 times the half-spread before quoting. Decided is the share of all pairs given an order. Wrong among decided is the wrong-order share of decided truly ordered pairs. False exclusion is the share of truly ordered pairs left undecided. Quote misses true premium is the share of names whose quoted call or put interval excludes the true premium, at baseline and under stress. Tick and half-spread are in price units. Dashes mark a method that made no decisions. Baseline decisions and errors are in Table C3; MCSE for these rows is in the companion CSV.

| n | Tick | Half-spread | Decided, E0 / E2 | Wrong among decided, E0 / E2 | False exclusion, E0 / E2 | Quote misses true premium, baseline / stress |
|:--|--:|--:|--:|--:|--:|--:|
| 10 | 0.005 | 0.01 | 57.5% / 20.2% | 4.46% / 0.00% | 42.8% / 78.3% | 0.0% / 100.0% |
| 10 | 0.005 | 0.05 | 57.5% / 15.3% | 11.60% / 0.00% | 42.8% / 83.0% | 0.0% / 100.0% |
| 10 | 0.005 | 0.25 | 57.5% / 1.7% | 28.37% / 0.00% | 42.8% / 98.1% | 0.0% / 100.0% |
| 10 | 0.01 | 0.01 | 57.4% / 13.3% | 5.15% / 0.00% | 42.8% / 85.9% | 0.0% / 100.0% |
| 10 | 0.01 | 0.05 | 57.4% / 10.7% | 11.65% / 0.00% | 42.8% / 88.2% | 0.0% / 100.0% |
| 10 | 0.01 | 0.25 | 57.4% / 1.5% | 28.33% / 0.00% | 42.8% / 98.4% | 0.0% / 100.0% |
| 10 | 0.05 | 0.01 | 51.7% / 0.0% | 3.40% / — | 48.4% / 100.0% | 70.3% / 70.3% |
| 10 | 0.05 | 0.05 | 52.9% / 0.0% | 8.68% / — | 47.2% / 100.0% | 0.0% / 100.0% |
| 10 | 0.05 | 0.25 | 52.9% / 0.0% | 26.31% / — | 47.2% / 100.0% | 0.0% / 100.0% |
| 50 | 0.005 | 0.01 | 59.3% / 20.3% | 4.96% / 0.00% | 40.7% / 78.3% | 0.0% / 100.0% |
| 50 | 0.005 | 0.05 | 59.3% / 15.3% | 12.03% / 0.00% | 40.7% / 83.0% | 0.0% / 100.0% |
| 50 | 0.005 | 0.25 | 59.3% / 1.7% | 29.05% / 0.00% | 40.7% / 98.2% | 0.0% / 100.0% |
| 50 | 0.01 | 0.01 | 59.2% / 13.7% | 5.55% / 0.00% | 40.7% / 85.5% | 0.0% / 100.0% |
| 50 | 0.01 | 0.05 | 59.2% / 11.0% | 12.18% / 0.00% | 40.7% / 87.8% | 0.0% / 100.0% |
| 50 | 0.01 | 0.25 | 59.2% / 1.5% | 29.03% / 0.00% | 40.7% / 98.3% | 0.0% / 100.0% |
| 50 | 0.05 | 0.01 | 52.3% / 0.0% | 3.37% / — | 47.6% / 100.0% | 71.7% / 71.7% |
| 50 | 0.05 | 0.05 | 54.5% / 0.0% | 9.32% / — | 45.4% / 100.0% | 0.0% / 100.0% |
| 50 | 0.05 | 0.25 | 54.5% / 0.0% | 26.67% / — | 45.4% / 100.0% | 0.0% / 100.0% |

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

Sokolov, M. (2019). *A deeper look at the implied volatility spread as a predictor of stock returns* [Doctoral dissertation, University of Rochester]. University of Rochester Research Repository. <https://urresearch.rochester.edu/fileDownloadForInstitutionalItem.action?itemId=35841&itemFileId=188460>
