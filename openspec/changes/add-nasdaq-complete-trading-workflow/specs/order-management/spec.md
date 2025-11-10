## ADDED Requirements
### Requirement: Order Placement from Airflow Workflow
The system SHALL place orders to IBKR from Airflow workflow tasks when trading signals are actionable.

#### Scenario: Place order from workflow task
- **WHEN** Airflow workflow task receives actionable trading signal
- **THEN** the system SHALL:
  - Validate signal (is_actionable=True, confidence=HIGH or MEDIUM)
  - Get symbol contract ID (conid) from IBKR
  - Calculate order quantity (from signal or fixed position size)
  - Construct order payload (conid, side, orderType, price, quantity, tif)
  - Submit order via IBKR API POST /v1/api/iserver/account/{accountId}/orders
  - Store order artifact with workflow metadata (execution_id, step_name)
  - Return order confirmation with order_id

#### Scenario: Store order artifact
- **WHEN** order is placed from workflow
- **THEN** order artifact SHALL be stored with:
  - workflow_id (e.g., "ibkr_trading_signal_workflow")
  - execution_id (Airflow run identifier)
  - step_name (e.g., "place_order")
  - symbol (e.g., "TSLA", "NVDA")
  - order_id (IBKR order identifier)
  - order_type (LMT, MKT)
  - side (BUY, SELL)
  - quantity
  - price (for limit orders)
  - status (submitted, filled, cancelled)
  - link to trading signal artifact that triggered the order

### Requirement: Order Status Tracking from Workflow
The system SHALL track order status and update artifacts when orders are filled.

#### Scenario: Poll order status in workflow
- **WHEN** order is placed from workflow
- **THEN** workflow SHALL:
  - Poll IBKR API for order status
  - Update order artifact when status changes
  - Create trade artifact when order is filled
  - Link trade artifact to order and execution_id

