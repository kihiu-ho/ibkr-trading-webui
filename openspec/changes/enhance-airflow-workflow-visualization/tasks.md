# Tasks: Enhance Airflow Workflow Visualization

## Phase 1: Fix Logs Endpoint

- [ ] **Task 1.1**: Debug 404 error in logs endpoint
  - Check route pattern matching
  - Verify URL encoding for dag_run_id
  - Test with different dag_run_id formats
  - Add debug logging

- [ ] **Task 1.2**: Fix route matching issues
  - Ensure route is registered correctly
  - Check FastAPI route ordering
  - Verify path parameter parsing
  - Test endpoint with actual requests

- [ ] **Task 1.3**: Add error handling
  - Handle missing logs gracefully
  - Return appropriate error messages
  - Log errors for debugging
  - Test error scenarios

## Phase 2: Add LLM Analysis to Workflow

- [ ] **Task 2.1**: Add chart generation task
  - Create chart generation function
  - Generate daily and weekly charts
  - Calculate technical indicators
  - Store charts as artifacts

- [ ] **Task 2.2**: Add LLM analysis task
  - Create LLM analysis function
  - Analyze daily and weekly charts
  - Generate trading signals
  - Store analysis as artifacts

- [ ] **Task 2.3**: Integrate into workflow
  - Add tasks to DAG definition
  - Set task dependencies
  - Link to MLflow tracking
  - Test workflow execution

- [ ] **Task 2.4**: Store artifacts
  - Store charts with execution_id
  - Store LLM analysis with execution_id
  - Link artifacts to workflow run
  - Verify artifact storage

## Phase 3: Display Charts in UI

- [ ] **Task 3.1**: Fetch charts by execution_id
  - Update artifacts API to filter by execution_id
  - Filter charts by type
  - Return chart metadata
  - Test API endpoint

- [ ] **Task 3.2**: Update Airflow monitor UI
  - Add charts section to run details modal
  - Display chart thumbnails
  - Show chart metadata
  - Add links to full chart views

- [ ] **Task 3.3**: Style chart display
  - Create chart cards
  - Add chart type badges
  - Show timeframe and symbol
  - Responsive layout

## Phase 4: Display LLM Analysis in UI

- [ ] **Task 4.1**: Fetch LLM analysis by execution_id
  - Update artifacts API
  - Filter LLM analysis by type
  - Return analysis data
  - Test API endpoint

- [ ] **Task 4.2**: Update Airflow monitor UI
  - Add LLM analysis section
  - Display trading signals
  - Show confidence scores
  - Display reasoning/insights

- [ ] **Task 4.3**: Style LLM analysis display
  - Create analysis cards
  - Highlight signals
  - Show confidence indicators
  - Format reasoning text

## Phase 5: Testing and Validation

- [ ] **Task 5.1**: Test logs endpoint
  - Test with various dag_run_id formats
  - Verify log content retrieval
  - Test error handling
  - Check performance

- [ ] **Task 5.2**: Test workflow execution
  - Run complete workflow
  - Verify all tasks execute
  - Check artifact generation
  - Validate MLflow tracking

- [ ] **Task 5.3**: Test UI display
  - Verify charts appear in UI
  - Verify LLM analysis appears
  - Test filtering and navigation
  - Check responsive design

- [ ] **Task 5.4**: End-to-end testing
  - Complete workflow run
  - Verify all features work together
  - Test error scenarios
  - Performance testing

## Phase 6: Documentation

- [ ] **Task 6.1**: Update documentation
  - Document new workflow structure
  - Update API documentation
  - Add UI usage guide
  - Create troubleshooting guide

- [ ] **Task 6.2**: Create test scripts
  - Script to test logs endpoint
  - Script to test workflow
  - Script to verify UI features
  - Integration test suite

