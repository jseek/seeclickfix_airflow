#!/bin/bash

# Wait for PostgreSQL to be available
echo "Waiting for PostgreSQL to be available..."
until pg_isready -h postgres -U airflow -d airflow; do
  echo "PostgreSQL is unavailable - waiting..."
  sleep 2
done

# Add the PostgreSQL server to pgAdmin (change if needed)
echo "Adding PostgreSQL server to pgAdmin..."

curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "PostgreSQL", "host": "postgres", "port": "5432", "username": "airflow", "password": "airflow", "sslMode": "prefer"}' \
  http://admin:admin@pgadmin:80/server/

echo "PostgreSQL server added to pgAdmin."

# Keep the container running
tail -f /dev/null
