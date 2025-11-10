# Fix Airflow DAG Import Errors - Implementation Tasks

## Implementation Checklist

### Phase 1: Investigation and Diagnosis

- [ ] 1.1 Check if `stock-indicators` is installed in Airflow container
- [ ] 1.2 List all Python packages installed in Airflow container
- [ ] 1.3 Test DAG import directly in container to get exact error
- [ ] 1.4 Check Dockerfile.airflow for all required dependencies
- [ ] 1.5 Verify Docker image was built with latest dependencies

### Phase 2: Fix Dependencies

- [ ] 2.1 Verify `stock-indicators` is in Dockerfile.airflow
- [ ] 2.2 Rebuild Airflow Docker image if needed
- [ ] 2.3 Verify package installation in rebuilt container
- [ ] 2.4 Test DAG imports after rebuild
- [ ] 2.5 Check for any other missing dependencies

### Phase 3: Diagnostic Tools

- [ ] 3.1 Enhance `scripts/check-dag-imports.sh` script
  - [ ] 3.1.1 Add dependency checking
  - [ ] 3.1.2 Add import error reporting
  - [ ] 3.1.3 Add fix suggestions
- [ ] 3.2 Create API endpoint for DAG health check
  - [ ] 3.2.1 Add `/api/airflow/dags/{dag_id}/health` endpoint
  - [ ] 3.2.2 Return import status and errors
- [ ] 3.3 Enhance UI to show specific import errors
  - [ ] 3.3.1 Display error messages in DAG cards
  - [ ] 3.3.2 Add "View Errors" button for failed DAGs

### Phase 4: Testing

- [ ] 4.1 Create test script for DAG imports
  - [ ] 4.1.1 Test all IBKR DAGs
  - [ ] 4.1.2 Report which DAGs fail and why
- [ ] 4.2 Test DAG triggering via API
  - [ ] 4.2.1 Test `ibkr_trading_signal_workflow`
  - [ ] 4.2.2 Test `ibkr_stock_data_workflow`
  - [ ] 4.2.3 Test `ibkr_multi_symbol_workflow`
- [ ] 4.3 Verify workflows appear correctly in UI
- [ ] 4.4 Run end-to-end workflow test

### Phase 5: Documentation

- [ ] 5.1 Document all DAG dependencies
  - [ ] 5.1.1 List required Python packages
  - [ ] 5.1.2 Document where dependencies are installed
- [ ] 5.2 Create troubleshooting guide
  - [ ] 5.2.1 How to check for import errors
  - [ ] 5.2.2 How to fix missing dependencies
  - [ ] 5.2.3 How to rebuild Docker image
- [ ] 5.3 Update README with dependency information
- [ ] 5.4 Add comments to Dockerfile.airflow explaining dependencies

### Phase 6: Validation

- [ ] 6.1 All three IBKR workflows show "Active" status
- [ ] 6.2 All DAGs can be triggered via API
- [ ] 6.3 Diagnostic script works correctly
- [ ] 6.4 UI shows correct status for all DAGs
- [ ] 6.5 No import errors in Airflow logs

## Testing Commands

```bash
# Check if stock-indicators is installed
docker exec ibkr-airflow-scheduler python3 -c "import stock_indicators; print('OK')"

# Test DAG import
docker exec ibkr-airflow-scheduler python3 -c "import sys; sys.path.insert(0, '/opt/airflow/dags'); exec(open('/opt/airflow/dags/ibkr_trading_signal_workflow.py').read())"

# Check Airflow DAG list
docker exec ibkr-airflow-scheduler airflow dags list | grep ibkr

# Trigger DAG via API
curl -X POST http://localhost:8000/api/airflow/dags/ibkr_trading_signal_workflow/dagRuns \
  -H "Content-Type: application/json" \
  -u airflow:airflow \
  -d '{}'
```

## Success Criteria

- ✅ All IBKR workflows appear in Airflow UI without import errors
- ✅ All DAGs can be triggered via API
- ✅ Diagnostic script identifies issues correctly
- ✅ UI shows helpful error messages
- ✅ Documentation is complete

