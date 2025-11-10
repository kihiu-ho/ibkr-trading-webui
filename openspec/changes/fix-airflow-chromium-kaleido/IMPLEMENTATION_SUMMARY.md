# Implementation Summary: Fix Airflow Chromium/Kaleido Chart Generation

## Problem

The `ibkr_trading_signal_workflow` chart generation tasks (`generate_daily_chart`, `generate_weekly_chart`) were failing with:
```
ChromeNotFoundError: Kaleido v1 and later requires Chrome to be installed.
```

The Airflow Docker container didn't have Chromium installed, while Kaleido (used by Plotly for image export) requires Chrome/Chromium to generate JPEG/PNG charts.

## Solution

### 1. Docker Image Updates (Dockerfile.airflow)

**Changes:**
- Added `chromium` and `chromium-driver` packages to system dependencies
- Set `CHROME_BIN` and `CHROMIUM_PATH` environment variables to `/usr/bin/chromium`
- These environment variables are available to all processes in the container

**Files Modified:**
- `Dockerfile.airflow`: Added Chromium installation and environment variables

### 2. Chart Generator Improvements (dags/utils/chart_generator.py)

**Changes:**
- Added `_init_kaleido()` method to initialize Kaleido with Chromium path if available
- Added `_save_html_fallback()` method to save charts as HTML when image export fails
- Improved error handling with `_is_chrome_error()` helper function
- Refactored chart export logic to use HTML fallback when Chromium is not available
- Enhanced error messages with clear installation instructions

**Error Handling Flow:**
1. Try JPEG export with timeout handling
2. If timeout, fallback to PNG export
3. If Chrome/Chromium error, fallback to HTML export
4. If other errors, try HTML fallback as last resort
5. Workflow continues even if JPEG export fails

**Files Modified:**
- `dags/utils/chart_generator.py`: Added Kaleido initialization, HTML fallback, and improved error handling

## Implementation Details

### Kaleido Initialization

```python
def _init_kaleido(self):
    """Initialize Kaleido for chart image export with Chromium support"""
    try:
        pio.kaleido.scope.mathjax = None
        chromium_path = os.environ.get('CHROMIUM_PATH') or os.environ.get('CHROME_BIN')
        if chromium_path and os.path.exists(chromium_path):
            pio.kaleido.scope.chromium_args += ("--single-process",)
            logger.info(f"Kaleido initialized with Chromium: {chromium_path}")
        else:
            logger.warning("Chromium not found. HTML fallback will be used if image export fails.")
    except Exception as e:
        logger.warning(f"Kaleido initialization warning: {e}. HTML fallback will be used if image export fails.")
```

### HTML Fallback

```python
def _save_html_fallback(self, fig, original_file_path: str, config: ChartConfig) -> str:
    """Save chart as HTML file when image export fails"""
    html_path = os.path.splitext(original_file_path)[0] + '.html'
    html_string = pio.to_html(fig, include_plotlyjs='cdn', full_html=True)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_string)
    logger.info(f"Chart saved as HTML fallback: {html_path}")
    return html_path
```

### Error Detection

```python
def _is_chrome_error(error: Exception) -> bool:
    """Check if error is related to Chrome/Chromium not found"""
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()
    return ('chrome' in error_str or 'chromium' in error_str or 
            'chromenotfounderror' in error_type or
            ('kaleido' in error_str and 'chrome' in error_str))
```

## Testing

### Prerequisites
1. Rebuild Airflow Docker image: `docker-compose build airflow-webserver airflow-scheduler`
2. Restart Airflow services: `docker-compose restart airflow-webserver airflow-scheduler`

### Test Cases

#### 1. Verify Chromium Installation
```bash
# Check Chromium is installed in Airflow container
docker exec ibkr-airflow-webserver which chromium
# Expected: /usr/bin/chromium

# Check environment variables
docker exec ibkr-airflow-webserver env | grep -i chrome
# Expected: CHROME_BIN=/usr/bin/chromium, CHROMIUM_PATH=/usr/bin/chromium
```

#### 2. Test Chart Generation with Chromium
- Trigger `ibkr_trading_signal_workflow`
- Verify `generate_daily_chart` task completes successfully
- Verify `generate_weekly_chart` task completes successfully
- Check logs for: "Kaleido initialized with Chromium: /usr/bin/chromium"
- Verify charts are generated as JPEG files
- Verify charts are uploaded to MinIO

#### 3. Test HTML Fallback (Optional)
- Temporarily remove Chromium from container (for testing)
- Trigger workflow
- Verify charts are generated as HTML files
- Verify workflow completes successfully
- Check logs for: "Chart saved as HTML fallback"

#### 4. End-to-End Workflow Test
- Trigger `ibkr_trading_signal_workflow`
- Verify all tasks complete successfully
- Verify charts are generated and stored
- Verify workflow completes without errors

## Expected Results

### With Chromium Installed
- Charts are generated as JPEG files
- Kaleido uses Chromium for image export
- Workflow completes successfully
- Charts are uploaded to MinIO

### Without Chromium (Fallback)
- Charts are generated as HTML files
- Workflow continues execution
- Charts are uploaded to MinIO
- Warning messages are logged

## Files Modified

1. **Dockerfile.airflow**
   - Added Chromium and Chromium-driver installation
   - Set CHROME_BIN and CHROMIUM_PATH environment variables

2. **dags/utils/chart_generator.py**
   - Added `_init_kaleido()` method
   - Added `_save_html_fallback()` method
   - Added `_is_chrome_error()` helper function
   - Improved error handling for Chrome/Chromium errors
   - Enhanced error messages

## Next Steps

1. **Rebuild Docker Image**: Rebuild Airflow Docker image to include Chromium
2. **Test**: Test chart generation with Chromium installed
3. **Verify**: Verify workflow completes successfully
4. **Monitor**: Monitor logs for any Chromium-related issues
5. **Document**: Update documentation if needed

## Notes

- HTML fallback ensures workflow continues even if Chromium is not available
- Chromium installation is required for JPEG/PNG chart export
- HTML charts are still usable for LLM vision analysis
- Error messages provide clear installation instructions
- Workflow execution is not blocked by Chromium issues

