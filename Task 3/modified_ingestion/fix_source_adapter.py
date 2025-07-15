import os
import json
import logging
import shutil

logger = logging.getLogger("SourceAdapterFixer")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


def fix_adapter_mapping():
    """Create symbolic links or copies to ensure files are found with expected names"""
    # Determine data directory
    data_dir = None
    if os.path.exists("/app/Data/Modified Data"):
        data_dir = "/app/Data/Modified Data"
    elif os.path.exists("../Data/Modified Data"):
        data_dir = "../Data/Modified Data"
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        data_dir = os.path.join(project_root, "Data", "Modified Data")

    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return

    logger.info(f"Using data directory: {data_dir}")

    # Mapping of expected file names to actual file names
    file_mappings = {
        "heart_rate_user1_modified.json": "hr_user1_modified.json",
        "heart_rate_user2_modified.json": "hr_user2_modified.json",
        "breathing_rate_user1_modified.json": "br_user1_modified.json",
        "breathing_rate_user2_modified.json": "br_user2_modified.json",
        "active_zone_minutes_user1_modified.json": "azm_user1_modified.json",
        "active_zone_minutes_user2_modified.json": "azm_user2_modified.json",
    }

    for expected_name, actual_name in file_mappings.items():
        expected_path = os.path.join(data_dir, expected_name)
        actual_path = os.path.join(data_dir, actual_name)

        if os.path.exists(actual_path) and not os.path.exists(expected_path):
            try:
                # Try symbolic link first
                try:
                    os.symlink(actual_name, expected_path)
                    logger.info(
                        f"Created symbolic link: {expected_path} -> {actual_path}"
                    )
                except (OSError, NotImplementedError):
                    # Fall back to copying if symlinks not supported
                    shutil.copy2(actual_path, expected_path)
                    logger.info(f"Copied file: {actual_path} -> {expected_path}")
            except Exception as e:
                logger.error(f"Error creating file mapping: {e}")

                # Alternative: copy file content
                try:
                    with open(actual_path, "r") as src_file:
                        data = json.load(src_file)
                    with open(expected_path, "w") as dst_file:
                        json.dump(data, dst_file)
                    logger.info(f"Created JSON file: {expected_path}")
                except Exception as e2:
                    logger.error(f"Error copying file content: {e2}")

    # Reset timestamps in DB to use January 2024 start date
    try:
        reset_db_timestamps()
        logger.info("Reset DB timestamps to January 2024")
    except Exception as e:
        logger.error(f"Failed to reset DB timestamps: {e}")


def reset_db_timestamps():
    """Reset all timestamps in the database to start from January 2024"""
    import psycopg2
    from datetime import datetime

    # Get database parameters from environment or use defaults
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = int(os.environ.get("DB_PORT", "5432"))
    db_name = os.environ.get("DB_NAME", "fitbit_data")
    db_user = os.environ.get("DB_USER", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "password")

    start_date = datetime(2024, 1, 1)

    conn = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        )
        cursor = conn.cursor()

        # Reset all existing timestamps
        cursor.execute(
            """
            DELETE FROM LAST_PROCESSED_DATES
        """
        )

        # Insert new timestamps for common metric types
        metric_types = [
            "heart_rate",
            "spo2",
            "hrv",
            "breathing_rate",
            "active_zone_minutes",
            "activity",
        ]
        user_ids = [1, 2]

        for metric_type in metric_types:
            for user_id in user_ids:
                cursor.execute(
                    """
                    INSERT INTO LAST_PROCESSED_DATES (METRIC_TYPE, USER_ID, LAST_PROCESSED_DATE)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (METRIC_TYPE, USER_ID) DO UPDATE 
                    SET LAST_PROCESSED_DATE = EXCLUDED.LAST_PROCESSED_DATE
                """,
                    (metric_type, user_id, start_date),
                )

        conn.commit()
        logger.info("Successfully reset all timestamps in database")
    except Exception as e:
        logger.error(f"Database operation error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    fix_adapter_mapping()
    print("Done fixing source adapter mapping")
