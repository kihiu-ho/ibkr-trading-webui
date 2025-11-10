## Why

The current chart generation uses matplotlib/mplfinance which produces simpler charts. The reference implementation in `reference/webapp/app.py` uses Plotly with stock_indicators library to generate more comprehensive technical analysis charts with 7 subplots (Price, SuperTrend, Volume, MACD, RSI, OBV, ATR) that provide better visual analysis for LLM interpretation.

Additionally, the current LLM prompt is basic and doesn't follow the structured analysis framework used in production workflows. The reference workflow (`IBKR_2_Indicator_4_Prod (1).json`) contains a comprehensive prompt structure that guides the LLM through systematic technical analysis including price analysis, trend indicators, confirmation signals, trading recommendations with R-multiple calculations, and risk assessment. The reference prompts are in Traditional Chinese and need to be translated to English for consistency.

## What Changes

- **MODIFIED**: Chart generation in `dags/utils/chart_generator.py` to use Plotly-based `generate_technical_chart` approach from `reference/webapp/app.py`
  - Replace matplotlib/mplfinance with Plotly
  - Add stock_indicators library integration for indicator calculations
  - Implement `create_plotly_figure` function with 7 subplots:
    1. Price chart with candlesticks, SMAs (20, 50, 200), and Bollinger Bands
    2. SuperTrend indicator (up/down signals)
    3. Volume chart with color-coded bars
    4. MACD (line, signal, histogram with color coding)
    5. RSI with overbought (70) and oversold (30) levels
    6. OBV (On-Balance Volume) with normalized values
    7. ATR (Average True Range)
  - Include max/min/average/median annotations for each indicator panel
  - Add latest value markers on secondary y-axis for each panel
  - Export as JPEG images using `plotly.io.write_image` for LLM analysis
  - Support configurable width and height parameters

- **MODIFIED**: LLM prompt in `dags/utils/llm_signal_analyzer.py` to match reference workflow structure
  - Translate Traditional Chinese prompts from reference JSON to English
  - Implement structured analysis framework matching reference workflow:
    1. **Core Price Analysis**: Current price and trend overview, key support/resistance levels, important candlestick patterns and price structure
    2. **Trend Indicator Analysis**:
       - SuperTrend (10,3): Current state (uptrend/downtrend), signal color, relative position to price
       - Moving Average System: 20-day, 50-day, 200-day SMA trends, golden/death cross situations, price-EMA relationships
    3. **Confirmation Indicator Analysis**:
       - Momentum: MACD (12,26,9) status and signals, RSI (14) levels and direction (overbought/oversold/neutral)
       - Volatility: ATR (14) values and trends, Bollinger Bands (20,2) width and price position
       - Volume: Current volume vs 20-day average, volume trend characteristics, OBV trends and price confirmation
    4. **Signal Confirmation System (3/4 Rule)**: At least 3 of 4 signals must confirm:
       - SuperTrend signal direction (bullish/bearish)
       - Price relationship to 20-day SMA (above/below)
       - MACD signal line crossover (buy/sell)
       - RSI relative position (>50 bullish/<50 bearish)
    5. **Trading Recommendations**:
       - Overall trend judgment (strongly bullish/bullish/neutral/bearish/strongly bearish)
       - Trading signal (entry/hold/exit)
       - Entry price range
       - Stop loss: Entry price ± (2 × ATR)
       - Profit targets with technical basis (support/resistance, chart patterns, Fibonacci levels, Bollinger Bands, moving averages, volume targets, ATR projections)
       - R-multiple calculation: (Target - Entry) ÷ (Entry - Stop Loss)
       - Suggested position size (% based on fixed risk management)
    6. **Risk Assessment**: Main technical risks, key reversal prices, potential signal failure scenarios, weekly chart confirmation
  - Add target price setting reference framework covering:
    - Previous support/resistance levels
    - Chart pattern projections
    - Fibonacci levels (extensions 127.2%, 161.8% or retracements 38.2%, 50%, 61.8%)
    - Bollinger Band targets
    - Moving average targets
    - Volume targets
    - Volatility projections based on ATR (e.g., 3×ATR)
  - Ensure all prompts are in English (remove Traditional Chinese instructions)
  - Update prompt to focus on medium-term trading (30-180 days holding period)
  - Add separate prompts for daily chart analysis and weekly chart confirmation

- **ADDED**: Dependencies for Plotly and stock_indicators in `Dockerfile.airflow`
  - `plotly>=5.17.0` for chart generation
  - `kaleido>=0.2.1` for image export (required by plotly.io.write_image)
  - `stock-indicators>=0.8.0` for technical indicator calculations

- **ADDED**: Helper functions from reference implementation
  - `calculate_obv()` function for On-Balance Volume calculation
  - `process_indicators()` function to normalize and format indicator data
  - `normalize_value()` function for OBV unit conversion (B/M)

## Impact

- Affected specs: `specs/llm-integration/spec.md`
- Affected code:
  - `dags/utils/chart_generator.py` - Complete rewrite of chart generation logic
  - `dags/utils/llm_signal_analyzer.py` - LLM prompt structure and analysis framework
  - `Dockerfile.airflow` - New dependencies (plotly, kaleido, stock-indicators)
  - `dags/ibkr_stock_data_workflow.py` - May need updates for chart generation calls
  - `dags/ibkr_trading_signal_workflow.py` - May need updates for chart generation calls
  - `dags/ibkr_multi_symbol_workflow.py` - May need updates for chart generation calls
- Breaking changes: Chart output format changes from PNG to JPEG, chart structure changes from matplotlib to Plotly

