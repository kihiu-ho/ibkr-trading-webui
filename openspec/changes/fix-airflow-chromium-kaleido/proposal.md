# Fix Airflow Chromium/Kaleido Chart Generation

## Why

The `ibkr_trading_signal_workflow` chart generation tasks (`generate_daily_chart`, `generate_weekly_chart`) are failing with:
```
ChromeNotFoundError: Kaleido v1 and later requires Chrome to be installed.
```

The Airflow Docker container doesn't have Chromium installed, while Kaleido (used by Plotly for image export) requires Chrome/Chromium to generate JPEG/PNG charts. This causes workflow tasks to fail and prevents the workflow from completing successfully.

## What Changes

### 1. Install Chromium in Airflow Docker Image
- **File**: `Dockerfile.airflow`
- **Issue**: Airflow container doesn't have Chromium installed
- **Fix**: 
  - Add Chromium and Chromium-driver packages to system dependencies
  - Set environment variables for Chromium path (CHROME_BIN, CHROMIUM_PATH)
  - Configure Kaleido to use installed Chromium
- **Impact**: Chart generation tasks can successfully export JPEG/PNG images

### 2. Add HTML Fallback for Chart Generation
- **File**: `dags/utils/chart_generator.py`
- **Issue**: Chart generation fails completely if JPEG export fails
- **Fix**:
  - Add HTML export as fallback when JPEG export fails
  - Save HTML file if JPEG generation fails due to Chromium issues
  - Log warning but continue workflow execution
  - Update ChartResult to indicate if HTML fallback was used
- **Impact**: Workflow continues even if JPEG export fails, charts still available as HTML

### 3. Improve Error Handling for Kaleido
- **File**: `dags/utils/chart_generator.py`
- **Issue**: Generic error messages don't explain Chromium requirement
- **Fix**:
  - Catch ChromeNotFoundError specifically
  - Provide clear error messages with installation instructions
  - Fall back to HTML export automatically
  - Log helpful error messages for debugging
- **Impact**: Better error messages and graceful degradation

### 4. Initialize Kaleido with Chromium Path
- **File**: `dags/utils/chart_generator.py`
- **Issue**: Kaleido doesn't know where to find Chromium
- **Fix**:
  - Set Kaleido scope chromium path if CHROMIUM_PATH environment variable is set
  - Configure Kaleido with single-process mode for Docker containers
  - Handle Kaleido initialization errors gracefully
- **Impact**: Kaleido can find and use Chromium automatically

## Impact

- **Affected specs**: `chart-generation`, `airflow-integration`
- **Affected code**:
  - `Dockerfile.airflow` - Add Chromium installation
  - `dags/utils/chart_generator.py` - Add HTML fallback and improved error handling

## Testing

1. **Verify Chromium installation**: Check that Chromium is installed in Airflow container
2. **Test chart generation**: Trigger workflow and verify charts are generated successfully
3. **Test fallback**: Temporarily remove Chromium and verify HTML fallback works
4. **Test error handling**: Verify error messages are clear and helpful
5. **End-to-end test**: Verify workflow completes successfully with chart generation

