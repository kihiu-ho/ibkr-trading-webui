# Multi-Symbol Workflow Enhancement - Quick Start

## Overview

The IBKR Trading Platform now supports multiple symbols with dynamic configuration, enhanced market data storage, and improved MLflow logging reliability.

## New Features

### 1. Dynamic Multi-Symbol Support
- Add/remove symbols without changing code
- Enable/disable symbols via API or UI
- Set priority for processing order
- Symbol-specific configurations

### 2. Enhanced Market Data in Artifacts
- Complete OHLCV data (Open, High, Low, Close, Volume)
- Technical indicator values (SMA, RSI, MACD, Bollinger Bands)
- Last 50 bars stored per chart artifact
- Accessible via API: `/api/artifacts/{id}`

### 3. Fixed MLflow Timeout Issues
- Increased timeout from 5 to 10 minutes
- Removed blocking API calls
- Added retry logic (2 retries, 30s delay)
- Better error handling

## Quick Start

### 1. Start Services

```bash
docker-compose up -d
./wait-for-docker.sh
```

### 2. Add Trading Symbols

**Via API:**
```bash
# Add TSLA
curl -X POST http://localhost:8000/api/workflow-symbols/ \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TSLA",
    "name": "Tesla Inc.",
    "enabled": true,
    "priority": 10
  }'

# Add NVDA
curl -X POST http://localhost:8000/api/workflow-symbols/ \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NVDA",
    "name": "NVIDIA Corporation",
    "enabled": true,
    "priority": 9
  }'
```

**Via Python Script:**
```bash
docker-compose exec backend python scripts/seed_workflow_symbols.py
```

### 3. Run Test Suite

```bash
./scripts/test_multi_symbol_workflow.sh
```

### 4. Trigger Workflow

**Option A: Airflow UI**
- Go to http://localhost:8080
- Find DAG: `ibkr_multi_symbol_workflow`
- Click "Trigger DAG"

**Option B: API**
```bash
curl -X POST http://localhost:8080/api/v1/dags/ibkr_multi_symbol_workflow/dagRuns \
  -H "Content-Type: application/json" \
  -d '{}'
```

## API Endpoints

### Workflow Symbols

```bash
# List all symbols
GET /api/workflow-symbols/

# List enabled symbols only
GET /api/workflow-symbols/?enabled_only=true

# Get specific symbol
GET /api/workflow-symbols/{symbol}

# Add symbol
POST /api/workflow-symbols/
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "enabled": true,
  "priority": 8
}

# Update symbol (enable/disable)
PATCH /api/workflow-symbols/{symbol}
{
  "enabled": false
}

# Delete symbol
DELETE /api/workflow-symbols/{symbol}
```

### Artifacts with Market Data

```bash
# List artifacts
GET /api/artifacts/?limit=10&symbol=TSLA

# Get artifact with market data
GET /api/artifacts/{id}

# Response includes:
{
  "id": 14,
  "symbol": "TSLA",
  "type": "chart",
  "metadata": {
    "market_data_snapshot": {
      "bars": [
        {
          "date": "2025-11-15",
          "open": 250.5,
          "high": 252.8,
          "low": 249.2,
          "close": 252.5,
          "volume": 1234567
        }
      ]
    },
    "indicator_summary": {
      "sma_20": 248.5,
      "sma_50": 245.2,
      "rsi_14": 54.2
    }
  }
}
```

## Workflow Configuration

The multi-symbol workflow automatically fetches enabled symbols from the backend API:

```python
# dags/ibkr_multi_symbol_workflow.py

SYMBOLS = get_enabled_symbols()  # Fetches from API
# Falls back to ['TSLA', 'NVDA'] if API unavailable
```

### Environment Variables

```bash
# .env
BACKEND_API_URL=http://backend:8000
WORKFLOW_SYMBOLS=TSLA,NVDA  # Fallback if API unavailable
```

## Monitoring

### Check Workflow Status
```bash
# Airflow UI
http://localhost:8080

# Check logs
docker-compose logs -f airflow-webserver
docker-compose logs -f airflow-scheduler
```

### View MLflow Runs
```bash
# MLflow UI
http://localhost:5500

# Check for:
# - Run completion (no timeouts)
# - Artifact uploads
# - Metrics logged
```

### Query Artifacts
```bash
# Get recent artifacts
curl http://localhost:8000/api/artifacts/?limit=5

# Check market data
curl http://localhost:8000/api/artifacts/{id} | jq '.metadata.market_data_snapshot'
```

## Troubleshooting

### MLflow Task Hangs
✅ **FIXED** - Timeout increased to 10 minutes, blocking calls removed

### Symbols Not Loading
```bash
# Check backend API
curl http://localhost:8000/health

# Check symbols exist
curl http://localhost:8000/api/workflow-symbols/

# Seed if empty
docker-compose exec backend python scripts/seed_workflow_symbols.py
```

### Market Data Missing in Artifacts
- Only chart-type artifacts contain market data
- Check `metadata.market_data_snapshot`
- Check `metadata.indicator_summary`

## Architecture

```
Frontend (React)
    ↓
Backend API (FastAPI)
    ↓
PostgreSQL (Symbols, Artifacts)
    ↓
Airflow DAG
    ↓
IBKR Gateway → Market Data → Charts → LLM → Orders
    ↓
MLflow (Tracking)
```

## Files Changed

### Backend
- `backend/models/workflow_symbol.py` - New model
- `backend/api/workflow_symbols.py` - New API
- `backend/models/__init__.py` - Import WorkflowSymbol
- `backend/main.py` - Add router

### DAGs
- `dags/ibkr_trading_signal_workflow.py` - MLflow timeout fix
- `dags/ibkr_multi_symbol_workflow.py` - Dynamic symbols

### Scripts
- `scripts/seed_workflow_symbols.py` - Seed TSLA, NVDA
- `scripts/test_multi_symbol_workflow.sh` - Test suite

### Documentation
- `docs/implementation/MULTI_SYMBOL_WORKFLOW_IMPLEMENTATION.md`
- `openspec/changes/multi-symbol-enhancement/proposal.md`
- `openspec/changes/multi-symbol-enhancement/tasks.md`

## Next Steps

1. ✅ Test symbol management API
2. ✅ Run multi-symbol workflow
3. ✅ Verify MLflow completion
4. ✅ Check market data in artifacts
5. ⏳ Build frontend Symbol Management page
6. ⏳ Update Dashboard for multi-symbol view
7. ⏳ Add OHLCV data table component

## Support

For issues or questions:
- Check logs: `docker-compose logs -f backend`
- Check Airflow: http://localhost:8080
- Check API docs: http://localhost:8000/docs
- Review: `docs/implementation/MULTI_SYMBOL_WORKFLOW_IMPLEMENTATION.md`
