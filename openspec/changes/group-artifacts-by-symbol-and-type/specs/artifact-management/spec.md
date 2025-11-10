# Artifact Management - Group by Symbol and Type

## MODIFIED Requirements

### Requirement: Artifact Grouping by Symbol and Type

The system SHALL group artifacts first by symbol, then by type, making it easier to view all analysis for a specific symbol.

#### Scenario: Group Artifacts by Symbol
- **Given** artifacts exist for multiple symbols (TSLA, NVDA)
- **When** the artifacts page is displayed
- **Then** artifacts SHALL be grouped by symbol first
- **And** each symbol group SHALL show the symbol name prominently
- **And** each symbol group SHALL display artifact counts by type

#### Scenario: Sub-group by Type Within Symbol
- **Given** a symbol group (e.g., TSLA) with multiple artifact types
- **When** the symbol group is expanded
- **Then** artifacts SHALL be sub-grouped by type (chart, llm, signal, etc.)
- **And** each type sub-group SHALL display the type name
- **And** each type sub-group SHALL show artifact count
- **And** artifacts SHALL be displayed within their type sub-group

#### Scenario: Display Workflow Information
- **Given** artifacts grouped by symbol and type
- **When** viewing a symbol group
- **Then** workflow/execution information SHALL be displayed as secondary information
- **And** the most recent execution date SHALL be shown
- **And** the workflow ID SHALL be displayed

#### Scenario: Handle Missing Symbols
- **Given** artifacts without a symbol
- **When** artifacts are grouped
- **Then** artifacts without symbol SHALL be grouped under "Unknown" or "No Symbol"
- **And** these artifacts SHALL still be sub-grouped by type

#### Scenario: Handle Multiple Executions for Same Symbol
- **Given** multiple workflow executions for the same symbol
- **When** artifacts are grouped
- **Then** all artifacts for the symbol SHALL be grouped together
- **And** artifacts SHALL be sub-grouped by type
- **And** execution metadata SHALL be preserved for display

