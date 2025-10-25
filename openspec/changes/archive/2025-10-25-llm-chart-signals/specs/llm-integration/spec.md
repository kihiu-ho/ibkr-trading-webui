# LLM Vision Integration - Spec

## ADDED Requirements

### Requirement: LLM Vision API Integration
The system SHALL integrate with LLM vision models to analyze technical charts.

#### Scenario: Analyze chart with OpenAI GPT-4V
- **GIVEN** a chart image URL and analysis prompt
- **WHEN** requesting chart analysis
- **THEN** the system SHALL:
  - Download the chart image
  - Encode image to base64
  - Send to OpenAI vision API with prompt
  - Receive text analysis response
  - Parse response into structured format

#### Scenario: Analyze chart with Google Gemini
- **GIVEN** a chart image URL and analysis prompt
- **WHEN** using Gemini model
- **THEN** the system SHALL:
  - Download the chart image
  - Send to Gemini API with prompt
  - Receive text analysis response
  - Parse response into structured format

#### Scenario: Handle API errors gracefully
- **GIVEN** an LLM API request
- **WHEN** the API fails or rate limits
- **THEN** the system SHALL:
  - Retry with exponential backoff (max 3 attempts)
  - Log the error with context
  - Return error status with message
  - Not crash the application

### Requirement: Prompt Template System
The system SHALL use structured prompts based on the reference workflow.

#### Scenario: Daily chart analysis prompt
- **GIVEN** a request to analyze a daily chart
- **WHEN** constructing the prompt
- **THEN** the system SHALL include:
  - Analysis date and symbol
  - Core price analysis instructions
  - Trend indicator analysis (SuperTrend, MAs)
  - Confirmation indicator analysis (MACD, RSI, ATR, BB, Volume, OBV)
  - 3/4 signal confirmation system
  - Trading recommendation format
  - Risk assessment requirements
  - Target price methodology

#### Scenario: Weekly chart analysis prompt
- **GIVEN** a request to analyze a weekly chart
- **WHEN** constructing the prompt
- **THEN** the system SHALL include:
  - Medium-term trend assessment (12 months)
  - Key price level analysis
  - Weekly indicator analysis
  - Price pattern identification
  - Volume characteristics
  - Daily-weekly correlation analysis
  - 30-180 day outlook

#### Scenario: Consolidation prompt
- **GIVEN** daily and weekly analyses
- **WHEN** requesting final recommendation
- **THEN** the system SHALL include:
  - Both analysis summaries
  - Multi-timeframe signal confirmation
  - Detailed trading recommendation format
  - Risk assessment across timeframes
  - Final conclusion requirements

### Requirement: Response Parsing
The system SHALL parse LLM text responses into structured trading data.

#### Scenario: Extract trading signal
- **GIVEN** LLM analysis text in Chinese or English
- **WHEN** parsing the response
- **THEN** the system SHALL extract:
  - Overall trend: "強烈看漲/看漲/中性/看跌/強烈看跌" or "Strong Bullish/Bullish/Neutral/Bearish/Strong Bearish"
  - Trade signal: "進場/持有/出場" or "BUY/HOLD/SELL"
  - Entry price range (low, high)
  - Stop loss price
  - Conservative target price
  - Aggressive target price
  - R-multiples
  - Position size percentage

#### Scenario: Extract signal confirmation
- **GIVEN** LLM analysis text
- **WHEN** parsing confirmation section
- **THEN** the system SHALL extract:
  - SuperTrend signal (bullish/bearish)
  - Price vs 20 SMA (above/below)
  - MACD signal (buy/sell)
  - RSI position (>50 / <50)
  - Confirmation count (X/4)
  - Confirmation passed (true/false)

#### Scenario: Handle parsing errors
- **GIVEN** LLM response that doesn't match expected format
- **WHEN** parsing fails
- **THEN** the system SHALL:
  - Log the raw response
  - Return partial data if available
  - Mark fields as None/null if missing
  - Not crash the parsing process

### Requirement: Language Support
The system SHALL support both English and Chinese prompts and responses.

#### Scenario: Chinese language analysis
- **GIVEN** language parameter set to "zh"
- **WHEN** generating prompts and parsing
- **THEN** the system SHALL:
  - Use Chinese prompt templates from reference
  - Apply terminology translations (回調->回檔, 股利->股息, etc.)
  - Parse Chinese response format
  - Return Chinese text in report

#### Scenario: English language analysis
- **GIVEN** language parameter set to "en"
- **WHEN** generating prompts and parsing
- **THEN** the system SHALL:
  - Use English prompt templates
  - Parse English response format
  - Return English text in report

## API Contract

### LLM Analysis Request
```python
{
    "chart_url": str,          # Public URL to chart image
    "prompt_template": str,    # "daily", "weekly", or "consolidation"
    "symbol": str,
    "language": str,           # "en" or "zh"
    "model": str,              # "gpt-4-vision" or "gemini-2.0-flash"
    "additional_context": dict # Optional extra info
}
```

### LLM Analysis Response
```python
{
    "raw_text": str,              # Full LLM response
    "parsed_signal": {
        "trend": str,
        "signal": str,           # BUY/SELL/HOLD
        "entry_low": float,
        "entry_high": float,
        "stop_loss": float,
        "target_conservative": float,
        "target_aggressive": float,
        "r_multiple_conservative": float,
        "r_multiple_aggressive": float,
        "position_size_percent": float,
        "confirmation": {
            "supertrend": str,
            "price_vs_ma20": str,
            "macd": str,
            "rsi": str,
            "confirmed_count": int,
            "passed": bool
        }
    },
    "analysis_sections": {
        "price_analysis": str,
        "trend_indicators": str,
        "confirmation_indicators": str,
        "risk_assessment": str
    },
    "model_used": str,
    "tokens_used": int,
    "analysis_time_ms": int
}
```

## Technical Implementation

### LLM Service
```python
class LLMService:
    def analyze_chart(
        chart_url: str,
        prompt_template: str,
        symbol: str,
        language: str = "en",
        model: str = "gpt-4-vision"
    ) -> LLMAnalysisResponse
    
    def _load_prompt_template(template_name, language) -> str
    def _download_chart_image(url) -> bytes
    def _encode_image_base64(image_data) -> str
    def _call_openai_vision(prompt, image_b64) -> str
    def _call_gemini_vision(prompt, image_data) -> str
    def _parse_response(raw_text, language) -> ParsedSignal
```

### Configuration
```python
# backend/config/settings.py
OPENAI_API_KEY: str
GEMINI_API_KEY: str
LLM_DEFAULT_MODEL: str = "gpt-4-vision"
LLM_MAX_TOKENS: int = 4096
LLM_TEMPERATURE: float = 0.1
LLM_TIMEOUT_SECONDS: int = 60
```

