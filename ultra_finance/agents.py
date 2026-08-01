from __future__ import annotations

from .models import (
    AgentOpinion,
    Candle,
    Decision,
    MarketRegime,
    MultiTimeframeSnapshot,
    Signal,
    TechnicalSnapshot,
)
from .strategies import BALANCED, StrategyConfig
from .technical import TechnicalAnalyzer


class AgentCouncil:
    """Dar görevli ajanların puanlarını birleştirir; emir göndermez."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or BALANCED
        self.analyzer = TechnicalAnalyzer(self.config)

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

    def _volume(self, snapshot: TechnicalSnapshot) -> AgentOpinion:
        ratio = snapshot.volume_ratio
        if ratio is None:
            return AgentOpinion("Hacim Ajanı", Signal.WAIT, 0.45, "Hacim ortalaması oluşmadı.")
        threshold = self.config.volume_confirmation
        if ratio >= threshold and snapshot.signal == Signal.BUY:
            return AgentOpinion("Hacim Ajanı", Signal.BUY, min(0.85, 0.60 + ratio / 10), f"Hacim oranı {ratio:.2f}; yükselişi teyit ediyor.")
        if ratio >= threshold and snapshot.signal == Signal.SELL:
            return AgentOpinion("Hacim Ajanı", Signal.SELL, min(0.85, 0.60 + ratio / 10), f"Hacim oranı {ratio:.2f}; satışı teyit ediyor.")
        return AgentOpinion("Hacim Ajanı", Signal.WAIT, 0.55, f"Hacim oranı {ratio:.2f}; güçlü teyit yok.")

    def _risk_sentinel(self, snapshot: TechnicalSnapshot) -> AgentOpinion:
        if snapshot.atr_pct is None:
            return AgentOpinion("Risk Gözcüsü", Signal.WAIT, 0.50, "ATR oluşmadı.")
        if snapshot.atr_pct >= self.config.max_atr_pct:
            return AgentOpinion("Risk Gözcüsü", Signal.BLOCK, 0.95, f"ATR/fiyat %{snapshot.atr_pct * 100:.2f}; eşik aşıldı.")
        if snapshot.rsi is not None and snapshot.rsi >= 82:
            return AgentOpinion("Risk Gözcüsü", Signal.WAIT, 0.75, "Aşırı alım nedeniyle yeni pozisyon önerilmiyor.")
        return AgentOpinion("Risk Gözcüsü", Signal.WAIT, 0.70, f"ATR/fiyat %{snapshot.atr_pct * 100:.2f}; olağan sınırda.")


class MultiTimeframeCouncil:
    """Birincil sinyali daha yüksek zaman dilimiyle doğrular."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or BALANCED
        self.primary_council = AgentCouncil(self.config)
        self.confirmation_council = AgentCouncil(self.config)

    def evaluate(
        self,
        symbol: str,
        primary_candles: list[Candle],
        confirmation_candles: list[Candle],
    ) -> tuple[MultiTimeframeSnapshot, tuple[AgentOpinion, ...], tuple[AgentOpinion, ...]]:
        primary_decision, primary_snapshot, primary_opinions = self.primary_council.evaluate(symbol, primary_candles)
        confirmation_decision, confirmation_snapshot, confirmation_opinions = self.confirmation_council.evaluate(symbol, confirmation_candles)
        reasons: list[str] = []

        if Signal.BLOCK in (primary_decision.signal, confirmation_decision.signal):
            decision = Decision(symbol, Signal.BLOCK, 0.95, "Zaman dilimlerinden en az biri risk engeli verdi.")
            alignment = "RİSK ENGELİ"
            reasons.append(decision.reason)
        elif primary_decision.signal == Signal.BUY and confirmation_snapshot.regime == MarketRegime.BEAR:
            decision = Decision(symbol, Signal.WAIT, 0.76, "1s alış sinyali, 4s düşüş rejimiyle çelişti.")
            alignment = "ÇELİŞKİ"
            reasons.append("Kısa vadeli yükseliş, yüksek zaman diliminde desteklenmedi.")
        elif primary_decision.signal == Signal.SELL and confirmation_snapshot.regime == MarketRegime.BULL:
            decision = Decision(symbol, Signal.WAIT, 0.76, "1s satış sinyali, 4s yükseliş rejimiyle çelişti.")
            alignment = "ÇELİŞKİ"
            reasons.append("Kısa vadeli düşüş, yüksek zaman diliminde desteklenmedi.")
        elif primary_decision.signal == confirmation_decision.signal and primary_decision.signal in (Signal.BUY, Signal.SELL):
            confidence = min(0.96, max(primary_decision.confidence, confirmation_decision.confidence) + 0.08)
            decision = Decision(symbol, primary_decision.signal, confidence, "1s ve 4s ajan kurulları aynı yönde uzlaştı.")
            alignment = "TAM UYUM"
            reasons.append("İki zaman dilimi aynı yönü destekliyor.")
        elif primary_decision.signal in (Signal.BUY, Signal.SELL) and confirmation_decision.signal == Signal.WAIT:
            confidence = max(0.45, primary_decision.confidence - 0.10)
            decision = Decision(symbol, Signal.WAIT, confidence, "Birincil sinyal yüksek zaman diliminden teyit alamadı.")
            alignment = "TEYİTSİZ"
            reasons.append("4s kurulu yön belirtmediği için işlem ertelendi.")
        else:
            decision = Decision(symbol, Signal.WAIT, max(0.50, primary_decision.confidence), "Zaman dilimleri işlem için yeterli ortak kanıt üretmedi.")
            alignment = "NÖTR"
            reasons.append("Sinyal kalitesi işlem eşiğinin altında.")

        result = MultiTimeframeSnapshot(
            symbol=symbol,
            primary_interval=primary_snapshot.interval,
            confirmation_interval=confirmation_snapshot.interval,
            primary=primary_snapshot,
            confirmation=confirmation_snapshot,
            decision=decision,
            alignment=alignment,
            reasons=tuple(reasons),
        )
        return result, primary_opinions, confirmation_opinions
