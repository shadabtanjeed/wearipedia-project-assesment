#!/usr/bin/env python3

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
import time
from typing import Dict, List

# Import the necessary components
from source_adapter import SourceAdapterFactory
from models import HealthMetricFactory
from db_operations import DBOperations

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("DBImportTest")

# Database configuration - modify as needed
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "fitbit_data",
    "user": "postgres",
    "password": "password",
}

# Data directory - adjust based on your setup
DATA_DIR = "../Data/Modified Data"
if not os.path.exists(DATA_DIR):
    DATA_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "Data", "Modified Data"
    )
    if not os.path.exists(DATA_DIR):
        raise ValueError(f"Data directory not found: {DATA_DIR}")

logger.info(f"Using data directory: {DATA_DIR}")


def initialize_db():
    """Initialize database connection"""
    db = DBOperations(**DB_CONFIG)
    if not db.connect():
        logger.error("Failed to connect to database")
        sys.exit(1)
    return db


def process_data(
    db, metric_type, user_id, start_date, end_date, adapter, metric_factory
):
    """Process and insert data for a specific metric and date range"""
    logger.info(
        f"Processing {metric_type} data for user {user_id} from {start_date.date()} to {end_date.date()}"
    )

    # Get data for this metric type
    data = adapter.get_data(metric_type, start_date, end_date, user_id)
    if not data:
        logger.warning(f"No data found for {metric_type} (user {user_id})")
        return 0

    # Ensure user and device exist
    db.ensure_users_and_devices(user_id, f"device-{user_id}")

    # Process data in the date range
    current_date = start_date
    total_records = 0

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        logger.info(f"Processing date: {date_str}")

        # Get filtered data for this specific date
        filtered_data = adapter.filter_data_for_date(data, date_str, metric_type)
        if filtered_data:
            # Create and process the metric
            metric = metric_factory.create_metric(
                metric_type, user_id, f"device-{user_id}"
            )
            metric.set_data(filtered_data)

            # Get flattened records and insert them
            flat_records = metric.get_flat_records()
            if flat_records:
                inserted = db.insert_records(flat_records)
                logger.info(f"Inserted {inserted} records for {date_str}")
                total_records += inserted
            else:
                logger.warning(f"No flat records generated for {date_str}")
        else:
            logger.warning(f"No data found for {date_str}")

        # Move to next day
        current_date += timedelta(days=1)

    # Update the last processed date
    if total_records > 0:
        db.update_last_processed_date(metric_type, user_id, end_date)

    return total_records


def normal_mode(db, adapter, metric_factory, user_ids, metrics):
    """Run in normal mode - process one day at a time"""
    for user_id in user_ids:
        logger.info(f"=== Processing data for User {user_id} ===")

        for metric_type in metrics:
            if not adapter.check_data_availability(metric_type, user_id):
                logger.warning(
                    f"No data file available for {metric_type} (user {user_id})"
                )
                continue

            # Get the last processed date
            last_date = db.get_last_processed_date(metric_type, user_id)

            # If no last date, start from Jan 1, 2024
            if not last_date:
                last_date = datetime(2024, 1, 1)

            # Process just one day
            target_date = last_date
            next_day = target_date + timedelta(days=1)

            # Don't process beyond Jan 30, 2024
            end_date = datetime(2024, 1, 30)
            if target_date > end_date:
                logger.info(f"Already at end date for {metric_type}")
                continue

            logger.info(f"Processing {metric_type} for {target_date.date()}")
            process_data(
                db,
                metric_type,
                user_id,
                target_date,
                target_date,
                adapter,
                metric_factory,
            )

            # Update last processed date
            db.update_last_processed_date(metric_type, user_id, next_day)


def test_mode(db, adapter, metric_factory, user_ids, metrics):
    """Run in test mode - process one day at a time with 2-min intervals"""
    current_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 30)

    while current_date <= end_date:
        logger.info(f"=== Processing date: {current_date.date()} ===")

        for user_id in user_ids:
            for metric_type in metrics:
                if adapter.check_data_availability(metric_type, user_id):
                    process_data(
                        db,
                        metric_type,
                        user_id,
                        current_date,
                        current_date,
                        adapter,
                        metric_factory,
                    )

        # Move to next day
        current_date += timedelta(days=1)

        if current_date <= end_date:
            logger.info(f"Test run complete. Waiting 2 minutes before next date...")
            time.sleep(120)  # 2 minutes


def catchup_mode(db, adapter, metric_factory, user_ids, metrics):
    """Run in catch-up mode - process all data up to Jan 30, 2024"""
    end_date = datetime(2024, 1, 30)

    for user_id in user_ids:
        logger.info(f"=== Catching up data for User {user_id} ===")

        for metric_type in metrics:
            if not adapter.check_data_availability(metric_type, user_id):
                logger.warning(
                    f"No data file available for {metric_type} (user {user_id})"
                )
                continue

            # Get the last processed date
            start_date = db.get_last_processed_date(metric_type, user_id)

            # If no last date, start from Jan 1, 2024
            if not start_date:
                start_date = datetime(2024, 1, 1)

            # Don't process if already at end date
            if start_date >= end_date:
                logger.info(f"Already at end date for {metric_type}")
                continue

            logger.info(
                f"Catching up {metric_type} from {start_date.date()} to {end_date.date()}"
            )
            process_data(
                db, metric_type, user_id, start_date, end_date, adapter, metric_factory
            )

            # Update last processed date to day after end_date
            next_day = end_date + timedelta(days=1)
            db.update_last_processed_date(metric_type, user_id, next_day)


def reset_mode(db):
    """Reset all data and timestamps"""
    logger.info("Resetting all data and timestamps")

    # Clear all data tables
    try:
        with db.conn.cursor() as cursor:
            tables = [
                "HEART_RATE",
                "HEART_RATE_ZONES",
                "SPO2",
                "HRV",
                "BREATHING_RATE",
                "ACTIVE_ZONE_MINUTES",
                "ACTIVITY",
                "LAST_PROCESSED_DATES",
            ]
            for table in tables:
                cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
            db.conn.commit()
            logger.info("Successfully cleared all data tables")
            return True
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        db.conn.rollback()
        return False


def initialize_schema(db):
    """Initialize database schema by executing schema.sql file"""
    logger.info("Initializing database schema...")

    # Look for schema.sql in the current directory and parent directory
    schema_paths = [
        "schema.sql",
        "../schema.sql",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql"),
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema.sql"
        ),
    ]

    schema_path = None
    for path in schema_paths:
        if os.path.exists(path):
            schema_path = path
            break

    if not schema_path:
        logger.error(
            "Schema file 'schema.sql' not found. Please provide a valid schema file path."
        )
        return False

    try:
        # Read the schema SQL
        logger.info(f"Reading schema from {schema_path}")
        with open(schema_path, "r") as f:
            schema_sql = f.read()

        # Execute the SQL script
        with db.conn.cursor() as cursor:
            cursor.execute(schema_sql)
        db.conn.commit()
        logger.info("Successfully initialized database schema")
        return True
    except Exception as e:
        logger.error(f"Error initializing database schema: {e}")
        import traceback

        logger.error(traceback.format_exc())
        db.conn.rollback()
        return False


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description="Test Fitbit data import to database")
    parser.add_argument(
        "--mode",
        choices=["normal", "test", "catchup", "reset"],
        default="normal",
        help="Operation mode",
    )
    parser.add_argument("--user-id", type=str, help="Specific user ID to process")
    parser.add_argument("--metric", type=str, help="Specific metric type to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--schema-file", type=str, help="Path to schema.sql file")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Initialize components
    adapter = SourceAdapterFactory.create_adapter("synthetic_flat", data_dir=DATA_DIR)
    metric_factory = HealthMetricFactory()
    db = initialize_db()

    # Initialize schema first
    schema_path = args.schema_file
    if schema_path and os.path.exists(schema_path):
        initialize_schema_with_path(db, schema_path)
    else:
        success = initialize_schema(db)
        if not success:
            logger.error("Failed to initialize schema. Exiting.")
            db.close()
            return

    # Define users and metrics
    user_ids = [args.user_id] if args.user_id else ["1", "2"]
    metrics = (
        [args.metric]
        if args.metric
        else [
            "heart_rate",
            "spo2",
            "hrv",
            "breathing_rate",
            "active_zone_minutes",
            "activity",
        ]
    )

    try:
        # Run in specified mode
        if args.mode == "reset":
            success = reset_mode(db)
            if success and args.mode == "reset":
                logger.info("Reset complete")
                return

        if args.mode == "normal":
            normal_mode(db, adapter, metric_factory, user_ids, metrics)
        elif args.mode == "test":
            test_mode(db, adapter, metric_factory, user_ids, metrics)
        elif args.mode == "catchup":
            catchup_mode(db, adapter, metric_factory, user_ids, metrics)

        logger.info(f"{args.mode.capitalize()} mode completed successfully")

    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
    except Exception as e:
        logger.error(f"Error during operation: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
