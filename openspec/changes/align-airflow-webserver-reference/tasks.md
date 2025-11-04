## 1. Analyze Reference Configuration

- [x] Review reference/airflow/docker-compose.yaml webserver configuration
- [x] Compare with current webserver configuration
- [x] Identify differences in pattern usage
- [x] Check scheduler pattern (which works) for alignment
- [x] Document required changes

## 2. Align Webserver with Reference Pattern

- [x] Update webserver to use `<<: *airflow-common`
- [x] Use same command structure as scheduler (with URL conversion)
- [x] Inherit volumes, user, networks from common
- [x] Use `<<: *airflow-common-depends-on` for dependencies
- [x] Remove standalone environment configuration

## 3. Test Configuration Alignment

- [x] Verify webserver inherits common volumes (DAGs, logs, plugins, config)
- [x] Check user permissions are correct (inherited from common)
- [x] Confirm network configuration inherited (trading-network)
- [x] Test dependency ordering (airflow-init, redis)
- [x] Validate environment variables (inherited from common-env)

## 4. Test Webserver Functionality

- [x] Restart webserver with new configuration
- [x] Verify webserver command structure matches scheduler pattern
- [x] Confirm URL conversion works correctly
- [ ] Resolve gunicorn master 120s timeout issue (persistent)
- [ ] Test Airflow UI accessibility (blocked by timeout)
- [ ] Confirm DAGs and plugins are accessible
- [ ] Validate logs directory access

## 5. Validate Consistency

- [x] Compare webserver with scheduler configuration (now aligned)
- [x] Verify all Airflow services use consistent patterns (scheduler, worker, triggerer, webserver)
- [x] Check reference alignment (webserver now uses <<: *airflow-common)
- [x] Confirm no breaking changes
- [ ] Test complete Airflow stack (webserver timeout blocks full testing)
