# Cleanup Codebase and Organize Folder Structure

## Why

The codebase has accumulated many temporary files, logs, and documentation files in the root directory, making it difficult to navigate and maintain. We need to:
- Remove unnecessary Airflow logs and temporary files
- Organize documentation into proper folders
- Establish a clear folder structure for future development
- Preserve the structure in AGENTS.md for consistency

## What Changes

### 1. Remove Temporary Files
- Delete all Airflow log files in `reference/airflow/logs/`
- Remove temporary test files and debug logs
- Clean up old build artifacts

### 2. Organize Documentation
- Move status/fix completion docs to `docs/history/`
- Move quick start guides to `docs/guides/`
- Move implementation summaries to `docs/implementation/`
- Keep only essential README files in root

### 3. Organize Scripts
- Move test scripts to `tests/scripts/`
- Move utility scripts to `scripts/`
- Organize by purpose

### 4. Update Folder Structure
- Document in `AGENTS.md` (or update existing)
- Ensure all developers understand the structure

## Impact

- **Positive**:
  - Cleaner root directory
  - Easier navigation
  - Better organization
  - Reduced repository size (after removing logs)
  
- **Negative**: 
  - May break links to moved files (need to update references)
  - Developers need to learn new structure

## Migration Path

1. Create folder structure
2. Move files to appropriate locations
3. Update any hardcoded paths
4. Document structure in AGENTS.md
5. Remove temporary files and logs

## Testing Checklist

- [ ] All documentation accessible
- [ ] Scripts still work after moving
- [ ] No broken links
- [ ] Folder structure documented
- [ ] Logs removed (will be regenerated)

## Files Affected

- Root directory (many .md files)
- `reference/airflow/logs/` (all log files)
- Documentation organization
- Script organization

## Status

🔄 **IN PROGRESS** - Designing folder structure and implementing cleanup.

