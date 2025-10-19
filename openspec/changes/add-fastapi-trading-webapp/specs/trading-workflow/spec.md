# Trading Workflow Specification

## ADDED Requirements

### Requirement: Automated Trading Workflow Execution
The system SHALL execute an automated trading workflow that analyzes multiple timeframes, generates AI-powered trading decisions, and places orders when risk criteria are met.

#### Scenario: Execute workflow for a strategy
- **WHEN** a user triggers a workflow execution for a strategy
- **THEN** the system SHALL retrieve the strategy configuration
- **AND** iterate through all associated symbols
- **AND** execute the complete analysis workflow for each symbol
- **AND** log all steps and results

#### Scenario: Workflow authentication check
- **WHEN** a workflow starts
- **THEN** the system SHALL verify IBKR authentication status
- **AND** abort with error if not authenticated
- **AND** log the authentication check result

### Requirement: Multi-Timeframe Chart Analysis
The system SHALL analyze both daily and weekly charts to provide comprehensive technical analysis.

#### Scenario: Fetch daily chart data
- **WHEN** workflow executes for a symbol
- **THEN** daily chart data SHALL be fetched using period_1 and bar_1 parameters from strategy
- **AND** data SHALL include OHLCV (Open, High, Low, Close, Volume)
- **AND** data SHALL be cached to market_data table
- **AND** chart SHALL be generated with technical indicators

#### Scenario: Fetch weekly chart data
- **WHEN** workflow executes for a symbol
- **THEN** weekly chart data SHALL be fetched using period_2 and bar_2 parameters from strategy
- **AND** data SHALL include OHLCV
- **AND** data SHALL be cached to market_data table
- **AND** chart SHALL be generated with technical indicators

#### Scenario: Generate chart images
- **WHEN** chart data is fetched
- **THEN** a chart image SHALL be generated with all configured indicators
- **AND** the image SHALL be uploaded to MinIO storage
- **AND** the storage URL SHALL be returned for AI analysis

### Requirement: AI-Powered Chart Analysis
The system SHALL use AI to analyze charts and provide trading insights.

#### Scenario: Analyze daily chart
- **WHEN** daily chart is generated
- **THEN** the chart image SHALL be sent to AI with daily analysis prompt
- **AND** AI SHALL analyze price trends, support/resistance, and indicator signals
- **AND** AI SHALL provide detailed technical analysis in Traditional Chinese
- **AND** the analysis text SHALL be stored

#### Scenario: Analyze weekly chart
- **WHEN** weekly chart is generated
- **THEN** the chart image SHALL be sent to AI with weekly analysis prompt
- **AND** AI SHALL analyze medium-term trends and confirm/contradict daily signals
- **AND** AI SHALL provide trend confirmation analysis in Traditional Chinese
- **AND** the analysis text SHALL be stored

#### Scenario: Consolidate multi-timeframe analysis
- **WHEN** both daily and weekly analyses are complete
- **THEN** the system SHALL send both analyses to AI with consolidation prompt
- **AND** AI SHALL synthesize findings across timeframes
- **AND** AI SHALL provide integrated analysis with trading recommendation
- **AND** the consolidated analysis SHALL be stored

### Requirement: Trading Decision Generation
The system SHALL generate structured trading decisions from AI analysis.

#### Scenario: Generate trading decision
- **WHEN** consolidated analysis is complete
- **THEN** the system SHALL send analysis to AI with decision-making prompt
- **AND** AI SHALL generate structured output with: code, type (buy/sell/hold), current_price, target_price, stop_loss, profit_margin, R_coefficient, strategy_used
- **AND** the decision SHALL be parsed and validated
- **AND** the decision SHALL be stored in the decision table

#### Scenario: Invalid decision output
- **WHEN** AI generates invalid or unparseable decision
- **THEN** the system SHALL log the error
- **AND** retry up to 3 times with clarified prompt
- **AND** abort workflow if still invalid
- **AND** notify user of the failure

### Requirement: Risk Validation
The system SHALL validate trading decisions against risk management rules before order placement.

#### Scenario: Validate R-coefficient threshold
- **WHEN** a trading decision is generated
- **THEN** the system SHALL calculate R_coefficient = (target_price - current_price) / (stop_loss - current_price)
- **AND** if R_coefficient < 1.0, the decision SHALL be rejected
- **AND** rejection reason SHALL be logged

#### Scenario: Validate profit margin threshold
- **WHEN** a trading decision is generated
- **THEN** the system SHALL calculate profit_margin = |target_price - current_price| / current_price
- **AND** if profit_margin < 0.05 (5%), the decision SHALL be rejected
- **AND** rejection reason SHALL be logged

#### Scenario: Validate decision type
- **WHEN** a trading decision is generated
- **THEN** if type is 'hold', no order SHALL be placed
- **AND** if type is 'buy' or 'sell', and risk criteria are met, order SHALL be placed

### Requirement: Automated Order Placement
The system SHALL automatically place orders when trading decisions meet all criteria.

#### Scenario: Place order after successful validation
- **WHEN** a decision passes risk validation and type is 'buy' or 'sell'
- **THEN** an order SHALL be placed via IBKR API
- **AND** order parameters SHALL use: conid, side (BUY/SELL), price (limit order at current_price), quantity (calculated or default), tif (GTC or DAY)
- **AND** order SHALL be stored in orders table linked to decision
- **AND** IBKR order ID SHALL be captured

#### Scenario: Order placement failure
- **WHEN** order placement fails
- **THEN** the error SHALL be logged
- **AND** order status SHALL be marked as 'rejected'
- **AND** workflow SHALL continue with next symbol
- **AND** user SHALL be notified

### Requirement: Workflow Loop and Delay
The system SHALL process multiple symbols with appropriate delays.

#### Scenario: Process multiple symbols
- **WHEN** a strategy has multiple associated codes
- **THEN** the workflow SHALL iterate through each symbol sequentially
- **AND** complete all steps for one symbol before moving to next
- **AND** a configurable delay (default 60 seconds) SHALL be applied between symbols
- **AND** all results SHALL be logged

#### Scenario: Workflow completion
- **WHEN** all symbols have been processed
- **THEN** the workflow SHALL complete
- **AND** summary results SHALL be provided (symbols processed, decisions made, orders placed)
- **AND** workflow status SHALL be updated to 'completed'

### Requirement: Workflow Error Handling
The system SHALL handle errors gracefully and continue processing when possible.

#### Scenario: Handle per-symbol errors
- **WHEN** an error occurs processing a specific symbol
- **THEN** the error SHALL be logged with context
- **AND** the workflow SHALL continue with the next symbol
- **AND** failed symbols SHALL be reported in summary

#### Scenario: Handle critical errors
- **WHEN** a critical error occurs (e.g., database connection lost, IBKR auth expired)
- **THEN** the workflow SHALL abort
- **AND** the error SHALL be logged
- **AND** user SHALL be notified
- **AND** partial results SHALL be preserved

### Requirement: Workflow Logging and Audit Trail
The system SHALL log all workflow steps for debugging and compliance.

#### Scenario: Log workflow execution
- **WHEN** workflow executes
- **THEN** each step SHALL be logged with timestamp, symbol, step name, and result
- **AND** AI prompts and responses SHALL be logged
- **AND** order placement attempts SHALL be logged
- **AND** logs SHALL be searchable by workflow ID, symbol, or date range

### Requirement: Manual Workflow Trigger
The system SHALL allow users to manually trigger workflow execution.

#### Scenario: Trigger workflow via API
- **WHEN** user calls POST /api/workflow/execute with strategy_id
- **THEN** the workflow SHALL start asynchronously
- **AND** a workflow execution ID SHALL be returned
- **AND** status SHALL be 'running'

#### Scenario: Check workflow status
- **WHEN** user calls GET /api/workflow/status/{id}
- **THEN** current workflow status SHALL be returned
- **AND** status SHALL be one of: 'pending', 'running', 'completed', 'failed'
- **AND** progress information SHALL be included (current symbol, step, completed/total)

### Requirement: Strategy Parameter Configuration
The system SHALL use configurable strategy parameters for flexible workflow execution.

#### Scenario: Parse strategy parameters
- **WHEN** workflow loads a strategy
- **THEN** param field SHALL be parsed as JSON
- **AND** period_1, bar_1, period_2, bar_2 SHALL be extracted
- **AND** default values SHALL be used if parameters are missing
- **AND** parameter validation SHALL occur before execution

#### Scenario: Default parameters
- **WHEN** strategy parameters are missing or invalid
- **THEN** default values SHALL be used: period_1='1y', bar_1='1d', period_2='1y', bar_2='1w'
- **AND** a warning SHALL be logged

## ADDED Requirements

### Requirement: Concurrent Workflow Execution via Task Queue
The system SHALL execute workflows as asynchronous tasks to enable concurrent processing of multiple strategies.

#### Scenario: Submit workflow to task queue
- **WHEN** workflow execution is triggered
- **THEN** create Celery task with workflow parameters
- **AND** return task_id immediately
- **AND** task SHALL be queued in Redis
- **AND** available worker SHALL pick up task

#### Scenario: Multiple workflows execute concurrently
- **WHEN** multiple workflows are submitted
- **THEN** workers SHALL process tasks concurrently
- **AND** each workflow SHALL execute independently
- **AND** workflows SHALL not block each other
- **AND** resource limits SHALL be respected per worker

### Requirement: Workflow Template Support
The system SHALL support different workflow templates including AutoGen multi-agent workflows.

#### Scenario: Execute AutoGen workflow
- **WHEN** strategy workflow_type is 'autogen_multi_agent'
- **THEN** initialize AutoGen agent orchestrator
- **AND** load agent configurations from strategy.param.autogen_config
- **AND** execute multi-agent decision process instead of single LLM call
- **AND** extract final decision from ExecutorAgent
- **AND** continue with risk validation and order placement

#### Scenario: Execute custom workflow
- **WHEN** strategy has custom workflow definition
- **THEN** load workflow steps from database
- **AND** execute each step in defined order
- **AND** pass output of one step as input to next
- **AND** support conditional step execution

### Requirement: Workflow-Strategy Separation
The system SHALL separate workflow definitions from strategy configurations for flexibility.

#### Scenario: Strategy references workflow
- **WHEN** strategy is created or updated
- **THEN** strategy SHALL reference workflow via workflow_id
- **AND** workflow SHALL define execution steps
- **AND** strategy SHALL provide parameters and symbols
- **AND** multiple strategies CAN use same workflow

#### Scenario: Workflow parameter override
- **WHEN** executing strategy with workflow
- **THEN** load workflow definition
- **AND** merge strategy.param with workflow.default_params
- **AND** strategy parameters SHALL override workflow defaults
- **AND** execute workflow with merged parameters

