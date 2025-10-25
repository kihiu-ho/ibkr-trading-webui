# LLM-Based Chart Analysis & Trading Signals

## Why
Currently, the system generates technical analysis using rule-based algorithms. However, the reference workflow shows a more advanced approach:
- Multi-timeframe chart analysis (daily, weekly, monthly)
- LLM vision models analyze chart images directly
- Sophisticated prompts guide the LLM to generate trading signals
- Consolidates analyses across timeframes for final recommendations

Users need:
- AI-powered visual chart analysis using LLMs
- Multi-timeframe confirmation (daily + weekly)
- Integration with existing strategy system
- Automated signal generation based on chart patterns

## What Changes
1. **Multi-Timeframe Chart Generation:**
   - Implement `create_plotly_figure()` based on reference/webapp/services/chart_service.py
   - Generate charts for daily, weekly, and monthly timeframes
   - Export charts as images (JPEG/PNG) for LLM consumption
   - Store chart URLs in strategy configuration

2. **LLM Integration Service:**
   - New service to communicate with OpenAI/Gemini vision models
   - Pass chart images to LLM with structured prompts
   - Parse LLM responses into structured trading signals
   - Support for both English and Chinese prompts

3. **Trading Signal Generation:**
   - Implement daily chart analysis using reference prompts
   - Implement weekly chart analysis for trend confirmation
   - Consolidate multi-timeframe analyses
   - Generate final trading recommendations with:
     - Entry/exit signals (BUY/SELL/HOLD)
     - Entry price zones
     - Stop loss levels
     - Target prices (conservative & aggressive)
     - R-multiples and position sizing

4. **Strategy Integration:**
   - Extend Strategy model with LLM configuration
   - Add timeframe settings (daily, weekly, monthly)
   - Store LLM prompts and model settings
   - Link strategies to generated signals

## Impact
- **Affected specs:** chart-generation (new), llm-integration (new), strategy-integration (modified)
- **Affected code:**
  - New: `backend/services/chart_generator.py` - Multi-timeframe chart creation
  - New: `backend/services/llm_service.py` - LLM integration for vision analysis
  - New: `backend/services/signal_generator.py` - Trading signal generation
  - New: `backend/api/signals.py` - Signal generation endpoints
  - Modified: `backend/models/strategy.py` - Add LLM config fields
  - Modified: `backend/schemas/strategy.py` - LLM configuration schemas
  - New: `frontend/templates/signals.html` - Signal generation UI
- **User impact:** AI-powered trading signals from visual chart analysis
- **Breaking changes:** None - additive feature
- **Dependencies:** OpenAI API or compatible LLM with vision capabilities (Gemini, GPT-4V, etc.)

## Reference
- Workflow: `reference/workflow/IBKR_2_Indicator_4_Prod (1).json`
- Chart Service: `reference/webapp/services/chart_service.py`

