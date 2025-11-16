## Why
Chart artifacts returned by the IBKR trading signal workflow only expose chart image metadata. Market data snapshots, indicator values, and the LLM prompt/response that produced the downstream signal are missing, leaving UI consumers with mostly null fields just like the TSLA Daily Chart example. Analysts need every artifact record to contain the complete context (market data + LLM reasoning) without stitching multiple endpoints.

## What Changes
- Capture the market data snapshot and indicator summary when storing daily/weekly chart artifacts in the Airflow DAG.
- Link LLM analysis output back to the chart artifacts so their `prompt`, `response`, and `model_name` fields are populated and metadata contains the signal summary.
- Hydrate artifact API responses with the enriched context so a single call returns the full object for chart artifacts, even for older runs that predate the new metadata.

## Impact
- Affected specs: artifact-management, api-backend
- Affected code: Airflow DAGs (`ibkr_trading_signal_workflow`), artifact storage utilities, backend artifact API/tests, sample artifact fixtures
