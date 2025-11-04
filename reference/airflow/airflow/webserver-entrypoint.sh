#!/bin/bash
set -e

# Convert AIRFLOW_DATABASE_URL format for Airflow (psycopg2-binary needs postgresql:// not postgresql+psycopg*://)
if [ -n "$AIRFLOW_DATABASE_URL" ]; then
  export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=$(echo "$AIRFLOW_DATABASE_URL" | sed 's/postgresql+psycopg[^:]*:/postgresql:/')
  export AIRFLOW__CELERY__RESULT_BACKEND="db+$(echo "$AIRFLOW_DATABASE_URL" | sed 's/postgresql+psycopg[^:]*:/postgresql:/')"
fi

# Use Airflow's default entrypoint to run webserver
exec /entrypoint airflow webserver