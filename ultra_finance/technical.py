from __future__ import annotations

from statistics import mean, pstdev

from .models import Candle, MarketRegime, Signal, TechnicalSnapshot


def sma(values: list[float], period: int) -> float | None:
    if period <= 0 or len(values) < period:
        return None
    return mean(values[-period:])


def ema_series(values: list[float], period: int) -> list[float]:
    if not values or period <= 0:
        return []
    alpha = 2.0 / (period + 1.0)
    result = [values[0]]
    for value in values[1:]:
        result.append(alpha * value + (1.0 - alpha) * result[-1])
    return result


def rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    seed = changes[:period]
    avg_gain = sum(max(c, 0.0) for c in seed) / period
    avg_loss = sum(max(-c, 0.0) for c in seed) / period
    for change in changes[period:]:
        avg_gain = ((avg_gain * (period - 1)) + max(change, 0.0)) / period
        avg_loss = ((avg_loss * (period - 1)) + max(-change, 0.0)) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def atr(candles: list[Candle], period: int = 14) -> float | None:
    if len(candles) <= period:
        return None
    true_ranges: list[float] = []
    for i in range(1, len(candles)):
        current, previous = candles[i], candles[i - 1]
        true_ranges.append(max(current.high - current.low, abs(current.high - previous.close), abs(current.low - previous.close)))
    value = mean(true_ranges[:period])
    for tr in true_ranges[period:]:
        value = ((value * (period - 1)) + tr) / period
    return value


def bollinger(values: list[float], period: int = 20, deviations: float = 2.0) -> tuple[float | None, float | None]:
    if len(values) < period:
        return None, None
    window = values[-period:]
    middle = mean(window)
    deviation = pstdev(window)
    return middle + deviations * deviation, middle - deviations * deviation


def candle_patterns(candles: list[Candle]) -> tuple[str, ...]:
    if not candles:
        return ()
    current = candles[-1]
    body = abs(current.close - current.open)
    total = max(current.high - current.low, 1e-12)
    upper = current.high - max(current.open, current.close)
    lower = min(current.open, current.close) - current.low
    patterns: list[str] = []
    if body / total <= 0.10:
        patterns.append("Doji")
    if lower >= max(body * 2.0, total * 0.45) and upper <= total * 0.20 and current.close >= current.open:
        patterns.append("Çekiç")
    if upper >= max(body * 2.0, total * 0.45) and lower <= total * 0.20 and current.close <= current.open:
        patterns.append("Kayan Yıldız")
    if body / total >= 0.80:
        patterns.append("Boğa Marubozu" if current.close > current.open else "Ayı Marubozu")
    if len(candles) >= 2:
        previous = candles[-2]
        prev_low, prev_high = sorted((previous.open, previous.close))
        cur_low, cur_high = sorted((current.open, current.close))
        if previous.close < previous.open and current.close > current.open and cur_low <= prev_low and cur_high >= prev_high:
            patterns.append("Boğa Yutan")
        if previous.close > previous.open and current.close < current.open and cur_low <= prev_low and cur_high >= prev_high:
            patterns.append("Ayı Yutan")
    return tuple(patterns)


class TechnicalAnalyzer:
    MIN_CANDLES = 55

    def analyze(self, candles: list[Candle]) -> TechnicalSnapshot:
        if not candles:
            raise ValueError("Teknik analiz için mum verisi gerekli.")
        symbol = candles[-1].symbol
        closes = [c.close for c in candles]
        volumes = [c.volume for c in candles]
        close = closes[-1]
        fast_sma = sma(closes, 20)
        slow_sma = sma(closes, 50)
        ema12_series = ema_series(closes, 12)
        ema26_series = ema_series(closes, 26)
        fast_ema = ema12_series[-1] if ema12_series else None
        slow_ema = ema26_series[-1] if ema26_series else None
        macd_series = [a - b for a, b in zip(ema12_series, ema26_series)]
        macd_value = macd_series[-1] if macd_series else None
        macd_signal_series = ema_series(macd_series, 9)
        macd_signal_value = macd_signal_series[-1] if macd_signal_series else None
        rsi_value = rsi(closes, 14)
        atr_value = atr(candles, 14)
        atr_pct = (atr_value / close) if atr_value is not None and close else None
        upper, lower = bollinger(closes, 20)
        volume_avg = mean(volumes[-20:]) if len(volumes) >= 20 else None
        volume_ratio = (volumes[-1] / volume_avg) if volume_avg else None
        support = min(c.low for c in candles[-20:]) if len(candles) >= 20 else None
        resistance = max(c.high for c in candles[-20:]) if len(candles) >= 20 else None
        patterns = candle_patterns(candles)

        if len(candles) < self.MIN_CANDLES:
            return TechnicalSnapshot(
                symbol, MarketRegime.UNKNOWN, Signal.WAIT, 50.0, 0.35, close,
                fast_sma, slow_sma, fast_ema, slow_ema, rsi_value, macd_value,
                macd_signal_value, atr_value, atr_pct, upper, lower, volume_ratio,
                support, resistance, patterns, (f"En az {self.MIN_CANDLES} mum gerekli.",),
            )

        regime = MarketRegime.SIDEWAYS
        if atr_pct is not None and atr_pct >= 0.055:
            regime = MarketRegime.HIGH_VOLATILITY
        elif fast_sma and slow_sma and fast_ema and slow_ema:
            if fast_sma > slow_sma * 1.004 and fast_ema > slow_ema and close > fast_sma:
                regime = MarketRegime.BULL
            elif fast_sma < slow_sma * 0.996 and fast_ema < slow_ema and close < fast_sma:
                regime = MarketRegime.BEAR

        score = 50.0
        reasons: list[str] = []
        if fast_sma is not None and slow_sma is not None:
            if fast_sma > slow_sma:
                score += 12
                reasons.append("SMA20, SMA50 üzerinde.")
            else:
                score -= 12
                reasons.append("SMA20, SMA50 altında.")
        if fast_ema is not None and slow_ema is not None:
            if fast_ema > slow_ema:
                score += 8
                reasons.append("EMA12, EMA26 üzerinde.")
            else:
                score -= 8
                reasons.append("EMA12, EMA26 altında.")
        if macd_value is not None and macd_signal_value is not None:
            if macd_value > macd_signal_value:
                score += 8
                reasons.append("MACD sinyal çizgisinin üzerinde.")
            else:
                score -= 8
                reasons.append("MACD sinyal çizgisinin altında.")
        if rsi_value is not None:
            if rsi_value < 30:
                score += 8
                reasons.append("RSI aşırı satım bölgesinde.")
            elif rsi_value > 70:
                score -= 7
                reasons.append("RSI aşırı alım bölgesinde; yeni alım riski yüksek.")
            elif 50 <= rsi_value <= 65:
                score += 4
                reasons.append("RSI pozitif fakat aşırı değil.")
            elif 35 <= rsi_value < 50:
                score -= 4
                reasons.append("RSI zayıf bölgede.")
        if volume_ratio is not None and volume_ratio >= 1.20:
            direction = candles[-1].close - candles[-1].open
            score += 6 if direction > 0 else -6
            reasons.append("Hacim ortalamanın üzerinde ve son mum yönünü teyit ediyor.")
        if "Boğa Yutan" in patterns or "Çekiç" in patterns or "Boğa Marubozu" in patterns:
            score += 6
            reasons.append("Pozitif mum formasyonu algılandı.")
        if "Ayı Yutan" in patterns or "Kayan Yıldız" in patterns or "Ayı Marubozu" in patterns:
            score -= 6
            reasons.append("Negatif mum formasyonu algılandı.")
        if upper is not None and close > upper:
            score -= 4
            reasons.append("Fiyat üst Bollinger bandının üzerinde; geri çekilme riski var.")
        elif lower is not None and close < lower:
            score += 4
            reasons.append("Fiyat alt Bollinger bandının altında; tepki ihtimali var.")

        score = max(0.0, min(100.0, score))
        if regime == MarketRegime.HIGH_VOLATILITY:
            signal = Signal.BLOCK
            confidence = 0.90
            reasons.insert(0, "ATR tabanlı oynaklık güvenlik eşiğini aştı.")
        elif score >= 68:
            signal = Signal.BUY
            confidence = min(0.92, 0.55 + (score - 50) / 100)
        elif score <= 32:
            signal = Signal.SELL
            confidence = min(0.92, 0.55 + (50 - score) / 100)
        else:
            signal = Signal.WAIT
            confidence = max(0.45, 0.68 - abs(score - 50) / 100)
        if not reasons:
            reasons.append("Göstergeler belirgin yön üretmedi.")
        return TechnicalSnapshot(
            symbol, regime, signal, score, confidence, close, fast_sma, slow_sma,
            fast_ema, slow_ema, rsi_value, macd_value, macd_signal_value,
            atr_value, atr_pct, upper, lower, volume_ratio, support, resistance,
            patterns, tuple(reasons),
        )
