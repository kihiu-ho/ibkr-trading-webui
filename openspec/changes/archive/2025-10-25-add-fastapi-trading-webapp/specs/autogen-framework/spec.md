# AutoGen Framework Specification

## ADDED Requirements

### Requirement: Microsoft AutoGen Integration
The system SHALL integrate Microsoft AutoGen framework for multi-agent collaborative decision-making in trading workflows.

#### Scenario: AutoGen installation and configuration
- **WHEN** the application starts
- **THEN** AutoGen library SHALL be installed and configured
- **AND** agent configurations SHALL be loaded from database or config files
- **AND** LLM clients SHALL be configured for each agent

#### Scenario: Agent initialization
- **WHEN** AutoGen workflow is triggered
- **THEN** required agents SHALL be initialized with their configurations
- **AND** each agent SHALL have: name, system_prompt, llm_config, tools, max_consecutive_auto_reply
- **AND** agents SHALL be registered with GroupChat orchestrator

### Requirement: Multi-Agent Decision Making
The system SHALL use multiple specialized agents to collaboratively analyze and make trading decisions.

#### Scenario: Technical analysis agent
- **WHEN** technical analysis is needed
- **THEN** TechnicalAnalystAgent SHALL be invoked
- **AND** agent SHALL analyze chart images and technical indicators
- **AND** agent SHALL provide insights on: trend direction, support/resistance levels, indicator signals, chart patterns
- **AND** agent SHALL use vision-capable model if analyzing chart images

#### Scenario: Risk management agent
- **WHEN** risk assessment is needed
- **THEN** RiskManagerAgent SHALL be invoked
- **AND** agent SHALL calculate: position size, stop-loss levels, take-profit targets, R-coefficient
- **AND** agent SHALL validate risk criteria
- **AND** agent SHALL have access to risk calculation tools

#### Scenario: Fundamental analysis agent
- **WHEN** fundamental analysis is configured
- **THEN** FundamentalAgent SHALL be invoked (optional)
- **AND** agent SHALL analyze: earnings reports, revenue trends, P/E ratios, news sentiment
- **AND** agent SHALL access financial data APIs if configured

#### Scenario: Sentiment analysis agent
- **WHEN** market sentiment analysis is configured
- **THEN** SentimentAgent SHALL be invoked (optional)
- **AND** agent SHALL analyze social media, news headlines, market sentiment indicators
- **AND** agent SHALL provide sentiment score and rationale

#### Scenario: Executor agent coordination
- **WHEN** all analyses are complete
- **THEN** ExecutorAgent SHALL consolidate all inputs
- **AND** agent SHALL weigh different perspectives
- **AND** agent SHALL make final trading decision: BUY, SELL, or HOLD
- **AND** agent SHALL provide comprehensive reasoning

### Requirement: Agent Communication and Consensus
The system SHALL enable agents to communicate, debate, and reach consensus on trading decisions.

#### Scenario: Agent conversation
- **WHEN** AutoGen workflow executes
- **THEN** agents SHALL exchange messages in sequence or rounds
- **AND** each agent SHALL respond based on previous messages
- **AND** conversation SHALL be limited to max_rounds (default 10)
- **AND** all messages SHALL be logged to database

#### Scenario: Consensus building
- **WHEN** agents have different opinions
- **THEN** agents SHALL debate and provide counterarguments
- **AND** ExecutorAgent SHALL mediate and synthesize consensus
- **AND** if no consensus after max_rounds, default to conservative decision (HOLD)

#### Scenario: Conversation termination
- **WHEN** ExecutorAgent makes final decision
- **THEN** conversation SHALL terminate
- **AND** termination message SHALL include: decision (BUY/SELL/HOLD), confidence level, summary of key factors
- **AND** decision SHALL be returned to workflow

### Requirement: Agent Tool Execution
The system SHALL provide agents with tools to perform calculations and data retrieval.

#### Scenario: Code execution tool
- **WHEN** agent needs to perform custom calculation
- **THEN** agent SHALL generate Python code
- **AND** code SHALL be executed in sandboxed environment (Docker container)
- **AND** execution result SHALL be returned to agent
- **AND** agent SHALL use result in reasoning

#### Scenario: Risk calculation tool
- **WHEN** RiskManagerAgent needs to calculate risk metrics
- **THEN** tool SHALL be called with: current_price, target_price, stop_loss, account_equity
- **AND** tool SHALL return: R_coefficient, position_size, risk_amount, profit_potential
- **AND** agent SHALL incorporate calculations into recommendation

#### Scenario: Market data tool
- **WHEN** agent needs additional market data
- **THEN** tool SHALL fetch: latest price, volume, market cap, volatility metrics
- **AND** data SHALL be returned in structured format
- **AND** agent SHALL use data for analysis

### Requirement: Agent Configuration Management
The system SHALL allow flexible configuration of agent behaviors and models.

#### Scenario: Per-agent LLM configuration
- **WHEN** agents are configured
- **THEN** each agent CAN use different LLM model
- **AND** TechnicalAnalystAgent MAY use vision model (e.g., GPT-4 Vision, Gemini Pro Vision)
- **AND** RiskManagerAgent MAY use cheaper, faster model (e.g., GPT-3.5)
- **AND** ExecutorAgent MAY use most capable model for synthesis

#### Scenario: Custom agent prompts
- **WHEN** strategy is configured with AutoGen workflow
- **THEN** user CAN customize system prompts for each agent
- **AND** prompts SHALL be stored in strategy.param.autogen_config.agents
- **AND** prompts SHALL be loaded and applied when agents are initialized

#### Scenario: Agent enablement
- **WHEN** configuring AutoGen workflow
- **THEN** user CAN enable/disable specific agents
- **AND** required agents (TechnicalAnalyst, RiskManager, Executor) SHALL always be enabled
- **AND** optional agents (Fundamental, Sentiment) CAN be toggled on/off

### Requirement: Human-in-the-Loop
The system SHALL support human oversight and intervention in AutoGen workflows.

#### Scenario: Manual approval mode
- **WHEN** strategy is configured with human_approval=true
- **THEN** after agents reach consensus, pause for human review
- **AND** send notification to user with decision and reasoning
- **AND** user CAN approve, reject, or modify decision
- **AND** workflow SHALL wait for user input (with timeout)

#### Scenario: Human input timeout
- **WHEN** waiting for human input
- **THEN** if no response within timeout (default 5 minutes)
- **AND** default to conservative action (HOLD, no order placed)
- **AND** log timeout event

### Requirement: Agent Conversation Logging
The system SHALL log all agent interactions for auditability and debugging.

#### Scenario: Log agent messages
- **WHEN** agents exchange messages
- **THEN** each message SHALL be logged with: timestamp, agent_name, message_content, message_type (request/response)
- **AND** logs SHALL be stored in database table: agent_conversations
- **AND** logs SHALL be linked to workflow_execution_id

#### Scenario: View agent conversation
- **WHEN** user views workflow execution details
- **THEN** display full agent conversation thread
- **AND** highlight key insights from each agent
- **AND** show final consensus decision and reasoning

### Requirement: AutoGen Workflow Type
The system SHALL support AutoGen as a distinct workflow type alongside standard workflows.

#### Scenario: Select AutoGen workflow
- **WHEN** creating or editing strategy
- **THEN** user CAN select workflow type: 'two_indicator' (standard) or 'autogen_multi_agent'
- **AND** if 'autogen_multi_agent' selected, show AutoGen configuration options
- **AND** configuration options include: enabled agents, agent prompts, LLM models per agent, max_rounds, human_approval

#### Scenario: Execute AutoGen workflow
- **WHEN** AutoGen workflow is triggered
- **THEN** fetch chart data as usual
- **AND** instead of single LLM call, initiate AutoGen group chat
- **AND** agents analyze and debate
- **AND** extract final decision from ExecutorAgent
- **AND** continue with risk validation and order placement

### Requirement: Agent Performance Tracking
The system SHALL track and report on agent performance and contribution to decisions.

#### Scenario: Track agent contribution
- **WHEN** decision results in trade
- **THEN** analyze which agent's input was most influential
- **AND** track agent accuracy: if agent recommended BUY and trade was profitable, increment accuracy score
- **AND** store agent performance metrics in database

#### Scenario: Agent performance dashboard
- **WHEN** user views AutoGen analytics
- **THEN** display per-agent metrics: decisions influenced, accuracy rate, average confidence, tokens used
- **AND** identify most/least valuable agents
- **AND** suggest agent configuration improvements

### Requirement: Error Handling in AutoGen Workflows
The system SHALL handle errors gracefully during agent execution.

#### Scenario: Agent API failure
- **WHEN** agent's LLM API call fails
- **THEN** retry up to 3 times with exponential backoff
- **AND** if still failing, exclude agent from conversation
- **AND** log error and continue with remaining agents
- **AND** if all agents fail, abort workflow

#### Scenario: Code execution error
- **WHEN** agent's code execution fails
- **THEN** return error message to agent
- **AND** agent CAN retry with corrected code
- **AND** limit code execution attempts to 3 per agent
- **AND** if code execution repeatedly fails, agent SHALL proceed without computation

#### Scenario: Conversation stall
- **WHEN** agents cannot reach consensus within max_rounds
- **THEN** ExecutorAgent SHALL make unilateral decision based on available information
- **AND** log "No consensus reached" with reason
- **AND** decision SHALL be conservative (prefer HOLD over risky BUY/SELL)

### Requirement: AutoGen Docker Configuration
The system SHALL configure AutoGen code execution in secure, isolated environment.

#### Scenario: Code execution sandbox
- **WHEN** AutoGen code execution is enabled
- **THEN** code SHALL run in separate Docker container
- **AND** container SHALL have limited resources (CPU, memory, timeout)
- **AND** container SHALL have access only to allowed libraries (numpy, pandas, scipy)
- **AND** network access SHALL be disabled for security

#### Scenario: Code execution result
- **WHEN** code executes successfully
- **THEN** return result to agent
- **AND** include stdout, stderr, and return value
- **AND** if result is large (>1MB), store in MinIO and return reference

