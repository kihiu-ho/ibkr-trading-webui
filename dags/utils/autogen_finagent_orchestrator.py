"""AutoGen-orchestrated FinAgent-style multi-agent decision helper.

This module provides a lightweight AutoGen group chat wrapper that can be used inside
Airflow tasks to generate a TradingSignal-style decision while capturing an auditable
conversation trace suitable for MLflow logging.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
from concurrent.futures import Future
from dataclasses import dataclass
from decimal import Decimal
import inspect
import threading
from typing import Any, Awaitable, Dict, List, Optional, Sequence, Tuple, TypeVar

import pandas as pd

from models.market_data import MarketData
from models.signal import SignalAction, SignalConfidence, TradingSignal
from utils.config import config

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _run_awaitable(awaitable: Awaitable[T]) -> T:
    """Run an awaitable to completion from sync code.

    AutoGen's agentchat APIs are async in newer versions. Airflow PythonOperators are sync, so we
    bridge by running the coroutine in a fresh event loop. If an event loop is already running in
    this thread, we execute the awaitable in a dedicated thread instead.
    """

    async def _runner() -> T:
        return await awaitable

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_runner())

    future: Future[T] = Future()

    def _thread_target() -> None:
        try:
            future.set_result(asyncio.run(_runner()))
        except BaseException as exc:
            future.set_exception(exc)

    thread = threading.Thread(target=_thread_target, name="autogen-awaitable-runner", daemon=True)
    thread.start()
    return future.result()


def _decimal(value: Optional[float]) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(round(float(value), 4)))
    except Exception:
        return None


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
    value = float(rsi.iloc[-1])
    return value if not math.isnan(value) else 50.0


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


def _compute_context(
    market_data: MarketData,
    *,
    news_items: Optional[List[Dict[str, Any]]] = None,
    support_resistance_lookback: int = 50,
) -> Dict[str, Any]:
    df = _market_data_to_dataframe(market_data)
    close = df["close"] if not df.empty else pd.Series(dtype=float)
    last_close = float(close.iloc[-1]) if len(close) else float(market_data.latest_price)
    sma_short = float(close.rolling(window=20).mean().iloc[-1]) if len(close) >= 20 else last_close
    sma_long = float(close.rolling(window=50).mean().iloc[-1]) if len(close) >= 50 else last_close
    rsi = _calculate_rsi(close, period=14) if len(close) else 50.0

    returns = close.pct_change().dropna() if len(close) else pd.Series(dtype=float)
    volatility = float(returns.std() * math.sqrt(252)) if len(returns) else 0.0

    lookback = max(10, min(int(support_resistance_lookback), len(df))) if len(df) else 0
    recent = df.tail(lookback) if lookback else df
    support = float(recent["low"].min()) if not recent.empty else None
    resistance = float(recent["high"].max()) if not recent.empty else None

    return {
        "symbol": market_data.symbol,
        "timeframe": market_data.timeframe,
        "bars": market_data.bar_count,
        "latest_price": last_close,
        "sma_20": sma_short,
        "sma_50": sma_long,
        "rsi_14": rsi,
        "volatility_ann": volatility,
        "support": support,
        "resistance": resistance,
        "news_items": (news_items or [])[:10],
        "price_series_tail": [
            {"timestamp": row["timestamp"].isoformat(), "close": float(row["close"])}
            for _, row in df.tail(30).iterrows()
        ]
        if not df.empty
        else [],
    }


def _confidence_level(score: Decimal) -> SignalConfidence:
    if score >= 80:
        return SignalConfidence.HIGH
    if score >= 50:
        return SignalConfidence.MEDIUM
    return SignalConfidence.LOW


@dataclass
class AutoGenDecision:
    signal: TradingSignal
    conversation: List[Dict[str, Any]]
    agent_outputs: Dict[str, Any]


class AutoGenFinAgentOrchestrator:
    """Runs a constrained AutoGen multi-agent conversation and returns a TradingSignal."""

    def __init__(
        self,
        *,
        max_turns: Optional[int] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.max_turns = max_turns or max(4, int(config.finagent_autogen_max_rounds))
        self.model_name = (model_name or config.llm_model).strip()
        self.api_key = api_key if api_key is not None else config.llm_api_key
        self.base_url = base_url if base_url is not None else config.llm_api_base_url

    @staticmethod
    def _lazy_import_autogen():
        try:
            from autogen_agentchat.agents import AssistantAgent
            from autogen_agentchat.conditions import TextMentionTermination
            from autogen_agentchat.teams import RoundRobinGroupChat
            from autogen_ext.models.openai import OpenAIChatCompletionClient
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError(
                "AutoGen dependencies missing. Install `autogen-agentchat`, `autogen-core`, "
                "and `autogen-ext[openai]` in the Airflow environment."
            ) from exc

        return AssistantAgent, TextMentionTermination, RoundRobinGroupChat, OpenAIChatCompletionClient

    def run(
        self,
        *,
        market_data: MarketData,
        news_items: Optional[List[Dict[str, Any]]] = None,
        max_turns: Optional[int] = None,
    ) -> AutoGenDecision:
        AssistantAgent, TextMentionTermination, RoundRobinGroupChat, OpenAIChatCompletionClient = self._lazy_import_autogen()

        if not self.api_key:
            raise RuntimeError("LLM API key missing (set LLM_API_KEY or OPENAI_API_KEY).")

        model_client = OpenAIChatCompletionClient(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0,
            model_capabilities={"vision": False, "function_calling": True, "json_output": True},
        )

        context = _compute_context(market_data, news_items=news_items)

        technical_agent = AssistantAgent(
            "TechnicalAnalyst",
            model_client,
            system_message=(
                "You are a technical analyst. Use only the provided context. "
                "Provide a concise technical read (trend, support/resistance, indicators) "
                "and what it implies for BUY/SELL/HOLD. Do not output JSON."
            ),
        )
        fundamental_agent = AssistantAgent(
            "FundamentalAnalyst",
            model_client,
            system_message=(
                "You are a fundamental/news analyst. Use only the provided context (news_items). "
                "Summarize material positives/negatives and sentiment impact. Do not output JSON."
            ),
        )
        risk_agent = AssistantAgent(
            "RiskManager",
            model_client,
            system_message=(
                "You are a risk manager. Given the technical/fundamental summaries, propose conservative "
                "entry/stop/take-profit levels and position sizing thoughts. Prefer HOLD when uncertain. "
                "Do not output JSON."
            ),
        )
        executor_agent = AssistantAgent(
            "Executor",
            model_client,
            system_message=(
                "You are the executor. Synthesize the team discussion into a single trading decision. "
                "Output ONLY a JSON object with keys: action, confidence_score, reasoning, key_factors, "
                "trend, support_level, resistance_level, suggested_entry_price, suggested_stop_loss, "
                "suggested_take_profit, timeframe_analyzed. After the JSON, output the word TERMINATE."
            ),
        )

        termination = TextMentionTermination("TERMINATE", sources=["Executor"])
        team = RoundRobinGroupChat(
            participants=[technical_agent, fundamental_agent, risk_agent, executor_agent],
            termination_condition=termination,
            max_turns=max_turns or self.max_turns,
        )

        task = (
            "Generate a trading signal for the following context. "
            "You MUST base answers only on this context.\n\n"
            f"CONTEXT_JSON={json.dumps(context, indent=2)}\n"
        )

        result = team.run(task=task)
        if inspect.isawaitable(result):
            result = _run_awaitable(result)
        conversation = [message.model_dump() for message in result.messages]

        decision_text = None
        for message in reversed(result.messages):
            if getattr(message, "source", None) == "Executor":
                payload = message.model_dump()
                decision_text = payload.get("content") or payload.get("text") or payload.get("message")
                if decision_text:
                    break

        if not decision_text:
            raise RuntimeError("AutoGen conversation ended without an Executor decision.")

        # Extract JSON object from the executor output (ignore trailing TERMINATE).
        json_start = decision_text.find("{")
        json_end = decision_text.rfind("}")
        if json_start == -1 or json_end == -1 or json_end <= json_start:
            raise ValueError("Executor did not return a JSON object.")
        decision_obj = json.loads(decision_text[json_start : json_end + 1])

        action_raw = str(decision_obj.get("action", "HOLD")).upper()
        if action_raw not in {SignalAction.BUY.value, SignalAction.SELL.value, SignalAction.HOLD.value}:
            action_raw = SignalAction.HOLD.value
        action = SignalAction(action_raw)

        confidence_score = _decimal(decision_obj.get("confidence_score")) or Decimal("50")
        confidence = _confidence_level(confidence_score)

        reasoning = str(decision_obj.get("reasoning") or "").strip()
        if len(reasoning) < 10:
            reasoning = (
                "AutoGen executor returned an incomplete rationale; defaulting to conservative interpretation "
                "of the provided context."
            )

        signal = TradingSignal(
            symbol=market_data.symbol,
            action=action,
            confidence=confidence,
            confidence_score=confidence_score,
            reasoning=reasoning,
            key_factors=list(decision_obj.get("key_factors") or []),
            trend=decision_obj.get("trend"),
            support_level=_decimal(decision_obj.get("support_level")),
            resistance_level=_decimal(decision_obj.get("resistance_level")),
            suggested_entry_price=_decimal(decision_obj.get("suggested_entry_price")),
            suggested_stop_loss=_decimal(decision_obj.get("suggested_stop_loss")),
            suggested_take_profit=_decimal(decision_obj.get("suggested_take_profit")),
            timeframe_analyzed=str(decision_obj.get("timeframe_analyzed") or market_data.timeframe),
            model_used=self.model_name,
        )

        agent_outputs = {
            "context": context,
            "stop_reason": result.stop_reason,
        }
        return AutoGenDecision(signal=signal, conversation=conversation, agent_outputs=agent_outputs)
