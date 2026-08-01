from __future__ import annotations

from .models import AgentOpinion, Candle, Decision, MarketRegime, Signal, TechnicalSnapshot
from .technical import TechnicalAnalyzer


class AgentCouncil:
    """Dar görevli ajanların puanlarını birleştirir; emir göndermez."""

    def __init__(self, analyzer: TechnicalAnalyzer | None = None) -> None:
        self.analyzer = analyzer or TechnicalAnalyzer()

    def evaluate(self, symbol: str, candles: list[Candle]) -> tuple[Decision, TechnicalSnapshot, tuple[AgentOpinion, ...]]:
        snapshot = self.analyzer.analyze(candles)
        opinions = (
            self._technical(snapshot),
            self._regime(snapshot),
            self._volume(snapshot),
            self._risk_sentinel(snapshot),
        )
        blocker = next((o for o in opinions if o.signal == Signal.BLOCK), None)
        if blocker:
            decision = Decision(symbol, Signal.BLOCK, max(0.90, blocker.score), f"Risk Gözcüsü: {blocker.reason}")
            return decision, snapshot, opinions

        weights = {"Teknik Ajan": 0.50, "Rejim Ajanı": 0.25, "Hacim Ajanı": 0.15, "Risk Gözcüsü": 0.10}
        vote = 0.0
        for opinion in opinions:
            direction = 1.0 if opinion.signal == Signal.BUY else -1.0 if opinion.signal == Signal.SELL else 0.0
            vote += direction * opinion.score * weights[opinion.agent]
        if vote >= 0.28:
            signal = Signal.BUY
        elif vote <= -0.28:
            signal = Signal.SELL
        else:
            signal = Signal.WAIT
        confidence = min(0.95, max(0.45, 0.50 + abs(vote) * 0.45))
        reason = " | ".join(f"{o.agent}: {o.reason}" for o in opinions)
        return Decision(symbol, signal, confidence, reason), snapshot, opinions

    @staticmethod
    def _technical(snapshot: TechnicalSnapshot) -> AgentOpinion:
        return AgentOpinion("Teknik Ajan", snapshot.signal, snapshot.confidence, f"Puan {snapshot.score:.0f}/100; {snapshot.reasons[0]}")

    @staticmethod
    def _regime(snapshot: TechnicalSnapshot) -> AgentOpinion:
        mapping = {
            MarketRegime.BULL: (Signal.BUY, 0.78, "Yükseliş rejimi."),
            MarketRegime.BEAR: (Signal.SELL, 0.78, "Düşüş rejimi."),
            MarketRegime.SIDEWAYS: (Signal.WAIT, 0.62, "Yatay rejim; trend işlemi zayıf."),
            MarketRegime.HIGH_VOLATILITY: (Signal.BLOCK, 0.95, "Yüksek oynaklık."),
            MarketRegime.UNKNOWN: (Signal.WAIT, 0.50, "Rejim için veri yetersiz."),
        }
        signal, score, reason = mapping[snapshot.regime]
        return AgentOpinion("Rejim Ajanı", signal, score, reason)

    @staticmethod
    def _volume(snapshot: TechnicalSnapshot) -> AgentOpinion:
        ratio = snapshot.volume_ratio
        if ratio is None:
            return AgentOpinion("Hacim Ajanı", Signal.WAIT, 0.45, "Hacim ortalaması oluşmadı.")
        if ratio >= 1.25 and snapshot.signal == Signal.BUY:
            return AgentOpinion("Hacim Ajanı", Signal.BUY, min(0.85, 0.60 + ratio / 10), f"Hacim oranı {ratio:.2f}; yükselişi teyit ediyor.")
        if ratio >= 1.25 and snapshot.signal == Signal.SELL:
            return AgentOpinion("Hacim Ajanı", Signal.SELL, min(0.85, 0.60 + ratio / 10), f"Hacim oranı {ratio:.2f}; satışı teyit ediyor.")
        return AgentOpinion("Hacim Ajanı", Signal.WAIT, 0.55, f"Hacim oranı {ratio:.2f}; güçlü teyit yok.")

    @staticmethod
    def _risk_sentinel(snapshot: TechnicalSnapshot) -> AgentOpinion:
        if snapshot.atr_pct is None:
            return AgentOpinion("Risk Gözcüsü", Signal.WAIT, 0.50, "ATR oluşmadı.")
        if snapshot.atr_pct >= 0.055:
            return AgentOpinion("Risk Gözcüsü", Signal.BLOCK, 0.95, f"ATR/fiyat %{snapshot.atr_pct * 100:.2f}; eşik aşıldı.")
        if snapshot.rsi is not None and snapshot.rsi >= 82:
            return AgentOpinion("Risk Gözcüsü", Signal.WAIT, 0.75, "Aşırı alım nedeniyle yeni pozisyon önerilmiyor.")
        return AgentOpinion("Risk Gözcüsü", Signal.WAIT, 0.70, f"ATR/fiyat %{snapshot.atr_pct * 100:.2f}; olağan sınırda.")
