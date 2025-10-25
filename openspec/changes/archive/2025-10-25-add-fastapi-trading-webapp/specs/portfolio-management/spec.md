# Portfolio Management Specification

## ADDED Requirements

### Requirement: Position Tracking
The system SHALL track all open positions with current values and P&L.

#### Scenario: Update open position
- **WHEN** an order is filled
- **THEN** if position exists for conid, update quantity and average_cost
- **AND** calculate new average: (old_avg × old_qty + fill_price × fill_qty) / (old_qty + fill_qty)
- **AND** if position is new, create position record with entry details

#### Scenario: Calculate unrealized P&L
- **WHEN** position is displayed or refreshed
- **THEN** fetch current market price from IBKR
- **AND** calculate unrealized_pnl = (current_price - average_cost) × quantity
- **AND** update position record with current_price and unrealized_pnl

#### Scenario: Close position
- **WHEN** a position is fully exited (quantity becomes 0)
- **THEN** calculate final realized P&L
- **AND** remove from active positions or mark as closed
- **AND** create trade record with complete entry/exit information

### Requirement: Trade History
The system SHALL maintain complete history of all executed trades.

#### Scenario: Record trade entry
- **WHEN** an order to open position is filled
- **THEN** create trade record with: conid, entry_price, entry_quantity, entry_date, order_id
- **AND** realized_pnl SHALL be null until position is closed

#### Scenario: Record trade exit
- **WHEN** an order to close position is filled
- **THEN** update corresponding trade record with: exit_price, exit_quantity, exit_date
- **AND** calculate realized_pnl = (exit_price - entry_price) × quantity × direction
- **AND** direction: +1 for long (buy then sell), -1 for short (sell then buy)

#### Scenario: Query trade history
- **WHEN** user views trade history
- **THEN** return all trades sorted by exit_date descending
- **AND** include: symbol, entry/exit dates, prices, quantities, realized P&L, holding period
- **AND** allow filtering by date range, symbol, or strategy

### Requirement: Portfolio Summary
The system SHALL provide comprehensive portfolio statistics and metrics.

#### Scenario: Calculate portfolio summary
- **WHEN** user views portfolio dashboard
- **THEN** calculate and display:
  - Total account value (cash + positions)
  - Total realized P&L (sum of all closed trades)
  - Total unrealized P&L (sum of open positions)
  - Number of open positions
  - Number of trades (all time, this month, this week)
  - Win rate (winning trades / total closed trades)
  - Average gain per trade
  - Largest win and largest loss

### Requirement: Performance Metrics
The system SHALL calculate trading performance metrics.

#### Scenario: Calculate win rate
- **WHEN** user views performance metrics
- **THEN** win_rate = (count of trades with realized_pnl > 0) / (count of closed trades)
- **AND** display as percentage

#### Scenario: Calculate average R achieved
- **WHEN** user views performance metrics
- **THEN** for each closed trade, calculate R_achieved = realized_pnl / risk_amount
- **AND** average_R = mean of all R_achieved values
- **AND** compare to expected R from decisions

#### Scenario: Calculate profit factor
- **WHEN** user views performance metrics
- **THEN** profit_factor = sum(winning trades) / sum(losing trades)
- **AND** display with interpretation (>1.5 is good)

### Requirement: Position Risk Monitoring
The system SHALL monitor risk for each open position.

#### Scenario: Display position risk
- **WHEN** viewing position details
- **THEN** show: entry price, current price, stop-loss, unrealized P&L, % gain/loss, distance to stop-loss
- **AND** highlight positions approaching stop-loss

#### Scenario: Stop-loss breach alert
- **WHEN** current price crosses stop-loss level
- **THEN** trigger alert notification
- **AND** suggest closing position
- **AND** log event for review

### Requirement: Portfolio Diversification
The system SHALL track portfolio concentration and diversification.

#### Scenario: Calculate position concentration
- **WHEN** viewing portfolio
- **THEN** for each position, calculate: position_value / total_portfolio_value
- **AND** flag positions exceeding 20% as concentrated
- **AND** display top 5 largest positions by value

### Requirement: Syncing with IBKR Positions
The system SHALL periodically sync positions with IBKR to ensure accuracy.

#### Scenario: Sync positions from IBKR
- **WHEN** sync is triggered or scheduled
- **THEN** fetch current positions from GET /v1/api/portfolio/{accountId}/positions
- **AND** compare with internal positions table
- **AND** update quantities and prices
- **AND** flag discrepancies for review

