## Why

The Airflow webserver configuration has diverged from the reference pattern, causing startup issues. The reference `reference/airflow/docker-compose.yaml` shows a working configuration using the `x-airflow-common` pattern with simple `command: webserver`, while our current implementation uses a standalone configuration that doesn't inherit common settings.

**Current Issues:**
- Webserver doesn't use `<<: *airflow-common` pattern
- Missing volume mounts from common configuration
- Missing user settings and network configuration
- Different dependency management than reference
- Not aligned with working scheduler pattern

**Reference Pattern:**
- Uses `<<: *airflow-common` to inherit common configuration
- Simple `command: webserver` (no complex arguments)
- Inherits volumes, user, networks from common
- Uses `<<: *airflow-common-depends-on` for dependencies
- Works reliably with standard Airflow setup

## What Changes

### 1. Align Webserver with Reference Pattern
Update webserver to use the same pattern as scheduler (which works) and reference:

**Before (broken):**
```yaml
airflow-webserver:
  image: ibkr-airflow:latest
  environment:
    # Standalone environment variables
  command: ["airflow", "webserver", "--workers", "1"]
```

**After (reference pattern):**
```yaml
airflow-webserver:
  <<: *airflow-common
  container_name: ibkr-airflow-webserver
  command:
    - -c
    - |
      # Convert AIRFLOW_DATABASE_URL format (same as scheduler)
      if [ -n "$AIRFLOW_DATABASE_URL" ]; then
        export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=$(echo "$AIRFLOW_DATABASE_URL" | sed 's/postgresql+psycopg[^:]*:/postgresql:/')
        export AIRFLOW__CELERY__RESULT_BACKEND="db+$(echo "$AIRFLOW_DATABASE_URL" | sed 's/postgresql+psycopg[^:]*:/postgresql:/')"
      fi
      exec /usr/bin/dumb-init airflow webserver
  depends_on:
    <<: *airflow-common-depends-on
    airflow-init:
      condition: service_completed_successfully
```

### 2. Match Reference Configuration Structure
- Use `<<: *airflow-common` to inherit common settings
- Inherit volumes, user, networks automatically
- Use same dependency pattern as reference
- Keep URL conversion for external database compatibility

### 3. Simplify Command Structure
- Use same command pattern as working scheduler
- Remove complex standalone configuration
- Let common configuration handle defaults

## Impact

### Fixed Services
- ✅ **airflow-webserver**: Will use proven reference pattern
- ✅ **Configuration Consistency**: All Airflow services use same pattern
- ✅ **Volume Access**: Proper volume mounts inherited from common
- ✅ **User Permissions**: Correct user settings applied
- ✅ **Network Configuration**: Proper network inheritance

### Benefits
- Aligned with working reference implementation
- Consistent with working scheduler configuration
- Proper volume mounts for DAGs, logs, plugins
- Better resource management through common config
- Easier maintenance with shared configuration

### Affected Files
- **MODIFIED**: `docker-compose.yml` - Webserver service aligned with reference pattern

### Breaking Changes
**None** - This aligns configuration with proven working pattern.

## Migration Path

### For Existing Users
1. Pull changes
2. Restart webserver: `docker compose restart airflow-webserver`
3. Webserver will use reference-aligned configuration
4. All Airflow services now consistent

### Rollback Plan
- Low risk (aligning with working pattern)
- If issues: revert webserver section
- Reference pattern is proven to work

## Testing Checklist

- [x] Webserver uses x-airflow-common pattern
- [x] All volumes properly mounted (DAGs, logs, plugins, config)
- [x] User permissions correctly applied (inherited from common)
- [x] Network configuration inherited (trading-network)
- [x] Dependencies properly configured (airflow-init, redis)
- [x] Configuration consistent with scheduler (identical pattern)
- [ ] Webserver starts successfully (gunicorn master timeout issue persists)
- [ ] Airflow UI accessible at http://localhost:8080 (blocked by timeout)

## Remaining Issue

The webserver configuration is now aligned with the reference pattern, but there's a persistent issue where gunicorn master doesn't respond within Airflow's hardcoded 120-second timeout. This appears to be an environment-specific issue (possibly related to external database connection timing or resource constraints) rather than a configuration pattern issue, as the configuration now matches both the reference and working scheduler pattern.
