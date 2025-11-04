# Docker Build/Restart Commands and LLM Environment Configuration

## Quick Reference

### Docker Commands

```bash
# Build Airflow services after code changes
docker compose build airflow-scheduler airflow-webserver airflow-triggerer

# Restart Airflow services
docker compose restart airflow-scheduler airflow-webserver airflow-triggerer

# Or rebuild and restart in one go
docker compose build airflow-scheduler airflow-webserver airflow-triggerer && \
docker compose restart airflow-scheduler airflow-webserver airflow-triggerer
```

**Note**: Use `docker compose` (v2) not `docker-compose` (v1 legacy)

### Environment Variables for LLM Configuration

Add to your `.env` file:

```bash
# LLM Configuration (Unified Names - Recommended)
LLM_PROVIDER=openai                    # or "anthropic"
LLM_API_BASE_URL=https://api.openai.com/v1  # or custom URL for OpenAI-compatible APIs
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4o                        # or gpt-4-turbo, etc.

# Anthropic Configuration (if using Anthropic)
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Legacy Environment Variables (Still Supported)

```bash
# Legacy OpenAI names (still work)
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo-preview

# Legacy LLM Vision names (still work)
LLM_VISION_PROVIDER=openai
LLM_VISION_MODEL=gpt-4-vision-preview
```

### Custom LLM API Example

To use Azure OpenAI or a local LLM server:

```bash
# In .env file
LLM_PROVIDER=openai
LLM_API_BASE_URL=https://your-resource.openai.azure.com/v1
LLM_API_KEY=your_azure_key
LLM_MODEL=gpt-4o
```

### Verification

Test LLM configuration:

```bash
docker compose exec airflow-scheduler python -c "
import sys
sys.path.insert(0, '/opt/airflow/dags')
from utils.config import config
print('LLM Provider:', config.llm_provider)
print('LLM Base URL:', config.llm_api_base_url)
print('LLM Model:', config.llm_model)
"
```

## Files Modified

- `docker-compose.yml` - Added LLM environment variables
- `dags/utils/config.py` - Added LLM configuration properties
- `dags/utils/llm_signal_analyzer.py` - Added base_url support
- `dags/ibkr_trading_signal_workflow.py` - Uses LLM config from environment

## Status

✅ **COMPLETE** - All changes applied and tested.

