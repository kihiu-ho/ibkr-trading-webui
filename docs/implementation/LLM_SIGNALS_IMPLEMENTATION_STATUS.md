# LLM Chart Signals - Implementation Status

## ✅ COMPLETED (Phase 1 & 2)

### 1. Configuration ✓
- **File**: `backend/config/settings.py`
- Added comprehensive LLM configuration:
  - `LLM_VISION_PROVIDER`: "openai" or "gemini"
  - `LLM_VISION_MODEL`: Model selection
  - `LLM_VISION_MAX_TOKENS`, `LLM_VISION_TEMPERATURE`, `LLM_VISION_TIMEOUT`
  - `GEMINI_API_KEY`: Alternative to OpenAI
  - `LLM_DEFAULT_LANGUAGE`: "en" or "zh"
  - Retry settings for resilience

### 2. Chart Generation Service ✓
- **File**: `backend/services/chart_generator.py`
- **Features Implemented**:
  - ✅ Multi-timeframe support (1d, 1w, 1mo)
  - ✅ 7-panel Plotly charts:
    1. Price with MA (20, 50, 200) & Bollinger Bands
    2. SuperTrend indicator
    3. Volume (millions)
    4. MACD with histogram
    5. RSI with 30/70 levels
    6. OBV (On-Balance Volume)
    7. ATR (Average True Range)
  - ✅ All indicator calculations (SMA, EMA, BB, SuperTrend, MACD, RSI, ATR, OBV)
  - ✅ JPEG export via Kaleido
  - ✅ MinIO upload with public URLs
  - ✅ Interactive HTML export
  - ✅ Based on `reference/webapp/services/chart_service.py`

### 3. LLM Integration Service ✓
- **File**: `backend/services/llm_service.py`
- **Features Implemented**:
  - ✅ OpenAI GPT-4-Vision integration
  - ✅ Image download and base64 encoding
  - ✅ Prompt template system:
    - Daily chart analysis prompt (English)
    - Weekly chart analysis prompt (English)
    - Consolidation prompt (English)
  - ✅ Response parsing into structured signals
  - ✅ Based on `reference/workflow/IBKR_2_Indicator_4_Prod (1).json` prompts
  - ⏳ Gemini integration placeholder (TODO)

### 4. OpenSpec Documentation ✓
- **Directory**: `openspec/changes/llm-chart-signals/`
- ✅ proposal.md - Validated
- ✅ tasks.md - Implementation checklist
- ✅ specs/chart-generation/spec.md
- ✅ specs/llm-integration/spec.md
- ✅ specs/strategy-integration/spec.md
- ✅ All validated with `openspec validate --strict`

---

## ⏳ REMAINING IMPLEMENTATION (Phase 3-5)

### 5. Signal Generator Service (TODO)
- **File**: `backend/services/signal_generator.py` (not created yet)
- **Needs**:
  - Orchestrate multi-timeframe workflow
  - Call chart generator for daily + weekly
  - Call LLM service for each chart
  - Consolidate analyses
  - Extract trading parameters
  - Calculate R-multiples
  - Store signals in database

### 6. Database Models (TODO)
- **Files**: 
  - `backend/models/strategy.py` - Extend with LLM config
  - `backend/models/trading_signal.py` - New model (not created yet)
- **Needs**:
  - Add LLM fields to Strategy model
  - Create TradingSignal model
  - Migration script

### 7. API Endpoints (TODO)
- **File**: `backend/api/signals.py` (not created yet)
- **Endpoints**:
  - POST /api/signals/generate
  - POST /api/signals/batch
  - GET /api/signals/{symbol}
  - GET /api/signals/history

### 8. Frontend UI (TODO)
- **File**: `frontend/templates/signals.html` (not created yet)
- **Needs**:
  - Signal generation form
  - Multi-chart display
  - Signal summary cards
  - Trade recommendation UI
  - Signal history table

### 9. Testing (TODO)
- Unit tests for services
- Integration tests for workflow
- End-to-end signal generation test
- LLM response validation

---

## 🚀 QUICK START (With Current Implementation)

### Prerequisites
1. **Install Dependencies**:
```bash
pip install plotly kaleido httpx
```

2. **Set Environment Variables**:
```bash
export OPENAI_API_KEY="sk-your-key-here"
export LLM_VISION_MODEL="gpt-4-vision-preview"
export LLM_VISION_PROVIDER="openai"
```

3. **Ensure Services Running**:
- PostgreSQL
- MinIO
- IBKR Gateway (for market data)

### Test Chart Generation

```python
import asyncio
from backend.services.chart_generator import ChartGenerator

async def test_chart():
    generator = ChartGenerator()
    
    # Generate daily chart
    result = await generator.generate_chart(
        symbol="TSLA",
        timeframe="1d",
        period=200
    )
    
    print(f"Chart generated: {result['chart_url_jpeg']}")
    print(f"Data points: {result['data_points']}")
    print(f"Latest price: ${result['latest_price']:.2f}")

asyncio.run(test_chart())
```

### Test LLM Analysis

```python
import asyncio
from backend.services.llm_service import LLMService

async def test_llm():
    llm = LLMService()
    
    # Analyze a chart
    result = await llm.analyze_chart(
        chart_url="http://localhost:9000/trading-charts/signals/TSLA_1d_20251024.jpg",
        prompt_template="daily",
        symbol="TSLA",
        language="en"
    )
    
    print(f"Analysis complete!")
    print(f"Signal: {result['parsed_signal']['signal']}")
    print(f"Trend: {result['parsed_signal']['trend']}")
    print(f"\nFull analysis:\n{result['raw_text'][:500]}...")

asyncio.run(test_llm())
```

---

## 📋 NEXT STEPS TO COMPLETE SYSTEM

### Step 1: Create Signal Generator Service
```bash
# Create the orchestration service
touch backend/services/signal_generator.py
```

Implement the workflow to:
1. Generate daily chart
2. Generate weekly chart
3. Analyze both with LLM
4. Consolidate results
5. Return structured signal

### Step 2: Extend Database Models
```bash
# Create migration
alembic revision --autogenerate -m "add_llm_signals"
```

Add to Strategy:
- llm_enabled
- llm_model
- llm_language
- timeframes
- consolidate_timeframes

Create TradingSignal model with all fields from spec.

### Step 3: Create API Endpoints
```bash
# Create API router
touch backend/api/signals.py
```

Implement the 4 main endpoints.

### Step 4: Build Frontend
```bash
# Create UI page
touch frontend/templates/signals.html
```

Create the signal generation interface.

### Step 5: Test End-to-End
```bash
# Create test script
touch tests/test_signal_generation.py
```

Test complete flow:
- Symbol → Charts → LLM Analysis → Signal → Display

---

## ⚠️ IMPORTANT NOTES

### API Key Required
The system **requires** an OpenAI API key with GPT-4-Vision access:
- Set `OPENAI_API_KEY` environment variable
- Model: `gpt-4-vision-preview`
- Cost: ~$0.03-0.07 per signal

### Dependencies
```bash
pip install plotly kaleido httpx openai
```

### Kaleido for Chart Export
If chart export fails:
```bash
pip install kaleido
# or
conda install -c conda-forge python-kaleido
```

### Chart URLs Must Be Accessible
- LLM needs to download the chart image
- Ensure MinIO public endpoint is correct
- Test URLs are accessible: `curl <chart_url>`

---

## 🎯 ESTIMATED COMPLETION

- ✅ **Phase 1 (Configuration)**: DONE
- ✅ **Phase 2 (Chart + LLM Services)**: DONE
- ⏳ **Phase 3 (Signal Generator)**: 1-2 days
- ⏳ **Phase 4 (Database + API)**: 2-3 days
- ⏳ **Phase 5 (Frontend + Testing)**: 2-3 days

**Total Remaining**: ~5-8 days for full implementation

---

## 📚 REFERENCE FILES

- **Workflow**: `reference/workflow/IBKR_2_Indicator_4_Prod (1).json`
  - Contains all prompt templates
  - Shows complete n8n workflow logic

- **Chart Service**: `reference/webapp/services/chart_service.py`
  - 7-panel chart implementation
  - Indicator calculations

- **OpenSpec Proposal**: `LLM_CHART_SIGNALS_PROPOSAL.md`
  - Complete system design
  - API contracts
  - Architecture diagrams

---

## ✅ VALIDATION

Run OpenSpec validation:
```bash
openspec validate llm-chart-signals --strict
```

Result: **PASSED ✓**

---

## 🔧 CONFIGURATION EXAMPLE

Create `.env` file:
```env
# LLM Configuration
OPENAI_API_KEY=sk-your-key-here
LLM_VISION_PROVIDER=openai
LLM_VISION_MODEL=gpt-4-vision-preview
LLM_VISION_MAX_TOKENS=4096
LLM_VISION_TEMPERATURE=0.1
LLM_DEFAULT_LANGUAGE=en

# Chart Settings
CHART_WIDTH=1920
CHART_HEIGHT=1400

# MinIO (must be publicly accessible)
MINIO_PUBLIC_ENDPOINT=localhost:9000
```

---

**Status**: Core services implemented, ready for integration and testing  
**Updated**: 2025-10-24

