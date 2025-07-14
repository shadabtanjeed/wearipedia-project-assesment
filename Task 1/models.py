from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import json

logger = logging.getLogger("Models")


class BaseHealthMetric:
    """Base class for health metrics"""

    def __init__(self, timestamp: datetime, user_id: int = 1, device_id: str = None):
        self.timestamp = timestamp
        self.user_id = user_id
        self.device_id = device_id or f"fitbit-charge6-{user_id}"  # Default device ID

    def __repr__(self):
        return f"{self.__class__.__name__}(timestamp={self.timestamp}, user_id={self.user_id})"


class HeartRateMetric(BaseHealthMetric):
    """Heart rate metric model"""

    def __init__(
        self,
        timestamp: datetime,
        user_id: int = 1,
        device_id: str = None,
        value: int = 0,
        resting_heart_rate: Optional[int] = None,
        zones: Optional[Dict] = None,
        summary: Optional[Dict] = None,
        intraday: Optional[Dict] = None,
    ):
        super().__init__(timestamp, user_id, device_id)
        self.value = value
        self.resting_heart_rate = resting_heart_rate
        self.zones = zones
        self.summary = summary
        self.intraday = intraday


class SpO2Metric(BaseHealthMetric):
    """SpO2 (oxygen saturation) metric model"""

    def __init__(
        self,
        timestamp: datetime,
        user_id: int = 1,
        device_id: str = None,
        value: float = 0,
        minute_data: Optional[List[Dict]] = None,
    ):
        super().__init__(timestamp, user_id, device_id)
        self.value = value
        self.minute_data = minute_data


class HRVMetric(BaseHealthMetric):
    """Heart Rate Variability metric model"""

    def __init__(
        self,
        timestamp: datetime,
        user_id: int = 1,
        device_id: str = None,
        rmssd: Optional[float] = None,
        coverage: Optional[float] = None,
        hf: Optional[float] = None,
        lf: Optional[float] = None,
        minute_data: Optional[List[Dict]] = None,
    ):
        super().__init__(timestamp, user_id, device_id)
        self.rmssd = rmssd
        self.coverage = coverage
        self.hf = hf  # High frequency power
        self.lf = lf  # Low frequency power
        self.minute_data = minute_data


class BreathingRateMetric(BaseHealthMetric):
    """Breathing rate metric model"""

    def __init__(
        self,
        timestamp: datetime,
        user_id: int = 1,
        device_id: str = None,
        deep_sleep_rate: Optional[float] = None,
        rem_sleep_rate: Optional[float] = None,
        light_sleep_rate: Optional[float] = None,
        full_sleep_rate: Optional[float] = None,
    ):
        super().__init__(timestamp, user_id, device_id)
        self.deep_sleep_rate = deep_sleep_rate
        self.rem_sleep_rate = rem_sleep_rate
        self.light_sleep_rate = light_sleep_rate
        self.full_sleep_rate = full_sleep_rate


class ActiveZoneMinutesMetric(BaseHealthMetric):
    """Active zone minutes metric model"""

    def __init__(
        self,
        timestamp: datetime,
        user_id: int = 1,
        device_id: str = None,
        fat_burn_minutes: int = 0,
        cardio_minutes: int = 0,
        peak_minutes: int = 0,
        active_zone_minutes: int = 0,
        minute_data: Optional[List[Dict]] = None,
    ):
        super().__init__(timestamp, user_id, device_id)
        self.fat_burn_minutes = fat_burn_minutes
        self.cardio_minutes = cardio_minutes
        self.peak_minutes = peak_minutes
        self.active_zone_minutes = active_zone_minutes
        self.minute_data = minute_data


class ActivityMetric(BaseHealthMetric):
    """Activity metric model (steps, distance, etc.)"""

    def __init__(
        self,
        timestamp: datetime,
        user_id: int = 1,
        device_id: str = None,
        value: int = 0,
    ):
        super().__init__(timestamp, user_id, device_id)
        self.value = value


class HealthMetricFactory:
    """Factory for creating health metrics from raw data"""

    def create_metric(self, metric_type: str, data: Dict) -> BaseHealthMetric:
        """Create and return a health metric of the specified type from raw data"""
        # Parse user ID - default to 1 if not present
        user_id = int(data.get("user_id", 1))

        # Parse device ID - use None for default
        device_id = data.get("device_id")

        # Parse timestamp
        timestamp = self._extract_timestamp(metric_type, data)

        # Create appropriate metric object based on type
        if metric_type == "hr":
            # Parse heart rate-specific fields
            heart_data = {}
            intraday_data = {}

            if "heart_rate_day" in data and data["heart_rate_day"]:
                heart_day = data["heart_rate_day"][0]

                # Get activities-heart data
                if "activities-heart" in heart_day and heart_day["activities-heart"]:
                    activities_heart = heart_day["activities-heart"][0]
                    heart_data = activities_heart.get("value", {})

                # Get intraday data
                if "activities-heart-intraday" in heart_day:
                    intraday_data = heart_day["activities-heart-intraday"]

            value = 0
            if (
                intraday_data
                and "dataset" in intraday_data
                and intraday_data["dataset"]
            ):
                # Use the first datapoint value
                value = intraday_data["dataset"][0].get("value", 0)

            resting_hr = heart_data.get("restingHeartRate")

            # Get zone information
            zones = {}
            if "heartRateZones" in heart_data:
                zones = heart_data["heartRateZones"]

            logger.debug(
                f"Created heart rate metric with value: {value}, resting HR: {resting_hr}"
            )

            return HeartRateMetric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                value=value,
                resting_heart_rate=resting_hr,
                zones=zones,
                summary=heart_data,
                intraday=intraday_data,
            )

        elif metric_type == "spo2":
            value = 0
            minute_data = []

            # Direct dateTime and value for daily summary
            value = data.get("value", 0)

            # Get minute-level data if available
            if "minutes" in data:
                minute_data = data["minutes"]

            logger.debug(f"Created SpO2 metric with value: {value}")

            return SpO2Metric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                value=value,
                minute_data=minute_data,
            )

        elif metric_type == "hrv":
            hrv_data = None
            minutes = []

            # Get HRV specific data
            if "hrv" in data and data["hrv"]:
                hrv_data = data["hrv"][0]
                minutes = hrv_data.get("minutes", [])

            # Get first minute values as representative sample or use empty dict
            first_minute = minutes[0] if minutes and len(minutes) > 0 else {}
            first_value = (
                first_minute.get("value", {}) if isinstance(first_minute, dict) else {}
            )

            rmssd = first_value.get("rmssd")
            coverage = first_value.get("coverage")
            hf = first_value.get("hf")
            lf = first_value.get("lf")

            logger.debug(
                f"Created HRV metric with rmssd: {rmssd}, coverage: {coverage}"
            )

            return HRVMetric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                rmssd=rmssd,
                coverage=coverage,
                hf=hf,
                lf=lf,
                minute_data=minutes,
            )

        elif metric_type == "br":
            br_data = None

            # Get breathing rate specific data
            if "br" in data and data["br"]:
                br_data = data["br"][0]

            deep_rate = None
            rem_rate = None
            light_rate = None
            full_rate = None

            if br_data and "value" in br_data:
                value_obj = br_data["value"]
                deep_rate = value_obj.get("deepSleepSummary", {}).get("breathingRate")
                rem_rate = value_obj.get("remSleepSummary", {}).get("breathingRate")
                light_rate = value_obj.get("lightSleepSummary", {}).get("breathingRate")
                full_rate = value_obj.get("fullSleepSummary", {}).get("breathingRate")

            logger.debug(f"Created BR metric with full rate: {full_rate}")

            return BreathingRateMetric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                deep_sleep_rate=deep_rate,
                rem_sleep_rate=rem_rate,
                light_sleep_rate=light_rate,
                full_sleep_rate=full_rate,
            )

        elif metric_type == "azm":
            azm_data = None
            minutes = []

            # Get active zone minutes specific data
            if "activities-active-zone-minutes-intraday" in data:
                azm_array = data["activities-active-zone-minutes-intraday"]
                if azm_array and len(azm_array) > 0:
                    azm_data = azm_array[0]
                    minutes = azm_data.get("minutes", [])

            fat_burn = 0
            cardio = 0
            peak = 0
            active = 0

            # Calculate totals from minute data
            for minute in minutes:
                if "value" in minute:
                    value_obj = minute["value"]
                    fat_burn += value_obj.get("fatBurnActiveZoneMinutes", 0)
                    cardio += value_obj.get("cardioActiveZoneMinutes", 0)
                    peak += value_obj.get("peakActiveZoneMinutes", 0)
                    active += value_obj.get("activeZoneMinutes", 0)

            logger.debug(f"Created AZM metric with active minutes: {active}")

            return ActiveZoneMinutesMetric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                fat_burn_minutes=fat_burn,
                cardio_minutes=cardio,
                peak_minutes=peak,
                active_zone_minutes=active,
                minute_data=minutes,
            )

        elif metric_type == "activity":
            # Activity has a simpler structure
            value = data.get("value", 0)

            logger.debug(f"Created Activity metric with value: {value}")

            return ActivityMetric(
                timestamp=timestamp, user_id=user_id, device_id=device_id, value=value
            )

        else:
            raise ValueError(f"Unknown metric type: {metric_type}")

    def _extract_timestamp(self, metric_type: str, data: Dict) -> datetime:
        """Extract timestamp from data based on metric type"""
        now = datetime.now()

        if metric_type == "activity":
            # Activity has direct dateTime field
            if "dateTime" in data:
                date_str = data["dateTime"]
                # Add time component if missing
                if len(date_str) <= 10:
                    date_str += "T00:00:00"
                try:
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    logger.warning(f"Could not parse timestamp: {date_str}")
                    return now

        elif metric_type == "hr":
            # Heart rate has nested structure
            if "heart_rate_day" in data and data["heart_rate_day"]:
                heart_day = data["heart_rate_day"][0]
                if "activities-heart" in heart_day and heart_day["activities-heart"]:
                    date_str = heart_day["activities-heart"][0].get("dateTime")
                    if date_str:
                        # Add time component if missing
                        if len(date_str) <= 10:
                            date_str += "T00:00:00"
                        try:
                            return datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        except:
                            logger.warning(f"Could not parse timestamp: {date_str}")

        elif metric_type == "spo2":
            # SpO2 has direct dateTime field
            if "dateTime" in data:
                date_str = data["dateTime"]
                # Add time component if missing
                if len(date_str) <= 10:
                    date_str += "T00:00:00"
                try:
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    logger.warning(f"Could not parse timestamp: {date_str}")

            # Try to get from minutes if available
            elif "minutes" in data and data["minutes"] and len(data["minutes"]) > 0:
                minute_str = data["minutes"][0].get("minute", "")
                if minute_str:
                    try:
                        return datetime.fromisoformat(minute_str.replace("Z", "+00:00"))
                    except:
                        logger.warning(
                            f"Could not parse minute timestamp: {minute_str}"
                        )

        elif metric_type == "hrv":
            # HRV has nested structure
            if "hrv" in data and data["hrv"]:
                hrv_data = data["hrv"][0]

                # First try dateTime field directly
                if "dateTime" in hrv_data:
                    date_str = hrv_data["dateTime"]
                    # Add time component if missing
                    if len(date_str) <= 10:
                        date_str += "T00:00:00"
                    try:
                        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except:
                        logger.warning(f"Could not parse timestamp: {date_str}")

                # Then try minutes
                if (
                    "minutes" in hrv_data
                    and hrv_data["minutes"]
                    and len(hrv_data["minutes"]) > 0
                ):
                    minute_str = hrv_data["minutes"][0].get("minute", "")
                    if minute_str:
                        try:
                            return datetime.fromisoformat(
                                minute_str.replace("Z", "+00:00")
                            )
                        except:
                            logger.warning(
                                f"Could not parse minute timestamp: {minute_str}"
                            )

        elif metric_type == "br":
            # Breathing rate has nested structure
            if "br" in data and data["br"]:
                br_data = data["br"][0]
                if "dateTime" in br_data:
                    date_str = br_data["dateTime"]
                    # Add time component if missing
                    if len(date_str) <= 10:
                        date_str += "T00:00:00"
                    try:
                        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except:
                        logger.warning(f"Could not parse timestamp: {date_str}")

        elif metric_type == "azm":
            # Active zone minutes has nested structure
            if "activities-active-zone-minutes-intraday" in data:
                azm_array = data["activities-active-zone-minutes-intraday"]
                if azm_array and len(azm_array) > 0:
                    azm_data = azm_array[0]
                    if "dateTime" in azm_data:
                        date_str = azm_data["dateTime"]
                        # Add time component if missing
                        if len(date_str) <= 10:
                            date_str += "T00:00:00"
                        try:
                            return datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                        except:
                            logger.warning(f"Could not parse timestamp: {date_str}")

                    # Try to get from minutes if available
                    if (
                        "minutes" in azm_data
                        and azm_data["minutes"]
                        and len(azm_data["minutes"]) > 0
                    ):
                        minute_str = azm_data["minutes"][0].get("minute", "")
                        if minute_str:
                            try:
                                return datetime.fromisoformat(
                                    minute_str.replace("Z", "+00:00")
                                )
                            except:
                                logger.warning(
                                    f"Could not parse minute timestamp: {minute_str}"
                                )

        # Default to current time if no timestamp found
        logger.warning(
            f"Could not extract timestamp for {metric_type}, using current time"
        )
        return now
