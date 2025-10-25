# Quick Start Testing Guide - LLM Trading Frontend

**Last Updated**: 2025-10-19  
**Purpose**: Guide for testing the new LLM trading frontend features

---

## Prerequisites

1. **Database**: PostgreSQL running with updated schema
2. **Backend Dependencies**: All Python packages installed
3. **IBKR Gateway**: Running (for actual trading workflow)
4. **Test Data**: Strategies and codes configured

---

## Setup Steps

### 1. Ensure Database is Up-to-Date

The database schema should include the new `workflow_logs` table from `database/init.sql`:

```bash
# If you haven't applied the schema updates
psql -U your_user -d your_database -f database/init.sql
```

### 2. Install Backend Dependencies

```bash
cd /Users/he/git/ibkr-trading-webui
source venv/bin/activate  # Or: . venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Start the Backend Server

```bash
cd /Users/he/git/ibkr-trading-webui
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 4. Start Celery Worker (for workflow execution)

In a **new terminal**:

```bash
cd /Users/he/git/ibkr-trading-webui
source venv/bin/activate
celery -A backend.celery_app worker --loglevel=info
```

---

## Testing Workflow Execution Page

### Option A: Using Existing Test Data

If you've already run the TSLA/NVDA workflow test:

1. Find an execution ID:
   ```bash
   # Query the database
   psql -U your_user -d your_database -c "SELECT id, strategy_id, status, started_at FROM workflow_executions ORDER BY started_at DESC LIMIT 5;"
   ```

2. Open the workflow execution page:
   ```
   http://localhost:8000/workflows/executions/{execution_id}
   ```
   Replace `{execution_id}` with an actual ID (e.g., `1`)

3. **What to Check**:
   - ✅ Page loads with execution details
   - ✅ Metrics display (duration, steps, success rate)
   - ✅ Workflow lineage graph renders
   - ✅ Logs table populates
   - ✅ WebSocket connection status shows "Connected"

### Option B: Execute a New Workflow

1. **Ensure test data exists**:
   ```bash
   # Run the setup script if you haven't
   cd /Users/he/git/ibkr-trading-webui
   psql -U your_user -d your_database -f scripts/setup_test_strategy.sql
   ```

2. **Trigger a workflow** via API:
   ```bash
   # Find a strategy ID
   curl http://localhost:8000/api/strategies
   
   # Execute the strategy (replace {strategy_id})
   curl -X POST http://localhost:8000/api/strategies/{strategy_id}/execute
   ```
   
   Response will include:
   ```json
   {
     "message": "Workflow execution started",
     "strategy_id": 1,
     "task_id": "abc-123-def-456"
   }
   ```

3. **Find the execution ID**:
   ```bash
   curl http://localhost:8000/api/workflows/executions
   ```
   
   Look for the most recent execution and note its `id`.

4. **Open the execution page**:
   ```
   http://localhost:8000/workflows/executions/{execution_id}
   ```

5. **Watch in Real-Time**:
   - Logs should appear as they're generated
   - Lineage graph should update with new nodes
   - Metrics should update automatically
   - Current step indicator should change
   - Recent activity list should update

---

## Testing API Endpoints

### Test Workflow Execution Endpoints

```bash
# List all executions
curl http://localhost:8000/api/workflows/executions

# Get specific execution
curl http://localhost:8000/api/workflows/executions/1

# Get execution logs
curl http://localhost:8000/api/workflows/executions/1/logs

# Get execution logs filtered by step_type
curl "http://localhost:8000/api/workflows/executions/1/logs?step_type=ai_analysis"

# Get execution lineage
curl http://localhost:8000/api/workflows/executions/1/lineage
```

### Test Log Endpoints

```bash
# Query all logs
curl http://localhost:8000/api/logs

# Query logs with filters
curl "http://localhost:8000/api/logs?step_type=fetch_data&success=true"

# Get log statistics
curl http://localhost:8000/api/logs/statistics

# Get specific log detail
curl http://localhost:8000/api/logs/1

# Export logs as JSON
curl "http://localhost:8000/api/logs/export?format=json&workflow_execution_id=1" > logs.json

# Export logs as CSV
curl "http://localhost:8000/api/logs/export?format=csv&workflow_execution_id=1" > logs.csv
```

### Test Strategy Validation

```bash
# Validate strategy parameters
curl -X POST http://localhost:8000/api/strategies/1/validate-params
```

Expected response:
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "delay_between_symbols < 10s may trigger rate limits"
  ],
  "parameters": {...},
  "symbols_count": 2
}
```

---

## Testing WebSocket Connection

### Using Browser Console

1. Open the workflow execution page
2. Open browser DevTools (F12)
3. Go to Console tab
4. Look for WebSocket messages:
   ```
   WebSocket connected
   Subscribed to execution: 1
   New log received: fetch_daily_data
   ```

### Using wscat (command line)

```bash
# Install wscat if you don't have it
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/logs

# After connection, subscribe to an execution
> {"command": "subscribe", "execution_id": 1}

# You should receive subscription confirmation
< {"type": "subscription_confirmed", "execution_id": 1}

# If the workflow is running, you'll receive log events
< {"workflow_execution_id": 1, "step_name": "fetch_daily_data", ...}
```

---

## Feature Testing Checklist

### Workflow Execution Page

- [ ] Page loads successfully
- [ ] Execution details display correctly
  - [ ] Strategy name
  - [ ] Workflow name
  - [ ] Status badge (with correct color)
  - [ ] Start time
- [ ] Metrics cards show accurate data
  - [ ] Duration
  - [ ] Total steps
  - [ ] Failed steps
  - [ ] Success rate
- [ ] Workflow lineage visualization
  - [ ] Graph renders
  - [ ] Nodes are color-coded by status
  - [ ] Edges show duration labels
  - [ ] Nodes are clickable
  - [ ] Click opens log detail modal
- [ ] Live status sidebar
  - [ ] WebSocket status shows "Connected"
  - [ ] Current step displays (if running)
  - [ ] Recent steps list updates
- [ ] Logs table
  - [ ] All logs display
  - [ ] Color coding by step type
  - [ ] Failed rows highlighted
  - [ ] Time formatting correct
- [ ] Log filtering
  - [ ] Filter by step type works
  - [ ] Filter by success/failed works
  - [ ] Filters combine properly
- [ ] Log detail modal
  - [ ] Opens on "eye" icon click
  - [ ] Shows all log details
  - [ ] Input/Output JSON formatted
  - [ ] Error message displayed (if failed)
  - [ ] Close button works
- [ ] Real-time updates (if workflow is running)
  - [ ] New logs appear automatically
  - [ ] Lineage graph updates
  - [ ] Metrics update
  - [ ] Current step updates
- [ ] Export functionality
  - [ ] Export button triggers download
  - [ ] JSON file downloads
  - [ ] Filename includes timestamp
- [ ] Controls
  - [ ] Stop button (if running)
  - [ ] Refresh button reloads data
- [ ] Toast notifications
  - [ ] Appear for actions
  - [ ] Auto-dismiss after 3 seconds

### API Endpoints

- [ ] All workflow endpoints return correct data
- [ ] Filtering works on logs endpoint
- [ ] Export endpoints generate correct files
- [ ] Statistics endpoint returns metrics
- [ ] Validation endpoint catches errors
- [ ] Pagination works correctly

### WebSocket

- [ ] Connection establishes on page load
- [ ] Subscribe command works
- [ ] Logs stream in real-time
- [ ] Reconnection works after disconnect
- [ ] Multiple clients can connect

---

## Common Issues & Troubleshooting

### Issue: "Failed to load execution"

**Cause**: Execution ID doesn't exist or database connection failed

**Solution**:
1. Check execution ID is valid: `curl http://localhost:8000/api/workflows/executions`
2. Check database connection in backend logs
3. Verify DATABASE_URL environment variable

### Issue: WebSocket shows "Disconnected"

**Cause**: WebSocket connection failed or backend not running

**Solution**:
1. Check backend is running: `http://localhost:8000/health`
2. Check browser console for WebSocket errors
3. Verify firewall isn't blocking WebSocket connections
4. Try refreshing the page

### Issue: Lineage graph doesn't render

**Cause**: vis.js library not loaded or no logs available

**Solution**:
1. Check browser console for JavaScript errors
2. Verify vis.js CDN is accessible
3. Check if logs exist: `curl http://localhost:8000/api/workflows/executions/1/logs`
4. Wait a few seconds for initial load

### Issue: Logs not appearing in real-time

**Cause**: WebSocket not connected or workflow not running

**Solution**:
1. Check WebSocket status indicator
2. Check browser console for errors
3. Verify workflow is actually running: `curl http://localhost:8000/api/workflows/executions/1`
4. Try reconnecting WebSocket (refresh page)

### Issue: "No logs available"

**Cause**: Workflow hasn't generated any logs yet or execution hasn't started

**Solution**:
1. Check execution status
2. Check Celery worker is running
3. Check backend logs for errors
4. Verify workflow task actually started

---

## Performance Testing

### Test with Large Number of Logs

```bash
# This will create a lot of logs
python scripts/test_workflow_tsla_nvda.py
```

**What to Check**:
- [ ] Page loads in < 3 seconds
- [ ] Scroll is smooth
- [ ] Filtering is responsive (< 500ms)
- [ ] Graph renders in < 5 seconds
- [ ] WebSocket remains stable

### Test with Multiple Concurrent Users

1. Open execution page in multiple browser tabs/windows
2. All should connect via WebSocket
3. All should receive real-time updates
4. Performance should remain acceptable

---

## Next Steps After Testing

1. **If Issues Found**: 
   - Document them
   - Check backend logs
   - Check browser console
   - Create bug reports

2. **If Tests Pass**:
   - Proceed to implement parameter editor
   - Enhance dashboard with real-time cards
   - Create standalone log viewer page

3. **Gather Feedback**:
   - User experience
   - Performance observations
   - Feature requests
   - UI/UX improvements

---

## Quick Reference

### URLs
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Workflow Execution**: http://localhost:8000/workflows/executions/{id}
- **Dashboard**: http://localhost:8000/dashboard
- **Strategies**: http://localhost:8000/strategies

### Key Files
- **Backend APIs**: `backend/api/workflows.py`, `backend/api/logs.py`
- **Frontend Page**: `frontend/templates/workflows/execution.html`
- **Frontend JS**: `frontend/static/js/workflow-execution.js`
- **WebSocket**: `backend/main.py` (ConnectionManager class)

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
OPENAI_API_KEY=your_api_key
IBKR_GATEWAY_URL=https://localhost:5055
```

---

## Support

For issues or questions:
1. Check backend logs
2. Check browser console
3. Review implementation summary: `LLM_TRADING_FRONTEND_IMPLEMENTATION_SUMMARY.md`
4. Review OpenSpec specs: `openspec/changes/add-llm-trading-frontend/`

---

**Happy Testing! 🚀**

*Last Updated: 2025-10-19*

