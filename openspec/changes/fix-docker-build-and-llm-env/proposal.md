# Fix Docker Build/Restart Commands and LLM Environment Configuration

## Why

1. **Docker Build/Restart Commands**: Need correct commands to rebuild and restart Airflow services after code changes
2. **LLM Configuration**: LLM analyzer should use base URL, API key, and model from `.env` file for flexibility and environment-specific configuration

## What Changes

### 1. Docker Build/Restart Commands

**Correct Commands**:
```bash
# Build Airflow services
docker compose build airflow-scheduler airflow-webserver airflow-triggerer

# Restart Airflow services
docker compose restart airflow-scheduler airflow-webserver airflow-triggerer
```

**Note**: Use `docker compose` (v2) not `docker-compose` (v1 legacy)

### 2. LLM Environment Configuration

**Added to `docker-compose.yml` (`x-airflow-common-env`)**:
- `LLM_PROVIDER`: LLM provider (openai/anthropic), defaults to `LLM_VISION_PROVIDER` or `openai`
- `LLM_API_BASE_URL`: Base URL for LLM API, defaults to `OPENAI_API_BASE` or `https://api.openai.com/v1`
- `LLM_API_KEY`: API key for LLM, defaults to `OPENAI_API_KEY`
- `LLM_MODEL`: Model name, defaults to `OPENAI_MODEL` or `gpt-4o`
- `ANTHROPIC_API_KEY`: Anthropic API key
- `ANTHROPIC_MODEL`: Anthropic model name

**Updated `dags/utils/config.py`**:
- Added LLM configuration properties that read from environment variables
- Supports both `LLM_*` and legacy `OPENAI_*` environment variable names for backward compatibility

**Updated `dags/utils/llm_signal_analyzer.py`**:
- Added `base_url` parameter to `__init__` method
- Reads `LLM_API_BASE_URL` or `OPENAI_API_BASE` from environment
- Supports custom base URL for OpenAI-compatible APIs (e.g., Azure OpenAI, local LLM servers)
- Falls back to environment variables if parameters not provided

**Updated `dags/ibkr_trading_signal_workflow.py`**:
- Reads LLM configuration from `config` object (which reads from environment)
- Passes `provider`, `model`, `api_key`, and `base_url` to `LLMSignalAnalyzer`

## Impact

- **Positive**:
  - LLM configuration now fully configurable via `.env` file
  - Supports custom base URLs for OpenAI-compatible APIs (Azure OpenAI, local servers, etc.)
  - Backward compatible with existing `OPENAI_*` environment variables
  - Clear Docker Compose commands for rebuilding/restarting services
  
- **Negative**: 
  - None

## Migration Path

### For Users

1. **Update `.env` file** (optional - backward compatible):
   ```bash
   # LLM Configuration (new unified names)
   LLM_PROVIDER=openai
   LLM_API_BASE_URL=https://api.openai.com/v1  # or custom URL
   LLM_API_KEY=your_api_key_here
   LLM_MODEL=gpt-4o
   
   # Or use legacy names (still supported)
   OPENAI_API_KEY=your_api_key_here
   OPENAI_API_BASE=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4o
   ```

2. **Rebuild and restart Airflow services**:
   ```bash
   docker compose build airflow-scheduler airflow-webserver airflow-triggerer
   docker compose restart airflow-scheduler airflow-webserver airflow-triggerer
   ```

### For Custom LLM APIs

To use a custom OpenAI-compatible API (e.g., Azure OpenAI, local server):

```bash
# In .env file
LLM_PROVIDER=openai
LLM_API_BASE_URL=https://your-custom-api.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o
```

## Testing Checklist

- [x] Docker Compose commands work correctly
- [x] LLM configuration reads from environment variables
- [x] Supports custom base URL for OpenAI API
- [x] Backward compatible with `OPENAI_*` environment variables
- [x] Falls back to mock mode when API key not set
- [x] Workflow uses LLM configuration from environment

## Files Modified

- `docker-compose.yml` - Added LLM environment variables to `x-airflow-common-env`
- `dags/utils/config.py` - Added LLM configuration properties
- `dags/utils/llm_signal_analyzer.py` - Added `base_url` support and environment variable reading
- `dags/ibkr_trading_signal_workflow.py` - Updated to use LLM config from environment

## Status

✅ **COMPLETE** - All changes applied and ready for testing.

