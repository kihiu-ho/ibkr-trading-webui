## ADDED Requirements
### Requirement: Trade Retrieval from IBKR in Workflow
The system SHALL retrieve executed trades from IBKR and store them as artifacts in Airflow workflows.

#### Scenario: Retrieve trades from IBKR
- **WHEN** workflow completes order placement
- **THEN** the system SHALL:
  - Query IBKR API for executed trades (GET /v1/api/iserver/account/trades)
  - Filter trades for symbols processed in current workflow execution
  - Store trade artifacts with:
    - workflow_id and execution_id
    - symbol, quantity, price, timestamp
    - order_id reference
    - P&L if available
  - Link trades to corresponding order artifacts

### Requirement: Portfolio Snapshot from Workflow
The system SHALL retrieve portfolio positions from IBKR and store as artifacts.

#### Scenario: Retrieve portfolio snapshot
- **WHEN** workflow completes trade tracking
- **THEN** the system SHALL:
  - Fetch current portfolio positions from IBKR API (GET /v1/api/portfolio/{accountId}/positions)
  - Calculate unrealized P&L for each position
  - Store portfolio snapshot as artifact with:
    - workflow_id and execution_id
    - timestamp of snapshot
    - list of positions with symbol, quantity, average_cost, current_price, unrealized_pnl
    - total portfolio value
    - total unrealized P&L
  - Link portfolio artifact to execution_id for workflow grouping

### Requirement: Portfolio Artifact Storage
The system SHALL store portfolio snapshots as artifacts with workflow metadata.

#### Scenario: Store portfolio artifact
- **WHEN** portfolio snapshot is retrieved in workflow
- **THEN** portfolio artifact SHALL include:
  - type="portfolio"
  - workflow_id and execution_id
  - step_name (e.g., "get_portfolio")
  - portfolio_data (JSON with positions, values, P&L)
  - timestamp of snapshot

