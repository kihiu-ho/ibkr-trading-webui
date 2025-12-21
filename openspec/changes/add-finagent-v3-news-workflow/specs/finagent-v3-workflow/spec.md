## ADDED Requirements
### Requirement: FinAgent Paper-v3 Workflow
The system SHALL provide a dedicated Airflow workflow that executes the FinAgent trading pipeline using the prompt templates defined in arXiv:2402.18485v3 (Appendix F) and logs an auditable trail to MLflow.

#### Scenario: Execute FinAgent v3 workflow with auditable prompts
- **GIVEN** `reference/paper/2402.18485v3.pdf` is the source of truth for v3 prompt templates
- **WHEN** the FinAgent v3 Airflow DAG is executed
- **THEN** it SHALL use the v3 prompt templates for market intelligence, low-level reflection, high-level reflection, and decision-making
- **AND** it SHALL record per-stage prompt text, raw model response, and parsed XML output as MLflow artifacts
- **AND** it SHALL mark the output signal payload with `analysis_method="finagent_v3"`

### Requirement: NewsAPI Market Intelligence Source
The system SHALL support fetching latest market intelligence via NewsAPI configured through `.env`, and pass those items into FinAgent’s market-intelligence stage.

#### Scenario: Fetch latest news from NewsAPI
- **GIVEN** `.env` provides `NEWS_API_KEY` and the NewsAPI endpoint configuration
- **WHEN** the workflow prepares inputs for a ticker
- **THEN** it SHALL call NewsAPI `/v2/everything` (or configured base URL) with ticker query and filters
- **AND** it SHALL transform results into a normalized list containing at least `title`, `published_at`, `source`, `url`, and optional `summary/description`
- **AND** on API failure it SHALL degrade gracefully (empty news list) while preserving error context in logs/MLflow

### Requirement: MLflow Audit Trail for FinAgent v3
The system SHALL log FinAgent v3 runs to MLflow with enough metadata and artifacts to reproduce and audit the decision.

#### Scenario: MLflow contains stage artifacts
- **WHEN** a FinAgent v3 run completes
- **THEN** MLflow SHALL contain parameters (symbol, prompt version, reflection rounds, LLM model/provider) and metrics (confidence, expected returns)
- **AND** MLflow SHALL include artifacts for each stage (prompt + response + parsed output) and the final signal payload
