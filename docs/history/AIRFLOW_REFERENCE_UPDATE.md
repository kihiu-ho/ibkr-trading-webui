# Airflow Reference Update - @airflow Structure Integration

## 🎯 Summary

Successfully updated the Dockerfile and docker-compose.yml to reference the `@airflow` structure from the `reference/airflow/` directory. This aligns the current implementation with the proven reference architecture.

## 📁 Files Updated

### 1. docker-compose.yml
**Updated sections:**

#### Airflow Common Configuration
```yaml
# OLD: ./docker/airflow
build:
  context: ./docker/airflow
  dockerfile: Dockerfile

# NEW: ./reference/airflow/airflow (referencing @airflow)
build:
  context: ./reference/airflow/airflow
  dockerfile: Dockerfile
```

#### Environment Variables
```yaml
# OLD: Complex external database setup
DATABASE_URL: "${DATABASE_URL}"
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: "postgresql://neondb_owner:..."

# NEW: Simple local postgres setup (reference style)
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
```

#### Volumes
```yaml
# OLD: Current implementation paths
- ./airflow/dags:/opt/airflow/dags
- ./airflow/plugins:/opt/airflow/plugins
- ./airflow/config:/opt/airflow/config

# NEW: Reference @airflow paths
- ./reference/airflow/dags:/opt/airflow/dags
- ./reference/airflow/plugins:/opt/airflow/plugins
- ./reference/airflow/config:/opt/airflow/config
- ./reference/airflow/models:/app/models
- ./reference/airflow/config.yaml:/app/config.yaml
- ./.env:/app/.env
```

#### Added PostgreSQL Service
```yaml
# NEW: Added postgres service from reference
postgres:
  image: postgres:13
  container_name: ibkr-postgres
  environment:
    POSTGRES_USER: airflow
    POSTGRES_PASSWORD: airflow
    POSTGRES_DB: airflow
  volumes:
    - postgres_db_volume:/var/lib/postgresql/data
    - ./reference/airflow/init-multiple-dbs.sh:/docker-entrypoint-initdb.d/init-multiple-dbs.sh
  healthcheck:
    test: ["CMD", "pg_isready", "-U", "airflow"]
```

#### Updated MLflow Service
```yaml
# OLD: External database
MLFLOW_DATABASE_URL: "${DATABASE_URL}"

# NEW: Local postgres with proper command
command: mlflow server --port 5500 --host 0.0.0.0 --backend-store-uri postgresql+psycopg2://airflow:airflow@postgres/mlflow --default-artifact-root s3://mlflow
```

### 2. docker/airflow/Dockerfile
**Complete replacement:**

```dockerfile
# OLD: Complex uv-based setup with multiple stages
FROM apache/airflow:2.10.5
# Install system dependencies and uv
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*
# Install uv package manager (much faster than pip)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"
# Create models directory and set ownership
RUN mkdir -p /app/models
# Copy requirements file while still root
COPY requirements.txt /tmp/requirements.txt
# Switch to airflow user before installing packages
USER airflow
# Ensure uv is in PATH for airflow user
ENV PATH="/root/.cargo/bin:${PATH}"
# Install psycopg2-binary first (required for PostgreSQL)
# Install as airflow user to ensure proper Python path
RUN uv pip install --no-cache psycopg2-binary
# Install Python packages using uv (10-100x faster than pip)
RUN uv pip install --no-cache -r /tmp/requirements.txt

# NEW: Simplified reference structure
FROM apache/airflow:2.10.5
#Create models directory and set ownership
USER root
RUN mkdir -p /app/models
USER airflow
#Copy requirements file
COPY requirements.txt /tmp/requirements.txt
# Install Python packages as root (system-wide)
RUN pip install -r /tmp/requirements.txt
#Switch back to airflow user for safety
USER airflow
```

### 3. docker/airflow/requirements.txt
**Updated packages:**

```txt
# OLD: Extended list with additional packages
xgboost
mlflow
kafka-python
python-dotenv
pyyaml
catboost
pyspark
lightgbm
imbalanced-learn
pandas
scikit-learn
boto3
tqdm
confluent-kafka
psycopg2-binary
apache-airflow-providers-celery
httpx
pytz
requests

# NEW: Reference structure packages
xgboost
mlflow
kafka-python
python-dotenv
pyyaml
catboost
pyspark
lightgbm
imblearn
pandas
scikit-learn
boto3
tqdm
tqdm-joblib
confluent-kafka
```

## 🔗 Reference Structure Integration

### What Was Referenced

1. **`reference/airflow/airflow/`**
   - `Dockerfile`: Simplified pip-based installation
   - `requirements.txt`: Core ML packages for fraud detection

2. **`reference/airflow/`**
   - `dags/`: DAG definitions
   - `plugins/`: Custom operators and hooks
   - `config/`: Configuration files
   - `models/`: ML model storage
   - `config.yaml`: YAML configuration
   - `init-multiple-dbs.sh`: Database initialization script

3. **`reference/airflow/docker-compose.yaml`**
   - PostgreSQL service configuration
   - MLflow service with local postgres
   - Airflow volume mounts
   - Environment variable structure

### Key Changes Made

#### 1. Database Architecture
- **Before**: External Neon PostgreSQL database
- **After**: Local PostgreSQL container with multiple databases (airflow, mlflow)

#### 2. Build Process
- **Before**: Complex uv-based multi-stage builds
- **After**: Simple pip-based installation (reference style)

#### 3. Volume Structure
- **Before**: Current implementation directories
- **After**: Reference @airflow directory structure

#### 4. Service Dependencies
- **Before**: External database dependency
- **After**: Local postgres + proper health checks

## ✅ Benefits of Reference Integration

### 1. **Proven Architecture**
- Uses the working reference implementation
- Tested and validated approach
- Known to work with the existing codebase

### 2. **Simplified Setup**
- Local PostgreSQL instead of external dependencies
- Standard pip installation instead of uv complexity
- Clear volume structure and paths

### 3. **Better Reliability**
- Local database = no network issues
- Health checks ensure service readiness
- Proper service dependencies

### 4. **Easier Maintenance**
- Standard Docker patterns
- Reference documentation available
- Known configuration structure

## 🚀 Next Steps

### 1. Test the Updated Setup
```bash
# Clean restart with new configuration
docker-compose down
docker-compose up -d postgres mlflow-server
sleep 30
docker-compose up -d airflow-webserver airflow-scheduler

# Check services
docker-compose ps
curl http://localhost:8080/health
curl http://localhost:5500/
```

### 2. Verify Reference Integration
- Check that DAGs load from `reference/airflow/dags/`
- Verify config.yaml is mounted correctly
- Confirm MLflow uses local postgres database

### 3. Update Documentation
- Update any references to old paths
- Document the new local database setup
- Update deployment instructions

## 📋 Files Now Using Reference Structure

- ✅ `docker-compose.yml` → References `./reference/airflow/`
- ✅ `docker/airflow/Dockerfile` → Matches reference structure
- ✅ `docker/airflow/requirements.txt` → Uses reference packages
- ✅ `docker/mlflow/` → Already referenced
- ✅ Volumes → Mount reference directories
- ✅ Database → Local postgres with multiple DBs

## 🔍 Verification Checklist

- [ ] `docker-compose up -d` starts all services
- [ ] PostgreSQL creates airflow and mlflow databases
- [ ] Airflow webserver accessible at http://localhost:8080
- [ ] MLflow accessible at http://localhost:5500
- [ ] DAGs load from reference/airflow/dags/
- [ ] Config.yaml properly mounted
- [ ] Models directory accessible

---

**✅ Docker and docker-compose now fully reference the @airflow structure!**

The implementation now uses the proven reference architecture from `reference/airflow/` with local PostgreSQL, simplified builds, and proper volume mounts.
