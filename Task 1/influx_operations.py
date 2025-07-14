import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger("InfluxOps")


class InfluxOperations:
    def __init__(self, url: str, token: str, org: str, bucket: str):
        """Initialize InfluxDB client."""
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None
        self.write_api = None

    def connect(self) -> bool:
        """Connect to InfluxDB."""
        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            logger.info("Successfully connected to InfluxDB")
            return True
        except Exception as e:
            logger.error(f"Error connecting to InfluxDB: {e}")
            return False

    def close(self):
        """Close the InfluxDB connection."""
        if self.client:
            self.client.close()
            logger.info("InfluxDB connection closed")

    def ensure_user_exists(self, user_id: int) -> bool:
        """User data stored as tags in InfluxDB, no need to create separately."""
        return True

    def ensure_device_exists(
        self, device_id: str, user_id: int, device_type: str, model: str = "unknown"
    ) -> bool:
        """Device data stored as tags in InfluxDB, no need to create separately."""
        return True

    def _serialize_json_field(self, data: Any) -> str:
        """Serialize complex objects to JSON strings for InfluxDB storage."""
        if data is None:
            return None
        return json.dumps(data)

    def insert_metrics(self, metric_type: str, metrics: List[Dict[str, Any]]) -> bool:
        """Insert metrics into InfluxDB."""
        if not metrics:
            logger.warning(f"No {metric_type} metrics to insert")
            return True

        try:
            points = []

            # Handle different metric types
            for metric in metrics:
                point = Point(metric_type)

                # Add common tags
                point.tag("user_id", str(metric.get("user_id", "unknown")))
                if metric.get("device_id"):
                    point.tag("device_id", metric["device_id"])

                # Add timestamp
                timestamp = metric.get("timestamp")
                if isinstance(timestamp, datetime):
                    point.time(timestamp)

                # Add fields based on metric type
                if metric_type == "hr":
                    if "value" in metric:
                        point.field("value", float(metric["value"]))
                    if (
                        "resting_heart_rate" in metric
                        and metric["resting_heart_rate"] is not None
                    ):
                        point.field(
                            "resting_heart_rate", float(metric["resting_heart_rate"])
                        )

                    # Handle complex nested JSON structures
                    for json_field in ["zones", "summary", "intraday"]:
                        if json_field in metric and metric[json_field]:
                            point.field(
                                json_field,
                                self._serialize_json_field(metric[json_field]),
                            )

                elif metric_type == "spo2":
                    if "value" in metric:
                        point.field("value", float(metric["value"]))
                    if "minute_data" in metric and metric["minute_data"]:
                        point.field(
                            "minute_data",
                            self._serialize_json_field(metric["minute_data"]),
                        )

                elif metric_type == "hrv":
                    for field in ["rmssd", "coverage", "hf", "lf"]:
                        if field in metric and metric[field] is not None:
                            point.field(field, float(metric[field]))
                    if "minute_data" in metric and metric["minute_data"]:
                        point.field(
                            "minute_data",
                            self._serialize_json_field(metric["minute_data"]),
                        )

                elif metric_type == "br":
                    for field in [
                        "deep_sleep_rate",
                        "rem_sleep_rate",
                        "light_sleep_rate",
                        "full_sleep_rate",
                    ]:
                        if field in metric and metric[field] is not None:
                            point.field(field, float(metric[field]))

                elif metric_type == "azm":
                    for field in [
                        "fat_burn_minutes",
                        "cardio_minutes",
                        "peak_minutes",
                        "active_zone_minutes",
                    ]:
                        if field in metric and metric[field] is not None:
                            point.field(field, float(metric[field]))
                    if "minute_data" in metric and metric["minute_data"]:
                        point.field(
                            "minute_data",
                            self._serialize_json_field(metric["minute_data"]),
                        )

                elif metric_type == "activity":
                    if "value" in metric:
                        point.field("value", float(metric["value"]))

                points.append(point)

            # Write points to InfluxDB
            self.write_api.write(bucket=self.bucket, record=points)
            logger.info(f"Successfully inserted {len(metrics)} {metric_type} metrics")
            return True

        except Exception as e:
            logger.error(f"Error inserting {metric_type} metrics: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def get_last_processed_date(
        self, metric_type: str, user_id: int
    ) -> Optional[datetime]:
        """Get the last processed date for a metric type and user."""
        try:
            query = f"""
            from(bucket: "{self.bucket}")
                |> range(start: -1y)
                |> filter(fn: (r) => r._measurement == "last_processed_dates")
                |> filter(fn: (r) => r.metric_type == "{metric_type}")
                |> filter(fn: (r) => r.user_id == "{user_id}")
                |> filter(fn: (r) => r._field == "last_processed_date")
                |> last()
            """
            query_api = self.client.query_api()
            tables = query_api.query(query, org=self.org)

            for table in tables:
                for record in table.records:
                    # Convert epoch timestamp back to datetime
                    ts = record.get_value()
                    if isinstance(ts, (int, float)):
                        return datetime.fromtimestamp(ts)
                    elif isinstance(ts, str):
                        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    else:
                        return ts

            return None

        except Exception as e:
            logger.error(f"Error getting last processed date: {e}")
            return None

    def update_last_processed_date(
        self, metric_type: str, user_id: int, date: datetime
    ) -> bool:
        """Update the last processed date for a metric type and user."""
        try:
            point = (
                Point("last_processed_dates")
                .tag("metric_type", metric_type)
                .tag("user_id", str(user_id))
                .field("last_processed_date", date.timestamp())
                .time(datetime.now())
            )

            self.write_api.write(bucket=self.bucket, record=point)
            logger.info(f"Updated last processed date for {metric_type}: {date}")
            return True

        except Exception as e:
            logger.error(f"Error updating last processed date: {e}")
            return False
