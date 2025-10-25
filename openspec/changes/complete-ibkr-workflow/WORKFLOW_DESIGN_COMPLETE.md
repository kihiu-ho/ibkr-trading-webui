# Complete IBKR Trading Workflow - Design Complete ✅

## Summary

The complete IBKR trading workflow has been fully designed using OpenSpec, including the **lineage tracking** feature for full transparency of input/output at each workflow step.

---

## What Was Created

### 1. OpenSpec Documentation
- ✅ **proposal.md** - Complete project proposal with benefits, risks, and timeline
- ✅ **design.md** - Comprehensive technical design (2,000+ lines)
- ✅ **tasks.md** - Detailed implementation checklist (~250 tasks across 9 phases)
- ✅ **spec.md** files - Requirements and scenarios for 4 new capabilities

### 2. Capability Spec Deltas
- ✅ **workflow-execution/spec.md** - Complete workflow execution with scheduling
- ✅ **order-management/spec.md** - Automated order placement and tracking
- ✅ **portfolio-management/spec.md** - Real-time portfolio and P&L tracking
- ✅ **lineage-tracking/spec.md** - Step-by-step execution lineage with input/output

### 3. Validation
- ✅ OpenSpec validation passed with `--strict` flag

---

## Complete Workflow Steps (13 Total)

1. **User Authentication** → IBKR login/session management
2. **Symbol Search** → Search symbols, get contract IDs (conid)
3. **Indicator Setup** → Configure technical indicators (RSI, MACD, ATR, etc.)
4. **Prompt Configuration** → Setup LLM prompts for chart analysis
5. **Strategy Creation** → Combine indicators + prompts into trading strategies
6. **Scheduled Execution** → Cron jobs to run strategies at intervals
7. **Chart Generation** → Generate technical analysis charts
8. **LLM Signal Generation** → Analyze charts with LLM to generate signals
9. **Order Placement** → Place buy orders on buy signals
10. **Position Management** → Sell positions on sell signals
11. **Order Status Tracking** → Monitor order execution
12. **Portfolio Updates** → Update portfolio on completed trades
13. **Lineage Tracking** → Track input/output of each workflow step ⭐ **NEW**

---

## Lineage Tracking Feature Details

### Purpose
Provides complete transparency and traceability for every workflow execution:
- 🔍 **Debugging** - Trace issues through execution history
- 📊 **Transparency** - Show users what happened at each step
- 🎯 **Audit Trail** - Complete record of all decisions
- 📈 **Performance Analysis** - Identify bottlenecks

### What Gets Tracked
For **each step** in every workflow execution:
- **Execution ID** - Unique identifier for the workflow run
- **Step Name** - e.g., "fetch_market_data", "llm_analysis", "place_order"
- **Step Number** - Sequential order (1, 2, 3, ...)
- **Input Data** - Complete JSON of inputs to the step
- **Output Data** - Complete JSON of outputs from the step
- **Duration** - Execution time in milliseconds
- **Status** - Success or error
- **Error Details** - Full error message if step failed
- **Metadata** - Strategy ID, user ID, timestamp, etc.

### Frontend Lineage Viewer

**New Page**: `/lineage` 

**Features**:
1. **Strategy Selector** - Choose which strategy to view
2. **Execution Selector** - Choose which execution to view
3. **Step Visualization** - Visual cards showing each step
4. **Rich Data Display** - Smart visualization based on step type ⭐ **NEW**
5. **Error Highlighting** - Red borders and badges for failed steps
6. **Step Details Modal** - Full visualization + collapsible JSON
7. **Performance Metrics** - Duration and statistics per step

**Rich Visualizations** ⭐:
- **Strategy**: Configuration table with badges and status
- **Market Data**: Input/output cards with symbol and price
- **Indicators**: Table of all indicator values (RSI, MACD, etc.)
- **Charts**: Actual chart images embedded (clickable for full size) 🖼️
- **LLM Analysis**: Full analysis text in readable format 🧠
- **Signal**: Large badges (BUY/SELL), price cards, risk/reward analysis 📡
- **Orders**: Order status badges, quantity/price/total display 🛒
- **Trades**: Trade details with P&L visualization 💰

**UI Example**:
```
┌─────────────────────────────────────────────────────┐
│ Step 1: Load Strategy                    ✓ 45ms    │
├─────────────────────────────────────────────────────┤
│ Input:                    →    Output:              │
│ {                              {                    │
│   "strategy_id": 123           "strategy": {...},   │
│ }                              "is_active": true    │
│                                }                    │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: Fetch Market Data               ✓ 1,234ms  │
├─────────────────────────────────────────────────────┤
│ Input:                    →    Output:              │
│ {                              {                    │
│   "symbol": "AAPL",            "rows": 500,         │
│   "conid": 265598              "latest_price": 175  │
│ }                              }                    │
└─────────────────────────────────────────────────────┘
```

### Database Schema

**New Table**: `workflow_lineage`
```sql
CREATE TABLE workflow_lineage (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    step_number INTEGER NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    metadata JSONB,
    error TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    duration_ms INTEGER,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_execution_step UNIQUE (execution_id, step_name)
);
```

### API Endpoints

**New Router**: `/api/lineage`

1. `GET /api/lineage/execution/{execution_id}`
   - Get complete lineage for a workflow execution
   - Returns all steps with input/output data

2. `GET /api/lineage/execution/{execution_id}/step/{step_name}`
   - Get lineage for a specific step
   - Returns detailed step information

3. `GET /api/lineage/strategy/{strategy_id}/recent?limit=10`
   - Get recent execution IDs for a strategy
   - Returns list of executions with timestamps

4. `GET /api/lineage/step/{step_name}/statistics?days=30`
   - Get statistics for a specific step
   - Returns success rate, avg duration, common errors

### Backend Implementation

**New Service**: `backend/services/lineage_tracker.py`
```python
class LineageTracker:
    async def record_step(
        self,
        execution_id: str,
        step_name: str,
        step_number: int,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> LineageRecord:
        """Record a single workflow step with its input/output"""
        # ... implementation
```

**Enhanced**: `backend/services/strategy_executor.py`
- Every step now records lineage before and after execution
- Input data captured before step
- Output data captured after step
- Errors captured on exception
- Duration automatically calculated

---

## Integration with Existing Systems

### ✅ Keeps & Uses
- **Prompt System** (Phases 1-14) - Already implemented, fully integrated
- **IBKR Gateway** - Authentication and order placement
- **PostgreSQL** - Database with all tables
- **Celery** - Background task execution and scheduling
- **Redis** - Message broker
- **MinIO** - Chart storage
- **FastAPI** - Backend API
- **Frontend** - HTML templates + JavaScript

### 🆕 New Services to Build
- `SymbolSearchService` - IBKR symbol search
- `StrategyService` - Strategy CRUD and management
- `StrategyExecutor` - Core execution engine
- `OrderManager` - Order placement and validation
- `PositionManager` - Position tracking and management
- `OrderTracker` - Order status monitoring
- `PortfolioService` - Portfolio and P&L calculations
- `LineageTracker` - Execution lineage recording ⭐

### 🗑️ To Remove
- `workflows/` directory - Merged into strategies
- `decisions/` directory - Merged into signals
- `analysis.html` - Integrated into strategy execution
- Extra logs pages - Consolidated

---

## Database Changes

### New Tables
1. `symbols` - Cache IBKR symbols
2. `user_sessions` - IBKR session management
3. `portfolio_snapshots` - Historical portfolio data
4. `workflow_lineage` - Execution lineage ⭐

### Enhanced Tables
1. `strategies` - Add fields: schedule, symbol_conid, prompt_template_id, risk_params
2. `strategy_executions` - Add field: execution_id (links to lineage)
3. `trading_signals` - Already enhanced in prompt system phases

### Removed Tables
1. `workflows` - Functionality merged into `strategies`
2. `workflow_executions` - Renamed to `strategy_executions`
3. `decisions` - Functionality merged into `trading_signals`

---

## Frontend Pages

### Keep & Enhance
1. ✅ Login (`ibkr_login.html`)
2. ✅ Dashboard (`dashboard.html`)
3. ✅ Symbols (`symbols.html`)
4. ✅ Indicators (`indicators.html`)
5. ✅ Prompts (`prompts.html`)
6. ✅ Strategies (`strategies.html`)
7. ✅ Signals (`signals.html`)
8. ✅ Charts (`charts.html`)

### New Pages
9. 🆕 Orders (`orders.html`) - Order list and details
10. 🆕 Portfolio (`portfolio.html`) - Portfolio dashboard
11. 🆕 Lineage (`lineage.html`) - Execution lineage viewer ⭐

### Remove
- ❌ `workflows/` pages
- ❌ `analysis.html`
- ❌ `decisions/` pages
- ❌ Extra logs pages

---

## Implementation Timeline

### Total: 20 Days (4 Weeks)

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| 1. Planning & Design | 2 days | ✅ Complete (this document) |
| 2. Core Workflow | 5 days | Symbol search, indicators, strategies, scheduling |
| 3. LLM Integration | 3 days | Charts, signals, executor engine |
| 4. Order Management | 4 days | Orders, positions, tracking, portfolio |
| 5. Lineage Tracking | 3 days | Tracker service, API, frontend viewer |
| 6. Cleanup & Refactoring | 3 days | Remove unused code, migrations |
| 7. Frontend Implementation | 4 days | New pages, enhanced UI |
| 8. Testing & Documentation | 3 days | Tests, docs, user guide |
| 9. Deployment | 2 days | Deploy, verify, monitor |

---

## Success Criteria

### Functional
- ✅ User can complete entire workflow without manual intervention
- ✅ Strategies execute automatically on schedule
- ✅ LLM generates actionable trading signals
- ✅ Orders placed successfully to IBKR
- ✅ Portfolio reflects all executed trades
- ✅ All errors handled gracefully with notifications
- ✅ **Complete lineage available for every execution** ⭐

### Non-Functional
- ✅ End-to-end workflow completes in < 5 minutes
- ✅ 99% uptime for automated executions
- ✅ Zero data loss on failures
- ✅ All actions logged for audit trail
- ✅ System recoverable from any failure state
- ✅ **Lineage recording adds < 100ms overhead per step** ⭐

### Quality
- ✅ 80%+ test coverage
- ✅ All OpenSpec documentation complete
- ✅ User guide and API docs published
- ✅ Zero critical security vulnerabilities
- ✅ Performance benchmarks met

---

## Key Benefits of Lineage Tracking

### For Users
1. **Transparency** - See exactly what happened at each step
2. **Debugging** - Quickly identify where and why failures occurred
3. **Confidence** - Understand how trading decisions were made
4. **Learning** - Analyze successful vs unsuccessful patterns

### For Developers
1. **Troubleshooting** - Trace issues through the entire workflow
2. **Performance Optimization** - Identify slow steps
3. **Testing** - Verify each step's input/output
4. **Monitoring** - Track success rates per step

### For Compliance
1. **Audit Trail** - Complete record of all decisions
2. **Reproducibility** - Replay any execution with full context
3. **Accountability** - Track which prompt and strategy produced each signal
4. **Documentation** - Automatic documentation of workflow behavior

---

## Next Steps

### 1. Review & Approval
- [ ] Review this complete design document
- [ ] Approve the overall approach
- [ ] Approve the lineage tracking feature
- [ ] Confirm timeline and resources

### 2. Begin Implementation (Phase 2)
Once approved, start with:
- [ ] 2.1 User Authentication enhancement
- [ ] 2.2 Symbol Search Service
- [ ] 2.3 Indicator Configuration
- [ ] 2.4 Strategy Creation
- [ ] 2.5 Scheduled Execution

### 3. Track Progress
- Use `tasks.md` as implementation checklist
- Mark tasks complete with `- [x]`
- Update this document with progress

---

## Files Created

```
openspec/changes/complete-ibkr-workflow/
├── proposal.md (224 lines)
├── design.md (2,040 lines)
├── tasks.md (460 lines)
├── WORKFLOW_DESIGN_COMPLETE.md (this file)
└── specs/
    ├── workflow-execution/
    │   └── spec.md (Requirements + 8 scenarios)
    ├── order-management/
    │   └── spec.md (Requirements + 12 scenarios)
    ├── portfolio-management/
    │   └── spec.md (Requirements + 10 scenarios)
    └── lineage-tracking/
        └── spec.md (Requirements + 12 scenarios)
```

**Total**: ~3,000 lines of comprehensive OpenSpec documentation

---

## Validation

```bash
$ openspec validate complete-ibkr-workflow --strict
✅ Change 'complete-ibkr-workflow' is valid
```

All requirements have proper scenarios, all scenarios have proper format, and all delta operations are valid.

---

## Ready for Implementation

The complete IBKR trading workflow is now fully designed and documented using OpenSpec, including the lineage tracking feature for complete transparency.

**Status**: ✅ Design Phase Complete - Ready for Development

**Next Action**: Review and approve to begin Phase 2 implementation

---

**Document Version**: 1.0  
**Created**: 2025-10-25  
**Last Updated**: 2025-10-25  
**OpenSpec Change ID**: `complete-ibkr-workflow`

