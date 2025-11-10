# Fix Artifacts & Workflow Automation

## Why

### Problem Statement
1. **Empty Artifacts Page**: Model artifacts page shows "No artifacts found" despite workflow executions completing successfully
2. **Manual Workflow Triggers**: Users must manually trigger the IBKR trading workflow, missing opportunities for automated trading signals
3. **Task Execution Logs Not Visible**: Airflow task logs show "[object Object]" instead of useful information in the run details modal

### Business Impact
- Users cannot see generated LLM analyses, charts, and trading signals
- No automated signal generation for timely trading decisions
- Difficult to debug workflow failures without proper log visibility
- Poor user experience with broken artifact tracking

### Root Causes
- Artifact storage may be failing silently in the workflow
- Backend API connectivity issues from Airflow workers
- DAG schedule_interval set to `None` (manual only)
- Task log rendering issues in frontend

## What Changes

### 1. Fix Artifact Storage Pipeline
- **Verify Backend API Connectivity**: Ensure Airflow workers can reach backend API
- **Add Retry Logic**: Implement robust retry mechanism for artifact API calls
- **Enhance Error Logging**: Better error messages when artifact storage fails
- **Validate Artifact Data**: Ensure all required fields are populated before storage

### 2. Enable Automatic Workflow Execution
- **Configure Schedule**: Change from manual (`None`) to configurable schedule
- **Add Environment Variable**: `WORKFLOW_SCHEDULE` for easy configuration
- **Default Schedule**: `0 9 * * 1-5` (9 AM Monday-Friday, market hours)
- **Allow Manual Override**: Keep ability to trigger manually

### 3. Fix Task Execution Logs Display
- **Frontend JSON Parsing**: Fix "object Object" rendering in Airflow run details
- **Format Log Output**: Pretty-print JSON and structured data
- **Add Log Streaming**: Real-time log updates in modal
- **Error Highlighting**: Color-code errors and warnings

### 4. Improve Workflow Robustness
- **Health Checks**: Pre-flight checks for IBKR connection, database, backend API
- **Graceful Degradation**: Continue workflow even if artifact storage fails
- **Transaction Boundaries**: Ensure critical data (orders, trades) saved even if logging fails
- **Comprehensive Testing**: Integration tests for full workflow

## Impact

### User Experience
- ✅ **Artifacts Visible**: All generated charts, LLM analyses, and signals appear on Artifacts page
- ✅ **Auto-Generated Signals**: Daily trading signals without manual intervention
- ✅ **Readable Logs**: Clear, formatted logs in task execution view
- ✅ **Reliable Workflow**: Robust error handling and recovery

### System Reliability
- Improved observability with better logging
- Reduced manual intervention requirements
- Higher confidence in workflow execution
- Better debugging capabilities

### Data Lineage
- Complete audit trail from market data → charts → LLM → signals → orders
- Traceable workflow executions with artifacts
- MLflow integration for experiment tracking

## Technical Approach

### Phase 1: Diagnose Artifact Storage (Priority: Critical)
1. Check backend API logs for artifact POST requests
2. Test artifact storage from Airflow worker container
3. Verify database schema and constraints
4. Check network connectivity between services

### Phase 2: Fix Artifact Storage (Priority: Critical)
1. Add connection pooling for backend API calls
2. Implement exponential backoff retry logic
3. Add validation before API calls
4. Store artifacts locally as fallback

### Phase 3: Enable Workflow Automation (Priority: High)
1. Add `WORKFLOW_SCHEDULE` environment variable
2. Update DAG definition with configurable schedule
3. Add schedule validation and documentation
4. Test automated execution

### Phase 4: Fix Log Display (Priority: Medium)
1. Update `airflow_monitor.html` to parse JSON logs
2. Add syntax highlighting for structured data
3. Implement log streaming with Server-Sent Events
4. Add log filtering and search

### Phase 5: Comprehensive Testing (Priority: High)
1. Integration test: Full workflow end-to-end
2. Load test: Multiple concurrent executions
3. Failure test: Simulate API failures, network issues
4. Recovery test: Verify retry mechanisms

## Success Criteria

### Acceptance Tests
- [ ] Workflow executes successfully and generates 3+ artifacts (charts, LLM, signal)
- [ ] Artifacts visible on `/artifacts` page within 1 minute of completion
- [ ] Workflow runs automatically on schedule (daily at 9 AM)
- [ ] Task logs display readable, formatted output
- [ ] Manual trigger still works
- [ ] Workflow completes even if artifact storage fails (graceful degradation)
- [ ] All artifacts linked to correct execution_id and workflow_id

### Performance Metrics
- Workflow completion time: < 3 minutes
- Artifact storage latency: < 2 seconds per artifact
- Log loading time: < 1 second
- 99% success rate for artifact storage

### User Validation
- User can view generated charts with indicators
- User can read LLM analysis and reasoning
- User can see trading signal with confidence level
- User can navigate from Airflow run → Artifacts → Artifact details

## Risks & Mitigation

### Risk: Frequent Workflow Failures
- **Mitigation**: Comprehensive health checks before execution
- **Mitigation**: Alert on repeated failures
- **Mitigation**: Automatic disable after N consecutive failures

### Risk: API Rate Limiting
- **Mitigation**: Respect IBKR API rate limits
- **Mitigation**: Implement exponential backoff
- **Mitigation**: Queue requests if necessary

### Risk: Resource Exhaustion
- **Mitigation**: Limit concurrent workflow runs (max_active_runs=1)
- **Mitigation**: Monitor memory and CPU usage
- **Mitigation**: Cleanup old artifacts and logs

### Risk: Market Hours Constraints
- **Mitigation**: Schedule only during market hours
- **Mitigation**: Skip execution if market closed
- **Mitigation**: Configurable schedule per timezone

## Dependencies

- Backend API must be available and responsive
- IBKR Gateway must be authenticated
- Database must have artifacts table with correct schema
- MLflow server must be running
- LLM API (OpenAI/Anthropic) must be configured

## Timeline Estimate

- **Phase 1 (Diagnosis)**: 1-2 hours
- **Phase 2 (Fix Storage)**: 2-3 hours  
- **Phase 3 (Automation)**: 1-2 hours
- **Phase 4 (Logs)**: 2-3 hours
- **Phase 5 (Testing)**: 2-3 hours

**Total**: 8-13 hours

## Rollback Plan

If issues arise:
1. Set `schedule_interval=None` to disable automation
2. Revert artifact storage changes
3. Fallback to manual workflow triggers
4. Review logs and diagnose issues
5. Re-implement with fixes

## Related Documentation

- [Artifact Workflow Tracking](../../docs/implementation/ARTIFACT_WORKFLOW_TRACKING_COMPLETE.md)
- [Airflow Integration](../../docs/implementation/AIRFLOW_ARTIFACT_INTEGRATION_COMPLETE.md)
- [IBKR Workflow DAG](../../dags/ibkr_trading_signal_workflow.py)
- [Artifact Storage Utility](../../dags/utils/artifact_storage.py)

