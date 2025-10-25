# LLM-Based Chart Analysis & Trading Signals - Implementation Proposal

## 🎯 Overview

This proposal introduces an AI-powered trading signal generation system that uses LLM vision models to analyze technical charts across multiple timeframes. Based on the reference workflow from `reference/workflow/IBKR_2_Indicator_4_Prod (1).json`.

## 📊 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. CHART GENERATION                                        │
│  Symbol + Timeframe → Multi-Panel Chart (7 indicators)     │
│  Daily, Weekly, Monthly charts with all technical analysis │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. LLM VISION ANALYSIS                                     │
│  Chart Images → GPT-4V/Gemini → Structured Analysis        │
│  AI reads charts like a human analyst would                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. MULTI-TIMEFRAME CONSOLIDATION                           │
│  Daily Analysis + Weekly Confirmation → Final Signal       │
│  3/4 signal confirmation system applied                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  4. TRADING SIGNAL OUTPUT                                   │
│  BUY/SELL/HOLD + Entry/Stop/Targets + Risk Assessment      │
│  R-multiples, position sizing, detailed reasoning          │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Core Components

### 1. Chart Generator Service (`backend/services/chart_generator.py`)

**Purpose**: Generate multi-timeframe technical analysis charts

**Features**:
- 7-panel Plotly charts (Price, SuperTrend, Volume, MACD, RSI, OBV, ATR)
- Support for 1d, 1w, 1mo timeframes
- Export to JPEG/PNG for LLM consumption
- Upload to MinIO with public URLs
- Based on `reference/webapp/services/chart_service.py`

**Key Methods**:
```python
class ChartGenerator:
    def generate_chart(symbol: str, timeframe: str) -> ChartResult
    def _create_plotly_figure(df, indicators) -> go.Figure
    def _export_to_image(fig) -> bytes
    def _upload_chart(image_data) -> str
```

### 2. LLM Integration Service (`backend/services/llm_service.py`)

**Purpose**: Communicate with vision-capable LLMs to analyze charts

**Features**:
- OpenAI GPT-4V integration
- Google Gemini 2.0 Flash integration
- Prompt template system (daily, weekly, consolidation)
- Response parsing into structured trading signals
- Support for English and Chinese

**Key Methods**:
```python
class LLMService:
    def analyze_chart(chart_url, prompt_template, symbol, language) -> Analysis
    def consolidate_analyses(daily, weekly) -> FinalSignal
    def _call_openai_vision(prompt, image) -> str
    def _parse_response(text) -> ParsedSignal
```

### 3. Signal Generator Service (`backend/services/signal_generator.py`)

**Purpose**: Orchestrate the complete signal generation workflow

**Features**:
- Multi-timeframe analysis workflow
- 3/4 signal confirmation system
- Entry/stop/target calculation
- R-multiple and position sizing
- Signal storage in database

**Key Methods**:
```python
class SignalGenerator:
    async def generate_signal(symbol, strategy) -> TradingSignal
    async def batch_generate(symbols) -> list[TradingSignal]
    def _extract_trading_params(analysis) -> dict
    def _calculate_r_multiples(entry, stop, targets) -> dict
```

## 📋 Database Schema

### Extended Strategy Model
```sql
ALTER TABLE strategies ADD COLUMN llm_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE strategies ADD COLUMN llm_model VARCHAR(50) DEFAULT 'gpt-4-vision';
ALTER TABLE strategies ADD COLUMN llm_language VARCHAR(5) DEFAULT 'en';
ALTER TABLE strategies ADD COLUMN timeframes JSONB DEFAULT '["1d", "1w"]';
ALTER TABLE strategies ADD COLUMN consolidate_timeframes BOOLEAN DEFAULT TRUE;
```

### New TradingSignal Model
```sql
CREATE TABLE trading_signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    strategy_id INTEGER REFERENCES strategies(id),
    signal_type VARCHAR(10) NOT NULL,  -- BUY/SELL/HOLD
    confidence FLOAT,
    
    -- Trading parameters
    entry_price_low FLOAT,
    entry_price_high FLOAT,
    stop_loss FLOAT,
    target_conservative FLOAT,
    target_aggressive FLOAT,
    r_multiple_conservative FLOAT,
    r_multiple_aggressive FLOAT,
    position_size_percent FLOAT,
    
    -- Analysis data
    confirmation_signals JSONB,
    analysis_text TEXT,
    chart_url_daily VARCHAR(500),
    chart_url_weekly VARCHAR(500),
    
    -- Metadata
    generated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    
    INDEX idx_symbol_status (symbol, status),
    INDEX idx_generated_at (generated_at DESC)
);
```

## 🌐 API Endpoints

### POST /api/signals/generate
Generate a trading signal for a symbol

**Request**:
```json
{
    "symbol": "TSLA",
    "strategy_id": 1,
    "timeframes": ["1d", "1w"],
    "force_regenerate": false
}
```

**Response**:
```json
{
    "signal_id": 123,
    "symbol": "TSLA",
    "signal_type": "BUY",
    "confidence": 0.75,
    "entry_price_low": 245.00,
    "entry_price_high": 250.00,
    "stop_loss": 235.00,
    "target_conservative": 270.00,
    "target_aggressive": 290.00,
    "r_multiple_conservative": 2.5,
    "r_multiple_aggressive": 4.0,
    "position_size_percent": 5.0,
    "confirmation": {
        "signals_confirmed": 3,
        "passed": true,
        "supertrend": "bullish",
        "price_vs_ma20": "above",
        "macd": "buy",
        "rsi": "bullish"
    },
    "charts": {
        "daily_url": "http://localhost:9000/trading-charts/signals/TSLA_1d_20251024.jpg",
        "weekly_url": "http://localhost:9000/trading-charts/signals/TSLA_1w_20251024.jpg"
    },
    "analysis": {
        "daily": "...(full LLM analysis text)...",
        "weekly": "...(weekly trend confirmation)...",
        "consolidated": "...(final recommendation)..."
    },
    "generated_at": "2025-10-24T10:30:00Z",
    "model_used": "gpt-4-vision"
}
```

### POST /api/signals/batch
Generate signals for multiple symbols

### GET /api/signals/{symbol}
Get latest active signal for a symbol

### GET /api/signals/history
Query signal history with filters

## 📝 Prompt Templates

Based on `reference/workflow/IBKR_2_Indicator_4_Prod (1).json`:

### Daily Chart Analysis Prompt
```
Analysis Date: {{now}}

# Daily Chart Analysis

## 1. Core Price Analysis
- Current price and trend overview
- Key support/resistance levels
- Important candlestick patterns
- Price structure

## 2. Trend Indicator Analysis
A. SuperTrend (10,3):
   - Current status: [uptrend/downtrend]
   - Signal color: [green/red]
   - Relative position to price

B. Moving Average System:
   - 20-day SMA: short-term trend
   - 50-day SMA: medium-term trend
   - 200-day SMA: long-term trend
   - Golden/Death cross situations
   - Price-MA relationships

## 3. Confirmation Indicator Analysis
A. Momentum Confirmation:
   - MACD (12,26,9) status and signals
   - RSI (14) level and direction [overbought/oversold/neutral]

B. Volatility Analysis:
   - ATR (14) value and trend
   - Bollinger Bands (20,2) width and price position

C. Volume Analysis:
   - Current volume vs. 20-day average
   - Volume trend characteristics
   - OBV trend and price confirmation

## 4. 3/4 Signal Confirmation System
At least 3 of the following 4 signals must confirm:
- SuperTrend direction [bullish/bearish]
- Price vs 20-day SMA [above/below]
- MACD signal line cross [buy/sell]
- RSI relative position [>50 bullish/<50 bearish]

## 5. Trading Recommendation
- Overall trend: [Strong Bullish/Bullish/Neutral/Bearish/Strong Bearish]
- Trade signal: [BUY/HOLD/SELL]

If Bullish:
- Entry range: [price range]
- Stop loss: Entry - (2 × ATR), approximately [value]
- Profit targets:
  * Conservative: [value] - Based on [support/resistance/pattern/indicator]
  * Aggressive: [value] - Based on [support/resistance/pattern/indicator]
- R-multiples: (Target - Entry) ÷ (Entry - Stop) = ?R

If Bearish:
- Entry range: [price range]
- Stop loss: Entry + (2 × ATR), approximately [value]
- Profit targets:
  * Conservative: [value] - Based on [technical basis]
  * Aggressive: [value] - Based on [technical basis]
- R-multiples: (Entry - Target) ÷ (Stop - Entry) = ?R

- Recommended position size: [%]

## 6. Risk Assessment
- Main technical risks
- Key reversal prices
- Potential signal failure scenarios
- Weekly chart confirmation status
```

## 🎨 Frontend UI (`frontend/templates/signals.html`)

### Features:
- Signal generation form (symbol input)
- Multi-chart display (daily + weekly side-by-side)
- LLM analysis results viewer
- Trading recommendation cards:
  - Entry zones (highlighted)
  - Stop loss (red)
  - Targets (green)
  - R-multiples displayed
- Signal confirmation indicator (3/4 rule)
- Signal history table
- Export/share functionality

### Layout:
```
┌─────────────────────────────────────────────────┐
│  Generate Signal Form                           │
│  [Symbol: TSLA] [Generate Signal]              │
└─────────────────────────────────────────────────┘

┌──────────────────┬──────────────────┐
│  Daily Chart     │  Weekly Chart    │
│  (7 panels)      │  (7 panels)      │
│                  │                  │
└──────────────────┴──────────────────┘

┌─────────────────────────────────────────────────┐
│  Signal Summary                                 │
│  ⬆️ BUY Signal - Confidence: 75%                │
│  3/4 Signals Confirmed ✓                       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Trade Parameters                               │
│  Entry: $245-250  │  Stop: $235  │  R: 2.5R    │
│  Conservative Target: $270  │  Aggressive: $290 │
│  Position Size: 5%                              │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  LLM Analysis (Expandable)                      │
│  Daily: ...                                     │
│  Weekly: ...                                    │
│  Consolidated: ...                              │
└─────────────────────────────────────────────────┘
```

## ⚙️ Configuration

### Environment Variables
```env
# LLM Configuration
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
LLM_DEFAULT_MODEL=gpt-4-vision
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.1
LLM_TIMEOUT_SECONDS=60

# Chart Generation
CHART_WIDTH=1920
CHART_HEIGHT=1400
CHART_DPI=150
```

### Strategy Configuration
```python
{
    "name": "LLM Daily+Weekly Strategy",
    "llm_enabled": true,
    "llm_model": "gpt-4-vision",
    "llm_language": "en",
    "timeframes": ["1d", "1w"],
    "consolidate_timeframes": true,
    "symbols": ["TSLA", "NVDA", "AAPL"],
    "prompt_customization": "Focus on momentum and volume"
}
```

## 📊 Example Workflow

1. **User Action**: Enter "TSLA" and click "Generate Signal"

2. **Backend Process**:
   ```
   a. Fetch TSLA data from IBKR
   b. Generate daily chart (1d, 200 bars)
   c. Generate weekly chart (1w, 52 bars)
   d. Upload charts to MinIO
   e. Call GPT-4V to analyze daily chart
   f. Call GPT-4V to analyze weekly chart
   g. Call GPT-4V to consolidate analyses
   h. Parse LLM responses into structured signal
   i. Save signal to database
   j. Return signal with charts and analysis
   ```

3. **Frontend Display**:
   - Show both charts side-by-side
   - Display signal summary (BUY/SELL/HOLD)
   - Show 3/4 confirmation status
   - Display entry/stop/targets
   - Show full LLM analysis text
   - Provide export/share options

## 💰 Cost Estimate

### LLM API Costs (approx.):
- GPT-4-Vision: ~$0.01-0.03 per chart analysis
- Gemini 2.0 Flash: ~$0.001-0.005 per chart analysis

Per signal generation:
- 2 charts (daily + weekly): ~$0.02-0.06 with GPT-4V
- 1 consolidation: ~$0.005-0.01
- **Total per signal: ~$0.025-0.07**

For 100 symbols daily: ~$2.50-$7.00/day

## ✅ Benefits

1. **AI-Powered Analysis**: Leverage advanced LLM vision models
2. **Multi-Timeframe Confirmation**: Daily + Weekly trend alignment
3. **Structured Signals**: Consistent BUY/SELL/HOLD with parameters
4. **Risk Management**: Automatic R-multiple and position sizing
5. **Scalable**: Batch process multiple symbols
6. **Auditable**: Full LLM analysis text stored
7. **Visual**: Charts generated for every signal

## 🚀 Implementation Plan

### Phase 1: Chart Generation (Days 1-2)
- [ ] Create `ChartGenerator` service
- [ ] Implement 7-panel Plotly charts
- [ ] Add multi-timeframe support
- [ ] Test chart export and MinIO upload

### Phase 2: LLM Integration (Days 3-4)
- [ ] Create `LLMService`
- [ ] Implement OpenAI vision client
- [ ] Create prompt templates
- [ ] Test response parsing

### Phase 3: Signal Generation (Days 5-6)
- [ ] Create `SignalGenerator` service
- [ ] Implement multi-timeframe workflow
- [ ] Add signal extraction logic
- [ ] Create database models

### Phase 4: API & Frontend (Days 7-8)
- [ ] Create `/api/signals` endpoints
- [ ] Build signal generation UI
- [ ] Add signal history view
- [ ] Test end-to-end workflow

### Phase 5: Testing & Optimization (Days 9-10)
- [ ] Test with real symbols
- [ ] Optimize LLM prompts
- [ ] Add error handling
- [ ] Performance tuning

## 📚 Documentation

- **API Docs**: Detailed in `openspec/changes/llm-chart-signals/specs/`
- **User Guide**: To be created after implementation
- **Prompt Engineering Guide**: Best practices for prompt customization
- **Cost Optimization**: Tips for reducing LLM API costs

## 🔒 Security Considerations

- API keys stored securely in environment variables
- Chart URLs use public MinIO endpoint but with unique filenames
- LLM analysis text sanitized before storage
- Rate limiting on signal generation endpoints
- User authentication required for signal access

---

**Status**: ✅ OpenSpec Validated  
**Ready for**: Implementation  
**Estimated Effort**: 10 days  
**Dependencies**: OpenAI API key or Gemini API key

