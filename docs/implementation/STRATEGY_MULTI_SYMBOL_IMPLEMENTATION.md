# Strategy Multi-Symbol Implementation

## Summary

Successfully implemented the ability for trading strategies to track multiple symbols (stocks/contracts) and added a symbol lookup page to search and save IBKR symbols.

## Issues Fixed

### 1. POST /api/strategies 422 Error
**Problem**: The strategy schema expected a `code` field that didn't exist in the database model.

**Solution**: Updated the schema to use `symbol_ids` (array of Code IDs) instead of a single `code` field.

## Features Implemented

### 1. Multiple Symbol Support for Strategies

**Changes Made**:
- Updated `StrategyCreate` schema to accept `symbol_ids: List[int]` instead of `code: str`
- Updated `StrategyUpdate` schema to support updating symbol associations
- Added `CodeInfo` schema for symbol information in responses
- Updated `StrategyResponse` to include `codes: List[CodeInfo]` field
- Modified `create_strategy` endpoint to associate multiple symbols
- Modified `update_strategy` endpoint to update symbol associations

**Files Modified**:
- `backend/schemas/strategy.py` - Updated schemas
- `backend/api/strategies.py` - Updated create/update endpoints

### 2. Symbol Lookup API

**New Endpoints**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/symbols/search` | GET | Search IBKR symbols by query string |
| `/api/symbols/saved` | GET | List all saved symbols |
| `/api/symbols/{conid}` | GET | Get symbol by IBKR contract ID |
| `/api/symbols/save` | POST | Save a symbol to database |
| `/api/symbols/{code_id}` | DELETE | Delete a saved symbol |

**Files Created**:
- `backend/api/symbols.py` - Symbol lookup and management API

**Files Modified**:
- `backend/main.py` - Added symbols router

### 3. Symbol Lookup Frontend Page

**Features**:
- Search symbols in IBKR using the search API
- Display search results with symbol, name, conid, exchange, and type
- Save symbols to database for future use
- View and manage saved symbols
- Delete symbols (with protection against deletion if used by strategies)

**Files Created**:
- `frontend/templates/symbols.html` - Symbol lookup page

**Files Modified**:
- `backend/api/frontend.py` - Added `/symbols` route
- `frontend/templates/partials/sidebar.html` - Added "Symbols" link

### 4. Updated Strategy Management UI

**Features**:
- Select multiple symbols from saved symbols
- Add/remove symbols from strategy
- View symbol list in strategy table
- Link to symbol lookup page for adding new symbols
- Display symbol count in strategy list

**Files Modified**:
- `frontend/templates/strategies.html` - Updated UI for multi-symbol support

## Database Schema

The implementation uses the existing many-to-many relationship:

```sql
-- Codes table (symbols)
CREATE TABLE codes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    conid INTEGER NOT NULL UNIQUE,
    exchange VARCHAR(50),
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Association table
CREATE TABLE strategy_codes (
    strategy_id INTEGER REFERENCES strategies(id),
    code_id INTEGER REFERENCES codes(id),
    PRIMARY KEY (strategy_id, code_id)
);
```

## API Examples

### Create Strategy with Multiple Symbols

```bash
curl -X POST http://localhost:8000/api/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Multi-Symbol Strategy",
    "symbol_ids": [1, 2],
    "workflow_id": null,
    "param": {
      "account_size": 100000,
      "risk_per_trade": 0.02
    },
    "active": true
  }'
```

**Response**:
```json
{
  "name": "Multi-Symbol Strategy",
  "workflow_id": null,
  "param": {
    "account_size": 100000,
    "risk_per_trade": 0.02
  },
  "active": true,
  "id": 1,
  "created_at": "2025-10-21T07:02:48.620657",
  "updated_at": null,
  "codes": [
    {
      "id": 1,
      "symbol": "AAPL",
      "conid": 265598,
      "exchange": "NASDAQ",
      "name": "Apple Inc."
    },
    {
      "id": 2,
      "symbol": "TSLA",
      "conid": 76792991,
      "exchange": "NASDAQ",
      "name": "Tesla Inc."
    }
  ]
}
```

### Save a Symbol

```bash
curl -X POST http://localhost:8000/api/symbols/save \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "conid": 265598,
    "exchange": "NASDAQ",
    "name": "Apple Inc."
  }'
```

### Search Symbols

```bash
curl http://localhost:8000/api/symbols/search?query=AAPL
```

### Update Strategy Symbols

```bash
curl -X PUT http://localhost:8000/api/strategies/1 \
  -H "Content-Type: application/json" \
  -d '{"symbol_ids": [1, 3, 5]}'
```

## Testing Results

All features have been tested and verified:

✅ Create strategy with multiple symbols  
✅ Retrieve strategy with codes  
✅ Update strategy symbols  
✅ List saved symbols  
✅ Save new symbols  
✅ Symbol search endpoint  

## Usage Guide

### Adding Symbols

1. Navigate to **Symbols** page from the sidebar
2. Enter a symbol (e.g., "AAPL") in the search box
3. Click **Search**
4. Review search results
5. Click **Save** on desired symbols

### Creating a Strategy with Symbols

1. Navigate to **Strategies** page
2. Click **Add Strategy**
3. Enter strategy name
4. Select symbols from the dropdown
5. Click **Add** to add each symbol
6. Configure other parameters
7. Click **Save**

### Managing Strategy Symbols

1. In the Strategies table, click **Edit** on a strategy
2. Add or remove symbols using the symbol selector
3. Click **Save** to update

## Technical Notes

- Symbol IDs are stored in the `strategy_codes` junction table
- Strategies can have 0 or more symbols
- Symbols can be shared across multiple strategies
- IBKR contract ID (conid) is the unique identifier for symbols
- The search API queries IBKR's `/iserver/secdef/search` endpoint

## Future Enhancements

Potential improvements:
- Bulk symbol import
- Symbol groups/watchlists
- Auto-refresh symbol data from IBKR
- Symbol favorites
- Recent searches
- Symbol details page with market data

---

**Implementation Date**: October 21, 2025  
**Status**: ✅ Complete and Tested

