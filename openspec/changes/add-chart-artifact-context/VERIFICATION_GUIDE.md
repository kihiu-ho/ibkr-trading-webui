# Chart Artifact Enrichment - Verification Guide

## ✅ Workflow Execution Status

Based on the Airflow logs, the IBKR trading signal workflow is **running successfully**:

```
[2025-11-15T05:13:43] ibkr_trading_signal_workflow.log_to_mlflow RUNNING
```

Tasks completed:
1. ✅ fetch_market_data
2. ✅ generate_daily_chart (with enrichment)
3. ✅ generate_weekly_chart (with enrichment)
4. ✅ analyze_with_llm (backfilled chart artifacts)
5. ✅ log_to_mlflow (currently running)

## 🔍 How to Verify Enrichment

### Step 1: Wait for Workflow Completion

The workflow should complete in a few minutes. Check Airflow UI:
```
http://localhost:8080/dags/ibkr_trading_signal_workflow/grid
```

### Step 2: Run Automated Test

Once workflow completes, run the enrichment test script:

```bash
python3 openspec/changes/add-chart-artifact-context/test_enrichment.py
```

**Expected output:**
```
🔍 Fetching chart artifacts...
✅ Found 2 chart artifact(s)

📊 Testing artifact #7: TSLA Daily Chart
   Symbol: TSLA
   Chart Type: daily

📋 Enrichment Status:
   ✅ prompt
   ✅ response
   ✅ model_name
   ✅ metadata
   ✅ market_data_snapshot
   ✅ indicator_summary
   ✅ llm_analysis

📈 Market Data Snapshot:
   Latest Price: $250.35
   Bar Count: 50
   Latest Bar: 2025-11-14T00:00:00
     Open: $248.50
     High: $252.00
     Low: $247.00
     Close: $250.35

📊 Indicator Summary:
   sma_20: 245.20
   sma_50: 242.10
   rsi_14: 62.50
   macd: 1.25

🤖 LLM Analysis:
   Action: BUY
   Confidence: HIGH (85%)
   Actionable: True
   Reasoning: Based on analysis, TSLA shows...

📊 Overall: 7/7 enrichment fields present
✅ Chart artifact enrichment working!
```

### Step 3: Manual API Verification

Check artifacts via API:

```bash
# List all chart artifacts
curl -s http://localhost:8000/api/artifacts/?type=chart | jq '.artifacts[] | {id, name, symbol, has_prompt: (.prompt != null), has_metadata: (.metadata != null)}'

# Get detailed artifact with enrichment
curl -s http://localhost:8000/api/artifacts/7 | jq '{
  id,
  name,
  prompt: (.prompt != null),
  response: (.response != null),
  model_name,
  market_data: (.metadata.market_data_snapshot != null),
  indicators: (.metadata.indicator_summary != null),
  llm_analysis: (.metadata.llm_analysis != null)
}'
```

**Expected enriched artifact:**
```json
{
  "id": 7,
  "name": "TSLA Daily Chart",
  "prompt": true,
  "response": true,
  "model_name": "gpt-4o",
  "market_data": true,
  "indicators": true,
  "llm_analysis": true
}
```

### Step 4: Check Database Directly

Verify enrichment in database:

```sql
-- Connect to database
docker exec -it postgres psql -U airflow -d trading

-- Check chart artifacts have enriched metadata
SELECT 
    id,
    name,
    prompt IS NOT NULL as has_prompt,
    response IS NOT NULL as has_response,
    model_name,
    metadata->'market_data_snapshot' IS NOT NULL as has_market_data,
    metadata->'indicator_summary' IS NOT NULL as has_indicators,
    metadata->'llm_analysis' IS NOT NULL as has_llm_analysis
FROM artifacts 
WHERE type = 'chart'
ORDER BY created_at DESC
LIMIT 5;
```

**Expected result:**
```
 id |       name          | has_prompt | has_response | model_name | has_market_data | has_indicators | has_llm_analysis 
----+---------------------+------------+--------------+------------+-----------------+----------------+------------------
  7 | TSLA Daily Chart    | t          | t            | gpt-4o     | t               | t              | t
  8 | TSLA Weekly Chart   | t          | t            | gpt-4o     | t               | t              | t
```

## 🐛 Troubleshooting

### Issue: Workflow Failed

If workflow fails, check logs:
```bash
# Check Airflow logs
docker logs airflow-webserver 2>&1 | grep ERROR

# Check specific task logs in Airflow UI
```

### Issue: Fields Still Null

**Possible causes:**

1. **Workflow ran before code changes**
   - Solution: Trigger a new workflow run after deployment

2. **XCom data missing**
   - Check: Airflow UI → Admin → XCom → Search for "artifact_id"
   - If missing: Chart tasks didn't store artifact IDs

3. **Update failed**
   - Check: Backend logs for "Failed to update chart artifacts"
   - Verify: Backend API is reachable from Airflow container

4. **Metadata not merged**
   - Issue: PATCH might overwrite instead of merge
   - Check: Full artifact in database vs API response

### Issue: Hydration Not Working

If old artifacts don't get hydrated:

1. **Check market_data table has data**
   ```sql
   SELECT COUNT(*) FROM market_data;
   ```

2. **Check codes table mapping**
   ```sql
   SELECT * FROM codes WHERE symbol = 'TSLA';
   ```

3. **Check for related LLM artifacts**
   ```sql
   SELECT id, type, symbol, execution_id 
   FROM artifacts 
   WHERE symbol = 'TSLA' 
   AND execution_id = '2025-11-13 13:09:57+00:00'
   ORDER BY created_at;
   ```

## ✅ Success Criteria

Feature is working correctly if:

1. ✅ New chart artifacts have all fields populated
   - prompt, response, model_name ≠ null
   - metadata.market_data_snapshot exists
   - metadata.indicator_summary exists  
   - metadata.llm_analysis exists

2. ✅ API returns complete context in single call
   - No need for /api/artifacts/{id}/market-data
   - All visualization data present

3. ✅ Old artifacts get hydrated
   - Legacy artifacts show enriched data via API
   - Fallback to market_data table works

4. ✅ Test script passes
   - 7/7 enrichment fields present
   - Market data and indicators displayed
   - LLM analysis available

## 📊 Current Status

Based on the Airflow log timestamp `[2025-11-15T05:13:43]`, the workflow started ~23 minutes ago and should be completing now.

**Next action:** Run the test script to verify enrichment!

```bash
python3 openspec/changes/add-chart-artifact-context/test_enrichment.py
```

If successful, you'll see a fully enriched TSLA Daily Chart artifact with all market data, indicators, and LLM analysis populated! 🎉
