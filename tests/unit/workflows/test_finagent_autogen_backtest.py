import os
import sys

# Ensure Airflow-style DAG imports work in unit tests.
sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("dags"))

import math
from datetime import datetime, timedelta
from decimal import Decimal

from dags.models.market_data import MarketData, OHLCVBar
from dags.utils.finagent_autogen_backtest import grid_search_sma_crossover, run_sma_crossover_backtest


def _build_market_data(symbol: str = "TSLA") -> MarketData:
    now = datetime.utcnow()
    bars = []
    price = Decimal("250.0")
    for idx in range(220):
        ts = now - timedelta(days=220 - idx)
        change = Decimal(str(math.sin(idx / 11) * 2))
        close = price + change
        bar = OHLCVBar(
            timestamp=ts,
            open=close - Decimal("0.5"),
            high=close + Decimal("1.0"),
            low=close - Decimal("1.5"),
            close=close,
            volume=1_000_000 + idx * 1000,
        )
        bars.append(bar)
    return MarketData(symbol=symbol, exchange="NASDAQ", bars=bars, timeframe="1 day", fetched_at=now)


def test_sma_backtest_returns_metrics():
    market_data = _build_market_data()
    result = run_sma_crossover_backtest(market_data, fast_window=20, slow_window=50)

    assert "sharpe" in result.metrics
    assert "max_drawdown" in result.metrics
    assert result.params["fast_window"] == 20
    assert result.params["slow_window"] == 50
    assert isinstance(result.equity_curve, list)


def test_grid_search_returns_best_and_all_results():
    market_data = _build_market_data()
    best, all_results = grid_search_sma_crossover(market_data, fast_windows=(10, 20), slow_windows=(50, 100))

    assert all_results
    assert "sharpe" in best.metrics
    assert best.params["fast_window"] in (10, 20)
    assert best.params["slow_window"] in (50, 100)

