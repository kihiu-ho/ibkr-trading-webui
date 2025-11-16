# Chart Artifact Context Enrichment - Implementation Complete

## Summary

Successfully implemented a feature to enrich chart artifacts with complete market data snapshots, indicator summaries, and LLM analysis context. Chart artifacts now expose all data needed for comprehensive UI visualization without requiring additional API calls.

## Changes Made

### 1. Specification (OpenSpec)
Created change proposal `add-chart-artifact-context` with:
- **artifact-management spec delta**: Describes persistence of market data snapshots and LLM context
- **api-backend spec delta**: Covers enriched artifact responses with hydration logic
- Validated with `openspec validate --strict` ✅

### 2. DAG Implementation (`dags/ibkr_trading_signal_workflow.py`)

#### Daily Chart Task
- Captures market data snapshot (last 50 bars with OHLCV data)
- Extracts indicator summary (SMA 20/50/200, RSI, MACD, Bollinger Bands)
- Stores enriched metadata alongside chart artifact
- Persists artifact ID to XCom for later enrichment

#### Weekly Chart Task
- Same enhancements as daily chart
- Captures last 20 weeks of data
- Stores indicator summary for weekly timeframe

#### LLM Analysis Task
- Retrieves chart artifact IDs from XCom
- Backfills prompt, response, and model_name onto both chart artifacts
- Adds llm_analysis metadata with:
  - Action (BUY/SELL/HOLD)
  - Confidence score and level
  - Reasoning snippet (first 200 chars)
  - Key factors (top 3)
  - Entry price, stop loss, take profit
  - Actionability flag

### 3. Artifact Storage Utility (`dags/utils/artifact_storage.py`)

Added `update_artifact()` function:
- PATCH endpoint to update existing artifacts
- Handles Decimal conversion for JSON fields
- Retry logic with exponential backoff
- Used by LLM task to enrich chart artifacts post-creation

### 4. Backend API Enhancement (`backend/api/artifacts.py`)

#### GET /api/artifacts/{id}
- Hydrates chart artifacts with missing context on-the-fly
- Falls back to market_data table for OHLCV bars if not persisted
- Derives LLM analysis from related signal/llm artifacts when available

#### `_hydrate_chart_artifact()` helper
- Queries market_data table for latest bars
- Finds related LLM/signal artifacts by symbol + execution_id
- Populates prompt, response, model_name if missing
- Builds llm_analysis metadata from signal_data

## Data Flow

```
Fetch Market Data
  ↓
Generate Daily Chart → Store with market_data_snapshot + indicators
  ↓                     (artifact_id → XCom)
Generate Weekly Chart → Store with market_data_snapshot + indicators
  ↓                      (artifact_id → XCom)
LLM Analysis → Update chart artifacts with prompt/response/llm_analysis
```

## Example Enriched Artifact

```json
{
  "id": 7,
  "name": "TSLA Daily Chart",
  "type": "chart",
  "symbol": "TSLA",
  "image_path": "http://localhost:9000/...",
  "chart_type": "daily",
  "prompt": "Analyze TSLA daily and weekly charts...",
  "response": "Based on analysis, TSLA shows...",
  "model_name": "gpt-4o",
  "chart_data": {
    "indicators": ["SMA_20", "SMA_50", "RSI", "MACD"],
    "timeframe": "daily",
    "bars_count": 200,
    "minio_url": "http://..."
  },
  "metadata": {
    "market_data_snapshot": {
      "symbol": "TSLA",
      "timeframe": "daily",
      "latest_price": 250.35,
      "bar_count": 50,
      "bars": [
        {
          "date": "2025-11-14T00:00:00",
          "open": 248.50,
          "high": 252.00,
          "low": 247.00,
          "close": 250.35,
          "volume": 15000000
        }
      ]
    },
    "indicator_summary": {
      "sma_20": 245.20,
      "sma_50": 242.10,
      "sma_200": 230.50,
      "rsi_14": 62.5,
      "macd": 1.25,
      "bb_upper": 255.00,
      "bb_lower": 240.00
    },
    "llm_analysis": {
      "action": "BUY",
      "confidence": "HIGH",
      "confidence_score": 85.0,
      "reasoning_snippet": "TSLA shows bullish momentum with price above all SMAs...",
      "key_factors": ["Strong uptrend", "RSI in healthy zone", "Volume confirming"],
      "entry_price": 251.00,
      "stop_loss": 245.00,
      "take_profit": 265.00,
      "is_actionable": true
    }
  }
}
```

## Benefits

1. **Single API call**: Frontend gets complete chart context without separate queries
2. **Historical compatibility**: Hydration logic fills missing data for old artifacts
3. **Market data tables**: Render OHLCV tables directly from artifact metadata
4. **Indicator visualization**: Display technical indicator values inline
5. **LLM reasoning**: Show AI analysis alongside chart image
6. **Reduced latency**: No waterfall requests for related data

## Testing Status

- ✅ Syntax validation (all files compile)
- ✅ OpenSpec validation (strict mode passed)
- ⏳ Unit tests (manual testing recommended)
- ⏳ Integration tests (workflow execution needed)

## Next Steps

1. Run full IBKR trading signal workflow to generate enriched artifacts
2. Verify artifact API returns complete context
3. Update frontend to display market data tables and indicator summaries
4. Add automated tests for enrichment logic

## Files Modified

- `dags/ibkr_trading_signal_workflow.py` - Market data capture + LLM enrichment
- `dags/utils/artifact_storage.py` - Added update_artifact()
- `backend/api/artifacts.py` - Hydration logic for GET endpoints
- `openspec/changes/add-chart-artifact-context/` - Specification files

## OpenSpec Change

Run `openspec list` to see the new change:
```
add-chart-artifact-context                     13/16 tasks complete
```

All implementation tasks complete. Testing tasks remain.
