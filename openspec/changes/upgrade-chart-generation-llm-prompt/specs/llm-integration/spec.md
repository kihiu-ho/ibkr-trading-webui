## MODIFIED Requirements

### Requirement: Chart Generation for LLM Analysis
The system SHALL generate comprehensive technical analysis charts using Plotly with 7 subplots for LLM analysis.

The chart generation SHALL:
- Use Plotly library for chart rendering
- Use stock_indicators library for technical indicator calculations
- Generate charts with 7 panels:
  1. Price chart with candlesticks, SMAs (20, 50, 200), and Bollinger Bands (upper, middle, lower)
  2. SuperTrend indicator showing up/down signals with color coding
  3. Volume chart with color-coded bars (green for up days, red for down days)
  4. MACD (line, signal, histogram with color coding based on momentum)
  5. RSI with overbought (70) and oversold (30) levels and shaded neutral zone
  6. OBV (On-Balance Volume) with normalized values and appropriate units (B/M)
  7. ATR (Average True Range) for volatility measurement
- Include max/min/average/median annotations for each indicator panel
- Include latest value markers on secondary y-axis for each panel
- Export charts as JPEG images using plotly.io.write_image for LLM vision analysis
- Support configurable width and height parameters
- Support both daily and weekly timeframes

#### Scenario: Generate daily chart with all indicators
- **WHEN** chart generation is requested for a symbol with daily timeframe
- **THEN** a Plotly chart is generated with 7 subplots containing price, SuperTrend, volume, MACD, RSI, OBV, and ATR
- **AND** each panel includes max/min/average/median annotations
- **AND** each panel includes latest value markers on secondary y-axis
- **AND** the chart is saved as a JPEG image file (not PNG)
- **AND** the chart file path is returned for LLM analysis

#### Scenario: Generate weekly chart with all indicators
- **WHEN** chart generation is requested for a symbol with weekly timeframe
- **THEN** a Plotly chart is generated with 7 subplots containing price, SuperTrend, volume, MACD, RSI, OBV, and ATR
- **AND** each panel includes max/min/average/median annotations
- **AND** each panel includes latest value markers on secondary y-axis
- **AND** the chart is saved as a JPEG image file (not PNG)
- **AND** the chart file path is returned for LLM analysis

### Requirement: LLM Trading Signal Analysis
The system SHALL use a structured English prompt framework for LLM-based trading signal analysis.

The LLM analysis SHALL follow this structured framework:
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

The LLM prompt SHALL be in English (all Traditional Chinese text SHALL be removed) and SHALL include target price setting reference framework covering:
- Previous support/resistance levels (historical highs/lows, trading dense areas)
- Chart pattern projections (head and shoulders, triangles, flags, wedges, etc.)
- Fibonacci levels (extensions: 127.2%, 161.8% or retracements: 38.2%, 50%, 61.8%)
- Bollinger Band targets (upper/lower bands or width projections)
- Moving average targets (important EMA/SMA positions or crossover points)
- Volume targets (volume distribution peaks, volume force field highs/lows)
- Volatility projections based on ATR (e.g., 3×ATR volatility range)

The LLM prompt SHALL focus on medium-term trading opportunities (30-180 days holding period) and SHALL provide separate analysis frameworks for daily chart (primary) and weekly chart (confirmation).

#### Scenario: LLM analyzes daily and weekly charts
- **WHEN** LLM analysis is requested with daily and weekly chart images
- **THEN** the LLM receives a structured English prompt following the 6-section framework
- **AND** the prompt contains no Traditional Chinese text
- **AND** the prompt focuses on medium-term trading (30-180 days holding period)
- **AND** the LLM analyzes both charts according to the framework
- **AND** the response includes all required sections: price analysis, trend indicators, confirmation indicators, signal confirmation, trading recommendations with R-multiples, and risk assessment
- **AND** the response is in English

#### Scenario: LLM provides trading recommendation with R-multiple
- **WHEN** LLM analysis identifies a trading opportunity
- **THEN** the response includes entry price, stop loss (calculated as Entry ± 2×ATR), and take profit targets
- **AND** the response includes R-multiple calculation: (Target - Entry) ÷ (Entry - Stop Loss)
- **AND** each target price includes technical basis (support/resistance, chart patterns, Fibonacci, etc.)

