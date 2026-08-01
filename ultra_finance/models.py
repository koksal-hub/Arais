from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class Signal(str, Enum):
    BUY = "AL"
    SELL = "SAT"
    WAIT = "BEKLE"
    BLOCK = "ENGELLE"


@dataclass(frozen=True)
class MarketQuote:
    source: str
    symbol: str
    price: float
    change_24h_pct: float | None = None
    volume_24h: float | None = None
    timestamp: datetime = datetime.now(timezone.utc)


@dataclass(frozen=True)
class AgentOpinion:
    agent: str
    signal: Signal
    score: float
    reason: str


@dataclass(frozen=True)
class Decision:
    symbol: str
    signal: Signal
    confidence: float
    reason: str
    max_position_try: float = 0.0
