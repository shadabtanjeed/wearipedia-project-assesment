from datetime import datetime
from typing import Dict, List, Optional, Union, Any, TypeVar, Generic
from pydantic import (
    BaseModel,
    Field,
    field_validator,
)

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


# the metric heart rate contains nested structures
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
    data_points: Optional[List[SpO2DataPoint]] = Field(None, alias="minutes")


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
    data_points: Optional[List[HRVDataPoint]] = None


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
    fat_burn_minutes: int = Field(..., alias="fatBurnActiveZoneMinutes")
    active_zone_minutes: int = Field(..., alias="activeZoneMinutes")


# Active Zone Minutes Metric
class ActiveZoneMinutesMetric(BaseHealthMetric):
    fat_burn_minutes: Optional[int] = None
    active_zone_minutes: Optional[int] = None
    data_points: Optional[List[ActiveZoneMinuteDataPoint]] = None


# A container for time series data that can hold any type of value
# This is useful when we want to store different kinds of measurements over time
# For example:
#  - TimeSeriesData[int] for step counts
#  - TimeSeriesData[float] for heart rates or temperatures
#  - TimeSeriesData[Dict] for complex measurements with multiple values

# T is a "type variable" - it's a placeholder that will be replaced with
# a real type (like int, float, etc.) when someone uses this class
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
            metric_type: Type of metric ('heart_rate', 'steps', etc.)
            data: Dict containing the metric data

        Returns:
            An instance of the appropriate metric class
        """
        timestamp = datetime.fromisoformat(
            data.get("dateTime", "").replace("Z", "+00:00")
        )
        user_id = data.get("user_id")

        # Get device ID using the device manager
        device_id = self.device_manager.get_device_id(data, user_id)

        if metric_type == "activity":
            return ActivityMetric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                value=data.get("value", 0),
            )
        elif metric_type == "heart_rate":
            # Extract heart rate value from the nested structure
            hr_data = data.get("heart_rate_day", [{}])[0]
            intraday_data = hr_data.get("activities-heart-intraday", {})
            dataset = intraday_data.get("dataset", [{}])

            value = dataset[0].get("value", 0) if dataset else 0

            # Get resting heart rate if available
            heart_activities = hr_data.get("activities-heart", [{}])[0]
            heart_values = heart_activities.get("value", {})
            resting_hr = heart_values.get("restingHeartRate")

            return HeartRateMetric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                value=value,
                resting_heart_rate=resting_hr,
            )
        elif metric_type == "spo2":
            minutes = data.get("minutes", [{}])
            value = minutes[0].get("value", 0) if minutes else 0

            return SpO2Metric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                value=value,
                data_points=minutes,
            )
        elif metric_type == "hrv":
            hrv_data = data.get("hrv", [{}])[0]
            minutes = hrv_data.get("minutes", [{}])
            value = minutes[0].get("value", {}) if minutes else {}

            return HRVMetric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                rmssd=value.get("rmssd"),
                coverage=value.get("coverage"),
                hf=value.get("hf"),
                lf=value.get("lf"),
            )
        elif metric_type == "breathing_rate":
            br_data = data.get("br", [{}])[0]
            value = br_data.get("value", {})

            deep_sleep = value.get("deepSleepSummary", {}).get("breathingRate")
            rem_sleep = value.get("remSleepSummary", {}).get("breathingRate")
            light_sleep = value.get("lightSleepSummary", {}).get("breathingRate")
            full_sleep = value.get("fullSleepSummary", {}).get("breathingRate")

            return BreathingRateMetric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                deep_sleep_rate=deep_sleep,
                rem_sleep_rate=rem_sleep,
                light_sleep_rate=light_sleep,
                full_sleep_rate=full_sleep,
            )
        elif metric_type == "active_zone_minutes":
            azm_data = data.get("activities-active-zone-minutes-intraday", [{}])[0]
            minutes = azm_data.get("minutes", [{}])
            value = minutes[0].get("value", {}) if minutes else {}

            return ActiveZoneMinutesMetric(
                timestamp=timestamp,
                user_id=user_id,
                device_id=device_id,
                fat_burn_minutes=value.get("fatBurnActiveZoneMinutes"),
                active_zone_minutes=value.get("activeZoneMinutes"),
            )
        else:
            # Default case - return base class with original data
            return BaseHealthMetric(
                timestamp=timestamp, user_id=user_id, device_id=device_id, **data
            )
