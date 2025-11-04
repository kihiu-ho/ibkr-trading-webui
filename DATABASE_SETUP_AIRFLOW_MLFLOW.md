# Database Setup for Airflow and MLflow

## Overview

The IBKR Trading WebUI system uses external PostgreSQL databases for all services including Airflow and MLflow. This guide explains how to set up the required databases.

## Requirements

You need **three databases** in your PostgreSQL instance:
1. **Backend database** - For trading application data
2. **Airflow database** - For Airflow metadata
3. **MLflow database** - For MLflow experiment tracking

All three can be in the same PostgreSQL instance but must be separate databases.

## Database Creation

### Option 1: Using psql Command Line

```sql
-- Connect to your PostgreSQL instance
psql "postgresql://username:password@host:port/postgres?sslmode=require"

-- Create databases
CREATE DATABASE ibkr_trading;  -- For backend (or use your existing database name)
CREATE DATABASE airflow;        -- For Airflow
CREATE DATABASE mlflow;         -- For MLflow

-- Grant permissions (if needed)
GRANT ALL PRIVILEGES ON DATABASE ibkr_trading TO your_user;
GRANT ALL PRIVILEGES ON DATABASE airflow TO your_user;
GRANT ALL PRIVILEGES ON DATABASE mlflow TO your_user;
```

### Option 2: Using Neon (Recommended)

If you're using Neon PostgreSQL:

1. Go to https://neon.tech
2. Log in to your account
3. Select your project
4. Click "Databases" in the left sidebar
5. Click "New Database" button
6. Create databases named:
   - `airflow` (if not already exists)
   - `mlflow`
7. Note down the connection strings

### Option 3: Using GUI Tool (pgAdmin, DBeaver, etc.)

1. Connect to your PostgreSQL server
2. Right-click on "Databases"
3. Select "Create" > "Database"
4. Create `airflow` database
5. Create `mlflow` database
6. Grant appropriate permissions

## Environment Configuration

### 1. Edit your `.env` file

```bash
# Copy from example if you haven't already
cp env.example .env

# Edit the file
nano .env  # or use your preferred editor
```

### 2. Configure Database URLs

Update these three variables in your `.env` file:

```bash
# Backend Database (existing)
DATABASE_URL=postgresql+psycopg2://user:password@host:port/ibkr_trading?sslmode=require

# Airflow Database (NEW)
AIRFLOW_DATABASE_URL=postgresql+psycopg2://user:password@host:port/airflow?sslmode=require

# MLflow Database (NEW)
MLFLOW_DATABASE_URL=postgresql+psycopg2://user:password@host:port/mlflow?sslmode=require
```

### 3. Connection String Format

The format is:
```
postgresql+psycopg2://USERNAME:PASSWORD@HOST:PORT/DATABASE?sslmode=require
```

**Components:**
- `USERNAME`: Your PostgreSQL username
- `PASSWORD`: Your PostgreSQL password (URL-encode special characters!)
- `HOST`: PostgreSQL server hostname
- `PORT`: PostgreSQL port (usually 5432)
- `DATABASE`: Database name (ibkr_trading, airflow, or mlflow)
- `sslmode=require`: Enforce SSL connection (recommended)

### 4. Special Characters in Password

If your password contains special characters, URL-encode them:

| Character | URL Encoded |
|-----------|-------------|
| @ | %40 |
| # | %23 |
| $ | %24 |
| % | %25 |
| & | %26 |
| + | %2B |
| / | %2F |
| = | %3D |
| ? | %3F |

**Example:**
```bash
# Password: my$ecret@pass
# Encoded:  my%24ecret%40pass

DATABASE_URL=postgresql+psycopg2://user:my%24ecret%40pass@host:5432/ibkr_trading?sslmode=require
```

## Example Configurations

### Example 1: Neon PostgreSQL

```bash
# Backend
DATABASE_URL=postgresql+psycopg2://myuser:mypass@ep-example-123456.us-east-1.aws.neon.tech/ibkr_trading?sslmode=require

# Airflow
AIRFLOW_DATABASE_URL=postgresql+psycopg2://myuser:mypass@ep-example-123456.us-east-1.aws.neon.tech/airflow?sslmode=require

# MLflow  
MLFLOW_DATABASE_URL=postgresql+psycopg2://myuser:mypass@ep-example-123456.us-east-1.aws.neon.tech/mlflow?sslmode=require
```

### Example 2: Local PostgreSQL (Docker Host)

```bash
# Backend
DATABASE_URL=postgresql+psycopg2://postgres:postgres@host.docker.internal:5432/ibkr_trading

# Airflow
AIRFLOW_DATABASE_URL=postgresql+psycopg2://postgres:postgres@host.docker.internal:5432/airflow

# MLflow
MLFLOW_DATABASE_URL=postgresql+psycopg2://postgres:postgres@host.docker.internal:5432/mlflow
```

### Example 3: AWS RDS

```bash
# Backend
DATABASE_URL=postgresql+psycopg2://admin:password@mydb.abc123.us-east-1.rds.amazonaws.com:5432/ibkr_trading?sslmode=require

# Airflow
AIRFLOW_DATABASE_URL=postgresql+psycopg2://admin:password@mydb.abc123.us-east-1.rds.amazonaws.com:5432/airflow?sslmode=require

# MLflow
MLFLOW_DATABASE_URL=postgresql+psycopg2://admin:password@mydb.abc123.us-east-1.rds.amazonaws.com:5432/mlflow?sslmode=require
```

## Verification

### 1. Test Backend Connection

```bash
docker-compose run --rm backend python -c "from backend.config.database import get_db; print('Backend DB: OK')"
```

### 2. Test Airflow Connection

```bash
docker-compose run --rm airflow-webserver airflow db check
```

### 3. Test MLflow Connection

```bash
docker-compose run --rm mlflow-server python -c "import psycopg2; conn = psycopg2.connect('$MLFLOW_DATABASE_URL'); print('MLflow DB: OK')"
```

## Initialization

### Airflow Database Initialization

Airflow will automatically initialize its database on first run via the `airflow-init` service. No manual steps required!

### MLflow Database Initialization

MLflow will automatically create required tables on first connection. No manual steps required!

### Backend Database Migrations

Run backend migrations as usual:
```bash
cd database/migrations
./run_migrations.sh
```

## Troubleshooting

### Error: "database does not exist"

**Solution:** Create the database in PostgreSQL:
```sql
CREATE DATABASE airflow;  -- or mlflow
```

### Error: "password authentication failed"

**Solution:** Check your credentials and ensure special characters are URL-encoded.

### Error: "SSL connection required"

**Solution:** Add `?sslmode=require` to your connection string.

### Error: "could not connect to server"

**Solution:** 
1. Check if PostgreSQL server is running
2. Verify host and port are correct
3. Check firewall rules allow connections
4. For Docker, use `host.docker.internal` for localhost

### Error: "permission denied"

**Solution:** Grant permissions to your user:
```sql
GRANT ALL PRIVILEGES ON DATABASE airflow TO your_user;
GRANT ALL PRIVILEGES ON DATABASE mlflow TO your_user;
```

## Migration from Containerized PostgreSQL

If you were using the old containerized PostgreSQL:

### 1. Export Data (if needed)

```bash
# Backup Airflow data
docker exec ibkr-postgres pg_dump -U airflow airflow > airflow_backup.sql

# Backup MLflow data
docker exec ibkr-postgres pg_dump -U mlflow mlflow > mlflow_backup.sql
```

### 2. Import to External Database

```bash
# Import Airflow
psql "postgresql://user:pass@host:port/airflow?sslmode=require" < airflow_backup.sql

# Import MLflow
psql "postgresql://user:pass@host:port/mlflow?sslmode=require" < mlflow_backup.sql
```

### 3. Update Configuration

Update `.env` with new database URLs as described above.

### 4. Remove Old Volume

```bash
# Stop services
docker-compose down

# Remove old PostgreSQL volume
docker volume rm ibkr_postgres_data

# Start with new configuration
docker-compose up -d
```

## Performance Recommendations

### 1. Connection Pooling

For production, consider connection pooling settings:

```bash
# In .env for Airflow
AIRFLOW__DATABASE__SQL_ALCHEMY_POOL_SIZE=5
AIRFLOW__DATABASE__SQL_ALCHEMY_MAX_OVERFLOW=10
```

### 2. Database Indexes

Airflow and MLflow create indexes automatically, but monitor performance.

### 3. Vacuum and Analyze

Regularly maintain your databases:
```sql
-- Connect to each database and run:
VACUUM ANALYZE;
```

## Security Best Practices

1. **Use Strong Passwords**: Generate strong, unique passwords
2. **Enable SSL**: Always use `sslmode=require` for remote connections
3. **Restrict Access**: Use firewall rules and IP allowlists
4. **Regular Backups**: Set up automated database backups
5. **Rotate Credentials**: Periodically update passwords
6. **Monitor Access**: Review database logs regularly

## Next Steps

After setting up databases:

1. Verify all three database URLs in `.env`
2. Run `docker-compose up -d` to start services
3. Check Airflow UI at http://localhost:8080
4. Check MLflow UI at http://localhost:5500
5. Verify no database connection errors in logs

## Related Documentation

- Main setup guide: `AIRFLOW_MLFLOW_SETUP.md`
- Quick start: `QUICKSTART_AIRFLOW_MLFLOW.md`
- Backend database setup: `DATABASE_SETUP.md`
- Environment variables: `env.example`

## Support

If you encounter issues:
1. Check logs: `docker-compose logs mlflow-server airflow-webserver`
2. Verify database connectivity from your machine
3. Review this document's troubleshooting section
4. Check PostgreSQL server logs

---

**Status**: Required for Airflow and MLflow integration  
**Updated**: November 2, 2025

