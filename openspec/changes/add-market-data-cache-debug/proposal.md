# Add Market Data Caching and Debug Mode

## Why

The system currently fetches market data from IBKR in real-time for every workflow execution, which causes several issues:
- Repeated API calls for the same data during development and testing
- IBKR API rate limiting can block development workflows
- Difficult to test and debug workflows with consistent data
- No persistent storage of historical market data for analysis

This change enables:
- Caching market data in PostgreSQL for reuse
- Debug mode that uses cached data instead of live IBKR API calls
- Faster development iterations without hitting API rate limits
- Ability to replay workflows with historical data

## What Changes

- **Database Schema**: Add market data caching table with symbol, timestamp, OHLCV data, and metadata
- **Market Data Service**: Implement fetch-and-cache logic for specified symbols (NVDA, TSLA initially)
- **Debug Mode Toggle**: Add DEBUG_MODE environment variable and configuration
- **Workflow Data Source**: Modify workflows to use cached DB data when DEBUG_MODE=true
- **API Endpoints**: Add endpoints to fetch/refresh cached market data
- **CLI Script**: Create script to populate cache for specific symbols

## Impact

### Affected Specs
- `database-schema` - Adding new market_data_cache table
- `trading-workflow` - Adding debug mode data source selection
- `api-backend` - Adding market data cache endpoints

### Affected Code
- `backend/models/` - New MarketDataCache model (extends existing MarketData)
- `backend/services/ibkr_service.py` - Add caching logic
- `backend/services/strategy_executor.py` - Debug mode data source switching
- `backend/api/market_data.py` - New endpoints for cache management
- `backend/config/settings.py` - Add DEBUG_MODE and CACHE_SYMBOLS settings
- `scripts/populate_market_cache.py` - New CLI script for data population

### Breaking Changes
None - this is purely additive functionality. Existing workflows continue to use live data by default.

### Migration Required
- Database migration to add market_data_cache table
- Environment variable configuration for debug mode

## Benefits

1. **Development Speed**: Faster iteration during development/testing
2. **Cost Reduction**: Reduce IBKR API calls during development
3. **Reproducibility**: Test workflows with consistent historical data
4. **Data Persistence**: Keep historical market data for analysis
5. **Rate Limit Avoidance**: Work around IBKR API rate limiting during testing

