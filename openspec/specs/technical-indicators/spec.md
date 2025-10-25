# technical-indicators Specification

## Purpose
TBD - created by archiving change add-ibkr-auth-indicators. Update Purpose after archive.
## Requirements
### Requirement: Indicator Database Model
The system SHALL persist indicator configurations in the database.

#### Scenario: Create indicator record
- **WHEN** new indicator is created
- **THEN** store indicator with fields: `id`, `name`, `type`, `parameters` (JSON), `created_at`, `updated_at`

#### Scenario: Associate indicator with strategy
- **WHEN** indicator is added to strategy
- **THEN** create record in `strategy_indicators` junction table with `strategy_id` and `indicator_id`

#### Scenario: Query strategy indicators
- **WHEN** retrieving strategy details
- **THEN** include all associated indicators with their parameters

### Requirement: Indicator CRUD API
The system SHALL provide REST API for indicator management.

#### Scenario: List all indicators
- **WHEN** GET request sent to `/api/indicators`
- **THEN** return JSON array of all indicators with parameters

#### Scenario: Get indicator by ID
- **WHEN** GET request sent to `/api/indicators/{id}`
- **THEN** return single indicator with full details or 404 if not found

#### Scenario: Create new indicator
- **WHEN** POST request sent to `/api/indicators` with `{name, type, parameters}`
- **THEN** validate parameters, create indicator, return created record with status 201

#### Scenario: Update indicator
- **WHEN** PUT request sent to `/api/indicators/{id}` with updated fields
- **THEN** validate parameters, update record, return updated indicator

#### Scenario: Delete indicator
- **WHEN** DELETE request sent to `/api/indicators/{id}`
- **THEN** remove indicator and all strategy associations, return 204 No Content

#### Scenario: Delete indicator in use
- **WHEN** DELETE request sent for indicator used by active strategies
- **THEN** return 400 error with list of strategies using the indicator

### Requirement: Indicator Library
The system SHALL provide pre-configured indicator templates.

#### Scenario: List indicator templates
- **WHEN** GET request sent to `/api/indicators/templates`
- **THEN** return JSON array of built-in indicator types with default parameters

#### Scenario: Available indicator types
- **WHEN** retrieving templates
- **THEN** include: Moving Average, RSI, MACD, Bollinger Bands, SuperTrend, ATR, Stochastic, ADX, CCI, OBV

#### Scenario: Create indicator from template
- **WHEN** POST request sent to `/api/indicators/from-template` with `{template_id, custom_params}`
- **THEN** create indicator using template defaults merged with custom parameters

### Requirement: Parameter Validation
The system SHALL validate indicator parameters based on indicator type.

#### Scenario: Valid parameters
- **WHEN** creating indicator with valid parameters (e.g., MA with period=20)
- **THEN** accept and save the indicator

#### Scenario: Invalid parameters
- **WHEN** creating indicator with invalid parameters (e.g., RSI with period=-5)
- **THEN** return 422 error with detailed validation message

#### Scenario: Missing required parameters
- **WHEN** creating indicator without required parameters (e.g., Bollinger Bands without standard deviation)
- **THEN** return 422 error listing missing parameters

### Requirement: Strategy-Indicator Association
The system SHALL allow strategies to have multiple indicators with individual configurations.

#### Scenario: Add indicator to strategy
- **WHEN** POST request sent to `/api/strategies/{id}/indicators` with `{indicator_id}`
- **THEN** associate indicator with strategy and return updated strategy

#### Scenario: Remove indicator from strategy
- **WHEN** DELETE request sent to `/api/strategies/{id}/indicators/{indicator_id}`
- **THEN** remove association and return confirmation

#### Scenario: List strategy indicators
- **WHEN** GET request sent to `/api/strategies/{id}`
- **THEN** response includes `indicators` array with all associated indicators

#### Scenario: Update strategy with indicators
- **WHEN** PUT request sent to `/api/strategies/{id}` with `{indicator_ids: [1,2,3]}`
- **THEN** replace all indicator associations with specified IDs

### Requirement: Indicator Calculation Support
The system SHALL support indicator value calculation from market data.

#### Scenario: Calculate indicator values
- **WHEN** POST request sent to `/api/indicators/{id}/calculate` with `{symbol, timeframe, data_points}`
- **THEN** compute indicator values using specified parameters and return time series

#### Scenario: Multiple indicator calculation
- **WHEN** strategy has multiple indicators
- **THEN** calculate all indicator values for given market data in single request

#### Scenario: Calculation error handling
- **WHEN** insufficient data points for indicator calculation
- **THEN** return 422 error specifying minimum required data points

