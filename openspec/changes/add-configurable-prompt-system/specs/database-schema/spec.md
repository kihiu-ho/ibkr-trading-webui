# Database Schema Spec Deltas

## ADDED Requirements

### Requirement: Prompt Templates Table
The system SHALL store LLM prompt templates in the database.

#### Scenario: Create prompt_templates table
- **GIVEN** database migration is run
- **WHEN** creating the prompt_templates table
- **THEN** the table SHALL have columns:
  - id: UUID primary key
  - name: VARCHAR(255) NOT NULL - human-readable name
  - description: TEXT - optional description of prompt purpose
  - prompt_type: VARCHAR(50) NOT NULL - enum: daily_chart, weekly_chart, consolidation, decision
  - language: VARCHAR(10) NOT NULL DEFAULT 'en' - enum: en, zh
  - content: TEXT NOT NULL - the actual prompt template text
  - version: INTEGER NOT NULL DEFAULT 1 - increments on each update
  - is_active: BOOLEAN NOT NULL DEFAULT TRUE - whether prompt is active
  - is_default: BOOLEAN NOT NULL DEFAULT FALSE - whether this is the default for its type+language
  - created_at: TIMESTAMP NOT NULL DEFAULT NOW()
  - updated_at: TIMESTAMP NOT NULL DEFAULT NOW()
  - created_by: VARCHAR(255) - username/email of creator
  - deleted_at: TIMESTAMP NULL - soft delete timestamp

#### Scenario: Create indexes for performance
- **GIVEN** prompt_templates table exists
- **WHEN** creating indexes
- **THEN** the system SHALL create:
  - Index on (prompt_type, language, is_active) WHERE deleted_at IS NULL
  - Unique index on (prompt_type, language, is_default) WHERE is_default=TRUE AND deleted_at IS NULL
  - Index on created_at for sorting
  - Index on version for history queries

#### Scenario: Add check constraints
- **GIVEN** prompt_templates table exists
- **WHEN** defining constraints
- **THEN** the system SHALL enforce:
  - prompt_type IN ('daily_chart', 'weekly_chart', 'consolidation', 'decision')
  - language IN ('en', 'zh')
  - content IS NOT NULL and length > 0
  - version >= 1

### Requirement: Signal-Prompt Linking
The system SHALL link trading signals to the prompt template used to generate them.

#### Scenario: Add prompt reference to signals
- **GIVEN** trading_signals table exists
- **WHEN** adding prompt traceability
- **THEN** the system SHALL:
  - Add column prompt_template_id UUID REFERENCES prompt_templates(id)
  - Add column prompt_version INTEGER - snapshot of version at generation time
  - Create index on prompt_template_id for queries
  - Allow NULL values (for signals before this feature)

#### Scenario: Query signals by prompt
- **GIVEN** an administrator wants to analyze prompt performance
- **WHEN** querying signals
- **THEN** the system SHALL support joins:
  - SELECT * FROM trading_signals JOIN prompt_templates ON prompt_template_id
  - Filter by prompt name, type, or version
  - Aggregate outcomes by prompt

### Requirement: Prompt Versioning
The system SHALL maintain version history for prompt templates.

#### Scenario: Increment version on update
- **GIVEN** a prompt template with version=3 is updated
- **WHEN** saving the changes
- **THEN** the system SHALL:
  - Increment version to 4
  - Update updated_at timestamp
  - Preserve old version (via soft delete pattern or separate row)

#### Scenario: Soft delete preserves history
- **GIVEN** a prompt template is deleted
- **WHEN** DELETE operation is performed
- **THEN** the system SHALL:
  - Set deleted_at = NOW()
  - Keep the row in database
  - Exclude from default queries (WHERE deleted_at IS NULL)
  - Allow recovery by clearing deleted_at

#### Scenario: Query version history
- **GIVEN** a prompt template has multiple versions
- **WHEN** querying history
- **THEN** the system SHALL return:
  - All versions ordered by version DESC
  - Including soft-deleted versions
  - Show who made each change and when

### Requirement: Default Prompt Management
The system SHALL enforce exactly one default prompt per (type, language) combination.

#### Scenario: Set prompt as default
- **GIVEN** a user activates a prompt as default for daily_chart + en
- **WHEN** setting is_default=TRUE
- **THEN** the system SHALL:
  - Set is_default=FALSE for any other daily_chart + en prompt
  - Set is_default=TRUE for the selected prompt
  - Ensure unique index is satisfied

#### Scenario: Prevent multiple defaults
- **GIVEN** a default prompt exists for (daily_chart, en)
- **WHEN** trying to create another default for same (type, language)
- **THEN** the system SHALL:
  - Raise constraint violation error
  - Reject the insert/update
  - Suggest deactivating existing default first

#### Scenario: Load default prompt
- **GIVEN** a query for default prompt
- **WHEN** SELECT WHERE prompt_type='daily_chart' AND language='en' AND is_default=TRUE
- **THEN** the system SHALL return exactly one row or zero rows

