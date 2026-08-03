from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean, median

from .backtest import BacktestEngine
from .models import (
    BacktestResult,
    Candle,
    StrategyLeaderboardEntry,
    WalkForwardFold,
    WalkForwardResult,
)
from .strategies import DEFAULT_STRATEGIES, StrategyConfig


def _compound(returns_pct: list[float]) -> float:
    value = 1.0
    for result in returns_pct:
        value *= 1.0 + result / 100.0
    return (value - 1.0) * 100.0


def _training_score(result: BacktestResult) -> float:
    """Kârı ödüllendirirken düşüşü ve işlemsiz sonucu cezalandırır."""
    if result.trades == 0:
        return -10.0 - result.max_drawdown_pct
    benchmark_edge = result.net_return_pct - result.benchmark_return_pct
    trade_credit = min(result.trades, 8) * 0.10
    return result.net_return_pct - 1.50 * result.max_drawdown_pct + 0.25 * benchmark_edge + trade_credit


class WalkForwardEngine:
    """Yuvarlanan eğitim/test pencereleriyle strateji seçimini denetler.

    Her katmanda strateji yalnızca eğitim penceresinde seçilir. Ardından seçilen
    strateji, daha sonra gelen ve seçim sırasında görülmeyen test penceresinde
    uygulanır. Ayrıca tüm adaylar aynı test pencerelerinde kıyaslanarak araştırma
    amaçlı şampiyon/adayı tablosu üretilir.
    """

    def __init__(self, strategies: tuple[StrategyConfig, ...] | None = None) -> None:
        self.strategies = strategies or DEFAULT_STRATEGIES
        if len(self.strategies) < 2:
            raise ValueError("Walk-forward için en az iki strateji gerekli.")

    def run(
        self,
        candles: list[Candle],
        train_size: int = 120,
        test_size: int = 30,
        step_size: int | None = None,
        starting_cash: float = 1250.0,
    ) -> WalkForwardResult:
        step_size = step_size or test_size
        max_warmup = max(BacktestEngine(s).council.analyzer.min_candles for s in self.strategies)
        minimum = train_size + test_size
        if train_size <= max_warmup + 2:
            raise ValueError(f"Eğitim penceresi en az {max_warmup + 3} mum olmalı.")
        if test_size < 8:
            raise ValueError("Test penceresi en az 8 mum olmalı.")
        if len(candles) < minimum:
            raise ValueError(f"Walk-forward için en az {minimum} mum gerekli.")

        folds: list[WalkForwardFold] = []
        selected_returns: list[float] = []
        selected_benchmarks: list[float] = []
        strategy_oos: dict[str, list[BacktestResult]] = defaultdict(list)

        fold_no = 1
        train_start = 0
        while train_start + train_size + test_size <= len(candles):
            train_end = train_start + train_size
            test_end = train_end + test_size
            train_slice = candles[train_start:train_end]

            train_scores: dict[str, float] = {}
            for strategy in self.strategies:
                result = BacktestEngine(strategy).run(train_slice, starting_cash=starting_cash)
                train_scores[strategy.name] = _training_score(result)
            selected = max(self.strategies, key=lambda s: train_scores[s.name])

            context_start = max(0, train_end - max_warmup)
            test_with_context = candles[context_start:test_end]
            test_warmup = train_end - context_start

            fold_oos: dict[str, BacktestResult] = {}
            for strategy in self.strategies:
                result = BacktestEngine(strategy).run(
                    test_with_context,
                    starting_cash=starting_cash,
                    warmup=test_warmup,
                )
                strategy_oos[strategy.name].append(result)
                fold_oos[strategy.name] = result

            selected_test = fold_oos[selected.name]
            selected_returns.append(selected_test.net_return_pct)
            selected_benchmarks.append(selected_test.benchmark_return_pct)
            folds.append(
                WalkForwardFold(
                    fold=fold_no,
                    train_start=train_slice[0].open_time.isoformat(),
                    train_end=train_slice[-1].open_time.isoformat(),
                    test_start=candles[train_end].open_time.isoformat(),
                    test_end=candles[test_end - 1].open_time.isoformat(),
                    selected_strategy=selected.name,
                    train_score=train_scores[selected.name],
                    test_return_pct=selected_test.net_return_pct,
                    test_benchmark_pct=selected_test.benchmark_return_pct,
                    test_drawdown_pct=selected_test.max_drawdown_pct,
                    trades=selected_test.trades,
                )
            )
            fold_no += 1
            train_start += step_size

        if not folds:
            raise ValueError("Belirlenen pencerelerle walk-forward katmanı oluşmadı.")

        leaderboard: list[StrategyLeaderboardEntry] = []
        for strategy in self.strategies:
            results = strategy_oos[strategy.name]
            returns = [r.net_return_pct for r in results]
            drawdowns = [r.max_drawdown_pct for r in results]
            positive_folds = sum(1 for value in returns if value > 0)
            avg_return = mean(returns)
            median_return = median(returns)
            avg_drawdown = mean(drawdowns)
            positive_ratio = positive_folds / len(results)
            total_trades = sum(r.trades for r in results)
            activity_penalty = 2.0 if total_trades == 0 else 0.0
            robustness = median_return - 1.25 * avg_drawdown + 2.0 * positive_ratio - activity_penalty
            if not math.isfinite(robustness):
                robustness = -999.0
            leaderboard.append(
                StrategyLeaderboardEntry(
                    strategy_name=strategy.name,
                    folds=len(results),
                    average_test_return_pct=avg_return,
                    median_test_return_pct=median_return,
                    average_drawdown_pct=avg_drawdown,
                    total_trades=total_trades,
                    positive_folds=positive_folds,
                    robustness_score=robustness,
                )
            )
        leaderboard.sort(key=lambda item: item.robustness_score, reverse=True)
        champion = leaderboard[0].strategy_name
        challenger = leaderboard[1].strategy_name if len(leaderboard) > 1 else None
        return WalkForwardResult(
            symbol=candles[-1].symbol,
            champion=champion,
            challenger=challenger,
            folds=tuple(folds),
            leaderboard=tuple(leaderboard),
            selected_strategy_return_pct=_compound(selected_returns),
            selected_strategy_benchmark_pct=_compound(selected_benchmarks),
            notes=(
                "Her katmanda seçim yalnızca geçmiş eğitim penceresinde yapıldı. "
                "Şampiyon etiketi araştırma amaçlıdır; bir sonraki görülmemiş canlı/sanal dönemi geçmeden gerçek işlem yetkisi vermez."
            ),
        )
