# OpenAI API Configuration Guide

## Overview

This application uses OpenAI's API (or OpenAI-compatible APIs) for:
- Chart analysis using GPT-4-Vision
- Trading signal generation
- Analysis consolidation and decision making

## How It Works

### Base URL Configuration

The application reads `OPENAI_API_BASE` from your `.env` file and automatically appends the appropriate endpoints:

```
Base URL from .env: https://turingai.plus/v1
↓
Full Endpoint: https://turingai.plus/v1/chat/completions
```

### What You'll See in Logs

When the application starts, you'll see logging that confirms the configuration:

```
🔧 Initializing AIService with OpenAI-compatible API
   Base URL (from .env): https://turingai.plus/v1
   Model: gpt-4-turbo-preview
   API Key configured: Yes

🔗 OpenAI API Configuration:
   Base URL (from .env): https://turingai.plus/v1
   Full Endpoint: https://turingai.plus/v1/chat/completions
   Model: gpt-4-vision-preview
```

This confirms the application is reading your `.env` configuration correctly!

## Supported OpenAI-Compatible APIs

### 1. OpenAI Official

```env
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-...your-key...
OPENAI_MODEL=gpt-4-turbo-preview
LLM_VISION_MODEL=gpt-4-vision-preview
```

### 2. TuringAI (Your Current Setup)

```env
OPENAI_API_BASE=https://turingai.plus/v1
OPENAI_API_KEY=your_turingai_key
OPENAI_MODEL=gpt-4-turbo-preview
LLM_VISION_MODEL=gpt-4-vision-preview
```

**What happens:**
- Base URL: `https://turingai.plus/v1` (from your .env)
- Endpoint called: `https://turingai.plus/v1/chat/completions`
- ✅ This is correct and working as intended!

### 3. Azure OpenAI

```env
OPENAI_API_BASE=https://your-resource.openai.azure.com/openai/deployments/your-deployment
OPENAI_API_KEY=your_azure_key
OPENAI_MODEL=gpt-4
```

### 4. Local LLM (Ollama, LM Studio, etc.)

```env
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=not-needed
OPENAI_MODEL=llama2
```

### 5. Other OpenAI-Compatible Services

Any service that implements the OpenAI API standard:
- DeepSeek
- Anthropic (via proxy)
- Custom LLM servers
- Enterprise AI gateways

## How Services Use the Configuration

### LLM Service (llm_service.py)

Uses `httpx` to make direct API calls:

```python
# Reads from settings (which loads from .env)
api_endpoint = f"{settings.OPENAI_API_BASE}/chat/completions"

# Makes API call
response = await client.post(
    api_endpoint,  # https://turingai.plus/v1/chat/completions
    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
    json=payload
)
```

### AI Service (ai_service.py)

Uses the official OpenAI Python library:

```python
# The library automatically handles endpoint construction
self.client = openai.OpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_API_BASE  # https://turingai.plus/v1
)

# Library automatically appends /chat/completions, /embeddings, etc.
response = self.client.chat.completions.create(
    model=self.model,
    messages=[...]
)
```

## Configuration Validation

### At Startup

Both services log their configuration when initialized:

```
INFO:backend.services.ai_service:🔧 Initializing AIService with OpenAI-compatible API
INFO:backend.services.ai_service:   Base URL (from .env): https://turingai.plus/v1
INFO:backend.services.ai_service:   Model: gpt-4-turbo-preview
INFO:backend.services.ai_service:   API Key configured: Yes
```

### At API Call Time

```
INFO:backend.services.llm_service:🔗 OpenAI API Configuration:
INFO:backend.services.llm_service:   Base URL (from .env): https://turingai.plus/v1
INFO:backend.services.llm_service:   Full Endpoint: https://turingai.plus/v1/chat/completions
INFO:backend.services.llm_service:   Model: gpt-4-vision-preview
```

This makes it easy to verify your configuration is being used correctly!

## Troubleshooting

### Issue: "Cannot connect to API endpoint"

**Symptom:**
```
Cannot connect to OpenAI API at https://turingai.plus/v1: ...
```

**Solutions:**
1. Check if the base URL is accessible:
   ```bash
   curl https://turingai.plus/v1/models
   ```

2. Verify your API key is valid

3. Check network connectivity from Docker container:
   ```bash
   docker-compose exec backend curl https://turingai.plus/v1/models
   ```

### Issue: "401 Unauthorized"

**Symptom:**
```
OpenAI API HTTP error: 401 - {"error": "Invalid API key"}
```

**Solutions:**
1. Check your API key in `.env` file
2. Ensure API key hasn't expired
3. Verify the API key is for the correct service (TuringAI, not OpenAI)

### Issue: "Model not found"

**Symptom:**
```
OpenAI API HTTP error: 404 - {"error": "Model not found"}
```

**Solutions:**
1. Check which models are available from your provider:
   ```bash
   curl https://turingai.plus/v1/models \
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

2. Update your `.env` with correct model name:
   ```env
   OPENAI_MODEL=gpt-4-turbo-preview
   LLM_VISION_MODEL=gpt-4-vision-preview
   ```

### Issue: Not reading from .env file

**Symptom:**
Logs show default values instead of your configuration

**Solutions:**
1. Ensure `.env` file exists in project root:
   ```bash
   ls -la .env
   ```

2. Check file contents:
   ```bash
   cat .env | grep OPENAI_API_BASE
   ```

3. Restart the services to pick up changes:
   ```bash
   docker-compose restart backend celery-worker
   ```

4. Verify environment variables are loaded:
   ```bash
   docker-compose exec backend env | grep OPENAI
   ```

## Testing Your Configuration

### 1. Check logs during startup

```bash
docker-compose logs backend | grep "OpenAI API Configuration"
```

You should see:
```
Base URL (from .env): https://turingai.plus/v1
```

### 2. Test API connectivity

```bash
# From host machine
curl https://turingai.plus/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# From inside container
docker-compose exec backend curl https://turingai.plus/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 3. Generate a test signal

Use the API or frontend to trigger chart analysis. Check logs for:

```
🔗 OpenAI API Configuration:
   Base URL (from .env): https://turingai.plus/v1
   Full Endpoint: https://turingai.plus/v1/chat/completions
   Model: gpt-4-vision-preview
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_BASE` | Yes | `https://api.openai.com/v1` | Base URL for OpenAI-compatible API |
| `OPENAI_API_KEY` | Yes | None | API key for authentication |
| `OPENAI_MODEL` | No | `gpt-4-turbo-preview` | Model for text generation |
| `LLM_VISION_MODEL` | No | `gpt-4-vision-preview` | Model for vision/image analysis |
| `LLM_VISION_PROVIDER` | No | `openai` | Provider type (`openai` or `gemini`) |
| `LLM_VISION_TIMEOUT` | No | `60` | Request timeout in seconds |
| `LLM_VISION_MAX_TOKENS` | No | `4096` | Maximum tokens in response |
| `LLM_VISION_TEMPERATURE` | No | `0.1` | Response randomness (0.0-2.0) |

## Best Practices

1. **Use environment variables**: Never hardcode API keys or URLs in code
2. **Test connectivity first**: Verify the API endpoint works before running workflows
3. **Monitor logs**: Check startup and API call logs to confirm configuration
4. **Set appropriate timeouts**: Vision API calls can take 30-60 seconds
5. **Use HTTPS**: Always use secure connections for API endpoints
6. **Keep keys secret**: Never commit `.env` files to version control

## Summary

✅ **Your current setup is working correctly!**

When you see:
```
Calling OpenAI API: https://turingai.plus/v1/chat/completions
```

This means:
- ✅ Application read `OPENAI_API_BASE=https://turingai.plus/v1` from your `.env`
- ✅ Application appended `/chat/completions` to form complete endpoint
- ✅ API call will be made to the correct URL

The logging has been improved to make this more explicit:

```
🔗 OpenAI API Configuration:
   Base URL (from .env): https://turingai.plus/v1
   Full Endpoint: https://turingai.plus/v1/chat/completions
   Model: gpt-4-vision-preview
```

No changes needed to your `.env` file - everything is working as designed!

