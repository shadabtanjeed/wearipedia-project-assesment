import os
import json
from abc import ABC, abstractmethod
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SourceAdapter")


# base class
class SourceAdapter(ABC):
    @abstractmethod
    # Retrieve data for the specified metric type and date range.
    def get_data(
        self,
        metric_type: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:

        pass

    # Returns list of supported metric types by this adapter.
    @abstractmethod
    def get_supported_metrics(self) -> List[str]:
        pass


# Adapter for synthetic Fitbit data stored as JSON files.
class SyntheticFitbitAdapter(SourceAdapter):
    # Mapping of metric types to file name patterns
    METRIC_FILE_MAPPING = {
        "heart_rate": "hr_user{}_modified.json",
        "activity": "activity_user{}_modified.json",
        "spo2": "spo2_user{}_modified.json",
        "hrv": "hrv_user{}_modified.json",
        "breathing_rate": "br_user{}_modified.json",
        "active_zone_minutes": "azm_user{}_modified.json",
    }

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        logger.info(
            f"Initialized SyntheticFitbitAdapter with data directory: {data_dir}"
        )

    def get_supported_metrics(self) -> List[str]:
        return list(self.METRIC_FILE_MAPPING.keys())

    def get_data(
        self,
        metric_type: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if end_date is None:
            end_date = start_date

        if metric_type not in self.METRIC_FILE_MAPPING:
            raise ValueError(f"Unsupported metric type: {metric_type}")

        # if user_id is not provided, default to "1"
        user = user_id if user_id else "1"

        file_name = self.METRIC_FILE_MAPPING[metric_type].format(user)
        file_path = os.path.join(self.data_dir, file_name)

        try:
            if not os.path.exists(file_path):
                logger.warning(f"Data file not found: {file_path}")
                return []

            with open(file_path, "r") as f:
                all_data = json.load(f)

            # Add user_id to each record if not present
            for record in all_data:
                if "user_id" not in record:
                    record["user_id"] = int(user)

            # Filter data by date range
            # this works if dateTime is in ISO format
            filtered_data = [
                record
                for record in all_data
                if self._is_in_date_range(
                    record.get("dateTime", ""), start_date, end_date
                )
            ]

            logger.info(
                f"Retrieved {len(filtered_data)} records for {metric_type} between "
                f"{start_date.date()} and {end_date.date()}"
            )

            return filtered_data

        except Exception as e:
            logger.error(f"Error retrieving data for {metric_type}: {str(e)}")
            return []

    def _is_in_date_range(
        self, date_str: str, start_date: datetime, end_date: datetime
    ) -> bool:
        if not date_str:
            return False

        try:
            # Handle ISO format with timezone
            date_str = date_str.replace("Z", "+00:00")
            record_date = datetime.fromisoformat(date_str).date()
            return start_date.date() <= record_date <= end_date.date()
        except (ValueError, TypeError):
            logger.warning(f"Invalid date format: {date_str}")
            return False


# Factory for creating source adapters based on device type.
class SourceAdapterFactory:
    @staticmethod
    def get_adapter(device_type: str, **kwargs) -> SourceAdapter:
        device_type = device_type.lower()

        if device_type == "fitbit":

            # For now, we're using the synthetic data adapter
            data_dir = kwargs.get("data_dir", os.path.join("Data", "Modified Data"))
            return SyntheticFitbitAdapter(data_dir)
        else:
            raise ValueError(f"Unsupported device type: {device_type}")
