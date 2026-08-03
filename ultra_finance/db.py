from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .models import BacktestResult, Candle, MarketQuote, WalkForwardResult


class Database:
    def __init__(self, path: str | Path = "ultra_finans.db") -> None:
        self.path = str(path)
        self._initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connect() as con:
            con.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS market_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    change_24h_pct REAL,
                    volume_24h REAL,
                    timestamp TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS market_candles (
                    source TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    open_time TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    PRIMARY KEY(source, symbol, interval, open_time)
                );
                CREATE TABLE IF NOT EXISTS accounts (
                    name TEXT PRIMARY KEY,
                    cash_try REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS positions (
                    account_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    average_price REAL NOT NULL,
                    PRIMARY KEY(account_name, symbol)
                );
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    fee_try REAL NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS backtest_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    strategy_name TEXT NOT NULL DEFAULT 'Dengeli',
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
                );
                CREATE TABLE IF NOT EXISTS walk_forward_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    champion TEXT NOT NULL,
                    challenger TEXT,
                    fold_count INTEGER NOT NULL,
                    selected_return_pct REAL NOT NULL,
                    benchmark_return_pct REAL NOT NULL,
                    leaderboard_json TEXT NOT NULL,
                    folds_json TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            self._ensure_column(con, "backtest_runs", "strategy_name", "TEXT NOT NULL DEFAULT 'Dengeli'")
            con.execute("INSERT OR IGNORE INTO accounts(name, cash_try) VALUES (?, ?)", ("Kripto Sanal", 1250.0))
            con.execute("INSERT OR IGNORE INTO accounts(name, cash_try) VALUES (?, ?)", ("Borsa Sanal", 10000.0))

    @staticmethod
    def _ensure_column(con: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def save_quote(self, quote: MarketQuote) -> None:
        with self.connect() as con:
            con.execute(
                "INSERT INTO market_quotes(source,symbol,price,change_24h_pct,volume_24h,timestamp) VALUES (?,?,?,?,?,?)",
                (quote.source, quote.symbol, quote.price, quote.change_24h_pct, quote.volume_24h, quote.timestamp.isoformat()),
            )

    def save_candles(self, candles: list[Candle]) -> None:
        if not candles:
            return
        rows = [
            (c.source, c.symbol, c.interval, c.open_time.isoformat(), c.open, c.high, c.low, c.close, c.volume)
            for c in candles
        ]
        with self.connect() as con:
            con.executemany(
                """
                INSERT INTO market_candles(source,symbol,interval,open_time,open,high,low,close,volume)
                VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(source,symbol,interval,open_time) DO UPDATE SET
                    open=excluded.open, high=excluded.high, low=excluded.low,
                    close=excluded.close, volume=excluded.volume
                """,
                rows,
            )

    def recent_prices(self, symbol: str, limit: int = 30) -> list[float]:
        with self.connect() as con:
            rows = con.execute(
                "SELECT price FROM market_quotes WHERE symbol=? ORDER BY timestamp DESC LIMIT ?",
                (symbol, limit),
            ).fetchall()
        return [float(row["price"]) for row in reversed(rows)]

    def account(self, name: str) -> dict[str, float | str]:
        with self.connect() as con:
            row = con.execute("SELECT name,cash_try FROM accounts WHERE name=?", (name,)).fetchone()
        if row is None:
            raise KeyError(f"Hesap bulunamadı: {name}")
        return {"name": row["name"], "cash_try": float(row["cash_try"])}

    def positions(self, account_name: str) -> list[dict[str, float | str]]:
        with self.connect() as con:
            rows = con.execute(
                "SELECT symbol,quantity,average_price FROM positions WHERE account_name=? ORDER BY symbol",
                (account_name,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_decision(self, symbol: str, signal: str, confidence: float, reason: str) -> None:
        with self.connect() as con:
            con.execute(
                "INSERT INTO decisions(symbol,signal,confidence,reason,created_at) VALUES (?,?,?,?,?)",
                (symbol, signal, confidence, reason, datetime.now(timezone.utc).isoformat()),
            )

    def save_backtest(self, result: BacktestResult) -> None:
        with self.connect() as con:
            con.execute(
                """
                INSERT INTO backtest_runs(
                    symbol,strategy_name,starting_cash,ending_equity,net_return_pct,benchmark_return_pct,
                    max_drawdown_pct,trades,wins,losses,win_rate_pct,profit_factor,total_fees,notes,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    result.symbol, result.strategy_name, result.starting_cash, result.ending_equity, result.net_return_pct,
                    result.benchmark_return_pct, result.max_drawdown_pct, result.trades, result.wins,
                    result.losses, result.win_rate_pct, result.profit_factor, result.total_fees,
                    result.notes, datetime.now(timezone.utc).isoformat(),
                ),
            )

    def save_walk_forward(self, result: WalkForwardResult) -> None:
        with self.connect() as con:
            con.execute(
                """
                INSERT INTO walk_forward_runs(
                    symbol,champion,challenger,fold_count,selected_return_pct,benchmark_return_pct,
                    leaderboard_json,folds_json,notes,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    result.symbol, result.champion, result.challenger, len(result.folds),
                    result.selected_strategy_return_pct, result.selected_strategy_benchmark_pct,
                    json.dumps([asdict(item) for item in result.leaderboard], ensure_ascii=False),
                    json.dumps([asdict(item) for item in result.folds], ensure_ascii=False),
                    result.notes, datetime.now(timezone.utc).isoformat(),
                ),
            )

    def execute_paper_order(
        self,
        account_name: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        fee_rate: float,
        reason: str,
    ) -> None:
        if quantity <= 0 or price <= 0:
            raise ValueError("Miktar ve fiyat pozitif olmalı.")
        gross, fee = quantity * price, quantity * price * fee_rate
        with self.connect() as con:
            account = con.execute("SELECT cash_try FROM accounts WHERE name=?", (account_name,)).fetchone()
            if account is None:
                raise KeyError(f"Hesap bulunamadı: {account_name}")
            position = con.execute(
                "SELECT quantity,average_price FROM positions WHERE account_name=? AND symbol=?",
                (account_name, symbol),
            ).fetchone()
            current_qty = float(position["quantity"]) if position else 0.0
            current_avg = float(position["average_price"]) if position else 0.0
            cash = float(account["cash_try"])
            if side == "BUY":
                if cash < gross + fee:
                    raise ValueError("Sanal hesap bakiyesi yetersiz.")
                new_qty = current_qty + quantity
                new_avg = ((current_qty * current_avg) + gross) / new_qty
                con.execute("UPDATE accounts SET cash_try=? WHERE name=?", (cash - gross - fee, account_name))
                con.execute(
                    """
                    INSERT INTO positions(account_name,symbol,quantity,average_price) VALUES (?,?,?,?)
                    ON CONFLICT(account_name,symbol) DO UPDATE SET
                        quantity=excluded.quantity, average_price=excluded.average_price
                    """,
                    (account_name, symbol, new_qty, new_avg),
                )
            elif side == "SELL":
                if current_qty < quantity:
                    raise ValueError("Satılacak kadar sanal pozisyon yok.")
                new_qty = current_qty - quantity
                con.execute("UPDATE accounts SET cash_try=? WHERE name=?", (cash + gross - fee, account_name))
                if new_qty <= 1e-12:
                    con.execute("DELETE FROM positions WHERE account_name=? AND symbol=?", (account_name, symbol))
                else:
                    con.execute(
                        "UPDATE positions SET quantity=? WHERE account_name=? AND symbol=?",
                        (new_qty, account_name, symbol),
                    )
            else:
                raise ValueError("İşlem yönü BUY veya SELL olmalı.")
            con.execute(
                """
                INSERT INTO orders(account_name,symbol,side,quantity,price,fee_try,reason,created_at)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    account_name, symbol, side, quantity, price, fee, reason,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
