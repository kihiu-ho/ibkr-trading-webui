# Order Management Specification

## ADDED Requirements

### Requirement: Order Placement
The system SHALL provide capabilities to place orders with IBKR through the Client Portal Gateway API.

#### Scenario: Place limit order
- **WHEN** a user or workflow requests to place an order
- **THEN** the system SHALL construct order payload with: conid, side (BUY/SELL), orderType (LMT), price, quantity, tif (GTC/DAY)
- **AND** submit order via POST /v1/api/iserver/account/{accountId}/orders
- **AND** store order in database with status 'submitted'
- **AND** return order confirmation to caller

#### Scenario: Order validation
- **WHEN** an order is submitted
- **THEN** the system SHALL validate: conid is valid, price is positive, quantity is positive integer, side is BUY or SELL
- **AND** reject invalid orders before submitting to IBKR
- **AND** log validation errors

### Requirement: Order Status Tracking
The system SHALL track the lifecycle of all orders.

#### Scenario: Poll order status
- **WHEN** an order is placed
- **THEN** the system SHALL periodically check status via GET /v1/api/iserver/account/orders
- **AND** update order status in database when it changes
- **AND** trigger trade record creation when status becomes 'filled'

#### Scenario: Update order status
- **WHEN** order status changes
- **THEN** the orders table SHALL be updated with new status and updated_at timestamp
- **AND** if status is 'filled', entry price and quantity SHALL be captured
- **AND** associated position SHALL be updated

### Requirement: Order Cancellation
The system SHALL allow cancellation of pending orders.

#### Scenario: Cancel order
- **WHEN** a user requests to cancel an order
- **THEN** the system SHALL call DELETE /v1/api/iserver/account/{accountId}/order/{orderId}
- **AND** update order status to 'cancelled' in database
- **AND** return cancellation confirmation

#### Scenario: Cancel order validation
- **WHEN** cancel is requested
- **THEN** the system SHALL verify order exists and is not already filled
- **AND** reject cancellation of filled or already cancelled orders

### Requirement: Order History
The system SHALL maintain complete order history.

#### Scenario: Query order history
- **WHEN** a user queries order history
- **THEN** the system SHALL return orders filtered by: date range, status, symbol, strategy
- **AND** include associated decision and strategy information
- **AND** sort by created_at descending by default

### Requirement: Order Quantity Calculation
The system SHALL calculate appropriate order quantities based on risk parameters.

#### Scenario: Calculate position size
- **WHEN** placing an order
- **THEN** if quantity is not specified, calculate based on: account equity, risk per trade (default 1%), distance to stop-loss
- **AND** formula: quantity = (account_equity * risk_percent) / |current_price - stop_loss|
- **AND** round down to integer
- **AND** enforce minimum quantity of 1

#### Scenario: Use specified quantity
- **WHEN** quantity is explicitly provided
- **THEN** use the provided quantity
- **AND** validate it is a positive integer

