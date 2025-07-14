#!/bin/bash
# filepath: /home/shadab/Desktop/Github Repos/wearipedia-project-assesment/Task 1/entrypoint.sh
set -e

echo "Starting ingestion service..."

# Create state directory for timestamps
mkdir -p /app/state

# Create symbolic links or copy files for proper mapping
python3 /app/fix_source_adapter.py

# Start cron service
service cron start

# If TEST_MODE is true, run the ingestion script every TEST_INTERVAL seconds
if [ "${TEST_MODE}" = "true" ]; then
    echo "Running in TEST_MODE, executing ingestion every ${TEST_INTERVAL} seconds"
    while true; do
        python3 /app/ingestions.py --single-day
        echo "Waiting ${TEST_INTERVAL} seconds before next run..."
        sleep ${TEST_INTERVAL}
    done
else
    echo "Running in normal mode, cron job will execute daily"
    # Keep container running
    tail -f /dev/null
fi