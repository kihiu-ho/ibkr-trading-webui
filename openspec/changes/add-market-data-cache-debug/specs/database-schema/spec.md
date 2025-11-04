# Database Schema Delta

## ADDED Requirements

### Requirement: Market Data Cache Storage
The system SHALL provide persistent storage for cached market data to enable offline development and reduce API calls.

#### Scenario: Store market data in cache
- **WHEN** market data is fetched from IBKR for a symbol
- **THEN** store in market_data_cache table with: symbol, exchange, timestamp, ohlcv_data (JSON), data_type
- **AND** include metadata: source="IBKR", cached_at=current_timestamp, expires_at=cached_at + TTL hours
- **AND** set unique constraint on (symbol, exchange, timestamp, data_type)

#### Scenario: Retrieve cached market data
- **WHEN** market data is requested and cache is enabled
- **THEN** query market_data_cache for matching symbol, exchange, timestamp range
- **AND** if cached data exists and not expired, return cached data
- **AND** if cached data expired or missing, fetch from IBKR and update cache

#### Scenario: Cache expiration
- **WHEN** cached data timestamp is older than CACHE_TTL_HOURS
- **THEN** mark data as expired
- **AND** trigger refresh on next access
- **AND** optionally purge expired data via scheduled job

### Requirement: Symbol Index Management
The system SHALL maintain efficient indexes for market data cache queries.

#### Scenario: Index on symbol and timestamp
- **WHEN** database tables are created
- **THEN** create composite index on (symbol, timestamp DESC)
- **AND** create index on (symbol, data_type, timestamp DESC)
- **AND** create index on expires_at for cleanup queries

#### Scenario: Cache lookup performance
- **WHEN** querying cached data for a symbol
- **THEN** query execution SHOULD complete in <100ms for single symbol
- **AND** support efficient range queries by timestamp

