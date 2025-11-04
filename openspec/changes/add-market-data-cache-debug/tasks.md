# Implementation Tasks

## 1. Database Schema
- [ ] 1.1 Create MarketDataCache model extending MarketData
- [ ] 1.2 Add fields: symbol, exchange, data_type, timestamp, ohlcv_data, indicators, metadata
- [ ] 1.3 Add indexes on (symbol, timestamp) and (symbol, data_type)
- [ ] 1.4 Create Alembic migration script
- [ ] 1.5 Test migration in development environment

## 2. Configuration
- [ ] 2.1 Add DEBUG_MODE boolean to backend/config/settings.py
- [ ] 2.2 Add CACHE_ENABLED boolean to settings
- [ ] 2.3 Add CACHE_SYMBOLS list to settings (default: ["NVDA", "TSLA"])
- [ ] 2.4 Add CACHE_EXCHANGE string to settings (default: "NASDAQ")
- [ ] 2.5 Add CACHE_TTL_HOURS integer to settings (default: 24)
- [ ] 2.6 Update env.example with new variables
- [ ] 2.7 Update docker-compose.yml with new environment variables

## 3. Market Data Service Enhancement
- [ ] 3.1 Add get_or_fetch_market_data() method to IBKRService
- [ ] 3.2 Implement cache lookup logic (check DB first)
- [ ] 3.3 Implement cache miss logic (fetch from IBKR, store in DB)
- [ ] 3.4 Add cache expiration logic based on CACHE_TTL_HOURS
- [ ] 3.5 Add debug mode bypass (always use cache when DEBUG_MODE=true)
- [ ] 3.6 Add logging for cache hits/misses

## 4. Workflow Integration
- [ ] 4.1 Modify StrategyExecutor._fetch_market_data() to check DEBUG_MODE
- [ ] 4.2 Add data source selection logic (cache vs live API)
- [ ] 4.3 Add metadata to lineage records indicating data source
- [ ] 4.4 Update workflow logs to show "DEBUG MODE" when active
- [ ] 4.5 Test workflows in both modes (debug and live)

## 5. API Endpoints
- [ ] 5.1 Create GET /api/market-data/cache endpoint to list cached data
- [ ] 5.2 Create GET /api/market-data/cache/{symbol} endpoint for specific symbol
- [ ] 5.3 Create POST /api/market-data/cache/refresh endpoint to update cache
- [ ] 5.4 Create DELETE /api/market-data/cache endpoint to clear cache
- [ ] 5.5 Add query parameters: symbol, date_from, date_to, data_type
- [ ] 5.6 Add proper error handling and validation

## 6. CLI Script
- [ ] 6.1 Create scripts/populate_market_cache.py script
- [ ] 6.2 Add argument parsing (--symbols, --exchange, --days-back)
- [ ] 6.3 Implement batch fetching logic for specified symbols
- [ ] 6.4 Add progress indicators for large fetches
- [ ] 6.5 Add error handling and retry logic
- [ ] 6.6 Create usage documentation in script docstring

## 7. Frontend Updates (Optional)
- [ ] 7.1 Add debug mode indicator to workflow execution UI
- [ ] 7.2 Add market data cache viewer page
- [ ] 7.3 Add cache refresh button
- [ ] 7.4 Show cache status (hit rate, last updated)

## 8. Testing
- [ ] 8.1 Test cache population for NVDA and TSLA
- [ ] 8.2 Test workflow execution with DEBUG_MODE=false (live data)
- [ ] 8.3 Test workflow execution with DEBUG_MODE=true (cached data)
- [ ] 8.4 Test cache expiration logic
- [ ] 8.5 Test API endpoints
- [ ] 8.6 Test CLI script with various parameters

## 9. Documentation
- [ ] 9.1 Update README with debug mode instructions
- [ ] 9.2 Document cache management endpoints
- [ ] 9.3 Add troubleshooting guide for cache issues
- [ ] 9.4 Document CLI script usage

## 10. Validation
- [ ] 10.1 Run openspec validate --strict
- [ ] 10.2 Fix any validation errors
- [ ] 10.3 Test complete workflow end-to-end
- [ ] 10.4 Verify all tasks completed

