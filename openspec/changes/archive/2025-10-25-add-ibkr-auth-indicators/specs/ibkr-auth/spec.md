# IBKR Authentication Capability

## ADDED Requirements

### Requirement: IBKR Gateway Login UI
The system SHALL provide a web-based login interface for IBKR Gateway authentication.

#### Scenario: User views login page
- **WHEN** user navigates to `/ibkr/login`
- **THEN** the page displays connection status, account info (if connected), and login controls

#### Scenario: User initiates authentication
- **WHEN** user clicks "Connect to Gateway"
- **THEN** the system attempts authentication via IBKR API and displays real-time status

#### Scenario: Connection established
- **WHEN** IBKR Gateway authentication succeeds
- **THEN** the UI shows "Connected" status with green indicator and account ID

#### Scenario: Connection failed
- **WHEN** IBKR Gateway authentication fails
- **THEN** the UI shows error message with red indicator and troubleshooting suggestions

### Requirement: Authentication Status API
The system SHALL provide API endpoints for checking and managing IBKR authentication status.

#### Scenario: Check authentication status
- **WHEN** GET request sent to `/api/ibkr/auth/status`
- **THEN** return JSON with `{authenticated: boolean, account_id: string|null, server_status: object}`

#### Scenario: Initiate authentication
- **WHEN** POST request sent to `/api/ibkr/auth/login`
- **THEN** trigger IBKR Gateway authentication flow and return result

#### Scenario: Logout from gateway
- **WHEN** POST request sent to `/api/ibkr/auth/logout`
- **THEN** terminate IBKR Gateway session and return confirmation

### Requirement: Session Persistence
The system SHALL maintain IBKR Gateway authentication session across page reloads.

#### Scenario: Page reload with active session
- **WHEN** user reloads page and has active IBKR session
- **THEN** connection status remains "Connected" without re-authentication

#### Scenario: Session expiry detection
- **WHEN** IBKR Gateway session expires
- **THEN** UI displays "Session Expired" notification and prompts re-authentication

### Requirement: Connection Health Monitoring
The system SHALL continuously monitor IBKR Gateway connection health.

#### Scenario: Periodic health check
- **WHEN** system performs health check every 30 seconds
- **THEN** verify IBKR Gateway is responsive via `/v1/api/tickle` endpoint

#### Scenario: Connection lost during operation
- **WHEN** health check detects IBKR Gateway is unreachable
- **THEN** update UI to show "Disconnected" status and disable trading actions

#### Scenario: Connection recovered
- **WHEN** IBKR Gateway becomes reachable after disconnection
- **THEN** update UI to show "Connected" status and enable trading actions

### Requirement: Account Selection
The system SHALL allow users to select trading account when multiple accounts exist.

#### Scenario: Multiple accounts detected
- **WHEN** IBKR Gateway returns multiple account IDs
- **THEN** display dropdown menu for account selection

#### Scenario: User selects account
- **WHEN** user selects account from dropdown
- **THEN** save selection and use for all subsequent trading operations

#### Scenario: Single account auto-select
- **WHEN** only one account ID exists
- **THEN** automatically select that account without user interaction

