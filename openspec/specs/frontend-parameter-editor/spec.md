# frontend-parameter-editor Specification

## Purpose
TBD - created by archiving change add-llm-trading-frontend. Update Purpose after archive.
## Requirements
### Requirement: Dynamic Parameter Form Generation
The system SHALL generate parameter forms dynamically based on strategy configuration schema.

#### Scenario: Load and display parameters
- **WHEN** user opens parameter editor for a strategy
- **THEN** all strategy parameters SHALL be loaded
- **AND** form SHALL be generated dynamically from parameter schema
- **AND** field types SHALL match parameter types (text, number, select, checkbox, etc.)
- **AND** current values SHALL be pre-filled
- **AND** help text/tooltips SHALL be displayed for each parameter

#### Scenario: Group parameters by category
- **WHEN** parameters are displayed
- **THEN** parameters SHALL be grouped into logical sections:
  - Basic Information (name, active status)
  - Symbols (multi-select symbol list)
  - Chart Parameters (timeframes, bars)
  - Risk Management (account size, risk per trade, thresholds)
  - AI/LLM Configuration (model, temperature, tokens)
  - Workflow Settings (delays, retries, auto-trading)
- **AND** each section SHALL be collapsible
- **AND** section SHALL show validation status

### Requirement: Multi-Symbol Management
The system SHALL provide an intuitive interface for managing multiple trading symbols.

#### Scenario: Add symbols to strategy
- **WHEN** user clicks "Add Symbol"
- **THEN** symbol search modal SHALL open
- **AND** user SHALL be able to search by symbol or name
- **AND** search SHALL query IBKR API for valid symbols
- **AND** selected symbol SHALL be added with conid and exchange
- **AND** duplicate symbols SHALL be prevented

#### Scenario: Manage symbol list
- **WHEN** viewing symbol list
- **THEN** each symbol SHALL show: symbol, name, conid, exchange
- **AND** symbols SHALL be drag-and-drop reorderable
- **AND** user SHALL be able to remove symbols
- **AND** at least one symbol SHALL be required

### Requirement: Parameter Validation
The system SHALL validate all parameters before saving with clear error messages.

#### Scenario: Client-side validation
- **WHEN** user modifies parameter
- **THEN** field SHALL be validated in real-time
- **AND** invalid fields SHALL be highlighted in red
- **AND** validation error message SHALL be displayed below field
- **AND** save button SHALL be disabled if errors exist

#### Scenario: Server-side validation
- **WHEN** user clicks save
- **THEN** parameters SHALL be sent to backend validation API
- **AND** backend SHALL validate against business rules
- **AND** validation errors SHALL be displayed
- **AND** successful validation SHALL show green checkmark

#### Scenario: Validation rules
- **THEN** account_size SHALL be > 0
- **AND** risk_per_trade SHALL be between 0 and 1 (0-100%)
- **AND** min_r_coefficient SHALL be > 0
- **AND** min_profit_margin SHALL be >= 0
- **AND** delay_between_symbols SHALL be >= 0
- **AND** temperature SHALL be between 0 and 2
- **AND** max_tokens SHALL be between 1 and 32000

### Requirement: Parameter Templates and Presets
The system SHALL provide templates for common parameter configurations.

#### Scenario: Load parameter template
- **WHEN** user selects template from dropdown
- **THEN** template parameters SHALL be loaded
- **AND** current values SHALL be replaced with template values
- **AND** confirmation dialog SHALL be shown before overwriting
- **AND** user can cancel and revert

#### Scenario: Save custom template
- **WHEN** user clicks "Save as Template"
- **THEN** template name dialog SHALL be shown
- **AND** current parameters SHALL be saved as named template
- **AND** template SHALL be available in dropdown
- **AND** templates SHALL persist across sessions

#### Scenario: Default templates
- **THEN** system SHALL provide default templates:
  - "Conservative" (low risk, high thresholds)
  - "Moderate" (balanced settings)
  - "Aggressive" (high risk, lower thresholds)
  - "Paper Trading" (safe defaults for testing)

### Requirement: Parameter Preview and Impact Analysis
The system SHALL show preview and impact of parameter changes before saving.

#### Scenario: Preview parameter changes
- **WHEN** user clicks "Preview"
- **THEN** comparison view SHALL show old vs new values
- **AND** changed parameters SHALL be highlighted
- **AND** calculated impacts SHALL be displayed:
  - Position sizing based on account size and risk
  - Expected number of trades per day
  - Estimated API costs for AI calls
- **AND** user can review before confirming

#### Scenario: Calculate position size preview
- **WHEN** risk parameters are modified
- **THEN** example position size SHALL be calculated
- **AND** calculation SHALL show:
  - Dollar amount risked per trade
  - Number of shares for example stock price
  - Stop loss distance
- **AND** preview SHALL update in real-time

### Requirement: Parameter History and Rollback
The system SHALL maintain history of parameter changes and allow rollback.

#### Scenario: View parameter history
- **WHEN** user clicks "History"
- **THEN** list of past parameter changes SHALL be displayed
- **AND** each entry SHALL show: timestamp, user, changes
- **AND** user can compare any two versions
- **AND** user can view full parameters for any version

#### Scenario: Rollback to previous parameters
- **WHEN** user selects historical version and clicks "Rollback"
- **THEN** confirmation dialog SHALL be shown
- **AND** parameters SHALL be restored to selected version
- **AND** rollback SHALL be recorded in history
- **AND** success message SHALL be displayed

### Requirement: Batch Parameter Editing
The system SHALL support editing parameters for multiple strategies at once.

#### Scenario: Select multiple strategies
- **WHEN** user is in strategies list view
- **THEN** user SHALL be able to select multiple strategies via checkboxes
- **AND** "Batch Edit" button SHALL become available
- **AND** selected count SHALL be displayed

#### Scenario: Apply common parameter changes
- **WHEN** user clicks "Batch Edit"
- **THEN** batch edit modal SHALL open
- **AND** only common parameters SHALL be editable
- **AND** changes SHALL apply to all selected strategies
- **AND** preview SHALL show impact on each strategy
- **AND** user can confirm or cancel batch changes

### Requirement: Parameter Export and Import
The system SHALL allow exporting and importing parameter configurations.

#### Scenario: Export parameters
- **WHEN** user clicks "Export Parameters"
- **THEN** parameters SHALL be exported as JSON file
- **AND** file SHALL include parameter schema version
- **AND** file SHALL be human-readable
- **AND** file SHALL include metadata (strategy name, export date)

#### Scenario: Import parameters
- **WHEN** user uploads parameter JSON file
- **THEN** file SHALL be validated against schema
- **AND** parameters SHALL be pre-filled from file
- **AND** user can review before saving
- **AND** incompatible parameters SHALL show warnings

### Requirement: Responsive and Accessible UI
The system SHALL provide parameter editor that works on all devices and is accessible.

#### Scenario: Mobile responsiveness
- **WHEN** viewed on mobile device
- **THEN** form SHALL be single-column layout
- **AND** all fields SHALL be usable on touch screen
- **AND** modal dialogs SHALL be full-screen on mobile
- **AND** navigation SHALL be optimized for mobile

#### Scenario: Accessibility
- **WHEN** using keyboard navigation
- **THEN** all form fields SHALL be keyboard accessible
- **AND** tab order SHALL be logical
- **AND** form validation SHALL be screen-reader accessible
- **AND** ARIA labels SHALL be present on all inputs

