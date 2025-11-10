# Airflow Configuration - Log URL Generation

## MODIFIED Requirements

### Requirement: Airflow Base URL Configuration

The system SHALL configure Airflow with proper base URL settings to generate valid log URLs.

#### Scenario: Configure Base URL for Log Generation
- **Given** Airflow services are running in Docker containers
- **When** Airflow generates log URLs for task instances
- **Then** the URLs SHALL include a valid host (e.g., `http://localhost:8080`)
- **And** the URLs SHALL NOT be missing the host part (e.g., `http://:8793/...`)

#### Scenario: Hostname Resolution
- **Given** Airflow needs to determine the hostname for log URLs
- **When** Airflow constructs log server URLs
- **Then** it SHALL use the configured `hostname_callable` function
- **And** the hostname SHALL be resolvable and accessible

## ADDED Requirements

### Requirement: Airflow Environment Variables

The system SHALL set the following Airflow environment variables:
- `AIRFLOW__WEBSERVER__BASE_URL`: Base URL for the Airflow webserver (e.g., `http://localhost:8080`)
- `AIRFLOW__CORE__HOSTNAME_CALLABLE`: Function to call for hostname resolution (e.g., `socket:getfqdn`)

#### Scenario: Base URL Configuration
- **Given** Airflow services are configured in `docker-compose.yml`
- **When** the services start
- **Then** `AIRFLOW__WEBSERVER__BASE_URL` SHALL be set to a valid URL with host
- **And** `AIRFLOW__CORE__HOSTNAME_CALLABLE` SHALL be set to a valid callable

#### Scenario: Log URL Generation
- **Given** Airflow is configured with proper base URL
- **When** a task instance log URL is generated
- **Then** the URL SHALL include the host from `BASE_URL`
- **And** the URL SHALL be accessible from the frontend

