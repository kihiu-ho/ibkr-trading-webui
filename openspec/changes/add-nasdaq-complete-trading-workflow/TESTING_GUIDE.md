# Testing Guide

## Multi-Symbol Workflow Testing

### 1. Test Multi-Symbol Workflow DAG

1. **Start Services**
   ```bash
   ./start-webapp.sh
   ```

2. **Access Airflow**
   - Navigate to http://localhost:8080
   - Login: admin/admin

3. **Trigger Multi-Symbol Workflow**
   - Find `ibkr_multi_symbol_workflow` in the DAG list
   - Click "Trigger DAG"
   - Monitor execution in Airflow UI

4. **Verify Parallel Processing**
   - Check that TSLA and NVDA tasks run in parallel
   - Verify TaskGroups: `process_TSLA` and `process_NVDA`
   - Each symbol should have:
     - fetch_market_data
     - generate_daily_chart
     - generate_weekly_chart
     - analyze_with_llm
     - place_order (if signal actionable)
     - get_trades (if order placed)

5. **Check Artifacts**
   - Navigate to http://localhost:8000/artifacts
   - Verify artifacts are grouped by execution_id
   - Check for:
     - Charts (daily and weekly for each symbol)
     - LLM analyses (one per symbol)
     - Trading signals (one per symbol)
     - Orders (if placed)
     - Trades (if executed)
     - Portfolio snapshot (one per execution)

### 2. Test Airflow Integration

1. **View Run Details**
   - In Airflow UI, click on a completed run
   - Click "View" button to see run details
   - Verify "Generated Artifacts" section appears

2. **Check Artifact Display**
   - Artifacts should show with proper badges:
     - LLM: Purple with robot icon
     - Chart: Blue with chart icon
     - Signal: Yellow with bolt icon
     - Order: Green with shopping cart icon
     - Trade: Orange with exchange icon
     - Portfolio: Teal with wallet icon

3. **Test Artifact Navigation**
   - Click on an artifact card
   - Should navigate to artifact detail page
   - Verify artifact details are displayed correctly

4. **Test Real-time Updates**
   - Trigger a workflow run
   - Open run details modal while run is executing
   - Verify artifacts appear as tasks complete
   - Check polling updates every 5 seconds

### 3. Test Artifacts API

1. **Test Grouping**
   ```bash
   curl "http://localhost:8000/api/artifacts/?group_by=execution_id"
   ```
   - Should return artifacts grouped by execution_id
   - Check `grouped` field in response

2. **Test Filtering**
   ```bash
   # Filter by type
   curl "http://localhost:8000/api/artifacts/?type=order"
   curl "http://localhost:8000/api/artifacts/?type=trade"
   curl "http://localhost:8000/api/artifacts/?type=portfolio"
   
   # Filter by execution_id
   curl "http://localhost:8000/api/artifacts/?execution_id=<run_id>"
   
   # Filter by symbol
   curl "http://localhost:8000/api/artifacts/?symbol=TSLA"
   ```

3. **Test Artifact Creation**
   - Run workflow
   - Check database for artifacts:
   ```sql
   SELECT id, name, type, symbol, execution_id, step_name 
   FROM artifacts 
   ORDER BY created_at DESC 
   LIMIT 20;
   ```

### 4. Test Frontend Artifacts Page

1. **Navigate to Artifacts Page**
   - Go to http://localhost:8000/artifacts
   - Verify page loads without errors

2. **Test Grouped View**
   - Toggle to "Grouped" view
   - Verify artifacts are grouped by execution_id
   - Check group headers show workflow_id and timestamp
   - Verify expand/collapse works

3. **Test Filtering**
   - Click filter buttons (LLM, Charts, Signals, Orders, Trades, Portfolio)
   - Verify only matching artifacts are shown
   - Test search functionality

4. **Test Artifact Cards**
   - Verify all artifact types display correctly
   - Check badges and icons are correct
   - Verify order/trade/portfolio show specific info

### 5. Common Issues and Fixes

**Issue: Artifacts not showing in Airflow modal**
- Check execution_id format matches between workflow and API
- Verify artifacts API is accessible
- Check browser console for errors

**Issue: Artifacts not grouped correctly**
- Verify execution_id is set correctly in workflow
- Check execution_id format matches DAG run ID
- Ensure artifacts API grouping works

**Issue: Order/Trade/Portfolio artifacts not displaying**
- Check artifact type detection in frontend
- Verify signal_data.artifact_type is set correctly
- Check artifact storage functions

**Issue: Multi-symbol workflow not running in parallel**
- Verify TaskGroups are set up correctly
- Check Airflow worker availability
- Verify no task dependencies between symbol groups

## Expected Results

After successful testing:
- ✅ Multi-symbol workflow processes TSLA and NVDA in parallel
- ✅ All artifacts are stored with proper metadata
- ✅ Artifacts are grouped by execution_id
- ✅ Airflow run details show generated artifacts
- ✅ Frontend displays all artifact types correctly
- ✅ Artifact navigation works bidirectionally

