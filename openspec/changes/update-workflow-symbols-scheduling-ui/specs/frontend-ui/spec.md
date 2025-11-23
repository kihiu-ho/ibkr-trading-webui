## ADDED Requirements
### Requirement: Workflow Symbol Assignment UI
The system SHALL provide a guided modal for creating and editing workflow symbols that explicitly binds each symbol to at least one workflow schedule instead of accepting ad-hoc session windows.

#### Scenario: Add workflow symbol with schedule coverage
- **WHEN** the user clicks "Add Symbol" from the Workflow Symbols page
- **THEN** display a multi-step slide-over modal with Step 1 (Symbol Details) and Step 2 (Schedule Coverage)
- **AND** Step 1 SHALL capture: symbol (uppercase, 1-10 chars), optional display name, target workflow, enable toggle, and priority order with real-time validation
- **AND** Step 2 SHALL list all schedules for the selected workflow (name, cron summary, timezone, enabled badge, next run) with search/filter controls
- **AND** at least one enabled schedule MUST be selected before the "Review & Save" action is enabled
- **AND** the modal SHALL offer a "Create schedule" shortcut that opens the workflow schedule modal pre-filtered to the chosen workflow when no schedules exist

#### Scenario: Review workflow symbol association
- **WHEN** the user advances past schedule selection
- **THEN** show a review step summarizing the symbol metadata plus the selected schedule badges (cron + timezone)
- **AND** warn with a blocking error if no enabled schedule is selected, or if every selected schedule is currently paused
- **AND** saving SHALL POST/PATCH the workflow symbol along with the set of schedule IDs to the backend API

#### Scenario: Surface schedule coverage in catalog
- **WHEN** workflow symbols are listed in the catalog table/cards
- **THEN** each symbol SHALL display schedule chips showing the linked schedules' names and enabled/paused status
- **AND** symbols with zero linked schedules SHALL show a red "Unscheduled" pill plus a tooltip explaining they will never run until a schedule is added
- **AND** filters SHALL allow narrowing the catalog by linked schedule or schedule status so operators can find gaps quickly

## MODIFIED Requirements
### Requirement: Scheduled Workflows Interface
The system SHALL provide an upgraded interface for scheduling periodic workflow executions that aligns with the workflow symbol assignment experience.

#### Scenario: Create schedule
- **WHEN** the user clicks "New Schedule" (or the schedule shortcut from the symbol modal)
- **THEN** display a two-step modal: Step 1 confirms the strategy + workflow pairing and shows the workflow's currently linked symbols, Step 2 captures cadence details
- **AND** cadence inputs SHALL include cron expression (with validation), timezone selection, enabled toggle, and optional description, plus preset buttons (daily open, hourly, etc.)
- **AND** a real-time preview SHALL render at least the next five run timestamps with human-friendly summary text, updating as cron or timezone changes
- **AND** the modal SHALL not allow submission until cron validation passes and both strategy + workflow are selected, surfacing inline errors next to the respective fields

#### Scenario: List scheduled workflows
- **WHEN** the user views the schedules page
- **THEN** the table SHALL include schedule coverage badges per row summarizing which workflow symbols (count + examples) will run under the attached strategy
- **AND** filters SHALL support narrowing by status, workflow, and linked symbol coverage (e.g., "shows symbols without schedules" state surfaced from the symbol catalog)
- **AND** each row SHALL expose the enhanced cron summary, next run preview chips, enable toggle, and action buttons consistent with the new modal styling

#### Scenario: Edit schedule
- **WHEN** the user edits an existing schedule
- **THEN** open the same upgraded modal pre-populated with current data plus a metadata callout (created/updated/last run) and read-only view of linked workflow symbols
- **AND** any cron/timezone change SHALL immediately refresh the preview and highlight risk if no upcoming runs are computed
- **AND** saving SHALL preserve the workflow-symbol linkage context so the symbol catalog immediately reflects schedule state changes
