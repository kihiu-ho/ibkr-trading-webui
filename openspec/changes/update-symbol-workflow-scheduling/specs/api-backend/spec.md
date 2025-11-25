## ADDED Requirements
### Requirement: Workflow Symbol Configuration API
The backend SHALL expose workflow symbol endpoints that accept nested workflow configuration objects so each workflow attached to a symbol can maintain unique scheduling data.

#### Scenario: Create workflow symbol with workflow configs
- **WHEN** POST /api/workflow-symbols is called with payload:
  - `symbol`: uppercase ticker (1-10 chars)
  - `name`: optional display name
  - `enabled`: boolean
  - `priority`: integer for catalog ordering
  - `workflows`: array of `SymbolWorkflowConfig` objects where each item includes `workflow_id`, optional `is_active` (defaults true), `timezone` (default "America/New_York"), optional `session_start` and `session_end` (ISO `HH:MM`), `allow_weekend` (default false), optional `config` (JSON object)
- **THEN** validate that workflow_ids exist, at least one workflow is provided, `session_start` precedes `session_end` when both set, and `timezone` is part of the supported Olson list
- **AND** persist each workflow entry as a `SymbolWorkflowLink` row capturing `is_active` (defaulting to true when omitted) and `priority` derived from the array order (index 0 = highest priority)
- **AND** respond with 201 Created including the symbol plus `workflows: [{workflow_id, workflow_name, is_active, priority, timezone, session_start, session_end, allow_weekend, config}]`

#### Scenario: Update workflow symbol workflow configs
- **WHEN** PATCH /api/workflow-symbols/{symbol} is called with updated `name`, `enabled`, `priority`, and/or replacement `workflows[]`
- **THEN** apply changes transactionally: remove links omitted from payload, upsert ones that exist (keeping IDs stable), and append new workflows with priority honoring payload order
- **AND** allow callers to send `is_active` toggles per workflow (default true if omitted) so specific workflows for the symbol can be paused without deleting the association
- **AND** respond with the refreshed symbol payload showing nested workflow objects including their database IDs and scheduling data

#### Scenario: Validate workflow-specific configuration
- **WHEN** the API processes `workflows[]`
- **THEN** reject requests where:
  - `session_start` or `session_end` is provided without the other
  - The computed window crosses midnight unless explicitly marked via `allow_weekend`
  - `config` is not a JSON object (e.g., string or array)
  - Duplicate workflow_ids appear in the same payload
- **AND** default missing optional fields to: `timezone="America/New_York"`, `session_start=null`, `session_end=null`, `allow_weekend=false`, `is_active=true`
- **AND** include validation errors in the response body (422) referencing the specific workflow entry index for quick frontend mapping
