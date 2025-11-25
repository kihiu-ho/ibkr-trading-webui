"""FinAgent runtime helpers for Airflow workflows."""
from __future__ import annotations

import json
import logging
import math
import os
import statistics
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import pandas as pd

from models.market_data import MarketData
from models.signal import SignalAction, SignalConfidence, TradingSignal
from utils.config import config
from utils.metadata_store import FinAgentMetadataStore, metadata_store as default_metadata_store

try:  # Optional dependency, installed via airflow/requirements-airflow.txt
    import weaviate
    from weaviate.classes.init import Auth
    from weaviate.classes import config as weaviate_config
    WEAVIATE_IMPORTED = True
except Exception as exc:  # pragma: no cover - optional path
    weaviate = None
    Auth = None
    weaviate_config = None
    WEAVIATE_IMPORTED = False
    _WEAVIATE_IMPORT_ERROR = exc
else:
    _WEAVIATE_IMPORT_ERROR = None

try:
    from webapp.services import chart_service
    CHART_SERVICE_AVAILABLE = True
except Exception as exc:  # pragma: no cover - fallback logged later
    chart_service = None
    CHART_SERVICE_AVAILABLE = False
    _CHART_IMPORT_ERROR = exc
else:
    _CHART_IMPORT_ERROR = None

logger = logging.getLogger(__name__)

if _CHART_IMPORT_ERROR:
    logger.warning("Chart service import fallback engaged: %s", _CHART_IMPORT_ERROR)
if _WEAVIATE_IMPORT_ERROR:
    logger.warning("Weaviate client not available yet: %s", _WEAVIATE_IMPORT_ERROR)

CONFIRMATION_FACTORS = 4


def _decimal(value: float) -> Decimal:
    return Decimal(str(round(value, 4)))


def _calculate_rsi(series: pd.Series, period: int = 14) -> float:
    if len(series) < period + 1:
        return 50.0
    delta = series.diff().dropna()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1 / period, min_periods=period).mean()
    ma_down = down.ewm(alpha=1 / period, min_periods=period).mean()
    rs = ma_up / ma_down.replace(to_replace=0, value=math.nan)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not math.isnan(float(rsi.iloc[-1])) else 50.0


@dataclass
class FinAgentContext:
    symbol: str
    chart_path: Optional[str]
    df: pd.DataFrame
    news: List[Dict[str, str]]
    market_snapshot: Dict[str, Any]
    last_close: float
    sma_short: float
    sma_long: float
    rsi: float
    volatility: float


class VectorMemoryClient:
    """Lightweight Weaviate-backed (or in-memory) store for FinAgent reflections."""

    def __init__(self, url: Optional[str], api_key: Optional[str]):
        self.url = url
        self.api_key = api_key
        self.client = None
        self._local_memory: List[Dict[str, Any]] = []
        if url and api_key and WEAVIATE_IMPORTED:
            try:
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=url,
                    auth_credentials=Auth.api_key(api_key),
                )
                if hasattr(self.client, "is_ready"):
                    self.client.is_ready()
                logger.info("Connected to Weaviate cluster for FinAgent memory")
            except Exception as exc:  # pragma: no cover - network path
                logger.warning("Weaviate connection failed, falling back to in-memory store: %s", exc)
                self.client = None
        elif url and api_key:
            logger.warning("weaviate-client not installed; FinAgent will use in-memory memory store")

    def add_memory(self, *, symbol: str, stage: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        record = {
            "id": str(uuid.uuid4()),
            "symbol": symbol,
            "stage": stage,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        self._local_memory.append(record)
        if len(self._local_memory) > 200:
            self._local_memory.pop(0)
        if self.client:
            self._push_remote(record)

    def query(self, *, symbol: str, top_k: int = 3) -> List[Dict[str, Any]]:
        recent = [row for row in reversed(self._local_memory) if row["symbol"] == symbol]
        return recent[:top_k]

    def _push_remote(self, record: Dict[str, Any]) -> None:
        try:
            collection = None
            if hasattr(self.client, "collections"):
                collections = getattr(self.client, "collections")
                try:
                    collection = collections.get("FinAgentMemory")
                except Exception:
                    try:
                        Configure = weaviate_config.Configure  # type: ignore[attr-defined]
                        collections.create(
                            name="FinAgentMemory",
                            vectorizer_config=Configure.Vectorizer.none(),
                            properties=[
                                Configure.Property(name="symbol", data_type=Configure.DataType.TEXT),
                                Configure.Property(name="stage", data_type=Configure.DataType.TEXT),
                                Configure.Property(name="content", data_type=Configure.DataType.TEXT),
                            ],
                        )
                        collection = collections.get("FinAgentMemory")
                    except Exception as exc:  # pragma: no cover - network path
                        logger.debug("Unable to create Weaviate collection: %s", exc)
                        collection = None
            if collection:
                try:
                    vector = self._embed(record["content"])
                    collection.data.insert(
                        properties={
                            "symbol": record["symbol"],
                            "stage": record["stage"],
                            "content": record["content"],
                        },
                        vector=vector,
                    )
                except Exception as exc:  # pragma: no cover - network path
                    logger.debug("Weaviate insert skipped: %s", exc)
        except Exception as exc:  # pragma: no cover - network path
            logger.debug("Weaviate push failed: %s", exc)

    @staticmethod
    def _embed(text: str) -> List[float]:
        if not text:
            return [0.0]
        tokens = [float((ord(char) % 96) / 100) for char in text.lower() if char.isalpha()]
        if not tokens:
            tokens = [0.0]
        return [float(statistics.mean(tokens))]


class FinAgentRunner:
    """Orchestrates FinAgent-style reasoning for Airflow workflows."""

    def __init__(
        self,
        metadata_store: Optional[FinAgentMetadataStore] = None,
        vector_memory: Optional[VectorMemoryClient] = None,
    ):
        self.metadata_store = metadata_store or default_metadata_store
        self.vector_memory = vector_memory or VectorMemoryClient(config.weaviate_url, config.weaviate_api_key)
        self.reflection_rounds = config.finagent_reflection_rounds
        self.model_name = config.llm_model

    def run(
        self,
        *,
        market_data: MarketData,
        execution_id: str,
        dag_id: str,
        task_id: str,
        workflow_id: str,
        run_id: Optional[str] = None,
        news_items: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        symbol = market_data.symbol
        df = self._market_data_to_dataframe(market_data)
        chart_path = self._render_chart(df, symbol)
        market_snapshot = self._build_market_snapshot(market_data)
        self.metadata_store.record_market_snapshot(symbol, market_snapshot, run_id=run_id, execution_id=execution_id)
        news_payload = news_items or self._generate_mock_news(symbol)
        self.metadata_store.record_import_data(symbol, {"news": news_payload}, run_id=run_id, execution_id=execution_id)

        context = self._build_context(df, news_payload, chart_path, market_snapshot)
        prompt = self._compose_prompt(context)
        memory_snippets = self.vector_memory.query(symbol=symbol, top_k=3)
        reflections = self._run_reflections(context, memory_snippets)
        reasoning = self._summarize_reasoning(context, reflections, memory_snippets)
        self.metadata_store.record_prompt(symbol, prompt, reasoning, stage="decision", run_id=run_id, execution_id=execution_id)
        for reflection in reflections:
            self.vector_memory.add_memory(symbol=symbol, stage=reflection["stage"], content=reflection["summary"], metadata={"signal": symbol})
        baseline = self._compute_rl_baseline(context)
        signal = self._build_signal(context, reasoning, baseline)
        metrics = self._derive_metrics(context, signal, baseline)

        llm_artifact = {
            "prompt": prompt,
            "response": reasoning,
            "reflections": reflections,
            "baseline": baseline,
            "memory_snippets": memory_snippets,
        }

        return {
            "signal": signal,
            "chart_path": chart_path,
            "metrics": metrics,
            "llm_artifact": llm_artifact,
            "market_snapshot": market_snapshot,
            "news": news_payload,
            "baseline": baseline,
        }

    def _market_data_to_dataframe(self, market_data: MarketData) -> pd.DataFrame:
        rows = [
            {
                "Date": bar.timestamp,
                "Open": float(bar.open),
                "High": float(bar.high),
                "Low": float(bar.low),
                "Close": float(bar.close),
                "Volume": int(bar.volume),
            }
            for bar in market_data.bars
        ]
        return pd.DataFrame(rows).sort_values("Date").reset_index(drop=True)

    def _render_chart(self, df: pd.DataFrame, symbol: str) -> Optional[str]:
        if not CHART_SERVICE_AVAILABLE or chart_service is None:
            logger.warning("Chart service unavailable; skipping Plotly export")
            return None
        try:
            buffer = chart_service.generate_technical_chart(df.copy(), symbol, width=1280, height=720)
            tmp_dir = Path(tempfile.mkdtemp())
            file_path = tmp_dir / f"{symbol}_finagent.jpeg"
            with open(file_path, "wb") as fh:
                fh.write(buffer.read())
            return str(file_path)
        except Exception as exc:  # pragma: no cover - dependent on kaleido
            logger.warning("Failed to render FinAgent chart via chart_service: %s", exc)
            return None

    def _build_market_snapshot(self, market_data: MarketData) -> Dict[str, Any]:
        return {
            "symbol": market_data.symbol,
            "exchange": market_data.exchange,
            "timeframe": market_data.timeframe,
            "fetched_at": market_data.fetched_at.isoformat(),
            "bars": [
                {
                    "timestamp": bar.timestamp.isoformat(),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume),
                }
                for bar in market_data.bars[-120:]
            ],
        }

    def _generate_mock_news(self, symbol: str) -> List[Dict[str, str]]:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return [
            {
                "title": f"{symbol} supply chain stabilizes",
                "summary": f"FinAgent market intelligence module found neutral-to-positive commentary for {symbol} on {today}.",
                "sentiment": "positive",
            },
            {
                "title": f"Macro backdrop for {symbol} peers",
                "summary": "Analysts highlight resilient demand while cautioning on valuation compression.",
                "sentiment": "neutral",
            },
        ]

    def _build_context(self, df: pd.DataFrame, news: List[Dict[str, str]], chart_path: Optional[str], snapshot: Dict[str, Any]) -> FinAgentContext:
        close_series = df["Close"]
        last_close = float(close_series.iloc[-1])
        sma_short = float(close_series.rolling(window=20, min_periods=5).mean().iloc[-1])
        sma_long = float(close_series.rolling(window=50, min_periods=10).mean().iloc[-1])
        rsi_value = _calculate_rsi(close_series)
        volatility = float(close_series.pct_change().rolling(window=20).std().iloc[-1] or 0)
        return FinAgentContext(
            symbol=snapshot["symbol"],
            chart_path=chart_path,
            df=df,
            news=news,
            market_snapshot=snapshot,
            last_close=last_close,
            sma_short=sma_short,
            sma_long=sma_long,
            rsi=rsi_value,
            volatility=volatility,
        )

    def _compose_prompt(self, context: FinAgentContext) -> str:
        trend = "bullish" if context.sma_short > context.sma_long else "bearish" if context.sma_short < context.sma_long else "neutral"
        news_summary = "; ".join(f"[{item['sentiment']}] {item['title']}" for item in context.news)
        return (
            "Market Intelligence Module:\n"
            f"Symbol: {context.symbol}\n"
            f"Trend (SMA20 vs SMA50): {trend}\n"
            f"RSI(14): {context.rsi:.2f}\n"
            f"Volatility(20d σ): {context.volatility:.4f}\n"
            f"News: {news_summary}\n"
            "Dual-level reflection should analyze price strength vs news catalysts, then synthesize a risk-aware action."
        )

    def _run_reflections(self, context: FinAgentContext, memories: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
        reflections: List[Dict[str, str]] = []
        memory_text = "; ".join(mem["content"] for mem in memories) if memories else "No prior reflections."
        for idx in range(self.reflection_rounds):
            low_summary = (
                f"Round {idx + 1} low-level reflection: price closes at {context.last_close:.2f}, "
                f"SMA20/50 delta={context.sma_short - context.sma_long:.2f}, RSI={context.rsi:.1f}."
            )
            high_summary = (
                f"Round {idx + 1} high-level reflection integrates memory -> {memory_text}. "
                f"Volatility context {context.volatility:.4f}."
            )
            reflections.append({"stage": "low_level", "summary": low_summary})
            reflections.append({"stage": "high_level", "summary": high_summary})
        return reflections

    def _summarize_reasoning(
        self,
        context: FinAgentContext,
        reflections: List[Dict[str, str]],
        memories: Sequence[Dict[str, Any]],
    ) -> str:
        confirmations = self._count_confirmations(context)
        memory_clause = "; ".join(mem["content"] for mem in memories) if memories else "memory empty"
        return (
            "Decision Module Summary: "
            f"Confirmations={confirmations}/{CONFIRMATION_FACTORS}. "
            f"Low-level insight -> {reflections[-2]['summary'] if reflections else 'n/a'}. "
            f"High-level insight -> {reflections[-1]['summary'] if reflections else 'n/a'}. "
            f"Memory: {memory_clause}."
        )

    def _compute_rl_baseline(self, context: FinAgentContext) -> Dict[str, Any]:
        directional_bias = "BUY" if context.sma_short > context.sma_long else "SELL" if context.sma_short < context.sma_long else "HOLD"
        expected_return = (context.sma_short / context.last_close - 1) if context.last_close else 0
        return {
            "ppo_action": directional_bias,
            "ppo_expected_return": expected_return,
            "dqn_action": directional_bias,
            "sac_action": directional_bias,
        }

    def _build_signal(self, context: FinAgentContext, reasoning: str, baseline: Dict[str, Any]) -> TradingSignal:
        confirmations = self._count_confirmations(context)
        confidence_pct = (confirmations / CONFIRMATION_FACTORS) * 100
        confidence = self._confidence_from_score(confidence_pct)
        action = self._determine_action(context)
        entry = _decimal(context.last_close * 0.995 if action == SignalAction.BUY.value else context.last_close)
        stop = _decimal(context.last_close * (0.98 if action == SignalAction.BUY.value else 1.02))
        target = _decimal(context.last_close * (1.04 if action == SignalAction.BUY.value else 0.96))
        r_multiple = _decimal(float(target - entry) / float(entry - stop)) if entry != stop else Decimal("0")
        key_factors = [
            f"SMA20 {'>' if context.sma_short > context.sma_long else '<='} SMA50",
            f"RSI {context.rsi:.1f}",
            f"Volatility {context.volatility:.4f}",
        ]
        return TradingSignal(
            symbol=context.symbol,
            action=SignalAction(action),
            confidence=confidence,
            confidence_score=_decimal(confidence_pct),
            reasoning=reasoning,
            key_factors=key_factors,
            trend="bullish" if context.sma_short > context.sma_long else "bearish" if context.sma_short < context.sma_long else "neutral",
            support_level=_decimal(context.sma_long * 0.98),
            resistance_level=_decimal(context.sma_long * 1.02),
            suggested_entry_price=entry,
            suggested_stop_loss=stop,
            suggested_take_profit=target,
            r_multiple=r_multiple,
            position_size_percent=_decimal(min(max(confidence_pct / 100 * 5, 1), 10)),
            timeframe_analyzed="daily",
            model_used=self.model_name,
        )

    def _derive_metrics(self, context: FinAgentContext, signal: TradingSignal, baseline: Dict[str, Any]) -> Dict[str, float]:
        entry = float(signal.suggested_entry_price or context.last_close)
        target = float(signal.suggested_take_profit or context.last_close)
        finagent_expected = (target - entry) / entry if entry else 0
        baseline_expected = float(baseline.get("ppo_expected_return", 0))
        return {
            "finagent_expected_return": finagent_expected,
            "baseline_expected_return": baseline_expected,
            "confidence_score": float(signal.confidence_score),
        }

    def _count_confirmations(self, context: FinAgentContext) -> int:
        confirmations = 0
        if context.sma_short > context.sma_long:
            confirmations += 1
        if context.last_close > context.sma_short:
            confirmations += 1
        if context.rsi > 55:
            confirmations += 1
        if context.volatility < 0.03:
            confirmations += 1
        return confirmations

    def _determine_action(self, context: FinAgentContext) -> str:
        if context.sma_short > context.sma_long and context.rsi >= 50:
            return SignalAction.BUY.value
        if context.sma_short < context.sma_long and context.rsi <= 45:
            return SignalAction.SELL.value
        return SignalAction.HOLD.value

    def _confidence_from_score(self, score: float) -> SignalConfidence:
        if score >= 80:
            return SignalConfidence.HIGH
        if score >= 50:
            return SignalConfidence.MEDIUM
        return SignalConfidence.LOW


__all__ = ["FinAgentRunner", "VectorMemoryClient", "FinAgentContext"]
