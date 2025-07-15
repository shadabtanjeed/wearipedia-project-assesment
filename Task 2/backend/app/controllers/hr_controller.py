from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from app.config.timezone import GMT6
from app.db import get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("app")


def get_all_heart_rate_data(
    user_id: int, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Try to get data for requested period
        query = """
        SELECT timestamp, value 
        FROM HEART_RATE 
        WHERE user_id = %s AND timestamp BETWEEN %s AND %s 
        ORDER BY timestamp
        """
        cursor.execute(query, (user_id, start_date, end_date))
        data = cursor.fetchall()

        # Fallback 1: If no data in requested range, try to get most recent data
        if not data:
            logger.info(
                f"No heart rate data for user {user_id} between {start_date} and {end_date}. Trying fallback."
            )
            fallback_query = """
            SELECT timestamp, value 
            FROM HEART_RATE 
            WHERE user_id = %s AND timestamp <= %s 
            ORDER BY timestamp DESC 
            LIMIT 100
            """
            cursor.execute(fallback_query, (user_id, end_date))
            data = cursor.fetchall()

            # Fallback 2: If still no data, check if user exists but has no heart rate data
            if not data:
                user_check_query = "SELECT user_id FROM USERS WHERE user_id = %s"
                cursor.execute(user_check_query, (user_id,))
                user_exists = cursor.fetchone()

                if not user_exists:
                    raise ValueError(f"User {user_id} does not exist")
                else:
                    logger.warning(f"User {user_id} exists but has no heart rate data")
                    return []  # Return empty but valid result

        return data

    except Exception as e:
        logger.error(f"Database error in get_all_heart_rate_data: {str(e)}")
        # Fallback 3: Return empty list rather than crashing
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_daily_avg_heart_rate_data(
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
            tz_cursor.execute("SET TIME ZONE '+06:00'")

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Try to get data for requested period
        query = """
        SELECT 
            date_trunc('day', timestamp) AT TIME ZONE '+06:00' AS day, 
            AVG(value) AS avg_heart_rate,
            AVG(resting_heart_rate) AS avg_resting_heart_rate
        FROM heart_rate
        WHERE user_id = %s AND timestamp BETWEEN %s AND %s
        GROUP BY day
        ORDER BY day
        """
        cursor.execute(query, (user_id, start_date, end_date))
        results = cursor.fetchall()

        # Fallback 1: If no data in requested range, try extending the date range by 7 days
        if not results:
            logger.info(
                f"No daily avg heart rate data for user {user_id} between {start_date} and {end_date}. Trying wider range fallback."
            )
            extended_start = start_date - timedelta(days=7)
            extended_end = end_date + timedelta(days=7)

            cursor.execute(query, (user_id, extended_start, extended_end))
            results = cursor.fetchall()

            # Fallback 2: If still no data, check if user exists but has no heart rate data
            if not results:
                user_check_query = "SELECT user_id FROM USERS WHERE user_id = %s"
                cursor.execute(user_check_query, (user_id,))
                user_exists = cursor.fetchone()

                if not user_exists:
                    raise ValueError(f"User {user_id} does not exist")
                else:
                    logger.warning(
                        f"User {user_id} exists but has no daily average heart rate data"
                    )
                    return []  # Return empty but valid result

        return results

    except Exception as e:
        logger.error(f"Database error in get_daily_avg_heart_rate_data: {str(e)}")
        # Fallback 3: Return empty list rather than crashing
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_heart_rate_zones_data(
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
            tz_cursor.execute("SET TIME ZONE '+06:00'")

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Try to get data for requested period
        query = """
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
        """
        cursor.execute(query, (user_id, start_date, end_date))
        results = cursor.fetchall()

        # Fallback 1: If no data in requested range, try most recent data
        if not results:
            logger.info(
                f"No heart rate zones data for user {user_id} between {start_date} and {end_date}. Trying fallback."
            )
            fallback_query = """
            SELECT 
                timestamp,
                zone_name,
                min_hr,
                max_hr,
                minutes,
                calories_out
            FROM heart_rate_zones
            WHERE user_id = %s AND timestamp <= %s
            ORDER BY timestamp DESC, zone_name
            LIMIT 100
            """
            cursor.execute(fallback_query, (user_id, end_date))
            results = cursor.fetchall()

            # Fallback 2: If still no data, check if user exists but has no heart rate zones data
            if not results:
                user_check_query = "SELECT user_id FROM USERS WHERE user_id = %s"
                cursor.execute(user_check_query, (user_id,))
                user_exists = cursor.fetchone()

                if not user_exists:
                    raise ValueError(f"User {user_id} does not exist")
                else:
                    logger.warning(
                        f"User {user_id} exists but has no heart rate zones data"
                    )
                    return []  # Return empty but valid result

        return results

    except Exception as e:
        logger.error(f"Database error in get_heart_rate_zones_data: {str(e)}")
        # Fallback 3: Return empty list rather than crashing
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
