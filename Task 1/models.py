import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger("Models")


def convert_to_utc(timestamp_input) -> datetime:
    """Convert timestamp to UTC datetime (timezone-naive for database storage)"""
    try:
        # Handle different input types
        if isinstance(timestamp_input, str):
            # Parse string timestamp
            if "T" in timestamp_input:
                # ISO format: "2024-01-01T00:00:00" or "2024-01-01T00:00:00.000"
                if "." in timestamp_input:
                    dt = datetime.fromisoformat(timestamp_input.replace(".000", ""))
                else:
                    dt = datetime.fromisoformat(timestamp_input)
            else:
                # Date only format: "2024-01-01"
                dt = datetime.strptime(timestamp_input, "%Y-%m-%d")
        elif isinstance(timestamp_input, datetime):
            dt = timestamp_input
        else:
            logger.error(f"Unsupported timestamp type: {type(timestamp_input)}")
            return None

        # If timezone-naive, assume it's UTC (since synthetic data is UTC)
        if dt.tzinfo is None:
            return dt

        # Convert to UTC and remove timezone info for storage
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception as e:
        logger.error(f"Error converting timestamp {timestamp_input} to UTC: {e}")
        return None


class HealthMetric:
    def __init__(self, metric_type: str, user_id: int, device_id: Optional[str] = None):
        self.metric_type = metric_type
        self.user_id = user_id
        self.device_id = device_id
        self.timestamp = None

    def set_timestamp(self, timestamp):
        """Set timestamp, ensuring it's converted to UTC"""
        self.timestamp = convert_to_utc(timestamp)

    def get_flat_records(self):
        """Return list of flattened records for database insertion"""
        raise NotImplementedError("Subclasses must implement get_flat_records")


class HeartRateMetric(HealthMetric):
    def __init__(self, user_id, device_id=None):
        super().__init__("heart_rate", user_id, device_id)
        self.value = None
        self.resting_heart_rate = None
        self.zones = []
        self.intraday = []
        self.date = None

    def set_data(self, data):
        if "activities-heart" in data:
            heart_data = data["activities-heart"][0]
            self.date = heart_data["dateTime"]
            self.timestamp = convert_to_utc(self.date)

            if "value" in heart_data and isinstance(heart_data["value"], dict):
                if "restingHeartRate" in heart_data["value"]:
                    self.resting_heart_rate = heart_data["value"]["restingHeartRate"]

                if "heartRateZones" in heart_data["value"]:
                    self.zones = heart_data["value"]["heartRateZones"]

        if (
            "activities-heart-intraday" in data
            and "dataset" in data["activities-heart-intraday"]
        ):
            self.intraday = data["activities-heart-intraday"]["dataset"]

    def get_flat_records(self):
        """Return flattened records for database insertion"""
        records = []

        # Process heart rate intraday data
        for entry in self.intraday:
            try:
                time_str = entry["time"]
                value = entry["value"]

                # Create timestamp by combining date and time, then convert to UTC
                if self.date:
                    timestamp_str = f"{self.date}T{time_str}"
                    timestamp = convert_to_utc(timestamp_str)

                    if timestamp:
                        records.append(
                            {
                                "table": "heart_rate",
                                "user_id": self.user_id,
                                "device_id": self.device_id,
                                "timestamp": timestamp,
                                "value": value,
                                "resting_heart_rate": self.resting_heart_rate,
                            }
                        )
            except (KeyError, ValueError) as e:
                logger.error(f"Error processing heart rate intraday data: {e}")

        # If no intraday data but we have a date, create at least one record
        if not records and self.date:
            utc_timestamp = convert_to_utc(self.date)
            if utc_timestamp:
                records.append(
                    {
                        "table": "heart_rate",
                        "user_id": self.user_id,
                        "device_id": self.device_id,
                        "timestamp": utc_timestamp,
                        "value": None,
                        "resting_heart_rate": self.resting_heart_rate,
                    }
                )

        # Process heart rate zones
        for zone in self.zones:
            try:
                utc_timestamp = (
                    convert_to_utc(self.date) if self.date else self.timestamp
                )
                if utc_timestamp:
                    records.append(
                        {
                            "table": "heart_rate_zones",
                            "user_id": self.user_id,
                            "device_id": self.device_id,
                            "timestamp": utc_timestamp,
                            "zone_name": zone.get("name"),
                            "min_hr": zone.get("min"),
                            "max_hr": zone.get("max"),
                            "minutes": zone.get("minutes"),
                            "calories_out": zone.get("caloriesOut"),
                        }
                    )
            except (KeyError, ValueError) as e:
                logger.error(f"Error processing heart rate zone: {e}")

        return records


class SpO2Metric(HealthMetric):
    def __init__(self, user_id, device_id=None):
        super().__init__("spo2", user_id, device_id)
        self.date = None
        self.minutes = []

    def set_data(self, data):
        if "dateTime" in data:
            self.date = data["dateTime"]
        if "minutes" in data:
            self.minutes = data["minutes"]

    def get_flat_records(self):
        records = []

        for minute_data in self.minutes:
            try:
                timestamp = convert_to_utc(minute_data["minute"])
                value = minute_data["value"]

                if timestamp:
                    records.append(
                        {
                            "table": "spo2",
                            "user_id": self.user_id,
                            "device_id": self.device_id,
                            "timestamp": timestamp,
                            "value": value,
                        }
                    )
            except (KeyError, ValueError) as e:
                logger.error(f"Error processing SpO2 minute data: {e}")

        return records


class HRVMetric(HealthMetric):
    def __init__(self, user_id, device_id=None):
        super().__init__("hrv", user_id, device_id)
        self.minutes = []

    def set_data(self, data):
        if "minutes" in data:
            self.minutes = data["minutes"]

    def get_flat_records(self):
        records = []

        for minute_data in self.minutes:
            try:
                timestamp = convert_to_utc(minute_data["minute"])
                value = minute_data.get("value", {})

                if timestamp:
                    records.append(
                        {
                            "table": "hrv",
                            "user_id": self.user_id,
                            "device_id": self.device_id,
                            "timestamp": timestamp,
                            "rmssd": value.get("rmssd"),
                            "coverage": value.get("coverage"),
                            "hf": value.get("hf"),
                            "lf": value.get("lf"),
                        }
                    )
            except (KeyError, ValueError) as e:
                logger.error(f"Error processing HRV minute data: {e}")

        return records


class BreathingRateMetric(HealthMetric):
    def __init__(self, user_id, device_id=None):
        super().__init__("breathing_rate", user_id, device_id)
        self.date = None
        self.deep_sleep_rate = None
        self.rem_sleep_rate = None
        self.light_sleep_rate = None
        self.full_sleep_rate = None

    def set_data(self, data):
        if "dateTime" in data:
            self.date = data["dateTime"]
            self.timestamp = convert_to_utc(data["dateTime"])
        if "value" in data:
            value = data["value"]
            if (
                "deepSleepSummary" in value
                and "breathingRate" in value["deepSleepSummary"]
            ):
                self.deep_sleep_rate = value["deepSleepSummary"]["breathingRate"]
            if (
                "remSleepSummary" in value
                and "breathingRate" in value["remSleepSummary"]
            ):
                self.rem_sleep_rate = value["remSleepSummary"]["breathingRate"]
            if (
                "lightSleepSummary" in value
                and "breathingRate" in value["lightSleepSummary"]
            ):
                self.light_sleep_rate = value["lightSleepSummary"]["breathingRate"]
            if (
                "fullSleepSummary" in value
                and "breathingRate" in value["fullSleepSummary"]
            ):
                self.full_sleep_rate = value["fullSleepSummary"]["breathingRate"]

    def get_flat_records(self):
        return (
            [
                {
                    "table": "breathing_rate",
                    "user_id": self.user_id,
                    "device_id": self.device_id,
                    "timestamp": self.timestamp,
                    "deep_sleep_rate": self.deep_sleep_rate,
                    "rem_sleep_rate": self.rem_sleep_rate,
                    "light_sleep_rate": self.light_sleep_rate,
                    "full_sleep_rate": self.full_sleep_rate,
                }
            ]
            if self.timestamp
            else []
        )


class ActiveZoneMinutesMetric(HealthMetric):
    def __init__(self, user_id, device_id=None):
        super().__init__("active_zone_minutes", user_id, device_id)
        self.date = None
        self.minutes = []

    def set_data(self, data):
        if "dateTime" in data:
            self.date = data["dateTime"]
        if "minutes" in data:
            self.minutes = data["minutes"]

    def get_flat_records(self):
        records = []

        for minute_data in self.minutes:
            try:
                minute_str = minute_data["minute"]
                # Handle different time formats
                if "T" in minute_str:
                    timestamp = convert_to_utc(minute_str)
                else:
                    # Assuming format like "08:30:00" with date from self.date
                    timestamp_str = f"{self.date}T{minute_str}"
                    timestamp = convert_to_utc(timestamp_str)

                value = minute_data.get("value", {})

                if timestamp:
                    records.append(
                        {
                            "table": "active_zone_minutes",
                            "user_id": self.user_id,
                            "device_id": self.device_id,
                            "timestamp": timestamp,
                            "fat_burn_minutes": value.get(
                                "fatBurnActiveZoneMinutes", 0
                            ),
                            "cardio_minutes": value.get("cardioActiveZoneMinutes", 0),
                            "peak_minutes": value.get("peakActiveZoneMinutes", 0),
                            "active_zone_minutes": value.get("activeZoneMinutes", 0),
                        }
                    )
            except (KeyError, ValueError) as e:
                logger.error(f"Error processing AZM minute data: {e}")

        return records


class ActivityMetric(HealthMetric):
    def __init__(self, user_id, device_id=None):
        super().__init__("activity", user_id, device_id)
        self.date = None
        self.value = None

    def set_data(self, data):
        if "dateTime" in data:
            self.date = data["dateTime"]
            self.timestamp = convert_to_utc(data["dateTime"])
        if "value" in data:
            self.value = data["value"]

    def get_flat_records(self):
        return (
            [
                {
                    "table": "activity",
                    "user_id": self.user_id,
                    "device_id": self.device_id,
                    "timestamp": self.timestamp,
                    "value": self.value,
                }
            ]
            if self.timestamp
            else []
        )


class HealthMetricFactory:
    @staticmethod
    def create_metric(metric_type: str, user_id: int, device_id: Optional[str] = None):
        if metric_type == "heart_rate":
            return HeartRateMetric(user_id, device_id)
        elif metric_type == "spo2":
            return SpO2Metric(user_id, device_id)
        elif metric_type == "hrv":
            return HRVMetric(user_id, device_id)
        elif metric_type == "breathing_rate":
            return BreathingRateMetric(user_id, device_id)
        elif metric_type == "active_zone_minutes":
            return ActiveZoneMinutesMetric(user_id, device_id)
        elif metric_type == "activity":
            return ActivityMetric(user_id, device_id)
        else:
            raise ValueError(f"Unknown metric type: {metric_type}")
