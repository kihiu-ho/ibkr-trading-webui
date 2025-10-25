# Order Management Capability - Spec Deltas

## ADDED Requirements

### Requirement: Automated Order Placement
The system SHALL automatically place orders to IBKR based on trading signals.

#### Scenario: Place buy order on buy signal
- **WHEN** a trading signal with action "BUY" is generated
- **THEN** the system SHALL calculate position size based on risk parameters
- **AND** the system SHALL validate available capital
- **AND** the system SHALL place a limit order to IBKR at the signal's entry price
- **AND** the system SHALL record the order in the database
- **AND** the system SHALL start monitoring the order status

#### Scenario: Position size calculation
- **WHEN** calculating position size for an order
- **THEN** the system SHALL use the formula: `Position Size = (Account Risk) / (Entry Price - Stop Loss)`
- **WHERE** Account Risk = Available Capital × Risk Percent (from strategy)
- **AND** the position size SHALL be at least 1 share
- **AND** the position size SHALL not exceed available capital / entry price

#### Scenario: Place sell order on sell signal
- **WHEN** a trading signal with action "SELL" is generated
- **AND** the strategy has an open position for that symbol
- **THEN** the system SHALL place a sell order for the entire position quantity
- **AND** the system SHALL use a limit order at the signal's entry price
- **AND** the system SHALL start monitoring the order status

### Requirement: Order Status Tracking
The system SHALL continuously monitor order status until completion or cancellation.

#### Scenario: Monitor order until filled
- **WHEN** an order is placed
- **THEN** the system SHALL poll IBKR every 10 seconds for order status
- **AND** the system SHALL update the order status in the database
- **AND** the system SHALL continue monitoring until the order reaches a terminal state (FILLED, CANCELLED, REJECTED)
- **AND** the system SHALL time out after 24 hours

#### Scenario: Order filled
- **WHEN** an order status changes to "FILLED"
- **THEN** the system SHALL record the fill price and quantity
- **AND** for buy orders, the system SHALL create or update the position
- **AND** for sell orders, the system SHALL close the position
- **AND** the system SHALL record a trade in the `trades` table
- **AND** the system SHALL update the trading signal's outcome
- **AND** the system SHALL send a notification to the user

#### Scenario: Order cancelled or rejected
- **WHEN** an order status changes to "CANCELLED" or "REJECTED"
- **THEN** the system SHALL record the reason
- **AND** the system SHALL log the event
- **AND** the system SHALL send a notification to the user
- **AND** the system SHALL not update any positions

### Requirement: Position Management
The system SHALL track and manage all open positions.

#### Scenario: Create position on buy order fill
- **WHEN** a buy order is filled
- **THEN** the system SHALL create a new position record
- **AND** the position SHALL include: symbol, quantity, average cost, stop loss, target price, and strategy ID
- **AND** the position SHALL be marked as "OPEN"

#### Scenario: Close position on sell order fill
- **WHEN** a sell order is filled
- **THEN** the system SHALL close the position
- **AND** the system SHALL calculate realized P&L: (Sell Price - Buy Price) × Quantity
- **AND** the system SHALL record the exit price and time
- **AND** the position SHALL be marked as "CLOSED"

#### Scenario: Stop-loss monitoring
- **WHEN** the system checks open positions
- **THEN** for each position with a stop loss, the system SHALL:
  - Fetch the current market price from IBKR
  - If current price ≤ stop loss, trigger a sell order
  - Record the stop-loss trigger event
- **AND** the system SHALL check positions every 60 seconds

#### Scenario: Take-profit monitoring
- **WHEN** the system checks open positions
- **THEN** for each position with a target price, the system SHALL:
  - Fetch the current market price from IBKR
  - If current price ≥ target price, trigger a sell order
  - Record the take-profit trigger event
- **AND** the system SHALL check positions every 60 seconds

### Requirement: Risk Management
The system SHALL enforce risk management rules for all orders.

#### Scenario: Validate available capital
- **WHEN** placing a buy order
- **THEN** the system SHALL verify that available capital ≥ (order quantity × entry price)
- **AND** if insufficient capital, the system SHALL reduce the order quantity
- **OR** if capital is too low for even 1 share, the system SHALL reject the order
- **AND** the system SHALL log the event

#### Scenario: Enforce maximum position size
- **WHEN** calculating position size
- **THEN** the system SHALL ensure the position size does not exceed a configurable maximum
- **AND** if the calculated size exceeds the maximum, the system SHALL use the maximum size instead
- **AND** the system SHALL log the adjustment

---

## MODIFIED Requirements

_None - this is a new capability_

---

## REMOVED Requirements

_None - this is a new capability_


