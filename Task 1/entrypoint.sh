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
    echo "Running in TEST MODE - will process daily data with 2 minute intervals"
    # Run ingestion in test mode
    python ingestions.py --test-mode
    
    # Keep container alive after finishing test mode
    echo "Test mode finished, keeping container alive..."
    tail -f /dev/null
    
elif [ "$CATCH_UP_MODE" = "true" ]; then
    echo "Running in CATCH-UP MODE - importing data up to 2024-01-30"
    # Run ingestion in catch-up mode
    python ingestions.py --catch-up
    
    # Keep container alive after finishing catch-up mode
    echo "Catch-up mode finished, keeping container alive..."
    tail -f /dev/null
    
elif [ "$RESET_MODE" = "true" ]; then
    echo "Running in RESET MODE - clearing all data"
    # Run ingestion in reset mode
    python ingestions.py --reset-all
    
    # Keep container alive after finishing reset mode
    echo "Reset mode finished, keeping container alive..."
    tail -f /dev/null
    
else
    echo "Running in PRODUCTION MODE - daily cron job"
    # Run initial ingestion
    echo "Running initial ingestion at $(date)"
    python ingestions.py
    
    # Start cron daemon in foreground
    echo "Starting cron daemon..."
    crontab /etc/cron.d/ingestion-cron
    cron -f
fi