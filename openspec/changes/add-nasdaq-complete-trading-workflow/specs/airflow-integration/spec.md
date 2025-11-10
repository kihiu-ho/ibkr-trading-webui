## MODIFIED Requirements
### Requirement: Airflow Run Artifacts Display
The system SHALL display all generated artifacts (charts, LLM analysis, signals, orders, trades, portfolio) in Airflow run details modal.

#### Scenario: Show all artifacts for completed run
- **WHEN** user opens run details modal for a completed workflow
- **THEN** fetch artifacts by execution_id
- **AND** display "Generated Artifacts" section with:
  - Chart artifacts (grouped by symbol and timeframe)
  - LLM analysis artifacts (one per symbol)
  - Trading signal artifacts (one per symbol)
  - Order artifacts (if orders were placed)
  - Trade artifacts (if trades were executed)
  - Portfolio snapshot artifact
- **AND** show artifact cards with type, name, symbol, and timestamp

#### Scenario: Artifact type badges in Airflow modal
- **WHEN** displaying artifact cards in Airflow modal
- **THEN** show colored badge for each type:
  - Chart: Blue with chart icon
  - LLM: Purple with robot icon
  - Signal: Yellow with bolt icon
  - Order: Green with order icon
  - Trade: Orange with trade icon
  - Portfolio: Teal with portfolio icon
- **AND** use consistent colors with artifact detail page

## ADDED Requirements
### Requirement: Artifact Summary Statistics
The system SHALL provide artifact summary statistics in Airflow run details.

#### Scenario: Display artifact counts by type
- **WHEN** run details modal shows artifacts
- **THEN** display summary: "X artifacts generated: Y charts, Z LLM analyses, N signals, M orders, P trades, 1 portfolio"
- **AND** show total storage size if available
- **AND** group by symbol if multiple symbols processed

### Requirement: Bidirectional Navigation
The system SHALL provide seamless navigation between Airflow runs and artifact detail pages.

#### Scenario: Navigate from Airflow to artifact detail
- **WHEN** user clicks artifact card in Airflow modal
- **THEN** open artifact detail page in new tab
- **AND** preserve Airflow modal state (don't close)
- **AND** highlight clicked artifact on detail page

#### Scenario: Navigate from artifact to Airflow
- **WHEN** user views artifact detail page
- **THEN** show "View in Airflow" button if workflow metadata exists
- **AND** clicking navigates to Airflow page with DAG highlighted
- **AND** execution_id is highlighted in run list
- **AND** run details modal opens automatically

