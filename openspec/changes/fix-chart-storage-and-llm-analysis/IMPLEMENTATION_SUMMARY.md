# Implementation Summary: Fix Chart Storage and LLM Analysis

## Overview
Fixed three issues:
1. **LLM Analysis Bug**: Fixed `NameError: bars is not defined` in LLM analysis function
2. **Chart Storage**: Added MinIO upload functionality to store charts persistently
3. **Artifact Grouping**: Updated frontend to display artifacts grouped by symbol and type

## Changes Made

### 1. Fixed LLM Analysis Bug
**File**: `dags/ibkr_stock_data_workflow.py`

- **Issue**: `bars` variable was not defined in LLM analysis function, causing `NameError`
- **Solution**: 
  - Added `bars_count` to charts_generated data structure
  - Retrieve `bars_count` from charts_generated in LLM analysis function
  - Use `bars_count` for `periods_shown` calculation with fallback to 100

### 2. Chart Storage in MinIO
**Files**: 
- `dags/utils/minio_upload.py` (new file)
- `dags/ibkr_stock_data_workflow.py`

- **Issue**: Charts were stored in `/tmp/` which is ephemeral and lost on container restart
- **Solution**:
  - Created `minio_upload.py` utility with `upload_chart_to_minio()` function
  - Upload charts to MinIO after generation
  - Store MinIO URLs in artifacts instead of local paths
  - Update LLM analysis to handle both MinIO URLs and local paths

**MinIO Upload Function**:
- Uploads chart images to MinIO bucket `trading-charts`
- Organizes charts by symbol and timeframe: `charts/{symbol}/{timeframe}/{timestamp}_{uuid}.png`
- Returns public MinIO URL for storage in artifacts
- Handles errors gracefully with logging

### 3. Frontend Artifact Grouping
**File**: `frontend/templates/airflow_monitor.html`

- **Issue**: Artifacts displayed in flat list, not organized by symbol or type
- **Solution**:
  - Added `getArtifactsBySymbol()` function to group artifacts by symbol, then by type
  - Updated artifact display to show grouped structure:
    - Symbol sections with artifact counts
    - Type subsections (charts, LLM, signals, etc.) within each symbol
    - Artifacts listed under their type
  - Improved visual hierarchy with headers and indentation

## Features

### Chart Storage
- Charts uploaded to MinIO after generation
- MinIO URLs stored in artifacts
- Charts accessible after container restart
- Fallback to local paths if MinIO upload fails

### LLM Analysis
- Fixed `bars` NameError by passing `bars_count` via XCom
- Handles both MinIO URLs and local paths for chart loading
- Downloads charts from MinIO if needed for analysis

### Artifact Display
- Grouped by symbol first (e.g., TSLA, NVDA, General)
- Within each symbol, grouped by type (charts, LLM, signals, etc.)
- Clear visual hierarchy with headers and counts
- Maintains all existing functionality (click to view details, etc.)

## Files Modified

1. `dags/ibkr_stock_data_workflow.py`:
   - Added MinIO upload calls after chart generation
   - Fixed LLM analysis to retrieve `bars_count` from charts_generated
   - Updated LLM analysis to handle MinIO URLs

2. `dags/utils/minio_upload.py` (new):
   - MinIO upload utility function
   - Handles bucket creation, file upload, URL generation

3. `frontend/templates/airflow_monitor.html`:
   - Added `getArtifactsBySymbol()` function
   - Updated artifact display to show grouped structure

## Testing

### Backend Tests
- ✅ Chart generation with MinIO upload
- ✅ Artifact storage with MinIO URLs
- ✅ LLM analysis with fixed `bars_count`
- ✅ LLM analysis handles MinIO URLs

### Frontend Tests
- ✅ Artifact grouping by symbol
- ✅ Artifact grouping by type within symbol
- ✅ Visual hierarchy and counts display correctly
- ✅ All existing functionality preserved

## Usage

1. **Chart Generation**: Charts are automatically uploaded to MinIO and stored as artifacts with MinIO URLs
2. **LLM Analysis**: Works with both MinIO URLs and local paths, retrieves `bars_count` from chart metadata
3. **Artifact Display**: Navigate to Airflow monitor → View run details → See artifacts grouped by symbol and type

## OpenSpec Proposal

The OpenSpec change proposal is located at:
- `openspec/changes/fix-chart-storage-and-llm-analysis/proposal.md`
- `openspec/changes/fix-chart-storage-and-llm-analysis/tasks.md`
- `openspec/changes/fix-chart-storage-and-llm-analysis/specs/airflow-integration/spec.md`
- `openspec/changes/fix-chart-storage-and-llm-analysis/specs/artifact-management/spec.md`

The proposal has been validated and all tasks are complete.

