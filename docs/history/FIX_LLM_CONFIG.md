# LLM Configuration Fix

## Issue
Error: `Failed to analyze any charts for NVDA`  
Root Cause: OpenAI API key not configured (still has placeholder value)

## Logs Show
```
INFO: Chart generated successfully ✅
INFO: Uploaded chart to MinIO ✅
ERROR: Error analyzing chart: All connection attempts failed ❌
ERROR: Failed to analyze 1d chart for NVDA: All connection attempts failed ❌
```

## Quick Fix

### Option 1: OpenAI (Recommended for best results)

1. **Get API Key**: https://platform.openai.com/api-keys

2. **Update `.env`**:
   ```bash
   # Replace this line:
   OPENAI_API_KEY=your_key_here
   
   # With your actual key:
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. **Restart Services**:
   ```bash
   docker-compose restart backend celery-worker
   ```

4. **Test**:
   - Go to http://localhost:8000/signals.html
   - Enter symbol: NVDA
   - Click "Generate Signal"
   - Should work now! ✅

### Option 2: Google Gemini (Free Alternative)

Gemini 2.0 Flash is free and works well for chart analysis.

1. **Get API Key**: https://aistudio.google.com/app/apikey

2. **Update `.env`** (add these lines):
   ```bash
   # Switch to Gemini
   LLM_VISION_PROVIDER=gemini
   LLM_VISION_MODEL=gemini-2.0-flash-exp
   GEMINI_API_KEY=your-gemini-api-key-here
   
   # Comment out or remove OpenAI key requirement
   # OPENAI_API_KEY=your_key_here
   ```

3. **Restart Services**:
   ```bash
   docker-compose restart backend celery-worker
   ```

### Option 3: Use Local LLM (Advanced)

If you want to avoid API costs, you can use a local LLM like LLaVA or Llama with vision support via Ollama.

1. **Install Ollama**: https://ollama.ai

2. **Pull a vision model**:
   ```bash
   ollama pull llava:13b
   ```

3. **Update `.env`**:
   ```bash
   LLM_VISION_PROVIDER=ollama
   LLM_VISION_MODEL=llava:13b
   OLLAMA_API_BASE=http://host.docker.internal:11434
   ```

4. This requires code changes to add Ollama support (not currently implemented)

## Verify Configuration

Check your current LLM config:
```bash
docker-compose exec backend python -c "
from backend.config.settings import settings
print(f'Provider: {settings.LLM_VISION_PROVIDER}')
print(f'Model: {settings.LLM_VISION_MODEL}')
print(f'API Key Configured: {bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != \"your_key_here\")}')
"
```

## Health Check Endpoint

Check LLM service status:
```bash
curl http://localhost:8000/api/signals/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "trading-signals",
  "llm_provider": "openai",
  "llm_model": "gpt-4-vision-preview",
  "api_key_configured": true
}
```

## Cost Estimates

### OpenAI GPT-4 Vision
- ~$0.01 - $0.03 per chart analysis
- ~$1-3 per 100 signals
- Best quality analysis

### Google Gemini 2.0 Flash
- **FREE** up to 1500 requests/day
- Good quality, fast
- Recommended for development/testing

## Next Steps

1. Choose your LLM provider
2. Get API key
3. Update `.env` file
4. Restart Docker services
5. Test signal generation

## Questions?

- Check API key validity at provider's console
- Ensure no trailing spaces in `.env` file
- Check Docker logs: `docker-compose logs backend --tail=100`

