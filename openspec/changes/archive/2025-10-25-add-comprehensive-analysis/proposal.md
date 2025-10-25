# Add Comprehensive Technical Analysis System

## Why
Currently, the system has individual technical indicators (SuperTrend, MACD, RSI, ATR, Bollinger Bands, Moving Averages, OBV) but lacks a comprehensive analysis framework that:
- Combines multiple indicators for signal confirmation (3/4 rule)
- Provides structured trade recommendations with entry/exit/stop-loss calculations
- Generates detailed analysis reports in Chinese
- Calculates risk-reward ratios (R-multiples)
- Provides multi-timeframe analysis (daily + weekly confirmation)

Traders need a systematic approach that synthesizes all indicators into actionable insights with clear risk management guidelines.

## What Changes
- Add Technical Analysis Service to synthesize indicator data into comprehensive analysis
- Implement 3/4 Signal Confirmation System (require 3 out of 4 signals to confirm trades)
- Add Analysis Report Generation endpoint with structured Chinese template
- Add Trade Recommendation Calculator (entry zones, stop-loss, take-profit targets)
- Add Risk-Reward Ratio Calculator (R-multiples)
- Add Multi-Timeframe Analysis support (daily + weekly)
- Add Target Price Calculation with technical justification (support/resistance, Fibonacci, chart patterns, etc.)
- Add frontend UI for displaying comprehensive analysis reports

## Impact
- **Affected specs:** New capability - `technical-analysis`
- **Affected code:**
  - New: `backend/services/analysis_service.py` - Core analysis logic
  - New: `backend/api/analysis.py` - Analysis API endpoints
  - New: `backend/schemas/analysis.py` - Analysis request/response models
  - Modified: `backend/main.py` - Register analysis router
  - New: `frontend/templates/analysis.html` - Analysis display page
  - Modified: `frontend/templates/partials/sidebar.html` - Add analysis menu item
- **User impact:** Traders get professional-grade analysis with clear trade recommendations
- **Breaking changes:** None - purely additive feature

## Implementation Strategy
1. Build analysis service with indicator synthesis
2. Implement signal confirmation logic (3/4 rule)
3. Add trade calculation engine (entry, stop-loss, targets, R-multiples)
4. Create API endpoints for generating analysis
5. Build frontend UI for displaying reports
6. Add OBV indicator template (currently calculated but not exposed as template)
7. Test with multiple symbols and timeframes

