# Fix Airflow DAG Import Errors

## Summary

**Why**: All IBKR Airflow workflows (`ibkr_trading_signal_workflow`, `ibkr_stock_data_workflow`, `ibkr_multi_symbol_workflow`) are showing "Import errors" in the Airflow UI, preventing them from being triggered and executed. The root cause is missing Python dependencies in the Airflow Docker container.

**What Changes**: 
- Verify and fix missing dependencies in Airflow container (specifically `stock-indicators`)
- Rebuild Airflow Docker image if needed
- Add diagnostic tools to detect and report import errors
- Create automated testing to verify DAG imports work correctly
- Add API-based testing and validation workflow

**Impact**: 
- All IBKR workflows will be functional and triggerable
- Developers can easily diagnose import issues
- CI/CD can validate DAG imports automatically

## Problem Statement

The Airflow UI shows three IBKR workflows with "Import errors" status:
- `ibkr_trading_signal_workflow`
- `ibkr_stock_data_workflow`  
- `ibkr_multi_symbol_workflow`

When attempting to import these DAGs, the error is:
```
ModuleNotFoundError: No module named 'stock_indicators'
```

This occurs in `dags/utils/chart_generator.py` which imports `stock_indicators` for technical indicator calculations.

## Root Cause Analysis

1. **Missing Dependency**: The `stock-indicators` package is listed in `Dockerfile.airflow` but may not be installed in the running container
2. **Container Not Rebuilt**: The Docker image may not have been rebuilt after adding the dependency
3. **No Validation**: There's no automated check to verify all required dependencies are installed
4. **No Diagnostic Tools**: No easy way to check which dependencies are missing

## Proposed Solution

### 1. Dependency Verification and Fix
- Verify `stock-indicators` is installed in Airflow container
- Rebuild Docker image if dependency is missing
- Add validation script to check all required dependencies

### 2. Diagnostic Tools
- Create script to test DAG imports in Airflow container
- Add API endpoint to check DAG import status
- Enhance UI to show specific import error messages

### 3. Automated Testing
- Add test script to validate all DAG imports
- Integrate into CI/CD pipeline
- Test DAG triggering via API

### 4. Documentation
- Document all required dependencies for DAGs
- Add troubleshooting guide for import errors
- Create runbook for fixing import issues

## Success Criteria

- [ ] All three IBKR workflows show "Active" status (no import errors)
- [ ] All DAGs can be triggered via API successfully
- [ ] Diagnostic script can identify missing dependencies
- [ ] Automated tests verify DAG imports work
- [ ] Documentation updated with dependency requirements

## Implementation Plan

1. **Investigate Current State**
   - Check if `stock-indicators` is installed in container
   - List all missing dependencies
   - Verify Dockerfile has all required packages

2. **Fix Dependencies**
   - Rebuild Airflow Docker image if needed
   - Verify all packages install correctly
   - Test DAG imports after fix

3. **Add Diagnostic Tools**
   - Create `scripts/check-dag-imports.sh` script
   - Add API endpoint for DAG health check
   - Enhance UI error messages

4. **Add Testing**
   - Create test script to validate all DAG imports
   - Add API-based DAG trigger test
   - Integrate into test suite

5. **Documentation**
   - Document all DAG dependencies
   - Add troubleshooting guide
   - Update README with dependency information

## Breaking Changes

None - this is a bug fix that restores intended functionality.

## Dependencies

- Docker and Docker Compose
- Airflow 2.10.5
- Python packages: `stock-indicators`, `plotly`, `kaleido`, etc.

## Testing Strategy

1. **Unit Tests**: Test DAG imports in isolated environment
2. **Integration Tests**: Test DAG imports in Docker container
3. **API Tests**: Test DAG triggering via REST API
4. **Manual Tests**: Verify workflows appear correctly in UI

## Rollback Plan

If issues occur:
1. Revert Dockerfile changes
2. Rebuild previous Docker image
3. Restart Airflow services

## Timeline

- Investigation: 30 minutes
- Fix implementation: 1 hour
- Testing: 1 hour
- Documentation: 30 minutes
- **Total**: ~3 hours

