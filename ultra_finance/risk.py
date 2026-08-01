from __future__ import annotations

from dataclasses import dataclass

from .models import Decision, Signal


@dataclass(frozen=True)
class RiskLimits:
    max_position_pct: float = 0.20
    min_confidence: float = 0.65
    fee_rate: float = 0.001
    reserve_cash_pct: float = 0.25
    max_daily_loss_pct: float = 0.03
    max_consecutive_losses: int = 3


@dataclass(frozen=True)
class RiskResult:
    approved: bool
    max_order_try: float
    reason: str


class RiskManager:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def review(
        self,
        decision: Decision,
        cash_try: float,
        daily_loss_pct: float = 0.0,
        consecutive_losses: int = 0,
        emergency_stop: bool = False,
    ) -> RiskResult:
        if emergency_stop:
            return RiskResult(False, 0.0, "Acil durdurma aktif.")
        if daily_loss_pct >= self.limits.max_daily_loss_pct:
            return RiskResult(False, 0.0, "Günlük zarar limiti aşıldı.")
        if consecutive_losses >= self.limits.max_consecutive_losses:
            return RiskResult(False, 0.0, "Arka arkaya zarar limiti aşıldı.")
        if decision.signal in (Signal.WAIT, Signal.BLOCK):
            return RiskResult(False, 0.0, "Karar işlem açmaya uygun değil.")
        if decision.confidence < self.limits.min_confidence:
            return RiskResult(False, 0.0, "Karar güven puanı risk eşiğinin altında.")
        spendable = max(0.0, cash_try * (1.0 - self.limits.reserve_cash_pct))
        max_order = min(spendable, cash_try * self.limits.max_position_pct)
        if max_order <= 0:
            return RiskResult(False, 0.0, "Kullanılabilir sanal bakiye yok.")
        return RiskResult(True, max_order, "Risk kuralları işlemi sınırlı tutarla onayladı.")
