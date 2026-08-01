from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ultra_finance.agents import AgentCouncil
from ultra_finance.backtest import BacktestEngine
from ultra_finance.db import Database
from ultra_finance.models import Candle, Decision, Signal
from ultra_finance.risk import RiskManager
from ultra_finance.technical import TechnicalAnalyzer


def synthetic_candles(count: int = 220, trend: float = 0.0015) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    candles: list[Candle] = []
    for i in range(count):
        open_price = price
        wave = ((i % 7) - 3) * 0.0005
        close = open_price * (1 + trend + wave)
        high = max(open_price, close) * 1.003
        low = min(open_price, close) * 0.997
        volume = 1000 + (i % 11) * 25
        candles.append(Candle("Test", "TESTUSDT", "1h", start + timedelta(hours=i), open_price, high, low, close, volume))
        price = close
    return candles


class TechnicalTests(unittest.TestCase):
    def test_indicator_snapshot_is_complete(self) -> None:
        snapshot = TechnicalAnalyzer().analyze(synthetic_candles())
        self.assertIsNotNone(snapshot.rsi)
        self.assertIsNotNone(snapshot.macd)
        self.assertIsNotNone(snapshot.atr)
        self.assertGreaterEqual(snapshot.score, 0)
        self.assertLessEqual(snapshot.score, 100)

    def test_future_data_does_not_change_past_decision(self) -> None:
        candles = synthetic_candles()
        council = AgentCouncil()
        before = council.evaluate("TESTUSDT", candles[:100])[0]
        altered = candles[:100] + [
            Candle(c.source, c.symbol, c.interval, c.open_time, c.open * 20, c.high * 20, c.low * 20, c.close * 20, c.volume)
            for c in candles[100:]
        ]
        after = council.evaluate("TESTUSDT", altered[:100])[0]
        self.assertEqual(before, after)


class RiskAndDatabaseTests(unittest.TestCase):
    def test_risk_caps_order_and_emergency_stop(self) -> None:
        risk = RiskManager()
        decision = Decision("BTCUSDT", Signal.BUY, 0.80, "test")
        approved = risk.review(decision, 1250.0)
        self.assertTrue(approved.approved)
        self.assertAlmostEqual(approved.max_order_try, 250.0)
        blocked = risk.review(decision, 1250.0, emergency_stop=True)
        self.assertFalse(blocked.approved)

    def test_paper_buy_sell(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            db = Database(Path(temp) / "test.db")
            db.execute_paper_order("Kripto Sanal", "BTCUSDT", "BUY", 1.0, 100.0, 0.001, "test")
            self.assertEqual(len(db.positions("Kripto Sanal")), 1)
            db.execute_paper_order("Kripto Sanal", "BTCUSDT", "SELL", 1.0, 110.0, 0.001, "test")
            self.assertEqual(db.positions("Kripto Sanal"), [])
            self.assertGreater(float(db.account("Kripto Sanal")["cash_try"]), 1259.0)


class BacktestTests(unittest.TestCase):
    def test_backtest_returns_finite_metrics(self) -> None:
        result = BacktestEngine().run(synthetic_candles())
        self.assertGreater(result.ending_equity, 0)
        self.assertGreaterEqual(result.max_drawdown_pct, 0)
        self.assertGreaterEqual(result.total_fees, 0)
        self.assertIn("sonraki mum", result.notes)


if __name__ == "__main__":
    unittest.main()
