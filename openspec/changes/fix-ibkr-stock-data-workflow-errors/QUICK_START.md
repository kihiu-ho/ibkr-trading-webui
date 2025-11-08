# Quick Start - Testing the Fixed Workflow

## What Was Fixed

Two critical bugs in the `ibkr_stock_data_workflow` DAG have been fixed:

1. **`log_to_mlflow` task** - Fixed variable scope error
2. **`transform_data` task** - Fixed NaN serialization error

## How to Test

### Step 1: Restart Airflow Services

```bash
cd /Users/he/git/ibkr-trading-webui

# Restart Airflow to pick up the changes
docker compose restart airflow-scheduler airflow-webserver
```

### Step 2: Access Airflow UI

Open your browser and navigate to:
```
http://localhost:8080
```

### Step 3: Trigger the DAG

1. Find the `ibkr_stock_data_workflow` DAG in the list
2. Click on the DAG name to open the Grid view
3. Click the ▶️ (Play) button in the top right
4. Select "Trigger DAG" from the dropdown

### Step 4: Monitor Execution

Watch the task execution in the Grid view. All tasks should turn **green**:

```
✓ extract_stock_data    (green)
✓ validate_data         (green)
✓ transform_data        (green) ← Previously failing
✓ log_to_mlflow         (green) ← Previously failing
```

### Step 5: Verify MLflow Logging (Optional)

Check that data was logged to MLflow:

```bash
# Open MLflow UI
open http://localhost:5500
```

Look for a new run with the name pattern: `stock_data_YYYYMMDD_HHMMSS`

## Expected Results

### ✅ Success Indicators

- All 4 tasks show **green** status
- DAG run status is **success**
- No error messages in task logs
- MLflow shows a new run entry

### ❌ If You Still See Errors

1. Check that you restarted Airflow services
2. View task logs in Airflow UI for specific error messages
3. Verify the DAG file was updated:
   ```bash
   grep "mlflow_run_id = None" dags/ibkr_stock_data_workflow.py
   grep "fillna(value=None)" dags/ibkr_stock_data_workflow.py
   ```

## What Changed

### In `log_to_mlflow` (Line 249-314)

**Before:**
```python
with mlflow_run_context(run_name=run_name, tags=tags) as tracker:
    # ... code ...
return {'mlflow_run_id': tracker.run_id}  # ❌ tracker out of scope
```

**After:**
```python
mlflow_run_id = None
with mlflow_run_context(run_name=run_name, tags=tags) as tracker:
    # ... code ...
    mlflow_run_id = tracker.run_id  # ✓ captured in scope
return {'mlflow_run_id': mlflow_run_id}  # ✓ uses captured value
```

### In `transform_data` (Line 206-209)

**Before:**
```python
task_instance.xcom_push(key='transformed_data', value=df.to_dict('records'))
# ❌ NaN values cause JSON serialization error
```

**After:**
```python
df_dict = df.replace({pd.NA: None}).fillna(value=None).to_dict('records')
task_instance.xcom_push(key='transformed_data', value=df_dict)
# ✓ NaN converted to None (JSON-serializable)
```

## Need Help?

- **Full documentation**: See `proposal.md` in this directory
- **Technical details**: See `specs/bug-fixes.md`
- **Implementation summary**: See `IMPLEMENTATION_COMPLETE.md`

## Rollback (If Needed)

If you need to revert the changes:

```bash
git checkout HEAD~1 dags/ibkr_stock_data_workflow.py
docker compose restart airflow-scheduler airflow-webserver
```

---

**Status**: Ready for Testing ✓
**Date**: November 8, 2025

