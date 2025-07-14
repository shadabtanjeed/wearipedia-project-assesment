import os
import logging
import argparse
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List, Optional

from source_adapter import SourceAdapterFactory
from models import HealthMetricFactory
from db_operations import DBOperations
from device_manager import DeviceManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Ingest")

# Environment variables for configuration with defaults
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "fitbit_data")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

DATA_DIR = os.environ.get("DATA_DIR", os.path.join("Data", "Modified Data"))
TIMESTAMP_FILE = os.environ.get("TIMESTAMP_FILE", "last_run_timestamp.txt")
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
TEST_INTERVAL = int(os.environ.get("TEST_INTERVAL", "300"))  # 5 minutes in seconds


def read_last_timestamp() -> Optional[datetime]:
    """
    Read the last processed timestamp from file.

    Returns:
        The last processed timestamp or None if file doesn't exist
    """
    try:
        if os.path.exists(TIMESTAMP_FILE):
            with open(TIMESTAMP_FILE, "r") as f:
                timestamp_str = f.read().strip()
                if timestamp_str:
                    return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        logger.error(f"Error reading timestamp file: {str(e)}")

    # Default to 7 days ago if no timestamp found
    return datetime.now() - timedelta(days=7)


def write_timestamp(timestamp: datetime):
    """
    Write the timestamp to file.

    Args:
        timestamp: The timestamp to write
    """
    try:
        with open(TIMESTAMP_FILE, "w") as f:
            f.write(timestamp.isoformat())
        logger.info(f"Updated timestamp file: {timestamp.isoformat()}")
    except Exception as e:
        logger.error(f"Error writing timestamp file: {str(e)}")


def process_metrics(
    adapter,
    metric_factory,
    db,
    metric_type: str,
    start_date: datetime,
    end_date: datetime,
    user_id: str = "1",
):
    """
    Process metrics for a specific type and date range.

    Args:
        adapter: Source adapter
        metric_factory: Health metric factory
        db: Database operations object
        metric_type: Type of metric to process
        start_date: Start date
        end_date: End date
        user_id: User ID to process
    """
    logger.info(
        f"Processing {metric_type} data for {start_date.date()} to {end_date.date()}"
    )

    # Get data from source adapter
    raw_data = adapter.get_data(
        metric_type=metric_type,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
    )

    if not raw_data:
        logger.info(f"No {metric_type} data found for the specified date range")
        return

    # Process each data point
    metrics_to_insert = []
    for data_point in raw_data:
        # Create metric using factory
        metric = metric_factory.create_metric(metric_type, data_point)

        # Ensure user and device exist in database
        db.ensure_user_exists(metric.user_id)

        if metric.device_id:
            device_type, model = metric.device_id.split("-")[:2]
            db.ensure_device_exists(
                device_id=metric.device_id,
                user_id=metric.user_id,
                device_type=device_type,
                model=model,
            )

        # Prepare for database insertion
        metrics_to_insert.append(
            {
                "metric_type": metric_type,
                "user_id": metric.user_id,
                "device_id": metric.device_id,
                "timestamp": metric.timestamp,
                "value": data_point,  # Store the full raw data as JSON
            }
        )

    # Insert metrics into database
    db.insert_metrics(metrics_to_insert)
    logger.info(f"Processed {len(metrics_to_insert)} {metric_type} data points")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Fitbit data ingestion script")
    parser.add_argument("--user-id", default="1", help="User ID to process")
    parser.add_argument(
        "--device-type", default="fitbit", help="Device type to process"
    )
    args = parser.parse_args()

    # Initialize components
    metric_factory = HealthMetricFactory(
        default_device_type=args.device_type, default_model="charge6"
    )

    adapter = SourceAdapterFactory.get_adapter(args.device_type, data_dir=DATA_DIR)

    db = DBOperations(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

    # Connect to database
    if not db.connect():
        logger.error("Failed to connect to database. Exiting.")
        return

    try:
        # Get list of supported metrics
        metric_types = adapter.get_supported_metrics()

        if TEST_MODE:
            logger.info("Running in TEST MODE with 5-minute intervals")

            while True:
                # Read the last processed date
                last_date = read_last_timestamp()
                next_date = last_date + timedelta(days=1)

                logger.info(f"Processing data for date: {next_date.date()}")

                # Process each metric type for the next day
                for metric_type in metric_types:
                    process_metrics(
                        adapter,
                        metric_factory,
                        db,
                        metric_type,
                        next_date,
                        next_date,
                        args.user_id,
                    )

                # Update the timestamp file with the processed date
                write_timestamp(next_date)

                # Sleep for the test interval
                logger.info(f"Sleeping for {TEST_INTERVAL} seconds")
                time.sleep(TEST_INTERVAL)

        else:
            # Production mode: Process all days since last run
            last_run = read_last_timestamp()
            today = datetime.now()

            logger.info(f"Processing data from {last_run.date()} to {today.date()}")

            # Process each metric type for the date range
            for metric_type in metric_types:
                process_metrics(
                    adapter,
                    metric_factory,
                    db,
                    metric_type,
                    last_run,
                    today,
                    args.user_id,
                )

            # Update the timestamp file
            write_timestamp(today)

    finally:
        # Close database connection
        db.close()


if __name__ == "__main__":
    main()
