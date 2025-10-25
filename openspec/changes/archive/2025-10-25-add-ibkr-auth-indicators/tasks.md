# Implementation Tasks

## 1. Database Schema
- [x] 1.1 Create `indicators` table with columns: id, name, type, parameters (JSONB), created_at, updated_at
- [x] 1.2 Create `strategy_indicators` junction table with columns: strategy_id, indicator_id, order (for display sequence)
- [x] 1.3 Add database migration script
- [x] 1.4 Update init.sql with new tables

## 2. Backend Models
- [x] 2.1 Create `backend/models/indicator.py` with Indicator and StrategyIndicator models
- [x] 2.2 Add relationships to Strategy model for indicators
- [x] 2.3 Create `backend/schemas/indicator.py` with Pydantic schemas (IndicatorCreate, IndicatorUpdate, IndicatorResponse)
- [x] 2.4 Add indicator validation logic for parameters

## 3. IBKR Authentication API
- [x] 3.1 Create `backend/api/ibkr_auth.py` with authentication endpoints
- [x] 3.2 Implement GET `/api/ibkr/auth/status` endpoint
- [x] 3.3 Implement POST `/api/ibkr/auth/login` endpoint
- [x] 3.4 Implement POST `/api/ibkr/auth/logout` endpoint
- [x] 3.5 Implement GET `/api/ibkr/auth/accounts` endpoint for account selection
- [x] 3.6 Add session persistence logic
- [x] 3.7 Add health check monitoring (30-second intervals)

## 4. Technical Indicators API
- [x] 4.1 Create `backend/api/indicators.py` with CRUD endpoints
- [x] 4.2 Implement GET `/api/indicators` - list all indicators
- [x] 4.3 Implement GET `/api/indicators/{id}` - get single indicator
- [x] 4.4 Implement POST `/api/indicators` - create indicator
- [x] 4.5 Implement PUT `/api/indicators/{id}` - update indicator
- [x] 4.6 Implement DELETE `/api/indicators/{id}` - delete indicator
- [x] 4.7 Implement GET `/api/indicators/templates` - list indicator templates
- [x] 4.8 Implement POST `/api/indicators/from-template` - create from template
- [x] 4.9 Implement POST `/api/indicators/{id}/calculate` - calculate indicator values
- [x] 4.10 Add strategy-indicator association endpoints to strategies API

## 5. Indicator Calculation Service
- [x] 5.1 Create `backend/services/indicator_service.py`
- [x] 5.2 Implement Moving Average (SMA, EMA, WMA) calculation
- [x] 5.3 Implement RSI calculation
- [x] 5.4 Implement MACD calculation
- [x] 5.5 Implement Bollinger Bands calculation
- [x] 5.6 Implement SuperTrend calculation
- [x] 5.7 Implement ATR calculation
- [x] 5.8 Implement Stochastic Oscillator calculation
- [x] 5.9 Implement ADX calculation
- [x] 5.10 Add parameter validation for each indicator type

## 6. IBKR Login Frontend
- [x] 6.1 Create `frontend/templates/ibkr_login.html` with connection UI
- [x] 6.2 Add connection status display (Connected/Disconnected/Connecting)
- [x] 6.3 Add "Connect to Gateway" button with loading state
- [x] 6.4 Add account selection dropdown for multi-account users
- [x] 6.5 Add error message display with troubleshooting tips
- [x] 6.6 Add session status indicator in navigation bar
- [x] 6.7 Implement auto-refresh of connection status
- [x] 6.8 Add frontend route in `backend/api/frontend.py`

## 7. Indicator Management Frontend
- [x] 7.1 Create `frontend/templates/indicators.html` with indicator list
- [x] 7.2 Add indicator creation modal with type selector
- [x] 7.3 Add dynamic parameter form generator based on indicator type
- [x] 7.4 Add parameter validation and error display
- [x] 7.5 Add edit indicator modal
- [x] 7.6 Add delete confirmation dialog
- [x] 7.7 Add indicator templates browser
- [x] 7.8 Add "Create from Template" functionality
- [x] 7.9 Add navigation link in sidebar
- [x] 7.10 Add frontend route in `backend/api/frontend.py`

## 8. Chart Visualization Frontend
- [x] 8.1 Add Chart.js or Lightweight Charts library to project
- [x] 8.2 Create `frontend/static/js/charts.js` with chart initialization
- [x] 8.3 Implement candlestick/line chart rendering
- [x] 8.4 Implement Moving Average overlay rendering
- [x] 8.5 Implement Bollinger Bands overlay rendering
- [x] 8.6 Implement RSI sub-panel rendering
- [x] 8.7 Implement MACD sub-panel rendering
- [x] 8.8 Add legend with indicator names and parameters
- [x] 8.9 Add zoom and pan controls
- [x] 8.10 Add hover tooltip with values at point
- [x] 8.11 Add indicator visibility toggles
- [x] 8.12 Add timeframe selector (1D, 1W, 1M)
- [x] 8.13 Add symbol selector for multi-symbol strategies

## 9. Strategy Integration
- [x] 9.1 Update `frontend/templates/strategies.html` to show associated indicators
- [x] 9.2 Add indicator selector in strategy create/edit modal
- [x] 9.3 Add "View Chart" link for each strategy
- [x] 9.4 Create strategy chart view page
- [x] 9.5 Update strategy response schema to include indicators

## 10. Testing
- [x] 10.1 Test IBKR authentication flow (login, logout, status)
- [x] 10.2 Test account selection with multiple accounts
- [x] 10.3 Test session persistence across page reloads
- [x] 10.4 Test connection health monitoring and reconnection
- [x] 10.5 Test indicator creation with valid parameters
- [x] 10.6 Test indicator parameter validation (invalid values)
- [x] 10.7 Test indicator update and deletion
- [x] 10.8 Test creating indicators from templates
- [x] 10.9 Test associating indicators with strategies
- [x] 10.10 Test removing indicators from strategies
- [x] 10.11 Test indicator calculation for different types
- [x] 10.12 Test chart rendering with single indicator
- [x] 10.13 Test chart rendering with multiple indicators
- [x] 10.14 Test chart interactions (zoom, pan, toggle)
- [x] 10.15 Test indicator preview functionality
- [x] 10.16 Test real-time indicator updates on charts
- [x] 10.17 Test multi-symbol visualization
- [x] 10.18 Test timeframe changes

## 11. Documentation
- [x] 11.1 Add indicator types and parameters documentation
- [x] 11.2 Add IBKR authentication setup guide
- [x] 11.3 Add chart visualization user guide
- [x] 11.4 Add API endpoint documentation
- [x] 11.5 Create example indicator configurations

