---
title: "Diagnosing Call–Put Implied-Volatility Spreads: Exact European-BSM Mapping and Synthetic Ranking-Stability Tests"
subtitle: "A measurement-focused quantitative methods note"
lang: en-US
date: "19 October 2026"
author: "Phirawit Jitnarong"
description-meta: "A reproducible diagnostic framework for CPIV measurement, European BSM inversion, quote intervals, and synthetic ranking stability."
---

**Affiliation:** Independent researcher  
**ORCID:** [0009-0006-8368-5309](https://orcid.org/0009-0006-8368-5309)  
**Contact:** nxme176@gmail.com

\newpage

## Thai summary

บทความนี้เสนอขั้นตอนตรวจวัด call–put implied-volatility spread (CPIV) โดยเริ่มจากอัตลักษณ์ภายใต้ European BSM: parity residual เท่ากับอินทิกรัลของ vega ระหว่าง implied volatility สองขาเมื่อใช้ inputs ร่วมกันและทั้งสองรากมีอยู่ อัตลักษณ์นี้เชื่อม CPIV กับ residual โดยโครงสร้าง ไม่ใช่หลักฐานยืนยันอิสระ ในตัวอย่างสังเคราะห์ที่กำหนด tick สมมติ \(t=0.01\) การช็อกราคาแบบเต็ม tick \((\pm t)\) ทำให้ ATM IV เปลี่ยนสูงสุด 0.087469 จุดเปอร์เซ็นต์ ส่วนการช็อกครึ่ง tick \((\pm t/2)\) ให้ 0.043735 จุด ดังนั้นที่ tolerance 0.05 จุด ผลจึงต่างกันตาม convention ทั้งสองขาในกรณี deep มี OTM-equivalent time value ประมาณ \(3.178\times10^{-6}\) ซึ่งต่ำกว่า tick; ช็อกราคาเพิ่ม \(t\) และ \(t/2\) ทำให้ IV เปลี่ยนด้านที่มีรากประมาณ 7.0717 และ 5.9264 จุดตามลำดับ ขณะที่ช็อกด้านลบไม่มีราก กรณีนี้จึง unresolved ทั้งสอง convention การคลาดเคลื่อนของ carry/spot ในกรณีสังเคราะห์สร้าง CPIV ที่เปลี่ยนได้หลายจุดเปอร์เซ็นต์ การประมาณ local รอบจุดกึ่งกลางมี error เพิ่มใกล้กำลังสามของขนาด spread ในกริดที่ออกแบบให้สมมาตร แต่เมื่อเลื่อน reference volatility เพียง 1 จุด volatility ค่า median error เพิ่มจาก 0.0000786 เป็น 0.04238 pp และ p95 เป็น 1.4767 pp การเปรียบเทียบเวิร์กโฟลว์แบบสังเคราะห์ที่ผู้เขียนรันเองพบว่า ในการออกแบบพื้นฐาน resolution screen ไม่ให้การจัดลำดับผิดในคู่ที่ตัดสินได้ แต่ทิ้งคู่ที่มีลำดับจริงจำนวนมากไว้โดยไม่ตัดสิน เมื่อเลื่อน midpoint ของแต่ละชื่อแบบสุ่มจนช่วง bid–ask ของหลายชื่อไม่ครอบคลุมราคาจริง screen ยังมีสัดส่วนการจัดลำดับผิดต่ำกว่า midpoint ดิบในทุกเซลล์ที่ตัดสินได้ แต่ให้การจัดลำดับผิดในบางเซลล์ (สูงสุด 37.3% ของคู่ที่ตัดสินได้ในเซลล์ที่แย่ที่สุด) ผลนี้เป็นการแลกระหว่างความครอบคลุมกับความผิดพลาด ไม่ใช่หลักฐานว่าดีกว่าบนใบเสนอราคาจริง เมื่อใช้เฉพาะช่วง bid–ask โดยไม่มีการตรวจสอบเพิ่มเติม (E3) วิธีนี้ตัดสินคู่ได้มากกว่าในเซลล์ baseline แต่ภายใต้การเลื่อน midpoint รายชื่อให้การจัดลำดับผิดมากกว่า screen ในทุกเซลล์ที่ screen ตัดสินได้ เมื่อเพิ่มเฉพาะการตรวจการช็อกราคาเข้ากับกฎช่วง bid–ask ผลการตัดสินจะตรงกับ screen ทุกประการ จึงสรุปได้ว่าการตรวจนี้ให้การลดความผิดพลาดทั้งหมดในการออกแบบนี้ ผลทั้งหมดมาจากการทดลองสังเคราะห์ ไม่ใช่ข้อมูล option-chain จริง ผลตอบแทน การทดสอบ alpha หรือข้อสรุปเชิงตลาด

**คำสำคัญ:** call–put implied-volatility spread; put–call parity; implied volatility; vega; quote uncertainty; numerical stability; synthetic measurement study

\newpage

## Abstract

This methods note specifies a diagnostic workflow for the call–put implied-volatility spread (CPIV). Under a common European Black–Scholes–Merton (BSM) map, the parity residual equals the integral of vega between the two leg-specific implied-volatility roots, so CPIV and the residual are linked by construction and do not provide independent confirmation. For a hypothetical price tick of 0.01, the synthetic at-the-money, 30-day, 20%-volatility example has a worst-direction IV displacement of 0.087 percentage points under full-tick shocks and 0.044 pp under half-tick shocks. At an illustrative 0.05-point threshold, the first is outside and the second within tolerance, so the classification depends on the declared shock convention. A deep synthetic pair, whose OTM-equivalent time values lie below the tick, remains unresolved under both conventions. A one-basis-point forward mismatch corresponds locally to 0.087469 CPIV points in the ATM example; this conversion is configuration-specific. Carry and spot-mismatch scenarios move CPIV by several points, and a centered approximation grid shows error growing roughly as the cube of the displacement. In an author-run synthetic cross-section with known truth, a resolution screen made no wrong-order decisions in any baseline cell where it decided, but left most truly ordered pairs undecided. Under per-name call-midpoint shifts that break quote coverage, it still had a lower wrong-order share than raw-midpoint ranking in every cell where it decided, yet it made wrong-order decisions in 20 of 36 stress cells, with a pooled share of up to 37.3% of decided truly ordered pairs. An interval-only variant without the screens decides more pairs at baseline but makes more wrong-order decisions than the screen in every per-name stress cell where the screen decides. Adding only the shock-inversion check to the interval rule reproduces the screen's decisions exactly, so that check accounts for the whole error reduction in this design. These are synthetic numerical and design checks, not independent replication, and they contain no market quotes, returns, or investment performance.

**Keywords:** call–put implied-volatility spread; put–call parity; implied volatility; vega; quote uncertainty; numerical stability; synthetic measurement study

## 1. Introduction

The call–put implied-volatility spread is often discussed as a measure of relative option richness or as a predictor of returns. Those interpretations concern different objects. CPIV is a difference between two model-implied volatility estimates. A return spread is an outcome measured in a later period. An option-return spread is different again. A measurement study should establish what the input prices and inversion procedure identify before attaching an economic interpretation.

This note makes a narrow operational contribution: it specifies and implements a diagnostic workflow that connects the common-map identity, input validation, inversion statuses, quote-implied ranges, separately reported price-resolution sensitivities, local approximation, and ranking stability. It does not claim a novel parity identity or an empirically superior estimator. Its contribution is the explicit workflow, the accompanying synthetic numerical stress tests, and a synthetic comparison that shows a coverage–error trade-off for the resolution screen (Section 7.9); the staged protocol appears in Table 10.

The scope is intentionally limited. The synthetic tests establish properties of the specified pricing map and simulation designs. They do not establish how often these conditions occur in listed markets, whether CPIV forecasts stock or option returns, or whether a CPIV strategy earns returns after costs. No historical option-chain data or market-wide position data is used.

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

in underlying-currency units per underlying unit, before applying any option-contract multiplier. If prices are stated per contract, every price and parity term must use that same contract basis; equivalently, \(R_{contract}=M R_{unit}\) for multiplier \(M\). The yield \(q\) is an effective pricing input, not automatically a stock-borrow fee or funding charge.

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

The round-trip design contains 60 contract configurations and 120 option-leg prices (five \(S/K\) ratios of 0.8, 0.9, 1.0, 1.1 and 1.2 × four expiries of 7, 30, 90 and 365 days × three target IVs of 10%, 20% and 40% × two legs), with fixed \(r=0.03\) and \(q=0.01\). In the recorded run, 104 prices inverted; 15 were rejected by the configured absolute near-bound guard and one binary64 price fell outside the bounds computed by the binary64 solver. A separate 180-digit Decimal code path recomputed the 16 intended BSM prices: all 16 exact prices lie strictly inside the high-precision bounds, their target roots lie inside the solver bracket, and all are within the configured \(10^{-10}\) absolute guard. Comparing the stored binary64 prices against those 180-digit bounds gives 12/16 strictly inside; this is a different comparison from the solver's binary64-bound classifier and must not be labeled as its strict-inside count. Replaying the solver-bound classification yields 10 strictly interior near-bound guard cases, five prices exactly equal to a binary64 bound and caught by the guard, and one strict binary64-bound violation. The three mutually exclusive groups are tabulated in Section 7.8. This is a classification of this generated numerical design, not a general floating-point failure rate. Among the 104 successful inversions, maximum absolute repricing error was \(2.84\times10^{-14}\) currency units and maximum/p95 absolute IV-recovery error was \(1.19\times10^{-11}/5.41\times10^{-13}\) in decimal volatility. Ten deliberately invalid-price probes were rejected and none accepted. These are synthetic outcomes, not market-quote failure rates; the threshold remains an implementation setting, not a universal filter.

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

For a predeclared CPIV tolerance \(\tau\) in percentage points, the local conversion is \(\partial CPIV_{pp}/\partial\log F=-(1/T)\partial CPIV_{pp}/\partial q\). In the synthetic ATM, 30-day, 20%-IV example, a 1-basis-point relative-forward discrepancy corresponds to 0.087469 CPIV points; equivalently, a 1% forward discrepancy corresponds locally to 8.7469 CPIV points. The 1-basis-point value coincides with the full-tick shift of Section 7.7 because, at \(S=100\), one basis point is 0.01 currency units, the tick size \(t=0.01\) used there. Thus a 1-point CPIV tolerance maps to approximately 11.4326 basis points, or 0.114326% of the forward. This conversion depends on moneyness, maturity, and both implied roots; it is a local diagnostic, not a universal acceptance threshold. Larger discrepancies should be evaluated by exact re-inversion rather than extrapolating the tangent.

The American-put comparison fixes \(S=K=100\), 30 days, \(r=5\%\), \(q=0\), and \(\sigma=20\%\); it pairs a European BSM call with an American put valued by CRR and an equal-probability Jarrow–Rudd tree. CRR uses \(u=e^{\sigma\sqrt{\Delta t}}\), \(d=1/u\), and risk-neutral probability \(p=(e^{(r-q)\Delta t}-d)/(u-d)\), with early exercise at each node. The implemented Jarrow–Rudd variant uses \(u=e^{(r-q-\sigma^2/2)\Delta t+\sigma\sqrt{\Delta t}}\), \(d=e^{(r-q-\sigma^2/2)\Delta t-\sigma\sqrt{\Delta t}}\), and probability 1/2, also with early exercise. Both are compared at 400, 800, 1,600, 3,200, and 6,400 steps. A successive-grid CPIV change below 0.001 percentage points is a descriptive audit threshold, not a formal error bound or preregistered stopping rule; the two schemes are not asserted to be exact American benchmarks (Cox et al., 1979; Jarrow & Rudd, 1983).

**Early-exercise premium against the price ticks.** Table 2 reports the American-minus-European difference for one at-the-money case, but the relevant question is how large that difference is relative to the ticks and tolerances used elsewhere in this note. Appendix Table C7 summarises a separate synthetic grid of 270 configurations: \(S/K\in\{0.8,0.9,1.0,1.1,1.2\}\), 30, 90 and 365 days, \(\sigma\in\{10,20,40\}\%\), \(r\in\{0,3,5\}\%\) and \(q\in\{0,2\}\%\). Each American put is priced by a Leisen–Reimer tree at 3,201 steps (Leisen & Reimer, 1996) and the European put by Black–Scholes–Merton. The CPIV bias is the change in put-implied volatility from inverting the American price with the European map, multiplied by \(-1\), so a positive premium gives a negative bias. The premium is at least 0.005 price units in 51.5% of configurations, at least 0.01 in 48.1%, and at least 0.05 in 38.5%. The median absolute bias is 0.069 pp and the largest is 51.79 pp; the bias exceeds 0.10 pp in 47.4% of the 268 configurations with a defined bias. The premium is largest for deep in-the-money puts (\(S/K=0.8\)), where the median absolute bias is 4.19 pp; at \(S/K=1.0\) it is 0.146 pp, and for out-of-the-money puts (\(S/K=1.2\)) it is 0.0054 pp. In 126 of 270 configurations the premium is below 0.005 and the bias is at most 0.05 pp. A European map is therefore adequate only where the premium is below the applicable tick and the bias is within the chosen tolerance; elsewhere American prices must be inverted with a stated American model, as Table 10 requires. The grid is synthetic and is not a sample of listed contracts.

### 6.3 Quote-implied intervals

When all four bid/ask endpoint prices admit finite European IVs under the same inputs, the quote-implied range is

$$
100\left[IV(C_{bid})-IV(P_{ask}),\;IV(C_{ask})-IV(P_{bid})\right]\quad\text{(6)}.
$$

The output is in volatility percentage points. Endpoints combine quote-side extremes; the interval is not statistical coverage, a confidence interval, probability statement, or arbitrage bound. If a quote endpoint lies at a pricing boundary and has no finite positive-IV root (as can happen with a zero bid), retain any valid endpoint as a one-sided bound, mark the pair incomplete, and do not impute a missing endpoint or discard the pair. Such observations contribute unresolved partial-order comparisons unless their one-sided bounds alone establish an order. All ten synthetic pairs use \(S=K=100\), 30 days to expiry, and \(r=q=0\); put IV is 20% and call IVs run from 16% through 25%. A symmetric premium half-spread of USD 0.01, 0.02, 0.05, 0.10, or 0.25 per underlying unit is added/subtracted before inversion. The code reports the four-endpoint-invertible fraction out of 10 pairs, sign-resolved count/fraction among those valid pairs, median interval width in points, and strict non-overlap counts divided both by eligible valid unordered pairs and all 45 possible unordered pairs. Touching endpoints count as overlap. Incomplete pairs remain in the total denominator and are not silently interpreted as ties.

### 6.4 Ranking stress experiment

The ranking experiment crosses \(n\in\{10,50\}\), five signal shapes, eight synthetic noise structures, and three configured scales (0.25, 0.50, 1.00 pp). For \(i=0,\ldots,n-1\), let \(x_i=-1+2i/(n-1)\), in CPIV points. The shapes are: equally spaced \(x_i\); clustered near zero \(x_i^3\); near-tied \(0.03x_i\); two clusters \(-1+0.02i/n\) for \(i<n/2\) and \(1+0.02i/n\) otherwise; and the concave-magnitude transform \(g(x_i)=\operatorname{sign}(x_i)\sqrt{|x_i|}\). It remains supported on \([-1,1]\); it is not a heavy-tailed distribution. The two-cluster shape is not confined to \([-1,1]\): its positive cluster lies between +1.01 and +1.02.

Noise is added directly in CPIV space, not option-price space. The families are: (1) uniform \(U(-\sqrt{3}s,\sqrt{3}s)\); (2) Gaussian \(N(0,s^2)\); (3) a 5% contaminated Gaussian whose contaminant SD is five times the base SD and whose theoretical mixture variance is normalized to \(s^2\); (4–6) Gaussian heteroskedastic noise with factors \(f_i=0.5+i/(n-1)\), normalized by \(\sqrt{n^{-1}\sum_i f_i^2}\), respectively increasing, decreasing, or randomly permuted across names in each replicate; (7) Gaussian call/put leg errors each with marginal SD \(s\) and correlation 0.8, with CPIV noise defined as call error minus put error, giving theoretical paired SD \(s\sqrt{2(1-0.8)}=s\sqrt{0.4}\); and (8) one Gaussian additive CPIV shock shared identically by every name, included as a ranking-invariance control rather than a market-error model. Therefore the same configured scale does not imply the same paired CPIV SD in family 7. Three fixed seeds (20261009, 20261010, 20261011) contribute 100 replicates each. The total is \(2\times5\times8\times3\times300=72{,}000\) synthetic rankings. Within each universe–signal-shape–noise-family design and seed, the same underlying random draws are reused across scale values; results are compared as paired replicate differences.

For a replicate, the inversion fraction is the number of discordant unordered pairs divided by \(n(n-1)/2\), with index order breaking exact ties. Spearman's \(\rho=1-6\sum_i d_i^2/[n(n^2-1)]\) uses the resulting tie-broken ranks. Let \(k=\lfloor n/5\rfloor\); top/bottom turnover is \(1-(|L\cap L'|+|B\cap B'|)/(2k)\), the mean of long- and bottom-set missing-member fractions. Sign accuracy is \(n^{-1}\sum_i\mathbf{1}[(x_i>0)=(y_i>0)]\); exact zero is treated as nonpositive. The code also records exact full-order preservation and any extreme-quintile membership change.

Continuous metric means and their normal Monte Carlo intervals use each replicate as the observation; names and within-replicate pairs are not treated as independent observations. Adjacent noise-scale contrasts use paired replicate differences, with paired MCSE/intervals. Wilson (1927) intervals are reported for simulated event rates only. These intervals quantify finite simulation variation conditional on the chosen generator and seeds; they are not market confidence intervals. Per-name inclusion probabilities are supplied for the ten-name universe. None of the vectors or noise distributions is asserted to be market-realistic or calibrated.

### 6.5 Price resolution and tolerance by source

Price discretization, quote width, and floating-point scale are distinct inputs and are not combined into one \(\delta P\) or treated as a standard deviation. For one option leg, let \(P\) be its synthetic premium, \(\nu_{dec}\) its BSM vega per decimal IV, and \(\nu_{pp}=\nu_{dec}/100\) its vega per IV percentage point. The reported first-order sensitivities are

$$
\delta IV_{tick,pp}\approx\frac{t}{\nu_{pp}},\qquad
\delta IV_{spread,pp}\approx\frac{h}{\nu_{pp}},\qquad
\delta IV_{roundoff,pp}\approx\frac{u|P|}{\nu_{pp}},
\qquad u=2^{-53}.
$$

Here \(t\) is a parameterized full price-tick step and \(h\) is a quote half-spread, both in price units per underlying unit. Their numerical levels are hypothetical scenarios, not claims about any market. A full-tick sensitivity applies price shocks \(\pm t\); a nearest-tick rounding-error sensitivity applies \(\pm t/2\). The half-tick results are reported separately and do not silently replace the full-tick convention. The roundoff row uses the IEEE-754 binary64 unit roundoff as an illustrative relative price perturbation; it is not a rigorous bound on total pricing or inversion error. The three sensitivities remain separate; they are neither summed nor collapsed by a maximum rule.

These derivatives are local. For tick and half-spread scenarios, the output also attempts exact IV inversion for both legs under positive and negative price shocks when each shocked price remains inside the configured European bounds. Define the leg-specific OTM-equivalent time values as \(X_C=C-\max(Se^{-qT}-Ke^{-rT},0)\) and \(X_P=P-\max(Ke^{-rT}-Se^{-qT},0)\). With \(A=Se^{-qT}-Ke^{-rT}\), the parity residual defined in Section 4 satisfies \(X_C-X_P=C-P-A=R\); the two values are equal only when \(R=0\), not in general when CPIV is nonzero. The pair-level screen is therefore \(\min(X_C,X_P)\ge t\), rather than assuming equal leg values or screening the in-the-money premium. Define the pair as **tick-resolved** under the full-tick finite-shock design only when this minimum reaches the declared tick \(t\) and all four shocked prices \(C\pm t\) and \(P\pm t\) have finite roots. For quote half-spread scenarios, the declared 0.01 reference tick is used for the same minimum-value screen; the exact shocks are applied separately to each leg. This is distinct from precision. For a predeclared tolerance \(\tau_{IV}\) in volatility percentage points, define the maximum available absolute IV displacement across legs and shock directions; a tick-resolved pair is **within \(\tau_{IV}\)** only if every required finite-shock displacement is no greater than \(\tau_{IV}\). This is the worst-direction displacement from the base IV, not the full two-sided interval width. A missing root or a pair minimum below the applicable reference tick is unresolved and does not qualify as within any tolerance. Nearest-tick rounding results use shocks of half a declared tick on each leg and are reported as a separate sensitivity; they do not alter the full-tick screen. Failed inversions are not clipped or converted into finite intervals. Roundoff-scale exact inversion is omitted because it is below the meaningful resolution of this solver. The baseline absolute-vega guard (\(\nu_{dec}\ge10^{-6}\)) is reported separately and is not used to certify tick resolution or precision.

The synthetic grid reuses the 120 combinations of \(S/K\), expiry, reference IV, and carry specified in Section 6.1. Each call and put is priced at the same reference IV to isolate price-to-IV sensitivity, so \(R=0\) and \(X_C=X_P\) in these particular base cases. Default tick scenarios are 0.0001, 0.001, 0.01, and 0.1 price units; half-spread scenarios are 0.01, 0.02, 0.05, 0.10, and 0.25. The source code accepts other positive tick and half-spread values. Tick rows compare \(\min(X_C,X_P)\) with the row-specific tick; half-spread and roundoff rows compare the same minimum with the 0.01 reference tick (or the smallest configured tick if 0.01 is absent). The CSV keeps call and put legs separate. Figure 4 reports tick resolution and whether the maximum worst-direction absolute finite-shock displacement is within the illustrative \(\tau_{IV}=0.10\) pp threshold; Figure 5 reports the magnitude of exact finite changes. Both figures preserve leg-level machine-readable rows in the generated output.

## 7. Results

Section 7 reports the synthetic results in the order of Section 6, from local approximation (7.1) to the workflow comparison (7.9). Every result in this section is computed from synthetic data and is not an estimate of market-observed CPIV.

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

![Log-log synthetic diagnostic of local-approximation error against absolute CPIV spread, with a cubic-scaling reference. Points summarize the median and nearest-rank p95 across equally weighted guard-passing cells.](research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-19_r32/local_approximation_error.png){#fig-local-error}

### 7.2 American-put scheme comparison

The reported statistic is a numerical CPIV generated from an exact European BSM call and a tree-priced American put. At 6,400 steps, each scheme's change from its immediately preceding doubled grid is below the selected 0.001 pp threshold (CRR 0.000502 pp; Jarrow–Rudd 0.000169 pp). The two schemes' CPIV values at 6,400 steps differ by 0.001086 pp (−0.264587 versus −0.265673). This is only a successive-grid change diagnostic: it is not a formal error bound, proof of convergence, or independent exact-price benchmark. A separate European-limit check, with early exercise switched off, compares each tree with the closed-form BSM put. At 6,400 steps the CRR tree differs from BSM by \(8.9\times10^{-5}\) USD, so the 0.001 pp successive-change threshold does not imply \(10^{-6}\) accuracy; the Leisen–Reimer tree (Leisen & Reimer, 1996) at 6,401 steps differs by \(3\times10^{-9}\) USD. These limits check the lattice implementation, not the early-exercise premium. No high-resolution American reference is claimed.

Table 2 lists the tree prices and implied-CPIV values across step counts, while Figure 2 visualizes their successive-grid changes. Table 2 shows one synthetic case as a numerical sensitivity check, not an independent American-option benchmark. Across the four scenarios in Appendix Table C2, the range of finest-grid CPIVs across CRR, Jarrow–Rudd and Leisen–Reimer is 0.0008 pp (zero-rate control), 0.0011 pp (ATM, 30 days), and 0.0009 pp (OTM put, 365 days). Barone–Adesi–Whaley (Barone-Adesi & Whaley, 1987) lies 0.04–0.05 pp from the Leisen–Reimer reference in the ATM and OTM cases; it is reported beside the range, not in it. The deep in-the-money case shows zero spread only because every method returns intrinsic value.

**Table 2.** Tree-price and implied-CPIV outputs for one synthetic American-put scenario; change threshold is 0.001 pp between adjacent doubled grids. Appendix Table C2 gives the scenario envelope.

| Steps | CRR put | CRR CPIV (pp) | Jarrow–Rudd put | Jarrow–Rudd CPIV (pp) |
|--:|--:|--:|--:|--:|
| 400 | 2.112510 | −0.257018 | 2.114871 | −0.277758 |
| 800 | 2.112971 | −0.261065 | 2.114140 | −0.271341 |
| 1,600 | 2.113200 | −0.263082 | 2.113498 | −0.265699 |
| 3,200 | 2.113315 | −0.264085 | 2.113515 | −0.265841 |
| 6,400 | 2.113372 | −0.264587 | 2.113495 | −0.265673 |

![CRR and equal-probability Jarrow–Rudd American-put synthetic tree comparison.](research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-19_r32/american_tree_convergence.png){#fig-american-convergence width=75%}

### 7.3 Carry and spot mismatch

With true \(q=5\%\) and inversion at \(q=0\), the generated CPIV is \(-3.58725\) points; at \(q=-2\%\), it is \(+1.43903\) points. At zero yield it is zero up to rounding. Around the correctly specified input, the proposition's local yield-gradient predicts −3.59646 pp for the +5-point yield misspecification and +1.43962 pp for the −2-point case; these tangents are close to, but are not substituted for, the exact finite-inversion results. This demonstrates sensitivity to the effective-yield input, not an empirical relationship between CPIV and stock lending.

When quotes use spot \(100\) and inversion uses spot \(100.10\), the synthetic CPIV is \(-0.87439\) points; using \(99.90\) produces \(+0.87526\) points. The local spot-gradient predicts −0.87469 and +0.87469 pp, respectively. The asymmetry comes from the nonlinear BSM map. These examples reinforce that a quote timestamp and the spot timestamp belong in the data contract.

### 7.4 Quote-implied interval width and rank resolution

All ten synthetic pairs have four invertible quote endpoints at each tested spread; this design contains no one-sided endpoint cases. At a USD 0.02 half-spread, median interval width is 0.700 pp, 9/10 pairs exclude zero, and 45/45 unordered pairwise intervals are strictly non-overlapping. At USD 0.10, median width is 3.499 pp, 7/10 pairs exclude zero, and 21/45 pairwise comparisons are non-overlapping. At USD 0.25, median width is 8.747 pp, 1/10 pairs excludes zero, and 1/45 comparison is non-overlapping. A non-overlap result means only that this interval rule orders that constructed pair; overlap means this rule does not resolve its order. In an application with a missing finite endpoint (for example, a zero bid at the lower pricing bound), retain the one-sided bound and count comparisons not resolved by that bound as unresolved partial-order cases; do not drop the pair. These are deterministic properties of ten constructed pairs and chosen premium bands—not statistical coverage, market rank accuracy, or evidence that any unresolved comparison is wrong.

### 7.5 Ranking stability depends on signal spacing

The stress test does not produce one universal “stability” number. For ten equally spaced signals and Gaussian noise with target SD 0.50 points, mean pairwise inversion fraction is 17.6%, mean Spearman correlation is 0.797, and top/bottom membership turnover is 36.7%. For ten near-tied signals at the same noise scale, those values are 49.5%, 0.015, and 79.2%. In the 300 draws for each of these cells, no full ordering was preserved; the Wilson 95% upper bound is 1.26%, not zero probability. Near-tied sign accuracy is approximately 50%, as expected when noise dominates the prescribed signal.

**Table 3.** Replicate-level means and Monte Carlo standard errors (in parentheses) for Gaussian CPIV-space noise at configured SD 0.50 pp; each cell has 300 replicates.

| Universe and prescribed signals | Inversion fraction (MCSE) | Spearman \(\rho\) (MCSE) | Top/bottom turnover (MCSE) | Sign accuracy (MCSE) | Exact orders / 300 (Wilson upper 95%) |
|:--|--:|--:|--:|--:|--:|
| 10, equally spaced | 0.1759 (0.0038) | 0.7971 (0.0067) | 0.3667 (0.0122) | 0.8260 (0.0066) | 0 (1.26%) |
| 10, near-tied | 0.4951 (0.0069) | 0.0145 (0.0187) | 0.7917 (0.0111) | 0.5040 (0.0089) | 0 (1.26%) |
| 50, equally spaced | 0.2119 (0.0014) | 0.7710 (0.0029) | 0.4023 (0.0049) | 0.8074 (0.0031) | 0 (1.26%) |
| 50, near-tied | 0.4922 (0.0028) | 0.0227 (0.0081) | 0.7977 (0.0047) | 0.5067 (0.0042) | 0 (1.26%) |

For this metric, a uniformly random ranking gives an exact chance reference. If each tail contains k = n/5 names, expected overlap with either fixed true tail is k²/n; therefore expected top/bottom turnover is 1 − (2k²/n)/(2k) = 1 − k/n = 0.8. The near-tied means, 0.7917 for n = 10 and 0.7977 for n = 50, are respectively 0.75 and 0.49 MCSE below that reference (Table 3). This contextualizes these low-signal synthetic rankings; it does not estimate market turnover.

The comparison changes with signal spacing and error structure. A common additive shock shifts every value equally and therefore leaves ordering unchanged by construction; it is an invariance control, not a market-noise model. Continuous-metric MCSEs are calculated across the 300 replicate-level metric values; names and within-replicate pairs are not counted as independent observations. The Wilson upper bound after 0/300 exact orders is 1.26%; zero observed events is not a zero probability. Full cell-level means/MCSEs, Wilson intervals, paired scale contrasts, and per-name inclusion probabilities are in the companion CSVs.

For Gaussian CPIV-space noise only, Appendix Table C1 compares the simulator with a closed-form benchmark for expected inversion fraction, sign accuracy, and Spearman correlation. A pair with prescribed gap \(\Delta\) is inverted with probability \(\Phi(-\Delta/(s\sqrt{2}))\), name \(i\) has the correct sign with probability \(\Phi(|x_i|/s)\), and the expected Spearman correlation follows from bivariate-normal probabilities. Top/bottom turnover has no closed form and is checked only against the stored run. The 90 closed-form comparisons and 960 fresh-versus-stored simulation comparisons form one 1,050-test Holm family (Holm, 1979); none is rejected at 0.05 (Table C1). The stored 300-replicate concave-magnitude inversion cell at \(s=0.50\) is \(0.1746\), 2.71 combined Monte Carlo standard errors above the fresh 3,000-replicate value of \(0.1647\); its Holm-adjusted p is 1.000. These are author-run consistency checks of the simulator, not independent replication; the script is research/cpiv/gaussian_rank_benchmark.py. Non-Gaussian families have no closed form and are compared only simulation against simulation.

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

![Mean replicate-level Spearman rank correlation under synthetic Gaussian CPIV-space noise, by signal shape and universe size.](research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-19_r32/rank_sensitivity.png){#fig-rank-sensitivity}

### 7.7 Price resolution and tolerance

At a hypothetical full tick \(t=0.01\) price units, the ATM, 30-day, 20%-IV example has vega 0.114326 currency units per IV point, giving a local full-tick shift of 0.087469 pp; exact shocks \(P\pm t\) change IV by approximately +0.087469 and −0.087469 pp. Under the illustrative worst-direction tolerance \(\tau_{IV}=0.10\) pp, the ATM case is tick-resolved and within tolerance; at \(\tau_{IV}=0.05\) pp it is tick-resolved but outside tolerance. Under nearest-tick rounding shocks \(P\pm t/2\), its maximum displacement is 0.043735 pp, so it is within both illustrative thresholds, including 0.05 pp. These are convention-dependent sensitivity classifications, not market defaults. At \(S/K=0.8\), 90 days, and 10% IV, the synthetic pair has \(R=0\), so \(X_C=X_P=3.177984\times10^{-6}\) price units and their minimum is below the hypothetical 0.01 tick. Vega is 7.2989×10⁻⁶ currency units per IV point, so the first-order full-tick quotient is 1,370.07 pp. This quotient is not a finite uncertainty interval: adding \(t\) yields a +7.0717-pp IV change, while subtracting \(t\) has no admissible root under the configured bounds. With the half-tick convention, adding \(t/2\) yields +5.9264 pp and subtracting \(t/2\) also has no root. The pair is below the \(\min(X_C,X_P)\) tick screen and has a missing negative-shock root, so it remains unresolved under both conventions and does not qualify as within either \(\tau_{IV}\), despite passing the baseline absolute-vega guard. Its finite positive-shock displacement already exceeds \(\tau_{IV}\) under both conventions, so it is known to lie outside both tolerances even though its resolution status is unresolved.

The deep call is out of the money and its model premium is below the hypothetical 0.01 tick; for this zero-residual synthetic pair, the put's premium above its European lower bound is equal, so \(\min(X_C,X_P)\) is also below tick. If the displayed call quote is bid 0 and ask 0.01, its midpoint 0.005 maps to a synthetic IV of 15.92548%; the ask price 0.01 maps to 17.07114%, while a zero bid has no interior positive-IV root. Under this European BSM example, the quote endpoints therefore give only a one-sided, boundary-limited IV range from the limiting lower bound 0 to about 17.07114%, not a uniquely identified latent premium or point IV. The quote pair remains in the analysis as an unresolved partial-order observation unless its available bound alone proves an order; the missing endpoint is neither imputed nor used to drop the pair. The midpoint conversion is a quote convention, not a transaction or market observation.

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

**Table 6.** Exact IV changes under full-tick price shocks of \(\pm0.01\) price units (\(\pm t\)); the displayed changes are in volatility percentage points (pp), not price units. The maximum is over directions with finite roots; it is partial when a direction has no root and does not qualify the case as tick-resolved.

| Synthetic leg | \(\Delta IV\) for +0.01 price-unit shock (pp) | \(\Delta IV\) for −0.01 price-unit shock (pp) | Max \(|\Delta IV|\)* (pp) | Tick-resolved? | Within \(\tau_{IV}=0.10\) pp? | Within \(\tau_{IV}=0.05\) pp? |
|:--|--:|--:|--:|:--:|:--:|:--:|
| ATM 30d/20% call | +0.0875 | −0.0875 | 0.0875 | Yes | Yes | No |
| ATM 30d/20% put | +0.0875 | −0.0875 | 0.0875 | Yes | Yes | No |
| \(S/K=0.8\), 90d/10% call | +7.0717 | No root | Partial: 7.0717 | No: OTM-equivalent value below tick | Known outside | Known outside |
| \(S/K=0.8\), 90d/10% put | +7.0717 | No root | Partial: 7.0717 | No: OTM-equivalent value below tick | Known outside | Known outside |

**Table 7.** Sensitivity to the price-shock convention for matched call–put pairs. Full-tick shocks are \(\pm t\); nearest-tick rounding shocks are \(\pm t/2\). Price changes are in price units and IV changes in pp. Call and put results coincide in these parity-matched examples. For unresolved cases, the maximum is partial; a finite displacement above a tolerance shows that tolerance is exceeded, and neither tolerance is certified.

| Matched call–put case | Price-shock convention | \(\Delta IV\) after positive price shock (pp) | \(\Delta IV\) after negative price shock (pp) | Maximum available \(|\Delta IV|\) (pp) | Within \(\tau_{IV}=0.10 / 0.05\) pp? |
|:--|:--|--:|--:|--:|:--:|
| ATM 30d/20% | \(\pm t=\pm0.01\) | +0.087469 | −0.087469 | 0.087469 | Yes / No |
| ATM 30d/20% | \(\pm t/2=\pm0.005\) | +0.043735 | −0.043735 | 0.043735 | Yes / Yes |
| \(S/K=0.8\), 90d/10% | \(\pm t=\pm0.01\) | +7.0717 | No root | Partial: 7.0717 | Known outside / Known outside |
| \(S/K=0.8\), 90d/10% | \(\pm t/2=\pm0.005\) | +5.9264 | No root | Partial: 5.9264 | Known outside / Known outside |

![Finite-shock resolution and illustrative precision status for hypothetical full ticks and quote half-spreads. Panels show zero-carry configurations at 10% and 20% reference IV across all five moneyness ratios and 30/90-day expiries. Gray is unresolved, blue is tick-resolved and within the illustrative 0.10-pp worst-direction-displacement tolerance, and orange is tick-resolved but outside that tolerance. In tick panels the dagger marks the pair minimum OTM-equivalent time value below the displayed tick; in spread panels it marks that minimum below the 0.01 reference tick. The cross marks a missing leg-specific shock root; roundoff remains a separate local diagnostic in Table 5.](research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-19_r32/price_resolution_status_heatmap.png){#fig-price-resolution}

![Exact finite-shock IV changes for zero-carry configurations at 10% and 20% reference IV, all five moneyness ratios, and 30/90-day expiries; the full grid is in the CSV. Colors show maximum available absolute changes in bands through the configured 500-pp solver cap; a marked pair may still be unresolved because its minimum OTM-equivalent time value is below tick or one leg/direction has no root. The dagger marks a below-tick pair minimum and the cross a missing shock-direction root; machine-readable rows retain each leg and direction.](research/cpiv/generated/cpiv_methods_note_reproduction_2026-10-19_r32/finite_shock_change_heatmap.png){#fig-finite-shock-change}

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

This section asks one narrow question: does the resolution screen of Table 10 convert unresolved rank pairs into fewer wrong-order decisions than ranking by raw-midpoint CPIV? The truth is known only inside the simulator, so the result is an author-run design check. It is not market evidence and not independent replication. The design constants, seeds, and claim rule are defined in `research/cpiv/workflow_comparison.py`; the per-name stress scenario is in `research/cpiv/workflow_stress_per_name.py`; the interval-only ablation and sensitivity sweep are in `research/cpiv/workflow_ablation.py`. No separate time-stamped pre-registration exists, so the claim rule is a stated decision rule, not a registered test.

Each replicate draws a universe of 10 or 50 names with spot \(S=100\), rate \(r=0.05\), and dividend yield \(q=0.02\). For each name, the moneyness ratio \(S/K\) is drawn uniformly from \(\{0.8,0.9,1.0,1.1,1.2\}\), the tenor from \(\{30,90\}\) days, and the put volatility \(\sigma_P\) from \(\{10\%,20\%,40\%\}\). The true CPIV \(\tau\) is drawn uniformly on \((-5,5)\) pp, and the call volatility is \(\sigma_C=\sigma_P+\tau/100\). True premiums are European Black–Scholes–Merton prices. A truly ordered pair has a true CPIV gap of at least 0.5 pp; smaller gaps are ties. Replicate \(k\) of a universe of size \(n\) is seeded from the string `20261018:n:k`. Each cell uses 200 replicates, and the same draws are reused across tick and spread cells.

Observed prices are the true premium rounded to the nearest tick \(t\in\{0.005,0.01,0.05\}\), with a symmetric half-spread \(h\in\{0.01,0.05,0.25\}\), both in price units. The quote is \(\text{bid}=\max(\text{mid}-h,0)\) and \(\text{ask}=\text{mid}+h\). The zero floor is the only truncation; because a premium is non-negative, the floor cannot exclude it. The quoted interval contains the true premium whenever \(h\ge t/2\). Of the nine \((t,h)\) cells, only \((0.05,0.01)\) violates this condition. There a name's quoted call or put interval misses the true premium for 70.3% of names at \(n=10\) and 71.7% at \(n=50\). In every other baseline cell the miss share is zero.

Three rules are compared on the same names:

- **E0** ranks by raw-midpoint CPIV and decides each pair whose two midpoint IVs exist.
- **E1** adds the absolute-vega guard from the price-resolution module (threshold \(10^{-6}\)) and leaves a pair undecided when either name fails it.
- **E2** applies the Table 10 resolution screen. Each leg's OTM-equivalent time value must be at least the tick; the \(\pm t\) price shocks must invert to IV displacements of at most \(\tau_{IV}=0.10\) pp; and bid and ask IVs must be finite. A pair is ordered only when both names pass and their quote-implied CPIV intervals do not overlap. Otherwise the pair stays undecided.

Three metrics are reported per cell: the decided fraction (share of all pairs given an order), the wrong-order share among decided truly ordered pairs, and the false-exclusion share (truly ordered pairs left undecided). Standard errors are replicate-level, \(\mathrm{sd}/\sqrt{200}\). The claim rule credits a benefit only when E0's wrong-order share exceeds E2's by more than twice their combined Monte Carlo standard error. The rule is descriptive: it is applied to 18 baseline and 36 stress cells without a multiplicity adjustment, and cells share draws across ticks and spreads, so credits are not independent tests and carry no error-rate guarantee. Table C3 in Appendix C gives all 18 baseline cells.

At baseline, 26–31% of names lack a midpoint IV in at least one leg. At ticks 0.005 and 0.01 the shortfall sits at \(S/K=0.8\) and \(1.2\): at 30 days, both legs at 0.8 (67–71% of names) and the put at 1.2 (65–69%); at 90 days, both legs at 0.8 and the put at 1.2 (25–34%). The 30-day call at 0.9 (21–27%) and put at 1.1 (33–34%) are missing less often, and the 30-day call at 1.2 depends on the tick. No leg is missing at \(S/K=1.0\). E0 leaves a pair undecided only when one of its names lacks a midpoint IV, so its decided fraction is about \((1-0.27)^2\approx0.53\), matching the 51.9–54.5% reported in the results below for ticks 0.005 and 0.01.

The stress scenario replaces the earlier common shift with independent per-name shifts. Each name's call midpoint is moved by \(\delta_i\sim U(-kh,kh)\) before rounding and quoting, with \(k\in\{4,8\}\) and \(h\) the half-spread; put quotes are unchanged. The shifts are design choices that test misspecification of the quote midpoint, not calibrated market effects. Because \(|\delta_i|>h\) with probability \(1-1/k\), the quoted call interval misses the true premium for about that share of names by construction. The observed miss shares are 73–75% at \(k=4\) and 86–87% at \(k=8\), except at \((t,h)=(0.05,0.01)\), where rounding raises them to 82% and 91%. Table C4 in Appendix C gives all 36 stress cells.

- E1 produced exactly the same decisions as E0 in every cell, so the vega check changed no order in this design. The diagnostics explain why: every name that fails the vega check already lacks a midpoint IV.
- E2 made no wrong-order decision in any baseline cell where it decided. In the baseline this zero follows from the quote model rather than from the screen: where \(h\ge t/2\) both quoted intervals contain the true premium, so non-overlapping CPIV intervals order the pair correctly. Its zero standard error reflects zero observed errors, not a bound on the error rate.
- In each of the 12 baseline cells where E2 decides any pair, E0 is also correct on every pair E2 orders. The E2 advantage therefore comes from the pairs it leaves undecided, not from E0 erring on the pairs E2 orders.
- At tick 0.05, E2 decided no pairs, because the resolution screen fails for every name: a \(\pm0.05\) price shock moves the 30-day at-the-money IV by 0.439 pp, more than four times \(\tau_{IV}\). Every truly ordered pair is therefore left undecided. E0 erred on 1.89–1.95% of its decided truly ordered pairs.
- At ticks 0.005 and 0.01, E0 erred on 0.06–0.18% of its decided truly ordered pairs and decided 51.9–54.5% of all pairs. E2 decided 1.3–20.3% of all pairs and left 78.3–98.5% of truly ordered pairs undecided, against 45.5–48.2% for E0.
- The claim rule credits a benefit in 9 of 18 baseline cells. The nine credits, computed from replicate means, come from three distinct \((n,t)\) comparisons: \(n=10\) at \(t=0.005\) (reduction 0.126 pp), \(n=50\) at \(t=0.005\) (0.175 pp), and \(n=50\) at \(t=0.01\) (0.079 pp). E0 does not depend on \(h\), so each comparison gives one reduction, repeated across three spreads. The rule fails at \(n=10\), \(t=0.01\), where the replicate-mean reduction is 0.057 pp against a replicate-mean threshold of 0.068 pp.
- Under stress, E2 is no longer error-free. Pooled over 200 replicates, E0's wrong-order share ranges from 4.3% to 44.5% of decided truly ordered pairs, and E2's from 0.0% to 37.3%; E2 made at least one wrong-order decision in 20 of 36 cells. The largest E2 share is at \(n=10\), \(t=0.005\), \(h=0.25\), \(k=8\): 254 wrong orders out of 681 decided truly ordered pairs (37.3%; Wilson 95% interval 33.7–41.0%), against 43.6% for E0 in the same cell.
- Where E2 decides, its wrong-order share is below E0's in every stress cell. The claim rule credits a benefit in 22 of 36 cells. The 12 uncredited tick-0.05 cells are those where E2 decides no pair. The other two uncredited cells (\(n=10\), \(k=8\), \(h=0.25\), \(t\in\{0.005,0.01\}\)) have replicate-mean reductions of 5.6 and 6.4 pp against replicate-mean thresholds of 6.2 and 7.0 pp.
- The replicate-mean reduction is 4.3–30.1 pp of decided pairs in the 24 cells where E2 decides (22 of them credited), bought with a replicate-mean increase of 24.5–39.4 pp in false exclusion. A credit therefore means that the reduction exceeds the Monte Carlo noise in the comparison; it does not show that E2 is error-free. E2 left 78–100% of truly ordered pairs undecided, against 46–69% for E0.

In the nine credited baseline cells the replicate-mean wrong-order share falls by 0.08–0.18 percentage points of decided pairs, an absolute reduction. It is bought with 32–53 percentage points more truly ordered pairs left undecided. Relative to E0's error share the reduction looks large, because E2 made no observed wrong decision, but that zero is an observation, not an estimate of E2's error rate.

The cost of abstention is the ratio of totals: correct E0 orders on pairs E2 leaves undecided, per E0 error avoided. In the baseline this ratio is 340–1,360 at ticks 0.005 and 0.01 and 51–56 at tick 0.05, because E0 errors are rare.

**Interval-only ablation.** E3 uses E2's bid–ask CPIV interval but drops the OTM-value, shock-inversion and \(\tau_{IV}\) screens, and orders a pair only when the two intervals are disjoint. It is a diagnostic ablation of the screen, not a proposed rule, and the claim rule of this section does not apply to it. Table C5 reports the 18 cells of the Section 7.9 setting under both stress designs, and Table C6 varies the true-CPIV range, \(\tau_{IV}\) and the tie margin.

At baseline, E3 made a wrong-order decision only at tick 0.05 and half-spread 0.01, where it erred on 0.08% (n=10) and 0.12% (n=50) of decided truly ordered pairs. Its decided share exceeds E2's by a factor that depends on the half-spread: about 2.1 to 3.2 at half-spread 0.01 with tick 0.005 or 0.01, about 1.25 to 1.9 at half-spread 0.05, and about 1.0 to 1.1 at half-spread 0.25, where both rules decide 1.3 to 1.5% of pairs. At tick 0.05, E2 decides no pair at any half-spread, while E3 decides 40 to 41% at half-spread 0.01 and 19 to 20% at half-spread 0.05. Averaged over the 18 cells, E3's wrong-order share is 0.01% and it decides 20.9% of pairs, against 6.9% for E2.

Under the call-offset stress, E2 still made no wrong-order decision, while E3 erred on 0.11 to 0.26% of decided truly ordered pairs at tick 0.005 and 0.01 with half-spread 0.01, and on 0.04 to 0.93% at tick 0.05 with half-spread 0.01 or 0.05.

Under per-name stress, E3 made more wrong-order decisions than E2 in all 24 cells where E2 decides (both values of k and n, ticks 0.005 and 0.01, and all three half-spreads), and fewer than E0 in all 36 cells. The interval alone therefore recovers part of the error reduction but not all of it. At half-spread 0.25 the two rules decide almost the same pairs (1.3 to 1.5%), but E3's wrong-order share is higher by at most 0.4 points at tick 0.005 and by up to 5.35 points at tick 0.01.

**Which screen does the work.** E3T adds the time-value check to E3. The check binds at tick 0.05, where at baseline E3T decides 36.6% of pairs against 40.4% for E3 at n=10 and half-spread 0.01 (Table C5). Over all cell-level comparisons of the wrong-order share, E3T differs from E3 by at most 1.19 pp. E3S adds only the shock-inversion check to E3. Its summaries are identical to E2's in all 2,160 comparisons of mean, MCSE and replicate count, across both designs, every stress level, the ten settings, every cell and every metric. In this design the shock check therefore excludes every pair that the time-value check excludes, and the whole reduction in wrong-order share from E3 to E2 is carried by the shock-inversion check.

Table C6 gives unweighted means of the cell values over the 18 cells of each design and stress level, for ten settings that each change one parameter. Across all ten settings, the ordering E2 < E3 < E0 holds under per-name stress with k=8. E0's wrong-order share falls as the true-CPIV range widens (baseline 3.31% at ±1 pp and 0.68% at ±10 pp), and under k=8 the gap E3 − E2 narrows from 5.9 to 2.7 points over the same range. Raising \(\tau_{IV}\) from 0.10 to 0.50 pp raises E2's baseline decided share from 6.9% to 15.1% and its per-name k=8 wrong-order share from 14.7% to 16.4%, a coverage–error trade-off inside the screen. Widening the tie margin from 0.5 to 1.0 pp leaves E2's baseline decided share at 6.9% and lowers its per-name k=8 wrong-order share from 14.7% to 13.4%, while E3's falls from 18.2% to 16.3%. E3 does not use \(\tau_{IV}\), so its values do not change with it.

In this synthetic design the interval-only variant is therefore not a substitute for the screen. It decides more pairs and recovers part of the error reduction under per-name stress, but it makes more wrong-order decisions than the screen wherever the screen decides under stress.

In this synthetic design the resolution screen trades coverage for a lower wrong-order share: 0.08–0.18 pp (replicate means) of decided pairs in the nine credited baseline cells, and 4.3–30.1 pp (replicate means) in the stress cells where it decides. It still made wrong-order decisions in 20 of 36 stress cells. The result does not show that the screen improves decisions on real quotes. The truth, the quote and spread model, the stress offset, the tie margin, and the universe are design choices, and no market quote was used.

## 8. Interpretation and limits

For carry screening, the local rule is \(|\Delta CPIV_{pp}|\approx|\partial CPIV_{pp}/\partial\log F|\,|\Delta\log F|\le\tau_{carry}\), followed by exact re-inversion for finite discrepancies. In the synthetic ATM, 30-day, 20%-IV example, 1 basis point of relative-forward mismatch corresponds locally to 0.087469 CPIV points; a 1-point tolerance therefore corresponds to about 11.4326 basis points. This conversion is specific to that configuration, not a default market tolerance.

The exact identity is an algebraic diagnostic under a specified European BSM inversion, not an economic explanation. Since CPIV and \(R\) are linked through the same option prices and common inputs, observing both does not provide two independent signals. A forward inferred from the same call–put pair and then used to force that pair's parity residual toward zero would be circular. Independent synchronized inputs, multiple strikes with leave-one-pair-out checks, or an externally sourced forward are needed for a separate validation design.

Quote intervals are useful for showing whether signs or ranks survive the selected bid–ask endpoints. They do not account automatically for quote dependence, stale legs, discrete ticks, hidden liquidity, transaction costs, exercise features, or model choice. Hentschel (2003) and Muravyev and Pearson (2020) motivate attention to these issues, but their empirical estimates are not transplanted into this synthetic experiment.

The ranking exercise is a controlled stress test. Its signal vectors are prescribed, its noise scales are chosen for illustration, and its distributional assumptions are not calibrated to market data. The Wilson intervals capture finite simulation uncertainty conditional on those choices only. The experiment cannot estimate real-world ranking error, sign error, strategy turnover, profitability, or expected returns.

We do not claim a novel parity identity or an empirically superior estimator. The contribution is the explicit specification and implementation of an integrated diagnostic workflow, together with documented synthetic numerical stress tests. The only workflow comparison in this version is the synthetic study of Section 7.9, which contrasts the Table 10 screen with raw-midpoint CPIV and the baseline vega check against the simulator's own truth, together with an interval-only ablation and a sensitivity sweep of that design. It does not compare minimally filtered or synchronized-input CPIV, and it uses no calibrated ground truth or market observations. Its credited benefits are absolute reductions in the replicate-mean wrong-order share of decided pairs: 0.08–0.18 percentage points in nine baseline cells from three distinct \((n,t)\) comparisons, and 4.3–30.1 percentage points in the 22 of 36 stress cells that the claim rule credits, all among the 24 cells where E2 decides. In both settings they are obtained by leaving far more truly ordered pairs undecided, and under per-name stress the screen still makes wrong-order decisions. It therefore establishes a coverage–error trade-off in a synthetic design, not incremental decision value or superior diagnostic performance. The interval-only ablation points the same way: without the screens the rule decides about three times as many pairs at baseline, but under per-name stress it makes more wrong-order decisions than the screen wherever the screen decides. Comparative validation on market quotes would additionally require a declared target and calibration source, real retained-data coverage, and ranking-stability checks; it is outside this synthetic note.

The study contains no historical option chain, underlying return panel, market-wide positions or liquidation data, out-of-sample test, transaction-cost-adjusted portfolio, or causal design. It therefore makes no alpha claim and is not a real-market-data or out-of-sample study. A real option-chain illustration is therefore not included (Section 9), and every illustration in this note is synthetic. A market study would need a defined universe, synchronized quotes and underlying observations, contract and exercise-style controls, explicit filters, a held-out time period, and a preregistered analysis plan before its results could support market claims.

The proposed staged checklist for future paired-option work is summarized in Table 10. It is an operational protocol, not market validation of the synthetic results.

**Table 10.** Operational diagnostic protocol proposed by this note; when required inputs or matching checks are unavailable, retain an unresolved status rather than infer a pass.

| Stage | Inputs | Check | Output/status | Action |
|:--|:--|:--|:--|:--|
| Contract matching | Underlying, option type, strike, expiry, exercise style, multiplier | Same pair definition and supported model | Matched / mismatch / unknown | Reject mismatch or analyze separately; do not pair unknown contracts; for American puts, use the European map only where the early-exercise premium is below the applicable tick and the bias is within tolerance (Section 6.2), otherwise invert with a stated American model |
| Timestamp validation | Option-leg and underlying timestamps; predeclared tolerance | Quote/spot synchronization | Synchronized / stale / unknown | Flag stale or unknown; do not silently substitute a spot |
| Carry/forward validation | Independently sourced synchronized spot, forward, rate, maturity; predeclared carry tolerance \(\tau_{carry}\) pp | Check \(F\approx S\exp((r-q)T)\); translate mismatch with the local gradient and re-invert finite mismatches | Validated / inconsistent / unknown | State tolerance in CPIV points; never infer the forward from the same option pair |
| Price validation | Bid/ask or selected price, common inputs, European bounds | Finite inputs and bound admissibility | Valid / theoretical-bound violation / unresolved | Preserve failure status; never clip prices into bounds |
| IV inversion | Price, common contract inputs, solver bracket and iteration rule | Root exists; report convergence and repricing error | IV with solver status / unresolved | Retain status and diagnostics; distinguish bracket rejection from invalid quote |
| Price resolution and precision | Declared tick, \(X_C\), \(X_P\), bid/ask, common inputs, predeclared \(\tau_{IV}\) in pp | Compare \(\min(X_C,X_P)\) with the applicable tick; test all leg-specific finite-shock roots; report worst-direction displacement | Tick-resolved / within \(\tau_{IV}\) / outside \(\tau_{IV}\) / known outside \(\tau_{IV}\) (partial) / unresolved / local-only | Tick resolution is not precision; only a tick-resolved case can pass \(\tau_{IV}\), and a finite displacement above \(\tau_{IV}\) rules out a pass even when the pair is unresolved; the baseline absolute-vega guard or local derivative alone is insufficient |
| CPIV measurement | Paired IVs, units, common inputs, optional quote sides | Compute pp spread and quote-implied range; report leg and average vegas | Point estimate and, when defined, endpoint range | Report contract/multiplier convention and all four-endpoint denominator |
| Rank diagnostics | Cross-sectional CPIV values or intervals, declared universe | Pairwise non-overlap, sign resolution, inversions, membership, denominators; retain one-sided bounds | Resolved comparisons / unresolved partial order, including incomplete endpoint cases | Keep pairs with bid = 0 or another non-invertible endpoint; use one-sided bounds only where they establish order, otherwise count unresolved rather than dropping or imputing |

## 9. Reproducibility and declarations

The common-map identity checker covers unequal-volatility European prices, an American-tree-origin put, stale source-spot quotes inverted at a different common spot, and admissible premium perturbations. Its maximum residual-versus-integrated-vega gap is below \(1.2\times10^{-14}\) currency units across these four constructed cases. A separate 180-digit standard-library Decimal implementation audits the generated near-bound cases. Both are numerical consistency checks maintained by the same author, not an independent replication, proof, or formal peer review. A supplemental checker, written by the author with AI assistance from the written specification, was run against the fixed grid and matched the project pipeline to the reported precision; this is an implementation cross-check, not independent human replication. This note reports selected assumptions and outputs but does not contain the analysis source or complete machine-readable input bundle.

The supplemental checker matched the project pipeline to the reported precision for the 624/96 pass/fail counts in the 720-cell grid; the centered error median/p95/maximum (0.00007858/0.087203/1.23552 pp); the cubic-scaling slope (median 3.0003, range 2.8733–3.0441, \(n=104\)); and every signed reference-offset summary in Table 1, including 168 skipped evaluations at the 10-volatility-point offset. Both implementations used the same written grid specification, so specification errors may be shared. These matches support implementation reproducibility conditional on that specification, not independent replication or external validation.

**Funding and in-kind support:** No external cash funding was received. The author received a complimentary one-month HyperTracker Surge subscription from CoinMarketMan as in-kind support. The provider supplied no data or analytical input for this note: no HyperTracker data are used, and all reported results are synthetic.  
**Competing interests:** The author discloses the complimentary CoinMarketMan subscription above as a potential competing interest. The provider supplied no data or analytical input, and no HyperTracker data are used in the results.  
**Data and code availability:** No market data or external quote dataset are used. The results are synthetic. A real option-chain illustration was considered and is not included. The free sources checked do not clearly allow publication of their quotes: Bybit's public options endpoint, which provides bid and ask quotes, is covered by terms that bar publishing platform price data without written consent (Bybit Card Terms and Conditions, section 15, checked 20 October 2026); a downloadable SPY chain is labelled MIT, but its raw data come from a third-party vendor whose terms were not verified; and a crypto options file provides no bid or ask quotes. No public chain with a clear publication licence was found, so all illustrations in this note are synthetic. The v28 review package ([10.5281/zenodo.23442601](https://doi.org/10.5281/zenodo.23442601)) archives the analysis code and generated inputs for the results of this note, except the per-name stress analysis of Section 7.9, which replaces the common-shift scenario in that package. The complete code, including `research/cpiv/workflow_stress_per_name.py`, `research/cpiv/workflow_ablation.py`, and their outputs, is in the GitHub repository ([bravforcode/Quant-paper](https://github.com/bravforcode/Quant-paper)). This manuscript alone does not contain all files required to rerun the analyses.  
**Acknowledgements:** None declared.  
**Use of generative AI:** Perplexity was used for research, including literature discovery. Claude (Anthropic) and OpenAI Codex agents assisted the author with drafting and editing of the text, writing and reviewing the analysis and build code, checking mathematical identities, and verifying the review package. The author set the research questions, designs, and claim rules, ran and checked the analyses against the code and outputs, and takes responsibility for all content and conclusions.

## Appendix A. Supplemental fixed-seed illustration

This supplemental fixed-seed, precomputed ten-name illustration is a presentation aid, not a result of the analyses in this note. Its slider selects among seven discrete, unequally spaced noise levels; it does not reprice options, invert implied volatility, or run Monte Carlo in the browser. At each level, the stored Monte Carlo summary is separate from one example draw, and plotted values share a fixed symmetric axis. The slider exists only in the HTML build; print formats show a static rendering.

<!-- CPIV_INTERACTIVE_WIDGET -->

## Appendix B. Reproduction commands

Requirements: `uv` 0.11.8 and Python 3.12 or newer, as declared in `pyproject.toml`. On 18 October 2026 the documented `uv` commands below were run verbatim in two clean copies of the sources, from which generated outputs, `dist/`, `site/`, and virtual environments had been removed. The table summarises the runs. The interval-only ablation and the early-exercise comparison were each run once in the source checkout after those clean-copy runs and are not covered by the table.

| Environment | Python | Exit status | Compared | Differences |
|:-----------------|:-------------|:---------|:-----------------------|:---------------------------------|
| Windows, PowerShell, two clean copies | 3.14.3 (locked environment) | 0 in both copies | CSV and PNG files and manifests identical across the two runs | SVG files: embedded timestamp and generated element identifiers; two JSON files: recorded output path |
| Windows, PowerShell | 3.12 and 3.13 | 0 | Completed; not itemised | Not itemised |
| WSL Ubuntu | 3.12.3 | 0 | CSV text fields identical; CPIV test modules passed | Numeric CSV fields differ by at most 3.34e-10; JSON files differ in recorded paths, the Python version, and the hash of the local approximation grid, whose residuals differ in the last digits; PNG and SVG files are not byte-identical apart from the timestamp |

Test failures in the clean copies were confined to tests of other deliverables that read build outputs absent from those copies; the full suite passed in the source checkout, where those outputs are present. The repository configures a Linux and Windows CI matrix for Python 3.12–3.14 (`.github/workflows/cpiv-repro.yml`); browser tests of the HTML build skip where Chromium is not installed. Repeating a run on one machine with the same code establishes determinism, not independent correctness. Byte identity across platforms is not claimed. The shell-neutral commands below are intended for both PowerShell and Bash. The source package is archived as described in the Data and code availability statement.

Run from a source checkout of the project root. The commands regenerate the synthetic design and diagnostics in the stated output directory. Use a fresh output directory for a subsequent run; the source package and code archive are not part of this standalone manuscript.

```text
uv sync --locked --no-install-project
uv run python -m scripts.reproduce_cpiv_methods --output research/cpiv/generated/repro
uv run python -m research.cpiv.workflow_stress_per_name --output research/cpiv/generated/stress_per_name
uv run python -m research.cpiv.workflow_ablation --output research/cpiv/generated/workflow_ablation_r32
uv run python -m research.cpiv.early_exercise_vs_tick --output research/cpiv/generated/early_exercise_vs_tick
uv run python -m pytest tests -q
```


## Appendix C. Supplementary benchmark and cross-check tables

The tables below are author-run synthetic checks. They are not independent replication, and the closed-form benchmark covers only Gaussian CPIV-space noise.

**Table C1.** Holm–Bonferroni family for the ranking-stress checks (one family of 1,050 tests, alpha 0.05). Closed-form comparisons use the Gaussian benchmark in Section 7.5. Fresh-versus-stored comparisons use three fresh seeds (31415926, 27182818, 16180339), with 1,000 replicates per seed, against the stored 300-replicate run. The generating script is research/cpiv/gaussian_rank_benchmark.py; per-test rows are in the companion CSV. Appendix D records an earlier fresh-seed value for one inversion cell.

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

**Table C4.** Per-name call-midpoint stress in the design of Section 7.9. Each name's call midpoint is shifted by an independent draw from \(U(-kh,kh)\) before rounding and quoting, with \(h\) the half-spread and \(k\in\{4,8\}\); put quotes are unchanged. Wrong-order and false-exclusion shares are pooled over the 200 replicates. The two numeric columns before Credited give replicate-mean reductions in E0 minus E2 wrong-order share and the threshold of the claim rule (twice the combined Monte Carlo standard error), from the companion CSV. These replicate-mean quantities are the ones quoted in Sections 7.9 and 8; they differ from differences between the pooled shares shown here. The bracketed interval is a Wilson 95% interval for the pooled E2 wrong-order share. Quote misses is the share of names whose quoted call or put interval excludes the true premium. Credited applies the claim rule in Section 7.9 to replicate means; its MCSE terms are in the companion CSV. Tick and half-spread are in price units. A dash marks a method that made no decisions.

| n | k | Tick | Half-spread | Wrong, E0 | Wrong, E2 | Wilson 95%, E2 | False excl., E0 / E2 | Quote misses | Reduction, rep. mean (pp) | Threshold, 2 × MCSE (pp) | Credited |
|:--|--:|--:|--:|--:|--:|:--|:--|--:|--:|--:|:--|
| 10 | 4 | 0.005 | 0.01 | 4.4% | 0.0% | [0.0, 0.2] | 48.3% / 78.6% | 73.5% | 4.40 | 1.01 | Yes |
| 10 | 4 | 0.005 | 0.05 | 17.5% | 0.7% | [0.3, 1.3] | 53.6% / 83.3% | 73.5% | 17.22 | 2.17 | Yes |
| 10 | 4 | 0.005 | 0.25 | 38.2% | 13.4% | [10.8, 16.6] | 62.2% / 93.4% | 73.5% | 24.87 | 4.74 | Yes |
| 10 | 4 | 0.01 | 0.01 | 4.3% | 0.0% | [0.0, 0.3] | 48.3% / 85.9% | 73.0% | 4.35 | 1.01 | Yes |
| 10 | 4 | 0.01 | 0.05 | 17.7% | 0.6% | [0.3, 1.4] | 53.9% / 88.5% | 73.5% | 17.51 | 2.19 | Yes |
| 10 | 4 | 0.01 | 0.25 | 38.2% | 9.5% | [6.8, 13.1] | 62.2% / 95.9% | 73.6% | 30.13 | 4.28 | Yes |
| 10 | 4 | 0.05 | 0.01 | 5.0% | — | — | 51.1% / 100.0% | 81.7% | — | — | No |
| 10 | 4 | 0.05 | 0.05 | 16.7% | — | — | 55.9% / 100.0% | 73.7% | — | — | No |
| 10 | 4 | 0.05 | 0.25 | 37.6% | — | — | 63.6% / 100.0% | 73.5% | — | — | No |
| 10 | 8 | 0.005 | 0.01 | 8.3% | 0.5% | [0.2, 0.9] | 48.8% / 79.0% | 86.7% | 8.01 | 1.44 | Yes |
| 10 | 8 | 0.005 | 0.05 | 24.6% | 8.5% | [7.1, 10.1] | 56.7% / 83.8% | 86.6% | 15.83 | 3.51 | Yes |
| 10 | 8 | 0.005 | 0.25 | 43.6% | 37.3% | [33.7, 41.0] | 66.4% / 91.6% | 86.5% | 5.58 | 6.25 | No |
| 10 | 8 | 0.01 | 0.01 | 8.5% | 0.1% | [0.0, 0.5] | 49.1% / 86.4% | 86.8% | 8.73 | 1.43 | Yes |
| 10 | 8 | 0.01 | 0.05 | 24.6% | 7.1% | [5.5, 9.0] | 56.8% / 89.4% | 86.4% | 17.26 | 3.60 | Yes |
| 10 | 8 | 0.01 | 0.25 | 43.5% | 36.6% | [32.4, 41.1] | 66.4% / 94.3% | 86.5% | 6.38 | 7.02 | No |
| 10 | 8 | 0.05 | 0.01 | 7.1% | — | — | 52.6% / 100.0% | 91.0% | — | — | No |
| 10 | 8 | 0.05 | 0.05 | 23.6% | — | — | 59.0% / 100.0% | 87.1% | — | — | No |
| 10 | 8 | 0.05 | 0.25 | 43.6% | — | — | 68.3% / 100.0% | 86.4% | — | — | No |
| 50 | 4 | 0.005 | 0.01 | 5.3% | 0.0% | [0.0, 0.0] | 45.9% / 78.6% | 74.7% | 5.36 | 0.44 | Yes |
| 50 | 4 | 0.005 | 0.05 | 19.3% | 0.7% | [0.6, 0.8] | 52.3% / 83.2% | 74.9% | 18.60 | 0.74 | Yes |
| 50 | 4 | 0.005 | 0.25 | 38.4% | 14.8% | [14.2, 15.4] | 61.2% / 94.2% | 74.9% | 22.88 | 1.59 | Yes |
| 50 | 4 | 0.01 | 0.01 | 5.3% | 0.0% | [0.0, 0.0] | 46.3% / 85.7% | 74.7% | 5.31 | 0.44 | Yes |
| 50 | 4 | 0.01 | 0.05 | 19.3% | 0.4% | [0.4, 0.5] | 52.5% / 88.6% | 74.9% | 18.82 | 0.74 | Yes |
| 50 | 4 | 0.01 | 0.25 | 38.4% | 12.8% | [12.1, 13.5] | 61.3% / 96.1% | 74.9% | 25.14 | 1.69 | Yes |
| 50 | 4 | 0.05 | 0.01 | 4.4% | — | — | 50.7% / 100.0% | 82.2% | — | — | No |
| 50 | 4 | 0.05 | 0.05 | 17.3% | — | — | 55.4% / 100.0% | 74.5% | — | — | No |
| 50 | 4 | 0.05 | 0.25 | 37.6% | — | — | 63.4% / 100.0% | 74.8% | — | — | No |
| 50 | 8 | 0.005 | 0.01 | 9.5% | 0.3% | [0.3, 0.4] | 48.5% / 78.9% | 87.4% | 9.21 | 0.55 | Yes |
| 50 | 8 | 0.005 | 0.05 | 26.7% | 8.3% | [8.0, 8.6] | 57.4% / 83.3% | 87.4% | 18.37 | 0.99 | Yes |
| 50 | 8 | 0.005 | 0.25 | 44.5% | 35.6% | [34.9, 36.3] | 67.1% / 91.5% | 87.3% | 8.80 | 2.04 | Yes |
| 50 | 8 | 0.01 | 0.01 | 9.6% | 0.2% | [0.1, 0.2] | 48.6% / 85.9% | 87.0% | 9.37 | 0.55 | Yes |
| 50 | 8 | 0.01 | 0.05 | 26.7% | 6.9% | [6.6, 7.2] | 57.5% / 88.9% | 87.3% | 19.88 | 0.99 | Yes |
| 50 | 8 | 0.01 | 0.25 | 44.5% | 33.8% | [33.0, 34.6] | 67.1% / 93.9% | 87.3% | 10.50 | 2.20 | Yes |
| 50 | 8 | 0.05 | 0.01 | 8.0% | — | — | 51.8% / 100.0% | 90.8% | — | — | No |
| 50 | 8 | 0.05 | 0.05 | 25.2% | — | — | 59.7% / 100.0% | 87.0% | — | — | No |
| 50 | 8 | 0.05 | 0.25 | 44.0% | — | — | 68.9% / 100.0% | 87.2% | — | — | No |

**Table C5.** Interval-only ablation in the Section 7.9 setting. Entries are replicate means. A replicate contributes to a metric only where that metric is defined; the counts and MCSEs are in the companion CSV. Decided is the share of all pairs given an order at baseline. Wrong is the wrong-order share of decided truly ordered pairs. Values separated by slashes are E2, E3 and E3T (E3 plus the time-value check) in that order. E3S (E3 plus the shock-inversion check) gives exactly the E2 values in every entry and is omitted. Baseline is the call-offset design with no offset; the call-offset column adds 1.5 half-spreads to the call midpoint; the per-name columns shift each call midpoint by a draw from U(−kh, kh) with k=4 and k=8. Because these are replicate means, the per-name E2 values differ from the pooled shares of Table C4 (for example, 37.9% here and 37.3% in Table C4 for n=10, tick 0.005, half-spread 0.25, k=8). A dash marks a cell where E2 decided no pair under that stress.

| n | Tick | Half-spread | Decided, baseline, E2 / E3 / E3T | Wrong, E3, baseline | Wrong, E3, call offset 1.5 | Wrong, E2 / E3 / E3T, per-name k=4 | Wrong, E2 / E3 / E3T, per-name k=8 |
|:--|--:|--:|:--|--:|--:|:--|:--|
| 10 | 0.005 | 0.01 | 20.2% / 42.4% / 42.4% | 0.00% | 0.11% | 0.00% / 0.56% / 0.56% | 0.55% / 3.14% / 3.14% |
| 10 | 0.005 | 0.05 | 15.5% / 19.4% / 19.4% | 0.00% | 0.00% | 0.46% / 2.77% / 2.77% | 8.80% / 12.81% / 12.81% |
| 10 | 0.005 | 0.25 | 1.4% / 1.4% / 1.4% | 0.00% | 0.00% | 12.38% / 12.42% / 12.42% | 37.86% / 38.26% / 38.26% |
| 10 | 0.01 | 0.01 | 13.1% / 42.2% / 42.2% | 0.00% | 0.12% | 0.00% / 0.57% / 0.57% | 0.03% / 3.22% / 3.22% |
| 10 | 0.01 | 0.05 | 10.4% / 19.5% / 19.5% | 0.00% | 0.00% | 0.39% / 2.67% / 2.67% | 7.28% / 12.84% / 12.84% |
| 10 | 0.01 | 0.25 | 1.3% / 1.4% / 1.4% | 0.00% | 0.00% | 7.20% / 12.54% / 12.54% | 36.79% / 38.26% / 38.26% |
| 10 | 0.05 | 0.01 | 0.0% / 40.4% / 36.6% | 0.08% | 0.77% | — / 1.58% / 0.99% | — / 3.52% / 3.37% |
| 10 | 0.05 | 0.05 | 0.0% / 19.4% / 19.4% | 0.00% | 0.04% | — / 3.25% / 3.25% | — / 14.72% / 14.72% |
| 10 | 0.05 | 0.25 | 0.0% / 1.4% / 1.4% | 0.00% | 0.00% | — / 11.60% / 11.60% | — / 37.64% / 37.64% |
| 50 | 0.005 | 0.01 | 20.3% / 42.6% / 42.6% | 0.00% | 0.17% | 0.00% / 0.61% / 0.61% | 0.31% / 3.61% / 3.61% |
| 50 | 0.005 | 0.05 | 15.3% / 19.0% / 19.0% | 0.00% | 0.00% | 0.69% / 2.84% / 2.84% | 8.41% / 14.77% / 14.77% |
| 50 | 0.005 | 0.25 | 1.5% / 1.5% / 1.5% | 0.00% | 0.00% | 15.48% / 15.61% / 15.61% | 35.65% / 35.67% / 35.67% |
| 50 | 0.01 | 0.01 | 13.6% / 42.3% / 42.3% | 0.00% | 0.26% | 0.00% / 0.64% / 0.64% | 0.16% / 3.58% / 3.58% |
| 50 | 0.01 | 0.05 | 10.6% / 19.1% / 19.1% | 0.00% | 0.00% | 0.44% / 2.85% / 2.85% | 6.82% / 14.76% / 14.76% |
| 50 | 0.01 | 0.25 | 1.4% / 1.5% / 1.5% | 0.00% | 0.00% | 13.21% / 15.59% / 15.59% | 33.93% / 35.67% / 35.67% |
| 50 | 0.05 | 0.01 | 0.0% / 41.0% / 37.7% | 0.12% | 0.93% | — / 1.50% / 0.97% | — / 4.19% / 3.61% |
| 50 | 0.05 | 0.05 | 0.0% / 19.6% / 19.6% | 0.00% | 0.21% | — / 2.91% / 2.91% | — / 14.55% / 14.55% |
| 50 | 0.05 | 0.25 | 0.0% / 1.5% / 1.5% | 0.00% | 0.00% | — / 15.40% / 15.40% | — / 35.55% / 35.55% |

**Table C6.** Sensitivity of the Section 7.9 comparison to the true-CPIV range, to \(\tau_{IV}\) and to the tie margin. Entries are unweighted means of the cell values over the 18 cells (n, tick and half-spread) of each design and stress level, with no MCSE; wrong and decided entries are percentages and the cell counts are integers. Wrong is the wrong-order share of decided truly ordered pairs; decided is the share of all pairs given an order. E2 averages only over the cells where it decided, so its cell count is given in the second column. Each row changes one parameter from the first row, the Section 7.9 setting. E3S is omitted because its values equal E2's in every row. The companion CSV gives k=4 and every cell.

| True-CPIV range; \(\tau_{IV}\); tie margin | E2 cells with a decision, baseline / k=8 | Wrong, baseline, E0 / E2 / E3 / E3T | Decided, baseline, E2 / E3 | Wrong, per-name k=8, E0 / E2 / E3 / E3T | Decided, per-name k=8, E2 / E3 |
|:--|:--|--:|--:|--:|--:|
| ±5 pp; 0.10 pp; 0.5 pp (Section 7.9) | 12 / 12 | 0.71 / 0.00 / 0.01 / 0.01 | 6.9 / 20.9 | 25.87 / 14.72 / 18.15 / 18.11 | 8.3 / 24.4 |
| ±1 pp; 0.10 pp; 0.5 pp | 8 / 12 | 3.31 / 0.00 / 0.03 / 0.01 | 3.3 / 8.4 | 37.23 / 26.58 / 32.45 / 32.34 | 7.1 / 20.6 |
| ±2.5 pp; 0.10 pp; 0.5 pp | 8 / 12 | 1.38 / 0.00 / 0.04 / 0.01 | 5.6 / 16.0 | 31.21 / 19.97 / 24.45 / 24.36 | 7.8 / 22.5 |
| ±10 pp; 0.10 pp; 0.5 pp | 12 / 12 | 0.68 / 0.00 / 0.01 / 0.01 | 7.9 / 24.4 | 20.78 / 9.93 / 12.65 / 12.60 | 8.3 / 25.8 |
| ±5 pp; 0.05 pp; 0.5 pp | 6 / 6 | 0.71 / 0.00 / 0.01 / 0.01 | 2.8 / 20.9 | 25.87 / 14.17 / 18.15 / 18.11 | 3.3 / 24.4 |
| ±5 pp; 0.20 pp; 0.5 pp | 12 / 12 | 0.71 / 0.00 / 0.01 / 0.01 | 9.1 / 20.9 | 25.87 / 15.87 / 18.15 / 18.11 | 11.1 / 24.4 |
| ±5 pp; 0.25 pp; 0.5 pp | 12 / 12 | 0.71 / 0.00 / 0.01 / 0.01 | 10.0 / 20.9 | 25.87 / 16.35 / 18.15 / 18.11 | 12.2 / 24.4 |
| ±5 pp; 0.50 pp; 0.5 pp | 18 / 18 | 0.71 / 0.00 / 0.01 / 0.01 | 15.1 / 20.9 | 25.87 / 16.39 / 18.15 / 18.11 | 18.1 / 24.4 |
| ±5 pp; 0.10 pp; 0.25 pp | 12 / 12 | 1.17 / 0.00 / 0.03 / 0.02 | 6.9 / 20.9 | 27.01 / 15.84 / 19.35 / 19.31 | 8.3 / 24.4 |
| ±5 pp; 0.10 pp; 1.0 pp | 12 / 12 | 0.31 / 0.00 / 0.00 / 0.00 | 6.9 / 20.9 | 24.36 / 13.38 / 16.30 / 16.26 | 8.3 / 24.4 |

**Table C7.** Early-exercise premium of American puts against the price ticks, and the CPIV bias from the European map. Synthetic grid of 270 configurations generated by research/cpiv/early_exercise_vs_tick.py. Premium is American minus European in price units; premium shares use all configurations, and bias columns use the configurations with a defined bias (a bracket failure leaves the bias undefined; the count is in parentheses). Shares are percentages; the bias is in volatility percentage points. The first row pools all configurations.

| Group | Configurations (bias defined) | Premium median | Premium max | Premium ≥ 0.005 | Premium ≥ 0.01 | Premium ≥ 0.05 | \|Bias\| median (pp) | \|Bias\| max (pp) | \|Bias\| > 0.05 pp | \|Bias\| > 0.10 pp |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| All | 270 (268) | 0.0076 | 5.91 | 51.5 | 48.1 | 38.5 | 0.069 | 51.79 | 51.5 | 47.4 |
| \(S/K=0.8\) | 54 (52) | 0.3483 | 5.91 | 66.7 | 66.7 | 66.7 | 4.195 | 51.79 | 69.2 | 69.2 |
| \(S/K=0.9\) | 54 (54) | 0.1555 | 3.55 | 66.7 | 66.7 | 64.8 | 1.019 | 18.70 | 66.7 | 66.7 |
| \(S/K=1.0\) | 54 (54) | 0.0190 | 0.52 | 66.7 | 61.1 | 38.9 | 0.146 | 1.46 | 61.1 | 57.4 |
| \(S/K=1.1\) | 54 (54) | 0.0006 | 0.31 | 37.0 | 29.6 | 13.0 | 0.019 | 0.92 | 35.2 | 27.8 |
| \(S/K=1.2\) | 54 (54) | 2.2e-06 | 0.19 | 20.4 | 16.7 | 9.3 | 0.005 | 0.65 | 25.9 | 16.7 |

## Appendix D. Revision history

- **r33 (20 October 2026).** Sections 8 and 9 state the licence limit on real option-chain data; no real chain is included, and every illustration remains synthetic. No analysis, table or figure changed.
- **r32 (19 October 2026).** Early-exercise premium compared with price ticks (Section 6.2, Table C7); replicate-mean columns for the per-name stress table (Table C4); the interval-only ablation extended with two intermediate variants (E3T, E3S) and with τ_IV of 0.25 and 0.50 pp and tie margins of 0.25 and 1.0 pp (Section 7.9, Tables C5 and C6); "identification" replaced by "tick resolution" where it names the pair status; a "known outside τ_IV" status for unresolved pairs whose finite-shock displacement already exceeds τ_IV; "reliability" replaced by "stability" in the Section 7.5 heading; references to a market-wide position census, liquidation census and crypto funding rate removed.
- **r31 (19 October 2026).** Interval-only ablation and sensitivity sweep added to Section 7.9 (Tables C5 and C6).
- **Earlier revisions.** See the repository commit history. The r26 caption reported a fresh concave-magnitude value of 0.1640 under seed offset 0, against 0.1647 under the present fresh seeds; the difference is about 0.6 Monte Carlo standard errors, and the standardised differences in Table C1 are therefore stream-dependent at this precision.

## References

Barone-Adesi, G., & Whaley, R. E. (1987). Efficient analytic approximation of American option values. *Journal of Finance, 42*(2), 301–320.

Black, F., & Scholes, M. (1973). The pricing of options and corporate liabilities. *Journal of Political Economy, 81*(3), 637–654. <https://doi.org/10.1086/260062>

Cox, J. C., Ross, S. A., & Rubinstein, M. (1979). Option pricing: A simplified approach. *Journal of Financial Economics, 7*(3), 229–263. <https://doi.org/10.1016/0304-405X(79)90015-1>

Cremers, M., & Weinbaum, D. (2010). Deviations from put-call parity and stock return predictability. *Journal of Financial and Quantitative Analysis, 45*(2), 335–367. <https://doi.org/10.1017/S002210901000013X>

Doran, J. S., Fodor, A., & Jiang, D. (2013). Call-put implied volatility spreads and option returns. *The Review of Asset Pricing Studies, 3*(2), 258–290. <https://doi.org/10.1093/rapstu/rat006>

Goncalves-Pinto, L., Grundy, B. D., Hameed, A., van der Heijden, T., & Zhu, Y. (2020). Why do option prices predict stock returns? The role of price pressure in the stock market. *Management Science, 66*(9), 3903–3926. <https://doi.org/10.1287/mnsc.2019.3398>

Hentschel, L. (2003). Errors in implied volatility estimation. *Journal of Financial and Quantitative Analysis, 38*(4), 779–810. <https://doi.org/10.2307/4126743>

Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics, 6*(2), 65–70.

Jarrow, R., & Rudd, A. (1983). *Option pricing*. Dow Jones-Irwin.

Leisen, D. P. J., & Reimer, M. (1996). Binomial models for option valuation: Examining and improving convergence. *Applied Mathematical Finance, 3*(4), 319–338.

Merton, R. C. (1973). Theory of rational option pricing. *The Bell Journal of Economics and Management Science, 4*(1), 141–183. <https://doi.org/10.2307/3003143>

Muravyev, D., & Pearson, N. D. (2020). Options trading costs are lower than you think. *The Review of Financial Studies, 33*(11), 4973–5014. <https://doi.org/10.1093/rfs/hhaa010>

Sokolov, M. (2019). *A deeper look at the implied volatility spread as a predictor of stock returns* [Doctoral dissertation, University of Rochester]. University of Rochester Research Repository. <https://urresearch.rochester.edu/fileDownloadForInstitutionalItem.action?itemId=35841&itemFileId=188460>

Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association, 22*(158), 209–212.
