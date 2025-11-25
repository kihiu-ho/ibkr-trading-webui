import math
from datetime import datetime, timedelta
from decimal import Decimal

from dags.models.market_data import MarketData, OHLCVBar
from dags.utils.finagent_runner import FinAgentRunner, VectorMemoryClient


class DummyMetadataStore:
    def __init__(self):
        self.records = []

    def record_market_snapshot(self, *_, **__):
        self.records.append(("market_data", __))

    def record_import_data(self, *_, **__):
        self.records.append(("import_data", __))

    def record_prompt(self, *_, **__):
        self.records.append(("llm_prompt", __))


class DummyVectorMemory(VectorMemoryClient):
    def __init__(self):
        super().__init__(url=None, api_key=None)


def _build_market_data(symbol: str = "TSLA") -> MarketData:
    now = datetime.utcnow()
    bars = []
    price = Decimal("250.0")
    for idx in range(60):
        ts = now - timedelta(days=60 - idx)
        change = Decimal(str(math.sin(idx / 6) * 2))
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


def test_finagent_runner_generates_signal(tmp_path):
    runner = FinAgentRunner(metadata_store=DummyMetadataStore(), vector_memory=DummyVectorMemory())
    market_data = _build_market_data()

    result = runner.run(
        market_data=market_data,
        execution_id="test_exec",
        dag_id="test_dag",
        task_id="run_finagent",
        workflow_id="finagent_trading_signal_workflow",
    )

    signal = result["signal"]
    assert signal.symbol == market_data.symbol
    assert signal.reasoning.startswith("Decision Module Summary")
    assert signal.confidence_score >= 0
    assert signal.model_used == runner.model_name
    assert "reflections" in result["llm_artifact"]
    assert "baseline" in result
    assert "finagent_expected_return" in result["metrics"]
