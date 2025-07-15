from typing import List, Dict, Any

from app.db import get_db_connection
from psycopg2.extras import RealDictCursor


def get_all_devices() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    device_id,
                    user_id,
                    device_type,
                    model,
                    registered_at
                FROM devices
                ORDER BY registered_at
                """
            )
            return cursor.fetchall()


def get_device_by_id(device_id: str) -> Dict[str, Any]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    device_id,
                    user_id,
                    device_type,
                    model,
                    registered_at
                FROM devices
                WHERE device_id = %s
                """,
                (device_id,),
            )
            return cursor.fetchone()
