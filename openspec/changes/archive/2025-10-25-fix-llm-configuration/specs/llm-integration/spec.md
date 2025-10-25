# LLM Integration Configuration - Spec Delta

## ADDED Requirements

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

