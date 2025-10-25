# Design: IBKR Authentication and Technical Indicators

## Context

The system currently requires manual API calls for IBKR Gateway authentication and lacks a flexible way to configure technical indicators for trading strategies. Users need a streamlined authentication process and the ability to create custom indicator combinations without modifying code.

**Constraints:**
- Must work with existing IBKR Client Portal Gateway
- Must integrate with current strategy and symbol systems
- Must support multiple indicators per strategy
- Must provide visual feedback for indicator configurations

**Stakeholders:**
- Traders who need to authenticate and configure indicators
- Developers maintaining the trading system
- System administrators monitoring connections

## Goals / Non-Goals

**Goals:**
- Provide user-friendly IBKR Gateway authentication UI
- Enable flexible indicator configuration per strategy
- Visualize indicators on price charts
- Support 10+ common technical indicators
- Allow real-time indicator parameter tuning

**Non-Goals:**
- Creating custom indicator formulas from scratch (use pre-defined types)
- Backtesting indicator performance (future enhancement)
- Automated indicator optimization
- Multi-broker authentication (IBKR only)

## Decisions

### Decision 1: Indicator Parameter Storage
**Choice:** Store indicator parameters as JSONB in PostgreSQL

**Rationale:**
- Flexibility: Each indicator type has different parameters
- No schema changes needed when adding new indicator types
- Easy to query and filter
- PostgreSQL JSONB supports indexing and validation

**Alternatives Considered:**
- EAV (Entity-Attribute-Value) tables - Too complex, harder to query
- Separate table per indicator type - Not scalable, requires migrations for new types
- Serialized Python objects - Not database-portable, harder to query

### Decision 2: Chart Library
**Choice:** Lightweight Charts by TradingView

**Rationale:**
- Designed specifically for financial charts
- Excellent performance with large datasets
- Built-in candlestick and line chart support
- Customizable overlays and indicators
- Free and open-source

**Alternatives Considered:**
- Chart.js - General purpose, less optimized for financial data
- D3.js - Too low-level, requires more custom code
- Plotly - Heavy library, overkill for our use case

### Decision 3: Indicator Calculation Location
**Choice:** Backend calculation with caching

**Rationale:**
- Consistent calculations across all clients
- Leverage Python libraries (pandas-ta, ta-lib)
- Can cache calculated values in database
- Reduces client-side computation

**Alternatives Considered:**
- Client-side calculation - Inconsistent results, slower, browser limitations
- Hybrid approach - Added complexity without clear benefits

### Decision 4: IBKR Session Management
**Choice:** Stateless authentication with periodic health checks

**Rationale:**
- IBKR Gateway manages session state
- Backend only tracks connection status
- Health checks every 30 seconds detect disconnections
- No complex state synchronization needed

**Alternatives Considered:**
- Server-side session storage - Redundant with IBKR's session
- WebSocket persistent connection - Unnecessary for our use case

### Decision 5: Indicator-Strategy Relationship
**Choice:** Many-to-many with junction table including order field

**Rationale:**
- Multiple strategies can share indicators
- Single strategy can have multiple indicators
- Order field preserves indicator layering for visualization
- Easy to add/remove associations

**Alternatives Considered:**
- One-to-many (copy indicators per strategy) - Data duplication
- Embedded in strategy JSON - Harder to query, less normalized

## Data Models

### Indicator Table
```sql
CREATE TABLE indicators (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- MA, RSI, MACD, BB, etc.
    parameters JSONB NOT NULL,  -- {period: 20, type: "SMA", source: "close"}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### Strategy-Indicator Junction Table
```sql
CREATE TABLE strategy_indicators (
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    indicator_id INTEGER REFERENCES indicators(id) ON DELETE CASCADE,
    display_order INTEGER DEFAULT 0,
    PRIMARY KEY (strategy_id, indicator_id)
);
```

### Indicator Parameters Schema (Examples)
```json
// Moving Average
{
  "period": 20,
  "type": "SMA",  // or "EMA", "WMA"
  "source": "close"  // or "open", "high", "low"
}

// RSI
{
  "period": 14,
  "overbought": 70,
  "oversold": 30
}

// Bollinger Bands
{
  "period": 20,
  "std_dev": 2,
  "source": "close"
}

// MACD
{
  "fast_period": 12,
  "slow_period": 26,
  "signal_period": 9
}
```

## API Design

### IBKR Authentication Endpoints
```
GET  /api/ibkr/auth/status       -> {authenticated: bool, account_id: str, server_status: {}}
POST /api/ibkr/auth/login        -> {success: bool, message: str}
POST /api/ibkr/auth/logout       -> {success: bool}
GET  /api/ibkr/auth/accounts     -> {accounts: [{id, alias}]}
```

### Indicator Endpoints
```
GET    /api/indicators                     -> [{id, name, type, parameters}]
GET    /api/indicators/{id}                -> {id, name, type, parameters}
POST   /api/indicators                     -> {name, type, parameters}
PUT    /api/indicators/{id}                -> {name, type, parameters}
DELETE /api/indicators/{id}                -> 204 No Content
GET    /api/indicators/templates           -> [{type, default_params, description}]
POST   /api/indicators/from-template       -> {template_id, custom_params}
POST   /api/indicators/{id}/calculate      -> {symbol, timeframe, values: [{time, value}]}
```

### Strategy-Indicator Endpoints
```
POST   /api/strategies/{id}/indicators      -> {indicator_id}
DELETE /api/strategies/{id}/indicators/{indicator_id}
```

## UI Flow

### IBKR Authentication Flow
1. User navigates to `/ibkr/login`
2. Page shows current connection status
3. User clicks "Connect to Gateway"
4. Frontend calls `/api/ibkr/auth/login`
5. Backend authenticates with IBKR Gateway
6. Status updates to "Connected" with green indicator
7. If multiple accounts, show dropdown selector
8. User selection saved for subsequent operations

### Indicator Configuration Flow
1. User navigates to `/indicators`
2. Clicks "Add Indicator"
3. Modal appears with type dropdown
4. User selects "Moving Average"
5. Form dynamically shows: period, type (SMA/EMA), source
6. User fills parameters
7. Clicks "Preview" to see sample chart
8. Adjusts parameters if needed
9. Clicks "Save"
10. Indicator created and modal closes

### Chart Visualization Flow
1. User views strategy detail page
2. Page loads associated symbols and indicators
3. JavaScript fetches market data for selected symbol
4. For each indicator, fetch calculated values via API
5. Render price chart with candlesticks
6. Overlay each indicator on chart
7. User can zoom, pan, toggle indicators
8. Hover shows tooltip with all values at that point

## Component Architecture

```
Frontend
├── ibkr_login.html
│   ├── Connection status display
│   ├── Login button with loading state
│   └── Account selector
├── indicators.html
│   ├── Indicator list table
│   ├── Create/Edit modal
│   └── Template browser
├── strategy_chart.html
│   ├── Symbol selector
│   ├── Timeframe selector
│   ├── Chart canvas (Lightweight Charts)
│   └── Indicator legend with toggles
└── static/js/charts.js
    ├── Chart initialization
    ├── Indicator overlay rendering
    └── User interaction handlers

Backend
├── api/ibkr_auth.py
│   └── Authentication endpoints
├── api/indicators.py
│   └── CRUD and calculation endpoints
├── services/indicator_service.py
│   └── Indicator calculation logic
└── models/indicator.py
    └── Database models
```

## Risks / Trade-offs

### Risk: IBKR Gateway Connection Instability
**Impact:** Users may experience frequent disconnections

**Mitigation:**
- Implement automatic reconnection logic
- Show clear status indicators
- Provide troubleshooting tips in UI

### Risk: Indicator Calculation Performance
**Impact:** Complex indicators on large datasets may be slow

**Mitigation:**
- Implement caching for calculated values
- Limit data points to reasonable window (e.g., 500 candles)
- Use efficient libraries (pandas-ta, numpy)

### Risk: Chart Rendering Performance
**Impact:** Multiple indicators on long timeframes may lag

**Mitigation:**
- Use Lightweight Charts (optimized for performance)
- Implement lazy loading for historical data
- Limit concurrent indicator overlays to 5

### Trade-off: Flexibility vs Complexity
**Decision:** Support 10 pre-defined indicator types vs custom formulas

**Rationale:** Pre-defined types cover 95% of use cases and reduce validation complexity. Custom formulas can be added later if needed.

## Migration Plan

**Phase 1: Database Setup**
1. Run migration to create `indicators` and `strategy_indicators` tables
2. Verify table creation in development environment

**Phase 2: Backend Implementation**
1. Deploy indicator models and schemas
2. Deploy IBKR auth API endpoints
3. Deploy indicator CRUD API endpoints
4. Test all endpoints with Postman/curl

**Phase 3: Frontend Implementation**
1. Deploy IBKR login page
2. Deploy indicator management page
3. Deploy chart visualization
4. Test UI flows manually

**Phase 4: Integration**
1. Connect strategies to indicators
2. Test end-to-end flows
3. Verify chart rendering with real data

**Rollback Plan:**
- If critical issues found, disable new pages via feature flag
- Drop new tables if schema issues detected
- Revert to previous deployment

## Open Questions

- **Q:** Should indicators be shared globally or scoped per user?
  **A:** Start with global indicators (simpler), add user scoping later if needed

- **Q:** How many historical candles to show on charts?
  **A:** Default to 100, max 500 to balance performance and visibility

- **Q:** Should we support custom indicator colors?
  **A:** Use predefined color palette initially, add customization in future

- **Q:** How to handle indicator dependencies (e.g., MACD requires EMA)?
  **A:** Calculate dependencies internally, user only configures top-level indicator

