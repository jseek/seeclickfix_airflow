import requests
from datetime import timedelta
import logging
import json
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.providers.postgres.hooks.postgres import PostgresHook
import psycopg2
from airflow.models import Variable
from datetime import datetime
import time

# Define the API URL and table name
API_URL = "https://seeclickfix.com/api/v2/issues"
TABLE_NAME = "seeclickfix_source"

# Function to pull data and store it in kwargs
def pull_scf_data(**kwargs):
    # Check if it's the first run by checking a DAG run-specific variable
    first_run = kwargs['dag_run'].run_id == 'manual__first_run'

    # Initialize the session and pagination parameters
    all_issues = []

    params = {
        # 'after': '2024-01-01T00:00:00Z',
        'page': 1,
        'per_page': 10,
        'details': True,
        'sort_direction': ASC,
        'sort': 'updated_at'
        'place_url': 'tacoma'
    }

    # If it's the first run, don't add the updated_at_after parameter
    if not first_run:
        # Get the max updated_at timestamp from the table
        pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        conn = pg_hook.get_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT MAX(updated_at) FROM {TABLE_NAME}")
        result = cur.fetchone()
        cur.close()
        conn.close()

        # If no value is found, use a default value
        max_updated_at = result[0] if result and result[0] else '2024-11-15T00:00:00Z'

        # Ensure max_updated_at is in the correct format (ISO 8601 with 'Z' for UTC)
        if isinstance(max_updated_at, datetime):
            max_updated_at = max_updated_at.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'

        params['updated_at_after'] = max_updated_at

    while True:
        logging.info(f"Fetching data with params: {params}")

        response = requests.get(API_URL, params=params)

        # Check for 429 (Rate Limit) error and handle retry with exponential backoff
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))  # Use default of 60 seconds if not provided
            logging.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            continue  # Skip the rest of the loop and try again

        # Check for a successful response
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}")

        data = response.json()
        issues = data['issues']
        all_issues.extend(issues)  # Append the issues to the all_issues list

        pagination = data['metadata']['pagination']
        next_page = pagination.get('next_page')

        if not next_page:
            logging.info("No more pages to process.")
            break
        else:
            params['page'] = next_page

        logging.info(f"Pagination info: {pagination}")

        # Add a small delay between requests to avoid hitting rate limits
        time.sleep(2)  # Adjust this sleep time as needed (e.g., 2 seconds)

    # Store the issues in the XCom system for downstream tasks
    kwargs['ti'].xcom_push(key='scf_issues', value=all_issues)
    logging.info(f"Collected {len(all_issues)} issues.")


# Function to process issues and store them in PostgreSQL
def process_and_store_issues(**kwargs):
    issues = kwargs['ti'].xcom_pull(task_ids='pull_scf_data', key='scf_issues')
    if not issues:
        logging.info("No issues to process.")
        return

    rows = [(issue['id'], json.dumps(issue), issue['updated_at']) for issue in issues]

    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = pg_hook.get_conn()
    cur = conn.cursor()

    insert_query = f"""
        INSERT INTO {TABLE_NAME} (id, obj, updated_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE 
        SET obj = EXCLUDED.obj, updated_at = EXCLUDED.updated_at;
    """
    
    logging.info(f"Inserting {len(rows)} issues into the database.")
    
    try:
        # Using executemany to insert multiple rows at once
        cur.executemany(insert_query, rows)
        conn.commit()
    except Exception as e:
        logging.error(f"Error inserting rows: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


# Define the DAG
with DAG(
    'pull_scf_data_dag',
    default_args={
        'owner': 'airflow',
        'retries': 0,
    },
    description='A DAG to pull and store SeeClickFix issues',
    schedule_interval='@hourly',  # This makes the DAG run every hour
    start_date=days_ago(1),
    catchup=False,
) as dag:

    # Task to pull data and store it in XCom
    pull_scf_data_task = PythonOperator(
        task_id='pull_scf_data',
        python_callable=pull_scf_data,
        provide_context=True,  # Enable the use of kwargs for XCom and other context variables
    )

    # Task to process and store issues in PostgreSQL
    process_and_store_issues_task = PythonOperator(
        task_id='process_and_store_issues',
        python_callable=process_and_store_issues,
        provide_context=True,  # Enable the use of kwargs for XCom and other context variables
    )

    # Set task dependencies
    pull_scf_data_task >> process_and_store_issues_task
