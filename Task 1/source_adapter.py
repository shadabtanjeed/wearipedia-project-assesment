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
        logger.info(f"Using data directory: {data_dir}")
        logger.info(
            f"Initialized SyntheticFitbitAdapter with data directory: {data_dir}"
        )

    def get_file_path(self, metric_type: str, user_id: str) -> str:
        """Get the file path for a specific metric type and user with explicit handling for naming conflicts."""
        # Map metric types to file name prefixes
        type_to_prefix = {
            "heart_rate": "hr",  # heart_rate -> hr in filenames
            "hr": "hr",  # hr is an alias for heart_rate
            "spo2": "spo2",  # spo2 keeps its name
            "hrv": "hrv",  # hrv keeps its name (important!)
            "breathing_rate": "br",  # breathing_rate -> br in filenames
            "br": "br",  # br is an alias for breathing_rate
            "active_zone_minutes": "azm",  # active_zone_minutes -> azm in filenames
            "azm": "azm",  # azm is an alias for active_zone_minutes
            "activity": "activity",  # activity keeps its name
        }

        # Get prefix based on metric_type
        prefix = type_to_prefix.get(metric_type, metric_type)

        # Construct file path
        file_name = f"{prefix}_user{user_id}_modified.json"
        file_path = os.path.join(self.data_dir, file_name)

        # For debugging
        logger.debug(f"File path for {metric_type} (user {user_id}): {file_path}")
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

            # Filter data by date range if possible
            if start_date and end_date:
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
        if metric_type == "activity":
            if "dateTime" in record:
                return datetime.fromisoformat(record["dateTime"])
        elif metric_type == "heart_rate" or metric_type == "hr":
            if "heart_rate_day" in record and record["heart_rate_day"]:
                heart_data = record["heart_rate_day"][0]
                if "activities-heart" in heart_data and heart_data["activities-heart"]:
                    date_str = heart_data["activities-heart"][0].get("dateTime")
                    if date_str:
                        return datetime.fromisoformat(date_str)
        # Add more metric types as needed
        return None


class SourceAdapterFactory:
    """Factory for creating source adapters"""

    @staticmethod
    def create_adapter(adapter_type: str, **kwargs) -> SourceAdapter:
        """Create and return a source adapter of the specified type."""
        if adapter_type == "synthetic":
            data_dir = kwargs.get("data_dir", ".")
            return SyntheticFitbitAdapter(data_dir)
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
