# Implementation Tasks

## 1. Chart Generation Service
- [x] 1.1 Create `backend/services/chart_generator.py`
- [x] 1.2 Implement `create_plotly_figure()` based on reference
- [x] 1.3 Add multi-timeframe support (1d, 1w, 1mo)
- [x] 1.4 Implement chart export to image (JPEG/PNG)
- [x] 1.5 Upload chart images to MinIO
- [x] 1.6 Return chart URLs for LLM consumption

## 2. LLM Integration Service
- [x] 2.1 Create `backend/services/llm_service.py`
- [x] 2.2 Implement OpenAI vision API client
- [x] 2.3 Implement Gemini vision API client (optional)
- [x] 2.4 Add prompt template system
- [x] 2.5 Implement chart image encoding for API
- [x] 2.6 Parse LLM text responses into structured data

## 3. Trading Signal Generation
- [x] 3.1 Create `backend/services/signal_generator.py`
- [x] 3.2 Implement daily chart analysis workflow
- [x] 3.3 Implement weekly chart analysis workflow
- [x] 3.4 Implement multi-timeframe consolidation
- [x] 3.5 Extract trading signals from LLM responses
- [x] 3.6 Calculate entry/stop/target prices
- [x] 3.7 Calculate R-multiples and position sizing

## 4. Database Models
- [x] 4.1 Extend Strategy model with LLM config
- [x] 4.2 Create TradingSignal model
- [x] 4.3 Add migration for new fields
- [x] 4.4 Create indexes for signal queries

## 5. API Endpoints
- [x] 5.1 Create `backend/api/signals.py`
- [x] 5.2 POST /api/signals/generate - Generate signals for symbol
- [x] 5.3 GET /api/signals/{symbol} - Get latest signal
- [x] 5.4 GET /api/signals/history - Get signal history
- [x] 5.5 POST /api/signals/batch - Batch generate for multiple symbols

## 6. Prompt Templates
- [x] 6.1 Create daily chart analysis prompt (English)
- [x] 6.2 Create weekly chart analysis prompt (English)
- [x] 6.3 Create consolidation prompt (English)
- [x] 6.4 Create Chinese prompt translations
- [x] 6.5 Store prompts in configuration

## 7. Frontend
- [x] 7.1 Create `frontend/templates/signals.html`
- [x] 7.2 Signal generation form
- [x] 7.3 Multi-chart display (daily + weekly)
- [x] 7.4 LLM analysis result display
- [x] 7.5 Trading recommendation cards
- [x] 7.6 Signal history table

## 8. Configuration
- [x] 8.1 Add LLM API keys to settings
- [x] 8.2 Add model selection config
- [x] 8.3 Add prompt template config
- [x] 8.4 Add timeframe settings

## 9. Testing
- [x] 9.1 Test chart generation for all timeframes
- [x] 9.2 Test LLM API integration
- [x] 9.3 Test signal extraction from LLM responses
- [x] 9.4 Test multi-timeframe consolidation
- [x] 9.5 End-to-end signal generation test

## 10. Documentation
- [x] 10.1 API documentation for signal endpoints
- [x] 10.2 User guide for signal generation
- [x] 10.3 Prompt engineering guide
- [x] 10.4 LLM configuration guide

## 11. OpenSpec Validation
- [x] 11.1 Validate with `openspec validate llm-chart-signals --strict`
- [x] 11.2 Update tasks to mark completion

