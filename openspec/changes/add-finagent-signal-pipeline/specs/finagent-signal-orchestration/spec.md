## ADDED Requirements
### Requirement: FinAgent Multimodal Agent Integration
The system SHALL provide a FinAgent runner that reproduces the market-intelligence, diversified memory, dual-level reflection, and decision modules described in arXiv:2402.18485 using the DVampire/FinAgent reference code plus our existing IBKR market-data + indicator modules.

#### Scenario: FinAgent reasoning over multimodal context
- **GIVEN** IBKR data services provide OHLCV data, precomputed indicators, `webapp/services/chart_service.py` renders the chart PNGs, and existing workflow utilities supply serialized news/headline feeds for a symbol
- **WHEN** the FinAgent runner executes
- **THEN** it SHALL construct FinAgent's four prompts (market intelligence, retrieval query, low-level reflection, high-level reflection) with both textual (news), numerical (price tensors), and visual (chart PNG) inputs
- **AND** SHALL execute FinAgent memory retrieval + tool calls (technical indicator tools, expert strategy templates) before producing a BUY/SELL/HOLD action with confidence and reasoning trace
- **AND** SHALL expose configuration for reflection rounds, retrieval top-k, tool enablement, and FinAgent checkpoint path via environment variables or Airflow variables

#### Scenario: Shared `.env` configuration
- **GIVEN** `.env` already defines `DATABASE_URL`, `NEON_DATABASE`, `OPENAI_API_KEY`, `OPENAI_API_BASE`, `OPENAI_MODEL`, and `LLM_VISION_*`
- **WHEN** the FinAgent runner initializes database + LLM clients
- **THEN** it SHALL reuse those environment variables (via existing config loader) instead of duplicating credentials, ensuring both the transactional Postgres connection and the Neon metadata database plus LLM provider configuration remain the single source of truth for backend, Airflow, and FinAgent components
- **AND** SHALL store FinAgent metadata, imported datasets, normalized market data, and LLM prompts/responses in the Neon database referenced by `NEON_DATABASE`

#### Scenario: RL baseline comparison
- **GIVEN** PPO/DQN/SAC baselines implemented in TradingAgents
- **WHEN** FinAgent finishes a run
- **THEN** it SHALL compare its action vs. baseline recommendation (if available) and record the delta (expected profit difference, Sharpe delta) inside the output payload for downstream risk checks

### Requirement: Airflow + MLflow Orchestration
The system SHALL orchestrate FinAgent runs inside a dedicated Airflow DAG and record every run in MLflow for auditability.

- **WHEN** `finagent_trading_signal_workflow` is triggered manually or on schedule
- **THEN** the DAG SHALL execute tasks for (1) dataset preparation via IBKR client + existing chart/indicator modules, (2) FinAgent inference, (3) risk validation + IBKR order context, (4) MLflow logging, and (5) signal persistence
- **AND** XCom payloads SHALL remain JSON-serializable and include workflow_execution_id + strategy_id for traceability
- **AND** failures in FinAgent inference SHALL mark the task failed and surface stack traces without affecting dataset prep artifacts

#### Scenario: MLflow experiment logging
- **WHEN** FinAgent inference completes (success or failure)
- **THEN** the workflow SHALL wrap execution in `mlflow_run_context`
- **AND** log parameters (FinAgent version/hash, dataset, symbol, reflection rounds, tool toggles), metrics (expected return, realized PnL simulation, Sharpe, confidence), and artifacts (market-intelligence prompt, dual-reflection transcripts, chart images, decision JSON)
- **AND** store MLflow `run_id` + artifact URIs in artifact storage so backend APIs can link to the run later

### Requirement: Signal Persistence + API Compatibility
The system SHALL convert FinAgent output into the existing TradingSignal schema while preserving FinAgent-specific metadata for UI/API consumers.

#### Scenario: FinAgent signal creation
- **WHEN** FinAgent produces a decision
- **THEN** the workflow SHALL construct a TradingSignal record with action, confidence, entry/stop/target ranges, reflection summary, RL baseline deltas, and MLflow `run_id`
- **AND** mark `analysis_method="finagent_v1"` so downstream services can distinguish FinAgent signals from legacy LLM outputs
- **AND** persist the signal in the backend database and attach stored artifacts (charts, reasoning logs) via existing artifact storage helpers

#### Scenario: API retrieval
- **WHEN** a client requests `/api/signals/{symbol}`
- **THEN** the backend SHALL be able to include FinAgent metadata (reflection summary, baseline comparison, MLflow link) without additional API versions as long as FinAgent fields exist in the TradingSignal payload's `metadata` map
#### Scenario: Weaviate vector memory
- **GIVEN** `.env` defines `WEAVIATE_URL` and `WEAVIATE_API_KEY`
- **WHEN** the FinAgent runner stores or retrieves diversified memories
- **THEN** it SHALL instantiate a client using:
  ```python
  import os
  import weaviate
  from weaviate.classes.init import Auth

  client = weaviate.connect_to_weaviate_cloud(
      cluster_url=os.environ["WEAVIATE_URL"],
      auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
  )
  ```
- **AND** SHALL use the vector store for both low-level and high-level reflections (querying by symbol + workflow execution + embedding space)
