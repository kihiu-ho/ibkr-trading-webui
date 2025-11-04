## 1. Analyze Reference Patterns

- [x] Review reference/airflow/wait-for-it.sh for service availability checking
- [x] Review reference/airflow/init-multiple-dbs.sh for database initialization
- [x] Review reference/airflow/docker-compose.yaml for dependency management patterns
- [x] Identify key improvements: wait-for-it.sh usage, init scripts, health check conditions

## 2. Create Initialization Scripts

- [x] Copy scripts/wait-for-it.sh from reference for service checking
- [x] Create scripts/init-databases.sh for database setup (adapted for external DBs)
- [x] Test scripts are executable and properly formatted

## 3. Update Docker Compose Dependencies

- [x] Improve mc service to use local wait-for-it.sh script
- [x] Update volume mounts for scripts directory
- [x] Maintain existing dependency conditions (already well-configured)

## 4. Improve Startup Script Logic

- [x] Replace manual curl health checks with Docker Compose health status
- [x] Implement dependency-aware service monitoring
- [x] Add proper error handling with jq JSON parsing
- [x] Improve logging and status reporting
- [x] Maintain backward compatibility with --fast flag

## 5. Testing and Validation

- [x] Validate script syntax (bash -n)
- [x] Check jq availability for JSON parsing
- [x] Verify docker compose --format json support
- [x] Confirm all tools and commands are available
- [x] Fix jq command syntax (remove array indexing for single service queries)
- [x] Fix service names (redis/minio vs ibkr-redis/ibkr-minio)
- [x] Test jq commands with actual services
- [x] Re-validate OpenSpec change after fixes
- [x] Test complete startup sequence with all services
- [x] Verify service dependency ordering works correctly
- [x] Confirm backend health endpoint responds correctly
