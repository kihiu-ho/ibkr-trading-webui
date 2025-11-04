# Project Folder Structure

This document defines the standard folder structure for the IBKR Trading WebUI project. All files should be organized according to this structure.

## Root Directory

```
ibkr-trading-webui/
├── .gitignore              # Git ignore rules
├── .env.example            # Environment variable template
├── README.md               # Main project documentation
├── LICENSE                  # License file
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Main application Dockerfile
├── Dockerfile.airflow     # Airflow Dockerfile
├── package.json            # Node.js dependencies (if any)
├── requirements.txt        # Python dependencies
├── pytest.ini              # Pytest configuration
├── AGENTS.md               # This file - folder structure guide
│
├── dags/                   # Airflow DAGs
│   ├── models/            # Pydantic models
│   ├── utils/             # Utility modules
│   └── *.py               # DAG files
│
├── backend/                # Backend application
│   ├── app/               # Application code
│   ├── tests/             # Backend tests
│   └── requirements.txt   # Backend dependencies
│
├── frontend/               # Frontend application
│   ├── src/               # Source code
│   ├── public/            # Public assets
│   └── package.json       # Frontend dependencies
│
├── webapp/                 # Web application (if separate)
│
├── scripts/                # Utility scripts
│   ├── init-databases.sh  # Database initialization
│   ├── wait-for-it.sh     # Service wait script
│   └── *.sh               # Other utility scripts
│
├── tests/                  # Test files and scripts
│   ├── scripts/           # Test scripts
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
│
├── docs/                   # Documentation
│   ├── guides/            # How-to guides and quick starts
│   ├── implementation/    # Implementation summaries
│   ├── history/           # Status/fix completion docs
│   └── api/               # API documentation
│
├── reference/              # Reference implementations
│   ├── airflow/           # Airflow reference configs
│   └── ...                # Other references
│
├── openspec/               # OpenSpec specifications
│   ├── AGENTS.md          # OpenSpec instructions
│   ├── project.md         # Project conventions
│   ├── specs/             # Current specifications
│   └── changes/           # Change proposals
│
├── database/               # Database scripts and migrations
│
├── docker/                 # Docker-related files
│
├── plugins/                # Airflow plugins
│
└── logs/                   # Application logs (gitignored)
```

## Directory Purposes

### `/dags/`
Airflow DAG definitions and supporting code:
- `models/` - Pydantic data models
- `utils/` - Utility functions and helpers
- `*.py` - Individual DAG files

### `/backend/`
Backend application code:
- `app/` - Main application code
- `tests/` - Backend-specific tests
- `requirements.txt` - Python dependencies

### `/frontend/`
Frontend application code:
- `src/` - Source code
- `public/` - Static assets
- `package.json` - Node.js dependencies

### `/scripts/`
Utility scripts for setup, deployment, and maintenance:
- Database initialization scripts
- Service wait scripts
- Setup/deployment scripts

### `/tests/`
Test files organized by type:
- `scripts/` - Test execution scripts
- `unit/` - Unit tests
- `integration/` - Integration tests

### `/docs/`
Documentation organized by purpose:
- `guides/` - How-to guides, quick starts, tutorials
- `implementation/` - Implementation summaries and reports
- `history/` - Status updates, fix completion docs, changelogs
- `api/` - API documentation

### `/reference/`
Reference implementations and example configurations:
- `airflow/` - Airflow configuration examples
- Other reference materials

### `/openspec/`
OpenSpec specification files:
- `AGENTS.md` - Instructions for AI assistants
- `project.md` - Project conventions
- `specs/` - Current specifications
- `changes/` - Proposed changes

## File Naming Conventions

### Documentation Files
- **Guides**: `QUICK_START.md`, `SETUP_GUIDE.md`, `USER_GUIDE.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`, `DESIGN.md`
- **History**: `CHANGELOG.md`, `STATUS.md`, `FIXES_COMPLETE.md`

### Script Files
- **Setup**: `setup-*.sh`, `init-*.sh`
- **Test**: `test-*.sh`, `test-*.py`
- **Utility**: `check-*.sh`, `verify-*.sh`

### Code Files
- **Python**: `snake_case.py`
- **DAGs**: `*_workflow.py`, `*_dag.py`
- **Models**: `snake_case.py`

## Files That Should NOT Be in Root

❌ **Do NOT put in root**:
- Status update files (`*_COMPLETE.md`, `*_FIXED.md`)
- Temporary documentation (`NOW_FIXED.txt`, `CURRENT_STATUS.md`)
- Test scripts (`test-*.sh`, `test-*.py`)
- Debug logs (`*.log`)
- Old build artifacts (`*.pyc`, `__pycache__/`)

✅ **Keep in root**:
- Essential project files (`README.md`, `docker-compose.yml`)
- Configuration files (`pytest.ini`, `package.json`)
- Entry point scripts (`start-webapp.sh`)

## Migration Checklist

When adding new files:
1. ✅ Check this document for correct location
2. ✅ Follow naming conventions
3. ✅ Place in appropriate subdirectory
4. ✅ Update this document if structure changes

## Log Files

All log files are gitignored and should be placed in:
- `reference/airflow/logs/` - Airflow logs (gitignored)
- `logs/` - Application logs (gitignored)

**Never commit log files to git.**

## Examples

### Correct File Locations

```
✅ docs/guides/QUICK_START.md
✅ docs/implementation/AIRFLOW_IMPLEMENTATION.md
✅ docs/history/FIXES_APPLIED.md
✅ tests/scripts/test-airflow-workflow.sh
✅ scripts/init-databases.sh
✅ dags/utils/config.py
```

### Incorrect File Locations

```
❌ QUICK_START.md (root)
❌ AIRFLOW_IMPLEMENTATION.md (root)
❌ test-airflow-workflow.sh (root)
❌ reference/airflow/logs/*.log (committed)
```

## Maintenance

- This document should be updated when:
  - New directory is added
  - Directory purpose changes
  - Naming conventions change
  - Structure is reorganized

- Review this document during:
  - Code reviews
  - Onboarding new developers
  - Major refactoring

## Related Documents

- `.gitignore` - Defines what files should not be tracked
- `openspec/AGENTS.md` - OpenSpec instructions
- `README.md` - Project overview and setup
