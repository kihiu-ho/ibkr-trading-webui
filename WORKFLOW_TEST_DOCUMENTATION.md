<!-- markdownlint-disable -->
# Workflow Testing Documentation: TSLA & NVDA

## Overview

This document describes the comprehensive workflow testing system for processing multiple trading codes (TSLA and NVDA) through the IBKR trading workflow with full I/O logging.

**Created**: 2025-10-19
**Test Symbols**: TSLA (conid: 76792991), NVDA (conid: 4815747)

## What Was Built

### 1. Enhanced Database Schema

Added `workflow_logs` table for comprehensive I/O logging:

```sql
CREATE TABLE workflow_logs (
    id SERIAL PRIMARY KEY,
    workflow_execution_id INTEGER REFERENCES workflow_executions(id),
    step_name VARCHAR(100) NOT NULL,
    step_type VARCHAR(50) NOT NULL,
    code VARCHAR(50),
    conid INTEGER,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Location**: `database/init.sql`

### 2. Enhanced Workflow Processing

Updated workflow task system to:
- Process multiple codes per strategy sequentially
- Log every step with full input/output data
- Track execution time for each step
- Handle errors gracefully and continue processing remaining codes
- Add 60-second delay between processing different codes (as per spec)

**Location**: `backend/tasks/workflow_tasks.py`

Key functions:
- `_log_workflow_step()` - Logs every workflow step with I/O
- `_execute_workflow_for_multiple_codes()` - Orchestrates multi-code processing
- `_execute_workflow_for_code()` - Processes single code with full logging

### 3. SQLAlchemy Model

Created `WorkflowLog` model for Python access to logs.

**Location**: `backend/models/workflow_log.py`

### 4. Test Scripts

#### Python Test Script
**Location**: `scripts/test_workflow_tsla_nvda.py`

Features:
- Sets up test strategy with TSLA and NVDA
- Executes workflow
- Displays comprehensive logs
- Shows execution summary

#### SQL Setup Script
**Location**: `scripts/setup_test_strategy.sql`

Creates:
- Code records for TSLA and NVDA
- Test strategy "Test Multi-Code Strategy - TSLA & NVDA"
- Associations between strategy and codes

#### SQL Query Script
**Location**: `scripts/query_workflow_logs.sql`

Provides 10 different queries to analyze workflow logs:
1. Recent workflow executions
2. Detailed logs for latest execution
3. Summary statistics
4. AI analysis I/O
5. Decision outputs
6. Order placement results
7. Timeline for specific code
8. Full JSON export
9. Performance comparison
10. Error tracking

## Workflow Steps Logged

Each workflow execution logs the following steps for EACH code:

### Initialization Phase
- `workflow_start` - Workflow initialization
- `start_code_processing` - Begin processing specific code

### Data Fetching Phase  
- `fetch_daily_data` - Fetch daily historical data from IBKR
  - Input: symbol, conid, period, bar
  - Output: data_points count, response structure
  - Duration: ms
  
- `fetch_weekly_data` - Fetch weekly historical data from IBKR
  - Input: symbol, conid, period, bar
  - Output: data_points count, response structure
  - Duration: ms

### Chart Generation Phase
- `generate_daily_chart` - Create daily chart with indicators
  - Input: symbol, timeframe, data_points
  - Output: chart_url, chart_name
  - Duration: ms

- `generate_weekly_chart` - Create weekly chart with indicators
  - Input: symbol, timeframe, data_points
  - Output: chart_url, chart_name
  - Duration: ms

### AI Analysis Phase
- `analyze_daily_chart` - AI analysis of daily chart
  - Input: symbol, chart_url
  - Output: analysis_length, analysis_preview (first 500 chars)
  - Duration: ms

- `analyze_weekly_chart` - AI analysis of weekly chart
  - Input: symbol, chart_url
  - Output: analysis_length, analysis_preview (first 500 chars)
  - Duration: ms

- `consolidate_analysis` - Multi-timeframe consolidation
  - Input: daily_analysis_length, weekly_analysis_length
  - Output: consolidated_length, consolidated_preview
  - Duration: ms

### Decision Phase
- `generate_decision` - Generate structured trading decision
  - Input: symbol, strategy, analysis_length
  - Output: Full decision JSON (type, current_price, target_price, stop_loss, profit_margin, R_coefficient)
  - Duration: ms

- `save_decision` - Save decision to database
  - Input: symbol, decision_type
  - Output: decision_id, saved status
  - Duration: ms

### Order Phase
- `place_order` - Place order via IBKR (if buy/sell decision)
  - Input: symbol, conid, side, quantity, type
  - Output: order_id, ibkr_order_id, status
  - Duration: ms
  - OR
- `skip_order` - Log when order is skipped (hold decision)
  - Input: symbol, decision_type
  - Output: reason for skipping

### Completion Phase
- `complete_code_processing` - Mark code processing complete
  - Input: symbol, conid
  - Output: total_duration_ms, decision_id, order_id, completed_at

### Multi-Code Management
- `delay_between_codes` - 60-second delay between codes
  - Input: current_code, next_code
  - Output: delay_seconds

- `workflow_complete` - Overall workflow completion
  - Input: execution_id
  - Output: Full result summary

### Error Handling
- `code_processing_error` - Error processing specific code
- `workflow_error` - Critical workflow error

## How to Use

### Method 1: Python Script (Recommended)

1. **Setup test data and execute workflow:**

```bash
cd /Users/he/git/ibkr-trading-webui
python scripts/test_workflow_tsla_nvda.py
```

This script will:
- Create/verify workflow, codes, and strategy
- Ask for confirmation before execution
- Execute workflow for both TSLA and NVDA
- Display comprehensive logs
- Show execution summary

Expected output:
```
================================================================================
IBKR TRADING WORKFLOW TEST - TSLA & NVDA
================================================================================

Timestamp: 2025-10-19T...

================================================================================
SETTING UP TEST DATA
================================================================================

✓ Workflow: Two Indicator Strategy (ID: 1)
✓ TSLA: TSLA (conid: 76792991, ID: 1)
✓ NVDA: NVDA (conid: 4815747, ID: 2)
✓ Strategy: Test Multi-Code Strategy - TSLA & NVDA (ID: 1, Workflow ID: 1)
✓ Strategy has 2 codes associated:
  - TSLA (conid: 76792991)
  - NVDA (conid: 4815747)

================================================================================
Proceed with workflow execution? (yes/no): yes

================================================================================
EXECUTING WORKFLOW
================================================================================
...
```

### Method 2: SQL Setup + API Call

1. **Setup test data:**

```bash
psql -U postgres -d ibkr_trading -f scripts/setup_test_strategy.sql
```

2. **Execute workflow via API:**

```bash
curl -X POST http://localhost:8000/api/workflows/execute \
  -H "Content-Type: application/json" \
  -d '{"strategy_id": 1}'
```

3. **Query logs:**

```bash
psql -U postgres -d ibkr_trading -f scripts/query_workflow_logs.sql
```

### Method 3: Direct Database Queries

**View recent executions:**
```sql
SELECT * FROM workflow_executions 
ORDER BY started_at DESC 
LIMIT 5;
```

**View logs for specific execution:**
```sql
SELECT 
    step_name, 
    step_type, 
    code, 
    success, 
    duration_ms,
    created_at
FROM workflow_logs 
WHERE workflow_execution_id = <execution_id>
ORDER BY created_at;
```

**View all I/O for TSLA:**
```sql
SELECT 
    step_name,
    input_data,
    output_data,
    duration_ms
FROM workflow_logs
WHERE code = 'TSLA'
ORDER BY created_at;
```

**Export full logs as JSON:**
```sql
SELECT jsonb_pretty(
    jsonb_agg(
        jsonb_build_object(
            'step', step_name,
            'type', step_type,
            'code', code,
            'input', input_data,
            'output', output_data,
            'duration_ms', duration_ms
        ) ORDER BY created_at
    )
) FROM workflow_logs
WHERE workflow_execution_id = <execution_id>;
```

## Expected Results

### Successful Execution

For each symbol (TSLA and NVDA), the workflow should:

1. ✓ Fetch daily historical data (1y, 1d bars)
2. ✓ Fetch weekly historical data (5y, 1w bars)
3. ✓ Generate daily chart with indicators
4. ✓ Generate weekly chart with indicators
5. ✓ Upload charts to storage (MinIO)
6. ✓ Analyze daily chart with AI
7. ✓ Analyze weekly chart with AI
8. ✓ Consolidate multi-timeframe analysis
9. ✓ Generate trading decision (buy/sell/hold)
10. ✓ Save decision to database
11. ✓ Place order (if buy/sell) or skip (if hold)
12. ✓ Wait 60 seconds before next symbol

### Logged Data

Each step logs:
- **Input parameters**: What data went into the step
- **Output results**: What data came out of the step
- **Duration**: How long the step took (in milliseconds)
- **Success status**: Whether the step succeeded or failed
- **Error message**: If failed, what went wrong

### Example Log Entry

```json
{
  "step_name": "analyze_daily_chart",
  "step_type": "ai_analysis",
  "code": "TSLA",
  "conid": 76792991,
  "input_data": {
    "symbol": "TSLA",
    "chart_url": "http://minio:9000/charts/TSLA_daily_20251019_143025.png"
  },
  "output_data": {
    "analysis_length": 2847,
    "analysis_preview": "## 1. Core Price Analysis\n\nTesla (TSLA) is currently trading at..."
  },
  "success": true,
  "duration_ms": 4523,
  "created_at": "2025-10-19T14:30:29.456Z"
}
```

## Performance Expectations

### Timing
- **Per Symbol**: 2-5 minutes (depending on AI response times)
- **Total for 2 Symbols**: 5-12 minutes (includes 60s delay between symbols)

### Resource Usage
- **Database**: ~20-30 log entries per symbol
- **Storage**: 2 chart images per symbol (~200KB each)
- **AI API**: 3 calls per symbol (daily, weekly, consolidation)

## Troubleshooting

### Common Issues

**1. "Strategy not found"**
- Run `scripts/setup_test_strategy.sql` first
- OR run `scripts/test_workflow_tsla_nvda.py` which auto-creates strategy

**2. "No codes associated with strategy"**
- Check `strategy_codes` table
- Verify many-to-many associations exist

**3. "IBKR authentication failed"**
- Ensure IBKR Gateway/TWS is running
- Check IBKR API is accessible at configured URL
- Verify account credentials

**4. "Chart generation failed"**
- Check MinIO storage is running
- Verify storage credentials in settings
- Check chart service dependencies (matplotlib, pandas)

**5. "AI analysis failed"**
- Verify OpenAI/LLM API key is configured
- Check API endpoint is accessible
- Verify model name is correct

### Debug Queries

**Find failed steps:**
```sql
SELECT * FROM workflow_logs 
WHERE success = FALSE 
ORDER BY created_at DESC;
```

**Check execution status:**
```sql
SELECT id, status, started_at, completed_at, error
FROM workflow_executions
ORDER BY started_at DESC
LIMIT 10;
```

**View error details:**
```sql
SELECT 
    step_name,
    code,
    error_message,
    input_data,
    created_at
FROM workflow_logs
WHERE success = FALSE
ORDER BY created_at DESC;
```

## Database Schema Reference

### Key Tables

**workflow_executions**
- Tracks each workflow run
- Links to strategy and workflow
- Stores overall status and results

**workflow_logs**
- Comprehensive step-by-step logging
- Full I/O data in JSONB format
- Duration and success tracking

**strategies**
- Strategy configuration
- Links to workflow template
- Parameters for execution

**strategy_codes**
- Many-to-many association
- Links strategies to codes

**codes**
- Financial instrument data
- Symbol, conid, exchange

**decisions**
- AI-generated trading decisions
- Links to code and strategy

**orders**
- Order placement records
- Links to decision and strategy

## API Endpoints

### Execute Workflow

```http
POST /api/workflows/execute
Content-Type: application/json

{
  "strategy_id": 1
}
```

Response:
```json
{
  "execution_id": 123,
  "status": "running",
  "message": "Workflow execution started"
}
```

### Check Status

```http
GET /api/workflows/executions/{execution_id}
```

Response:
```json
{
  "id": 123,
  "strategy_id": 1,
  "workflow_id": 1,
  "status": "completed",
  "started_at": "2025-10-19T14:30:00Z",
  "completed_at": "2025-10-19T14:42:15Z",
  "result": {
    "codes_processed": [...],
    "codes_failed": [],
    "summary": {...}
  }
}
```

### Query Logs

```http
GET /api/workflows/executions/{execution_id}/logs
```

Response:
```json
{
  "execution_id": 123,
  "logs": [
    {
      "step_name": "fetch_daily_data",
      "step_type": "fetch_data",
      "code": "TSLA",
      "success": true,
      "duration_ms": 1234,
      "input_data": {...},
      "output_data": {...}
    },
    ...
  ]
}
```

## Conclusion

This testing system provides comprehensive visibility into workflow execution, enabling:

1. **Debugging**: Trace exact inputs/outputs at each step
2. **Performance Analysis**: Identify bottlenecks and optimize
3. **Audit Trail**: Full record of all trading decisions and actions
4. **Validation**: Verify workflow operates according to spec
5. **Monitoring**: Track success rates and error patterns

All I/O is automatically logged to the `workflow_logs` table and can be queried using the provided SQL scripts or Python tools.

---

**Next Steps**:
1. Run the test script: `python scripts/test_workflow_tsla_nvda.py`
2. Review the logs in the database
3. Analyze decision outputs and order results
4. Verify workflow behavior matches specifications

