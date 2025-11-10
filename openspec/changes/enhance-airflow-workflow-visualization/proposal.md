# Enhance Airflow Workflow Visualization and Add LLM Analysis

## Problem Statement

The current Airflow workflow visualization and `ibkr_stock_data_workflow` have several gaps:

1. **Task Instance Logs Endpoint Returns 404**: The logs endpoint `/api/airflow/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}` is returning 404 errors, preventing users from viewing task logs.

2. **Missing LLM Analysis in Workflow**: The `ibkr_stock_data_workflow` does not include LLM analysis of stock data, which is a critical component for generating trading signals.

3. **No Chart Visualization**: Charts generated during workflow execution are not displayed in the Airflow workflow run details UI.

4. **No LLM Analysis Display**: LLM analysis results are not visible in the Airflow workflow run details, making it difficult to understand the AI-driven insights.

## Proposed Changes

### 1. Fix Task Instance Logs Endpoint
- Investigate and fix the 404 error for the logs endpoint
- Ensure proper route matching and URL encoding
- Add comprehensive error handling and logging

### 2. Add LLM Analysis to ibkr_stock_data_workflow
- Integrate chart generation (daily and weekly) into the workflow
- Add LLM analysis task that analyzes charts and generates trading signals
- Store LLM analysis results as artifacts
- Link LLM analysis to MLflow tracking

### 3. Display Charts in Airflow Workflow UI
- Enhance the Airflow run details modal to display generated charts
- Filter and display charts by execution_id
- Show chart metadata (symbol, timeframe, indicators)
- Provide links to full chart views

### 4. Display LLM Analysis in Airflow Workflow UI
- Show LLM analysis results in the workflow run details
- Display trading signals, confidence scores, and reasoning
- Link to full LLM analysis artifacts
- Show analysis summary and key insights

## Impact

### Benefits
- **Improved Debugging**: Users can view task logs directly from the UI
- **Complete Workflow**: LLM analysis provides AI-driven insights for trading decisions
- **Better Visualization**: Charts and analysis visible in workflow context
- **Enhanced UX**: All workflow outputs accessible from one place

### Risks
- Route matching issues may require FastAPI route adjustments
- LLM API calls may add latency to workflow execution
- Chart generation may require additional storage

### Dependencies
- Existing artifact storage system
- Chart generation utilities
- LLM signal analyzer
- Airflow proxy routes

## Success Criteria

1. ✅ Task instance logs endpoint returns 200 with log content
2. ✅ `ibkr_stock_data_workflow` includes LLM analysis task
3. ✅ Charts are visible in Airflow workflow run details
4. ✅ LLM analysis is displayed in workflow run details
5. ✅ All features tested and working end-to-end

## Implementation Approach

1. **Fix logs endpoint** - Debug route matching and fix 404 errors
2. **Add LLM analysis task** - Integrate chart generation and LLM analysis into workflow
3. **Enhance UI** - Update Airflow monitor to display charts and LLM analysis
4. **Test and validate** - End-to-end testing of all features

