# Docker Airflow Setup README

This repo runs a docker container with airflow and postgres to pull data from the seeclickfix api and store issues in a postgres database.

## Prerequisites

Make sure you have the following tools installed:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Setup

### Clone the Repository

```bash
git clone https://github.com/jseek/seeclickfix_etl.git
cd your-repo-directory
```

### Configuration

Before running the services, you can configure them according to your needs by modifying the following files:

- **`init.sql`**: This script is executed when the PostgreSQL container starts, and can be used to initialize the database schema.
- **`pgadmin/init_pgadmin.sh`**: This script is executed when the pgAdmin container starts, and can be used to configure pgAdmin settings and connections.
- **`dags/`**: Place your Airflow DAGs in this directory to have them automatically loaded when the Airflow webserver and scheduler start.

## Running the Setup

### 1. Start the Services

To bring up all the services defined in the `docker-compose.yml` file, run the following command:

```bash
docker-compose up -d
```

This will start the following services:

- **postgres**: PostgreSQL 13 database for Airflow's metadata.
- **airflow-webserver**: Airflow web server (accessible via port 8082).
- **airflow-scheduler**: Airflow scheduler for executing DAGs.
- **airflow-init**: Initializes the Airflow database and creates an admin user.
- **trigger_dag**: Triggers an Airflow DAG after initialization (can be customized).
- **pgadmin**: Web interface for managing the PostgreSQL database (accessible via port 5050).

### 2. Access the Services

- **Airflow Web UI**: Go to `http://localhost:8082` to access the Airflow web UI. Log in with the username `admin` and the password you specified in the `airflow-init` container's command.
- **pgAdmin**: Go to `http://localhost:5050` to access pgAdmin. Log in using the email `admin@pgadmin.org` and the password `admin`.

### 3. Initializing the Airflow Database

The `airflow-init` service automatically runs the necessary commands to initialize the Airflow metadata database and create an admin user. If you need to reinitialize the database, you can stop and remove all containers, then restart:

```bash
docker-compose down
docker-compose up -d airflow-init
```

This will recreate the database and the user.

### 4. Running and Triggering DAGs

Once the containers are running, you can trigger DAGs manually or through the Airflow Web UI.

If you want to trigger a specific DAG automatically, the `trigger_dag` container can be configured to do so by editing the `entrypoint` and specifying the desired DAG name.

## Volumes

- **`postgres_data`**: Persists PostgreSQL data.
- **`pgadmin_data`**: Persists pgAdmin configuration and settings.
- **`./dags`**: Mount your custom DAGs here.
- **`./logs`**: Mount logs for Airflow.

## Stopping the Services

To stop the services, run:

```bash
docker-compose down
```

This will stop all services but keep the data volumes intact.

## Notes

- **Airflow Web UI**: If you have enabled RBAC, ensure that the admin user is created properly by checking the `airflow-init` logs or creating a new user via the Airflow Web UI.
- **PostgreSQL**: The database is preconfigured with a user named `airflow` and a database also named `airflow`. You can modify this setup in the `docker-compose.yml` file as needed.

## Customization

- Modify the PostgreSQL version or Airflow version by changing the respective image tags in the `docker-compose.yml` file.
- Add custom Airflow configurations by modifying the `airflow.cfg` file or passing environment variables in the Airflow containers.

## Troubleshooting

- If the Airflow webserver or scheduler fails to start, check the logs with:

  ```bash
  docker-compose logs airflow-webserver
  docker-compose logs airflow-scheduler
  ```

- If the `airflow-init` container hangs or fails, check for errors in the database connection and the Airflow initialization commands.
