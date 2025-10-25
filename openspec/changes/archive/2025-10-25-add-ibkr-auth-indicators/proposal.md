# Add IBKR Authentication Panel and Technical Indicators

## Why

The current implementation lacks:
1. **User-friendly IBKR Gateway authentication** - No UI panel for users to authenticate and manage their IBKR Gateway connection
2. **Flexible indicator configuration** - Strategies are limited to hardcoded indicators without user customization
3. **Visual indicator representation** - No frontend visualization of technical indicators and their parameters

These gaps prevent users from:
- Easily connecting to IBKR Gateway without manual API calls
- Creating custom trading strategies with different indicator combinations
- Understanding which indicators are active and what their parameters are
- Visualizing indicator signals and overlays on price charts

## What Changes

### 1. IBKR Gateway Authentication Panel
- **Frontend login page** at `/ibkr/login` with connection status display
- **Authentication API endpoints** for login, logout, status check, and session management
- **Session persistence** and automatic re-authentication
- **Connection health monitoring** with visual status indicators
- **Account selection** for multi-account users

### 2. Technical Indicator System
- **Indicator database model** with name, type, parameters (JSON), and associations
- **Strategy-Indicator many-to-many relationship** allowing multiple indicators per strategy
- **Indicator CRUD API endpoints** for create, read, update, delete operations
- **Parameter validation** ensuring indicator parameters are valid
- **Indicator library** with pre-configured popular indicators (MA, RSI, MACD, Bollinger Bands, SuperTrend, ATR, etc.)

### 3. Indicator Visualization Frontend
- **Indicator management page** at `/indicators` for browsing and configuring indicators
- **Visual indicator builder** with drag-and-drop parameter configuration
- **Chart visualization** showing price data with indicator overlays
- **Real-time updates** when indicators are modified
- **Indicator preview** showing how indicators will appear on charts
- **Multi-timeframe support** for indicator display

### Key Features
- Users can authenticate to IBKR Gateway directly from the UI
- Strategies can have 0-N indicators with custom parameters
- Each indicator stores its configuration (type, period, threshold, etc.)
- Frontend displays all active indicators with visual representations
- Charts show price data with indicator overlays (lines, bands, signals)
- Indicators can be added, edited, removed without code changes

## Impact

### Affected Capabilities (New)
- `ibkr-auth` - IBKR Gateway authentication and session management
- `technical-indicators` - Indicator configuration and management
- `indicator-visualization` - Frontend charting and indicator display

### Affected Code
- **Database**: New `indicators` table, `strategy_indicators` junction table
- **Backend**: 
  - `backend/models/indicator.py` - Indicator database model
  - `backend/schemas/indicator.py` - Indicator Pydantic schemas
  - `backend/api/ibkr_auth.py` - IBKR authentication endpoints
  - `backend/api/indicators.py` - Indicator CRUD endpoints
  - `backend/services/ibkr_service.py` - Enhanced with auth methods
- **Frontend**:
  - `frontend/templates/ibkr_login.html` - IBKR login page
  - `frontend/templates/indicators.html` - Indicator management page
  - `frontend/static/js/charts.js` - Chart library integration
  - `frontend/templates/partials/sidebar.html` - Add navigation links

### Breaking Changes
None - This is purely additive functionality

### Dependencies
- Chart.js or Lightweight Charts for indicator visualization
- Existing IBKR service for API integration
- Existing strategy system for associations

