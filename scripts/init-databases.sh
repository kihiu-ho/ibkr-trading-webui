#!/bin/bash
set -e

# Database initialization script for Airflow and MLflow
# This script runs during PostgreSQL container startup to create required databases and users

echo "Initializing databases..."

# Create Airflow database and user if they don't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
  -- Create airflow user and database
  DO \$\$
  BEGIN
     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'airflow') THEN
        CREATE USER airflow WITH PASSWORD 'airflow';
     END IF;
  END
  \$\$;

  -- Create airflow database if it doesn't exist
  SELECT 'CREATE DATABASE airflow OWNER airflow'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

  -- Grant permissions
  GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
EOSQL

# Create MLflow database and user if they don't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
  -- Create mlflow user and database
  DO \$\$
  BEGIN
     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mlflow') THEN
        CREATE USER mlflow WITH PASSWORD 'mlfLow';
     END IF;
  END
  \$\$;

  -- Create mlflow database if it doesn't exist
  SELECT 'CREATE DATABASE mlflow OWNER mlflow'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mlflow')\gexec

  -- Grant permissions
  GRANT ALL PRIVILEGES ON DATABASE mlflow TO mlflow;
EOSQL

# Create backend (ibkr_trading) database for artifacts and market data
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
  -- The backend database uses the postgres user (default)
  -- Create ibkr_trading database if it doesn't exist
  SELECT 'CREATE DATABASE ibkr_trading'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ibkr_trading')\gexec

  -- Grant permissions to postgres user (which is the default)
  GRANT ALL PRIVILEGES ON DATABASE ibkr_trading TO postgres;
EOSQL

echo "Database initialization completed successfully"
