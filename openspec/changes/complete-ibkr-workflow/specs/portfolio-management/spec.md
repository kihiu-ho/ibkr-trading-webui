# Portfolio Management Capability - Spec Deltas

## ADDED Requirements

### Requirement: Real-Time Portfolio Tracking
The system SHALL maintain an up-to-date view of the user's portfolio including positions, cash balance, and P&L.

#### Scenario: Fetch portfolio data
- **WHEN** a user requests their portfolio
- **THEN** the system SHALL retrieve:
  - All open positions with current market prices
  - Cash balance from IBKR account
  - Total portfolio value (cash + positions market value)
  - Realized P&L from closed trades
  - Unrealized P&L from open positions
- **AND** the system SHALL calculate and return these values in real-time

#### Scenario: Calculate unrealized P&L
- **WHEN** calculating unrealized P&L for a position
- **THEN** the system SHALL fetch the current market price from IBKR
- **AND** the system SHALL calculate: Unrealized P&L = (Current Price - Average Cost) × Quantity
- **AND** the system SHALL display the P&L both as absolute value and percentage

#### Scenario: Calculate realized P&L
- **WHEN** a position is closed
- **THEN** the system SHALL calculate: Realized P&L = (Exit Price - Entry Price) × Quantity
- **AND** the system SHALL store the realized P&L in the `trades` table
- **AND** the system SHALL update the portfolio's total realized P&L

### Requirement: Portfolio Statistics
The system SHALL provide comprehensive trading statistics for the user's portfolio.

#### Scenario: Calculate trading statistics
- **WHEN** a user requests portfolio statistics
- **THEN** the system SHALL calculate and return:
  - Total number of trades
  - Number of winning trades (P&L > 0)
  - Number of losing trades (P&L < 0)
  - Win rate (winning trades / total trades)
  - Total realized P&L
  - Average profit per winning trade
  - Average loss per losing trade
  - Largest single win
  - Largest single loss
  - Average R-multiple
- **AND** all calculations SHALL be based on closed trades only

#### Scenario: View portfolio history
- **WHEN** a user views portfolio history
- **THEN** the system SHALL display historical portfolio snapshots
- **AND** each snapshot SHALL include: date, total value, cash balance, positions, and P&L
- **AND** the user SHALL be able to filter by date range
- **AND** the user SHALL be able to view a chart of portfolio value over time

### Requirement: Portfolio Snapshots
The system SHALL periodically record portfolio snapshots for historical analysis.

#### Scenario: Record daily snapshot
- **WHEN** the market closes each day
- **THEN** the system SHALL record a portfolio snapshot
- **AND** the snapshot SHALL include:
  - User ID
  - Snapshot date
  - Cash balance
  - Total portfolio value
  - List of positions with quantities and market values
  - Realized P&L to date
  - Unrealized P&L
- **AND** the snapshot SHALL be stored in the `portfolio_snapshots` table

#### Scenario: Query historical snapshots
- **WHEN** a user queries portfolio history
- **THEN** the system SHALL return snapshots ordered by date (newest first)
- **AND** the system SHALL support pagination (e.g., 30 snapshots per page)
- **AND** the system SHALL support filtering by date range

### Requirement: Portfolio Refresh
The system SHALL allow users to manually refresh their portfolio data.

#### Scenario: Manual portfolio refresh
- **WHEN** a user clicks "Refresh Portfolio"
- **THEN** the system SHALL fetch the latest data from IBKR
- **AND** the system SHALL recalculate all portfolio values
- **AND** the system SHALL update the display with the latest data
- **AND** the refresh SHALL complete within 10 seconds

#### Scenario: Automatic portfolio updates
- **WHEN** a trade is executed (order filled)
- **THEN** the system SHALL automatically update the portfolio
- **AND** the user's portfolio display SHALL reflect the new position or cash balance
- **AND** the update SHALL occur within 60 seconds of trade execution

### Requirement: Position Details
The system SHALL provide detailed information for each position in the portfolio.

#### Scenario: View position details
- **WHEN** a user views a position
- **THEN** the system SHALL display:
  - Symbol and name
  - Quantity
  - Average cost per share
  - Current market price
  - Total cost basis
  - Current market value
  - Unrealized P&L (absolute and percentage)
  - Stop loss price
  - Target price
  - Associated strategy
  - Entry date and time
- **AND** the system SHALL fetch the current market price in real-time

---

## MODIFIED Requirements

_None - this is a new capability_

---

## REMOVED Requirements

_None - this is a new capability_


