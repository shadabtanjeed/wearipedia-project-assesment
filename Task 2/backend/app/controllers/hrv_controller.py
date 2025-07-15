from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from app.config.timezone import GMT6
from app.db import get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("app")


def get_all_hrv_data(
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
            rmssd,
            coverage,
            hf,
            lf
        FROM hrv
        WHERE user_id = %s AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp
        """
        cursor.execute(query, (user_id, start_date, end_date))
        results = cursor.fetchall()

        # Fallback mechanism starts here
        if not results:
            logger.info(
                f"No HRV data for user {user_id} between {start_date} and {end_date}. Trying fallback."
            )
            fallback_query = """
            SELECT 
                timestamp,
                rmssd,
                coverage,
                hf,
                lf
            FROM hrv
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
                    logger.warning(f"User {user_id} exists but has no HRV data")
                    return []

        return results

    except Exception as e:
        logger.error(f"Database error in get_all_hrv_data: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_daily_avg_hrv_data(
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
            AVG(rmssd) AS avg_rmssd,
            AVG(coverage) AS avg_coverage,
            AVG(hf) AS avg_hf,
            AVG(lf) AS avg_lf
        FROM hrv
        WHERE user_id = %s AND timestamp BETWEEN %s AND %s
        GROUP BY day
        ORDER BY day
        """
        cursor.execute(query, (user_id, start_date, end_date))
        results = cursor.fetchall()

        # Fallback mechanism starts here
        if not results:
            logger.info(
                f"No daily avg HRV data for user {user_id} between {start_date} and {end_date}. Trying wider range fallback."
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
                        f"User {user_id} exists but has no daily average HRV data"
                    )
                    return []

        return results

    except Exception as e:
        logger.error(f"Database error in get_daily_avg_hrv_data: {str(e)}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
