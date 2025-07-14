import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger("SourceAdapter")


class SourceAdapter:
    """Base class for source data adapters"""

    def get_data(
        self,
        metric_type: str,
        start_date: datetime,
        end_date: datetime,
        user_id: str = "1",
    ) -> List[Dict]:
        """Get data for a specific metric type and date range."""
        raise NotImplementedError("Subclasses must implement get_data")

    def check_data_availability(self, metric_type: str, user_id: str) -> bool:
        """Check if data is available for a specific metric type and user."""
        raise NotImplementedError("Subclasses must implement check_data_availability")


class SyntheticFitbitAdapter(SourceAdapter):
    """Adapter for synthetic Fitbit data stored in JSON files"""

    def __init__(self, data_dir: str):
        """Initialize adapter with path to data directory."""
        self.data_dir = data_dir
        # Flag to indicate flat record processing
        self.flat_records = False
        logger.info(f"Using data directory: {data_dir}")
        logger.info(
            f"Initialized SyntheticFitbitAdapter with data directory: {data_dir}"
        )

    def get_file_path(self, metric_type: str, user_id: str) -> str:
        """Get the file path for a specific metric type and user."""
        # Map metric types to file name prefixes
        type_to_prefix = {
            "heart_rate": "hr",  # Allow both heart_rate and hr
            "hr": "hr",
            "spo2": "spo2",
            "hrv": "hrv",
            "breathing_rate": "br",
            "br": "br",
            "active_zone_minutes": "azm",
            "azm": "azm",
            "activity": "activity",
        }

        prefix = type_to_prefix.get(metric_type, metric_type)
        file_name = f"{prefix}_user{user_id}_modified.json"
        file_path = os.path.join(self.data_dir, file_name)

        return file_path

    def check_data_availability(self, metric_type: str, user_id: str) -> bool:
        """Check if data file is available for this metric type and user."""
        file_path = self.get_file_path(metric_type, user_id)
        exists = os.path.exists(file_path)
        if not exists:
            logger.warning(f"Data file not found: {file_path}")
        return exists

    def get_data(
        self,
        metric_type: str,
        start_date: datetime,
        end_date: datetime,
        user_id: str = "1",
    ) -> List[Dict]:
        """Get synthetic data for a specific metric type and date range."""
        file_path = self.get_file_path(metric_type, user_id)

        if not os.path.exists(file_path):
            logger.warning(f"Data file not found: {file_path}")
            return []

        try:
            with open(file_path, "r") as f:
                all_data = json.load(f)

            # Filter data based on date if needed
            if start_date and end_date:
                # For different metrics, date filtering will be handled differently
                filtered_data = self._filter_data_by_date(
                    metric_type, all_data, start_date, end_date
                )
                logger.info(
                    f"Retrieved {len(filtered_data)} records for {metric_type} between {start_date.date()} and {end_date.date()}"
                )
                return filtered_data

            logger.info(f"Retrieved {len(all_data)} total records for {metric_type}")
            return all_data
        except Exception as e:
            logger.error(f"Error reading data file {file_path}: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return []

    def _filter_data_by_date(
        self,
        metric_type: str,
        data: List[Dict],
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict]:
        """Filter data by date based on metric type."""
        # Convert dates to string format (YYYY-MM-DD) for comparison
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        filtered_data = []

        for record in data:
            record_date = None

            # Extract date based on metric type and structure
            if metric_type == "activity" or metric_type == "spo2":
                # Activity and SPO2 have dateTime directly in the record
                if "dateTime" in record:
                    record_date = record["dateTime"].split("T")[
                        0
                    ]  # Extract date part only

            elif metric_type == "heart_rate" or metric_type == "hr":
                # Heart rate has nested structure
                if "heart_rate_day" in record and record["heart_rate_day"]:
                    heart_data = record["heart_rate_day"][0]
                    if (
                        "activities-heart" in heart_data
                        and heart_data["activities-heart"]
                    ):
                        activities_heart = heart_data["activities-heart"][0]
                        if "dateTime" in activities_heart:
                            record_date = activities_heart["dateTime"].split("T")[0]

            elif metric_type == "hrv":
                # HRV has minutes data with timestamps
                if "hrv" in record and record["hrv"]:
                    hrv_data = record["hrv"][0]
                    if "minutes" in hrv_data and hrv_data["minutes"]:
                        first_minute = hrv_data["minutes"][0]
                        if "minute" in first_minute:
                            record_date = first_minute["minute"].split("T")[0]

            elif metric_type == "breathing_rate" or metric_type == "br":
                # Breathing rate has nested data
                if "br" in record and record["br"]:
                    br_data = record["br"][0]
                    if "dateTime" in br_data:
                        record_date = br_data["dateTime"].split("T")[0]

            elif metric_type == "active_zone_minutes" or metric_type == "azm":
                # AZM has nested data
                if "activities-active-zone-minutes-intraday" in record:
                    azm_data = record["activities-active-zone-minutes-intraday"]
                    if azm_data and "dateTime" in azm_data[0]:
                        record_date = azm_data[0]["dateTime"].split("T")[0]

            # If we found a date and it matches the range, include it
            if record_date and start_date_str <= record_date <= end_date_str:
                filtered_data.append(record)

        logger.info(
            f"Filtered {len(filtered_data)} records out of {len(data)} for {metric_type} between {start_date_str} and {end_date_str}"
        )
        return filtered_data

    def _extract_date_from_record(
        self, record: Dict, metric_type: str
    ) -> Optional[datetime]:
        """Extract date from record based on metric type."""
        if metric_type == "activity" or metric_type == "spo2":
            if "dateTime" in record:
                return datetime.fromisoformat(record["dateTime"])

        elif metric_type == "heart_rate" or metric_type == "hr":
            if "heart_rate_day" in record and record["heart_rate_day"]:
                heart_data = record["heart_rate_day"][0]
                if "activities-heart" in heart_data and heart_data["activities-heart"]:
                    date_str = heart_data["activities-heart"][0].get("dateTime")
                    if date_str:
                        return datetime.fromisoformat(date_str)

        elif metric_type == "hrv":
            if "hrv" in record and record["hrv"]:
                hrv_data = record["hrv"][0]
                if "minutes" in hrv_data and hrv_data["minutes"]:
                    first_minute = hrv_data["minutes"][0]
                    if "minute" in first_minute:
                        date_str = first_minute["minute"].split("T")[0]
                        return datetime.fromisoformat(date_str)

        elif metric_type == "breathing_rate" or metric_type == "br":
            if "br" in record and record["br"]:
                br_data = record["br"][0]
                if "dateTime" in br_data:
                    return datetime.fromisoformat(br_data["dateTime"])

        elif metric_type == "active_zone_minutes" or metric_type == "azm":
            if "activities-active-zone-minutes-intraday" in record:
                azm_data = record["activities-active-zone-minutes-intraday"]
                if azm_data and "dateTime" in azm_data[0]:
                    return datetime.fromisoformat(azm_data[0]["dateTime"])

        return None

    def extract_heart_rate_intraday(self, record: Dict) -> List[Dict]:
        """Extract intraday heart rate readings from a heart rate record."""
        if "heart_rate_day" in record and record["heart_rate_day"]:
            heart_data = record["heart_rate_day"][0]
            if (
                "activities-heart-intraday" in heart_data
                and "dataset" in heart_data["activities-heart-intraday"]
            ):
                return heart_data["activities-heart-intraday"]["dataset"]
        return []

    def extract_heart_rate_zones(self, record: Dict) -> List[Dict]:
        """Extract heart rate zones from a heart rate record."""
        zones = []
        if "heart_rate_day" in record and record["heart_rate_day"]:
            heart_data = record["heart_rate_day"][0]
            if "activities-heart" in heart_data and heart_data["activities-heart"]:
                heart_value = heart_data["activities-heart"][0].get("value", {})
                # Add standard zones
                if "heartRateZones" in heart_value:
                    for zone in heart_value["heartRateZones"]:
                        zone["zone_type"] = "standard"
                        zones.append(zone)
                # Add custom zones
                if "customHeartRateZones" in heart_value:
                    for zone in heart_value["customHeartRateZones"]:
                        zone["zone_type"] = "custom"
                        zones.append(zone)
        return zones

    def extract_resting_heart_rate(self, record: Dict) -> Optional[int]:
        """Extract resting heart rate from a heart rate record."""
        if "heart_rate_day" in record and record["heart_rate_day"]:
            heart_data = record["heart_rate_day"][0]
            if "activities-heart" in heart_data and heart_data["activities-heart"]:
                heart_value = heart_data["activities-heart"][0].get("value", {})
                return heart_value.get("restingHeartRate")
        return None

    def extract_spo2_minutes(self, record: Dict) -> List[Dict]:
        """Extract SpO2 minute readings from a record."""
        if "minutes" in record:
            return record["minutes"]
        return []

    def extract_hrv_minutes(self, record: Dict) -> List[Dict]:
        """Extract HRV minute readings from a record."""
        if "hrv" in record and record["hrv"]:
            hrv_data = record["hrv"][0]
            if "minutes" in hrv_data:
                return hrv_data["minutes"]
        return []

    def extract_azm_minutes(self, record: Dict) -> List[Dict]:
        """Extract Active Zone Minutes from a record."""
        if "activities-active-zone-minutes-intraday" in record:
            azm_data = record["activities-active-zone-minutes-intraday"][0]
            if "minutes" in azm_data:
                return azm_data["minutes"]
        return []

    def extract_breathing_rate_data(self, record: Dict) -> Dict:
        """Extract breathing rate data from a record."""
        result = {"deep": None, "rem": None, "light": None, "full": None}
        if "br" in record and record["br"]:
            br_data = record["br"][0]
            if "value" in br_data:
                value = br_data["value"]
                if (
                    "deepSleepSummary" in value
                    and "breathingRate" in value["deepSleepSummary"]
                ):
                    result["deep"] = value["deepSleepSummary"]["breathingRate"]
                if (
                    "remSleepSummary" in value
                    and "breathingRate" in value["remSleepSummary"]
                ):
                    result["rem"] = value["remSleepSummary"]["breathingRate"]
                if (
                    "lightSleepSummary" in value
                    and "breathingRate" in value["lightSleepSummary"]
                ):
                    result["light"] = value["lightSleepSummary"]["breathingRate"]
                if (
                    "fullSleepSummary" in value
                    and "breathingRate" in value["fullSleepSummary"]
                ):
                    result["full"] = value["fullSleepSummary"]["breathingRate"]
        return result

    def filter_data_for_date(
        self, data: List[Dict], target_date: str, metric_type: str
    ) -> Optional[Dict]:
        """Filter data for a specific date."""
        if not data:
            return None

        # Convert string date to datetime if needed
        if isinstance(target_date, str):
            target_date = datetime.fromisoformat(target_date)

        # Extract just the date part
        target_date_str = target_date.strftime("%Y-%m-%d")

        # Check the structure of the data
        if isinstance(data, list) and data:
            first_item = data[0]

            # Heart Rate format
            if metric_type == "heart_rate" or metric_type == "hr":
                for item in data:
                    if "heart_rate_day" in item:
                        heart_day = item.get("heart_rate_day", [])
                        for day_data in heart_day:
                            if "activities-heart" in day_data:
                                heart_data = day_data["activities-heart"][0]
                                date_str = heart_data.get("dateTime")
                                if date_str == target_date_str:
                                    return day_data
                return None

            # Active Zone Minutes format
            elif metric_type == "active_zone_minutes" or metric_type == "azm":
                for item in data:
                    if "activities-active-zone-minutes-intraday" in item:
                        azm_list = item.get(
                            "activities-active-zone-minutes-intraday", []
                        )
                        for azm_data in azm_list:
                            date_str = azm_data.get("dateTime")
                            if date_str == target_date_str:
                                return azm_data
                return None

            # Breathing Rate format
            elif metric_type == "breathing_rate" or metric_type == "br":
                for item in data:
                    if "br" in item:
                        br_list = item.get("br", [])
                        for br_data in br_list:
                            date_str = br_data.get("dateTime")
                            if date_str == target_date_str:
                                return br_data
                return None

            # HRV format
            elif metric_type == "hrv":
                for item in data:
                    if "hrv" in item:
                        hrv_list = item.get("hrv", [])
                        for hrv_data in hrv_list:
                            if "minutes" in hrv_data and hrv_data["minutes"]:
                                first_minute = hrv_data["minutes"][0]["minute"]
                                date_part = (
                                    first_minute.split("T")[0]
                                    if "T" in first_minute
                                    else None
                                )
                                if date_part == target_date_str:
                                    return hrv_data
                return None

            # Regular format (Activity, SpO2)
            else:
                for item in data:
                    date_str = item.get("dateTime")
                    if date_str == target_date_str:
                        return item
                return None

        return None

    def get_data_structure(self, metric_type: str, user_id: str = "1") -> Dict:
        """Get a representation of the data structure for a specific metric type."""
        file_path = self.get_file_path(metric_type, user_id)

        if not os.path.exists(file_path):
            logger.warning(f"Data file not found: {file_path}")
            return {}

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Get first record as a sample
            if data and isinstance(data, list) and len(data) > 0:
                return {
                    "structure": self._describe_structure(data[0]),
                    "sample": data[0],
                }
            return {}
        except Exception as e:
            logger.error(f"Error reading data file {file_path}: {e}")
            return {}

    def _describe_structure(self, obj, level=0, max_level=3):
        """Recursively describe the structure of an object."""
        if level >= max_level:
            return "..."

        if isinstance(obj, dict):
            return {
                k: self._describe_structure(v, level + 1, max_level)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            if obj and len(obj) > 0:
                return [self._describe_structure(obj[0], level + 1, max_level)]
            return []
        else:
            return type(obj).__name__


class SourceAdapterFactory:
    """Factory for creating source adapters"""

    @staticmethod
    def create_adapter(adapter_type: str, **kwargs) -> SourceAdapter:
        """Create and return a source adapter of the specified type."""
        if adapter_type == "synthetic":
            data_dir = kwargs.get("data_dir", ".")
            return SyntheticFitbitAdapter(data_dir)
        elif adapter_type == "synthetic_flat":
            # Same adapter but with a flag indicating flat record processing
            data_dir = kwargs.get("data_dir", ".")
            adapter = SyntheticFitbitAdapter(data_dir)
            adapter.flat_records = True
            return adapter
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
