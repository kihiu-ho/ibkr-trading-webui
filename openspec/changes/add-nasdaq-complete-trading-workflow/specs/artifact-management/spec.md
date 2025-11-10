## MODIFIED Requirements
### Requirement: Grouped Artifact Visualization
The system SHALL provide a grouped view of artifacts organized by workflow execution, supporting all artifact types (charts, LLM analysis, signals, orders, trades, portfolio).

#### Scenario: View artifacts grouped by execution
- **WHEN** user navigates to the artifacts page
- **THEN** artifacts are grouped by execution_id
- **AND** each group shows execution metadata (workflow_id, dag_id, timestamp)
- **AND** artifacts within each group are sorted by step_name order
- **AND** all artifact types are displayed (charts, LLM, signals, orders, trades, portfolio)

#### Scenario: Display all artifact types in grouped view
- **WHEN** viewing execution group
- **THEN** group SHALL display:
  - Chart artifacts (daily and weekly for each symbol)
  - LLM analysis artifacts (one per symbol)
  - Trading signal artifacts (one per symbol)
  - Order artifacts (if orders were placed)
  - Trade artifacts (if trades were executed)
  - Portfolio snapshot artifact (one per execution)

## ADDED Requirements
### Requirement: Artifact API Grouping Support
The system SHALL provide API endpoints to retrieve artifacts grouped by execution_id.

#### Scenario: Get artifacts grouped by execution
- **WHEN** API request includes group_by=execution_id parameter
- **THEN** API SHALL return artifacts grouped by execution_id
- **AND** each group SHALL include:
  - execution_id
  - workflow_id
  - dag_id
  - execution_timestamp
  - artifact_count by type
  - list of artifacts in that execution

#### Scenario: Get artifacts for specific execution
- **WHEN** API request includes execution_id parameter
- **THEN** API SHALL return all artifacts for that execution_id
- **AND** artifacts SHALL be sorted by step_name or created_at

### Requirement: Artifact Type Filtering
The system SHALL support filtering artifacts by type in the grouped view.

#### Scenario: Filter artifacts by type
- **WHEN** user selects artifact type filter (charts, LLM, signals, orders, trades, portfolio)
- **THEN** grouped view SHALL show only artifacts of selected type
- **AND** execution groups with no matching artifacts SHALL be hidden
- **AND** artifact counts in group headers SHALL be updated

