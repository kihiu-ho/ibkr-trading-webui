## ADDED Requirements
### Requirement: Symbol Workflow Association Table
The database SHALL model workflow-specific scheduling metadata via an association object instead of storing schedule columns on the parent workflow symbol record.

#### Scenario: Persist per-workflow scheduling data
- **WHEN** a workflow symbol is linked to a workflow
- **THEN** create a `symbol_workflow_links` row with: `id`, `workflow_symbol_id`, `workflow_id`, `is_active` (default true), `priority` (int, scoped to the symbol), `timezone` (default "America/New_York"), `session_start` (TIME, nullable), `session_end` (TIME, nullable), `allow_weekend` (bool, default false), `config` (JSONB), `created_at`, `updated_at`
- **AND** enforce a composite uniqueness constraint on (`workflow_symbol_id`, `workflow_id`) plus an index on (`workflow_symbol_id`, `priority`) so execution order is deterministic
- **AND** store workflow-specific overrides such as timezone or JSON config inside this association row so multiple workflows referencing the same symbol can keep different schedules

#### Scenario: Workflow symbol stores identity-only data
- **WHEN** the `workflow_symbols` table is created or migrated
- **THEN** it SHALL retain only identity and catalog fields: `id`, `symbol` (unique, uppercase), `name`, `enabled`, `priority`, `created_at`, `updated_at`
- **AND** scheduling columns (`timezone`, `session_start`, `session_end`, `allow_weekend`, `config`) SHALL be removed from `workflow_symbols`
- **AND** any existing scheduling values SHALL be migrated into the corresponding `symbol_workflow_links` rows so no information is lost
