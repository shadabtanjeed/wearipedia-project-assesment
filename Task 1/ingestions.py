import os
import logging
import argparse
from datetime import datetime, timedelta
import time
import json
import subprocess
from typing import Dict, List, Optional

from source_adapter import SourceAdapterFactory
from models import HealthMetricFactory
from influx_operations import InfluxOperations

# Configure more detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG for more detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ingestion_debug.log"),  # Log to file
        logging.StreamHandler(),  # And to console
    ],
)
logger = logging.getLogger("Ingest")

# Environment variables with defaults for both Docker and local execution
INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN", "my-super-secret-token")
INFLUXDB_ORG = os.environ.get("INFLUXDB_ORG", "fitbit")
INFLUXDB_BUCKET = os.environ.get("INFLUXDB_BUCKET", "fitbit_metrics")

# New environment variables for execution mode
CONTINUOUS_MODE = os.environ.get("CONTINUOUS_MODE", "false").lower() == "true"
CONTINUOUS_INTERVAL = int(
    os.environ.get("CONTINUOUS_INTERVAL", "120")
)  # 2 minutes in seconds
DAILY_EXECUTION_HOUR = int(os.environ.get("DAILY_EXECUTION_HOUR", "13"))  # 1 PM

# Fix data directory resolution
if os.path.exists("/app/Data/Modified Data"):
    # Running in Docker
    DATA_DIR = "/app/Data/Modified Data"
elif os.path.exists("../Data/Modified Data"):
    # Running locally from Task 1 directory
    DATA_DIR = "../Data/Modified Data"
else:
    # Fallback to environment variable or default
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    DATA_DIR = os.environ.get(
        "DATA_DIR", os.path.join(project_root, "Data", "Modified Data")
    )

print(f"Using data directory: {DATA_DIR}")

TIMESTAMP_FILE = os.environ.get("TIMESTAMP_FILE", "last_run_timestamp.txt")
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
TEST_INTERVAL = int(
    os.environ.get("TEST_INTERVAL", "120")
)  # Changed to 2 minutes in seconds


# Add debugging function
def debug_data(msg, data, truncate=True):
    """Log data for debugging purposes with option to truncate for readability"""
    if isinstance(data, list) and truncate and len(data) > 3:
        data_str = json.dumps(data[:3]) + f"... ({len(data)} items total)"
    elif isinstance(data, dict) and truncate and len(data) > 10:
        data_str = (
            json.dumps({k: data[k] for k in list(data.keys())[:10]})
            + f"... ({len(data)} keys total)"
        )
    else:
        data_str = json.dumps(data)
    logger.debug(f"{msg}: {data_str}")


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

    # Also check InfluxDB
    db = InfluxOperations(INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET)
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
                # Default to start of synthetic data range - FIXED DATE
                default_start = datetime(2024, 1, 1, tzinfo=None)
                logger.info(
                    f"No existing timestamp found, using default: {default_start}"
                )
                return default_start
    except Exception as e:
        logger.error(f"Error reading timestamp from database: {e}")
        # Also return 2024-01-01 as fallback
        return file_timestamp or datetime(2024, 1, 1, tzinfo=None)
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
    db = InfluxOperations(INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET)
    try:
        if db.connect():
            db.update_last_processed_date(metric_type, int(user_id), timestamp)
    except Exception as e:
        logger.error(f"Error writing timestamp to database: {e}")
    finally:
        db.close()


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
    logger.info(
        f"Processing {metric_type} metrics from {start_date} to {end_date} for user {user_id}"
    )

    # Get raw data from adapter
    raw_data = adapter.get_data(metric_type, start_date, end_date, user_id)

    # Debug raw data
    debug_data(f"Raw {metric_type} data for user {user_id}", raw_data)

    if not raw_data:
        logger.warning(
            f"No {metric_type} data found for the specified date range for user {user_id}"
        )
        return

    # Sort raw data by timestamp to ensure correct ordering
    def get_timestamp(data_point):
        if isinstance(data_point, dict) and "dateTime" in data_point:
            dt_str = data_point["dateTime"]
            # Add time component if missing to ensure consistent datetime parsing
            if "T" not in dt_str and len(dt_str) <= 10:
                dt_str += "T00:00:00"
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        elif isinstance(data_point, dict) and "timestamp" in data_point:
            return data_point["timestamp"]
        logger.warning(f"Cannot determine timestamp for data point: {data_point}")
        return datetime.now()

    sorted_raw_data = sorted(raw_data, key=get_timestamp)
    logger.debug(f"Sorted {len(sorted_raw_data)} data points")

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
    logger.debug(f"Mapped {metric_type} to factory type {factory_metric_type}")

    for idx, data_point in enumerate(sorted_raw_data):
        try:
            # Debug every 10th item to avoid log flooding
            if idx % 10 == 0:
                debug_data(f"Processing data point {idx}", data_point)

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
                        "value": getattr(metric, "value", 0),
                        "resting_heart_rate": getattr(
                            metric, "resting_heart_rate", None
                        ),
                        "zones": getattr(metric, "zones", None),
                        "summary": getattr(metric, "summary", None),
                        "intraday": getattr(metric, "intraday", None),
                    }
                )
            elif factory_metric_type == "spo2":
                metric_data.update(
                    {
                        "value": getattr(metric, "value", 0),
                        "minute_data": getattr(metric, "minute_data", None),
                    }
                )
            elif factory_metric_type == "hrv":
                metric_data.update(
                    {
                        "rmssd": getattr(metric, "rmssd", None),
                        "coverage": getattr(metric, "coverage", None),
                        "hf": getattr(metric, "hf", None),
                        "lf": getattr(metric, "lf", None),
                        "minute_data": getattr(metric, "minute_data", None),
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
                        "minute_data": getattr(metric, "minute_data", None),
                    }
                )
            elif factory_metric_type == "activity":
                metric_data.update({"value": getattr(metric, "value", 0)})

            metrics_to_insert.append(metric_data)

            # Debug every 50th processed item
            if idx % 50 == 0 and idx > 0:
                logger.debug(f"Processed {idx} items for {metric_type}")

        except Exception as e:
            logger.error(
                f"Error processing {factory_metric_type} data point at index {idx}: {e}"
            )
            logger.error(f"Problematic data point: {json.dumps(data_point)}")
            import traceback

            logger.error(traceback.format_exc())
            continue

    # Insert metrics into appropriate measurement using factory metric type
    if metrics_to_insert:
        logger.info(
            f"Attempting to insert {len(metrics_to_insert)} {factory_metric_type} metrics"
        )
        try:
            db.insert_metrics(factory_metric_type, metrics_to_insert)
            logger.info(
                f"Successfully processed {len(metrics_to_insert)} {factory_metric_type} data points for user {user_id}"
            )
        except Exception as e:
            logger.error(f"Failed to insert {factory_metric_type} metrics: {e}")
            import traceback

            logger.error(traceback.format_exc())
    else:
        logger.warning(
            f"No valid {factory_metric_type} data points to insert for user {user_id}"
        )


def monitor_influxdb():
    """Print monitoring information for the InfluxDB database"""
    logger.info("Monitoring InfluxDB database...")

    db = InfluxOperations(INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET)

    try:
        if db.connect():
            # Get bucket stats
            query = f"""
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -30d)
                |> count()
                |> group(columns: ["_measurement"])
                |> sum()
            """

            query_api = db.client.query_api()
            tables = query_api.query(query, org=INFLUXDB_ORG)

            logger.info("InfluxDB Database Stats:")

            metrics_count = {}
            for table in tables:
                for record in table.records:
                    measurement = record.get_measurement()
                    count = record.get_value()
                    metrics_count[measurement] = count

            for metric, count in metrics_count.items():
                logger.info(f"  - {metric}: {count} data points")

            # Get total storage info
            logger.info(f"Bucket: {INFLUXDB_BUCKET}")
            logger.info(f"Organization: {INFLUXDB_ORG}")

            return metrics_count
    except Exception as e:
        logger.error(f"Error monitoring InfluxDB: {e}")
    finally:
        db.close()

    return None


def process_date_range(
    adapter, metric_factory, db, metric_type, start_date, end_date, user_id
):
    """Process metrics for a date range, one day at a time"""
    current_date = start_date

    while current_date <= end_date:
        logger.info(f"Processing date: {current_date.date()}")
        process_metrics(
            adapter,
            metric_factory,
            db,
            metric_type,
            current_date,
            current_date,
            user_id,
        )

        # Move to next day
        current_date += timedelta(days=1)

        # Update timestamp to indicate we've processed this day
        write_timestamp(metric_type, current_date, user_id)


def main():
    print(f"Current working directory: {os.getcwd()}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Data directory exists: {os.path.exists(DATA_DIR)}")

    if os.path.exists(DATA_DIR):
        print(f"Contents of data directory: {os.listdir(DATA_DIR)}")
    else:
        print("Data directory does not exist!")
        # Try to find where the data actually is
        for root, dirs, files in os.walk("/app"):
            if "Data" in dirs:
                print(f"Found Data directory at: {os.path.join(root, 'Data')}")
                break

    parser = argparse.ArgumentParser(description="Ingest health metrics data")
    parser.add_argument(
        "--user-id", default="all", help="User ID to process ('all' for all users)"
    )
    parser.add_argument("--metric-type", help="Specific metric type to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--reset-timestamps", action="store_true", help="Reset all timestamp files"
    )
    parser.add_argument(
        "--single-day", action="store_true", help="Process only one day of data"
    )
    parser.add_argument(
        "--check-files", action="store_true", help="Check and fix file mappings"
    )
    parser.add_argument(
        "--continuous", action="store_true", help="Run continuously every 2 minutes"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process full batch from Jan 1 to Jan 31, 2024",
    )
    parser.add_argument("--monitor", action="store_true", help="Monitor InfluxDB stats")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # If only monitoring was requested, do that and exit
    if args.monitor:
        stats = monitor_influxdb()
        return

    # Check and fix file mappings if requested
    if args.check_files:
        try:
            from fix_source_adapter import fix_adapter_mapping

            fix_adapter_mapping()
            logger.info("Fixed file mappings")
        except Exception as e:
            logger.error(f"Failed to fix file mappings: {e}")

    # Initialize components
    adapter = SourceAdapterFactory.create_adapter("synthetic", data_dir=DATA_DIR)
    metric_factory = HealthMetricFactory()

    # Use InfluxDB operations instead of PostgreSQL
    db = InfluxOperations(INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET)

    # Connect to database
    if not db.connect():
        logger.error("Failed to connect to InfluxDB. Exiting.")
        return

    # Reset timestamps if requested
    if args.reset_timestamps:
        logger.info("Resetting all timestamp files")
        import glob

        for timestamp_file in glob.glob("last_timestamp_*"):
            try:
                os.remove(timestamp_file)
                logger.info(f"Removed timestamp file: {timestamp_file}")
            except Exception as e:
                logger.error(f"Failed to remove timestamp file {timestamp_file}: {e}")

        # Also reset database timestamps
        try:
            from fix_source_adapter import reset_timestamps

            reset_timestamps()
            logger.info("Reset database timestamps")
        except Exception as e:
            logger.error(f"Failed to reset database timestamps: {e}")

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
        if args.metric_type in metric_types:
            metric_types = [args.metric_type]
        else:
            logger.warning(
                f"Unknown metric type: {args.metric_type}. Valid types: {', '.join(metric_types)}"
            )
            return

    # Determine users to process
    user_ids = ["1", "2"]  # Default to both users
    if args.user_id != "all":
        if args.user_id in user_ids:
            user_ids = [args.user_id]
        else:
            logger.warning(
                f"Unknown user ID: {args.user_id}. Valid IDs: {', '.join(user_ids)}"
            )
            return

    logger.info(f"Processing data for users: {user_ids}")
    logger.info(f"Processing metric types: {metric_types}")

    # Use continuous mode from args or environment variable
    continuous_mode = args.continuous or CONTINUOUS_MODE

    try:
        available_data = {}
        for user_id in user_ids:
            available_data[user_id] = []
            for metric_type in metric_types:
                if adapter.check_data_availability(metric_type, user_id):
                    available_data[user_id].append(metric_type)
                else:
                    logger.warning(
                        f"No data file available for user {user_id}, metric type {metric_type}"
                    )

        logger.info(f"Processing data for users with available data: {available_data}")

        # Batch processing mode - process all data from Jan 1 to Jan 31, 2024
        if args.batch:
            batch_start_date = datetime(2024, 1, 1)
            batch_end_date = datetime(2024, 1, 31)

            logger.info(
                f"Batch processing from {batch_start_date.date()} to {batch_end_date.date()}"
            )

            for user_id in user_ids:
                if not available_data[user_id]:
                    logger.info(f"Skipping User {user_id} - no data files available")
                    continue

                logger.info(f"==== Processing data for User {user_id} ====")

                for metric_type in available_data[user_id]:
                    logger.info(
                        f"-- Batch processing {metric_type} for User {user_id} --"
                    )

                    # Process all dates in the range
                    process_date_range(
                        adapter,
                        metric_factory,
                        db,
                        metric_type,
                        batch_start_date,
                        batch_end_date,
                        user_id,
                    )

            logger.info("Batch processing complete")
            return

        # Single execution or continuous loop
        while True:
            run_time = datetime.now()
            logger.info(f"Starting data processing at {run_time}")

            # Process each user and metric type
            for user_id in user_ids:
                if not available_data[user_id]:
                    logger.info(f"Skipping User {user_id} - no data files available")
                    continue

                logger.info(f"==== Processing data for User {user_id} ====")

                for metric_type in available_data[user_id]:
                    logger.info(f"-- Processing {metric_type} for User {user_id} --")

                    last_run = read_last_timestamp(metric_type, user_id)

                    # Process only the day from last_run
                    target_date = last_run
                    logger.info(
                        f"Processing {metric_type} data for {target_date.date()} for user {user_id}"
                    )

                    # Process single day
                    process_metrics(
                        adapter,
                        metric_factory,
                        db,
                        metric_type,
                        target_date,
                        target_date,
                        user_id,
                    )

                    # Update timestamp to next day
                    next_day = target_date + timedelta(days=1)
                    write_timestamp(metric_type, next_day, user_id)
                    logger.info(f"Updated timestamp to {next_day.date()} for next run")

                    logger.info(
                        f"Completed processing {metric_type} data for user {user_id}"
                    )

            # After processing all metrics and users
            logger.info("All processing complete for this run")

            # Show database stats after processing
            monitor_influxdb()

            # Exit if not in continuous mode
            if not continuous_mode:
                break

            # Sleep for the interval before running again
            logger.info(f"Waiting {CONTINUOUS_INTERVAL} seconds before next run...")
            time.sleep(CONTINUOUS_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
