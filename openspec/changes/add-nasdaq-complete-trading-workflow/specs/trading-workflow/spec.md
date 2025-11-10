## ADDED Requirements
### Requirement: Multi-Symbol NASDAQ Workflow
The system SHALL support processing multiple NASDAQ symbols (TSLA, NVDA) in a single workflow execution.

#### Scenario: Process multiple symbols in parallel
- **WHEN** workflow is triggered with symbol list ["TSLA", "NVDA"]
- **THEN** the system SHALL fetch market data for all symbols in parallel
- **AND** generate charts (daily and weekly) for each symbol
- **AND** analyze each symbol's charts with LLM independently
- **AND** generate trading signals for each symbol
- **AND** store all artifacts with proper symbol tagging

#### Scenario: Workflow with symbol parameter
- **WHEN** DAG is configured with SYMBOLS=["TSLA", "NVDA"]
- **THEN** workflow SHALL process each symbol through complete pipeline:
  - Market data fetching
  - Daily chart generation
  - Weekly chart generation
  - LLM analysis
  - Signal generation
  - Order placement (if signal is actionable)
  - Trade tracking
  - Portfolio update

### Requirement: Order Placement from Workflow
The system SHALL place orders to IBKR when trading signals are actionable.

#### Scenario: Place order from workflow
- **WHEN** LLM generates actionable trading signal (BUY or SELL with HIGH confidence)
- **THEN** workflow SHALL:
  - Validate signal is actionable (is_actionable=True)
  - Calculate order quantity based on position size or risk parameters
  - Place order via IBKR API
  - Store order artifact with execution_id linkage
  - Track order status until filled or cancelled

#### Scenario: Skip order placement for non-actionable signals
- **WHEN** LLM generates HOLD signal or LOW confidence signal
- **THEN** workflow SHALL skip order placement
- **AND** log signal for review
- **AND** continue to portfolio tracking step

### Requirement: Trade Retrieval from IBKR
The system SHALL retrieve executed trades from IBKR and store them as artifacts.

#### Scenario: Retrieve trades after order placement
- **WHEN** order is placed and filled
- **THEN** workflow SHALL:
  - Query IBKR API for executed trades
  - Match trades to placed orders
  - Store trade artifacts with execution_id
  - Include trade details: symbol, quantity, price, timestamp, P&L

### Requirement: Portfolio Management from Workflow
The system SHALL retrieve and update portfolio positions from IBKR.

#### Scenario: Retrieve portfolio positions
- **WHEN** workflow completes order placement and trade tracking
- **THEN** workflow SHALL:
  - Fetch current portfolio positions from IBKR API
  - Calculate unrealized P&L for each position
  - Store portfolio snapshot as artifact
  - Link portfolio artifact to execution_id

