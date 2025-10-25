# llm-integration Specification

## Purpose
TBD - created by archiving change llm-chart-signals. Update Purpose after archive.
## Requirements
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

### Requirement: LLM Provider Configuration
The system SHALL allow users to configure LLM provider settings via environment variables.

#### Scenario: Configure OpenAI provider
- **GIVEN** a user wants to use OpenAI for chart analysis
- **WHEN** configuring the system
- **THEN** the system SHALL accept configuration via .env:
  - `LLM_VISION_PROVIDER=openai`
  - `LLM_VISION_MODEL=gpt-4-vision-preview`
  - `OPENAI_API_KEY=sk-proj-...`
  - `OPENAI_API_BASE=https://api.openai.com/v1`
- **AND** SHALL validate API key is not a placeholder value

#### Scenario: Configure Gemini provider
- **GIVEN** a user wants to use Google Gemini for chart analysis
- **WHEN** configuring the system
- **THEN** the system SHALL accept configuration via .env:
  - `LLM_VISION_PROVIDER=gemini`
  - `LLM_VISION_MODEL=gemini-2.0-flash-exp`
  - `GEMINI_API_KEY=...`
  - `GEMINI_API_BASE=https://generativelanguage.googleapis.com/v1beta`
- **AND** SHALL validate API key is configured

### Requirement: Configuration Validation
The system SHALL validate LLM configuration on startup and provide clear error messages.

#### Scenario: Missing API key detected on startup
- **GIVEN** LLM_VISION_PROVIDER is "openai"
- **WHEN** OPENAI_API_KEY is not set or equals "your_key_here"
- **THEN** the system SHALL log a warning message:
  - "⚠️  OpenAI API key not configured!"
  - "Signal generation will fail."
  - "Please set OPENAI_API_KEY in .env file."
  - "Get your key from https://platform.openai.com/api-keys"
- **AND** SHALL continue startup (not crash)

#### Scenario: API key validation during request
- **GIVEN** a signal generation request is made
- **WHEN** the LLM service attempts to call the API
- **AND** the API key is missing or invalid
- **THEN** the system SHALL raise a ValueError with:
  - Clear explanation of the problem
  - Instructions for where to set the API key
  - Link to get a new API key
- **AND** SHALL return HTTP 500 with helpful error message

### Requirement: Configuration Documentation
The system SHALL provide comprehensive documentation for LLM configuration.

#### Scenario: User needs to configure LLM
- **GIVEN** a user encounters an LLM configuration error
- **WHEN** they check the documentation
- **THEN** the system SHALL provide:
  - FIX_LLM_CONFIG.md with step-by-step instructions
  - .env.example with all LLM options documented
  - Comments explaining each configuration option
  - Links to API key registration pages
  - Cost comparison between providers
  - Troubleshooting section

#### Scenario: Environment variable documentation
- **GIVEN** .env.example file
- **WHEN** user reviews LLM configuration options
- **THEN** the file SHALL include:
  - Provider selection options (openai, gemini, ollama)
  - Model options for each provider
  - API key placeholders with helpful comments
  - Optional parameters (timeout, temperature, max_tokens)
  - Feature flags (LLM_ENABLED, LLM_CONSOLIDATE_TIMEFRAMES)
  - Example values that work out of the box

