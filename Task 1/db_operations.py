import os
import logging
import psycopg2
from psycopg2.extras import execute_values
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("DBOperations")


# Database operations class for interacting with TimescaleDB
class DBOperations:

    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        # Initialize database connection parameters
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.cursor = None

    # Connect to the database
    def connect(self) -> bool:

        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            self.cursor = self.conn.cursor()
            logger.info("Successfully connected to database")
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return False

    def close(self):
        """Close the database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

    def ensure_user_exists(self, user_id: int) -> bool:
        """Ensure a user exists in the database, creating if necessary"""
        if not self.conn or self.conn.closed:
            if not self.connect():
                return False

        try:
            # Check if user exists
            self.cursor.execute("SELECT 1 FROM USERS WHERE USER_ID = %s", (user_id,))
            if self.cursor.fetchone() is None:
                # Insert new user
                self.cursor.execute(
                    "INSERT INTO USERS (USER_ID) VALUES (%s) ON CONFLICT DO NOTHING",
                    (user_id,),
                )
                self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error ensuring user exists: {e}")
            self.conn.rollback()
            return False

    def ensure_device_exists(
        self, device_id: str, user_id: int, device_type: str, model: str
    ) -> bool:
        """Ensure a device exists in the database, creating if necessary"""
        if not self.conn or self.conn.closed:
            if not self.connect():
                return False

        try:
            # Check if device exists
            self.cursor.execute(
                "SELECT 1 FROM DEVICES WHERE DEVICE_ID = %s", (device_id,)
            )
            if self.cursor.fetchone() is None:
                # Insert new device
                self.cursor.execute(
                    """
                    INSERT INTO DEVICES (DEVICE_ID, USER_ID, DEVICE_TYPE, MODEL) 
                    VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING
                    """,
                    (device_id, user_id, device_type, model),
                )
                self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error ensuring device exists: {e}")
            self.conn.rollback()
            return False

    def get_last_processed_date(
        self, metric_type: str, user_id: int
    ) -> Optional[datetime]:
        """Get the last processed date for a specific metric type and user"""
        if not self.conn or self.conn.closed:
            if not self.connect():
                return None

        try:
            # Query the last processed date
            self.cursor.execute(
                """
                SELECT LAST_PROCESSED_DATE FROM LAST_PROCESSED_DATES 
                WHERE METRIC_TYPE = %s AND USER_ID = %s
                """,
                (metric_type, user_id),
            )
            result = self.cursor.fetchone()
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting last processed date: {e}")
            return None

    def update_last_processed_date(
        self, metric_type: str, user_id: int, timestamp: datetime
    ) -> bool:
        """Update the last processed date for a specific metric type and user"""
        if not self.conn or self.conn.closed:
            if not self.connect():
                return False

        try:
            # Insert or update the last processed date
            self.cursor.execute(
                """
                INSERT INTO LAST_PROCESSED_DATES (METRIC_TYPE, USER_ID, LAST_PROCESSED_DATE) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (METRIC_TYPE, USER_ID) 
                DO UPDATE SET LAST_PROCESSED_DATE = %s, UPDATED_AT = NOW()
                """,
                (metric_type, user_id, timestamp, timestamp),
            )
            self.conn.commit()
            logger.info(f"Updated last processed date for {metric_type}: {timestamp}")
            return True
        except Exception as e:
            logger.error(f"Error updating last processed date: {e}")
            self.conn.rollback()
            return False

    def insert_metrics(self, metric_type: str, metrics: List[Dict]) -> bool:
        """Insert metrics into the appropriate table"""
        if not metrics:
            logger.warning(f"No {metric_type} metrics to insert")
            return False

        if not self.conn or self.conn.closed:
            if not self.connect():
                return False

        try:
            # Determine the appropriate table and columns based on metric_type
            table_name, columns, values_list = self._prepare_metrics_for_insertion(
                metric_type, metrics
            )

            # Construct placeholders for the VALUES clause
            placeholders = ", ".join(["%s"] * len(columns))
            columns_str = ", ".join(columns)

            # Use execute_values for bulk insertion
            execute_values(
                self.cursor,
                f"INSERT INTO {table_name} ({columns_str}) VALUES %s ON CONFLICT DO NOTHING",
                values_list,
                template=f"({placeholders})",
                page_size=1000,  # Insert in batches of 1000
            )
            self.conn.commit()
            logger.info(f"Successfully inserted {len(metrics)} {metric_type} metrics")
            return True
        except Exception as e:
            logger.error(f"Error inserting {metric_type} metrics: {e}")
            import traceback

            logger.error(traceback.format_exc())
            self.conn.rollback()
            return False

    def _prepare_metrics_for_insertion(
        self, metric_type: str, metrics: List[Dict]
    ) -> tuple:
        """Prepare metrics for insertion based on metric type"""
        table_name = self._get_table_name(metric_type)
        columns = self._get_columns_for_metric_type(metric_type)
        values_list = []

        # Prepare values list based on columns
        for metric in metrics:
            row_values = []
            for col in columns:
                # Convert column name to lowercase for case-insensitive lookup
                col_lower = col.lower()
                value = metric.get(col_lower, None)

                # Serialize JSON/dict data for PostgreSQL
                if isinstance(value, (dict, list)) and col in [
                    "ZONES",
                    "SUMMARY",
                    "INTRADAY",
                    "MINUTE_DATA",
                ]:
                    # Convert Python dict/list to JSON string
                    import json

                    value = json.dumps(value)

                row_values.append(value)
            values_list.append(tuple(row_values))

        return table_name, columns, values_list

    def _get_table_name(self, metric_type: str) -> str:
        """Get the appropriate table name for a metric type"""
        mapping = {
            "hr": "HEART_RATE",
            "spo2": "SPO2",
            "hrv": "HRV",
            "br": "BREATHING_RATE",
            "azm": "ACTIVE_ZONE_MINUTES",
            "activity": "ACTIVITY",
        }
        return mapping.get(metric_type, metric_type.upper())

    def _get_columns_for_metric_type(self, metric_type: str) -> List[str]:
        """Get the appropriate columns for a metric type"""
        base_columns = ["USER_ID", "DEVICE_ID", "TIMESTAMP"]

        if metric_type == "hr":
            return base_columns + [
                "VALUE",
                "RESTING_HEART_RATE",
                "ZONES",
                "SUMMARY",
                "INTRADAY",
            ]
        elif metric_type == "spo2":
            return base_columns + ["VALUE", "MINUTE_DATA"]
        elif metric_type == "hrv":
            return base_columns + ["RMSSD", "COVERAGE", "HF", "LF", "MINUTE_DATA"]
        elif metric_type == "br":
            return base_columns + [
                "DEEP_SLEEP_RATE",
                "REM_SLEEP_RATE",
                "LIGHT_SLEEP_RATE",
                "FULL_SLEEP_RATE",
            ]
        elif metric_type == "azm":
            return base_columns + [
                "FAT_BURN_MINUTES",
                "CARDIO_MINUTES",
                "PEAK_MINUTES",
                "ACTIVE_ZONE_MINUTES",
                "MINUTE_DATA",
            ]
        elif metric_type == "activity":
            return base_columns + ["VALUE"]
        else:
            logger.warning(f"Unknown metric type: {metric_type}, using base columns")
            return base_columns
