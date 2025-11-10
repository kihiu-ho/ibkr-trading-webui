## 1. Implementation

- [ ] 1.1 Add Plotly, kaleido, and stock_indicators dependencies to Dockerfile.airflow
- [ ] 1.2 Port helper functions from reference/webapp/app.py:
  - [ ] 1.2.1 Port `calculate_obv()` function
  - [ ] 1.2.2 Port `normalize_value()` function
  - [ ] 1.2.3 Port `process_indicators()` function
- [ ] 1.3 Port `create_plotly_figure()` function from reference with 7 subplots
- [ ] 1.4 Port `generate_technical_chart()` function using stock_indicators library
- [ ] 1.5 Update ChartGenerator class to use Plotly-based generation:
  - [ ] 1.5.1 Replace matplotlib/mplfinance imports with Plotly
  - [ ] 1.5.2 Update `generate_chart()` method to use new Plotly implementation
  - [ ] 1.5.3 Update `calculate_indicators()` to use stock_indicators library
  - [ ] 1.5.4 Ensure chart export format is JPEG (not PNG)
- [ ] 1.6 Translate LLM prompts from Traditional Chinese to English:
  - [ ] 1.6.1 Translate daily chart analysis prompt
  - [ ] 1.6.2 Translate weekly chart analysis prompt
  - [ ] 1.6.3 Translate consolidation prompt
  - [ ] 1.6.4 Remove all Traditional Chinese instructions
- [ ] 1.7 Update LLM analyzer to use new prompt structure:
  - [ ] 1.7.1 Update ANALYSIS_PROMPT constant with structured framework
  - [ ] 1.7.2 Ensure prompt includes all 6 sections (price, trends, confirmation, signals, recommendations, risk)
  - [ ] 1.7.3 Add target price setting reference framework
  - [ ] 1.7.4 Update prompt to focus on medium-term trading (30-180 days)
- [ ] 1.8 Verify all LLM prompts are in English (no Chinese text)
- [ ] 1.9 Test chart generation with new Plotly implementation
- [ ] 1.10 Test LLM analysis with new prompt
- [ ] 1.11 Verify charts are correctly uploaded to MinIO
- [ ] 1.12 Verify LLM analysis produces structured responses matching new format

## 2. Testing

- [ ] 2.1 Run IBKR workflow and verify charts are generated correctly
- [ ] 2.2 Verify chart images contain all 7 panels (Price, SuperTrend, Volume, MACD, RSI, OBV, ATR)
- [ ] 2.3 Verify each panel has max/min/average/median annotations
- [ ] 2.4 Verify each panel has latest value markers on secondary y-axis
- [ ] 2.5 Verify chart format is JPEG (not PNG)
- [ ] 2.6 Verify LLM analysis follows new prompt structure
- [ ] 2.7 Verify LLM responses include all required sections:
  - [ ] 2.7.1 Core price analysis
  - [ ] 2.7.2 Trend indicator analysis (SuperTrend, SMAs)
  - [ ] 2.7.3 Confirmation indicator analysis (MACD, RSI, ATR, Bollinger Bands, Volume, OBV)
  - [ ] 2.7.4 Signal confirmation system (3/4 rule)
  - [ ] 2.7.5 Trading recommendations with R-multiple calculations
  - [ ] 2.7.6 Risk assessment
- [ ] 2.8 Verify LLM responses are in English (no Chinese text)
- [ ] 2.9 Test with multiple symbols (TSLA, NVDA)
- [ ] 2.10 Test with both daily and weekly timeframes
- [ ] 2.11 Verify R-multiple calculations are correct
- [ ] 2.12 Verify target prices include technical basis explanations

## 3. Documentation

- [ ] 3.1 Update any relevant documentation about chart generation
- [ ] 3.2 Document new LLM prompt structure and framework
- [ ] 3.3 Document new dependencies (plotly, kaleido, stock-indicators)
- [ ] 3.4 Update README if chart generation process changed significantly

