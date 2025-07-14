from datetime import datetime
from typing import Dict, List, Optional, Union, Any, TypeVar, Generic
from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

import logging
import json

logger = logging.getLogger("Models")

from device_manager import DeviceManager


class User(BaseModel):
    user_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


# For storing device information for future expansion
class Device(BaseModel):
    device_id: str
    user_id: int
    device_type: str  # basically the manufacturer
    model: Optional[str] = None
    registered_at: datetime = Field(default_factory=datetime.now)


# Base class for all health metrics
class BaseHealthMetric(BaseModel):
    timestamp: datetime
    user_id: int
    device_id: Optional[str] = None

    # this allows for extra fields that might be added in the future
    class Config:
        extra = "allow"


class ActivityMetric(BaseHealthMetric):
    value: int


# Heart Rate Zone is one of such nested structures
class HeartRateZone(BaseModel):
    calories_out: float = Field(..., alias="caloriesOut")
    max: int
    min: int
    minutes: int
    name: str


class HeartRateMetric(BaseHealthMetric):
    value: int
    resting_heart_rate: Optional[int] = None
    zones: Optional[List[HeartRateZone]] = None
    summary: Optional[Dict] = None  # Store activities-heart as JSONB
    intraday: Optional[Dict] = None  # Store activities-heart-intraday as JSONB


# Heart Rate Dataset Entry
class HeartRateDataPoint(BaseModel):
    time: str
    value: int


# SpO2 Data Point
class SpO2DataPoint(BaseModel):
    minute: str
    value: float


# SpO2 Metric
class SpO2Metric(BaseHealthMetric):
    value: float
    minute_data: Optional[List[Dict]] = Field(None, alias="minutes")  # Store as JSONB


# HRV Data Point
class HRVDataPoint(BaseModel):
    minute: str
    rmssd: float
    coverage: float
    hf: float
    lf: float


# Heart Rate Variability Metric
class HRVMetric(BaseHealthMetric):
    rmssd: Optional[float] = None
    coverage: Optional[float] = None
    hf: Optional[float] = None
    lf: Optional[float] = None
    minute_data: Optional[List[Dict]] = None  # Store as JSONB


# Breathing Rate Summary
class BreathingRateSummary(BaseModel):
    breathing_rate: float = Field(..., alias="breathingRate")


# Breathing Rate Metric
class BreathingRateMetric(BaseHealthMetric):
    deep_sleep_rate: Optional[float] = None
    rem_sleep_rate: Optional[float] = None
    light_sleep_rate: Optional[float] = None
    full_sleep_rate: Optional[float] = None

    @field_validator("*", mode="before")
    def extract_breathing_rates(cls, v, info):
        if isinstance(v, dict) and "breathingRate" in v:
            return v["breathingRate"]
        return v


# Active Zone Minute Data Point
class ActiveZoneMinuteDataPoint(BaseModel):
    minute: str
    fat_burn_minutes: Optional[int] = Field(None, alias="fatBurnActiveZoneMinutes")
    cardio_minutes: Optional[int] = Field(None, alias="cardioActiveZoneMinutes")
    peak_minutes: Optional[int] = Field(None, alias="peakActiveZoneMinutes")
    active_zone_minutes: int = Field(..., alias="activeZoneMinutes")


# Active Zone Minutes Metric
class ActiveZoneMinutesMetric(BaseHealthMetric):
    fat_burn_minutes: Optional[int] = None
    cardio_minutes: Optional[int] = None
    peak_minutes: Optional[int] = None
    active_zone_minutes: Optional[int] = None
    minute_data: Optional[List[Dict]] = None  # Store as JSONB


# A container for time series data that can hold any type of value
T = TypeVar("T")


class TimeSeriesData(BaseModel, Generic[T]):
    timestamp: datetime
    value: T


# Factory for creating appropriate metric objects based on data type
class HealthMetricFactory:
    def __init__(self, default_device_type="fitbit", default_model="charge6"):
        self.device_manager = DeviceManager(
            default_device_type=default_device_type, default_model=default_model
        )

    def create_metric(self, metric_type: str, data: Dict) -> BaseHealthMetric:
        """
        Create the appropriate metric object based on the metric type.

        Args:
            metric_type: Type of metric ('hr', 'steps', etc.)
            data: Dict containing the metric data

        Returns:
            An instance of the appropriate metric class
        """
        # Log the input data for debugging
        if isinstance(data, dict):
            logger.debug(
                f"Creating metric of type {metric_type} with data keys: {', '.join(data.keys())}"
            )
        else:
            logger.debug(
                f"Creating metric of type {metric_type} with non-dict data type: {type(data)}"
            )
            return BaseHealthMetric(
                timestamp=datetime.now(),
                user_id=1,
                device_id=self.device_manager.get_device_id({}, 1),
            )

        # Extract common fields with better error handling
        try:
            # For timestamp, look at different possible fields
            timestamp = None
            if "dateTime" in data:
                dt_str = data["dateTime"]
                # Add time component if missing
                if "T" not in dt_str and len(dt_str) <= 10:
                    dt_str += "T00:00:00"
                timestamp = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            else:
                # Look for nested timestamp fields
                if metric_type == "hr" and "heart_rate_day" in data:
                    hr_data = data.get("heart_rate_day", [{}])[0]
                    activities_heart = hr_data.get("activities-heart", [{}])[0]
                    if "dateTime" in activities_heart:
                        dt_str = activities_heart["dateTime"]
                        if "T" not in dt_str and len(dt_str) <= 10:
                            dt_str += "T00:00:00"
                        timestamp = datetime.fromisoformat(
                            dt_str.replace("Z", "+00:00")
                        )
                elif metric_type == "hrv" and "hrv" in data:
                    hrv_data = data.get("hrv", [{}])[0]
                    if "minutes" in hrv_data and hrv_data["minutes"]:
                        dt_str = hrv_data["minutes"][0].get("minute", "")
                        if dt_str:
                            timestamp = datetime.fromisoformat(
                                dt_str.replace("Z", "+00:00")
                            )
                elif metric_type == "br" and "br" in data:
                    br_data = data.get("br", [{}])[0]
                    if "dateTime" in br_data:
                        dt_str = br_data["dateTime"]
                        if "T" not in dt_str and len(dt_str) <= 10:
                            dt_str += "T00:00:00"
                        timestamp = datetime.fromisoformat(
                            dt_str.replace("Z", "+00:00")
                        )
                elif (
                    metric_type == "azm"
                    and "activities-active-zone-minutes-intraday" in data
                ):
                    azm_data = data.get(
                        "activities-active-zone-minutes-intraday", [{}]
                    )[0]
                    if "dateTime" in azm_data:
                        dt_str = azm_data["dateTime"]
                        if "T" not in dt_str and len(dt_str) <= 10:
                            dt_str += "T00:00:00"
                        timestamp = datetime.fromisoformat(
                            dt_str.replace("Z", "+00:00")
                        )

            # If still no timestamp, use current time
            if not timestamp:
                timestamp = datetime.now()
                logger.warning(
                    f"No timestamp found in data, using current time: {timestamp}"
                )

            user_id = data.get("user_id", 1)  # Default to user 1 if not specified

            # Get device ID using the device manager
            device_id = self.device_manager.get_device_id(data, user_id)

        except Exception as e:
            logger.error(f"Error extracting common fields: {str(e)}")
            logger.error(f"Data: {json.dumps(str(data)[:200])}")
            import traceback

            logger.error(traceback.format_exc())
            # Return a basic metric with default values
            return BaseHealthMetric(
                timestamp=datetime.now(),
                user_id=1,
                device_id=self.device_manager.get_device_id({}, 1),
            )

        try:
            if metric_type == "activity":
                value = data.get("value", 0)
                logger.debug(f"Created activity metric with value: {value}")
                return ActivityMetric(
                    timestamp=timestamp,
                    user_id=user_id,
                    device_id=device_id,
                    value=value,
                )
            elif metric_type == "hr":
                # Extract heart rate value from the nested structure
                hr_data = data.get("heart_rate_day", [{}])[0]
                intraday_data = hr_data.get("activities-heart-intraday", {})
                dataset = intraday_data.get("dataset", [{}])

                value = dataset[0].get("value", 0) if dataset else 0

                # Get resting heart rate if available
                heart_activities = hr_data.get("activities-heart", [{}])[0]
                heart_values = heart_activities.get("value", {})
                resting_hr = heart_values.get("restingHeartRate")

                # Extract zones if available
                zones = heart_values.get("heartRateZones", [])

                logger.debug(
                    f"Created heart rate metric with value: {value}, resting_hr: {resting_hr}"
                )
                return HeartRateMetric(
                    timestamp=timestamp,
                    user_id=user_id,
                    device_id=device_id,
                    value=value,
                    resting_heart_rate=resting_hr,
                    zones=zones,
                    summary=hr_data.get(
                        "activities-heart", []
                    ),  # Store full summary as JSONB
                    intraday=intraday_data,  # Store full intraday data as JSONB
                )
            elif metric_type == "spo2":
                minutes = data.get("minutes", [])
                value = minutes[0].get("value", 0) if minutes else 0

                logger.debug(
                    f"Created SpO2 metric with value: {value}, minute_data count: {len(minutes)}"
                )
                return SpO2Metric(
                    timestamp=timestamp,
                    user_id=user_id,
                    device_id=device_id,
                    value=value,
                    minute_data=minutes,  # Store full minutes array as JSONB
                )
            elif metric_type == "hrv":
                hrv_data = data.get("hrv", [{}])[0]
                minutes = hrv_data.get("minutes", [])
                value = minutes[0].get("value", {}) if minutes else {}

                rmssd = value.get("rmssd")
                coverage = value.get("coverage")
                hf = value.get("hf")
                lf = value.get("lf")

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
                    minute_data=minutes,  # Store full minutes array as JSONB
                )
            elif metric_type == "br":
                br_data = data.get("br", [{}])[0]
                value = br_data.get("value", {})

                deep_sleep = value.get("deepSleepSummary", {}).get("breathingRate")
                rem_sleep = value.get("remSleepSummary", {}).get("breathingRate")
                light_sleep = value.get("lightSleepSummary", {}).get("breathingRate")
                full_sleep = value.get("fullSleepSummary", {}).get("breathingRate")

                logger.debug(
                    f"Created breathing rate metric with deep_sleep_rate: {deep_sleep}"
                )
                return BreathingRateMetric(
                    timestamp=timestamp,
                    user_id=user_id,
                    device_id=device_id,
                    deep_sleep_rate=deep_sleep,
                    rem_sleep_rate=rem_sleep,
                    light_sleep_rate=light_sleep,
                    full_sleep_rate=full_sleep,
                )
            elif metric_type == "azm":
                azm_data = data.get("activities-active-zone-minutes-intraday", [{}])[0]
                minutes = azm_data.get("minutes", [])

                # Get the first minute's values as a representative sample
                value = minutes[0].get("value", {}) if minutes else {}

                fat_burn = value.get("fatBurnActiveZoneMinutes")
                cardio = value.get("cardioActiveZoneMinutes")
                peak = value.get("peakActiveZoneMinutes")
                active = value.get("activeZoneMinutes")

                logger.debug(
                    f"Created AZM metric with fat_burn: {fat_burn}, active_zone_minutes: {active}"
                )
                return ActiveZoneMinutesMetric(
                    timestamp=timestamp,
                    user_id=user_id,
                    device_id=device_id,
                    fat_burn_minutes=fat_burn,
                    cardio_minutes=cardio,
                    peak_minutes=peak,
                    active_zone_minutes=active,
                    minute_data=minutes,  # Store full minutes array as JSONB
                )
            else:
                logger.warning(f"Unknown metric type: {metric_type}")
                return BaseHealthMetric(
                    timestamp=timestamp, user_id=user_id, device_id=device_id, **data
                )
        except Exception as e:
            logger.error(f"Error creating metric of type {metric_type}: {str(e)}")
            logger.error(f"Data: {json.dumps(str(data)[:200])}")
            import traceback

            logger.error(traceback.format_exc())
            return BaseHealthMetric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
            )
