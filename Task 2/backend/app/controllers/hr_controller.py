from datetime import datetime
from typing import List, Dict, Any

from app.config.timezone import GMT6
from app.db import get_db_connection
from psycopg2.extras import RealDictCursor


def get_all_heart_rate_data(
    user_id: int, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    if start_date.tzinfo is None:
        start_date = GMT6.localize(start_date)
    if end_date.tzinfo is None:
        end_date = GMT6.localize(end_date)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET TIME ZONE '+06:00'")

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    timestamp,
                    value,
                    resting_heart_rate
                FROM heart_rate
                WHERE user_id = %s AND timestamp BETWEEN %s AND %s
                ORDER BY timestamp
                """,
                (user_id, start_date, end_date),
            )
            results = cursor.fetchall()
            return results


def get_daily_avg_heart_rate_data(
    user_id: int, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    if start_date.tzinfo is None:
        start_date = GMT6.localize(start_date)
    if end_date.tzinfo is None:
        end_date = GMT6.localize(end_date)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET TIME ZONE '+06:00'")

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    date_trunc('day', timestamp) AT TIME ZONE '+06:00' AS day, 
                    AVG(value) AS avg_heart_rate,
                    AVG(resting_heart_rate) AS avg_resting_heart_rate
                FROM heart_rate
                WHERE user_id = %s AND timestamp BETWEEN %s AND %s
                GROUP BY day
                ORDER BY day
                """,
                (user_id, start_date, end_date),
            )
            results = cursor.fetchall()
            return results


def get_heart_rate_zones_data(
    user_id: int, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    if start_date.tzinfo is None:
        start_date = GMT6.localize(start_date)
    if end_date.tzinfo is None:
        end_date = GMT6.localize(end_date)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET TIME ZONE '+06:00'")

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    timestamp,
                    zone_name,
                    min_hr,
                    max_hr,
                    minutes,
                    calories_out
                FROM heart_rate_zones
                WHERE user_id = %s AND timestamp BETWEEN %s AND %s
                ORDER BY timestamp, zone_name
                """,
                (user_id, start_date, end_date),
            )
            results = cursor.fetchall()
            return results
