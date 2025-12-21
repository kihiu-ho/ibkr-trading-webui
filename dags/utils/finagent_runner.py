"""FinAgent runtime helpers for Airflow workflows."""
from __future__ import annotations

import base64
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
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from models.market_data import MarketData
from models.signal import SignalAction, SignalConfidence, TradingSignal
from utils.config import config
from utils.metadata_store import FinAgentMetadataStore, metadata_store as default_metadata_store
from utils import finagent_prompts as finagent_prompts_v1
from utils import finagent_prompts_v3 as finagent_prompts_v3
from utils.finagent_xml import get_required, get_required_map, parse_finagent_xml, safe_get_str

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

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except Exception:  # pragma: no cover - optional path
    OpenAI = None  # type: ignore[assignment]
    _OPENAI_AVAILABLE = False


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
        return self.query_filtered(symbol=symbol, top_k=top_k, stage_prefix=None, query_text=None)

    def query_filtered(
        self,
        *,
        symbol: str,
        top_k: int = 3,
        stage_prefix: Optional[str] = None,
        query_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return recent memories for symbol, optionally filtered by stage prefix."""
        filtered = [row for row in reversed(self._local_memory) if row["symbol"] == symbol]
        if stage_prefix:
            filtered = [row for row in filtered if str(row.get("stage", "")).startswith(stage_prefix)]
        if query_text:
            query_lower = query_text.lower()
            filtered.sort(
                key=lambda row: (
                    0 if query_lower in str(row.get("content", "")).lower() else 1,
                    -len(str(row.get("content", ""))),
                )
            )
        return filtered[:top_k]

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
        prompts_version: Optional[str] = None,
        llm_client: Optional["FinAgentLLMClient"] = None,
    ):
        self.metadata_store = metadata_store or default_metadata_store
        self.vector_memory = vector_memory or VectorMemoryClient(config.weaviate_url, config.weaviate_api_key)
        self.reflection_rounds = config.finagent_reflection_rounds
        self.model_name = config.llm_model
        self.prompts_version = (prompts_version or config.finagent_prompts_version or "v1").strip().lower()
        self.prompts = finagent_prompts_v3 if self.prompts_version.startswith("v3") else finagent_prompts_v1
        self.llm = llm_client or FinAgentLLMClient(
            provider=config.llm_provider,
            api_key=config.llm_api_key,
            base_url=config.llm_api_base_url,
            model=config.llm_model,
            vision_model=config.llm_vision_model,
        )

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
        baseline = self._compute_rl_baseline(context)

        prompt_values = self._build_asset_prompt_values(context, market_data)
        stage_artifacts: Dict[str, Any] = {}

        latest_mi = self._run_market_intelligence_latest(
            context,
            prompt_values,
            execution_id=execution_id,
            run_id=run_id,
        )
        stage_artifacts["market_intelligence_latest"] = latest_mi["artifact"]

        past_mi = self._run_market_intelligence_past(
            context,
            prompt_values,
            latest_queries=latest_mi["parsed"].get("query", {}),
            execution_id=execution_id,
            run_id=run_id,
        )
        stage_artifacts["market_intelligence_past"] = past_mi["artifact"]

        low_level = self._run_low_level_reflection(
            context,
            prompt_values,
            past_summary=past_mi["parsed"].get("summary", ""),
            latest_summary=latest_mi["parsed"].get("summary", ""),
            execution_id=execution_id,
            run_id=run_id,
        )
        stage_artifacts["low_level_reflection"] = low_level["artifact"]

        high_level = self._run_high_level_reflection(
            context,
            prompt_values,
            past_market_summary=past_mi["parsed"].get("summary", ""),
            latest_market_summary=latest_mi["parsed"].get("summary", ""),
            past_low_level=self._get_past_stage_summary(symbol, stage_prefix="low_level_reflection_summary"),
            latest_low_level=low_level["summary_text"],
            execution_id=execution_id,
            run_id=run_id,
        )
        stage_artifacts["high_level_reflection"] = high_level["artifact"]

        decision = self._run_decision_making(
            context,
            prompt_values,
            past_market_summary=past_mi["parsed"].get("summary", ""),
            latest_market_summary=latest_mi["parsed"].get("summary", ""),
            past_low_level=self._get_past_stage_summary(symbol, stage_prefix="low_level_reflection_summary"),
            latest_low_level=low_level["summary_text"],
            past_high_level=self._get_past_stage_summary(symbol, stage_prefix="high_level_reflection_summary"),
            latest_high_level=high_level["summary_text"],
            baseline=baseline,
            execution_id=execution_id,
            run_id=run_id,
        )
        stage_artifacts["decision"] = decision["artifact"]

        signal = self._build_signal(context, decision["reasoning_text"], baseline, action_override=decision["action"])
        metrics = self._derive_metrics(context, signal, baseline)

        llm_artifact = {
            "prompt": decision["prompt"],
            "response": decision["reasoning_text"],
            "raw_response": decision["raw_response"],
            "reflections": {
                "low_level": low_level.get("parsed", {}),
                "high_level": high_level.get("parsed", {}),
            },
            "baseline": baseline,
            "stages": stage_artifacts,
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

    def _build_asset_prompt_values(self, context: FinAgentContext, market_data: MarketData) -> Dict[str, str]:
        return {
            "asset_type": "company",
            "asset_name": context.symbol,
            "asset_symbol": context.symbol,
            "asset_exchange": market_data.exchange or "UNKNOWN",
            "asset_sector": "N/A",
            "asset_industry": "N/A",
            "asset_description": "N/A",
        }

    def _format_market_intelligence_items(self, items: List[Dict[str, str]]) -> str:
        lines: List[str] = []
        for idx, item in enumerate(items, start=1):
            item_id = f"{idx:06d}"
            title = (item.get("title") or "").strip()
            summary = (item.get("summary") or "").strip()
            publisher = (item.get("publisher") or item.get("source") or "").strip()
            published_at = (item.get("published_at") or "").strip()
            url = (item.get("url") or "").strip()
            sentiment = (item.get("sentiment") or "neutral").strip().lower()

            lines.append(f"ID: {item_id}")
            if published_at:
                lines.append(f"Date: {published_at}")
            if publisher:
                lines.append(f"Source: {publisher}")
            if title:
                lines.append(f"Headline: {title}")
            if summary:
                lines.append(f"Content: {summary}")
            if not self.prompts_version.startswith("v3"):
                lines.append(f"Market Sentiment: {sentiment}")
            if url:
                lines.append(f"URL: {url}")
            lines.append("")
        return "\n".join(lines).strip()

    def _run_market_intelligence_latest(
        self,
        context: FinAgentContext,
        values: Dict[str, str],
        *,
        execution_id: str,
        run_id: Optional[str],
    ) -> Dict[str, Any]:
        latest_block = self._format_market_intelligence_items(context.news)
        prompt_lib = self.prompts
        render = prompt_lib.render
        base_values = {**values, "latest_market_intelligence": latest_block}
        if self.prompts_version.startswith("v3") and hasattr(prompt_lib, "LATEST_MARKET_INTELLIGENCE_CONTEXT"):
            context_block = render(prompt_lib.LATEST_MARKET_INTELLIGENCE_CONTEXT, base_values)
        else:
            context_block = (
                f"Latest market intelligence and price context:\nSymbol={context.symbol}\nLatest Close={context.last_close:.2f}\n\n{latest_block}"
            )
        user_prompt = "\n\n".join(
            [
                render(prompt_lib.TASK_DESCRIPTION_MARKET_INTELLIGENCE, values),
                context_block,
                prompt_lib.MARKET_INTELLIGENCE_EFFECTS,
                render(prompt_lib.LATEST_MARKET_INTELLIGENCE_PROMPT, values),
                prompt_lib.LATEST_MARKET_INTELLIGENCE_OUTPUT_FORMAT,
            ]
        )
        raw = self.llm.complete_xml(stage="market_intelligence_latest", system=prompt_lib.SYSTEM_CONTENT_TRADING, user=user_prompt)
        parsed = parse_finagent_xml(raw)
        artifact = {"prompt": user_prompt, "response": raw, "parsed": parsed}
        self.metadata_store.record_prompt(context.symbol, user_prompt, raw, stage="market_intelligence_latest", run_id=run_id, execution_id=execution_id)
        summary = safe_get_str(parsed, "summary") or ""
        query_map = parsed.get("query") if isinstance(parsed.get("query"), dict) else {}
        self.vector_memory.add_memory(symbol=context.symbol, stage="market_intelligence_latest_raw", content=latest_block, metadata={})
        if summary:
            self.vector_memory.add_memory(symbol=context.symbol, stage="market_intelligence_latest_summary", content=summary, metadata={"query": query_map})
        return {"prompt": user_prompt, "raw": raw, "parsed": parsed, "artifact": artifact}

    def _run_market_intelligence_past(
        self,
        context: FinAgentContext,
        values: Dict[str, str],
        *,
        latest_queries: Any,
        execution_id: str,
        run_id: Optional[str],
    ) -> Dict[str, Any]:
        query_text = ""
        if isinstance(latest_queries, dict):
            query_text = " ".join(str(val) for val in latest_queries.values() if val)
        past_raw = self.vector_memory.query_filtered(
            symbol=context.symbol,
            top_k=10,
            stage_prefix="market_intelligence_latest_raw",
            query_text=query_text or None,
        )
        past_items_text = "\n\n".join(str(item.get("content", "")).strip() for item in past_raw if item.get("content"))
        if not past_items_text.strip():
            parsed = {"analysis": "", "summary": "No past market intelligence available.", "query": {}}
            artifact = {"prompt": "", "response": "", "parsed": parsed}
            return {"prompt": "", "raw": "", "parsed": parsed, "artifact": artifact}

        prompt_lib = self.prompts
        render = prompt_lib.render
        base_values = {**values, "past_market_intelligence": past_items_text}
        if self.prompts_version.startswith("v3") and hasattr(prompt_lib, "PAST_MARKET_INTELLIGENCE_CONTEXT"):
            context_block = render(prompt_lib.PAST_MARKET_INTELLIGENCE_CONTEXT, base_values)
        else:
            context_block = f"Past market intelligence (retrieved):\n{past_items_text}"
        user_prompt = "\n\n".join(
            [
                render(prompt_lib.TASK_DESCRIPTION_MARKET_INTELLIGENCE, values),
                context_block,
                prompt_lib.MARKET_INTELLIGENCE_EFFECTS,
                render(prompt_lib.PAST_MARKET_INTELLIGENCE_PROMPT, values),
                prompt_lib.PAST_MARKET_INTELLIGENCE_OUTPUT_FORMAT,
            ]
        )
        raw = self.llm.complete_xml(stage="market_intelligence_past", system=prompt_lib.SYSTEM_CONTENT_TRADING, user=user_prompt)
        parsed = parse_finagent_xml(raw)
        artifact = {"prompt": user_prompt, "response": raw, "parsed": parsed}
        self.metadata_store.record_prompt(context.symbol, user_prompt, raw, stage="market_intelligence_past", run_id=run_id, execution_id=execution_id)
        summary = safe_get_str(parsed, "summary") or ""
        if summary:
            self.vector_memory.add_memory(symbol=context.symbol, stage="market_intelligence_past_summary", content=summary, metadata={})
        return {"prompt": user_prompt, "raw": raw, "parsed": parsed, "artifact": artifact}

    @staticmethod
    def _format_pct(value: float) -> str:
        pct = value * 100
        if abs(pct) < 0.05:
            return "no significant change"
        direction = "an increase" if pct > 0 else "a decrease"
        return f"{direction} of {abs(pct):.2f}%"

    def _price_movement_fields(self, context: FinAgentContext) -> Dict[str, str]:
        df = context.df
        df = df.sort_values("Date").reset_index(drop=True)
        close = df["Close"].astype(float)
        if close.empty:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            return {
                "date": today,
                "short_term_past_date_range": "1",
                "short_term_next_date_range": "1",
                "medium_term_past_date_range": "7",
                "medium_term_next_date_range": "7",
                "long_term_past_date_range": "14",
                "long_term_next_date_range": "14",
                "short_term_past_price_movement": "unknown",
                "short_term_next_price_movement": "unknown",
                "medium_term_past_price_movement": "unknown",
                "medium_term_next_price_movement": "unknown",
                "long_term_past_price_movement": "unknown",
                "long_term_next_price_movement": "unknown",
            }

        def movement(days: int) -> float:
            if len(close) <= days:
                return 0.0
            start = float(close.iloc[-(days + 1)])
            end = float(close.iloc[-1])
            return (end - start) / start if start else 0.0

        short_days, med_days, long_days = 1, 7, 14
        short_move = movement(short_days)
        med_move = movement(med_days)
        long_move = movement(long_days)
        today = df["Date"].iloc[-1]
        date_str = today.strftime("%Y-%m-%d") if hasattr(today, "strftime") else str(today)
        return {
            "date": date_str,
            "short_term_past_date_range": str(short_days),
            "short_term_next_date_range": str(short_days),
            "medium_term_past_date_range": str(med_days),
            "medium_term_next_date_range": str(med_days),
            "long_term_past_date_range": str(long_days),
            "long_term_next_date_range": str(long_days),
            "short_term_past_price_movement": self._format_pct(short_move),
            "short_term_next_price_movement": self._format_pct(short_move),
            "medium_term_past_price_movement": self._format_pct(med_move),
            "medium_term_next_price_movement": self._format_pct(med_move),
            "long_term_past_price_movement": self._format_pct(long_move),
            "long_term_next_price_movement": self._format_pct(long_move),
        }

    def _run_low_level_reflection(
        self,
        context: FinAgentContext,
        values: Dict[str, str],
        *,
        past_summary: str,
        latest_summary: str,
        execution_id: str,
        run_id: Optional[str],
    ) -> Dict[str, Any]:
        price_values = self._price_movement_fields(context)
        prompt_lib = self.prompts
        render = prompt_lib.render
        prompt_values = {**values, **price_values, "kline_path": context.chart_path or ""}
        if self.prompts_version.startswith("v3") and hasattr(prompt_lib, "MARKET_INTELLIGENCE_SUMMARIES_CONTEXT"):
            mi_block = render(
                prompt_lib.MARKET_INTELLIGENCE_SUMMARIES_CONTEXT,
                {
                    **values,
                    "past_market_intelligence_summary": past_summary or "N/A",
                    "latest_market_intelligence_summary": latest_summary or "N/A",
                },
            )
        else:
            mi_block = "\n".join(
                [
                    "Market intelligence summaries:",
                    f"Past summary:\n{past_summary or 'N/A'}",
                    f"Latest summary:\n{latest_summary or 'N/A'}",
                ]
            )
        user_prompt = "\n\n".join(
            [
                render(prompt_lib.TASK_DESCRIPTION_LOW_LEVEL_REFLECTION, values),
                mi_block,
                prompt_lib.MARKET_INTELLIGENCE_EFFECTS,
                render(prompt_lib.KLINE_CHART_DESCRIPTION, prompt_values),
                render(prompt_lib.PRICE_CHANGE_DESCRIPTION, prompt_values),
                prompt_lib.LOW_LEVEL_REFLECTION_EFFECTS,
                prompt_lib.LOW_LEVEL_REFLECTION_PROMPT,
                prompt_lib.LOW_LEVEL_REFLECTION_OUTPUT_FORMAT,
            ]
        )
        raw = self.llm.complete_xml(
            stage="low_level_reflection",
            system=prompt_lib.SYSTEM_CONTENT_TRADING,
            user=user_prompt,
            image_paths=[context.chart_path] if context.chart_path else None,
        )
        parsed = parse_finagent_xml(raw)
        artifact = {"prompt": user_prompt, "response": raw, "parsed": parsed}
        self.metadata_store.record_prompt(context.symbol, user_prompt, raw, stage="low_level_reflection", run_id=run_id, execution_id=execution_id)
        reasoning_map = get_required_map(parsed, "reasoning")
        query = safe_get_str(parsed, "query") or ""
        summary_text = (
            f"Short-Term: {reasoning_map.get('short_term_reasoning','')}\n"
            f"Medium-Term: {reasoning_map.get('medium_term_reasoning','')}\n"
            f"Long-Term: {reasoning_map.get('long_term_reasoning','')}"
        ).strip()
        if summary_text:
            self.vector_memory.add_memory(symbol=context.symbol, stage="low_level_reflection_summary", content=summary_text, metadata={"query": query})
        return {"prompt": user_prompt, "raw": raw, "parsed": parsed, "artifact": artifact, "summary_text": summary_text}

    def _get_past_stage_summary(self, symbol: str, *, stage_prefix: str) -> str:
        past = self.vector_memory.query_filtered(symbol=symbol, top_k=1, stage_prefix=stage_prefix)
        if not past:
            return ""
        return str(past[0].get("content") or "").strip()

    def _run_high_level_reflection(
        self,
        context: FinAgentContext,
        values: Dict[str, str],
        *,
        past_market_summary: str,
        latest_market_summary: str,
        past_low_level: str,
        latest_low_level: str,
        execution_id: str,
        run_id: Optional[str],
    ) -> Dict[str, Any]:
        look_back_days = 14
        previous_actions = self.vector_memory.query_filtered(symbol=context.symbol, top_k=look_back_days, stage_prefix="decision_action_reasoning")
        previous_action_and_reasoning = "\n".join(
            str(item.get("content", "")).strip() for item in reversed(previous_actions) if item.get("content")
        ).strip()
        if not previous_action_and_reasoning:
            previous_action_and_reasoning = "No prior trading decisions available."
        prompt_lib = self.prompts
        render = prompt_lib.render
        if self.prompts_version.startswith("v3") and hasattr(prompt_lib, "MARKET_INTELLIGENCE_SUMMARIES_CONTEXT"):
            mi_block = render(
                prompt_lib.MARKET_INTELLIGENCE_SUMMARIES_CONTEXT,
                {
                    **values,
                    "past_market_intelligence_summary": past_market_summary or "N/A",
                    "latest_market_intelligence_summary": latest_market_summary or "N/A",
                },
            )
        else:
            mi_block = "\n".join(
                [
                    "Market intelligence summaries:",
                    f"Past summary:\n{past_market_summary or 'N/A'}",
                    f"Latest summary:\n{latest_market_summary or 'N/A'}",
                ]
            )
        if self.prompts_version.startswith("v3") and hasattr(prompt_lib, "LOW_LEVEL_REFLECTION_CONTEXT"):
            low_level_block = render(
                prompt_lib.LOW_LEVEL_REFLECTION_CONTEXT,
                {
                    **values,
                    "past_low_level_reflection": past_low_level or "N/A",
                    "latest_low_level_reflection": latest_low_level or "N/A",
                },
            )
        else:
            low_level_block = "\n".join(
                [
                    "Low-level reflection (price movement reasoning):",
                    f"Past low-level reflection:\n{past_low_level or 'N/A'}",
                    f"Latest low-level reflection:\n{latest_low_level or 'N/A'}",
                ]
            )
        user_prompt = "\n\n".join(
            [
                render(prompt_lib.TASK_DESCRIPTION_HIGH_LEVEL_REFLECTION, values),
                mi_block,
                prompt_lib.MARKET_INTELLIGENCE_EFFECTS,
                low_level_block,
                prompt_lib.LOW_LEVEL_REFLECTION_EFFECTS,
                render(
                    prompt_lib.TRADING_CHART_DESCRIPTION,
                    {
                        **values,
                        "previous_action_look_back_days": str(look_back_days),
                        "previous_action_and_reasoning": previous_action_and_reasoning,
                        "trading_path": context.chart_path or "",
                    },
                ),
                prompt_lib.HIGH_LEVEL_REFLECTION_EFFECTS,
                prompt_lib.HIGH_LEVEL_REFLECTION_PROMPT,
                prompt_lib.HIGH_LEVEL_REFLECTION_OUTPUT_FORMAT,
            ]
        )
        raw = self.llm.complete_xml(
            stage="high_level_reflection",
            system=prompt_lib.SYSTEM_CONTENT_TRADING,
            user=user_prompt,
            image_paths=[context.chart_path] if context.chart_path else None,
        )
        parsed = parse_finagent_xml(raw)
        artifact = {"prompt": user_prompt, "response": raw, "parsed": parsed}
        self.metadata_store.record_prompt(context.symbol, user_prompt, raw, stage="high_level_reflection", run_id=run_id, execution_id=execution_id)
        summary_text = safe_get_str(parsed, "summary") or ""
        query = safe_get_str(parsed, "query") or ""
        if summary_text:
            self.vector_memory.add_memory(symbol=context.symbol, stage="high_level_reflection_summary", content=summary_text, metadata={"query": query})
        return {"prompt": user_prompt, "raw": raw, "parsed": parsed, "artifact": artifact, "summary_text": summary_text}

    @staticmethod
    def _ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    def _strategy_signals(self, context: FinAgentContext) -> Dict[str, str]:
        close = context.df["Close"].astype(float)
        # Strategy 1: MACD crossover
        ema12 = self._ema(close, 12)
        ema26 = self._ema(close, 26)
        macd = ema12 - ema26
        signal = self._ema(macd, 9)
        macd_last = float(macd.iloc[-1])
        signal_last = float(signal.iloc[-1])
        action1 = "HOLD"
        if macd_last > signal_last:
            action1 = "BUY"
        elif macd_last < signal_last:
            action1 = "SELL"
        strategy1 = f"Decision: {action1}. MACD={macd_last:.4f}, Signal={signal_last:.4f}."

        # Strategy 2: KDJ with RSI filter (simplified)
        low_n = context.df["Low"].astype(float).rolling(window=9, min_periods=3).min()
        high_n = context.df["High"].astype(float).rolling(window=9, min_periods=3).max()
        rsv = (close - low_n) / (high_n - low_n).replace(0, math.nan) * 100
        k = rsv.ewm(alpha=1 / 3, adjust=False).mean()
        d = k.ewm(alpha=1 / 3, adjust=False).mean()
        j = 3 * k - 2 * d
        k_last = float(k.iloc[-1]) if not math.isnan(float(k.iloc[-1])) else 50.0
        d_last = float(d.iloc[-1]) if not math.isnan(float(d.iloc[-1])) else 50.0
        j_last = float(j.iloc[-1]) if not math.isnan(float(j.iloc[-1])) else 50.0
        action2 = "HOLD"
        if k_last < 20 and context.rsi < 35:
            action2 = "BUY"
        elif k_last > 80 and context.rsi > 65:
            action2 = "SELL"
        strategy2 = f"Decision: {action2}. K={k_last:.2f}, D={d_last:.2f}, J={j_last:.2f}, RSI={context.rsi:.1f}."

        # Strategy 3 (paper labels as $$strategy4$$): mean reversion via z-score
        mean = close.rolling(window=20, min_periods=10).mean().iloc[-1]
        std = close.rolling(window=20, min_periods=10).std().iloc[-1]
        z = (context.last_close - float(mean)) / float(std) if std and not math.isnan(float(std)) else 0.0
        action3 = "HOLD"
        if z < -2:
            action3 = "BUY"
        elif z > 2:
            action3 = "SELL"
        strategy4 = f"Decision: {action3}. z-score={z:.2f} (window=20)."

        return {"strategy1": strategy1, "strategy2": strategy2, "strategy4": strategy4}

    def _run_decision_making(
        self,
        context: FinAgentContext,
        values: Dict[str, str],
        *,
        past_market_summary: str,
        latest_market_summary: str,
        past_low_level: str,
        latest_low_level: str,
        past_high_level: str,
        latest_high_level: str,
        baseline: Dict[str, Any],
        execution_id: str,
        run_id: Optional[str],
    ) -> Dict[str, Any]:
        trader_pref = "Risk-aware, medium-term trader focused on capital preservation and clear confirmations."
        guidance_lines = []
        for item in context.news:
            title = (item.get("title") or "").strip()
            summary = (item.get("summary") or "").strip()
            sentiment = (item.get("sentiment") or "neutral").strip()
            if not title and not summary:
                continue
            guidance_lines.append(f"- Headline: {title}\n  Content: {summary}\n  Sentiment: {sentiment}")
        guidance_text = "\n".join(guidance_lines).strip() or "No professional investment guidance available."

        prompt_lib = self.prompts
        render = prompt_lib.render

        strategies = self._strategy_signals(context)
        strategy_block = render(
            prompt_lib.DECISION_STRATEGY,
            {
                "strategy1": strategies["strategy1"],
                "strategy2": strategies["strategy2"],
                "strategy4": strategies["strategy4"],
            },
        )
        state_description = (
            "Current state constraints:\n"
            f"- Current Adj Close (proxy): {context.last_close:.2f}\n"
            "- CASH reserve (placeholder): 100000.00\n"
            "- Existing POSITION (placeholder): 0"
        )

        if self.prompts_version.startswith("v3") and hasattr(prompt_lib, "MARKET_INTELLIGENCE_SUMMARIES_CONTEXT"):
            mi_block = render(
                prompt_lib.MARKET_INTELLIGENCE_SUMMARIES_CONTEXT,
                {
                    **values,
                    "past_market_intelligence_summary": past_market_summary or "N/A",
                    "latest_market_intelligence_summary": latest_market_summary or "N/A",
                },
            )
        else:
            mi_block = "\n".join(
                [
                    "Market intelligence summaries:",
                    f"Past summary:\n{past_market_summary or 'N/A'}",
                    f"Latest summary:\n{latest_market_summary or 'N/A'}",
                ]
            )

        if self.prompts_version.startswith("v3") and hasattr(prompt_lib, "LOW_LEVEL_REFLECTION_CONTEXT"):
            low_level_block = render(
                prompt_lib.LOW_LEVEL_REFLECTION_CONTEXT,
                {
                    **values,
                    "past_low_level_reflection": past_low_level or "N/A",
                    "latest_low_level_reflection": latest_low_level or "N/A",
                },
            )
            low_level_block = "\n\n".join(
                [
                    low_level_block,
                    "Please consider these reflections, identify the potential price movements patterns and characteristics of this particular stock and incorporate these insights into your further analysis and reflections when applicable.",
                ]
            )
        else:
            low_level_block = "\n".join(
                [
                    "Low-level reflection (price movement reasoning):",
                    f"Past low-level reflection:\n{past_low_level or 'N/A'}",
                    f"Latest low-level reflection:\n{latest_low_level or 'N/A'}",
                ]
            )

        if self.prompts_version.startswith("v3") and hasattr(prompt_lib, "HIGH_LEVEL_REFLECTION_CONTEXT"):
            high_level_block = render(
                prompt_lib.HIGH_LEVEL_REFLECTION_CONTEXT,
                {
                    **values,
                    "past_high_level_reflection": past_high_level or "N/A",
                    "latest_high_level_reflection": latest_high_level or "N/A",
                },
            )
        else:
            high_level_block = "\n".join(
                [
                    "High-level reflection (trading decision reflection):",
                    f"Past high-level reflection:\n{past_high_level or 'N/A'}",
                    f"Latest high-level reflection:\n{latest_high_level or 'N/A'}",
                ]
            )

        user_prompt = "\n\n".join(
            [
                render(prompt_lib.TASK_DESCRIPTION_DECISION, values),
                render(prompt_lib.TRADER_PREFERENCE, {"trader_preference": trader_pref}),
                mi_block,
                prompt_lib.MARKET_INTELLIGENCE_EFFECTS,
                low_level_block,
                prompt_lib.LOW_LEVEL_REFLECTION_EFFECTS,
                high_level_block,
                prompt_lib.HIGH_LEVEL_REFLECTION_EFFECTS,
                render(prompt_lib.DECISION_GUIDANCE, {"guidance": guidance_text}),
                strategy_block,
                state_description,
                prompt_lib.DECISION_PROMPT,
                prompt_lib.DECISION_OUTPUT_FORMAT,
            ]
        )

        raw = self.llm.complete_xml(stage="decision", system=prompt_lib.SYSTEM_CONTENT_TRADING, user=user_prompt)
        parsed = parse_finagent_xml(raw)
        artifact = {"prompt": user_prompt, "response": raw, "parsed": parsed}
        self.metadata_store.record_prompt(context.symbol, user_prompt, raw, stage="decision", run_id=run_id, execution_id=execution_id)

        action_text = (safe_get_str(parsed, "action") or "HOLD").upper()
        analysis_text = safe_get_str(parsed, "analysis") or ""
        reasoning_text = safe_get_str(parsed, "reasoning") or ""
        decision_reasoning = "\n\n".join(
            [chunk for chunk in [analysis_text.strip(), reasoning_text.strip()] if chunk]
        ).strip()
        if not decision_reasoning:
            decision_reasoning = "Decision reasoning unavailable (empty model response)."

        action = action_text if action_text in {SignalAction.BUY.value, SignalAction.SELL.value, SignalAction.HOLD.value} else SignalAction.HOLD.value
        today = datetime.utcnow().strftime("%Y-%m-%d")
        self.vector_memory.add_memory(
            symbol=context.symbol,
            stage="decision_action_reasoning",
            content=f"{today}: {action} - {decision_reasoning[:240]}",
            metadata={"baseline": baseline},
        )
        return {
            "prompt": user_prompt,
            "raw_response": raw,
            "parsed": parsed,
            "artifact": artifact,
            "action": action,
            "reasoning_text": decision_reasoning,
        }

    def _compute_rl_baseline(self, context: FinAgentContext) -> Dict[str, Any]:
        directional_bias = "BUY" if context.sma_short > context.sma_long else "SELL" if context.sma_short < context.sma_long else "HOLD"
        expected_return = (context.sma_short / context.last_close - 1) if context.last_close else 0
        return {
            "ppo_action": directional_bias,
            "ppo_expected_return": expected_return,
            "dqn_action": directional_bias,
            "sac_action": directional_bias,
        }

    def _build_signal(
        self,
        context: FinAgentContext,
        reasoning: str,
        baseline: Dict[str, Any],
        *,
        action_override: Optional[str] = None,
    ) -> TradingSignal:
        confirmations = self._count_confirmations(context)
        confidence_pct = (confirmations / CONFIRMATION_FACTORS) * 100
        confidence = self._confidence_from_score(confidence_pct)
        action = action_override or self._determine_action(context)
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


class FinAgentLLMClient:
    """Minimal OpenAI client wrapper (with deterministic mock fallback) for FinAgent prompt stages."""

    def __init__(
        self,
        *,
        provider: str,
        api_key: str,
        base_url: str,
        model: str,
        vision_model: str,
    ) -> None:
        self.provider = (provider or "openai").lower()
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or "").strip()
        self.model = model
        self.vision_model = vision_model or model
        self.client = None

        if self.provider != "openai":
            logger.warning("FinAgentLLMClient running in mock mode; unsupported provider: %s", self.provider)
            return
        if not self.api_key or not _OPENAI_AVAILABLE or OpenAI is None:
            logger.warning("FinAgentLLMClient running in mock mode; OpenAI API key not configured or SDK missing")
            return
        try:
            kwargs: Dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self.client = OpenAI(**kwargs)
        except Exception as exc:  # pragma: no cover - network/path dependent
            logger.warning("FinAgentLLMClient falling back to mock mode: %s", exc)
            self.client = None

    @staticmethod
    def _encode_image(path: str) -> str:
        with open(path, "rb") as fh:
            return base64.b64encode(fh.read()).decode("utf-8")

    def complete_xml(
        self,
        *,
        stage: str,
        system: str,
        user: str,
        image_paths: Optional[List[str]] = None,
        max_tokens: int = 1500,
        temperature: float = 0.2,
    ) -> str:
        if not self.client:
            return self._mock_xml(stage=stage)

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system}]
        if image_paths:
            parts: List[Dict[str, Any]] = [{"type": "text", "text": user}]
            for path in image_paths:
                if not path or not os.path.exists(path):
                    continue
                encoded = self._encode_image(path)
                parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}})
            messages.append({"role": "user", "content": parts})
            model = self.vision_model
        else:
            messages.append({"role": "user", "content": user})
            model = self.model

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return (response.choices[0].message.content or "").strip()

    @staticmethod
    def _mock_xml(*, stage: str) -> str:
        if stage == "market_intelligence_latest":
            return (
                "<output>"
                "<string name=\"analysis\">- ID: 000001 - Key insight: neutral update; Duration: LONG-TERM; Sentiment: NEUTRAL.</string>"
                "<string name=\"summary\">Overall sentiment: NEUTRAL (mixed/uncertain).</string>"
                "<map name=\"query\">"
                "<string name=\"short_term_query\">earnings, guidance, price reaction</string>"
                "<string name=\"medium_term_query\">product, demand, valuation</string>"
                "<string name=\"long_term_query\">macro, rates, competition</string>"
                "</map>"
                "</output>"
            )
        if stage == "market_intelligence_past":
            return (
                "<output>"
                "<string name=\"analysis\">- ID: 000001 - Historical context: mixed; Duration: LONG-TERM; Sentiment: NEUTRAL.</string>"
                "<string name=\"summary\">Overall sentiment: NEUTRAL based on past context.</string>"
                "</output>"
            )
        if stage == "low_level_reflection":
            return (
                "<output>"
                "<map name=\"reasoning\">"
                "<string name=\"short_term_reasoning\">Short-term momentum is modest; catalysts are limited.</string>"
                "<string name=\"medium_term_reasoning\">Medium-term trend is influenced by MA alignment and sentiment.</string>"
                "<string name=\"long_term_reasoning\">Long-term movement reflects broader positioning and volatility.</string>"
                "</map>"
                "<string name=\"query\">momentum, moving average, volatility, sentiment</string>"
                "</output>"
            )
        if stage == "high_level_reflection":
            return (
                "<output>"
                "<string name=\"reasoning\">Past decisions show mixed outcomes; avoid overtrading.</string>"
                "<string name=\"improvement\">If wrong, wait for clearer confirmations before acting.</string>"
                "<string name=\"summary\">Lesson: prioritize confirmations and risk controls.</string>"
                "<string name=\"query\">confirmations, risk controls, avoid overtrading</string>"
                "</output>"
            )
        # decision
        return (
            "<output>"
            "<string name=\"analysis\">Market intelligence is mixed; rely more on signals and risk constraints.</string>"
            "<string name=\"action\">HOLD</string>"
            "<string name=\"reasoning\">Wait for stronger alignment across indicators before BUY/SELL.</string>"
            "</output>"
        )
