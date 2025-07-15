import os
import logging
import argparse
import sys
from datetime import datetime, timedelta, timezone
import time
import json
from typing import Dict, List, Optional

from source_adapter import SourceAdapterFactory
from models import HealthMetricFactory
from db_operations import DBOperations

import psycopg2

# Configure more detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ingestion_debug.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("Ingest")

# Environment variables with defaults for both Docker and local execution
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "fitbit_data")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

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
TEST_INTERVAL = int(os.environ.get("TEST_INTERVAL", "300"))  # 5 minutes in seconds


def initialize_database(db_conn):
    """Initialize database schema if tables don't exist"""
    logger.info("Checking and initializing database schema if needed")

    # Path to schema.sql - adjust if needed
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found at {schema_path}")
        return False

    try:
        # Read the schema SQL
        with open(schema_path, "r") as f:
            schema_sql = f.read()

        # Execute the SQL script
        with db_conn.conn.cursor() as cursor:
            cursor.execute(schema_sql)
        db_conn.conn.commit()
        logger.info("Successfully initialized database schema")
        return True
    except Exception as e:
        logger.error(f"Error initializing database schema: {e}")
        import traceback

        logger.error(traceback.format_exc())
        db_conn.conn.rollback()
        return False

def refresh_aggregates_for_metric(db, metric_type, start_date, end_date, levels=None):
    """Refresh aggregates with special handling for continuous aggregates"""
    if not db or not hasattr(db, 'conn'):
        logger.error("Invalid DB connection")
        raise ValueError("Valid DB connection required")

    start_dt = convert_to_utc(start_date)
    end_dt = convert_to_utc(end_date)
    
    metric_levels = {
        "heart_rate": ["1m", "1h", "1d", "1w", "1mo"],
        # ... other metrics ...
    }
    levels = levels or metric_levels.get(metric_type, [])

    try:
        # Handle continuous aggregate separately (needs autocommit)
        if "1m" in levels and metric_type == "heart_rate":
            logger.debug("Refreshing continuous aggregate (special handling)")
            with db.conn.cursor() as cursor:
                # Ensure autocommit is enabled for this operation
                db.conn.autocommit = True
                cursor.execute(
                    "CALL refresh_continuous_aggregate('heart_rate_1m', %s, %s)",
                    (start_dt, end_dt)
                )
                logger.info("Successfully refreshed heart_rate_1m")
                db.conn.autocommit = False  # Reset to original state

        # Handle materialized views in a transaction
        other_levels = [l for l in levels if l != "1m"]
        if other_levels:
            with db.conn.cursor() as cursor:
                for level in other_levels:
                    logger.debug(f"Refreshing materialized view heart_rate_{level}")
                    cursor.execute(f"REFRESH MATERIALIZED VIEW heart_rate_{level}")
                db.conn.commit()
                logger.info(f"Refreshed materialized views: {other_levels}")

    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        db.conn.rollback()
        raise

# Add UTC conversion utilities
def convert_to_utc(timestamp_input) -> datetime:
    """Convert timestamp to UTC datetime (timezone-naive for database storage)"""
    try:
        # Handle different input types
        if isinstance(timestamp_input, str):
            # Parse string timestamp
            if "T" in timestamp_input:
                # ISO format: "2024-01-01T00:00:00" or "2024-01-01T00:00:00.000"
                if "." in timestamp_input:
                    dt = datetime.fromisoformat(timestamp_input.replace(".000", ""))
                else:
                    dt = datetime.fromisoformat(timestamp_input)
            else:
                # Date only format: "2024-01-01"
                dt = datetime.strptime(timestamp_input, "%Y-%m-%d")
        elif isinstance(timestamp_input, datetime):
            dt = timestamp_input
        else:
            logger.error(f"Unsupported timestamp type: {type(timestamp_input)}")
            return None

        # If timezone-naive, assume it's UTC (since synthetic data is UTC)
        if dt.tzinfo is None:
            # Return as timezone-naive UTC for database storage
            return dt

        # Convert to UTC and remove timezone info for storage
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception as e:
        logger.error(f"Error converting timestamp {timestamp_input} to UTC: {e}")
        return None


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
                    # Convert to UTC timezone-naive datetime
                    file_timestamp = convert_to_utc(timestamp_str)
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
                # Ensure it's timezone-naive UTC
                if db_timestamp.tzinfo is not None:
                    db_timestamp = db_timestamp.astimezone(timezone.utc).replace(
                        tzinfo=None
                    )

            # Use the later timestamp if both exist
            if file_timestamp and db_timestamp:
                return max(file_timestamp, db_timestamp)
            elif file_timestamp:
                return file_timestamp
            elif db_timestamp:
                return db_timestamp
            else:
                # Default to start of synthetic data range as UTC
                default_start = datetime(2024, 1, 1)  # Already timezone-naive UTC
                logger.info(
                    f"No existing timestamp found, using default: {default_start}"
                )
                return default_start
    except Exception as e:
        logger.error(f"Error reading timestamp from database: {e}")
        return file_timestamp or datetime(2024, 1, 1)
    finally:
        db.close()


def write_timestamp(metric_type: str, timestamp: datetime, user_id: str = "1"):
    """Write the last processed timestamp for a specific metric type to file and database."""
    # Convert to UTC timezone-naive for consistent storage
    utc_timestamp = convert_to_utc(timestamp)

    if utc_timestamp is None:
        logger.error(f"Failed to convert timestamp {timestamp} to UTC")
        return

    # Write to file
    timestamp_file = f"last_timestamp_{metric_type}_user_{user_id}.txt"
    try:
        with open(timestamp_file, "w") as f:
            f.write(utc_timestamp.isoformat())
        logger.info(f"Wrote UTC timestamp to file {timestamp_file}: {utc_timestamp}")
    except Exception as e:
        logger.error(f"Error writing timestamp to file: {e}")

    # Write to database
    db = DBOperations(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
    try:
        if db.connect():
            db.update_last_processed_date(metric_type, int(user_id), utc_timestamp)
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
    """Process metrics for a specific type and date range, using flat records."""
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

    # Process data and create flattened records
    total_records = 0
    device_id = f"fitbit-device-{user_id}"

    # Ensure user and device exist in database
    db.ensure_users_and_devices(int(user_id), device_id)

    # Map metric types to internal factory types
    metric_type_mapping = {
        "heart_rate": "heart_rate",
        "spo2": "spo2",
        "hrv": "hrv",
        "breathing_rate": "breathing_rate",
        "active_zone_minutes": "active_zone_minutes",
        "activity": "activity",
    }

    factory_metric_type = metric_type_mapping.get(metric_type, metric_type)

    try:
        # Process each data point based on metric type
        if metric_type == "heart_rate":
            # Heart rate data has a different structure
            for item in raw_data:
                heart_day = item.get("heart_rate_day", [])
                for day_data in heart_day:
                    try:
                        metric = metric_factory.create_metric(
                            factory_metric_type, int(user_id), device_id
                        )
                        metric.set_data(day_data)

                        # Get flattened records for this day
                        flat_records = metric.get_flat_records()
                        if flat_records:
                            inserted = db.insert_records(flat_records)
                            total_records += inserted
                            logger.debug(
                                f"Inserted {inserted} flattened records for heart rate"
                            )
                    except Exception as e:
                        logger.error(f"Error processing heart rate data: {e}")
                        import traceback

                        logger.error(traceback.format_exc())

        elif metric_type == "active_zone_minutes":
            # AZM data has a different structure
            for item in raw_data:
                azm_list = item.get("activities-active-zone-minutes-intraday", [])
                for azm_data in azm_list:
                    try:
                        metric = metric_factory.create_metric(
                            factory_metric_type, int(user_id), device_id
                        )
                        metric.set_data(azm_data)

                        # Get flattened records
                        flat_records = metric.get_flat_records()
                        if flat_records:
                            inserted = db.insert_records(flat_records)
                            total_records += inserted
                            logger.debug(
                                f"Inserted {inserted} flattened records for AZM"
                            )
                    except Exception as e:
                        logger.error(f"Error processing AZM data: {e}")
                        import traceback

                        logger.error(traceback.format_exc())

        elif metric_type == "breathing_rate":
            # Breathing rate data structure
            for item in raw_data:
                br_list = item.get("br", [])
                for br_data in br_list:
                    try:
                        metric = metric_factory.create_metric(
                            factory_metric_type, int(user_id), device_id
                        )
                        metric.set_data(br_data)

                        # Get flattened records
                        flat_records = metric.get_flat_records()
                        if flat_records:
                            inserted = db.insert_records(flat_records)
                            total_records += inserted
                            logger.debug(
                                f"Inserted {inserted} flattened records for breathing rate"
                            )
                    except Exception as e:
                        logger.error(f"Error processing breathing rate data: {e}")
                        import traceback

                        logger.error(traceback.format_exc())

        elif metric_type == "hrv":
            # HRV data structure
            for item in raw_data:
                hrv_list = item.get("hrv", [])
                for hrv_data in hrv_list:
                    try:
                        metric = metric_factory.create_metric(
                            factory_metric_type, int(user_id), device_id
                        )
                        metric.set_data(hrv_data)

                        # Get flattened records
                        flat_records = metric.get_flat_records()
                        if flat_records:
                            inserted = db.insert_records(flat_records)
                            total_records += inserted
                            logger.debug(
                                f"Inserted {inserted} flattened records for HRV"
                            )
                    except Exception as e:
                        logger.error(f"Error processing HRV data: {e}")
                        import traceback

                        logger.error(traceback.format_exc())

        elif metric_type in ["spo2", "activity"]:
            # SpO2 and Activity have similar structure
            for item in raw_data:
                try:
                    metric = metric_factory.create_metric(
                        factory_metric_type, int(user_id), device_id
                    )
                    metric.set_data(item)

                    # Get flattened records
                    flat_records = metric.get_flat_records()
                    if flat_records:
                        inserted = db.insert_records(flat_records)
                        total_records += inserted
                        logger.debug(
                            f"Inserted {inserted} flattened records for {metric_type}"
                        )
                except Exception as e:
                    logger.error(f"Error processing {metric_type} data: {e}")
                    import traceback

                    logger.error(traceback.format_exc())

        logger.info(
            f"Successfully processed {total_records} flattened records for {metric_type}"
        )
        refresh_aggregates_for_metric(db, metric_type, start_date, end_date)

    except Exception as e:
        logger.error(f"Error during {metric_type} processing: {e}")
        import traceback

        logger.error(traceback.format_exc())


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

    # Add new arguments for docker operation modes
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode, fetching data every 2 minutes",
    )
    parser.add_argument(
        "--catch-up",
        action="store_true",
        help="Import all data from last timestamp to 2024-01-30",
    )
    parser.add_argument(
        "--reset-all",
        action="store_true",
        help="Clear all stored data and start fresh from 2024-01-01",
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

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
    db = DBOperations(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)

    # Connect to database
    if not db.connect():
        logger.error("Failed to connect to database. Exiting.")
        return

    # Initialize database schema if needed
    if not initialize_database(db):
        logger.warning("Database schema initialization had issues, but continuing...")

    # Handle reset-all mode - this should run first if specified
    if args.reset_all:
        logger.info("Resetting all data to start from 2024-01-01")

        # Reset timestamps
        import glob

        for timestamp_file in glob.glob("last_timestamp_*"):
            try:
                os.remove(timestamp_file)
                logger.info(f"Removed timestamp file: {timestamp_file}")
            except Exception as e:
                logger.error(f"Failed to remove timestamp file {timestamp_file}: {e}")

        # Reset database timestamps and clear tables
        try:
            # First reset timestamps
            from fix_source_adapter import reset_db_timestamps

            reset_db_timestamps()

            # Then truncate data tables
            with db.conn.cursor() as cursor:
                tables = [
                    "HEART_RATE",
                    "HEART_RATE_ZONES",
                    "SPO2",
                    "HRV",
                    "BREATHING_RATE",
                    "ACTIVE_ZONE_MINUTES",
                    "ACTIVITY",
                ]
                for table in tables:
                    cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
                db.conn.commit()
                logger.info("Successfully cleared all data tables")
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            db.conn.rollback()

        # After reset, continue with normal processing or exit
        if not args.test_mode and not args.catch_up:
            logger.info("Reset complete. Exiting.")
            return

    # Reset timestamps if requested (and not already done by reset-all)
    elif args.reset_timestamps:
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
            from fix_source_adapter import reset_db_timestamps

            reset_db_timestamps()
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

    # Check data availability for users and metrics
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

    try:
        # Handle test mode - process one day at a time with 2 minute intervals
        if args.test_mode:
            logger.info("Running in test mode - fetching data every 2 minutes")

            # Start from January 1, 2024
            current_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 30)  # Process up to January 30

            while current_date <= end_date:
                logger.info(
                    f"-- Test run for date: {current_date.strftime('%Y-%m-%d')} --"
                )

                for user_id in user_ids:
                    if not available_data[user_id]:
                        continue

                    for metric_type in available_data[user_id]:
                        logger.info(
                            f"Processing {metric_type} for User {user_id} on {current_date.date()}"
                        )

                        # Process metrics for the current date
                        process_metrics(
                            adapter,
                            metric_factory,
                            db,
                            metric_type,
                            current_date,
                            current_date,
                            user_id,
                        )

                        # Update timestamp for next run
                        next_day = current_date + timedelta(days=1)
                        write_timestamp(metric_type, next_day, user_id)

                # Move to the next day
                current_date += timedelta(days=1)

                if current_date <= end_date:
                    logger.info(
                        f"Test run complete. Sleeping for 10 seconds before processing {current_date.date()}..."
                    )
                    time.sleep(10)  # Sleep for 10 seconds
                else:
                    logger.info("Test mode complete - reached end date")

            # Exit after test mode completes - no need to continue to regular processing
            logger.info("Test mode finished, exiting...")
            return

        # Handle catch-up mode - process all data up to Jan 30, 2024
        elif args.catch_up:
            logger.info("Running in catch-up mode - importing data up to 2024-01-30")
            end_date = datetime(2024, 1, 30)

            for user_id in user_ids:
                if not available_data[user_id]:
                    continue

                logger.info(f"==== Catching up data for User {user_id} ====")

                for metric_type in available_data[user_id]:
                    # Get the last processed date
                    start_date = read_last_timestamp(metric_type, user_id)

                    # If the start date is already past the end date, skip
                    if start_date >= end_date:
                        logger.info(
                            f"Skipping {metric_type} for user {user_id} - already up to date"
                        )
                        continue

                    logger.info(
                        f"Catching up {metric_type} for user {user_id} from {start_date} to {end_date}"
                    )

                    # Process data for the entire range
                    process_metrics(
                        adapter,
                        metric_factory,
                        db,
                        metric_type,
                        start_date,
                        end_date,
                        user_id,
                    )

                    # Update timestamp to the day after end_date
                    next_day = end_date + timedelta(days=1)
                    write_timestamp(metric_type, next_day, user_id)
                    logger.info(f"Updated timestamp to {next_day.date()} for next run")
                    logger.info(
                        f"Completed catching up {metric_type} data for user {user_id}"
                    )

            logger.info("Catch-up mode complete.")
            # Exit after catch-up mode completes - no need to continue to regular processing
            logger.info("Catch-up mode finished, exiting...")
            return

        # Normal processing mode - process one day at a time
        else:
            # Process each user and metric type
            for user_id in user_ids:
                if not available_data[user_id]:
                    logger.info(f"Skipping User {user_id} - no data files available")
                    continue

                logger.info(f"==== Processing data for User {user_id} ====")

                for metric_type in available_data[user_id]:
                    logger.info(f"-- Processing {metric_type} for User {user_id} --")

                    last_run = read_last_timestamp(metric_type, user_id)

                    # Process only the next day from last_run
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
