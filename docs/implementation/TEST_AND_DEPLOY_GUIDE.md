# Test and Deploy Guide - LLM Trading Frontend

**Date**: 2025-10-19  
**OpenSpec Status**: 25/42 tasks complete (60%)  
**Status**: ✅ **Core Features Ready for Testing**

---

## 🎯 What's Been Built

### OpenSpec Progress

```
add-llm-trading-frontend: 25/42 tasks complete
├── Backend API Enhancements: 6/6 ✅ COMPLETE
├── Workflow Visualization: 5/5 ✅ COMPLETE
├── Logging Viewer: 5/5 ✅ COMPLETE
├── Parameter Editor: 2/5 ⚠️ PARTIAL (API only)
├── Dashboard Enhancement: 0/5 ⏳ DEFERRED
├── Workflow Execution Page: 5/5 ✅ COMPLETE
├── Testing: 0/7 🔄 READY TO START
└── Documentation: 2/4 ✅ MOSTLY COMPLETE
```

### Core Features Implemented (100% Ready)

1. **Trigger Workflows** ✅
   - Modal-based workflow execution
   - Strategy selection
   - Validation before execution
   - Auto-redirect to monitoring

2. **Monitor Workflows** ✅
   - Real-time status updates
   - Live metrics dashboard
   - WebSocket integration
   - Execution controls

3. **Trace Workflows** ✅
   - Interactive DAG visualization
   - Complete log viewer
   - I/O inspection
   - Export functionality

---

## 🚀 Quick Start Testing

### Option 1: Automated Test Script

```bash
cd /Users/he/git/ibkr-trading-webui

# Start backend (Terminal 1)
source venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start worker (Terminal 2)
source venv/bin/activate
celery -A backend.celery_app worker --loglevel=info

# Run automated tests (Terminal 3)
./tests/test_frontend_features.sh
```

The automated script tests:
- ✅ Backend availability
- ✅ All workflow API endpoints
- ✅ All log API endpoints
- ✅ All strategy API endpoints
- ✅ Frontend page loading
- ✅ Static assets

### Option 2: Manual Browser Testing

**Step 1**: Start the application
```bash
# Terminal 1: Backend
cd /Users/he/git/ibkr-trading-webui
source venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Worker
cd /Users/he/git/ibkr-trading-webui
source venv/bin/activate
celery -A backend.celery_app worker --loglevel=info
```

**Step 2**: Open browser
```
http://localhost:8000/workflows
```

**Step 3**: Execute a workflow
1. Click "Execute Workflow"
2. Select a strategy
3. Click "Execute Workflow" button
4. Watch real-time monitoring

---

## 🧪 Comprehensive Test Plan

### Phase 1: API Testing (Automated)

**Run**: `./tests/test_frontend_features.sh`

**Tests**:
- ✅ GET /api/workflows
- ✅ GET /api/workflows/executions
- ✅ GET /api/workflows/executions/{id}
- ✅ GET /api/workflows/executions/{id}/logs
- ✅ GET /api/workflows/executions/{id}/lineage
- ✅ GET /api/logs
- ✅ GET /api/logs/statistics
- ✅ GET /api/strategies
- ✅ GET /api/strategies/{id}
- ✅ POST /api/strategies/{id}/validate-params

**Expected Results**: All endpoints return 200 with valid JSON

### Phase 2: Frontend UI Testing (Manual)

#### Test 2.1: Workflows List Page

**URL**: `http://localhost:8000/workflows`

**Checklist**:
- [ ] Page loads without errors
- [ ] Execution cards display (if any exist)
- [ ] "Execute Workflow" button visible
- [ ] Filters work (Strategy, Status)
- [ ] Auto-refresh works (every 15s)
- [ ] Click "View Details →" navigates correctly

#### Test 2.2: Execute Workflow Modal

**Steps**:
1. Click "Execute Workflow"

**Checklist**:
- [ ] Modal opens
- [ ] Strategy dropdown populates
- [ ] Selecting strategy shows details
- [ ] Strategy details accurate (name, symbols, status)
- [ ] Execute button disabled if inactive strategy
- [ ] Execute button triggers execution
- [ ] Success message appears
- [ ] Auto-redirects to execution page

#### Test 2.3: Workflow Execution Page

**URL**: `http://localhost:8000/workflows/executions/{id}`

**Checklist**:
- [ ] Page loads with execution data
- [ ] Status badge shows correct state
- [ ] Metrics display (Duration, Steps, Success Rate)
- [ ] WebSocket connects (shows "Connected")
- [ ] Lineage graph renders
- [ ] Logs table populates
- [ ] Current step indicator works

#### Test 2.4: Real-Time Updates

**Prerequisites**: Run a workflow that takes >30 seconds

**Checklist**:
- [ ] New logs appear automatically
- [ ] No page refresh needed
- [ ] Graph updates with new nodes
- [ ] Metrics update live
- [ ] Current step changes
- [ ] Recent activity updates

#### Test 2.5: Interactive Visualization

**Checklist**:
- [ ] Click node → detail modal opens
- [ ] Modal shows input/output JSON
- [ ] Node colors match status (green/red/blue/gray)
- [ ] Edges show duration
- [ ] Graph is zoomable/pannable

#### Test 2.6: Log Filtering

**Checklist**:
- [ ] Filter by step_type works
- [ ] Filter by success/failed works
- [ ] Filters combine correctly
- [ ] Filter state persists
- [ ] Reset filters works

#### Test 2.7: Log Detail Inspection

**Checklist**:
- [ ] Click eye icon → modal opens
- [ ] Input data displays as formatted JSON
- [ ] Output data displays as formatted JSON
- [ ] Error message shows (if failed)
- [ ] Duration and timestamps correct
- [ ] Close button works

#### Test 2.8: Export Functionality

**Checklist**:
- [ ] Export button triggers download
- [ ] JSON file downloads
- [ ] Filename includes timestamp
- [ ] JSON is valid and complete
- [ ] Current filters reflected in export

#### Test 2.9: Execution Controls

**Checklist**:
- [ ] Stop button available (if running)
- [ ] Stop button stops execution
- [ ] Status changes to "Stopped"
- [ ] Refresh button reloads data
- [ ] Toast notifications appear

### Phase 3: WebSocket Testing (Manual)

**Using wscat**:
```bash
# Install wscat if needed
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/logs

# Subscribe to execution
> {"command": "subscribe", "execution_id": 1}

# Should receive confirmation
< {"type": "subscription_confirmed", "execution_id": 1}

# Should receive log events (if workflow running)
< {"workflow_execution_id": 1, "step_name": "...", ...}
```

**Checklist**:
- [ ] WebSocket connects successfully
- [ ] Subscribe command works
- [ ] Subscription confirmed
- [ ] Log events received in real-time
- [ ] Unsubscribe works
- [ ] Ping/pong works

### Phase 4: Performance Testing

#### Test 4.1: Large Dataset Performance

**Setup**: Create execution with 100+ log entries

**Checklist**:
- [ ] Page loads in < 3 seconds
- [ ] Scroll is smooth
- [ ] Filtering is responsive (< 500ms)
- [ ] Graph renders in < 5 seconds
- [ ] Export completes in < 10 seconds

#### Test 4.2: Multiple Concurrent Users

**Setup**: Open execution page in 5 browser tabs

**Checklist**:
- [ ] All tabs connect via WebSocket
- [ ] All tabs receive updates
- [ ] No performance degradation
- [ ] Server remains stable

#### Test 4.3: Long-Running Workflow

**Setup**: Execute workflow that runs > 10 minutes

**Checklist**:
- [ ] WebSocket stays connected
- [ ] Updates continue throughout
- [ ] No memory leaks in browser
- [ ] Page remains responsive

### Phase 5: Error Handling Testing

#### Test 5.1: Network Errors

**Checklist**:
- [ ] Graceful handling of failed API calls
- [ ] Error messages displayed
- [ ] Retry mechanisms work
- [ ] WebSocket reconnects automatically

#### Test 5.2: Invalid Data

**Checklist**:
- [ ] Invalid execution ID shows error
- [ ] Missing data handled gracefully
- [ ] Empty states display correctly

#### Test 5.3: Backend Failures

**Setup**: Stop backend while viewing execution

**Checklist**:
- [ ] WebSocket shows "Disconnected"
- [ ] Appropriate error messages
- [ ] UI remains functional
- [ ] Reconnects when backend returns

---

## 📊 Test Results Template

### Test Execution Summary

```
Date: _______________
Tester: _______________
Environment: _______________

Phase 1: API Testing
- Tests Run: ___
- Tests Passed: ___
- Tests Failed: ___

Phase 2: Frontend UI Testing
- Tests Run: ___
- Tests Passed: ___
- Tests Failed: ___

Phase 3: WebSocket Testing
- Tests Run: ___
- Tests Passed: ___
- Tests Failed: ___

Phase 4: Performance Testing
- Tests Run: ___
- Tests Passed: ___
- Tests Failed: ___

Phase 5: Error Handling Testing
- Tests Run: ___
- Tests Passed: ___
- Tests Failed: ___

Overall Result: PASS / FAIL
```

### Issues Found

```
Issue #1:
- Description: _______________
- Steps to Reproduce: _______________
- Expected: _______________
- Actual: _______________
- Severity: Critical / High / Medium / Low
- Status: Open / Fixed

[Add more issues as needed]
```

---

## 🚢 Deployment Checklist

### Pre-Deployment

- [ ] All tests passed
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Database schema updated
- [ ] Dependencies installed
- [ ] Environment variables set
- [ ] SSL certificates configured (if needed)

### Deployment Steps

1. **Update Database**:
   ```sql
   psql -U your_user -d your_database -f database/init.sql
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Start Services**:
   ```bash
   # Backend
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   
   # Worker
   celery -A backend.celery_app worker --loglevel=info
   ```

4. **Verify Health**:
   ```bash
   curl http://localhost:8000/health
   ```

5. **Smoke Test**:
   - Open http://localhost:8000/workflows
   - Execute a test workflow
   - Verify real-time updates work

### Post-Deployment

- [ ] Monitor logs for errors
- [ ] Check WebSocket connections
- [ ] Verify database connections
- [ ] Test workflow execution
- [ ] Monitor performance metrics

---

## 🐛 Troubleshooting

### Issue: Backend Won't Start

**Symptoms**: uvicorn fails to start

**Solutions**:
1. Check Python version: `python --version` (need 3.11+)
2. Activate venv: `source venv/bin/activate`
3. Install dependencies: `pip install -r backend/requirements.txt`
4. Check port 8000: `lsof -i :8000`

### Issue: WebSocket Won't Connect

**Symptoms**: Shows "Disconnected" in UI

**Solutions**:
1. Check backend is running
2. Check firewall settings
3. Try different browser
4. Check browser console for errors
5. Verify WebSocket endpoint: `wscat -c ws://localhost:8000/ws/logs`

### Issue: No Workflows Listed

**Symptoms**: Empty workflows list

**Solutions**:
1. Check database connection
2. Verify database has data: `SELECT * FROM workflow_executions;`
3. Check API endpoint: `curl http://localhost:8000/api/workflows/executions`
4. Check backend logs for errors

### Issue: Real-Time Updates Not Working

**Symptoms**: Logs don't appear automatically

**Solutions**:
1. Check WebSocket status indicator
2. Refresh the page
3. Check Celery worker is running
4. Verify workflow is actually executing
5. Check backend logs

### Issue: Graph Doesn't Render

**Symptoms**: Empty visualization area

**Solutions**:
1. Check browser console for errors
2. Verify vis.js CDN is accessible
3. Wait for logs to appear
4. Check if execution has any logs
5. Try different browser

---

## 📈 Performance Benchmarks

### Expected Performance

| Metric | Target | Acceptable |
|--------|--------|------------|
| Page Load Time | < 1s | < 3s |
| API Response Time | < 100ms | < 500ms |
| WebSocket Latency | < 50ms | < 200ms |
| Graph Render Time | < 2s | < 5s |
| Log Export Time (1000 entries) | < 5s | < 15s |
| Filter Response Time | < 200ms | < 500ms |

### Monitoring

**Key Metrics to Track**:
- API response times
- WebSocket connection count
- Active workflow executions
- Database query performance
- Memory usage
- CPU usage

---

## ✅ Sign-Off

### Development Complete

- [x] Core features implemented
- [x] OpenSpec validated
- [x] Documentation created
- [x] Test scripts created

**Developer**: AI Assistant  
**Date**: 2025-10-19

### Testing Complete

- [ ] All automated tests passed
- [ ] All manual tests passed
- [ ] Performance acceptable
- [ ] No critical bugs

**Tester**: _______________  
**Date**: _______________

### Deployment Approved

- [ ] Tests passed
- [ ] Documentation reviewed
- [ ] Deployment plan reviewed
- [ ] Ready for production

**Approver**: _______________  
**Date**: _______________

---

## 📚 Additional Resources

- **User Guide**: `FRONTEND_COMPLETE_USER_GUIDE.md`
- **Quick Start**: `README_FRONTEND_READY.md`
- **API Testing**: `QUICK_START_TESTING_GUIDE.md`
- **Implementation Details**: `COMPLETE_FRONTEND_IMPLEMENTATION.md`
- **OpenSpec Specs**: `openspec/changes/add-llm-trading-frontend/`

---

**Status**: ✅ **Ready for Comprehensive Testing**

Run `./tests/test_frontend_features.sh` to begin automated testing!

