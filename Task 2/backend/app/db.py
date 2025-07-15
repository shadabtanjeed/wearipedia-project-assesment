import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "fitbit_data")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")


def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    conn.autocommit = True
    return conn


def get_users() -> List[int]:
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT USER_ID FROM USERS ORDER BY USER_ID")
            users = [row[0] for row in cursor.fetchall()]
            return users
    finally:
        if conn:
            conn.close()


def get_available_metrics() -> List[str]:
    return [
        "heart_rate",
        "spo2",
        "hrv",
        "breathing_rate",
        "active_zone_minutes",
        "activity",
    ]
