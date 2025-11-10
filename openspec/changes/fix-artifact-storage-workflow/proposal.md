# Fix Artifact Storage in ibkr_stock_data_workflow

## Problem Statement

The `ibkr_stock_data_workflow` has been enhanced with chart generation and LLM analysis tasks, but artifacts are not being stored or retrieved correctly:

1. **Chart Generation Fails**: `ChartConfig` requires a `symbol` field that is not being provided
2. **Artifact Storage Mismatch**: `store_chart_artifact` function signature doesn't match usage (expects `chart_type` but receives `timeframe`)
3. **LLM Artifact Storage Mismatch**: `store_llm_artifact` function expects `prompt`, `response`, `model_name` but is being called with a `signal` object
4. **No Artifacts Retrieved**: Even when tasks succeed, artifacts are not found when querying by `execution_id`

## Root Causes

1. **ChartConfig Missing Symbol**: The `ChartConfig` model requires a `symbol` field, but the workflow is not providing it when creating chart configurations.

2. **Function Signature Mismatch**: 
   - `store_chart_artifact` expects `chart_type` parameter, but code passes `timeframe`
   - `store_llm_artifact` expects `prompt`, `response`, `model_name`, but code passes a `signal` object

3. **Artifact Storage Not Called**: Due to errors in chart generation, artifacts are never stored, so retrieval returns empty results.

## Proposed Changes

### 1. Fix ChartConfig Usage
- Add `symbol` parameter to all `ChartConfig` instantiations
- Ensure symbol is passed correctly to chart generator

### 2. Fix store_chart_artifact Call
- Change `timeframe` parameter to `chart_type` to match function signature
- Or update function signature to accept `timeframe` if that's the preferred parameter name

### 3. Fix store_llm_artifact Call
- Extract `prompt`, `response`, and `model_name` from signal object
- Or create a new function `store_signal_artifact` that accepts a signal object
- Update function to handle signal-based LLM artifacts

### 4. Verify Execution ID Format
- Ensure `execution_id` format matches between storage and retrieval
- Verify URL encoding/decoding is consistent

## Impact

### Benefits
- Charts will be generated successfully
- LLM analysis artifacts will be stored correctly
- Artifacts will be retrievable by execution_id
- Workflow will complete end-to-end with all artifacts visible

### Risks
- Function signature changes may affect other workflows
- Need to ensure backward compatibility

## Success Criteria

1. ✅ Chart generation succeeds and stores artifacts
2. ✅ LLM analysis succeeds and stores artifacts
3. ✅ Artifacts are retrievable by execution_id
4. ✅ Charts and LLM analysis visible in Airflow UI
5. ✅ All workflow tasks complete successfully

## Implementation Approach

1. **Fix ChartConfig** - Add symbol parameter
2. **Fix store_chart_artifact** - Correct parameter names
3. **Fix store_llm_artifact** - Handle signal objects or create new function
4. **Test end-to-end** - Verify artifacts are stored and retrieved
5. **Verify UI display** - Check artifacts appear in Airflow monitor

