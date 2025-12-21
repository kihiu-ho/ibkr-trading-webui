"""Prompt templates adapted from arXiv:2402.18485v3 (FinAgent)."""

from __future__ import annotations

from textwrap import dedent
from typing import Dict


def render(template: str, values: Dict[str, str]) -> str:
    """Replace $$placeholders$$ in a prompt template."""
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"$${key}$$", value)
    return rendered


SYSTEM_CONTENT_TRADING = dedent(
    """
    You are an expert trader who has sufficient financial experience and provides expert guidance.
    Imagine working in a real market environment where you have access to various types of information
    (e.g., daily real-time market price, news, financial reports, professional investment guidance and market sentiment)
    relevant to financial markets.
    You will be able to view visual data that contains comprehensive information, including Kline charts accompanied by
    technical indicators, historical trading curves and cumulative return curves.
    There will be some auxiliary strategies providing you with explanations for trading decisions.
    You are capable of deeply analyzing, understanding, and summarizing information, and use this information to make
    informed and wise trading decisions (i.e., BUY, HOLD and SELL).
    """
).strip()


TASK_DESCRIPTION_MARKET_INTELLIGENCE = dedent(
    """
    You are currently focusing on summarizing and extracting the key insights of the market intelligence of a $$asset_type$$
    known as $$asset_name$$, which is denoted by the symbol $$asset_symbol$$.
    This $$asset_type$$ is publicly traded and is listed on the $$asset_exchange$$.
    Its primary operations are within the $$asset_sector$$ sector, specifically within the $$asset_industry$$ industry.
    To provide you with a better understanding, here is a brief description of $$asset_name$$: $$asset_description$$.
    In this role, your current goal as an analyst is to conduct a comprehensive summary of the market intelligence of the asset
    represented by the symbol $$asset_symbol$$.
    """
).strip()


MARKET_INTELLIGENCE_EFFECTS = dedent(
    """
    Considering the effects of market intelligence:
    1. If there is market intelligence UNRELATED to asset prices, you should ignore it (e.g., advertisements).
    2. Based on effect duration on asset prices:
       - SHORT-TERM: significant impact over the next few days
       - MEDIUM-TERM: impact over the next few weeks
       - LONG-TERM: impact over the next several months
       - If unclear, treat as LONG-TERM
    3. Based on sentiment:
       - POSITIVE: typically favorable; focus more on favorable effects but do not ignore unfavorable effects
       - NEGATIVE: typically unfavorable; focus more on unfavorable effects but do not ignore favorable effects
       - NEUTRAL: uncertain impact with no clear bias; if related but unclear, treat as NEUTRAL
    4. Intelligence related to collaborators or competitors may influence the asset price.
    5. Past intelligence usually has lower effect on the present; pay MORE attention to the latest intelligence.
    """
).strip()


LATEST_MARKET_INTELLIGENCE_PROMPT = dedent(
    """
    Based on the above information, analyze key insights and summarize the market intelligence.
    Please strictly follow the following constraints and output formats.

    "analysis":
    1. Disregard UNRELATED market intelligence.
    2. For each piece of market intelligence:
       - Extract key insights (MUST NOT contain IDs, $$asset_name$$ or $$asset_symbol$$)
       - Determine effect duration: SHORT-TERM, MEDIUM-TERM, or LONG-TERM (choose exactly one)
       - Determine sentiment: POSITIVE, NEGATIVE, or NEUTRAL (choose exactly one; prefer POSITIVE/NEGATIVE if possible)
    3. Keep each per-item analysis concise (<= 40 tokens per item).
    4. Format exactly:
       - ID: 000001 - ...
       - ID: 000002 - ...

    "summary":
    1. Disregard UNRELATED market intelligence.
    2. Focus primarily on asset-related investment insights for trading decisions.
    3. Combine insights with similar sentiment and effect duration.
    4. Provide overall sentiment (POSITIVE/NEGATIVE/NEUTRAL) with reasoning.
    5. MUST reference IDs (e.g., ID: 000001).
    6. Keep concise (<= 300 tokens).

    "query":
    Used to retrieve past market intelligence by effect duration.
    1. Disregard UNRELATED market intelligence.
    2. Focus on asset-related key insights + duration.
    3. Combine analyses with similar durations.
    4. Provide one query per duration: short_term_query, medium_term_query, long_term_query.
       - Use keywords from original intelligence
       - MUST NOT contain IDs, $$asset_name$$ or $$asset_symbol$$
       - Keep each query concise (<= 100 tokens)
    """
).strip()


LATEST_MARKET_INTELLIGENCE_OUTPUT_FORMAT = dedent(
    """
    You should ONLY return a valid XML object in this exact format:
    <output>
      <string name="analysis">...</string>
      <string name="summary">...</string>
      <map name="query">
        <string name="short_term_query">...</string>
        <string name="medium_term_query">...</string>
        <string name="long_term_query">...</string>
      </map>
    </output>
    """
).strip()


PAST_MARKET_INTELLIGENCE_PROMPT = dedent(
    """
    Based on the above information, analyze key insights and summarize the market intelligence.
    Please strictly follow the following constraints and output formats.

    "analysis":
    1. Disregard UNRELATED market intelligence.
    2. For each piece of market intelligence:
       - Extract key insights (MUST NOT contain IDs, $$asset_name$$ or $$asset_symbol$$)
       - Determine effect duration: SHORT-TERM, MEDIUM-TERM, or LONG-TERM (choose exactly one)
       - Determine sentiment: POSITIVE, NEGATIVE, or NEUTRAL (choose exactly one; prefer POSITIVE/NEGATIVE if possible)
    3. Keep each per-item analysis concise (<= 40 tokens per item).
    4. Format exactly:
       - ID: 000001 - ...
       - ID: 000002 - ...

    "summary":
    1. Disregard UNRELATED market intelligence.
    2. Focus primarily on asset-related investment insights for trading decisions.
    3. Combine insights with similar sentiment and effect duration.
    4. Provide overall sentiment (POSITIVE/NEGATIVE/NEUTRAL) with reasoning.
    5. MUST reference IDs (e.g., ID: 000001).
    6. Keep concise (<= 300 tokens).
    """
).strip()


PAST_MARKET_INTELLIGENCE_OUTPUT_FORMAT = dedent(
    """
    You should ONLY return a valid XML object in this exact format:
    <output>
      <string name="analysis">...</string>
      <string name="summary">...</string>
    </output>
    """
).strip()


TASK_DESCRIPTION_LOW_LEVEL_REFLECTION = dedent(
    """
    You are currently focusing on analyzing the price movement of a $$asset_type$$ known as $$asset_name$$, which is denoted
    by the symbol $$asset_symbol$$.
    This corporation is publicly traded and is listed on the $$asset_exchange$$.
    Its primary operations are within the $$asset_sector$$ sector, specifically within the $$asset_industry$$ industry.
    To provide you with a better understanding, here is a brief description of $$asset_name$$: $$asset_description$$.
    Your objective is to act as an analyst and formulate predictions regarding the future price movement of the asset
    represented by the symbol $$asset_symbol$$.
    """
).strip()


KLINE_CHART_DESCRIPTION = dedent(
    """
    The following is a Kline chart with Moving Average (MA) and Bollinger Bands (BB) technical indicators.
    1. MA smooths out price fluctuations and highlights longer-term trends.
    2. Bollinger Bands identify overbought/oversold conditions:
       - BBU: MA + 2σ, BBL: MA - 2σ
       - Wider bands imply higher volatility; narrower implies lower volatility.
    3. The chart shows price movements over time:
       - Horizontal axis: date; vertical axis: price.
       - Candlestick real body: open-close range; shadows: high/low.
       - GREEN candle: close > open; RED candle: close < open.
       - MA5 is BLUE; BBL is GREEN; BBU is YELLOW.
       - Grey balloon marker indicates today's date.
    """
).strip()


PRICE_CHANGE_DESCRIPTION = dedent(
    """
    As the Kline chart shows, today's date is $$date$$.
    The chart's date range is from past $$long_term_past_date_range$$ days to next $$long_term_next_date_range$$ days.
    Price movements can be categorized into three time horizons:
    1. Short-Term: past $$short_term_past_date_range$$ days: $$short_term_past_price_movement$$; next $$short_term_next_date_range$$ days: $$short_term_next_price_movement$$.
    2. Medium-Term: past $$medium_term_past_date_range$$ days: $$medium_term_past_price_movement$$; next $$medium_term_next_date_range$$ days: $$medium_term_next_price_movement$$.
    3. Long-Term: past $$long_term_past_date_range$$ days: $$long_term_past_price_movement$$; next $$long_term_next_date_range$$ days: $$long_term_next_price_movement$$.
    * For each price movement, do not only focus on start/end prices; pay attention to the price-change trend.
    """
).strip()


LOW_LEVEL_REFLECTION_EFFECTS = dedent(
    """
    Lessons learned from analysis of price movements:
    1. Momentum: prices tend to keep moving in their current direction over time. Securities that performed well often continue
       performing well; those that performed poorly often continue performing poorly.
    2. Identify potential price-movement patterns and characteristics for this asset and incorporate these insights into further
       analysis and reflections when applicable.
    """
).strip()


LOW_LEVEL_REFLECTION_PROMPT = dedent(
    """
    Based on the above information, analyze the market-intelligence summaries and the Kline chart reasoning that led from past to
    future price movements.

    "reasoning":
    - Provide three fields: short_term_reasoning, medium_term_reasoning, long_term_reasoning.
    - For each horizon:
      - Consider a trend shift from past to future.
      - Analyze market intelligence that led to price movements (pay MORE attention to latest intelligence).
      - Analyze the Kline chart focusing on price changes and drivers.
      - Keep concise (<= 300 tokens per horizon).

    "query":
    - Summarize each horizon reasoning into a concise sentence (<= 100 tokens) to extract key information for retrieving past
      reasoning for price movements.
    """
).strip()


LOW_LEVEL_REFLECTION_OUTPUT_FORMAT = dedent(
    """
    You should ONLY return a valid XML object in this exact format:
    <output>
      <map name="reasoning">
        <string name="short_term_reasoning">...</string>
        <string name="medium_term_reasoning">...</string>
        <string name="long_term_reasoning">...</string>
      </map>
      <string name="query">...</string>
    </output>
    """
).strip()


TASK_DESCRIPTION_HIGH_LEVEL_REFLECTION = dedent(
    """
    You are currently targeting the trading decisions of a $$asset_type$$ known as $$asset_name$$, which is denoted by the symbol
    $$asset_symbol$$.
    This $$asset_type$$ is publicly traded and is listed on the $$asset_exchange$$.
    Its primary operations are within the $$asset_sector$$ sector, specifically within the $$asset_industry$$ industry.
    To provide you with a better understanding, here is a brief description of $$asset_name$$: $$asset_description$$.
    Your objective is to make correct trading decisions during the trading process of the asset represented by $$asset_symbol$$,
    considering step-by-step decision reasoning.
    """
).strip()


TRADING_CHART_DESCRIPTION = dedent(
    """
    Trading chart and cumulative returns:
    1. Trading chart: Adj Close price movements with trading decisions over time.
       - GREEN rhombic marker: BUY; RED balloon marker: SELL; no sign: HOLD.
    2. Cumulative returns chart:
       - Cumulative return > 0 indicates profit; < 0 indicates loss.

    Trading decisions and reasoning for the past $$previous_action_look_back_days$$ days:
    $$previous_action_and_reasoning$$
    """
).strip()


HIGH_LEVEL_REFLECTION_EFFECTS = dedent(
    """
    Lessons learned from reflection of past trading decisions:
    1. Learning from correct and wrong experiences can provide guidance for subsequent decisions to maximize profit.
    """
).strip()


HIGH_LEVEL_REFLECTION_PROMPT = dedent(
    """
    Based on the above information, think step-by-step and provide detailed analysis and summary to highlight key investment
    insights.

    "reasoning":
    - Reflect on whether each decision was right or wrong and provide reasoning.
    - A right decision would lead to increased return; a wrong decision leads otherwise.
    - Analyze contributing factors of success/mistakes considering market intelligence, Kline analysis, indicators, signals,
      and price-movement reflections; include weightings.

    "improvement":
    - If there are bad decisions, explain how you would revise them to maximize return.
    - Provide detailed list of improvements, e.g., 2023-01-03: HOLD -> BUY.

    "summary":
    - Summarize lessons learned from successes/mistakes that can be adapted to future decisions; draw connections between similar
      scenarios and apply learned lessons.

    "query":
    - Summarize the summary into a concise sentence (<= 1000 tokens) to extract key information for retrieving past reflection.
    """
).strip()


HIGH_LEVEL_REFLECTION_OUTPUT_FORMAT = dedent(
    """
    You should ONLY return a valid XML object in this exact format:
    <output>
      <string name="reasoning">...</string>
      <string name="improvement">...</string>
      <string name="summary">...</string>
      <string name="query">...</string>
    </output>
    """
).strip()


TASK_DESCRIPTION_DECISION = dedent(
    """
    You are currently targeting the trading of a company known as $$asset_name$$, denoted by $$asset_symbol$$.
    The company is publicly traded and listed on $$asset_exchange$$.
    Its primary operations are within the $$asset_sector$$ sector, specifically within the $$asset_industry$$ industry.
    Brief description of $$asset_name$$: $$asset_description$$.
    Your objective is to make correct trading decisions during the trading process of the asset represented by $$asset_symbol$$,
    considering step-by-step decision reasoning.
    """
).strip()


TRADER_PREFERENCE = dedent(
    """
    $$trader_preference$$
    """
).strip()


DECISION_GUIDANCE = dedent(
    """
    As follows are the professional investment guidances, including headlines, content, and market sentiment:
    $$guidance$$
    """
).strip()


DECISION_STRATEGY = dedent(
    """
    As follows are the trading strategies, including current state-based investment decisions and investment explanations.

    1. MACD Crossover Strategy - generates BUY when MACD crosses above signal (bullish momentum), SELL when it crosses below
       (bearish momentum).
       $$strategy1$$

    2. KDJ with RSI Filter Strategy - best in sideways markets; uses KDJ for momentum signals and RSI as a filter for reversals.
       $$strategy2$$

    3. Mean Reversion Strategy - assumes prices revert to mean; uses z-score deviations to signal BUY (oversold) / SELL
       (overbought).
       $$strategy4$$
    """
).strip()


DECISION_PROMPT = dedent(
    """
    Based on the above information, step-by-step analyze the summary of market intelligence and provide reasoning for whether you
    should BUY, SELL, or HOLD the asset. Please strictly follow the constraints and output formats.

    "analysis": How the above information affects the decision:
    1. Determine whether market intelligence is overall positive, negative, or neutral.
       - If overall neutral, pay less attention to market intelligence summary.
       - If positive/negative, provide a decision based on this.
    2. From analysis of price movements, determine whether future trend is bullish or bearish and reflect on lessons learned.
       - Bullish: consider BUY instead of HOLD.
       - Bearish: consider SELL instead of HOLD.
    3. From reflection of past trading decisions, reflect on lessons learned.
       - If missed a BUY opportunity, BUY as soon as possible.
       - If missed a SELL, SELL immediately.
    4. From professional investment guidances, determine bullish/bearish trend and provide decision.
    5. From trading strategies decisions/explanations, consider them together and provide decision.
    6. Pay less attention to neutral/unrelated market intelligence.
    7. Pay more attention to market intelligence that can cause an immediate impact on price.
    8. If market intelligence is mixed, pay more attention to professional investment guidances and consider which guidance is
       trustworthy based on historical price.
    9. Check current situation constraints:
       - If CASH reserve < current Adj Close price, action MUST NOT be BUY.
       - If there is no existing POSITION, action MUST NOT be SELL.
    10. Combine all analyses and determine whether it is suitable to BUY, SELL, or HOLD, and provide final decision.

    "reasoning": Provide detailed step-by-step reasoning for each point of the analysis and the final result.

    "action": Output exactly one of BUY, HOLD, SELL.
    """
).strip()


DECISION_OUTPUT_FORMAT = dedent(
    """
    You should ONLY return a valid XML object in this exact format:
    <output>
      <string name="analysis">...</string>
      <string name="action">BUY|HOLD|SELL</string>
      <string name="reasoning">...</string>
    </output>
    """
).strip()


__all__ = [
    "render",
    "SYSTEM_CONTENT_TRADING",
    "TASK_DESCRIPTION_MARKET_INTELLIGENCE",
    "MARKET_INTELLIGENCE_EFFECTS",
    "LATEST_MARKET_INTELLIGENCE_PROMPT",
    "LATEST_MARKET_INTELLIGENCE_OUTPUT_FORMAT",
    "PAST_MARKET_INTELLIGENCE_PROMPT",
    "PAST_MARKET_INTELLIGENCE_OUTPUT_FORMAT",
    "TASK_DESCRIPTION_LOW_LEVEL_REFLECTION",
    "KLINE_CHART_DESCRIPTION",
    "PRICE_CHANGE_DESCRIPTION",
    "LOW_LEVEL_REFLECTION_EFFECTS",
    "LOW_LEVEL_REFLECTION_PROMPT",
    "LOW_LEVEL_REFLECTION_OUTPUT_FORMAT",
    "TASK_DESCRIPTION_HIGH_LEVEL_REFLECTION",
    "TRADING_CHART_DESCRIPTION",
    "HIGH_LEVEL_REFLECTION_EFFECTS",
    "HIGH_LEVEL_REFLECTION_PROMPT",
    "HIGH_LEVEL_REFLECTION_OUTPUT_FORMAT",
    "TASK_DESCRIPTION_DECISION",
    "TRADER_PREFERENCE",
    "DECISION_GUIDANCE",
    "DECISION_STRATEGY",
    "DECISION_PROMPT",
    "DECISION_OUTPUT_FORMAT",
]

