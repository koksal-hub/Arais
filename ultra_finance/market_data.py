from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Candle, MarketQuote


class MarketDataError(RuntimeError):
    pass


class BinancePublicDataClient:
    """API anahtarı istemeyen yalnızca-okuma piyasa veri istemcisi."""

    BASE_URL = "https://data-api.binance.vision/api/v3/klines"

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    def fetch_candles(self, symbol: str, interval: str = "1h", limit: int = 200) -> list[Candle]:
        query = urlencode({"symbol": symbol.upper(), "interval": interval, "limit": max(50, min(limit, 1000))})
        req = Request(f"{self.BASE_URL}?{query}", headers={"User-Agent": "UltraFinansAjani/0.2"})
        try:
            with urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise MarketDataError(str(exc)) from exc
        if not isinstance(payload, list) or not payload:
            raise MarketDataError("Borsa boş mum verisi döndürdü.")
        candles: list[Candle] = []
        for row in payload:
            candles.append(
                Candle(
                    source="Binance",
                    symbol=symbol.upper(),
                    interval=interval,
                    open_time=datetime.fromtimestamp(int(row[0]) / 1000, tz=timezone.utc),
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                )
            )
        return candles

    @staticmethod
    def quote_from_candles(candles: list[Candle]) -> MarketQuote:
        if len(candles) < 2:
            raise MarketDataError("Fiyat üretmek için yeterli mum yok.")
        last = candles[-1]
        lookback = candles[-25] if len(candles) >= 25 else candles[0]
        change = ((last.close / lookback.close) - 1.0) * 100 if lookback.close else 0.0
        volume = sum(c.close * c.volume for c in candles[-24:])
        return MarketQuote(last.source, last.symbol, last.close, change, volume)

    def load_market(self, symbol: str, interval: str = "1h", limit: int = 200) -> tuple[MarketQuote, list[Candle], bool]:
        try:
            candles = self.fetch_candles(symbol, interval, limit)
            return self.quote_from_candles(candles), candles, True
        except MarketDataError:
            candles = self.demo_candles(symbol, interval, limit)
            return self.quote_from_candles(candles), candles, False

    @staticmethod
    def demo_candles(symbol: str, interval: str = "1h", limit: int = 200) -> list[Candle]:
        bases = {
            "BTCUSDT": 65000.0,
            "ETHUSDT": 3400.0,
            "DOGEUSDT": 0.12,
            "SHIBUSDT": 0.000015,
            "BONKUSDT": 0.000022,
            "SKYUSDT": 0.06,
        }
        base = bases.get(symbol.upper(), 100.0)
        seed = int(hashlib.sha256(f"{symbol}-{interval}".encode()).hexdigest()[:16], 16)
        rng = random.Random(seed)
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        step = timedelta(hours=1)
        if interval.endswith("m"):
            step = timedelta(minutes=max(1, int(interval[:-1])))
        elif interval.endswith("h"):
            step = timedelta(hours=max(1, int(interval[:-1])))
        elif interval.endswith("d"):
            step = timedelta(days=max(1, int(interval[:-1])))
        price = base * 0.92
        candles: list[Candle] = []
        for i in range(limit):
            drift = 0.00045 + 0.0012 * math.sin(i / 17)
            shock = rng.gauss(0, 0.006)
            open_price = price
            close = max(base * 0.05, open_price * (1 + drift + shock))
            span = abs(rng.gauss(0.004, 0.002))
            high = max(open_price, close) * (1 + span)
            low = min(open_price, close) * max(0.01, 1 - span)
            volume = max(1.0, rng.lognormvariate(8.0, 0.45))
            candles.append(
                Candle(
                    source="Demo",
                    symbol=symbol.upper(),
                    interval=interval,
                    open_time=now - step * (limit - 1 - i),
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                )
            )
            price = close
        return candles
