# Risk Management Specification

## ADDED Requirements

### Requirement: R-Coefficient Validation
The system SHALL enforce minimum R-coefficient thresholds before order placement.

#### Scenario: Calculate R-coefficient
- **WHEN** a trading decision is made
- **THEN** R-coefficient SHALL be calculated as: (target_price - current_price) / (stop_loss - current_price)
- **AND** for sell decisions: (current_price - target_price) / (current_price - stop_loss)
- **AND** result SHALL be stored with decision

#### Scenario: Enforce R-coefficient threshold
- **WHEN** validating a decision for order placement
- **THEN** if R-coefficient < 1.0, order SHALL be rejected
- **AND** rejection reason "R-coefficient below minimum 1.0" SHALL be logged
- **AND** decision status SHALL be marked as 'rejected'

### Requirement: Profit Margin Validation
The system SHALL enforce minimum profit margin thresholds.

#### Scenario: Calculate profit margin
- **WHEN** a trading decision is made
- **THEN** profit_margin SHALL be calculated as: |target_price - current_price| / current_price
- **AND** result SHALL be expressed as decimal (0.05 = 5%)
- **AND** result SHALL be stored with decision

#### Scenario: Enforce profit margin threshold
- **WHEN** validating a decision for order placement
- **THEN** if profit_margin < 0.05 (5%), order SHALL be rejected
- **AND** rejection reason "Profit margin below minimum 5%" SHALL be logged
- **AND** decision status SHALL be marked as 'rejected'

### Requirement: Stop-Loss Calculation
The system SHALL calculate appropriate stop-loss levels based on technical indicators.

#### Scenario: Calculate stop-loss from AI analysis
- **WHEN** AI generates trading decision
- **THEN** stop-loss SHALL be provided in structured output
- **AND** if not provided, calculate as: current_price ± (2 × ATR)
- **AND** for buy: stop-loss = current_price - (2 × ATR)
- **AND** for sell: stop-loss = current_price + (2 × ATR)

### Requirement: Position Sizing
The system SHALL calculate position sizes based on risk management rules.

#### Scenario: Risk-based position sizing
- **WHEN** calculating order quantity
- **THEN** the system SHALL retrieve account equity
- **AND** apply risk percentage (default 1% per trade)
- **AND** calculate: quantity = (equity × risk_percent) / |entry_price - stop_loss|
- **AND** round down to integer shares
- **AND** enforce minimum quantity of 1

#### Scenario: Maximum position size
- **WHEN** calculating position size
- **THEN** quantity SHALL NOT exceed maximum position size (default 10% of equity / current_price)
- **AND** if calculated quantity exceeds max, use max instead
- **AND** log position size adjustment

### Requirement: Portfolio Risk Limits
The system SHALL enforce portfolio-level risk limits.

#### Scenario: Check total exposure
- **WHEN** placing a new order
- **THEN** calculate total portfolio exposure (sum of all position values)
- **AND** if new position would exceed max portfolio exposure (default 90%), reject order
- **AND** log "Portfolio exposure limit exceeded"

#### Scenario: Check maximum open positions
- **WHEN** placing a new order
- **THEN** count current open positions
- **AND** if count >= max positions (default 10), reject new order
- **AND** log "Maximum open positions limit reached"

### Requirement: Risk Metrics Reporting
The system SHALL calculate and report risk metrics for portfolio.

#### Scenario: Calculate portfolio risk metrics
- **WHEN** user views risk dashboard
- **THEN** the system SHALL calculate:
  - Total portfolio value
  - Total exposure (sum of position values)
  - Exposure percentage (exposure / portfolio value)
  - Number of open positions
  - Average R-coefficient of open trades
  - Largest position size (as % of portfolio)
- **AND** display metrics with visual indicators

### Requirement: Risk Alerts
The system SHALL alert users when risk limits are approached.

#### Scenario: Exposure warning
- **WHEN** portfolio exposure exceeds 75%
- **THEN** a warning SHALL be logged
- **AND** user SHALL be notified
- **AND** subsequent orders SHALL be flagged for review

#### Scenario: Consecutive losses alert
- **WHEN** more than 3 consecutive losing trades occur
- **THEN** an alert SHALL be triggered
- **AND** automated trading SHALL be paused (optional mode)
- **AND** user SHALL be notified for review

