## MODIFIED Requirements
### Requirement: Multi-Symbol Management
The system SHALL provide an intuitive, multi-step interface for managing multiple trading symbols, including workflow-level scheduling controls, so operators can configure per-symbol/per-workflow execution windows without duplicating symbols.

#### Scenario: Add symbols to strategy
- **WHEN** user clicks "Add Symbol" from the workflow symbols view
- **THEN** open a three-step modal that enforces completion of each stage before moving forward
- **AND** Step 1 (Symbol Details) SHALL collect: uppercase symbol (1-10 chars, validated via IBKR search), optional display name auto-filled from search, global enabled toggle, and catalog priority (drag-handle or numeric input)
- **AND** Step 2 (Workflow Configuration) SHALL show all available workflows in a searchable left column and an "Active Workflows" column on the right; users CAN click or drag workflows to activate them, reorder active workflows to define per-symbol execution priority, and toggle each workflow on/off without removing it
- **AND** each active workflow expands into a scheduling card that includes: timezone dropdown (default "America/New_York"), Session Start/End time pickers (15-minute increments, HH:MM), Weekend toggle, and a JSON config editor (textarea with live JSON validation)
- **AND** Step 3 (Review) SHALL summarize the symbol metadata plus every selected workflow with badges for timezone + session window, highlight validation errors (missing window, invalid JSON, zero active workflows), and only enable "Save Symbol" once at least one workflow is active and all cards validate

#### Scenario: Manage symbol list
- **WHEN** viewing the symbol list
- **THEN** each row SHALL display: symbol, display name, global priority, enable state, and chips for every workflow showing timezone + session window + weekend badge + active/inactive state
- **AND** rows SHALL be drag-and-drop reorderable to update the global priority, while per-row "Edit" opens the three-step modal pre-populated with the symbol and workflow data
- **AND** removing a workflow removes it from the Active column but preserves its previous settings for undo until the modal is saved, and deleting the symbol requires confirmation showing how many workflows will be impacted

#### Scenario: Configure per-workflow schedule
- **WHEN** editing an active workflow card
- **THEN** changes to timezone or session fields SHALL immediately update the summary badges and validate that `session_start < session_end` (same-day window) unless the user explicitly sets both fields empty to indicate "run whenever"
- **AND** enabling the Weekend toggle SHALL allow Saturday/Sunday execution; if disabled, the review step SHALL warn when the configured window overlaps weekends for workflows marked as always-on
- **AND** JSON config editor SHALL require valid JSON objects (not arrays/strings) and display inline errors referencing the offending line before allowing the user to continue
- **AND** saving the modal SHALL send `workflows[]` as ordered objects `{workflow_id, is_active, timezone, session_start, session_end, allow_weekend, config}` matching the backend schema so per-workflow scheduling persists
