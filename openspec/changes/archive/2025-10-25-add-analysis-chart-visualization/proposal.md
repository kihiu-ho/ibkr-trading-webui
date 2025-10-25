# Add Interactive Chart Visualization to Technical Analysis

## Why
The current technical analysis page provides comprehensive text-based analysis reports but lacks visual chart representation. Users need to:
- See visual confirmation of the indicators analyzed
- Understand price action and indicator relationships at a glance
- View multiple indicator subplots (7 panels as per reference implementation)
- Have interactive Plotly charts for zooming and exploration

The reference implementation in `reference/webapp/services/chart_service.py` demonstrates a proven 7-panel chart layout that effectively displays:
1. Price with SMA (20, 50, 200) and Bollinger Bands
2. SuperTrend indicator
3. Volume
4. MACD
5. RSI
6. OBV (On-Balance Volume)
7. ATR (Average True Range)

## What Changes
- Add interactive chart generation to analysis page using existing `ChartService`
- Display Plotly chart alongside analysis report
- Show the same indicators that are analyzed in the text report
- Add chart download capability (PNG/JPEG)
- Reference the 7-panel layout from `reference/webapp/services/chart_service.py`
- Enhance analysis response to include chart URLs

## Impact
- **Affected specs:** technical-analysis (enhancement)
- **Affected code:**
  - Modified: `backend/api/analysis.py` - Add chart generation after analysis
  - Modified: `backend/schemas/analysis.py` - Add chart_url fields
  - Modified: `frontend/templates/analysis.html` - Display interactive chart
  - Reference: `reference/webapp/services/chart_service.py` - Chart layout inspiration
- **User impact:** Visual charts complement text analysis, better trading decisions
- **Breaking changes:** None - purely additive enhancement

## Reference Implementation

The chart layout from `reference/webapp/services/chart_service.py::generate_technical_chart` provides:
- 7 subplots with optimal row heights: [0.35, 0.15, 0.1, 0.15, 0.15, 0.1, 0.1]
- Max/Min/Avg/Median annotations for each indicator
- Latest value markers with yellow dots
- Proper color coding (green=bullish, red=bearish)
- Interactive Plotly features (zoom, pan, hover)
- Professional layout with shared X-axis

This proven layout will be referenced for consistency and best practices.

