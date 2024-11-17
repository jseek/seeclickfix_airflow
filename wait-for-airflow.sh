#!/bin/bash

# Wait for Airflow Webserver to be ready
until curl -s "http://airflow_webserver:8080/health" | grep '"status": "healthy"' > /dev/null; do
  echo "Waiting for Airflow Webserver..."
  sleep 10
done

# Wait for Airflow Scheduler to be ready
until pgrep airflow > /dev/null; do
  echo "Waiting for Airflow Scheduler..."
  sleep 10
done

echo "Airflow is ready. Triggering DAG..."
exec "$@"
