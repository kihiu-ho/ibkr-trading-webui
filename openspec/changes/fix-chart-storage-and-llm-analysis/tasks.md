## 1. Fix LLM Analysis Bug
- [x] 1.1 Fix `NameError: bars is not defined` in `llm_analysis` function
- [x] 1.2 Pass bars data from chart generation to LLM analysis via XCom
- [x] 1.3 Test LLM analysis with fixed code

## 2. Chart Storage in MinIO
- [x] 2.1 Add MinIO upload functionality to chart generation
- [x] 2.2 Upload charts to MinIO after generation
- [x] 2.3 Store MinIO URLs in artifacts instead of local paths
- [x] 2.4 Update artifact storage to handle MinIO URLs

## 3. Frontend Artifact Grouping
- [x] 3.1 Update frontend to group artifacts by symbol
- [x] 3.2 Within each symbol, group by type (charts, LLM, signals, etc.)
- [x] 3.3 Update artifact display UI to show grouped structure
- [x] 3.4 Test artifact grouping display

## 4. Testing
- [x] 4.1 Test chart generation and MinIO upload
- [x] 4.2 Test artifact storage with MinIO URLs
- [x] 4.3 Test LLM analysis with fixed code
- [x] 4.4 Test frontend artifact grouping
- [ ] 4.5 Test end-to-end workflow

