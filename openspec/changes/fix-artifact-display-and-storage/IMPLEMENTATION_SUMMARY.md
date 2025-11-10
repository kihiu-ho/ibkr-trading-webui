# Implementation Summary: Fix Artifact Display and Storage

## Overview
Fixed three issues related to artifact storage and display:
1. Empty artifact endpoint response
2. Charts not uploaded to MinIO
3. Decimal JSON serialization error

## Issues Found and Fixed

### 1. Empty Artifact Endpoint Response
**Issue**: Artifact endpoint `/api/artifacts/{id}` was returning incomplete or empty data
**Root Cause**: Decimal values in artifact data were not being properly serialized to JSON
**Fix**: 
- Added `convert_decimals()` function in `Artifact.to_dict()` to recursively convert Decimal to float
- Updated artifact model to handle Decimal types in all JSON fields (chart_data, signal_data, metadata)

### 2. Charts Not in MinIO
**Issue**: Chart images stored in `/tmp/` (local paths) instead of MinIO, making them inaccessible after container restart
**Root Cause**: Charts were not being uploaded to MinIO before storing as artifacts
**Fix**:
- Added MinIO upload calls in `ibkr_trading_signal_workflow.py` for both daily and weekly charts
- Store MinIO URLs in artifact `image_path` field
- Fallback to local path if MinIO upload fails
- Store both MinIO URL and local path in chart_data metadata

### 3. Decimal JSON Serialization Error
**Error**: `Object of type Decimal is not JSON serializable`
**Root Cause**: Decimal values in signal_data (e.g., confidence_score) were not converted to float before JSON serialization
**Fix**:
- Added `_convert_decimals()` helper function in `artifact_storage.py` to recursively convert Decimal to float
- Applied conversion to signal_data, metadata, and chart_data before JSON serialization
- Updated signal artifact storage to convert confidence_score to float
- Updated artifact model `to_dict()` to convert Decimal values in all JSON fields

## Changes Made

### Backend Changes

1. **`backend/models/artifact.py`**:
   - Added `convert_decimals()` function to handle Decimal serialization
   - Updated `to_dict()` to convert Decimal values in chart_data, signal_data, and metadata
   - Convert confidence field to float

2. **`dags/utils/artifact_storage.py`**:
   - Added `_convert_decimals()` helper function
   - Convert Decimal values in signal_data, metadata, and chart_data before JSON serialization
   - Handle Decimal in confidence field

### Workflow Changes

3. **`dags/ibkr_trading_signal_workflow.py`**:
   - Added MinIO upload for daily charts
   - Added MinIO upload for weekly charts
   - Store MinIO URLs in artifact image_path
   - Convert confidence_score to float in signal_data

## Features

### Chart Storage
- Charts uploaded to MinIO after generation
- MinIO URLs stored in artifact image_path field
- Charts accessible after container restart
- Fallback to local paths if MinIO upload fails
- Both MinIO URL and local path stored in metadata

### Decimal Handling
- Automatic conversion of Decimal to float for JSON serialization
- Recursive conversion in nested dictionaries and lists
- Applied to all JSON fields (chart_data, signal_data, metadata)
- No serialization errors when storing artifacts

### Artifact Display
- Complete artifact data returned by endpoint
- All fields properly serialized
- Chart images display from MinIO URLs
- Graceful handling of missing or invalid data

## Files Modified

1. `backend/models/artifact.py` - Added Decimal conversion in to_dict()
2. `dags/utils/artifact_storage.py` - Added _convert_decimals() function
3. `dags/ibkr_trading_signal_workflow.py` - Added MinIO upload for charts

## Testing

### Before Fix
- Artifact endpoint returned incomplete data
- Charts stored in `/tmp/` (ephemeral)
- JSON serialization errors with Decimal values

### After Fix
- Artifact endpoint returns complete data
- Charts uploaded to MinIO and accessible via URLs
- No JSON serialization errors
- All Decimal values properly converted to float

## Usage

1. **Chart Generation**: Charts are automatically uploaded to MinIO and stored as artifacts with MinIO URLs
2. **Artifact Retrieval**: `/api/artifacts/{id}` returns complete artifact data with all fields
3. **Chart Display**: Frontend displays charts from MinIO URLs in artifacts page

## OpenSpec Proposal

The OpenSpec change proposal is located at:
- `openspec/changes/fix-artifact-display-and-storage/proposal.md`
- `openspec/changes/fix-artifact-display-and-storage/tasks.md`
- `openspec/changes/fix-artifact-display-and-storage/specs/artifact-management/spec.md`
- `openspec/changes/fix-artifact-display-and-storage/specs/airflow-integration/spec.md`

The proposal has been validated and all implementation tasks are complete.

