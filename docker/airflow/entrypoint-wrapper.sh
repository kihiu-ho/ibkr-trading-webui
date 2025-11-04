#!/bin/bash
# Convert DATABASE_URL format for Airflow
# Airflow works better with postgresql:// when psycopg2-binary is installed

if [ -n "$DATABASE_URL" ]; then
    # Convert postgresql+psycopg2:// to postgresql://
    export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=$(echo "$DATABASE_URL" | sed 's/postgresql+psycopg2:/postgresql:/')
    export AIRFLOW__CELERY__RESULT_BACKEND="db+$(echo "$DATABASE_URL" | sed 's/postgresql+psycopg2:/postgresql:/')"
fi

# Execute the original command
exec "$@"

