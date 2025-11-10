# Tasks: Fix Chart File Access Between Containers

## 1. Add Shared Volume for Charts
- [x] Add shared volume mount to Airflow services in docker-compose.yml
- [x] Add shared volume mount to backend service in docker-compose.yml
- [x] Verify volume is accessible from both containers

## 2. Update Chart Storage in DAGs
- [x] Update `ibkr_stock_data_workflow.py` to save charts to shared volume
- [x] Update `ibkr_trading_signal_workflow.py` to save charts to shared volume
- [x] Update `ibkr_multi_symbol_workflow.py` if needed

## 3. Update Chart Images Endpoint
- [x] Update `chart_images.py` to check shared volume location
- [x] Add better error messages for missing files
- [x] Ensure MinIO URLs are still handled correctly

## 4. Testing
- [ ] Test chart generation and storage
- [ ] Test chart image access from frontend
- [ ] Verify MinIO uploads work after container rebuild

