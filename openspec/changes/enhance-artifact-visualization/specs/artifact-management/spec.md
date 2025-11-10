# Artifact Management - Enhanced Visualization

## ADDED Requirements

### Requirement: Market Data Table Display

The system SHALL display market data (OHLC, volume) in a table format for chart artifacts.

#### Scenario: Display Market Data Table for Chart Artifact
- **Given** a chart artifact exists with ID 47
- **When** the artifact detail page is displayed
- **Then** the system SHALL display a market data table
- **And** the table SHALL include columns: Date, Open, High, Low, Close, Volume
- **And** the table SHALL show the most recent market data for the symbol
- **And** the table SHALL be sortable and paginated if there are many rows
- **And** the table SHALL be responsive for mobile devices

### Requirement: Indicators Table Display

The system SHALL display technical indicators in a table format for chart artifacts.

#### Scenario: Display Indicators Table for Chart Artifact
- **Given** a chart artifact exists with indicators in chart_data
- **When** the artifact detail page is displayed
- **Then** the system SHALL display an indicators table
- **And** the table SHALL list all indicators from chart_data.indicators
- **And** the table SHALL show indicator names and values if available
- **And** the table SHALL be organized and readable

## MODIFIED Requirements

### Requirement: Chart Artifact Display

The system SHALL display chart artifacts with market data, indicators, and chart image.

#### Scenario: Enhanced Chart Artifact View
- **Given** a chart artifact exists with ID 47
- **When** the artifact detail page is displayed
- **Then** the system SHALL display:
  - Chart image (existing)
  - Market data table (new)
  - Indicators table (new)
  - Chart configuration (existing)
- **And** the sections SHALL be organized with tabs or clear sections
- **And** all data SHALL be accessible and readable

### Requirement: LLM Artifact Display

The system SHALL display LLM artifacts with enhanced input/output visualization.

#### Scenario: Enhanced LLM Artifact View
- **Given** an LLM artifact exists with ID 49
- **When** the artifact detail page is displayed
- **Then** the system SHALL display:
  - Clear "Input" section with prompt
  - Clear "Output" section with response
  - Model information
  - Copy to clipboard functionality
- **And** the prompt and response SHALL be well-formatted
- **And** the sections SHALL be clearly labeled

## ADDED Requirements

### Requirement: Market Data API Endpoint

The system SHALL provide an API endpoint to fetch market data for chart artifacts.

#### Scenario: Fetch Market Data for Chart Artifact
- **Given** a chart artifact exists with ID 47 and symbol TSLA
- **When** a GET request is made to `/api/artifacts/47/market-data`
- **Then** the endpoint SHALL return HTTP 200 OK
- **And** the response SHALL contain market data array
- **And** each market data entry SHALL include: date, open, high, low, close, volume
- **And** the data SHALL be sorted by date (most recent first)
- **And** the response SHALL be limited to a reasonable number of rows (e.g., 50-100)

