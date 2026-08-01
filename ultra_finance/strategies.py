from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyConfig:
    """Teknik stratejinin denetlenebilir parametreleri.

    Bu nesne emir göndermez. Aynı veri üzerinde farklı adayların adil biçimde
    karşılaştırılmasını sağlar.
    """

    name: str
    sma_fast: int = 20
    sma_slow: int = 50
    ema_fast: int = 12
    ema_slow: int = 26
    rsi_period: int = 14
    atr_period: int = 14
    bollinger_period: int = 20
    buy_score: float = 68.0
    sell_score: float = 32.0
    max_atr_pct: float = 0.055
    volume_confirmation: float = 1.20
    max_position_pct: float = 0.20
    reserve_cash_pct: float = 0.25
    fee_rate: float = 0.001
    slippage_bps: float = 5.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Strateji adı boş olamaz.")
        if self.sma_fast <= 1 or self.sma_slow <= self.sma_fast:
            raise ValueError("SMA periyotları geçersiz.")
        if self.ema_fast <= 1 or self.ema_slow <= self.ema_fast:
            raise ValueError("EMA periyotları geçersiz.")
        if not 0 < self.sell_score < self.buy_score < 100:
            raise ValueError("Al/sat puan eşikleri geçersiz.")
        if not 0 < self.max_atr_pct < 1:
            raise ValueError("ATR risk eşiği geçersiz.")
        if not 0 < self.max_position_pct <= 1:
            raise ValueError("Pozisyon sınırı geçersiz.")
        if not 0 <= self.reserve_cash_pct < 1:
            raise ValueError("Nakit rezervi geçersiz.")
        if self.fee_rate < 0 or self.slippage_bps < 0:
            raise ValueError("İşlem maliyetleri negatif olamaz.")


BALANCED = StrategyConfig(name="Dengeli")

CONSERVATIVE = StrategyConfig(
    name="Muhafazakâr",
    sma_fast=24,
    sma_slow=55,
    ema_fast=15,
    ema_slow=30,
    buy_score=73.0,
    sell_score=27.0,
    max_atr_pct=0.040,
    volume_confirmation=1.30,
    max_position_pct=0.15,
    reserve_cash_pct=0.35,
    slippage_bps=7.0,
)

MOMENTUM = StrategyConfig(
    name="Momentum",
    sma_fast=12,
    sma_slow=36,
    ema_fast=8,
    ema_slow=21,
    rsi_period=10,
    atr_period=12,
    buy_score=64.0,
    sell_score=36.0,
    max_atr_pct=0.065,
    volume_confirmation=1.12,
    max_position_pct=0.20,
    reserve_cash_pct=0.25,
    slippage_bps=6.0,
)

MEAN_REVERSION = StrategyConfig(
    name="Tepki",
    sma_fast=16,
    sma_slow=48,
    ema_fast=10,
    ema_slow=28,
    rsi_period=9,
    buy_score=62.0,
    sell_score=38.0,
    max_atr_pct=0.045,
    volume_confirmation=1.05,
    max_position_pct=0.12,
    reserve_cash_pct=0.40,
    slippage_bps=8.0,
)

DEFAULT_STRATEGIES: tuple[StrategyConfig, ...] = (
    BALANCED,
    CONSERVATIVE,
    MOMENTUM,
    MEAN_REVERSION,
)
