# API Backend Delta

## ADDED Requirements

### Requirement: Market Data Cache API
The system SHALL provide REST API endpoints for managing cached market data.

#### Scenario: List cached market data
- **WHEN** GET /api/market-data/cache is called
- **THEN** return JSON array of cached data entries
- **AND** each entry includes: id, symbol, exchange, timestamp, data_type, cached_at, expires_at
- **AND** support query parameters: symbol, date_from, date_to, limit, offset
- **AND** order by timestamp DESC by default

#### Scenario: Get cached data for specific symbol
- **WHEN** GET /api/market-data/cache/{symbol} is called
- **THEN** return all cached data for that symbol
- **AND** support query parameters: date_from, date_to, data_type
- **AND** return 404 if no cached data exists for symbol

#### Scenario: Refresh cached data
- **WHEN** POST /api/market-data/cache/refresh is called with {"symbols": ["NVDA", "TSLA"]}
- **THEN** fetch latest data from IBKR for each symbol
- **AND** update or insert into market_data_cache table
- **AND** return refresh summary: {refreshed: ["NVDA", "TSLA"], failed: [], timestamp: "..."}
- **AND** if IBKR API fails, return partial success with error details

#### Scenario: Clear cache
- **WHEN** DELETE /api/market-data/cache is called
- **THEN** delete all expired cache entries
- **AND** support query parameter: symbol (to clear specific symbol)
- **AND** support query parameter: days_old (to clear data older than N days)
- **AND** return deletion count: {deleted: 42, remaining: 128}

### Requirement: Cache Population Script
The system SHALL provide a CLI script to populate market data cache for specified symbols.

#### Scenario: Populate cache for default symbols
- **WHEN** script is run: `python scripts/populate_market_cache.py`
- **THEN** fetch market data for CACHE_SYMBOLS from settings (NVDA, TSLA)
- **AND** fetch last 365 days of daily data
- **AND** store in market_data_cache table
- **AND** display progress: "Fetching NVDA: [====>    ] 50%"

#### Scenario: Populate cache with custom parameters
- **WHEN** script is run: `python scripts/populate_market_cache.py --symbols AAPL MSFT --days 90`
- **THEN** fetch data for specified symbols
- **AND** fetch specified number of days back from today
- **AND** handle IBKR API errors gracefully with retries
- **AND** log results: "Successfully cached 90 days for AAPL, MSFT"

#### Scenario: Handle API rate limiting
- **WHEN** IBKR API returns 429 rate limit error during cache population
- **THEN** wait for rate limit reset (or use exponential backoff)
- **AND** retry failed requests up to 3 times
- **AND** log rate limit encounters
- **AND** continue with remaining symbols after rate limit clears

