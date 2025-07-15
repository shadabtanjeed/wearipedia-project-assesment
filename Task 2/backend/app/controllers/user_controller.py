from typing import List, Dict, Any

from app.db import get_db_connection
from psycopg2.extras import RealDictCursor


def get_all_users() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    user_id,
                    name,
                    email,
                    created_at
                FROM users
                ORDER BY user_id
                """
            )
            return cursor.fetchall()


def get_user_by_id(user_id: int) -> Dict[str, Any]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    user_id,
                    name,
                    email,
                    created_at
                FROM users
                WHERE user_id = %s
                """,
                (user_id,),
            )
            return cursor.fetchone()


def get_user_devices(user_id: int) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    device_id,
                    device_type,
                    model,
                    registered_at
                FROM devices
                WHERE user_id = %s
                ORDER BY registered_at
                """,
                (user_id,),
            )
            return cursor.fetchall()
