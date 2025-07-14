#!/bin/bash

# Wait for the database to be ready using built-in commands
echo "Waiting for database to be ready..."
until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping 3 seconds"
  sleep 3
done
echo "PostgreSQL is up - continuing"

# Initialize the database if requested
if [ "$RESET_MODE" = "true" ]; then
  echo "Initializing database..."
  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f /app/schema.sql
fi

# Run the ingestion process based on modes
echo "Starting Fitbit data ingestion..."

# Determine which arguments to pass to ingestions.py
ARGS=""

if [ "$TEST_MODE" = "true" ]; then
  ARGS="$ARGS --test-mode"
fi

if [ "$CATCH_UP_MODE" = "true" ]; then
  ARGS="$ARGS --catch-up"
fi

if [ "$RESET_MODE" = "true" ]; then
  ARGS="$ARGS --reset-all"
fi

# Run ingestion script with appropriate arguments
python /app/ingestions.py $ARGS

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