# Complete Frontend User Guide - LLM Trading Platform

**Date**: 2025-10-19  
**Status**: ✅ **READY TO USE**

---

## 🎯 What's Available

You now have a complete frontend for **LLM-powered automatic trading** with:

1. ✅ **Workflow Trigger** - Start new workflow executions
2. ✅ **Workflow Monitoring** - Watch executions in real-time
3. ✅ **Workflow Tracing** - See every step with full details
4. ✅ **Interactive Visualization** - DAG graph of workflow lineage
5. ✅ **Real-Time Updates** - WebSocket streaming of logs

---

## 🚀 Quick Start (3 Steps)

### Step 1: Start the Backend

```bash
cd /Users/he/git/ibkr-trading-webui
source venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Start Celery Worker (New Terminal)

```bash
cd /Users/he/git/ibkr-trading-webui
source venv/bin/activate
celery -A backend.celery_app worker --loglevel=info
```

### Step 3: Open the Application

```
http://localhost:8000
```

---

## 📱 User Interface Guide

### 1. Workflows Page (`/workflows`)

**Purpose**: Trigger new workflows and view execution history

**Features**:
- **Execute Workflow Button** - Start a new workflow execution
- **Execution Cards** - Visual cards showing all executions
- **Filters** - Filter by strategy or status
- **Auto-Refresh** - Updates every 15 seconds if workflows are running

**How to Trigger a Workflow**:

1. Click **"Execute Workflow"** button (top right)
2. **Modal opens** with:
   - Strategy selector dropdown
   - Strategy details display (name, workflow, status, symbols)
   - Important notes about execution
3. **Select a strategy** from the dropdown
4. Review the strategy details that appear
5. Click **"Execute Workflow"** button in modal
6. **Automatically redirects** to the execution monitoring page

**What You'll See on Each Card**:
- Strategy name and workflow name
- Status badge (Running, Completed, Failed, Stopped, Pending)
- Started and completed timestamps
- Execution ID and Strategy ID
- Quick stats (if available): symbols processed, decisions made, orders placed
- "View Details →" link to monitoring page

### 2. Workflow Execution Page (`/workflows/executions/{id}`)

**Purpose**: Monitor a specific workflow execution in real-time

**Layout**:

#### Header Section
- **Strategy & Workflow Names**
- **Status Badge** - Color-coded by status:
  - 🔵 Blue: Running (with spinner)
  - ✅ Green: Completed
  - ❌ Red: Failed
  - 🟡 Yellow: Stopped
  - ⚪ Gray: Pending
- **Stop Button** - Stop running execution
- **Refresh Button** - Manually reload data

#### Metrics Cards
Four key metrics displayed:
1. **Duration** - How long the workflow has been running
2. **Total Steps** - Number of steps executed
3. **Failed Steps** - Count of failed steps (red if > 0)
4. **Success Rate** - Percentage of successful steps

#### Main Content Area

**Left Side - Workflow Lineage Visualization**:
- Interactive DAG (Directed Acyclic Graph)
- Each node represents a workflow step
- Color coding:
  - Green nodes: Successful steps
  - Red nodes: Failed steps
  - Blue nodes: Currently running
  - Gray nodes: Pending
- Click any node to see full details
- Edges show duration between steps
- Updates in real-time as workflow executes

**Right Side - Live Status Panel**:
- **WebSocket Status** - Shows "Connected" or "Disconnected"
- **Current Step** - Highlighted blue box showing active step
- **Recent Activity** - Last 5 steps with success/failure icons

#### Bottom Section - Execution Logs

**Logs Table** shows:
- **Time** - When the step executed
- **Step Name** - Descriptive name of the step
- **Type** - Color-coded badges:
  - 🔵 Blue: fetch_data
  - 🟣 Purple: ai_analysis
  - 🟡 Yellow: decision
  - 🟢 Green: order
  - ⚪ Gray: initialization
- **Symbol** - Trading symbol (TSLA, NVDA, etc.)
- **Duration** - How long the step took (in milliseconds)
- **Status** - ✓ success or ✗ failed
- **Actions** - 👁️ eye icon to view details

**Log Filtering**:
- **Filter by Type** - Show only specific step types
- **Filter by Status** - Show only success or failed steps
- **Export Button** - Download logs as JSON

**Log Detail Modal**:
Click the eye icon on any log entry to see:
- Complete step information
- Full input data (formatted JSON)
- Full output data (formatted JSON)
- Error message (if failed)
- Duration and timestamps
- Symbol/code information

### 3. Strategies Page (`/strategies`)

**Purpose**: Manage trading strategies

**Features**:
- List all strategies
- Create/Edit/Delete strategies
- **Execute button** on each strategy row
- Filter by active/inactive status

**Quick Execute**:
- Click the ▶️ play icon next to any active strategy
- Workflow execution starts immediately
- Confirmation prompt shown
- Redirects to execution monitoring page

---

## 🎬 Complete Workflow Tutorial

### Tutorial: Execute a Workflow for TSLA & NVDA

#### Step 1: Navigate to Workflows Page
```
http://localhost:8000/workflows
```

#### Step 2: Click "Execute Workflow"
The execute modal opens.

#### Step 3: Select Your Strategy
Choose "Test Multi-Code Strategy" (or your configured strategy)

You'll see:
```
Strategy Details:
- Strategy Name: Test Multi-Code Strategy
- Workflow: Two Indicator Strategy
- Status: Active
- Symbols: 2

Trading Symbols:
[TSLA] [NVDA]

Important Notes:
✓ This will execute the trading workflow
✓ All symbols will be processed sequentially
✓ LLM analysis will be performed
✓ Orders may be placed (based on mode)
✓ Monitor progress in real-time
```

#### Step 4: Click "Execute Workflow"
Button shows "Executing..." with spinner.

After 1-2 seconds:
- ✅ Success message appears
- Automatically redirects to monitoring page

#### Step 5: Watch Real-Time Execution

You're now on the execution monitoring page.

**What Happens**:

1. **Initial Steps** (5-10 seconds)
   - Lineage graph shows first nodes appearing
   - "Current Step" shows: "start_code_processing"
   - Logs table starts populating
   - WebSocket status: "Connected" ✓

2. **TSLA Processing** (2-3 minutes)
   ```
   fetch_daily_data (TSLA) → 30s
   fetch_weekly_data (TSLA) → 30s
   generate_daily_chart (TSLA) → 15s
   generate_weekly_chart (TSLA) → 15s
   ai_analysis_daily (TSLA) → 30s
   ai_analysis_weekly (TSLA) → 30s
   ai_consolidated_analysis (TSLA) → 20s
   decision_generation (TSLA) → 10s
   [optional] place_order (TSLA) → 5s
   ```

3. **60-Second Delay**
   - Log shows: "Waiting 60 seconds before next symbol"
   - Timer counts down in logs

4. **NVDA Processing** (2-3 minutes)
   - Same steps as TSLA
   - All logs append to table
   - Graph adds new branch for NVDA

5. **Completion** (1 second)
   - Status changes to "Completed" ✅
   - Final metrics update:
     ```
     Duration: 6m 23s
     Total Steps: 18
     Failed Steps: 0
     Success Rate: 100%
     ```

**During Execution, You Can**:
- ✅ Click any node in the graph to see details
- ✅ Filter logs by type or symbol
- ✅ Click eye icon to see full input/output
- ✅ Export logs at any time
- ✅ Stop execution with Stop button
- ✅ Watch metrics update in real-time

#### Step 6: Explore the Results

**Click on a Node**:
1. Click "ai_analysis_daily (TSLA)" node
2. Log detail modal opens showing:
   ```json
   {
     "step_name": "ai_analysis_daily",
     "step_type": "ai_analysis",
     "code": "TSLA",
     "input_data": {
       "chart_path": "/path/to/chart.png",
       "period": "1y",
       "bar": "1d"
     },
     "output_data": {
       "analysis": "Based on the daily chart...",
       "indicators": {...},
       "decision": "BUY",
       "confidence": 0.85
     },
     "duration_ms": 32450
   }
   ```

**Filter Logs**:
1. Select "ai_analysis" from Type dropdown
2. Table shows only AI analysis steps
3. See all LLM responses in one view

**Export Data**:
1. Click "Export" button
2. JSON file downloads: `workflow_logs_1_1729368123.json`
3. Open in text editor or analysis tool

---

## 🎨 Visual Guide

### Status Indicators

| Status | Color | Icon | Meaning |
|--------|-------|------|---------|
| Running | Blue | 🔵 ⟳ | Workflow executing |
| Completed | Green | ✅ | Successfully finished |
| Failed | Red | ❌ | Errors occurred |
| Stopped | Yellow | ⏹️ | User stopped |
| Pending | Gray | ⏱️ | Queued, not started |

### Step Type Colors

| Type | Color | Badge | Purpose |
|------|-------|-------|---------|
| fetch_data | Blue | 🔵 | Data retrieval from IBKR |
| ai_analysis | Purple | 🟣 | LLM chart analysis |
| decision | Yellow | 🟡 | Trading decision made |
| order | Green | 🟢 | Order placement |
| initialization | Gray | ⚪ | Setup/config steps |

---

## 🔍 Monitoring Features

### Real-Time Updates

**WebSocket Connection**:
- Automatically connects when you open execution page
- Status indicator shows connection state
- Reconnects automatically if disconnected
- Receives log events as they happen

**What Updates in Real-Time**:
1. ✅ New log entries appear instantly
2. ✅ Lineage graph adds new nodes
3. ✅ Metrics recalculate
4. ✅ Current step indicator changes
5. ✅ Recent activity list updates
6. ✅ Status badge changes when complete

**No Refresh Needed!**

### Tracing & Debugging

**Full Audit Trail**:
Every step logs:
- Complete input data
- Complete output data
- Success/failure status
- Error messages (if any)
- Execution duration
- Timestamp

**Common Debugging Scenarios**:

**Scenario 1: AI Analysis Failed**
1. Filter logs by "ai_analysis" type
2. Find failed entry (red row)
3. Click eye icon
4. Check error_message: "OpenAI API key invalid"
5. Fix API key in settings

**Scenario 2: No Orders Placed**
1. Filter logs by "decision" type
2. Check output_data for decision
3. See: `"action": "HOLD"` (not BUY/SELL)
4. Check AI analysis to understand why
5. Adjust strategy parameters if needed

**Scenario 3: Slow Execution**
1. Look at duration_ms for each step
2. Identify bottleneck (e.g., "ai_analysis: 60000ms")
3. Check if LLM is slow or timing out
4. Consider adjusting timeout parameters

---

## 📊 What Data You Can See

### For Each Workflow Execution:

**Summary Level**:
- Execution ID
- Strategy used
- Workflow used
- Status
- Start/end times
- Duration
- Total steps
- Success rate

**Detail Level**:
- Every single step executed
- Complete input for each step
- Complete output for each step
- Timing for each step
- Success/failure for each step
- Error messages for failures

**Example: AI Analysis Step**:
```json
{
  "step_name": "ai_analysis_daily",
  "step_type": "ai_analysis",
  "code": "TSLA",
  "conid": 76792991,
  "input_data": {
    "chart_path": "/tmp/charts/TSLA_1d_chart.png",
    "period": "1y",
    "bar": "1d",
    "prompt": "Analyze this daily chart..."
  },
  "output_data": {
    "analysis": "The daily chart shows strong uptrend...",
    "current_price": 221.86,
    "support_level": 215.00,
    "resistance_level": 230.00,
    "recommendation": "BUY",
    "confidence": 0.85,
    "reasoning": "Strong momentum with..."
  },
  "success": true,
  "duration_ms": 32450,
  "created_at": "2025-10-19T10:15:23Z"
}
```

---

## 🛠️ Advanced Features

### Filtering Workflows List

**By Strategy**:
1. Select strategy from dropdown
2. See only executions for that strategy
3. Track strategy performance over time

**By Status**:
1. Select "Running" to see active executions
2. Select "Failed" to troubleshoot issues
3. Select "Completed" to review history

### Exporting Data

**Export Logs**:
1. Open execution page
2. Apply any filters you want
3. Click "Export" button
4. Choose JSON format
5. File downloads with timestamp

**Use Exported Data For**:
- Offline analysis
- Importing to Excel/Google Sheets
- Custom reporting
- Sharing with team
- Compliance/audit

### Stopping Executions

**When to Stop**:
- Detected an error
- Want to adjust parameters
- Testing/debugging
- Emergency situations

**How to Stop**:
1. Click "Stop" button (top right)
2. Confirm the action
3. Execution status changes to "Stopped"
4. No more steps execute
5. Can still view all logs up to that point

---

## 💡 Tips & Best Practices

### Tip 1: Monitor First Execution Closely
**Why**: First execution reveals any configuration issues  
**How**: Keep execution page open, watch each step complete

### Tip 2: Use Filters to Debug
**Why**: Faster to find specific issues  
**How**: Filter by type "ai_analysis" to check all LLM responses

### Tip 3: Export Logs After Important Executions
**Why**: Creates backup for analysis  
**How**: Click Export after completion

### Tip 4: Check WebSocket Connection
**Why**: Ensures real-time updates work  
**How**: Look for "Connected" indicator (green)

### Tip 5: Review Success Rate
**Why**: Quick health check of execution  
**How**: Look at metrics card (should be near 100%)

### Tip 6: Multiple Browser Windows
**Why**: Monitor multiple executions simultaneously  
**How**: Open execution page in multiple tabs

### Tip 7: Use Recent Activity for Quick Debugging
**Why**: See last few steps without scrolling  
**How**: Check "Recent Steps" panel on right side

---

## 🎯 What to Look For

### Successful Execution Indicators:
- ✅ Status: Completed (green)
- ✅ Success Rate: 95-100%
- ✅ All critical steps present
- ✅ AI analysis steps completed
- ✅ Decisions generated
- ✅ Orders placed (if conditions met)

### Warning Signs:
- ⚠️ Success Rate < 90%
- ⚠️ Missing steps in lineage
- ⚠️ Long durations (> 5 minutes per symbol)
- ⚠️ Repeated errors in logs
- ⚠️ WebSocket disconnected

### Error Indicators:
- ❌ Status: Failed (red)
- ❌ Error messages in logs
- ❌ Red nodes in lineage graph
- ❌ Failed Steps > 0
- ❌ Incomplete execution

---

## 📱 Mobile Access

The interface is **fully responsive** and works on:
- ✅ Desktop browsers (Chrome, Firefox, Safari, Edge)
- ✅ Tablet devices (iPad, Android tablets)
- ✅ Mobile phones (iPhone, Android phones)

**Mobile Features**:
- Single-column layout
- Touch-friendly buttons
- Swipeable modals
- Responsive tables
- Collapsible sections

---

## 🔄 Auto-Refresh Behavior

**Workflows List Page**:
- Auto-refreshes every 15 seconds
- Only if at least one execution is running
- Reduces server load when idle

**Execution Page**:
- Real-time updates via WebSocket (instant)
- No polling needed
- More efficient than refreshing

---

## 📞 Troubleshooting

### Issue: Can't See Execute Button
**Solution**: Make sure you have at least one active strategy

### Issue: Execute Button Disabled
**Causes**:
- No strategy selected
- Selected strategy is inactive
**Solution**: Select active strategy or activate in Strategies page

### Issue: No Real-Time Updates
**Causes**:
- WebSocket disconnected
- Backend not running
- Network issues
**Solution**: 
1. Check WebSocket status indicator
2. Refresh the page
3. Check backend is running

### Issue: Lineage Graph Not Rendering
**Causes**:
- No logs available
- vis.js library not loaded
**Solution**:
1. Wait for first log entry
2. Check browser console for errors
3. Refresh the page

### Issue: Empty Workflows List
**Causes**:
- No workflows executed yet
- Filters too restrictive
**Solution**:
1. Execute a workflow
2. Reset filters
3. Check database connection

---

## 🎊 Summary

You now have a complete, production-ready frontend for:

1. ✅ **Triggering Workflows** - Easy modal with strategy selection
2. ✅ **Monitoring Executions** - Real-time updates with WebSocket
3. ✅ **Tracing Every Step** - Complete audit trail with full I/O
4. ✅ **Visualizing Workflow** - Interactive DAG graph
5. ✅ **Filtering & Searching** - Find specific logs quickly
6. ✅ **Exporting Data** - Download for offline analysis

**Everything works together seamlessly!**

---

## 🚀 Ready to Start

1. **Start the backend** (see Quick Start above)
2. **Open** http://localhost:8000/workflows
3. **Click** "Execute Workflow"
4. **Select** your strategy
5. **Watch** the magic happen! ✨

---

*Happy Trading! 📈*

---

**Need Help?**
- Review `START_HERE.md` for setup
- Check `QUICK_START_TESTING_GUIDE.md` for API testing
- See `LLM_TRADING_FRONTEND_IMPLEMENTATION_SUMMARY.md` for technical details

