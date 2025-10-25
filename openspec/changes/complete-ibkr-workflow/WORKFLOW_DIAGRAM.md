# Complete IBKR Trading Workflow - Visual Diagrams

## High-Level System Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                             │
│  Login → Search Symbol → Configure → Create Strategy → Monitor    │
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────┐
│                      FASTAPI BACKEND                               │
│  ┌──────────────┬──────────────┬──────────────┬─────────────────┐│
│  │ Auth Service │Symbol Service│ Strategy Svc │ Lineage Tracker ││
│  ├──────────────┼──────────────┼──────────────┼─────────────────┤│
│  │Indicator Svc │  Prompt Svc  │ Chart Gen    │ Order Manager   ││
│  ├──────────────┼──────────────┼──────────────┼─────────────────┤│
│  │  LLM Service │ Signal Gen   │ Position Mgr │ Portfolio Svc   ││
│  └──────────────┴──────────────┴──────────────┴─────────────────┘│
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────┐
│                      CELERY WORKERS                                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ • Strategy Execution Worker (Scheduled by Celery Beat)       │ │
│  │ • Chart Generation Worker                                    │ │
│  │ • LLM Analysis Worker                                        │ │
│  │ • Order Placement Worker                                     │ │
│  │ • Order Monitoring Worker                                    │ │
│  │ • Position Monitoring Worker (Stop Loss / Take Profit)       │ │
│  │ • Portfolio Update Worker                                    │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────┐
│                    EXTERNAL SERVICES                               │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────────┐│
│  │ IBKR API │PostgreSQL│  Redis   │  MinIO   │ LLM API (OpenAI) ││
│  └──────────┴──────────┴──────────┴──────────┴──────────────────┘│
└───────────────────────────────────────────────────────────────────┘
```

---

## Complete Workflow Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW EXECUTION STARTS                         │
│                  (Triggered by Celery Beat Schedule)                 │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │ STEP 1: Load Strategy           │◄─── Lineage: Input: {strategy_id}
    │ - Get strategy from database    │     Output: {strategy config}
    │ - Validate is_active            │
    └─────────────┬───────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │ STEP 2: Fetch Market Data       │◄─── Lineage: Input: {symbol_conid}
    │ - Call IBKR API                 │     Output: {OHLCV data, 500 rows}
    │ - Get historical price data     │
    └─────────────┬───────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │ STEP 3: Calculate Indicators    │◄─── Lineage: Input: {indicators, data}
    │ - RSI, MACD, ATR, SMA, etc.     │     Output: {RSI: 45, MACD: 0.2...}
    │ - Apply to market data          │
    └─────────────┬───────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │ STEP 4: Generate Charts         │◄─── Lineage: Input: {data, indicators}
    │ - Daily chart with indicators   │     Output: {chart_urls: [url1, url2]}
    │ - Weekly chart (if configured)  │
    │ - Upload to MinIO               │
    └─────────────┬───────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │ STEP 5: LLM Analysis            │◄─── Lineage: Input: {chart_urls, prompt}
    │ - Load prompt template          │     Output: {analysis_text, model}
    │ - Render with Jinja2            │
    │ - Call LLM API with charts      │
    └─────────────┬───────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │ STEP 6: Parse Signal            │◄─── Lineage: Input: {analysis_text}
    │ - Extract BUY/SELL/HOLD         │     Output: {signal: BUY, entry: 175,
    │ - Parse entry, stop, target     │              stop: 170, target: 185}
    └─────────────┬───────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │ STEP 7: Place Order (if signal) │◄─── Lineage: Input: {signal, strategy}
    │ - Calculate position size       │     Output: {order_id, ibkr_order_id,
    │ - Validate risk parameters      │              quantity, price, status}
    │ - Place order to IBKR           │
    │ - Start order monitoring        │
    └─────────────┬───────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │ STEP 8: Record Execution        │◄─── Lineage: Input: {execution_id}
    │ - Store in strategy_executions  │     Output: {status: completed,
    │ - Link to lineage records       │              duration_ms: 45000}
    └─────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW EXECUTION COMPLETE                       │
│              All steps recorded in workflow_lineage table            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Order Management Flow

```
┌──────────────────┐
│  BUY Signal      │
│  Generated       │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│ Calculate Position Size  │
│ Formula: (Capital × Risk)│
│         ÷ (Entry - Stop) │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Validate Available       │
│ Capital & Risk Limits    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Place Limit Order        │
│ to IBKR                  │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐     ┌──────────────────┐
│ Monitor Order Status     │────►│ FILLED?          │──Yes──┐
│ (Poll every 10 sec)      │     └──────────────────┘       │
└────────┬─────────────────┘              │                 │
         │                                No                │
         │                                 │                 │
         │                                 ▼                 │
         │                    ┌──────────────────────┐      │
         │                    │ CANCELLED/REJECTED?  │─Yes──┤
         │                    └──────────────────────┘      │
         │                                │                 │
         │                               No                │
         │                                │                 │
         └────────────────────────────────┘                 │
                                                            │
         ┌──────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Order Filled:            │
│ - Create/Update Position │
│ - Record Trade           │
│ - Update Signal Outcome  │
│ - Update Portfolio       │
│ - Send Notification      │
└──────────────────────────┘
```

---

## Position Management Flow

```
┌──────────────────────────────────────────────────────────────┐
│           Position Monitoring (Every 60 seconds)              │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Get All Open Positions   │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ For Each Position:       │
│ Fetch Current Price      │
└────────┬─────────────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────────┐
│ Current Price│ │ SELL Signal │ │ Stop Loss│ │ Take Profit  │
│ Check        │ │ Generated?  │ │ Hit?     │ │ Hit?         │
└──────┬───────┘ └──────┬──────┘ └────┬─────┘ └──────┬───────┘
       │ OK            │ Yes          │ Yes          │ Yes
       │               │              │              │
       │               ▼              ▼              ▼
       │         ┌────────────────────────────────────────┐
       │         │      Place SELL Order                  │
       │         │  - Quantity: Full position             │
       │         │  - Type: Limit order                   │
       │         └────────────┬───────────────────────────┘
       │                      │
       └──────────────────────┴──────► Continue Monitoring
```

---

## Lineage Tracking Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Workflow Execution                          │
└───────────────────┬─────────────────────────────────────────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
     ▼              ▼              ▼
  Step 1         Step 2   ...   Step N
     │              │              │
     │ Before       │              │
     ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│ LineageTracker.record_step()                                     │
│ - execution_id: "strategy_123_2025-10-25T10:30:00"              │
│ - step_name: "fetch_market_data"                                │
│ - step_number: 2                                                │
│ - input_data: {"symbol": "AAPL", "conid": 265598}               │
│ - output_data: {"rows": 500, "latest_price": 175.23}            │
│ - duration_ms: 1234                                              │
│ - status: "success"                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │  PostgreSQL   │
                 │workflow_lineage│
                 └───────┬───────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Frontend   │ │     API      │ │  Analytics   │
│ Lineage View │ │  Query by    │ │ Performance  │
│              │ │ execution_id │ │  Statistics  │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Frontend Lineage Viewer Layout

```
┌───────────────────────────────────────────────────────────────────┐
│                      Workflow Lineage Viewer                       │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Strategy: [Dropdown: AAPL Swing Trading ▼]                       │
│  Execution: [Dropdown: 2025-10-25 10:30:00 - Completed ▼]         │
│                                                                    │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Step 1: Load Strategy                       ✓ SUCCESS 45ms │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  INPUT                  →        OUTPUT                     │  │
│  │  {                               {                          │  │
│  │    "strategy_id": 123              "strategy": {...},      │  │
│  │  }                                 "is_active": true        │  │
│  │                                  }                          │  │
│  │                                                             │  │
│  │  [View Full Details]                                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ↓                                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Step 2: Fetch Market Data                 ✓ SUCCESS 1234ms │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  INPUT                  →        OUTPUT                     │  │
│  │  {                               {                          │  │
│  │    "symbol": "AAPL",               "rows": 500,             │  │
│  │    "conid": 265598                 "latest_price": 175.23   │  │
│  │  }                               }                          │  │
│  │                                                             │  │
│  │  [View Full Details]                                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ↓                                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Step 3: Calculate Indicators              ✓ SUCCESS 567ms  │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  INPUT                  →        OUTPUT                     │  │
│  │  {                               {                          │  │
│  │    "indicators": [...]             "RSI_14": 45.2,          │  │
│  │    "market_data_rows": 500         "MACD": 0.23,           │  │
│  │  }                                 "ATR_14": 2.1            │  │
│  │                                  }                          │  │
│  │                                                             │  │
│  │  [View Full Details]                                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ...                                      │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

---

## Database Entity Relationships (with Lineage)

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   users     │         │  strategies  │         │  indicators │
│-------------|         │--------------|         │-------------|
│ id (PK)     │────┐    │ id (PK)      │◄───┐    │ id (PK)     │
│ username    │    └───►│ user_id (FK) │    └────│ strategy_id │
│ email       │         │ symbol_conid │         │ type        │
└─────────────┘         │ schedule     │         │ parameters  │
                        │ prompt_id(FK)│         └─────────────┘
                        └──────┬───────┘
                               │
                ┌──────────────┴───────────────┐
                │                              │
                ▼                              ▼
      ┌──────────────────┐         ┌─────────────────────┐
      │strategy_executions│         │ trading_signals     │
      │------------------|         │---------------------|
      │ id (PK)          │         │ id (PK)             │
      │ strategy_id (FK) │         │ strategy_id (FK)    │
      │ execution_id ●───┼─────┐   │ signal_type         │
      │ executed_at      │     │   │ entry_price         │
      │ status           │     │   │ stop_loss           │
      └──────────────────┘     │   │ target_price        │
                               │   │ prompt_id (FK)      │
                               │   └─────────────────────┘
                               │
                               │
                               ▼
                    ┌─────────────────────┐
                    │ workflow_lineage ●  │
                    │---------------------|
                    │ id (PK)             │
                    │ execution_id        │
                    │ step_name           │
                    │ step_number         │
                    │ input_data (JSONB)  │
                    │ output_data (JSONB) │
                    │ duration_ms         │
                    │ status              │
                    │ error               │
                    └─────────────────────┘

● = New lineage tracking feature
```

---

## Timeline Gantt Chart

```
Week 1: Planning & Core Workflow
├── Mon-Tue:   Planning & Design ████████████ COMPLETE
├── Wed-Thu:   Symbol Search     ░░░░░░░░░░░░
└── Fri:       Indicators        ░░░░░░

Week 2: Core Workflow Continued
├── Mon-Tue:   Strategy Creation ░░░░░░░░░░░░
└── Wed-Fri:   Scheduling        ░░░░░░░░░░░░

Week 3: LLM & Orders
├── Mon-Tue:   Charts & LLM      ░░░░░░░░░░░░
├── Wed-Thu:   Order Management  ░░░░░░░░░░░░
└── Fri:       Position Tracking ░░░░░░

Week 4: Lineage & Cleanup
├── Mon-Tue:   Lineage Tracking  ░░░░░░░░░░░░ ●
├── Wed:       Cleanup            ░░░░░░
└── Thu-Fri:   Testing & Deploy  ░░░░░░░░░░░░

● = New lineage tracking feature (3 days)

Legend:
████ = Complete
░░░░ = Planned
```

---

## Summary Statistics

- **Total Steps in Workflow**: 13 (including lineage tracking)
- **New Database Tables**: 4 (symbols, user_sessions, portfolio_snapshots, workflow_lineage)
- **New API Endpoints**: ~30 across all services
- **New Frontend Pages**: 3 (orders, portfolio, lineage)
- **Total Implementation Tasks**: ~250
- **Estimated Duration**: 20 days (4 weeks)
- **Lines of Code (estimated)**: ~8,000-10,000 LOC

**Lineage Tracking Impact**:
- **Development Time**: 3 days
- **Database Storage**: ~1KB per step × 13 steps × executions
- **Performance Overhead**: < 100ms per step
- **API Endpoints**: 4 new endpoints
- **Frontend Pages**: 1 complete page
- **Value**: Complete transparency and debugging capability ✨

---

**Document Version**: 1.0  
**Created**: 2025-10-25  
**OpenSpec Change ID**: `complete-ibkr-workflow`

