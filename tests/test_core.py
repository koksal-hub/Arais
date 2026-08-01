from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ultra_finance.agents import AgentCouncil, MultiTimeframeCouncil
from ultra_finance.backtest import BacktestEngine
from ultra_finance.db import Database
from ultra_finance.models import Candle, Decision, Signal
from ultra_finance.risk import RiskManager
from ultra_finance.strategies import CONSERVATIVE, MOMENTUM, StrategyConfig
from ultra_finance.technical import TechnicalAnalyzer
from ultra_finance.walkforward import WalkForwardEngine


def synthetic_candles(
    count: int = 260,
    trend: float = 0.0015,
    interval: str = "1h",
    symbol: str = "TESTUSDT",
) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    candles: list[Candle] = []
    step = timedelta(hours=4 if interval == "4h" else 1)
    for i in range(count):
        open_price = price
        wave = ((i % 7) - 3) * 0.0005
        close = open_price * (1 + trend + wave)
        high = max(open_price, close) * 1.003
        low = min(open_price, close) * 0.997
        volume = 1000 + (i % 11) * 25
        candles.append(Candle("Test", symbol, interval, start + step * i, open_price, high, low, close, volume))
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

    def test_strategy_config_validation(self) -> None:
        with self.assertRaises(ValueError):
            StrategyConfig(name="hatalı", sma_fast=50, sma_slow=20)

    def test_multi_timeframe_conflict_forces_wait(self) -> None:
        primary = synthetic_candles(trend=0.002, interval="1h")
        confirmation = synthetic_candles(trend=-0.002, interval="4h")
        result, _, _ = MultiTimeframeCouncil().evaluate("TESTUSDT", primary, confirmation)
        self.assertEqual(result.decision.signal, Signal.WAIT)
        self.assertEqual(result.alignment, "ÇELİŞKİ")


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

    def test_old_database_schema_is_migrated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "old.db"
            con = sqlite3.connect(path)
            con.execute(
                """
                CREATE TABLE backtest_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    starting_cash REAL NOT NULL,
                    ending_equity REAL NOT NULL,
                    net_return_pct REAL NOT NULL,
                    benchmark_return_pct REAL NOT NULL,
                    max_drawdown_pct REAL NOT NULL,
                    trades INTEGER NOT NULL,
                    wins INTEGER NOT NULL,
                    losses INTEGER NOT NULL,
                    win_rate_pct REAL NOT NULL,
                    profit_factor REAL,
                    total_fees REAL NOT NULL,
                    notes TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            con.commit()
            con.close()
            Database(path)
            con = sqlite3.connect(path)
            columns = {row[1] for row in con.execute("PRAGMA table_info(backtest_runs)")}
            con.close()
            self.assertIn("strategy_name", columns)


class BacktestTests(unittest.TestCase):
    def test_backtest_returns_finite_metrics(self) -> None:
        result = BacktestEngine().run(synthetic_candles())
        self.assertGreater(result.ending_equity, 0)
        self.assertGreaterEqual(result.max_drawdown_pct, 0)
        self.assertGreaterEqual(result.total_fees, 0)
        self.assertIn("sonraki mum", result.notes)

    def test_different_strategies_are_reported(self) -> None:
        candles = synthetic_candles()
        conservative = BacktestEngine(CONSERVATIVE).run(candles)
        momentum = BacktestEngine(MOMENTUM).run(candles)
        self.assertEqual(conservative.strategy_name, "Muhafazakâr")
        self.assertEqual(momentum.strategy_name, "Momentum")


class WalkForwardTests(unittest.TestCase):
    def test_walk_forward_creates_folds_and_leaderboard(self) -> None:
        candles = synthetic_candles(count=270)
        result = WalkForwardEngine().run(candles, train_size=120, test_size=30, step_size=30)
        self.assertGreaterEqual(len(result.folds), 4)
        self.assertEqual(len(result.leaderboard), 4)
        self.assertTrue(result.champion)
        self.assertIsNotNone(result.challenger)
        self.assertIn("görülmemiş", result.notes)


if __name__ == "__main__":
    unittest.main()
