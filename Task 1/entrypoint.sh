#!/bin/bash

# Wait for the database to be ready
echo "Waiting for database to be ready..."
/app/wait-for-it.sh $DB_HOST:$DB_PORT -t 60

# Initialize the database if requested
if [ "$RESET_MODE" = "true" ]; then
  echo "Initializing database..."
  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f /app/schema.sql
fi

# Run the ingestion process
echo "Starting Fitbit data ingestion..."
python /app/main.py

# Start the cron service if enabled
if [ "$ENABLE_CRON" = "true" ]; then
  echo "Starting cron service..."
  crontab /app/crontab
  cron -f
else
  # Keep the container running
  echo "Cron disabled. Container will exit now."
  tail -f /dev/null
fi