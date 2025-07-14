import logging
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Dict, Any, Optional
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
                        (user_id, name, email),
                    )
                    self.conn.commit()
                    logger.info(f"Created new user with ID: {user_id}")

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
                    logger.info(f"Created new device: {device_id} for user: {user_id}")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error ensuring device exists: {str(e)}")

    def insert_metrics(self, metrics: List[Dict[str, Any]]):
        if not metrics:
            logger.info("No metrics to insert")
            return

        try:
            with self.conn.cursor() as cur:
                # Prepare data for batch insert
                values = [
                    (
                        m["metric_type"],
                        m["user_id"],
                        m["device_id"],
                        m["timestamp"],
                        json.dumps(m["value"]),
                    )
                    for m in metrics
                ]

                # Use execute_values for efficient batch insert
                execute_values(
                    cur,
                    """
                    INSERT INTO raw_data (metric_type, user_id, device_id, timestamp, value)
                    VALUES %s
                    """,
                    values,
                )

                self.conn.commit()
                logger.info(f"Successfully inserted {len(metrics)} metrics")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting metrics: {str(e)}")

    def get_latest_timestamp(
        self, metric_type: Optional[str] = None, user_id: Optional[int] = None
    ) -> Optional[str]:
        try:
            query = "SELECT MAX(timestamp) FROM raw_data"
            params = []

            # Build WHERE clause if filters provided
            where_clauses = []
            if metric_type:
                where_clauses.append("metric_type = %s")
                params.append(metric_type)

            if user_id:
                where_clauses.append("user_id = %s")
                params.append(user_id)

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            with self.conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()

                if result and result[0]:
                    return result[0].isoformat()
                return None

        except Exception as e:
            logger.error(f"Error getting latest timestamp: {str(e)}")
            return None
