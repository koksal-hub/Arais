from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Signal(str, Enum):
    BUY = "AL"
    SELL = "SAT"
    WAIT = "BEKLE"
    BLOCK = "ENGELLE"


class MarketRegime(str, Enum):
    BULL = "YÜKSELİŞ"
    BEAR = "DÜŞÜŞ"
    SIDEWAYS = "YATAY"
    HIGH_VOLATILITY = "YÜKSEK OYNAKLIK"
    UNKNOWN = "BELİRSİZ"


@dataclass(frozen=True)
class MarketQuote:
    source: str
    symbol: str
    price: float
    change_24h_pct: float | None = None
    volume_24h: float | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Candle:
    source: str
    symbol: str
    interval: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


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


@dataclass(frozen=True)
class TechnicalSnapshot:
    symbol: str
    regime: MarketRegime
    signal: Signal
    score: float
    confidence: float
    close: float
    sma_fast: float | None
    sma_slow: float | None
    ema_fast: float | None
    ema_slow: float | None
    rsi: float | None
    macd: float | None
    macd_signal: float | None
    atr: float | None
    atr_pct: float | None
    bollinger_upper: float | None
    bollinger_lower: float | None
    volume_ratio: float | None
    support: float | None
    resistance: float | None
    patterns: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class BacktestResult:
    symbol: str
    starting_cash: float
    ending_equity: float
    net_return_pct: float
    benchmark_return_pct: float
    max_drawdown_pct: float
    trades: int
    wins: int
    losses: int
    win_rate_pct: float
    profit_factor: float | None
    total_fees: float
    notes: str
