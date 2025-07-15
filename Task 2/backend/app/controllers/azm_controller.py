from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from app.config.timezone import GMT6
from app.db import get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("app")


def get_all_azm_data(
    user_id: int, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    if start_date.tzinfo is None:
        start_date = GMT6.localize(start_date)
    if end_date.tzinfo is None:
        end_date = GMT6.localize(end_date)

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = None

        # Set timezone for this connection
        with conn.cursor() as tz_cursor:
            tz_cursor.execute("SET TIME ZONE 'UTC'")

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Try to get data for requested period
        query = """
        SELECT 
            timestamp,
            fat_burn_minutes, 
            cardio_minutes, 
            peak_minutes, 
            active_zone_minutes 
        FROM active_zone_minutes
        WHERE user_id = %s AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp
        """
        cursor.execute(query, (user_id, start_date, end_date))
        results = cursor.fetchall()

        # Fallback mechanism starts here
        if not results:
            logger.info(
                f"No active zone minutes data for user {user_id} between {start_date} and {end_date}. Trying fallback."
            )
            fallback_query = """
            SELECT 
                timestamp,
                fat_burn_minutes, 
                cardio_minutes, 
                peak_minutes, 
                active_zone_minutes 
            FROM active_zone_minutes
            WHERE user_id = %s AND timestamp <= %s
            ORDER BY timestamp DESC
            LIMIT 100
            """
            cursor.execute(fallback_query, (user_id, end_date))
            results = cursor.fetchall()

            if not results:
                user_check_query = "SELECT user_id FROM USERS WHERE user_id = %s"
                cursor.execute(user_check_query, (user_id,))
                user_exists = cursor.fetchone()

                if not user_exists:
                    raise ValueError(f"User {user_id} does not exist")
                else:
                    logger.warning(
                        f"User {user_id} exists but has no active zone minutes data"
                    )
                    return []

        return results

    except Exception as e:
        logger.error(f"Database error in get_all_azm_data: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_daily_avg_azm_data(
    user_id: int, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    if start_date.tzinfo is None:
        start_date = GMT6.localize(start_date)
    if end_date.tzinfo is None:
        end_date = GMT6.localize(end_date)

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = None

        # Set timezone for this connection
        with conn.cursor() as tz_cursor:
            tz_cursor.execute("SET TIME ZONE 'UTC'")

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Try to get data for requested period
        query = """
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
        """
        cursor.execute(query, (user_id, start_date, end_date))
        results = cursor.fetchall()

        # Fallback mechanism starts here
        if not results:
            logger.info(
                f"No daily avg AZM data for user {user_id} between {start_date} and {end_date}. Trying wider range fallback."
            )
            extended_start = start_date - timedelta(days=7)
            extended_end = end_date + timedelta(days=7)

            cursor.execute(query, (user_id, extended_start, extended_end))
            results = cursor.fetchall()

            if not results:
                user_check_query = "SELECT user_id FROM USERS WHERE user_id = %s"
                cursor.execute(user_check_query, (user_id,))
                user_exists = cursor.fetchone()

                if not user_exists:
                    raise ValueError(f"User {user_id} does not exist")
                else:
                    logger.warning(
                        f"User {user_id} exists but has no daily average AZM data"
                    )
                    return []

        return results

    except Exception as e:
        logger.error(f"Database error in get_daily_avg_azm_data: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
