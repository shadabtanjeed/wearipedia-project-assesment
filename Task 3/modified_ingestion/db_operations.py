import os
import logging
import psycopg2
from psycopg2.extras import execute_values
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger("DBOperations")


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
            return dt

        # Convert to UTC and remove timezone info for storage
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception as e:
        logger.error(f"Error converting timestamp {timestamp_input} to UTC: {e}")
        return None


# Database operations class for interacting with TimescaleDB
class DBOperations:
    def __init__(self, host, port, dbname, user, password):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
            )
            logger.debug(
                f"Connected to database {self.dbname} at {self.host}:{self.port}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")

    def execute_query(self, query, params=None, commit=True):
        if not self.conn:
            logger.error("No database connection")
            return None

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                if commit:
                    self.conn.commit()
                return cursor.fetchall() if not commit else None
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.conn.rollback()
            return None

    def insert_records(self, records):
        """Insert records into appropriate tables based on the 'table' field in each record"""
        if not records:
            return 0

        # Group records by table
        grouped_records = {}
        for record in records:
            table = record.pop("table", None)
            if not table:
                logger.error(f"Record is missing 'table' field: {record}")
                continue

            # Convert timestamp to UTC if present
            if "timestamp" in record and record["timestamp"]:
                timestamp = record["timestamp"]
                if isinstance(timestamp, str):
                    timestamp = convert_to_utc(timestamp)
                elif timestamp.tzinfo is not None:
                    timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
                record["timestamp"] = timestamp

            if table not in grouped_records:
                grouped_records[table] = []
            grouped_records[table].append(record)

        # Insert records for each table
        total_inserted = 0
        for table, table_records in grouped_records.items():
            inserted = self._insert_to_table(table, table_records)
            total_inserted += inserted

        return total_inserted

    def _insert_to_table(self, table, records):
        """Insert records to the specified table"""
        if not records:
            return 0

        try:
            with self.conn.cursor() as cursor:
                # Dynamically generate the query based on the first record's keys
                columns = list(records[0].keys())
                placeholders = ", ".join([f"%({col})s" for col in columns])
                query = f"""
                INSERT INTO {table} ({", ".join(columns)})
                VALUES %s
                """

                template = f"({placeholders})"
                execute_values(cursor, query, records, template)
                inserted = len(records)
                self.conn.commit()
                logger.debug(f"Inserted {inserted} records into {table}")
                return inserted
        except Exception as e:
            logger.error(f"Error inserting into {table}: {e}")
            self.conn.rollback()
            return 0

    def get_last_processed_date(self, metric_type, user_id):
        """Get last processed date as UTC timezone-naive"""
        query = """
        SELECT last_processed_date FROM last_processed_dates
        WHERE metric_type = %s AND user_id = %s;
        """
        result = self.execute_query(query, (metric_type, user_id), commit=False)

        if result and result[0]:
            timestamp = result[0][0]
            # Ensure it's timezone-naive UTC
            if timestamp.tzinfo is not None:
                timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
            return timestamp
        return None

    def update_last_processed_date(self, metric_type, user_id, date):
        """Update last processed date with UTC timezone-naive timestamp"""
        # Ensure the date is UTC timezone-naive
        if date.tzinfo is not None:
            date = date.astimezone(timezone.utc).replace(tzinfo=None)

        query = """
        INSERT INTO last_processed_dates (metric_type, user_id, last_processed_date)
        VALUES (%s, %s, %s)
        ON CONFLICT (metric_type, user_id)
        DO UPDATE SET last_processed_date = %s, updated_at = NOW();
        """
        return self.execute_query(query, (metric_type, user_id, date, date))

    def ensure_users_and_devices(self, user_id, device_id=None):
        """Ensure user and device exists in DB"""

        # First insert/check user
        user_query = """
        INSERT INTO users (user_id, name, email)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING;
        """
        self.execute_query(
            user_query, (user_id, f"User {user_id}", f"user{user_id}@example.com")
        )

        # Then insert/check device if provided
        if device_id:
            device_query = """
            INSERT INTO devices (device_id, user_id, device_type, model)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (device_id) DO NOTHING;
            """
            self.execute_query(device_query, (device_id, user_id, "Fitbit", "Charge 6"))
