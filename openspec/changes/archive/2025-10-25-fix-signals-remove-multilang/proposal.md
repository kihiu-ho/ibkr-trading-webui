## Why

Three critical issues needed to be addressed:
1. Chart generation failing with "Failed to generate any charts" causing 500 errors
2. Multi-language support adding unnecessary complexity
3. MinIO upload method mismatch causing chart upload failures

## What Changes

- **CRITICAL FIX 1**: Fix chart generation failure by addressing data fetching issues
- **CRITICAL FIX 2**: Fix MinIO upload method mismatch
- Remove multi-language (Chinese) support from LLM prompts and UI
- Simplify codebase to English-only
- Update all prompt templates to English only
- Remove language selection from frontend

## Impact

- Affected specs: `llm-integration`, `chart-generation`
- Affected code:
  - `backend/services/chart_generator.py` - Fix data fetching + MinIO upload
  - `backend/services/llm_service.py` - Remove Chinese prompts
  - `backend/services/signal_generator.py` - Remove language parameter
  - `backend/config/settings.py` - Remove language config
  - `backend/api/signals.py` - Remove language from API
  - `frontend/templates/signals.html` - Remove language selector
