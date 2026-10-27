"""The container for one attempted call/put pair.

It lives in its own module so that the *same* protocol code path is exercised
by two different feeders: the synthetic ground-truth generator, which knows the
answer before the quote exists, and the vendor-schema replay, which reads a
file shaped like a real feed. Nothing downstream may treat the two as
different populations.

Fields that only a simulation can know (``call_fair``, ``put_fair``,
``true_cpiv_pp``) are optional and are ``None`` for a replayed file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class QuotePair:
    """One attempted pair: two quotes, the underlying, the terms, the clock."""

    pair_id: str
    underlying: str
    day: str
    day_index: int
    strike: float
    put_strike: float
    days: int
    spot: float
    rate: float
    dividend_yield: float
    snapshot_utc: datetime
    call_bid: float
    call_ask: float
    put_bid: float
    put_ask: float
    call_timestamp_utc: datetime
    put_timestamp_utc: datetime
    spot_timestamp_utc: datetime
    defect: str = "none"
    log_moneyness: float = 0.0
    call_fair: float | None = None
    put_fair: float | None = None
    true_cpiv_pp: float | None = None
    true_call_iv: float | None = None
    true_put_iv: float | None = None
    half_spread_ticks: int = 0
    wide_session: bool = False
    expiry: date | None = None
    multiplier: int = 100
    settlement: str = "cash"
    exercise_style: str = "american"
    put_multiplier: int | None = None
    put_settlement: str | None = None
    put_exercise_style: str | None = None

    @property
    def block(self) -> str:
        """The bootstrap dependence unit: one underlying on one trading day."""
        return f"{self.underlying}|{self.day}"

    @property
    def call_mid(self) -> float:
        return (self.call_bid + self.call_ask) / 2.0

    @property
    def put_mid(self) -> float:
        return (self.put_bid + self.put_ask) / 2.0

    @property
    def log_moneyness_checked(self) -> float:
        """Log-moneyness recomputed from the pair itself, never trusted."""
        if self.spot <= 0.0 or self.strike <= 0.0:
            return math.nan
        return math.log(self.strike / self.spot)
