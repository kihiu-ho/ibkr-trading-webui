## ADDED Requirements
### Requirement: Gateway CLI Health Guidance
The system SHALL provide clear CLI guidance for probing the IBKR Gateway tickle endpoint and interpreting its responses.

#### Scenario: Developer runs tickle health check before authentication
- **WHEN** a developer executes `curl -k https://localhost:5055/v1/api/tickle`
- **THEN** documentation and tooling explain that `Access Denied` indicates the gateway is running but not yet authenticated, and direct the developer to log in at https://localhost:5055

#### Scenario: Developer relies on project tooling
- **WHEN** the developer runs `check_ibkr_auth.sh`
- **THEN** the script uses the `/v1/api/tickle` endpoint and prints actionable remediation steps whenever the response shows `Access Denied`
