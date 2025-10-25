# Fix LLM Configuration for Signal Generation

## Why

Users encounter "Failed to analyze any charts" error when generating trading signals because:
1. OpenAI API key not configured in .env (has placeholder value)
2. Missing LLM vision configuration options
3. No fallback or graceful degradation when LLM unavailable
4. Unclear error messages don't guide users to fix the issue

This blocks a core feature (LLM trading signals) and causes confusion.

## What Changes

### Configuration Updates
- Add comprehensive LLM configuration to `.env` with:
  - Provider selection (OpenAI vs Gemini)
  - Model selection per provider
  - API key configuration for both providers
  - Timeout and retry settings
  - Clear comments explaining each option
- Update `.env.example` with all LLM options and helpful comments
- Add LLM_ENABLED flag to allow disabling LLM features

### Error Handling Improvements
- Add clear error messages when API key missing
- Add startup validation warnings
- Provide actionable guidance in error messages (where to get API keys)
- Validate configuration on LLMService initialization

### Documentation
- Add FIX_LLM_CONFIG.md with step-by-step setup guide
- Document both OpenAI and Gemini options
- Include cost comparison and recommendations

## Impact

### Affected Specs
- `llm-integration` - Configuration requirements updated

### Affected Code
- `.env` - Add LLM configuration variables
- `.env.example` - Add complete LLM section with documentation
- `backend/services/llm_service.py` - Already updated with validation
- `FIX_LLM_CONFIG.md` - New documentation file

### Breaking Changes
None - Additive only. Existing configurations continue to work.

## Testing
- [x] Verify clear error message when API key missing
- [x] Verify startup warning when API key not configured
- [ ] Test with valid OpenAI API key
- [ ] Test with Gemini API key (when implemented)
- [ ] Verify graceful degradation when LLM disabled

