# Design: Enhance Airflow Workflow Visualization

## Architecture Overview

### Current State
- `ibkr_stock_data_workflow`: extract -> validate -> transform -> log_to_mlflow
- Airflow proxy routes handle DAG and task instance queries
- Artifacts stored with execution_id for workflow tracking
- Charts and LLM analysis exist in other workflows but not in stock data workflow

### Target State
- `ibkr_stock_data_workflow`: extract -> validate -> transform -> **generate_charts** -> **llm_analysis** -> log_to_mlflow
- Logs endpoint working correctly
- Charts and LLM analysis visible in Airflow UI
- All artifacts linked by execution_id

## Technical Design

### 1. Fix Logs Endpoint

#### Problem Analysis
The route pattern `/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}` may not be matching due to:
- URL encoding issues with dag_run_id (contains `+`, `:`)
- Route ordering in FastAPI
- Path parameter parsing

#### Solution
- Verify route registration in `backend/app/routes/airflow_proxy.py`
- Ensure proper URL encoding when forwarding to Airflow API
- Add route-specific logging for debugging
- Test with various dag_run_id formats

#### Implementation
```python
@router.get('/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}')
async def task_instance_logs(...):
    # URL encode dag_run_id for Airflow API
    # Handle both JSON and text responses
    # Return appropriate error messages
```

### 2. Add LLM Analysis to Workflow

#### Chart Generation Task
- Use existing `ChartGenerator` utility
- Generate daily and weekly charts for each symbol
- Calculate technical indicators (SMA, RSI, MACD, Bollinger Bands)
- Store charts as artifacts with execution_id

#### LLM Analysis Task
- Use existing `LLMSignalAnalyzer` utility
- Analyze both daily and weekly charts together
- Generate trading signals with confidence scores
- Store analysis as artifacts with execution_id

#### Workflow Integration
```python
# New tasks in ibkr_stock_data_workflow
generate_charts_task = PythonOperator(...)
llm_analysis_task = PythonOperator(...)

# Updated dependencies
extract_task >> validate_task >> transform_task >> generate_charts_task >> llm_analysis_task >> mlflow_task
```

### 3. Display Charts in UI

#### API Changes
- Artifacts API already supports filtering by execution_id
- Add chart-specific filtering
- Return chart metadata (symbol, timeframe, indicators)

#### UI Changes
- Update `airflow_monitor.html`
- Add "Generated Charts" section to run details modal
- Display chart thumbnails with metadata
- Link to full chart views

#### Data Flow
```
Workflow Run -> execution_id -> Artifacts API -> Filter charts -> Display in UI
```

### 4. Display LLM Analysis in UI

#### API Changes
- Filter LLM analysis artifacts by execution_id
- Return analysis data (signals, confidence, reasoning)
- Include metadata (symbol, timestamp)

#### UI Changes
- Add "LLM Analysis" section to run details modal
- Display trading signals with badges
- Show confidence scores with visual indicators
- Format reasoning text for readability

#### Data Flow
```
Workflow Run -> execution_id -> Artifacts API -> Filter LLM analysis -> Display in UI
```

## Data Models

### Chart Artifact
```json
{
  "type": "chart",
  "symbol": "TSLA",
  "execution_id": "manual__2025-11-09T04:30:25.024562+00:00",
  "metadata": {
    "timeframe": "daily",
    "indicators": ["SMA", "RSI", "MACD"]
  }
}
```

### LLM Analysis Artifact
```json
{
  "type": "llm",
  "symbol": "TSLA",
  "execution_id": "manual__2025-11-09T04:30:25.024562+00:00",
  "signal_data": {
    "action": "BUY",
    "confidence": 0.85,
    "reasoning": "..."
  }
}
```

## UI Components

### Chart Display Component
- Chart thumbnail/image
- Symbol and timeframe badges
- Indicators list
- Link to full view

### LLM Analysis Component
- Signal badge (BUY/SELL/HOLD)
- Confidence score with visual indicator
- Reasoning text (collapsible)
- Timestamp and symbol

## Error Handling

### Logs Endpoint
- 404: Logs not found → Return appropriate message
- 500: Airflow API error → Log and return error
- Timeout: Request timeout → Return 504

### Workflow Execution
- Chart generation failure → Log error, continue workflow
- LLM analysis failure → Log error, continue workflow
- Artifact storage failure → Log error, retry

## Testing Strategy

### Unit Tests
- Test route matching for logs endpoint
- Test chart generation function
- Test LLM analysis function
- Test artifact storage

### Integration Tests
- Test complete workflow execution
- Test API endpoints
- Test UI components
- Test error scenarios

### End-to-End Tests
- Run complete workflow
- Verify logs are accessible
- Verify charts appear in UI
- Verify LLM analysis appears in UI

## Performance Considerations

### Chart Generation
- Generate charts in parallel for multiple symbols
- Cache chart data if possible
- Optimize image storage

### LLM Analysis
- Batch analysis for multiple symbols
- Cache LLM responses if appropriate
- Handle API rate limits

### UI Loading
- Lazy load charts and analysis
- Paginate if many artifacts
- Cache API responses

## Security Considerations

### API Access
- Verify Airflow authentication
- Validate execution_id format
- Sanitize user inputs

### Artifact Access
- Verify execution_id ownership
- Check user permissions
- Validate artifact types

## Migration Strategy

### Backward Compatibility
- Existing workflows continue to work
- New features are additive
- No breaking changes to APIs

### Rollout Plan
1. Fix logs endpoint (immediate)
2. Add LLM analysis to workflow (next)
3. Update UI for charts (then)
4. Update UI for LLM analysis (finally)

