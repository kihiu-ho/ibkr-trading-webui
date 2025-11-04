## Why

Airflow webserver fails to start despite successful database connection fixes for other Airflow components. The webserver container starts but gunicorn fails to initialize within timeout, while scheduler, worker, and triggerer work correctly with identical configuration.

**Symptoms:**
- ✅ Container starts successfully
- ✅ Database connection works (no SSL errors)
- ❌ Gunicorn master doesn't respond within 120 seconds
- ❌ Webserver exits with timeout error
- ❌ Airflow UI inaccessible at http://localhost:8080

**Comparison with Working Services:**
- Scheduler: Uses identical command structure, works perfectly
- Worker/Triggerer: Use same pattern, work correctly
- Webserver: Same configuration, fails consistently

**Root Cause Candidates:**
1. **Resource Constraints**: Memory/CPU limits preventing gunicorn startup
2. **Gunicorn Configuration**: Worker count, timeout, or other settings
3. **Command Structure**: YAML parsing or shell execution differences
4. **Dependency Issues**: Webserver-specific requirements not met
5. **Environment Variables**: Missing or incorrect webserver-specific config

## What Changes

### 1. Diagnose Resource and Configuration Issues
Compare webserver with working scheduler configuration:
- Memory limits: webserver (1G) vs scheduler (1G)
- CPU limits: webserver (1.0) vs scheduler (1.0)
- Gunicorn settings: workers, timeout, host binding
- Environment variables and command structure

### 2. Simplify Webserver Configuration
Start with minimal working configuration:
- Reduce workers from 4 to 1 (already done)
- Increase timeout from 120s to 300s (already done)
- Remove complex command structures
- Use simplest possible startup command

### 3. Fix Command Execution Issues
Debug why identical command structure works for scheduler but not webserver:
- Check YAML parsing differences
- Verify shell execution environment
- Test command isolation (run webserver command manually)
- Compare actual executed commands

### 4. Optimize for Reliable Startup
Implement proven startup pattern:
- Use same entrypoint/command as working scheduler
- Ensure proper environment variable handling
- Add startup validation and error handling
- Configure for development/production modes appropriately

## Impact

### Fixed Services
- ✅ **airflow-webserver**: Will start reliably and serve UI
- ✅ **Airflow UI**: Accessible at http://localhost:8080
- ✅ **DAG Management**: Web interface for DAG operations
- ✅ **Task Monitoring**: Real-time task status and logs
- ✅ **User Management**: Web-based user administration

### Performance
- Webserver starts in <60 seconds (instead of timing out)
- UI responds within 2-3 seconds
- No resource conflicts with other services
- Stable operation under normal load

### Affected Files
- **MODIFIED**: `docker-compose.yml` - Webserver service configuration
- **OPTIONAL**: `reference/airflow/airflow/webserver-entrypoint.sh` - Custom startup script
- **OPTIONAL**: Airflow configuration files for webserver optimization

### Dependencies
- Requires database connection fix (already completed)
- No breaking changes to existing working services
- Backward compatible with current environment

### Breaking Changes
**None** - Fixes broken webserver functionality without affecting other services.

## Migration Path

### For Existing Users
1. Pull changes and restart webserver: `docker compose restart airflow-webserver`
2. Airflow UI becomes accessible at http://localhost:8080
3. Test DAG management and monitoring features
4. Verify user authentication and permissions

### Rollback Plan
- Extremely low risk (fixes broken webserver)
- If issues: revert docker-compose.yml webserver section
- Other Airflow services remain unaffected

## Testing Checklist

- [ ] Airflow webserver starts within 60 seconds
- [ ] Webserver health check passes (/health endpoint)
- [ ] Airflow UI loads at http://localhost:8080
- [ ] DAGs display correctly in web interface
- [ ] User login and authentication work
- [ ] Task instances show proper status
- [ ] Webserver remains stable under load
- [ ] No resource conflicts with other services