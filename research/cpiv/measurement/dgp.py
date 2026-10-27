"""Ground-truth market generator for the CPIV measurement study.

The generator builds an arbitrage-consistent market of **American** options on a
non-dividend-paying underlying. The call leg is worth exactly its European
value (no early exercise without dividends); the put leg carries a genuine
early-exercise premium. Pricing both legs under one common European Black–
Scholes–Merton map therefore produces a **known, non-zero** call–put implied
volatility spread: the volatility-equivalent of the exercise premium.

Because the fair value is fixed before any quote exists, the protocol can be
scored for *accuracy*, not only for coverage and stability. That is the one
thing a licensed market sample can never provide, and it is what makes this
benchmark a pre-registration instrument rather than a substitute for market
evidence.

The quote layer then adds declared microstructure: tick rounding, bid/ask
width, timestamp lag, and a small number of feed defects. No market data is
read and no network access is used.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import numpy as np
from research.cpiv import build_demo as bsm
from research.cpiv.measurement.inversion import invert_leg
from research.cpiv.measurement.pricing import american_put_prices
from research.cpiv.measurement.quotes import QuotePair

FIRST_SESSION = datetime(2026, 1, 5, 15, 55, tzinfo=UTC)
DEFECT_NONE = "none"
DEFECT_STALE = "stale_quote"
DEFECT_CROSSED = "crossed_quote"
DEFECT_OUT_OF_BOUNDS = "out_of_bounds_quote"
DEFECT_CONTRACT = "contract_mismatch"
DEFECT_MISSING_LEG = "missing_leg"


@dataclass(frozen=True)
class GeneratorConfig:
    """Declared parameters of the synthetic market."""

    seed: int = 20261022
    underlyings: tuple[str, ...] = ("SIM-A", "SIM-B")
    base_spots: tuple[float, ...] = (100.0, 250.0)
    trading_days: int = 30
    expiries: tuple[int, ...] = (14, 30, 60)
    strike_fractions: tuple[float, ...] = (0.90, 0.95, 1.00, 1.05, 1.10)
    rate: float = 0.05
    dividend_yield: float = 0.0
    base_vol: float = 0.22
    vol_term_slope: float = 0.0012
    vol_skew: float = -1.10
    tick: float = 0.01
    tree_steps: int = 800
    half_spread_ticks: int = 1
    wing_spread_ticks: int = 1
    short_dated_extra_ticks: int = 1
    wide_day_period: int = 7
    quote_sync_tolerance_seconds: float = 2.0
    timestamp_jitter_seconds: float = 0.35
    stale_quote_rate: float = 0.015
    crossed_quote_rate: float = 0.008
    out_of_bounds_rate: float = 0.005
    contract_mismatch_rate: float = 0.005
    missing_leg_rate: float = 0.004
    spot_drift_sd: float = 0.012

    def __post_init__(self) -> None:
        if len(self.underlyings) != len(self.base_spots):
            raise ValueError("each underlying needs one base spot")
        if self.tree_steps < 1:
            raise ValueError("tree_steps must be positive")
        if self.tick <= 0.0:
            raise ValueError("tick must be positive")


def american_put_price(
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
    sigma: float,
    steps: int = 800,
) -> float:
    """Cox-Ross-Rubinstein price of an American put, vectorised over nodes.

    The tree is the same construction used by :mod:`research.cpiv.build_demo`;
    only the backward induction is evaluated with array operations.
    """
    maturity = days / 365.0
    dt = maturity / steps
    up = math.exp(sigma * math.sqrt(dt))
    down = 1.0 / up
    growth = math.exp((rate - dividend_yield) * dt)
    probability = (growth - down) / (up - down)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("CRR risk-neutral probability must lie in [0, 1]")
    discount = math.exp(-rate * dt)
    up_moves = np.arange(steps + 1, dtype=float)
    stock = spot * (up**up_moves) * (down ** (steps - up_moves))
    values = np.maximum(strike - stock, 0.0)
    for time_step in range(steps - 1, -1, -1):
        nodes = np.arange(time_step + 1, dtype=float)
        stock = spot * (up**nodes) * (down ** (time_step - nodes))
        continuation = discount * (
            probability * values[1 : time_step + 2]
            + (1.0 - probability) * values[0 : time_step + 1]
        )
        values[0 : time_step + 1] = np.maximum(
            continuation, np.maximum(strike - stock, 0.0)
        )
    return float(values[0])


def _round_down(value: float, tick: float) -> float:
    return math.floor(value / tick + 1e-9) * tick


def _round_up(value: float, tick: float) -> float:
    return math.ceil(value / tick - 1e-9) * tick


def _half_spread_ticks(config: GeneratorConfig, log_moneyness: float, days: int) -> int:
    """Half-spread in ticks: wider in the wings and at the short end.

    The wing threshold sits at 0.09 in log-moneyness so that both the 0.90 and
    the 1.10 strike bucket qualify: log(1.10) is 0.0953, which a 0.10
    threshold would have missed and left the call wing artificially tight.
    """
    extra = 0
    if abs(log_moneyness) >= 0.09:
        extra += config.wing_spread_ticks
    if days <= 14:
        extra += config.short_dated_extra_ticks
    return config.half_spread_ticks + extra


def _quote(fair: float, half_ticks: int, tick: float) -> tuple[float, float]:
    half = half_ticks * tick
    bid = _round_down(fair - half, tick)
    ask = _round_up(fair + half, tick)
    if bid < 0.0:
        bid = 0.0
    if ask <= 0.0:
        ask = tick
    return bid, ask


def _true_cpiv(
    spot: float,
    strike: float,
    days: int,
    rate: float,
    dividend_yield: float,
    call_fair: float,
    put_fair: float,
) -> tuple[float | None, float | None, float | None]:
    """The CPIV a perfect measurement of the unrounded fair values would give."""
    call = invert_leg("call", call_fair, spot, strike, days, rate, dividend_yield)
    put = invert_leg("put", put_fair, spot, strike, days, rate, dividend_yield)
    if not call.ok or not put.ok:
        return None, None, None
    assert call.iv is not None and put.iv is not None
    return 100.0 * (call.iv - put.iv), call.iv, put.iv


@dataclass(frozen=True)
class _PairSpec:
    """One attempted pair, recorded before the put leg has been priced.

    The generator is written in two phases on purpose. The first phase draws
    every random number in the declared order and records the option's
    contractual terms; the second phase prices the whole put leg in one batch
    and assembles the quotes. Splitting the phases this way keeps the random
    stream identical to a single-pass generator while making the market cheap
    enough to replicate across many seeds.
    """

    underlying: str
    day_label: str
    day_index: int
    strike: float
    put_strike: float
    days: int
    spot: float
    sigma: float
    snapshot: datetime
    call_fair: float
    call_bid: float
    call_ask: float
    call_timestamp: datetime
    put_timestamp: datetime
    spot_timestamp: datetime
    defect: str
    log_moneyness: float
    half_ticks: int
    wide_session: bool


def generate_market(
    config: GeneratorConfig,
) -> tuple[list[QuotePair], dict[str, int]]:
    """Generate the synthetic market and the count of every injected defect."""
    specs: list[_PairSpec] = []
    counts: dict[str, int] = {}
    for index, (underlying, base_spot) in enumerate(
        zip(config.underlyings, config.base_spots, strict=True)
    ):
        rng = random.Random(config.seed + 1009 * index)
        spot = base_spot
        for day_index in range(config.trading_days):
            day_label = f"{underlying}-D{day_index:02d}"
            if day_index > 0:
                spot *= math.exp(rng.gauss(0.0, config.spot_drift_sd))
            snapshot = FIRST_SESSION + timedelta(days=day_index)
            wide_session = config.wide_day_period > 0 and day_index % config.wide_day_period == 0
            for days in config.expiries:
                for fraction in config.strike_fractions:
                    strike = round(spot * fraction, 2)
                    log_moneyness = math.log(strike / spot)
                    sigma = (
                        config.base_vol
                        + config.vol_term_slope * days
                        + config.vol_skew * log_moneyness
                    )
                    call_fair = bsm.bs_price(
                        "call", spot, strike, days, config.rate,
                        config.dividend_yield, sigma,
                    )
                    half_ticks = _half_spread_ticks(config, log_moneyness, days)
                    if wide_session:
                        half_ticks *= 2
                    call_bid, call_ask = _quote(call_fair, half_ticks, config.tick)
                    put_strike = strike
                    defect = DEFECT_NONE
                    draw = rng.random()
                    if draw < config.missing_leg_rate:
                        defect = DEFECT_MISSING_LEG
                    elif draw < config.missing_leg_rate + config.stale_quote_rate:
                        defect = DEFECT_STALE
                    elif draw < (
                        config.missing_leg_rate
                        + config.stale_quote_rate
                        + config.crossed_quote_rate
                    ):
                        defect = DEFECT_CROSSED
                    elif draw < (
                        config.missing_leg_rate
                        + config.stale_quote_rate
                        + config.crossed_quote_rate
                        + config.out_of_bounds_rate
                    ):
                        defect = DEFECT_OUT_OF_BOUNDS
                    elif draw < (
                        config.missing_leg_rate
                        + config.stale_quote_rate
                        + config.crossed_quote_rate
                        + config.out_of_bounds_rate
                        + config.contract_mismatch_rate
                    ):
                        defect = DEFECT_CONTRACT
                    jitter = config.timestamp_jitter_seconds
                    call_ts = snapshot + timedelta(
                        seconds=rng.uniform(-jitter, jitter)
                    )
                    put_ts = snapshot + timedelta(seconds=rng.uniform(-jitter, jitter))
                    spot_ts = snapshot + timedelta(seconds=rng.uniform(-jitter, jitter))
                    if defect == DEFECT_STALE:
                        lag = config.quote_sync_tolerance_seconds + rng.uniform(0.5, 6.0)
                        put_ts = call_ts + timedelta(seconds=lag)
                    if defect == DEFECT_CROSSED:
                        call_bid = call_ask + config.tick
                    if defect == DEFECT_OUT_OF_BOUNDS:
                        _, upper = bsm.price_bounds(
                            "call", spot, strike, days, config.rate,
                            config.dividend_yield,
                        )
                        call_ask = upper * 1.2 + config.tick
                        call_bid = call_ask
                    if defect == DEFECT_CONTRACT:
                        put_strike = round(strike + config.tick, 2)
                    counts[defect] = counts.get(defect, 0) + 1
                    if defect == DEFECT_MISSING_LEG:
                        continue
                    specs.append(
                        _PairSpec(
                            underlying=underlying,
                            day_label=day_label,
                            day_index=day_index,
                            strike=strike,
                            put_strike=put_strike,
                            days=days,
                            spot=spot,
                            sigma=sigma,
                            snapshot=snapshot,
                            call_fair=call_fair,
                            call_bid=call_bid,
                            call_ask=call_ask,
                            call_timestamp=call_ts,
                            put_timestamp=put_ts,
                            spot_timestamp=spot_ts,
                            defect=defect,
                            log_moneyness=log_moneyness,
                            half_ticks=half_ticks,
                            wide_session=wide_session,
                        )
                    )
    pairs = _assemble(specs, config)
    return pairs, counts


def _assemble(
    specs: Sequence[_PairSpec], config: GeneratorConfig
) -> list[QuotePair]:
    """Price the put leg in one batch and build the quoted pairs."""
    if not specs:
        return []
    put_fairs = american_put_prices(
        [spec.spot for spec in specs],
        [spec.strike for spec in specs],
        [spec.days / 365.0 for spec in specs],
        [config.rate] * len(specs),
        [config.dividend_yield] * len(specs),
        [spec.sigma for spec in specs],
        config.tree_steps,
    )
    pairs: list[QuotePair] = []
    for spec, put_fair in zip(specs, put_fairs, strict=True):
        put_fair_value = float(put_fair)
        put_bid, put_ask = _quote(put_fair_value, spec.half_ticks, config.tick)
        true_cpiv, true_call_iv, true_put_iv = _true_cpiv(
            spec.spot, spec.strike, spec.days, config.rate, config.dividend_yield,
            spec.call_fair, put_fair_value,
        )
        pairs.append(
            QuotePair(
                pair_id=f"{spec.day_label}-{spec.days}d-{spec.strike:.2f}",
                underlying=spec.underlying,
                day=spec.day_label,
                day_index=spec.day_index,
                strike=spec.strike,
                put_strike=spec.put_strike,
                days=spec.days,
                spot=spec.spot,
                rate=config.rate,
                dividend_yield=config.dividend_yield,
                snapshot_utc=spec.snapshot,
                call_bid=spec.call_bid,
                call_ask=spec.call_ask,
                put_bid=put_bid,
                put_ask=put_ask,
                call_timestamp_utc=spec.call_timestamp,
                put_timestamp_utc=spec.put_timestamp,
                spot_timestamp_utc=spec.spot_timestamp,
                call_fair=spec.call_fair,
                put_fair=put_fair_value,
                true_cpiv_pp=true_cpiv,
                true_call_iv=true_call_iv,
                true_put_iv=true_put_iv,
                defect=spec.defect,
                log_moneyness=spec.log_moneyness,
                half_spread_ticks=spec.half_ticks,
                wide_session=spec.wide_session,
                expiry=(FIRST_SESSION + timedelta(days=spec.days)).date(),
            )
        )
    return pairs
