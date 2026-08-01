from __future__ import annotations

import math

from .agents import AgentCouncil
from .models import BacktestResult, Candle, Signal


class BacktestEngine:
    """Sinyali kapanışta üretir, işlemi bir sonraki mum açılışında uygular."""

    def __init__(self, council: AgentCouncil | None = None) -> None:
        self.council = council or AgentCouncil()

    def run(
        self,
        candles: list[Candle],
        starting_cash: float = 1250.0,
        fee_rate: float = 0.001,
        slippage_bps: float = 5.0,
        max_position_pct: float = 0.20,
        reserve_cash_pct: float = 0.25,
        warmup: int = 60,
    ) -> BacktestResult:
        if len(candles) <= warmup + 2:
            raise ValueError("Backtest için daha fazla mum gerekli.")
        cash = starting_cash
        quantity = 0.0
        entry_total = 0.0
        total_fees = 0.0
        trade_pnls: list[float] = []
        equity_curve: list[float] = [starting_cash]
        slip = slippage_bps / 10_000.0

        for i in range(warmup, len(candles) - 1):
            history = candles[: i + 1]
            decision, _, _ = self.council.evaluate(candles[i].symbol, history)
            next_open = candles[i + 1].open
            if decision.signal == Signal.BUY and quantity <= 1e-15:
                spendable = max(0.0, cash * (1.0 - reserve_cash_pct))
                budget = min(cash * max_position_pct, spendable)
                execution_price = next_open * (1.0 + slip)
                fee = budget * fee_rate
                if budget > fee and cash >= budget + fee:
                    quantity = budget / execution_price
                    cash -= budget + fee
                    entry_total = budget + fee
                    total_fees += fee
            elif decision.signal == Signal.SELL and quantity > 0:
                execution_price = next_open * (1.0 - slip)
                gross = quantity * execution_price
                fee = gross * fee_rate
                proceeds = gross - fee
                cash += proceeds
                total_fees += fee
                trade_pnls.append(proceeds - entry_total)
                quantity = 0.0
                entry_total = 0.0
            equity_curve.append(cash + quantity * candles[i + 1].close)

        if quantity > 0:
            execution_price = candles[-1].close * (1.0 - slip)
            gross = quantity * execution_price
            fee = gross * fee_rate
            proceeds = gross - fee
            cash += proceeds
            total_fees += fee
            trade_pnls.append(proceeds - entry_total)
            quantity = 0.0

        ending_equity = cash
        peak = equity_curve[0]
        max_drawdown = 0.0
        for equity in equity_curve:
            peak = max(peak, equity)
            if peak > 0:
                max_drawdown = max(max_drawdown, (peak - equity) / peak)
        wins = sum(1 for pnl in trade_pnls if pnl > 0)
        losses = sum(1 for pnl in trade_pnls if pnl <= 0)
        gross_profit = sum(p for p in trade_pnls if p > 0)
        gross_loss = abs(sum(p for p in trade_pnls if p < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (math.inf if gross_profit > 0 else None)
        benchmark_start = candles[warmup + 1].open
        benchmark_end = candles[-1].close
        benchmark_return = ((benchmark_end / benchmark_start) - 1.0) * 100 if benchmark_start else 0.0
        trades = len(trade_pnls)
        return BacktestResult(
            symbol=candles[-1].symbol,
            starting_cash=starting_cash,
            ending_equity=ending_equity,
            net_return_pct=((ending_equity / starting_cash) - 1.0) * 100,
            benchmark_return_pct=benchmark_return,
            max_drawdown_pct=max_drawdown * 100,
            trades=trades,
            wins=wins,
            losses=losses,
            win_rate_pct=(wins / trades * 100) if trades else 0.0,
            profit_factor=profit_factor,
            total_fees=total_fees,
            notes="Gelecek veri kullanılmadı; sinyal kapanışta, işlem sonraki mum açılışında ve maliyetli uygulandı.",
        )
