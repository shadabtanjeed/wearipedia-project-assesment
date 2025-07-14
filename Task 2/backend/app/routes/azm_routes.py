from db import get_db_connection
from datetime import datetime, timezone
import pytz
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any


def get_all_azm_data(user_id, start_date, end_date):
    gmt6 = pytz.timezone("Asia/Dhaka")

    if start_date.tzinfo is None:
        start_date = gmt6.localize(start_date)
    if end_date.tzinfo is None:
        end_date = gmt6.localize(end_date)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET TIME ZONE '+06:00'")

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    timestamp,
                    fat_burn_minutes, 
                    cardio_minutes, 
                    peak_minutes, 
                    active_zone_minutes 
                FROM active_zone_minutes
                WHERE user_id = %s AND timestamp BETWEEN %s AND %s
                ORDER BY timestamp
            """,
                (user_id, start_date, end_date),
            )
            return cursor.fetchall()


def get_daily_avg_azm_data(user_id, start_date, end_date):
    gmt6 = pytz.timezone("Asia/Dhaka")

    if start_date.tzinfo is None:
        start_date = gmt6.localize(start_date)
    if end_date.tzinfo is None:
        end_date = gmt6.localize(end_date)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET TIME ZONE '+06:00'")

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    date_trunc('day', timestamp) AT TIME ZONE '+06:00' AS day, 
                    AVG(fat_burn_minutes) AS avg_fat_burn_minutes, 
                    AVG(cardio_minutes) AS avg_cardio_minutes, 
                    AVG(peak_minutes) AS avg_peak_minutes, 
                    AVG(active_zone_minutes) AS avg_active_zone_minutes
                FROM active_zone_minutes
                WHERE user_id = %s AND timestamp BETWEEN %s AND %s
                GROUP BY day
                ORDER BY day
            """,
                (user_id, start_date, end_date),
            )
            return cursor.fetchall()
