# Airflow Integration Specification

## ADDED Requirements

### Requirement: Airflow Run Artifacts Display
The system SHALL display generated artifacts in Airflow run details modal.

#### Scenario: Show artifacts for completed run
- **WHEN** user opens run details modal for a completed workflow
- **THEN** fetch artifacts by execution_id
- **AND** display "Generated Artifacts" section
- **AND** show artifact cards with type, name, and timestamp

#### Scenario: Artifact loading states
- **WHEN** artifacts are being fetched
- **THEN** show loading spinner in artifacts section
- **AND** if fetch fails, show error message
- **AND** if no artifacts, show "No artifacts generated"

#### Scenario: Click artifact card
- **WHEN** user clicks an artifact card in Airflow modal
- **THEN** open artifact detail page in same or new tab
- **AND** preserve Airflow modal state (don't close)

### Requirement: Workflow-Artifact Linking
The system SHALL maintain bidirectional links between workflows and artifacts.

#### Scenario: Link from DAG to artifacts
- **WHEN** viewing DAG card on Airflow monitor page
- **THEN** show "View Artifacts" quick action button
- **AND** clicking navigates to artifacts page filtered by workflow_id

#### Scenario: Link from artifact to Airflow
- **WHEN** viewing artifact detail page
- **THEN** show "View in Airflow" button if workflow metadata exists
- **AND** clicking navigates to Airflow page with DAG highlighted
- **AND** execution_id is highlighted in run list

### Requirement: Artifact Summary in Run Details
The system SHALL provide artifact summary statistics in run details.

#### Scenario: Display artifact counts by type
- **WHEN** run details modal shows artifacts
- **THEN** display summary: "3 artifacts generated: 2 charts, 1 LLM analysis"
- **AND** show total storage size if available

#### Scenario: Highlight missing artifacts
- **WHEN** workflow completed but generated no artifacts
- **THEN** show warning indicator
- **AND** suggest possible workflow issues

### Requirement: Real-time Artifact Updates
The system SHALL update artifact display when new artifacts are generated.

#### Scenario: Artifact generated during active run
- **WHEN** workflow is running and generating artifacts
- **THEN** poll for new artifacts every 5 seconds
- **AND** update artifact count and list without full page refresh
- **AND** stop polling when run completes or user closes modal

#### Scenario: Manual refresh
- **WHEN** user clicks refresh button in artifacts section
- **THEN** re-fetch artifacts for that execution
- **AND** show updated count and list
- **AND** display "Updated X seconds ago" timestamp

### Requirement: Artifact Type Visualization
The system SHALL visually distinguish artifact types in Airflow modal.

#### Scenario: Artifact type badges
- **WHEN** displaying artifact cards
- **THEN** show colored badge for each type:
  - LLM: Pink with flask icon
  - Chart: Indigo with chart icon  
  - Signal: Purple with signal icon
- **AND** use consistent colors with artifact detail page

#### Scenario: Artifact preview
- **WHEN** hovering over artifact card
- **THEN** show preview tooltip with:
  - Full artifact name
  - Step that generated it
  - Creation timestamp
  - Quick metadata (e.g., model name for LLM)

