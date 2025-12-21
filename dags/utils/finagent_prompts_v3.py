"""Prompt templates verbatim from arXiv:2402.18485v3 (FinAgent) Appendix F.

These templates are plain-text equivalents of the paper's HTML templates/iframes.
Placeholders are preserved as $$key$$ for late binding.
"""

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
    You are an expert trader who have sufficient financial experience and provides expert guidance. Imagine working in a
    real market environment where you have access to various types of information (e.g., daily real-time market price, news,
    financial reports, professional investment guidance and market sentiment) relevant to financial markets. You will be able to view
    visual data that contains comprehensive information, including Kline charts accompanied by technical indicators, historical
    trading curves and cumulative return curves. And there will be some auxiliary strategies providing you with explanations for
    trading decisions. You are capable of deeply analyzing, understanding, and summarizing information, and use these information to
    make informed and wise trading decisions (i.e., BUY, HOLD and SELL).
    """
).strip()


TASK_DESCRIPTION_MARKET_INTELLIGENCE = dedent(
    """
    You are currently focusing on summarizing and extracting the key insights of the market intelligence of a $$asset_type$$ known as
    $$asset_name$$, which is denoted by the symbol $$asset_symbol$$. This $$asset_type$$ is publicly traded and is listed on the
    $$asset_exchange$$. Its primary operations are within the $$asset_sector$$ sector, specifically within the $$asset_industry$$
    industry. To provide you with a better understanding, here is a brief description of $$asset_name$$: $$asset_description$$. In
    this role, your current goal as an analyst is to conduct a comprehensive summary of the market intelligence of the asset
    represented by the symbol $$asset_symbol$$. To do so effectively, you will rely on a comprehensive set of information as follows:
    """
).strip()


LATEST_MARKET_INTELLIGENCE_CONTEXT = dedent(
    """
    The following market intelligence (e.g., news, financial reports) contains latest (i.e., today) information related to
    $$asset_symbol$$, including the corresponding dates, headlines, and contents, with each item distinguished by a unique ID.
    Furthermore, if the day is not closed for trading, the section also provides the open, high, low, close, and adjusted close prices.

    Latest market intelligence and prices are as follows:
    $$latest_market_intelligence$$
    """
).strip()


PAST_MARKET_INTELLIGENCE_CONTEXT = dedent(
    """
    The following market intelligence (e.g., news, financial reports) contains past (i.e., before today) information related to
    $$asset_symbol$$, including the corresponding dates, headlines, and contents, with each item distinguished by a unique ID.
    Furthermore, if the day is not closed for trading, the section also provides the open, high, low, close, and adjusted close prices.

    Past market intelligence and prices are as follows:
    $$past_market_intelligence$$
    """
).strip()


MARKET_INTELLIGENCE_SUMMARIES_CONTEXT = dedent(
    """
    The following are summaries of the latest (i.e., today) and past (i.e., before today) market intelligence
    (e.g., news, financial reports) you've provided.

    The following is a summary from your assistant of the past market intelligence:
    $$past_market_intelligence_summary$$

    The following is a summary from your assistant of the latest market intelligence:
    $$latest_market_intelligence_summary$$
    """
).strip()


MARKET_INTELLIGENCE_EFFECTS = dedent(
    """
    Considering the effects of market intelligence can be in the following ways:
    1. If there is market intelligence UNRELATED to asset prices, you should ignore it. For example, advertisements on some news
       platforms.
    2. Based on the duration of their effects on asset prices, market intelligence can be divided into three types:
       - SHORT-TERM market intelligence can significantly impact asset prices over the next few days.
       - MEDIUM-TERM market intelligence is likely to impact asset prices for the upcoming few weeks.
       - LONG-TERM market intelligence should have an impact on asset prices for the next several months.
       - If the duration of the market intelligence impact is not clear, then you should consider it as LONG-TERM.
    3. According to market sentiment, market intelligence can be divided into three types:
       - POSITIVE market intelligence typically has favorable effects on asset prices. You should focus more on the favorable effects,
         but do not ignore the unfavorable effects:
         - Favorable: Positive market intelligence boosts investor confidence, increases asset demand, enhances asset image, and
           reflects asset health. It may lead to increased buying activity and a potential increase in asset prices.
         - Unfavorable: Positive market intelligence can lead to market overreaction and volatility, short-term investment focus, risk
           of price manipulation, and may have only a temporary effect on stock prices. It may contribute to a decline in asset prices.
       - NEGATIVE market intelligence typically has unfavorable effects on asset prices. You should focus more on the unfavorable
         effects, but do not ignore the favorable effects:
         - Favorable: Negative market intelligence act as a market correction mechanism, provide crucial investment information,
           ultimately contributing to the long-term health of the market and the asset prices.
         - Unfavorable: Negative market intelligence lead to investor panic and a short-term decline in stock prices, as well as cause
           long-term damage to a company's reputation and brand, adversely contributing to a decline in asset prices.
       - NEUTRAL market intelligence describes an event that has an uncertain impact on the asset price with no apparent POSITIVE or
         NEGATIVE bias.
       - If the market intelligence is RELATED to the $$asset_name$$, but it's not clear whether the sentiment is positive or
         negative. Then you should consider it as NEUTRAL.
    4. Market intelligence related to the asset collaborators or competitors may influence the asset prices.
    5. Because the past market intelligence has a lower effect on the present, you should pay MORE attention to the latest market
       intelligence.
    """
).strip()


LATEST_MARKET_INTELLIGENCE_PROMPT = dedent(
    """
    Based on the above information, you should analyze the key insights and summarize the market intelligence.
    Please strictly follow the following constraints and output formats:

    "analysis": This field is used to extract key insights from the above information. You should analyze step-by-step and
    follow the rules as follows and do not miss any of them:
    1. Please disregard UNRELATED market intelligence.
    2. For each piece of market intelligence, you should analyze it and extract key insights according to the following steps:
       - Extract the key insights that can represent this market intelligence. It should NOT contain IDs, $$asset_name$$ or
         $$asset_symbol$$.
       - Analyze the market effects duration and provide the duration of the effects on asset prices. You are only allowed to select
         the only one of the three types: SHORT-TERM, MEDIUM-TERM and LONG-TERM.
       - Analyze the market sentiment and provide the type of market sentiment. A clear preference over POSITIVE or NEGATIVE is much
         better than being NEUTRAL. You are only allowed to select the only one of the three types: POSITIVE, NEGATIVE and NEUTRAL.
    3. The analysis you provide for each piece of market intelligence should be concise and clear, with no more than 40 tokens per
       piece.
    4. Your analysis MUST be in the following format:
       - ID: 000001 - Analysis that you provided for market intelligence 000001.
       - ID: 000002 - Analysis that you provided for market intelligence 000002.
       - ...

    "summary": This field is used to summarize the above analysis and extract key investment insights. You should summarize
    step-by-step and follow the rules as follows and do not miss any of them:
    1. Please disregard UNRELATED market intelligence.
    2. Because this field is primarily used for decision-making in trading tasks, you should focus primarily on asset related key
       investment insights.
    3. Please combine and summarize market intelligence on similar sentiment tendencies and duration of effects on asset prices.
    4. You should provide an overall analysis of all the market intelligence, explicitly provide a market sentiment (POSITIVE,
       NEGATIVE or NEUTRAL) and provide a reasoning for the analysis.
    5. Summary that you provided for market intelligence should contain IDs (e.g., ID: 000001, 000002).
    6. The summary you provide should be concise and clear, with no more than 300 tokens.

    "query": This field will be used to retrieve past market intelligence based on the duration of effects on asset prices. You
    should summarize step-by-step the above analysis and extract key insights. Please follow the rules as follows and do not miss
    any of them:
    1. Please disregard UNRELATED market intelligence.
    2. Because this field is primarily used for retrieving past market intelligence based on the duration of effects on asset
       prices, you should focus primarily on asset related key insights and duration of effects.
    3. Please combine the analysis of market intelligence on similar duration of effects on asset prices.
    4. You should provide a query text for each duration of effects on asset prices, which can be associated with several pieces of
       market intelligence.
       - The query text that you provide should be primarily keywords from the original market intelligence contained.
       - The query text that you provide should NOT contain IDs, $$asset_name$$ or $$asset_symbol$$.
       - The query text that you provide should be concise and clear, with no more than 100 tokens per query.
    """
).strip()


LATEST_MARKET_INTELLIGENCE_OUTPUT_FORMAT = dedent(
    """
    You should ONLY return a valid XML object. You MUST FOLLOW the XML output format as follows:
    <output>
      <string name="analysis">- ID: 000001 - Analysis that you provided for market intelligence 000001. - ID: 000002 - Analysis that you provided for market intelligence 000002...</string>
      <string name="summary">The summary that you provided.</string>
      <map name="query">
        <string name="short_term_query">Query text that you provided for SHORT-TERM.</string>
        <string name="medium_term_query">Query text that you provided for MEDIUM-TERM.</string>
        <string name="long_term_query">Query text that you provided for LONG-TERM.</string>
      </map>
    </output>
    """
).strip()


PAST_MARKET_INTELLIGENCE_PROMPT = dedent(
    """
    Based on the above information, you should analyze the key insights and summarize the market intelligence. Please
    strictly follow the following constraints and output formats:

    "analysis": This field is used to extract key insights from the above information. You should analyze step-by-step and
    follow the rules as follows and do not miss any of them:
    1. Please disregard UNRELATED market intelligence.
    2. For each piece of market intelligence, you should analyze it and extract key insights according to the following steps:
       - Extract the key insights that can represent this market intelligence. It should NOT contain IDs, $$asset_name$$ or
         $$asset_symbol$$.
       - Analyze the market effects duration and provide the duration of the effects on asset prices. You are only allowed to select
         the only one of the three types: SHORT-TERM, MEDIUM-TERM and LONG-TERM.
       - Analyze the market sentiment and provide the type of market sentiment. A clear preference over POSITIVE or NEGATIVE is much
         better than being NEUTRAL. You are only allowed to select the only one of the three types: POSITIVE, NEGATIVE and NEUTRAL.
    3. The analysis you provide for each piece of market intelligence should be concise and clear, with no more than 40 tokens per
       piece.
    4. Your analysis MUST be in the following format:
       - ID: 000001 - Analysis that you provided for market intelligence 000001.
       - ID: 000002 - Analysis that you provided for market intelligence 000002.
       - ...

    "summary": This field is used to summarize the above analysis and extract key investment insights. You should summarize
    step-by-step and follow the rules as follows and do not miss any of them:
    1. Please disregard UNRELATED market intelligence.
    2. Because this field is primarily used for decision-making in trading tasks, you should focus primarily on asset related key
       investment insights.
    3. Please combine and summarize market intelligence on similar sentiment tendencies and duration of effects on asset prices.
    4. You should provide an overall analysis of all the market intelligence, explicitly provide a market sentiment (POSITIVE,
       NEGATIVE or NEUTRAL) and provide a reasoning for the analysis.
    5. Summary that you provided for market intelligence should contain IDs (e.g., ID: 000001, 000002).
    6. The summary you provide should be concise and clear, with no more than 300 tokens.
    """
).strip()


PAST_MARKET_INTELLIGENCE_OUTPUT_FORMAT = dedent(
    """
    You should ONLY return a valid XML object. You MUST FOLLOW the XML output format as follows:
    <output>
      <string name="analysis">- ID: 000001 - Analysis that you provided for market intelligence 000001. - ID: 000002 - Analysis that you provided for market intelligence 000002...</string>
      <string name="summary">The summary that you provided.</string>
    </output>
    """
).strip()


TASK_DESCRIPTION_LOW_LEVEL_REFLECTION = dedent(
    """
    You are currently focusing on analyzing the price movement of a $$asset_type$$ known as $$asset_name$$, which is
    denoted by the symbol $$asset_symbol$$. This corporation is publicly traded and is listed on the $$asset_exchange$$. Its primary
    operations are within the $$asset_sector$$ sector, specifically within the $$asset_industry$$ industry. To provide you with a
    better understanding, here is a brief description of $$asset_name$$: $$asset_description$$. In this role, your objective is to
    act as an analyst and formulate predictions regarding the future price movement of the asset represented by the symbol
    $$asset_symbol$$. To do so effectively, you will rely on a comprehensive set of information and data as follows.
    """
).strip()


KLINE_CHART_DESCRIPTION = dedent(
    """
    The following is a Kline chart with Moving Average (MA) and Bollinger Bands (BB) technical indicators.
    1.Moving Average (MA) is a trend indicator that is calculated by averaging the price over a period of time. The MA is used to
    smooth out price fluctuations and highlight longer-term trends or cycles.
    2.Bollinger Bands (BB) are a technical analysis tool based on moving averages and standard deviations, which are used to
    identify overbought and oversold conditions.
     - Bollinger Band Upper (BBU): The upper band is calculated by adding 2 standard deviations to the moving average.
     - Bollinger Band Lower (BBL): The lower band is calculated by subtracting 2 standard deviations from the moving average.
     - When the bandwidth (the distance between the upper and lower bands) widens, it indicates increased market volatility; when
    it narrows, it indicates reduced volatility.
    3.The Kline chart shows the price movements of the asset over time.
     - The "horizontal axis" is the date and the "vertical axis" is the price.
     - The wider part of the candlestick, known as the "real body" represents the range between the opening and closing prices.
    Lines extending from the top and bottom of the body, also called "shadows" or "tails" indicate the high and low prices during
    the period.
     - The "GREEN" candlestick indicates that the closing price is higher than the opening price, and the "RED" candlestick
    indicates that the closing price is lower than the opening price.
     - The "BLUE" line is MA5, the "GREEN" line is BBL, the "YELLOW" line is BBU.
     - The "GREY BALLOON MARKER" is today's date.
    Kline chart image path: $$kline_path$$
    """
).strip()


PRICE_CHANGE_DESCRIPTION = dedent(
    """
    As the above Kline chart shows, today's date is $$date$$. The chart's date range is from past
    $$long_term_past_date_range$$ days to next $$long_term_next_date_range$$ days. Additionally, the price movements within this
    range can be categorized into three time horizons:
    1. Short-Term: Over the past $$short_term_past_date_range$$ days, the price movement ratio has shown
    $$short_term_past_price_movement$$, and for the next $$short_term_next_date_range$$ days, it indicates
    $$short_term_next_price_movement$$.
    2. Medium-Term: Over the past $$medium_term_past_date_range$$ days, the price movement ratio has shown
    $$medium_term_past_price_movement$$, and for the next $$medium_term_next_date_range$$ days, it indicates
    $$medium_term_next_price_movement$$.
    3. Long-Term: Over the past $$long_term_past_date_range$$ days, the price movement ratio has shown
    $$long_term_past_price_movement$$, and for the next $$long_term_next_date_range$$ days, it indicates
    $$long_term_next_price_movement$$.
    * For each price movement, you should not only focus on the starting price and ending price but also pay attention to the price
    change trends.
    """
).strip()


LOW_LEVEL_REFLECTION_EFFECTS = dedent(
    """
    Lessons learnt from analysis of price movments can be considered in the following ways:
    1. Momentum is a term used in financial market analysis to describe the tendency of asset prices to keep moving in their
    current direction over time. It is often used to predict short-term price movements based on historical trends. The basic
    premise of momentum is that securities that have performed well in the past are likely to continue performing well, while
    those that have performed poorly are likely to continue performing poorly.
    2. Identify the potential price movements patterns and characteristics of this particular asset and incorporate these insights
    into your further analysis and reflections when applicable.
    """
).strip()


LOW_LEVEL_REFLECTION_PROMPT = dedent(
    """
    Based on the above information, you should analyze the summary of market intelligence and the Kline chart on the
    reasoning that lead to past to feature price movements. Then output the results as the following constraints:

    "reasoning": This field will be used for trading decisions. You should think step-by-step and provide the detailed
    reasoning to determine how the summary of market intelligence and Kline chart that lead to the price movements. Please
    strictly follow the following constraints and output formats:
    1. There should be three fields under this field, corresponding to the three time horizons: "short_term_reasoning", "
    medium_term_reasoning", and "long_term_reasonig".
     - "short_term_reasoning": Reasoning about the price movements at the Short-Term.
     - "medium_term_reasoning": Reasoning about the price movements at the Medium-Term.
     - "long_term_reasoning": Reasoning about the price movements at the Long-Term.
    3. For the reasoning of each time horizon, you should analyze step-by-step and follow the rules as follows and do not miss any
    of them:
     - Price movements should involve a shift in trend from the past to the future.
     - You should analyze the summary of market intelligence that lead to the price movements. And you should pay MORE attention to
    the effect of latest market intelligence on price movements.
     - You should conduct a thorough analysis of the Kline chart, focusing on price changes. And provide the reasoning driving
    these price movements.
     - The reasoning you provide for each time horizon should be concise and clear, with no more than 300 tokens.

    "query": This field will be used to retrieve past reasoning for price movements, so you should step-by-step analyze and
    extract the key information that represent each piece of reasoning based on the above analysis. You need to follow the rules
    and do not miss any of them:
    1. Analyzing and summarizing reasoning of each time horizon, condensing it into a concise sentence of no more than 100 tokens
    to extract key information.
    """
).strip()


LOW_LEVEL_REFLECTION_OUTPUT_FORMAT = dedent(
    """
    You should ONLY return a valid XML object. You MUST FOLLOW the XML output format as follows:
    <output>
      <map name="reasoning">
        <string name="short_term_reasoning">Reasoning about the Short-Term price movements.</string>
        <string name="medium_term_reasoning">Reasoning about the Medium-Term price movements.</string>
        <string name="long_term_reasoning">Reasoning about the Long-Term price movements.</string>
      </map>
      <string name="query">The key sentence should be utilized to retrieve past reasoning for price movements.</string>
    </output>
    """
).strip()


TASK_DESCRIPTION_HIGH_LEVEL_REFLECTION = dedent(
    """
    You are currently targeting the trading decisions of a $$asset_type$$ known as $$asset_name$$, which is denoted
    by the symbol $$asset_symbol$$. This $$asset_type$$ is publicly traded and is listed on the $$asset_exchange$$. Its primary
    operations are within the $$asset_sector$$ sector, specifically within the $$asset_industry$$ industry. To provide you with a
    better understanding, here is a brief description of $$asset_name$$: $$asset_description$$. In this role, your objective is to
    make correct trading decisions during the trading process of the asset represented by the $$asset_symbol$$, and considering stepby-step about the decision reasoning. To do so effectively, you will rely on a comprehensive set of information as follows.
    """
).strip()


LOW_LEVEL_REFLECTION_CONTEXT = dedent(
    """
    The analysis of price movements provided by your assistant across three time horizons: Short-Term, Medium -Term, and Long-Term.

    Past analysis of price movements are as follows:
    $$past_low_level_reflection$$

    Latest analysis of price movements are as follows:
    $$latest_low_level_reflection$$
    """
).strip()


TRADING_CHART_DESCRIPTION = dedent(
    """
    The following figure showing the Adj Close price movements with trading decisions (e.g., BUY and SELL), together
    with another plot showing the cumulative returns below. The price movements of the traded asset after the trading decisions can
    be seen in the figure.
    1. The first chart is the trading chart, which shows the price movements and trading decisions of the trade over time.
     - The "horizontal axis" is the date and the "vertical axis" is the Adj Close price.
     - The "GREEN" rhombic marker indicates the "BUY" decision, the "RED" balloon marker indicates the "SELL" decision, no sign
    indicates that a "HOLD" decision is made.
    2. The second chart is the cumulative returns chart, which shows the cumulative returns of the trade over time.
     - The "horizontal axis" is the date and the "vertical axis" is the cumulative returns.
     - Cumulative return greater than 0 indicates a profit, while less than 0 signifies a loss.
    Trading chart image path: $$trading_path$$

    Trading decision and reasoing made by your assistant for the past $$previous_action_look_back_days$$ days are as follows:
    $$previous_action_and_reasoning$$
    """
).strip()


HIGH_LEVEL_REFLECTION_EFFECTS = dedent(
    """
    Lessons learnt from reflection of the past trading decisions can be considered in the following ways:
    1. Learning about the correct and wrong experiences of past trading decisions can provide guidance for subsequent decisions
    that have maximized profit.
    """
).strip()


HIGH_LEVEL_REFLECTION_PROMPT = dedent(
    """
    Based on the above information, you should think step-by-step and provide the detailed analysis and summary to
    highlight key investment insights. Then output the results as the following constraints:

    "reasoning": You should reflect on whether the decisions made at each point in time were right or wrong and give reasoning.
    You need to follow the rules and do not miss any of them:
    1. If the trading decision was right or wrong (a right trading decision would lead to an increase in return and a wrong
    decision does otherwise).
    2. Analyse the contributing factors of the success decision / mistake, considering the market intelligences, Kline chart
    analysis, technical indicators, technical signals and analysis of price movements and the weightage of each factor in the
    decision-making.

    "improvement": If there are bad decisions, are you likely to revise them and maximise the return? If so, how would you
    revise them? You need to follow the rules and do not miss any of them:
    1. Suggest improvements or corrective actions for each identified mistake/success.
    2. Detailed list of improvements (e.g., 2023-01-03: HOLD to BUY) to the trading decisions that could have been made to improve
    the return.

    "summary": Provide a summary of the lessons learnt from the success / mistakes that can be adapted to future trading
    decisions, where you can draw connections between similar scenarios and apply learnt lessons.

    "query": This field will be used to retrieve past reflection of the trading decisions, so you should step-by-step analyze
    and extract the key information that represent each piece of reasoning based on the above analysis. You need to follow the
    rules and do not miss any of them:
    1. Analyze and summarize the "summary", and condensing it into a concise sentence of no more than 1000 tokens to extract key
    information.
    """
).strip()


HIGH_LEVEL_REFLECTION_OUTPUT_FORMAT = dedent(
    """
    You should ONLY return a valid XML object. You MUST FOLLOW the XML output format as follows:
    <output>
      <string name="reasoning">Reflection about trading decision.</string>
      <string name="improvement">Improvements or corrective decisions.</string>
      <string name="summary">Analysis and summary.</string>
      <string name="query">Query for the past reflection of the trading decisions.</string>
    </output>
    """
).strip()


HIGH_LEVEL_REFLECTION_CONTEXT = dedent(
    """
    As follows are the analysis provided by your assistant about the reflection on the trading decisions you
    made during the trading processs, and evaluating if they were correct or incorrect, and considering if there are
    opportunities for optimization to achieve maximum returns.

    Past reflections on the trading decisions are as follows:
    $$past_high_level_reflection$$

    Latest reflections on the trading decisions are as follows:
    $$latest_high_level_reflection$$
    """
).strip()


TASK_DESCRIPTION_DECISION = dedent(
    """
    You are currently targeting the trading of a company known as $$asset_name$$, which is denoted by the symbol
    $$asset_symbol$$. This corporation is publicly traded and is listed on the $$asset_exchange$$. Its primary operations are within
    the $$asset_sector$$ sector, specifically within the $$asset_industry$$ industry. To provide you with a better understanding,
    here is a brief description of $$asset_name$$: $$asset_description$$. In this role, your objective is to make correct trading
    decisions during the trading process of the asset represented by the $$asset_symbol$$, and considering step by step about the
    decision reasoning. To do so effectively, you will rely on a comprehensive set of information and data as follows.
    """
).strip()


TRADER_PREFERENCE = dedent(
    """
    $$trader_preference$$
    """
).strip()


DECISION_GUIDANCE = dedent(
    """
    As follows are the professional investment guidances, including headlines, content, and market sentiment.
    $$guidance$$
    """
).strip()


DECISION_STRATEGY = dedent(
    """
    As follows are the trading strategies, including current state-based investment decisions and investment
    explanations.

    1. MACD Crossover Strategy - This strategy generates buy signals when the MACD line crosses above the signal line,
       indicative of bullish momentum, and sell signals when it crosses below, signaling bearish momentum. It's ideal for those who
       are comfortable with fast-paced market dynamics and are adept at anticipating trend changes. The strategy's reliance on trend
       continuation makes it less suitable for range-bound or choppy markets, hence appealing primarily to risk-seeking, proactive
       traders.
    $$strategy1$$

    2. KDJ with RSI Filter Strategy - This strategy works best in sideways or ranging markets, where it employs the KDJ for
       momentum signals and RSI as a filter to pinpoint potential reversals. It's designed for traders who are methodical and patient,
       preferring to wait for clear signals before executing trades. This strategy is well-suited for risk-aware traders who are
       not necessarily aggressive but are keen on capturing opportunities that arise from market inefficiencies.
    $$strategy2$$

    3. Mean Reversion Strategy - This strategy assumes that prices will revert to their mean over time, generating buy signals
       when the z-score shows significant deviation below the mean (oversold), and sell signals when it deviates above (overbought).
       It works best in stable, range-bound markets and is less effective in trending or highly volatile environments. This strategy
       caters to cautious traders who look for statistical evidence of price anomalies and prefer a more deliberative trading style,
       focusing on long-term stability over short-term gains.
    $$strategy4$$
    """
).strip()


DECISION_PROMPT = dedent(
    """
    Based on the above information, you should step-by-step analyze the summary of the market intelligence.
    And provide the reasoning for what you should to BUY, SELL or HOLD on the asset. Please strictly follow the following constraints and output
    formats:

    "analysis": You should analyze step-by-step how the above information may affect the results of your decisions.
    You need to follow the rules as follows and do not miss any of them:
    1. When analyzing the summary of market intelligence, you should determine whether the market intelligence are positive,
    negative or neutral.
     - If the overall is neurtal, your decision should pay less attention to the summary of market intelligence.
     - If the overall is positive or negative. you should give a decision result based on this.
    2. When analyzing the analysis of price movements, you should determine whether the future trend is bullish or bearish and
    reflect on the lessons you've learned.
     - If the future trend is bullish, you should consider a BUY instead of a HOLD to increase your profits.
     - If the future trend is bearish, you should consider a SELL instead of a HOLD to prevent further losses.
     - You should provide your decision result based on the analysis of price movements.
    3. When analyzing the analysis of the past trading decisions, you should reflect on the lessons you've learned.
     - If you have missed a BUY opportunity, you should BUY as soon as possible to increase your profits.
     - If you have missed a SELL, you should SELL immediately to prevent further losses.
     - You should provide your decision result based on the reflection of the past trading decisions.
    4. When analyzing the professional investment guidances, you should determine whether the guidances show the trend is bullish
    or bearish. And provide your decision results.
    5. When analyzing the decisions and explanations of some trading strategies, you should consider the results and explanations
    of their decisions together. And provide your decision results.
    6. When providing the final decision, you should pay less attention to the market intelligence whose sentiment is neutral or
    unrelated.
    7. When providing the final decision, you should pay more attention to the market intelligence which will cause an immediate
    impact on the price.
    8. When providing the final decision, if the overall market intelligence is mixed up, you should pay more attention to the
    professional investment guidances, and consider which guidance is worthy trusting based on historical price.
    9. Before making a decision, you must check the current situation. If your CASH reserve is lower than the current Adj Close
    Price, then the decision result should NOT be BUY. Similarly, the decision result should NOT be SELL if you have no existing
    POSITION.
    10. Combining the results of all the above analysis and decisions, you should determine whether the current situation is
    suitable for BUY, SELL or HOLD. And provide your final decision results.

    "reasoning": You should think step-by-step and provide the detailed reasoning to determine the decision result executed on
    the current observation for the trading task. Please strictly follow the following constraints and output formats:
    1.You should provide the reasoning for each point of the "analysis" and the final results you provide.

    "action": Based on the above information and your analysis. Please strictly follow the following constraints and output
    formats:
    1.You can only output one of BUY, HOLD and SELL.
    2.The above information may be in the opposite direction of decision-making (e.g., BUY or SELL), but you should consider stepby-step all of the above information together to give an exact BUY or SELL decision result.
    """
).strip()


DECISION_OUTPUT_FORMAT = dedent(
    """
    You should ONLY return a valid XML object. You MUST FOLLOW the XML output format as follows:
    <output>
      <string name="analysis">Analysis that you provided.</string>
      <string name="action">BUY</string>
      <string name="reasoning">Reasoning about the decision result that you provided.</string>
    </output>
    """
).strip()


__all__ = [
    "render",
    "SYSTEM_CONTENT_TRADING",
    "TASK_DESCRIPTION_MARKET_INTELLIGENCE",
    "LATEST_MARKET_INTELLIGENCE_CONTEXT",
    "PAST_MARKET_INTELLIGENCE_CONTEXT",
    "MARKET_INTELLIGENCE_SUMMARIES_CONTEXT",
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
    "LOW_LEVEL_REFLECTION_CONTEXT",
    "TRADING_CHART_DESCRIPTION",
    "HIGH_LEVEL_REFLECTION_EFFECTS",
    "HIGH_LEVEL_REFLECTION_PROMPT",
    "HIGH_LEVEL_REFLECTION_OUTPUT_FORMAT",
    "HIGH_LEVEL_REFLECTION_CONTEXT",
    "TASK_DESCRIPTION_DECISION",
    "TRADER_PREFERENCE",
    "DECISION_GUIDANCE",
    "DECISION_STRATEGY",
    "DECISION_PROMPT",
    "DECISION_OUTPUT_FORMAT",
]

