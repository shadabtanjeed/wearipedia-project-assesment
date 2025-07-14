from typing import Dict, Any
import logging

logger = logging.getLogger("DeviceManager")


class DeviceManager:
    """
    Manages device information during data ingestion.
    Handles both explicit device IDs (future case) and default assignments (current case).
    """

    def __init__(self, default_device_type="fitbit", default_model="charge6"):
        self.default_device_type = default_device_type
        self.default_model = default_model

    def get_device_id(self, data: Dict[str, Any], user_id: int) -> str:
        """
        Extract or generate device ID from data.

        Strategy:
        1. Try to get device_id directly from data (future case)
        2. If not found and it's a Fitbit Charge 6, use fixed device ID "1"
        3. Otherwise, generate a default device ID based on user_id

        Args:
            data: The raw data dictionary
            user_id: The user ID for this data point

        Returns:
            A device ID string
        """
        # First, try to extract device information from the data
        # This handles the future case where device info is included
        device_id = data.get("device_id")
        if device_id:
            logger.debug(f"Found device_id in data: {device_id}")
            return device_id

        # Device type might be provided separately
        device_type = data.get("device_type", self.default_device_type)
        device_model = data.get("device_model", self.default_model)

        # For Fitbit Charge 6, use fixed device ID "1"
        if device_type.lower() == "fitbit" and "charge" in device_model.lower():
            logger.debug(f"Using fixed device ID '1' for Fitbit Charge 6")
            return "1"

        # For other devices, generate a deterministic device ID
        generated_id = f"{device_type}-{device_model}-{user_id}"
        logger.debug(f"Generated device_id: {generated_id}")

        return generated_id
