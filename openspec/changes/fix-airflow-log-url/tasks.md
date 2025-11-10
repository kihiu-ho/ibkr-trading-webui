# Tasks: Fix Airflow Log URL Configuration

## 1. Update Docker Compose Configuration
- [x] Add `AIRFLOW__WEBSERVER__BASE_URL` to Airflow environment
- [x] Add `AIRFLOW__CORE__HOSTNAME_CALLABLE` configuration
- [x] Verify configuration is applied to both webserver and scheduler

## 2. Test Log URL Generation
- [x] Restart Airflow services
- [ ] Trigger a DAG run
- [ ] Verify log URLs are correctly generated
- [ ] Check that logs can be accessed via the URLs

## 3. Validate Fix
- [ ] Check Airflow logs for URL generation errors
- [ ] Verify frontend can display logs correctly
- [ ] Test with multiple DAG runs

