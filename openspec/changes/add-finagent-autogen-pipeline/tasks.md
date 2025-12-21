## 1. Specification + Planning
- [ ] 1.1 Add/modify spec deltas for `trading-workflow` and new `finagent-autogen-pipeline` capability.
- [ ] 1.2 Define DAG id, run modes (`inference`, `train_backtest`, `both`), and required env vars in docs.
- [ ] 1.3 Pin upstream dependencies (`akshata29/finagent` + AutoGen) and document reproducibility assumptions.

## 2. Dependencies + Container Wiring
- [ ] 2.1 Update `airflow/requirements-airflow.txt` with AutoGen and `akshata29/finagent` (pinned to commit).
- [ ] 2.2 Add new config/env entries to `env.example` (FinAgent + AutoGen + MLflow registry names).
- [ ] 2.3 Ensure Airflow image builds with new dependencies (no GPU requirement for baseline path).

## 3. AutoGen Orchestration Layer
- [ ] 3.1 Implement an AutoGen orchestrator utility that runs a constrained multi-agent conversation and returns a structured decision payload.
- [ ] 3.2 Capture full conversation as an artifact (`autogen_conversation.jsonl`) and optionally persist to `agent_conversations`.
- [ ] 3.3 Add unit tests for deterministic orchestration using stubbed LLM responses.

## 4. Upstream FinAgent Adapter (akshata29)
- [ ] 4.1 Implement an adapter wrapper around `akshata29/finagent` for training/backtest and inference entrypoints.
- [ ] 4.2 Normalize upstream outputs into existing TradingSignal schema + metrics + trace bundle.
- [ ] 4.3 Add unit tests for mapping and failure modes (no network; stub upstream).

## 5. New Airflow DAG (Training + Inference)
- [ ] 5.1 Add new DAG file implementing TaskGroups for `train_backtest` and `inference`, branching on `dag_run.conf`.
- [ ] 5.2 Enforce XCom size safety: store large payloads as MLflow/MinIO artifacts, not XCom.
- [ ] 5.3 Log everything to MLflow (params, metrics, artifacts; register model/config package on training).
- [ ] 5.4 Persist WebUI artifacts (signal, reasoning, optional chart) with lineage to MLflow run.

## 6. Documentation (Model Logic + Diagrams)
- [ ] 6.1 Add deep-dive doc covering model logic and the AutoGen agent graph with Mermaid diagrams.
- [ ] 6.2 Add runbook guide explaining configuration, modes, and troubleshooting.

## 7. Validation
- [ ] 7.1 Run unit tests for adapter/orchestrator/mappers.
- [ ] 7.2 Run `airflow dags test <new_dag_id> <date>` and confirm DAG imports.
- [ ] 7.3 Smoke-run in docker compose and verify MLflow artifacts + WebUI artifact rendering.

