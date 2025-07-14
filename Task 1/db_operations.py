import logging
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger("DBOperations")


class DBOperations:
    def __init__(self, host: str, port: int, dbname: str, user: str, password: str):
        # initialize the database connection parameters
        self.conn_params = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password,
        }
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            logger.info("Successfully connected to database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def ensure_user_exists(
        self, user_id: int, name: Optional[str] = None, email: Optional[str] = None
    ):
        try:
            with self.conn.cursor() as cur:
                # Check if user exists
                cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
                if cur.fetchone() is None:
                    # Create user if doesn't exist
                    cur.execute(
                        "INSERT INTO users (user_id, name, email) VALUES (%s, %s, %s)",
                        (
                            user_id,
                            name or f"User {user_id}",
                            email or f"user{user_id}@example.com",
                        ),
                    )
                    self.conn.commit()
                    logger.info(f"Created new user: {user_id}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error ensuring user exists: {str(e)}")

    def ensure_device_exists(
        self,
        device_id: str,
        user_id: int,
        device_type: str,
        model: Optional[str] = None,
    ):
        try:
            with self.conn.cursor() as cur:
                # Check if device exists
                cur.execute("SELECT 1 FROM devices WHERE device_id = %s", (device_id,))
                if cur.fetchone() is None:
                    # Create device if doesn't exist
                    cur.execute(
                        "INSERT INTO devices (device_id, user_id, device_type, model) VALUES (%s, %s, %s, %s)",
                        (device_id, user_id, device_type, model),
                    )
                    self.conn.commit()
                    logger.info(f"Created new device: {device_id}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error ensuring device exists: {str(e)}")

    def get_table_name(self, metric_type: str) -> str:
        """Get the table name for a given metric type."""
        table_mapping = {
            "hr": "heart_rate",
            "spo2": "spo2",
            "hrv": "hrv",
            "br": "breathing_rate",
            "azm": "active_zone_minutes",
            "activity": "activity",
        }
        return table_mapping.get(metric_type, "raw_data")

    def insert_heart_rate_metrics(self, metrics: List[Dict[str, Any]]):
        """Insert heart rate metrics into heart_rate table."""
        if not metrics:
            return

        try:
            with self.conn.cursor() as cur:
                values = [
                    (
                        m["user_id"],
                        m["device_id"],
                        m["timestamp"],
                        m["value"],
                        m.get("resting_heart_rate"),
                        json.dumps(m.get("zones")) if m.get("zones") else None,
                    )
                    for m in metrics
                ]

                execute_values(
                    cur,
                    """
                    INSERT INTO heart_rate (user_id, device_id, timestamp, value, resting_heart_rate, zones)
                    VALUES %s
                    ON CONFLICT (id, timestamp) DO UPDATE SET
                        value = EXCLUDED.value,
                        resting_heart_rate = EXCLUDED.resting_heart_rate,
                        zones = EXCLUDED.zones
                    """,
                    values,
                )

                self.conn.commit()
                logger.info(f"Successfully inserted {len(metrics)} heart rate metrics")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting heart rate metrics: {str(e)}")
            raise

    def insert_spo2_metrics(self, metrics: List[Dict[str, Any]]):
        """Insert SpO2 metrics into spo2 table."""
        if not metrics:
            return

        try:
            with self.conn.cursor() as cur:
                values = [
                    (
                        m["user_id"],
                        m["device_id"],
                        m["timestamp"],
                        m["value"],
                        (
                            json.dumps(m.get("minute_data"))
                            if m.get("minute_data")
                            else None
                        ),
                    )
                    for m in metrics
                ]

                execute_values(
                    cur,
                    """
                    INSERT INTO spo2 (user_id, device_id, timestamp, value, minute_data)
                    VALUES %s
                    ON CONFLICT (id, timestamp) DO UPDATE SET
                        value = EXCLUDED.value,
                        minute_data = EXCLUDED.minute_data
                    """,
                    values,
                )

                self.conn.commit()
                logger.info(f"Successfully inserted {len(metrics)} SpO2 metrics")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting SpO2 metrics: {str(e)}")
            raise

    def insert_hrv_metrics(self, metrics: List[Dict[str, Any]]):
        """Insert HRV metrics into hrv table."""
        if not metrics:
            return

        try:
            with self.conn.cursor() as cur:
                values = [
                    (
                        m["user_id"],
                        m["device_id"],
                        m["timestamp"],
                        m.get("rmssd"),
                        m.get("coverage"),
                        m.get("hf"),
                        m.get("lf"),
                        (
                            json.dumps(m.get("minute_data"))
                            if m.get("minute_data")
                            else None
                        ),
                    )
                    for m in metrics
                ]

                execute_values(
                    cur,
                    """
                    INSERT INTO hrv (user_id, device_id, timestamp, rmssd, coverage, hf, lf, minute_data)
                    VALUES %s
                    ON CONFLICT (id, timestamp) DO UPDATE SET
                        rmssd = EXCLUDED.rmssd,
                        coverage = EXCLUDED.coverage,
                        hf = EXCLUDED.hf,
                        lf = EXCLUDED.lf,
                        minute_data = EXCLUDED.minute_data
                    """,
                    values,
                )

                self.conn.commit()
                logger.info(f"Successfully inserted {len(metrics)} HRV metrics")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting HRV metrics: {str(e)}")
            raise

    def insert_breathing_rate_metrics(self, metrics: List[Dict[str, Any]]):
        """Insert breathing rate metrics into breathing_rate table."""
        if not metrics:
            return

        try:
            with self.conn.cursor() as cur:
                values = [
                    (
                        m["user_id"],
                        m["device_id"],
                        m["timestamp"],
                        m.get("deep_sleep_rate"),
                        m.get("rem_sleep_rate"),
                        m.get("light_sleep_rate"),
                        m.get("full_sleep_rate"),
                    )
                    for m in metrics
                ]

                execute_values(
                    cur,
                    """
                    INSERT INTO breathing_rate (user_id, device_id, timestamp, deep_sleep_rate, rem_sleep_rate, light_sleep_rate, full_sleep_rate)
                    VALUES %s
                    ON CONFLICT (id, timestamp) DO UPDATE SET
                        deep_sleep_rate = EXCLUDED.deep_sleep_rate,
                        rem_sleep_rate = EXCLUDED.rem_sleep_rate,
                        light_sleep_rate = EXCLUDED.light_sleep_rate,
                        full_sleep_rate = EXCLUDED.full_sleep_rate
                    """,
                    values,
                )

                self.conn.commit()
                logger.info(
                    f"Successfully inserted {len(metrics)} breathing rate metrics"
                )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting breathing rate metrics: {str(e)}")
            raise

    def insert_active_zone_minutes_metrics(self, metrics: List[Dict[str, Any]]):
        """Insert active zone minutes metrics into active_zone_minutes table."""
        if not metrics:
            return

        try:
            with self.conn.cursor() as cur:
                values = [
                    (
                        m["user_id"],
                        m["device_id"],
                        m["timestamp"],
                        m.get("fat_burn_minutes"),
                        m.get("cardio_minutes"),
                        m.get("peak_minutes"),
                        m.get("active_zone_minutes"),
                        (
                            json.dumps(m.get("minute_data"))
                            if m.get("minute_data")
                            else None
                        ),
                    )
                    for m in metrics
                ]

                execute_values(
                    cur,
                    """
                    INSERT INTO active_zone_minutes (user_id, device_id, timestamp, fat_burn_minutes, cardio_minutes, peak_minutes, active_zone_minutes, minute_data)
                    VALUES %s
                    ON CONFLICT (id, timestamp) DO UPDATE SET
                        fat_burn_minutes = EXCLUDED.fat_burn_minutes,
                        cardio_minutes = EXCLUDED.cardio_minutes,
                        peak_minutes = EXCLUDED.peak_minutes,
                        active_zone_minutes = EXCLUDED.active_zone_minutes,
                        minute_data = EXCLUDED.minute_data
                    """,
                    values,
                )

                self.conn.commit()
                logger.info(
                    f"Successfully inserted {len(metrics)} active zone minutes metrics"
                )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting active zone minutes metrics: {str(e)}")
            raise

    def insert_activity_metrics(self, metrics: List[Dict[str, Any]]):
        """Insert activity metrics into activity table."""
        if not metrics:
            return

        try:
            with self.conn.cursor() as cur:
                values = [
                    (m["user_id"], m["device_id"], m["timestamp"], m["value"])
                    for m in metrics
                ]

                execute_values(
                    cur,
                    """
                    INSERT INTO activity (user_id, device_id, timestamp, value)
                    VALUES %s
                    ON CONFLICT (id, timestamp) DO UPDATE SET
                        value = EXCLUDED.value
                    """,
                    values,
                )

                self.conn.commit()
                logger.info(f"Successfully inserted {len(metrics)} activity metrics")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting activity metrics: {str(e)}")
            raise

    def insert_metrics(self, metric_type: str, metrics: List[Dict[str, Any]]):
        """Insert metrics into appropriate table based on metric type."""
        if not metrics:
            logger.info(f"No {metric_type} metrics to insert")
            return

        # Sort metrics by timestamp to ensure correct ordering
        sorted_metrics = sorted(metrics, key=lambda x: x["timestamp"])

        insertion_methods = {
            "hr": self.insert_heart_rate_metrics,
            "spo2": self.insert_spo2_metrics,
            "hrv": self.insert_hrv_metrics,
            "br": self.insert_breathing_rate_metrics,
            "azm": self.insert_active_zone_minutes_metrics,
            "activity": self.insert_activity_metrics,
        }

        if metric_type in insertion_methods:
            insertion_methods[metric_type](sorted_metrics)
        else:
            logger.error(f"Unknown metric type: {metric_type}")

    def get_latest_timestamp(
        self, metric_type: str, user_id: Optional[int] = None
    ) -> Optional[str]:
        """Get the latest timestamp for a specific metric type and user."""
        try:
            table_name = self.get_table_name(metric_type)
            query = f"SELECT MAX(timestamp) FROM {table_name}"
            params = []

            if user_id:
                query += " WHERE user_id = %s"
                params.append(user_id)

            with self.conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()

                if result and result[0]:
                    return result[0].isoformat()
                return None
        except Exception as e:
            logger.error(f"Error getting latest timestamp for {metric_type}: {str(e)}")
            return None

    def update_last_processed_date(
        self, metric_type: str, user_id: int, processed_date: datetime
    ):
        """Update the last processed date for a metric type and user."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO last_processed_dates (metric_type, user_id, last_processed_date)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (metric_type) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        last_processed_date = EXCLUDED.last_processed_date,
                        updated_at = NOW()
                    """,
                    (metric_type, user_id, processed_date),
                )
                self.conn.commit()
                logger.info(
                    f"Updated last processed date for {metric_type}: {processed_date}"
                )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating last processed date: {str(e)}")

    def get_last_processed_date(
        self, metric_type: str, user_id: Optional[int] = None
    ) -> Optional[datetime]:
        """Get the last processed date for a metric type and user."""
        try:
            query = "SELECT last_processed_date FROM last_processed_dates WHERE metric_type = %s"
            params = [metric_type]

            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)

            with self.conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()

                if result and result[0]:
                    return result[0]
                return None
        except Exception as e:
            logger.error(
                f"Error getting last processed date for {metric_type}: {str(e)}"
            )
            return None
