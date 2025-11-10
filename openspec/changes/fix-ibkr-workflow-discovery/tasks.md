## 1. Investigation
- [x] 1.1 Check Airflow logs for DAG parsing errors
- [x] 1.2 Test Airflow API directly to see if DAGs are registered
- [x] 1.3 Check DAG file syntax and imports
- [x] 1.4 Verify DAG IDs are correct and unique

## 2. Fix DAG Discovery
- [x] 2.1 Fix any syntax errors in DAG files
- [x] 2.2 Fix any import errors (minio module missing)
- [x] 2.3 Fix timetable errors (empty string vs None)
- [x] 2.4 Add minio to Airflow Dockerfile
- [x] 2.5 Make minio import optional with graceful fallback

## 3. Frontend Improvements
- [ ] 3.1 Add error handling for DAG loading failures
- [ ] 3.2 Add filtering to show only IBKR workflows if needed
- [ ] 3.3 Add debug logging for DAG discovery
- [ ] 3.4 Improve empty state messaging

## 4. Testing
- [ ] 4.1 Test DAG discovery in Airflow
- [ ] 4.2 Test frontend DAG loading
- [ ] 4.3 Test DAG triggering
- [ ] 4.4 Test end-to-end workflow visibility

