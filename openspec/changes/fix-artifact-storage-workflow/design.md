# Design: Fix Artifact Storage in ibkr_stock_data_workflow

## Issues Identified

### 1. ChartConfig Model Mismatch
**Problem**: `ChartConfig` requires:
- `symbol` (required)
- `include_sma`, `include_rsi`, etc. (not `show_sma`, `show_rsi`)

**Solution**: 
- Add `symbol` parameter to all ChartConfig instantiations
- Change `show_*` flags to `include_*` flags

### 2. ChartResult Field Mismatch
**Problem**: `ChartResult` uses `file_path`, not `image_path`

**Solution**:
- Change all references from `image_path` to `file_path`
- Add required fields: `width`, `height`, `periods_shown`

### 3. store_chart_artifact Parameter Mismatch
**Problem**: Function expects:
- `image_path` (not `chart_path`)
- `chart_type` (not `timeframe`)

**Solution**:
- Use `image_path` parameter name
- Use `chart_type` parameter name
- Store `timeframe` in metadata

### 4. LLM Analysis Storage Mismatch
**Problem**: 
- `analyze_charts` requires `symbol` as first parameter
- `store_llm_artifact` expects `prompt`, `response`, `model_name`
- But we have a `TradingSignal` object

**Solution**:
- Add `symbol` parameter to `analyze_charts` call
- Use `store_signal_artifact` instead of `store_llm_artifact`
- Extract signal data from TradingSignal object
- Store in `signal_data` field with proper structure

## Implementation Details

### Chart Generation Fix
```python
# Before
config=ChartConfig(
    show_sma=True,
    timeframe=Timeframe.DAILY
)

# After
config=ChartConfig(
    symbol=symbol,
    timeframe=Timeframe.DAILY,
    include_sma=True,
    include_rsi=True,
    include_macd=True,
    include_bollinger=True
)
```

### ChartResult Creation Fix
```python
# Before
ChartResult(
    symbol=symbol,
    timeframe=Timeframe.DAILY,
    image_path=str(daily_path),
    image_base64=daily_image
)

# After
ChartResult(
    symbol=symbol,
    timeframe=Timeframe.DAILY,
    file_path=str(daily_path),
    width=1920,
    height=1080,
    periods_shown=len(bars)
)
```

### Artifact Storage Fix
```python
# Chart storage
store_chart_artifact(
    name=f"{symbol}_daily_chart",
    symbol=symbol,
    image_path=daily_chart.file_path,  # Changed from chart_path
    chart_type="daily",  # Changed from timeframe
    execution_id=execution_id,
    metadata={'timeframe': 'daily', ...}  # timeframe in metadata
)

# LLM/Signal storage
store_signal_artifact(  # Changed from store_llm_artifact
    name=f"{symbol}_llm_analysis",
    symbol=symbol,
    action=str(signal.action),
    confidence=float(signal.confidence_score),
    execution_id=execution_id,
    signal_data={
        'action': str(signal.action),
        'confidence': str(signal.confidence),
        'confidence_score': float(signal.confidence_score),
        'reasoning': signal.reasoning,
        'key_factors': signal.key_factors
    }
)
```

## Data Flow

### Chart Generation Flow
```
Transformed Data → MarketData → ChartGenerator → ChartResult → store_chart_artifact → Database
```

### LLM Analysis Flow
```
ChartResults → LLMSignalAnalyzer → TradingSignal → store_signal_artifact → Database
```

### Artifact Retrieval Flow
```
execution_id → Artifacts API → Filter by type → Return charts and signals
```

## Testing Strategy

1. **Unit Tests**: Test each function with correct parameters
2. **Integration Tests**: Test complete workflow execution
3. **End-to-End Tests**: Verify artifacts stored and retrieved
4. **UI Tests**: Verify artifacts appear in Airflow monitor

## Error Handling

- Chart generation errors should not fail the workflow
- LLM analysis errors should not fail the workflow
- Artifact storage errors should be logged but not fail tasks
- Missing artifacts should return empty results gracefully

