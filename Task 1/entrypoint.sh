#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME; do
    echo "Database is not ready yet. Waiting..."
    sleep 2
done

echo "Database is ready!"

# Check if we're in test mode
if [ "$TEST_MODE" = "true" ]; then
    echo "Running in TEST MODE - ingestion every $TEST_INTERVAL seconds"
    # Run ingestion in a loop for testing
    while true; do
        echo "Running ingestion at $(date)"
        python ingestions.py
        echo "Sleeping for $TEST_INTERVAL seconds..."
        sleep $TEST_INTERVAL
    done
else
    echo "Running in PRODUCTION MODE - daily cron job"
    # Run initial ingestion
    echo "Running initial ingestion at $(date)"
    python ingestions.py
    
    # Start cron daemon
    echo "Starting cron daemon..."
    cron -f
fi