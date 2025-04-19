#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define constants
RUN_DIR="./run"
PLUGINS_DIR="$RUN_DIR/plugins"
DAGS_DIR="$RUN_DIR/dags"
PYTHON_PROJECT_DIR="$RUN_DIR/python_project"

# Step 1: Create necessary directories
if [ ! -d "$RUN_DIR" ]; then
  echo "Creating run directory..."
  mkdir -p "$RUN_DIR"
fi

if [ ! -d "$PLUGINS_DIR" ]; then
  echo "Creating plugins directory in run..."
  mkdir -p "$PLUGINS_DIR"
fi

if [ ! -d "$DAGS_DIR" ]; then
  echo "Creating DAGs directory in run..."
  mkdir -p "$DAGS_DIR"
fi

if [ ! -d "$PYTHON_PROJECT_DIR" ]; then
  echo "Creating Python project directory in run..."
  mkdir -p "$PYTHON_PROJECT_DIR"
fi

# Step 3: Update Airflow configurations to use run directory
export AIRFLOW_HOME="$RUN_DIR/airflow"
export AIRFLOW__CORE__DAGS_FOLDER="$DAGS_DIR"
export AIRFLOW__CORE__PLUGINS_FOLDER="$PLUGINS_DIR"

# Step 4: Initialize Airflow database
echo "Initializing Airflow database..."
docker-compose run --rm airflow-webserver airflow db init

# Step 5: Create an Airflow user
echo "Creating an Airflow admin user..."
docker-compose run --rm airflow-webserver airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com

# Step 6: Start all containers
echo "Starting all containers..."
docker-compose up -d

# Step 7: Verify Airflow is running
echo "Waiting for Airflow webserver to start..."
sleep 10
curl -f http://localhost:8080 || { echo "Airflow webserver failed to start."; exit 1; }

# Step 8: Restart Airflow to load new DAGs
echo "Restarting Airflow to load new DAGs..."
docker-compose restart airflow-webserver airflow-scheduler

# Final message
echo "Setup complete. Airflow is now scheduling scrape_sentiments."