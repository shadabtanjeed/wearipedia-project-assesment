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


def read_last_timestamp(metric_type: str, user_id: str = "1") -> Optional[datetime]:
    """Read the last processed timestamp for a specific metric type from file and database."""
    # First check the text file
    timestamp_file = f"last_timestamp_{metric_type}_user_{user_id}.txt"
    file_timestamp = None

    if os.path.exists(timestamp_file):
        try:
            with open(timestamp_file, "r") as f:
                timestamp_str = f.read().strip()
                if timestamp_str:
                    file_timestamp = datetime.fromisoformat(timestamp_str)
                    logger.info(
                        f"Read timestamp from file {timestamp_file}: {file_timestamp}"
                    )
        except Exception as e:
            logger.error(f"Error reading timestamp from file: {e}")

    # Also check the database
    db = DBOperations(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
    try:
        if db.connect():
            db_timestamp = db.get_last_processed_date(metric_type, int(user_id))
            if db_timestamp:
                logger.info(
                    f"Read timestamp from database for {metric_type}: {db_timestamp}"
                )

            # Use the later timestamp if both exist
            if file_timestamp and db_timestamp:
                return max(file_timestamp, db_timestamp)
            elif file_timestamp:
                return file_timestamp
            elif db_timestamp:
                return db_timestamp
            else:
                # Default to a reasonable start date if no timestamp exists
                default_start = datetime(2024, 1, 1)
                logger.info(
                    f"No existing timestamp found, using default: {default_start}"
                )
                return default_start
    except Exception as e:
        logger.error(f"Error reading timestamp from database: {e}")
        return file_timestamp or (datetime.now() - timedelta(days=30))
    finally:
        db.close()


def write_timestamp(metric_type: str, timestamp: datetime, user_id: str = "1"):
    """Write the last processed timestamp for a specific metric type to file and database."""
    # Write to file
    timestamp_file = f"last_timestamp_{metric_type}_user_{user_id}.txt"
    try:
        with open(timestamp_file, "w") as f:
            f.write(timestamp.isoformat())
        logger.info(f"Wrote timestamp to file {timestamp_file}: {timestamp}")
    except Exception as e:
        logger.error(f"Error writing timestamp to file: {e}")

    # Write to database
    db = DBOperations(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
    try:
        if db.connect():
            db.update_last_processed_date(metric_type, int(user_id), timestamp)
    except Exception as e:
        logger.error(f"Error writing timestamp to database: {e}")
    finally:
        db.close()


# ...existing code...


# ...existing code...


def process_metrics(
    adapter,
    metric_factory,
    db,
    metric_type: str,
    start_date: datetime,
    end_date: datetime,
    user_id: str = "1",
):
    """Process metrics for a specific type and date range, ensuring data is ordered."""
    logger.info(f"Processing {metric_type} metrics from {start_date} to {end_date}")

    # Get raw data from adapter
    raw_data = adapter.get_data(metric_type, start_date, end_date, user_id)

    if not raw_data:
        logger.info(f"No {metric_type} data found for the specified date range")
        return

    # Sort raw data by timestamp to ensure correct ordering
    def get_timestamp(data_point):
        if isinstance(data_point, dict) and "dateTime" in data_point:
            return datetime.fromisoformat(data_point["dateTime"].replace("Z", "+00:00"))
        elif isinstance(data_point, dict) and "timestamp" in data_point:
            return data_point["timestamp"]
        return datetime.now()

    sorted_raw_data = sorted(raw_data, key=get_timestamp)

    metrics_to_insert = []

    # Map source adapter metric types to database/factory metric types
    metric_type_mapping = {
        "heart_rate": "hr",
        "spo2": "spo2",
        "hrv": "hrv",
        "breathing_rate": "br",
        "active_zone_minutes": "azm",
        "activity": "activity",
    }

    factory_metric_type = metric_type_mapping.get(metric_type, metric_type)

    for data_point in sorted_raw_data:
        try:
            # Create metric using factory with mapped type
            metric = metric_factory.create_metric(factory_metric_type, data_point)

            # Ensure user and device exist in database
            db.ensure_user_exists(metric.user_id)

            if metric.device_id:
                device_parts = metric.device_id.split("-")
                device_type = device_parts[0] if len(device_parts) > 0 else "unknown"
                model = device_parts[1] if len(device_parts) > 1 else "unknown"
                db.ensure_device_exists(
                    device_id=metric.device_id,
                    user_id=metric.user_id,
                    device_type=device_type,
                    model=model,
                )

            # Prepare metric data for insertion based on type
            metric_data = {
                "user_id": metric.user_id,
                "device_id": metric.device_id,
                "timestamp": metric.timestamp,
            }

            # Add metric-specific fields using factory metric type
            if factory_metric_type == "hr":
                metric_data.update(
                    {
                        "value": metric.value,
                        "resting_heart_rate": getattr(
                            metric, "resting_heart_rate", None
                        ),
                        "zones": getattr(metric, "zones", None),
                    }
                )
            elif factory_metric_type == "spo2":
                metric_data.update(
                    {
                        "value": metric.value,
                        "minute_data": getattr(metric, "data_points", None),
                    }
                )
            elif factory_metric_type == "hrv":
                metric_data.update(
                    {
                        "rmssd": getattr(metric, "rmssd", None),
                        "coverage": getattr(metric, "coverage", None),
                        "hf": getattr(metric, "hf", None),
                        "lf": getattr(metric, "lf", None),
                        "minute_data": getattr(metric, "data_points", None),
                    }
                )
            elif factory_metric_type == "br":
                metric_data.update(
                    {
                        "deep_sleep_rate": getattr(metric, "deep_sleep_rate", None),
                        "rem_sleep_rate": getattr(metric, "rem_sleep_rate", None),
                        "light_sleep_rate": getattr(metric, "light_sleep_rate", None),
                        "full_sleep_rate": getattr(metric, "full_sleep_rate", None),
                    }
                )
            elif factory_metric_type == "azm":
                metric_data.update(
                    {
                        "fat_burn_minutes": getattr(metric, "fat_burn_minutes", None),
                        "cardio_minutes": getattr(metric, "cardio_minutes", None),
                        "peak_minutes": getattr(metric, "peak_minutes", None),
                        "active_zone_minutes": getattr(
                            metric, "active_zone_minutes", None
                        ),
                        "minute_data": getattr(metric, "data_points", None),
                    }
                )
            elif factory_metric_type == "activity":
                metric_data.update({"value": metric.value})

            metrics_to_insert.append(metric_data)

        except Exception as e:
            logger.error(f"Error processing {factory_metric_type} data point: {e}")
            continue

    # Insert metrics into appropriate table using factory metric type
    if metrics_to_insert:
        db.insert_metrics(factory_metric_type, metrics_to_insert)
        logger.info(
            f"Processed {len(metrics_to_insert)} {factory_metric_type} data points"
        )
    else:
        logger.info(f"No valid {factory_metric_type} data points to insert")


# ...existing code...


def main():
    parser = argparse.ArgumentParser(description="Ingest health metrics data")
    parser.add_argument("--user-id", default="1", help="User ID to process")
    parser.add_argument("--metric-type", help="Specific metric type to process")
    args = parser.parse_args()

    # Initialize components
    adapter = SourceAdapterFactory.create_adapter("synthetic", data_dir=DATA_DIR)
    metric_factory = HealthMetricFactory()
    db = DBOperations(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)

    # Connect to database
    if not db.connect():
        logger.error("Failed to connect to database. Exiting.")
        return

    # Define metric types to process - updated to match source adapter expectations
    metric_types = [
        "heart_rate",
        "spo2",
        "hrv",
        "breathing_rate",
        "active_zone_minutes",
        "activity",
    ]
    if args.metric_type:
        metric_types = [args.metric_type]

    try:
        if TEST_MODE:
            logger.info("Running in TEST MODE - processing one day every 5 minutes")
            while True:
                for metric_type in metric_types:
                    last_date = read_last_timestamp(metric_type, args.user_id)
                    next_date = last_date + timedelta(days=1)

                    logger.info(
                        f"Processing {metric_type} data for date: {next_date.date()}"
                    )

                    # Process the metric for the next day
                    process_metrics(
                        adapter,
                        metric_factory,
                        db,
                        metric_type,
                        next_date,
                        next_date,
                        args.user_id,
                    )

                    # Update the timestamp
                    write_timestamp(metric_type, next_date, args.user_id)

                # Sleep for the test interval
                logger.info(f"Sleeping for {TEST_INTERVAL} seconds")
                time.sleep(TEST_INTERVAL)
        else:
            # Production mode: Process all days since last run for each metric
            for metric_type in metric_types:
                last_run = read_last_timestamp(metric_type, args.user_id)
                today = datetime.now()

                logger.info(
                    f"Processing {metric_type} data from {last_run.date()} to {today.date()}"
                )

                # Process each day individually to maintain order
                current_date = last_run
                while current_date <= today:
                    process_metrics(
                        adapter,
                        metric_factory,
                        db,
                        metric_type,
                        current_date,
                        current_date,
                        args.user_id,
                    )

                    # Update timestamp after each day
                    write_timestamp(metric_type, current_date, args.user_id)
                    current_date += timedelta(days=1)

                logger.info(f"Completed processing {metric_type} data")

    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


# ...existing code...

if __name__ == "__main__":
    main()
