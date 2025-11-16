## 1. Specification
- [x] 1.1 Add artifact-management delta describing chart context persistence
- [x] 1.2 Add api-backend delta covering enriched artifact responses
- [x] 1.3 `openspec validate add-chart-artifact-context --strict`

## 2. Implementation
- [x] 2.1 Capture market data + indicator metadata when storing daily/weekly chart artifacts
- [x] 2.2 Persist chart artifact IDs in XCom for later enrichment
- [x] 2.3 Update LLM task to backfill prompt/response/model_name + metadata onto chart artifacts
- [x] 2.4 Add artifact update helper in `utils.artifact_storage`
- [x] 2.5 Hydrate backend artifact API responses with market data + LLM context fallbacks

## 3. Testing
- [x] 3.1 Create test script for enrichment verification (`test_enrichment.py`)
- [x] 3.2 Syntax validation (all files compile successfully)
