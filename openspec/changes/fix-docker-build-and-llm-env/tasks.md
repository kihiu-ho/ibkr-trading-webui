# Fix Docker Build/Restart Commands and LLM Environment Configuration - Tasks

## Completed Tasks

- [x] Add LLM environment variables to docker-compose.yml (x-airflow-common-env)
- [x] Update config.py to read LLM settings from environment
- [x] Update LLM analyzer to support base_url parameter
- [x] Update workflow to use LLM config from environment
- [x] Document correct Docker Compose commands
- [x] Create OpenSpec change documentation

## Docker Commands

### Correct Commands:
```bash
# Build Airflow services
docker compose build airflow-scheduler airflow-webserver airflow-triggerer

# Restart Airflow services  
docker compose restart airflow-scheduler airflow-webserver airflow-triggerer
```

**Note**: Use `docker compose` (v2) not `docker-compose` (v1 legacy)

## Environment Variables

### New Unified Names (Recommended):
- `LLM_PROVIDER` - LLM provider (openai/anthropic)
- `LLM_API_BASE_URL` - Base URL for API
- `LLM_API_KEY` - API key
- `LLM_MODEL` - Model name

### Legacy Names (Still Supported):
- `OPENAI_API_KEY`
- `OPENAI_API_BASE`
- `OPENAI_MODEL`
- `ANTHROPIC_API_KEY`
- `ANTHROPIC_MODEL`

## Testing

- [ ] Test Docker build commands
- [ ] Test Docker restart commands
- [ ] Test LLM configuration from .env
- [ ] Test custom base URL support
- [ ] Test backward compatibility with legacy env vars

