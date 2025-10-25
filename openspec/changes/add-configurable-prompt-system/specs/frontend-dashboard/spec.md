# Frontend Dashboard Spec Deltas

## ADDED Requirements

### Requirement: Prompt Manager Page
The system SHALL provide a web interface for managing LLM prompt templates.

#### Scenario: Navigate to Prompt Manager
- **GIVEN** a user is logged into the dashboard
- **WHEN** clicking "Prompts" in the sidebar navigation
- **THEN** the system SHALL:
  - Navigate to `/prompts` route
  - Display the Prompt Manager page
  - Show list of existing prompts

#### Scenario: View prompt list
- **GIVEN** the Prompt Manager page is loaded
- **WHEN** displaying prompts
- **THEN** the system SHALL show a table with columns:
  - Name - prompt template name
  - Type - daily_chart, weekly_chart, consolidation, decision
  - Language - en, zh
  - Version - version number
  - Status - Active badge if is_active=TRUE
  - Default badge if is_default=TRUE
  - Last Updated - timestamp
  - Actions - Edit, Clone, Delete, Activate/Deactivate buttons

#### Scenario: Filter prompts
- **GIVEN** the prompt list is displayed
- **WHEN** user selects filters
- **THEN** the system SHALL support filtering by:
  - Type - dropdown with all prompt types
  - Language - dropdown with en, zh
  - Status - All, Active, Inactive
  - Search by name

### Requirement: Prompt Editor
The system SHALL provide a rich editor for creating and editing prompts.

#### Scenario: Create new prompt
- **GIVEN** user clicks "New Prompt" button
- **WHEN** the editor modal opens
- **THEN** the system SHALL display a form with:
  - Name field - text input
  - Description field - textarea
  - Type dropdown - daily_chart, weekly_chart, consolidation, decision
  - Language dropdown - en, zh
  - Content editor - Monaco editor with syntax highlighting
  - Variable reference panel - shows available variables ({{symbol}}, {{now}}, etc.)
  - Preview button - renders prompt with sample data
  - Save button
  - Cancel button

#### Scenario: Edit existing prompt
- **GIVEN** user clicks Edit on a prompt
- **WHEN** the editor modal opens
- **THEN** the system SHALL:
  - Load prompt data into form
  - Display content in Monaco editor
  - Show current version number
  - Auto-increment version on save
  - Warn if prompt is currently active/default

#### Scenario: Syntax highlighting and validation
- **GIVEN** user is editing prompt content
- **WHEN** typing in the Monaco editor
- **THEN** the system SHALL:
  - Highlight {{variables}} in different color
  - Show autocomplete for available variables
  - Validate closing braces {{ }}
  - Display character count
  - Show line numbers

#### Scenario: Preview prompt with sample data
- **GIVEN** user has entered prompt content
- **WHEN** clicking Preview button
- **THEN** the system SHALL:
  - Render prompt with sample variable values
  - Show in read-only modal
  - Display how it will appear to LLM
  - Allow closing to continue editing

### Requirement: Prompt Testing
The system SHALL allow testing prompts before activation.

#### Scenario: Test prompt with real chart
- **GIVEN** a prompt is created or edited
- **WHEN** user clicks "Test Prompt" button
- **THEN** the system SHALL:
  - Show dialog to select: Symbol, Timeframe
  - Fetch a real chart for that symbol/timeframe
  - Call LLM API with the test prompt
  - Display the generated analysis
  - Show latency and token usage
  - Allow saving if test passes

#### Scenario: Test fails with error
- **GIVEN** a test prompt generates an error
- **WHEN** LLM API call fails
- **THEN** the system SHALL:
  - Display error message with details
  - Show what was sent to API (for debugging)
  - Suggest fixes (missing variables, syntax errors)
  - Prevent saving until test passes

### Requirement: Prompt Activation
The system SHALL allow activating/deactivating prompts.

#### Scenario: Activate prompt as default
- **GIVEN** a user selects a prompt
- **WHEN** clicking "Set as Default" button
- **THEN** the system SHALL:
  - Show confirmation dialog: "This will make [name] the active prompt for [type] in [language]. Previous default will be deactivated. Continue?"
  - On confirm, call API to set is_default=TRUE
  - Update UI to show Default badge
  - Remove Default badge from previous default

#### Scenario: Deactivate prompt
- **GIVEN** a default prompt is displayed
- **WHEN** clicking "Deactivate" button
- **THEN** the system SHALL:
  - Show warning: "Deactivating will cause system to fall back to hardcoded prompt. Activate another prompt first?"
  - On confirm, set is_default=FALSE
  - Update UI to remove Default badge
  - Show warning banner if no default exists for that type

### Requirement: Prompt Cloning
The system SHALL support cloning prompts for easy versioning.

#### Scenario: Clone existing prompt
- **GIVEN** a user wants to create a variant of existing prompt
- **WHEN** clicking "Clone" button
- **THEN** the system SHALL:
  - Copy all fields from original prompt
  - Append " (Copy)" to name
  - Set version=1 (new version chain)
  - Set is_active=TRUE, is_default=FALSE
  - Open editor for modification
  - Save as new prompt (different ID)

#### Scenario: Revert to default
- **GIVEN** a user has modified a prompt and wants to start over
- **WHEN** clicking "Revert to Default" button
- **THEN** the system SHALL:
  - Show confirmation dialog
  - Load the seeded default prompt for that type+language
  - Copy content to current prompt
  - Increment version
  - Mark as updated

### Requirement: Prompt History
The system SHALL display version history for prompts.

#### Scenario: View version history
- **GIVEN** a prompt with multiple versions
- **WHEN** clicking "History" button
- **THEN** the system SHALL:
  - Display timeline of all versions
  - Show version number, timestamp, author for each
  - Allow viewing content of previous versions (read-only)
  - Allow restoring a previous version (creates new version)

#### Scenario: Restore previous version
- **GIVEN** user views a previous version
- **WHEN** clicking "Restore This Version" button
- **THEN** the system SHALL:
  - Copy content from old version
  - Create new version with incremented number
  - Update updated_at timestamp
  - Close history modal

### Requirement: Signal Traceability in UI
The system SHALL display prompt information in signal detail pages.

#### Scenario: View signal with prompt link
- **GIVEN** a user views a signal detail page
- **WHEN** the signal was generated with a database prompt
- **THEN** the system SHALL display:
  - "Generated with: [Prompt Name] v[Version]" label
  - Link to view full prompt
  - Language used badge
  - Timestamp of generation

#### Scenario: Navigate from signal to prompt
- **GIVEN** a signal detail page shows a prompt link
- **WHEN** user clicks the prompt link
- **THEN** the system SHALL:
  - Navigate to Prompt Manager
  - Open the specific prompt in read-only view
  - Highlight the version that was used
  - Show "Used by X signals" count

### Requirement: Bulk Operations
The system SHALL support bulk operations on prompts.

#### Scenario: Export prompts
- **GIVEN** user wants to backup or version control prompts
- **WHEN** clicking "Export All" button
- **THEN** the system SHALL:
  - Call API to export all prompts as JSON
  - Download file: prompts_export_[timestamp].json
  - Include all metadata (name, type, language, content, version)

#### Scenario: Import prompts
- **GIVEN** user has a JSON file with prompts
- **WHEN** clicking "Import" and selecting file
- **THEN** the system SHALL:
  - Parse JSON file
  - Validate format and required fields
  - Show preview of prompts to be imported
  - Allow selecting which to import
  - Warn about conflicts (same type+language)
  - Import selected prompts
  - Show success/error report

