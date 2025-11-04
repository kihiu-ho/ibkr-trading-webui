# Deployment Specification

## MODIFIED Requirements

### Requirement: Database Setup Automation
The setup script SHALL correctly parse database connection strings and create databases automatically.

#### Scenario: Extract connection details from DATABASE_URL
- **WHEN** DATABASE_URL is set in .env file
- **THEN** script extracts username correctly
- **AND** script extracts password correctly
- **AND** script extracts host and port correctly
- **AND** script handles URL-encoded passwords

#### Scenario: Create databases automatically
- **WHEN** user chooses to create databases automatically
- **THEN** script connects to PostgreSQL server
- **AND** script creates airflow database
- **AND** script creates mlflow database
- **AND** script verifies databases were created

#### Scenario: Handle connection failures gracefully
- **WHEN** connection to PostgreSQL fails
- **THEN** script shows clear error message
- **AND** script provides manual creation instructions
- **AND** script continues to update .env file
- **AND** user can still proceed manually

