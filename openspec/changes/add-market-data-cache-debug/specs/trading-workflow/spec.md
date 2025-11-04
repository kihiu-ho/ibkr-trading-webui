# Trading Workflow Delta

## ADDED Requirements

### Requirement: Debug Mode Data Source
The system SHALL support debug mode that uses cached data instead of live IBKR API calls for development and testing.

#### Scenario: Enable debug mode
- **WHEN** DEBUG_MODE environment variable is set to "true"
- **THEN** all workflow executions MUST use cached market data from database
- **AND** workflow logs SHALL indicate "DEBUG MODE: Using cached data"
- **AND** lineage records SHALL include metadata field: data_source="cache"

#### Scenario: Disable debug mode (default)
- **WHEN** DEBUG_MODE is "false" or not set
- **THEN** workflows SHALL fetch live data from IBKR API
- **AND** fetched data SHALL be cached for future debug mode use
- **AND** lineage records SHALL include metadata field: data_source="live_api"

#### Scenario: Cache miss in debug mode
- **WHEN** DEBUG_MODE is enabled and requested data not in cache
- **THEN** workflow SHALL fail with clear error message
- **AND** error message SHALL indicate: "Debug mode enabled but data not in cache for {symbol} at {timestamp}"
- **AND** error message SHALL suggest: "Run populate_market_cache.py script to cache data"

### Requirement: Data Source Transparency
The system SHALL clearly indicate the data source for all workflow executions.

#### Scenario: Display data source in workflow logs
- **WHEN** workflow execution begins
- **THEN** log entry SHALL show: "Data Source: [LIVE_API|CACHE]"
- **AND** show cache status if applicable: "Cache Status: HIT|MISS"
- **AND** show data timestamp and age

#### Scenario: Data source in execution summary
- **WHEN** viewing workflow execution details
- **THEN** display data_source field in metadata
- **AND** if cached, show cached_at timestamp
- **AND** if live, show fetched_at timestamp

