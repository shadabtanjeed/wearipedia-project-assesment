import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("SourceAdapterFixer")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


def fix_adapter_mapping():
    """Create symbolic links to ensure files are found with expected names"""
    data_dir = "../Data/Modified Data"

    # Mapping of source adapter expected filenames to actual filenames
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
                # Create symbolic link
                os.symlink(actual_name, expected_path)
                logger.info(f"Created symbolic link: {expected_path} -> {actual_path}")
            except Exception as e:
                logger.error(f"Error creating symbolic link: {e}")

                # Alternative: copy file
                try:
                    with open(actual_path, "r") as src_file:
                        data = json.load(src_file)
                    with open(expected_path, "w") as dst_file:
                        json.dump(data, dst_file)
                    logger.info(f"Copied file: {actual_path} -> {expected_path}")
                except Exception as e2:
                    logger.error(f"Error copying file: {e2}")


def reset_timestamps():
    """Reset timestamps to January 2024 for all metrics and users"""
    from datetime import datetime

    start_date = datetime(2024, 1, 1)

    # Using InfluxDB operations to reset timestamps
    try:
        from influx_operations import InfluxOperations

        # Get environment variables
        import os

        url = os.environ.get("INFLUXDB_URL", "http://localhost:8086")
        token = os.environ.get("INFLUXDB_TOKEN", "my-super-secret-token")
        org = os.environ.get("INFLUXDB_ORG", "fitbit")
        bucket = os.environ.get("INFLUXDB_BUCKET", "fitbit_metrics")

        db = InfluxOperations(url, token, org, bucket)
        if not db.connect():
            logger.error("Failed to connect to InfluxDB")
            return

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
                db.update_last_processed_date(metric_type, user_id, start_date)
                logger.info(
                    f"Reset timestamp for {metric_type}, user {user_id} to {start_date}"
                )

        db.close()
        logger.info("Successfully reset all timestamps")
    except Exception as e:
        logger.error(f"Error resetting timestamps: {e}")
        import traceback

        logger.error(traceback.format_exc())


if __name__ == "__main__":
    fix_adapter_mapping()
    reset_timestamps()
