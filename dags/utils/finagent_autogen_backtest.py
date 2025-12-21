"""Lightweight backtest helpers for the FinAgent AutoGen pipeline.

This is intentionally simple and deterministic: it provides an "offline" evaluation
path for the Airflow DAG that does not require calling an LLM repeatedly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from models.market_data import MarketData


def _market_data_to_dataframe(market_data: MarketData) -> pd.DataFrame:
    rows = [
        {
            "timestamp": bar.timestamp,
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume),
        }
        for bar in market_data.bars
    ]
    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def _max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    running_max = equity.cummax()
    drawdown = (equity / running_max) - 1.0
    return float(drawdown.min())


@dataclass
class BacktestResult:
    metrics: Dict[str, float]
    params: Dict[str, Any]
    equity_curve: List[Dict[str, Any]]


def run_sma_crossover_backtest(
    market_data: MarketData,
    *,
    fast_window: int = 20,
    slow_window: int = 50,
    annualization_days: int = 252,
) -> BacktestResult:
    """Simple long/flat SMA crossover backtest using close-to-close returns."""
    df = _market_data_to_dataframe(market_data)
    if df.empty or len(df) < max(fast_window, slow_window) + 5:
        return BacktestResult(
            metrics={
                "cumulative_return": 0.0,
                "annualized_return": 0.0,
                "annualized_volatility": 0.0,
                "sharpe": 0.0,
                "max_drawdown": 0.0,
                "num_trades": 0.0,
            },
            params={"fast_window": fast_window, "slow_window": slow_window},
            equity_curve=[],
        )

    close = df["close"]
    returns = close.pct_change().fillna(0.0)
    sma_fast = close.rolling(window=fast_window).mean()
    sma_slow = close.rolling(window=slow_window).mean()

    # Position is 1 when fast > slow, else 0 (long/flat).
    position = (sma_fast > sma_slow).astype(int).fillna(0)
    strategy_returns = returns * position.shift(1).fillna(0)

    equity = (1.0 + strategy_returns).cumprod()
    cumulative_return = float(equity.iloc[-1] - 1.0)

    ann_return = float((1.0 + cumulative_return) ** (annualization_days / max(len(df), 1)) - 1.0)
    ann_vol = float(strategy_returns.std() * math.sqrt(annualization_days))
    sharpe = float((ann_return / ann_vol) if ann_vol > 1e-12 else 0.0)
    mdd = _max_drawdown(equity)

    # Approx trade count: number of position changes 0->1 (entries)
    entries = ((position.diff() > 0).fillna(0)).sum()

    curve = [
        {"timestamp": row["timestamp"].isoformat(), "equity": float(eq)}
        for (_, row), eq in zip(df.iterrows(), equity)
    ]

    return BacktestResult(
        metrics={
            "cumulative_return": cumulative_return,
            "annualized_return": ann_return,
            "annualized_volatility": ann_vol,
            "sharpe": sharpe,
            "max_drawdown": mdd,
            "num_trades": float(entries),
        },
        params={"fast_window": fast_window, "slow_window": slow_window},
        equity_curve=curve,
    )


def grid_search_sma_crossover(
    market_data: MarketData,
    *,
    fast_windows: Sequence[int] = (10, 20),
    slow_windows: Sequence[int] = (50, 100),
) -> Tuple[BacktestResult, List[Dict[str, Any]]]:
    """Grid-search a small SMA crossover space; returns best result + all results."""
    all_results: List[Dict[str, Any]] = []
    best: Optional[BacktestResult] = None

    for fast in fast_windows:
        for slow in slow_windows:
            if fast >= slow:
                continue
            result = run_sma_crossover_backtest(market_data, fast_window=fast, slow_window=slow)
            record = {
                "fast_window": fast,
                "slow_window": slow,
                **result.metrics,
            }
            all_results.append(record)
            if best is None or result.metrics.get("sharpe", 0.0) > best.metrics.get("sharpe", 0.0):
                best = result

    if best is None:
        best = run_sma_crossover_backtest(market_data)
    return best, all_results

