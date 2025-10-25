# workflow-builder Specification

## Purpose
TBD - created by archiving change add-fastapi-trading-webapp. Update Purpose after archive.
## Requirements
### Requirement: Workflow Template Management
The system SHALL provide pre-defined workflow templates that users can customize for their trading strategies.

#### Scenario: List workflow templates
- **WHEN** user accesses workflow builder
- **THEN** display available templates:
  - "2-Indicator Multi-Timeframe" (daily + weekly)
  - "3-Indicator Multi-Timeframe" (daily + weekly + monthly)
  - "Single Timeframe" (one chart analysis)
  - "AutoGen Multi-Agent" (collaborative AI decision)
  - "Custom" (build from scratch)
- **AND** each template SHALL have description, steps diagram, typical use case

#### Scenario: Select workflow template
- **WHEN** user selects a template
- **THEN** load template configuration with default steps
- **AND** display workflow steps in visual builder
- **AND** user CAN modify steps, add/remove, reorder

### Requirement: Workflow Definition
The system SHALL allow users to define custom workflows with configurable steps.

#### Scenario: Create new workflow
- **WHEN** user creates new workflow
- **THEN** provide form with: name (required), description, type (select from templates or custom)
- **AND** initialize workflow with empty steps array
- **AND** save workflow to database with status 'draft'

#### Scenario: Define workflow steps
- **WHEN** user adds steps to workflow
- **THEN** each step SHALL have: step_type, order, configuration (JSON)
- **AND** supported step_types:
  - fetch_data: Get historical market data
  - generate_chart: Create technical analysis chart
  - ai_analyze: Send to LLM for analysis
  - consolidate: Merge multiple analysis results
  - decide: Generate trading decision
  - validate_risk: Check risk criteria
  - place_order: Execute order
  - wait: Delay between steps
  - custom_code: Execute custom Python code
- **AND** steps SHALL be executed in order

#### Scenario: Configure step parameters
- **WHEN** user configures a step
- **THEN** show step-specific configuration form
- **AND** for fetch_data: period, bar, indicators[]
- **AND** for ai_analyze: prompt_template, model, temperature, max_tokens
- **AND** for validate_risk: min_r_coefficient, min_profit_margin
- **AND** validate configuration before saving

### Requirement: Visual Workflow Builder
The system SHALL provide a visual interface for building and editing workflows.

#### Scenario: Drag-and-drop workflow builder
- **WHEN** user edits workflow in visual mode
- **THEN** display workflow as connected nodes
- **AND** user CAN drag steps to reorder
- **AND** user CAN click step to configure
- **AND** user CAN add new step with dropdown menu
- **AND** user CAN delete step with confirmation

#### Scenario: Workflow validation
- **WHEN** user saves workflow
- **THEN** validate workflow structure:
  - At least one fetch_data step
  - At least one ai_analyze or decide step
  - validate_risk step before place_order
  - No circular dependencies
- **AND** if invalid, show errors and prevent save
- **AND** if valid, save to database with status 'active'

### Requirement: Workflow Versioning
The system SHALL maintain version history of workflows for tracking changes.

#### Scenario: Create workflow version
- **WHEN** workflow is modified and saved
- **THEN** create new version record: workflow_id, version_number, steps (JSON), created_at, created_by
- **AND** increment version number
- **AND** previous versions SHALL remain accessible

#### Scenario: View workflow history
- **WHEN** user views workflow history
- **THEN** display all versions with: version number, created date, creator, changes summary
- **AND** user CAN view details of any version
- **AND** user CAN revert to previous version

#### Scenario: Rollback workflow version
- **WHEN** user reverts to previous version
- **THEN** create new version with content from selected version
- **AND** mark as "Reverted from v{X}"
- **AND** update active workflow to use reverted version

### Requirement: Workflow Cloning
The system SHALL allow users to duplicate workflows as starting points for customization.

#### Scenario: Clone workflow
- **WHEN** user clicks "Clone" on existing workflow
- **THEN** create copy of workflow with name "{Original Name} (Copy)"
- **AND** copy all steps and configuration
- **AND** assign new workflow ID
- **AND** set status to 'draft'
- **AND** user CAN rename and modify clone

### Requirement: Strategy-Workflow Association
The system SHALL link strategies to workflows, allowing multiple strategies to use the same workflow.

#### Scenario: Assign workflow to strategy
- **WHEN** creating or editing strategy
- **THEN** user SHALL select workflow from dropdown
- **AND** strategy.workflow_id SHALL be set
- **AND** strategy CAN override workflow parameters via strategy.param

#### Scenario: View strategies using workflow
- **WHEN** viewing workflow details
- **THEN** display list of strategies using this workflow
- **AND** show: strategy name, symbols, last execution, status
- **AND** warn if attempting to delete workflow that's in use

### Requirement: Workflow Execution Tracking
The system SHALL track all executions of each workflow with detailed logs.

#### Scenario: Record workflow execution
- **WHEN** workflow executes
- **THEN** create workflow_execution record with: workflow_id, strategy_id, status, started_at, completed_at, results (JSON)
- **AND** for each step executed, log: step_name, duration, status, output
- **AND** link to decisions and orders created

#### Scenario: View workflow execution history
- **WHEN** user views workflow
- **THEN** display execution history table with filters: date range, status, strategy
- **AND** each execution row shows: start time, duration, status, symbols processed, decisions made, orders placed
- **AND** user CAN click to view detailed logs

### Requirement: Workflow Testing
The system SHALL allow users to test workflows without placing real orders.

#### Scenario: Dry-run workflow
- **WHEN** user triggers workflow with dry_run=true
- **THEN** execute all steps normally
- **AND** generate decisions
- **AND** skip place_order step
- **AND** log "Dry run - order not placed: {order details}"
- **AND** return mock order confirmation

#### Scenario: Validate workflow before activation
- **WHEN** user activates workflow
- **THEN** run validation checks:
  - All required configurations present
  - API keys valid
  - LLM endpoints reachable
  - Risk thresholds reasonable
- **AND** display validation results
- **AND** block activation if critical errors

### Requirement: Workflow Parameters
The system SHALL support parameterized workflows that can be customized per strategy.

#### Scenario: Define workflow parameters
- **WHEN** creating workflow
- **THEN** user CAN define parameters: name, type (string/number/boolean/list), default_value, description
- **AND** parameters CAN be referenced in step configurations with {{param_name}} syntax
- **AND** example: {{timeframe_1}}, {{ai_model}}, {{min_r}}

#### Scenario: Override parameters in strategy
- **WHEN** strategy uses workflow
- **THEN** strategy.param CAN override workflow parameters
- **AND** strategy-level values take precedence
- **AND** if parameter not provided, use workflow default

### Requirement: Workflow Marketplace (Future)
The system SHALL support sharing and importing workflows from a community marketplace.

#### Scenario: Export workflow
- **WHEN** user exports workflow
- **THEN** generate JSON file with: workflow definition, steps, parameters, metadata
- **AND** exclude sensitive information (API keys, account IDs)
- **AND** include usage statistics (success rate, average R, win rate) if consented

#### Scenario: Import workflow
- **WHEN** user imports workflow JSON
- **THEN** validate JSON structure
- **AND** create new workflow in database
- **AND** mark as "Imported from {source}"
- **AND** user MUST configure sensitive parameters before use

### Requirement: Conditional Workflow Steps
The system SHALL support conditional execution of steps based on runtime conditions.

#### Scenario: Conditional step execution
- **WHEN** step has condition defined
- **THEN** evaluate condition before executing step
- **AND** conditions support: value comparisons, regex matches, logical operators
- **AND** example: "if RSI < 30, execute step, else skip"
- **AND** if condition false, skip step and continue

#### Scenario: Branching workflows
- **WHEN** workflow has decision point
- **THEN** execute different branches based on condition
- **AND** example: "if trend is bullish, analyze with prompt A, else prompt B"
- **AND** branches SHALL rejoin at merge step

### Requirement: Workflow Metrics and Analytics
The system SHALL provide analytics on workflow performance.

#### Scenario: Workflow performance metrics
- **WHEN** viewing workflow analytics
- **THEN** display:
  - Total executions
  - Success rate (completed vs failed)
  - Average execution time
  - Decisions generated (BUY/SELL/HOLD breakdown)
  - Orders placed
  - Average R-coefficient of decisions
  - Win rate of resulting trades
- **AND** allow filtering by date range, strategy

#### Scenario: Compare workflow performance
- **WHEN** comparing multiple workflows
- **THEN** display side-by-side metrics
- **AND** highlight best-performing workflow for each metric
- **AND** suggest optimization opportunities

