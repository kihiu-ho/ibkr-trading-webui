# Implementation Tasks

## Phase 1: Diagnose Artifact Storage Issues
- [ ] 1.1 Check backend logs for artifact API requests
- [ ] 1.2 Test artifact storage from Airflow worker container
- [ ] 1.3 Verify artifacts table schema in database
- [ ] 1.4 Test backend API connectivity from Airflow
- [ ] 1.5 Check for silenced exceptions in workflow code

## Phase 2: Fix Artifact Storage
- [ ] 2.1 Add connection timeout and retry logic to artifact_storage.py
- [ ] 2.2 Implement exponential backoff for API calls
- [ ] 2.3 Add comprehensive error logging with context
- [ ] 2.4 Validate artifact data before API calls
- [ ] 2.5 Add fallback local storage mechanism
- [ ] 2.6 Update workflow tasks to handle storage failures gracefully
- [ ] 2.7 Test artifact storage with mock failures

## Phase 3: Enable Workflow Automation
- [ ] 3.1 Add WORKFLOW_SCHEDULE environment variable to docker-compose
- [ ] 3.2 Update DAG to use schedule from environment
- [ ] 3.3 Set default schedule to `0 9 * * 1-5` (9 AM weekdays)
- [ ] 3.4 Add schedule validation logic
- [ ] 3.5 Update DAG documentation
- [ ] 3.6 Test scheduled execution
- [ ] 3.7 Verify manual trigger still works

## Phase 4: Fix Task Log Display
- [ ] 4.1 Update airflow_monitor.html to parse JSON in logs
- [ ] 4.2 Add syntax highlighting for structured data
- [ ] 4.3 Format "[object Object]" as readable JSON
- [ ] 4.4 Add log filtering (errors, warnings, info)
- [ ] 4.5 Implement collapsible log sections
- [ ] 4.6 Add copy-to-clipboard for logs

## Phase 5: Improve Workflow Robustness
- [ ] 5.1 Add pre-flight health check task
- [ ] 5.2 Verify IBKR connection before market data fetch
- [ ] 5.3 Check backend API availability
- [ ] 5.4 Add workflow-level error handling
- [ ] 5.5 Implement transaction boundaries for critical operations
- [ ] 5.6 Add workflow failure notifications

## Phase 6: Testing & Validation
- [ ] 6.1 Integration test: Full workflow end-to-end
- [ ] 6.2 Test artifact visibility on frontend
- [ ] 6.3 Test automatic schedule execution
- [ ] 6.4 Test manual trigger override
- [ ] 6.5 Failure test: Simulate backend API down
- [ ] 6.6 Failure test: Simulate IBKR connection loss
- [ ] 6.7 Verify graceful degradation
- [ ] 6.8 Load test: Multiple runs in sequence

## Phase 7: Documentation
- [ ] 7.1 Update workflow documentation
- [ ] 7.2 Document schedule configuration
- [ ] 7.3 Add troubleshooting guide
- [ ] 7.4 Create runbook for common issues
- [ ] 7.5 Update user guide with automation features

## Quick Wins (Do First)
- [ ] QW.1 Check backend logs NOW for errors
- [ ] QW.2 Test artifact API from Airflow worker: `curl http://backend:8000/api/artifacts/`
- [ ] QW.3 Add print statements to artifact_storage.py for debugging
- [ ] QW.4 Trigger workflow manually and watch logs in real-time
- [ ] QW.5 Check if artifacts table exists: `docker exec -it ibkr-postgres psql -U ibkr_user -d ibkr_trading -c "\d artifacts"`

