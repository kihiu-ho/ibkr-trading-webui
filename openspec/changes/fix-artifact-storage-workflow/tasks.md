# Tasks: Fix Artifact Storage in ibkr_stock_data_workflow

## Phase 1: Fix Chart Generation

- [x] **Task 1.1**: Fix ChartConfig missing symbol field
  - Add `symbol` parameter to ChartConfig instantiations
  - Change `show_*` to `include_*` to match ChartConfig model

- [x] **Task 1.2**: Fix ChartResult field names
  - Change `image_path` to `file_path` in ChartResult creation
  - Add required fields: `width`, `height`, `periods_shown`

- [x] **Task 1.3**: Fix store_chart_artifact parameters
  - Change `chart_path` to `image_path` to match function signature
  - Change `timeframe` to `chart_type` to match function signature
  - Add `timeframe` to metadata instead

## Phase 2: Fix LLM Analysis Storage

- [x] **Task 2.1**: Fix analyze_charts call
  - Add `symbol` as first parameter to `analyze_charts` call

- [x] **Task 2.2**: Fix artifact storage for LLM analysis
  - Change from `store_llm_artifact` to `store_signal_artifact`
  - Extract signal data (action, confidence, reasoning) for storage
  - Store signal data in `signal_data` field

- [x] **Task 2.3**: Update imports
  - Change import from `store_llm_artifact` to `store_signal_artifact`

## Phase 3: Testing and Verification

- [ ] **Task 3.1**: Test workflow execution
  - Trigger new workflow run
  - Verify all tasks complete successfully
  - Check logs for errors

- [ ] **Task 3.2**: Verify artifact storage
  - Check artifacts are stored with correct execution_id
  - Verify charts are stored
  - Verify LLM analysis signals are stored

- [ ] **Task 3.3**: Verify artifact retrieval
  - Query artifacts by execution_id
  - Verify charts are returned
  - Verify LLM analysis signals are returned

- [ ] **Task 3.4**: Verify UI display
  - Check charts appear in Airflow monitor
  - Check LLM analysis appears in Airflow monitor
  - Verify artifact links work

## Phase 4: Documentation

- [ ] **Task 4.1**: Update documentation
  - Document artifact storage format
  - Update workflow documentation
  - Add troubleshooting guide

