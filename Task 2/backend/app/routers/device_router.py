from fastapi import APIRouter, HTTPException, Query
import logging

from app.controllers.device_controller import get_all_devices, get_device_by_id

router = APIRouter(prefix="/api/devices", tags=["Devices"])
logger = logging.getLogger("app")


@router.get("/get_all_devices")
async def api_get_all_devices():
    try:
        data = get_all_devices()

        warning_message = None
        if not data:
            warning_message = "No devices found in the database"

        response = {
            "success": True,
            "data_count": len(data),
            "data": data,
        }

        if warning_message:
            response["warning"] = warning_message

        return response
    except Exception as e:
        import traceback

        logger.error(f"Error in api_get_all_devices: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching devices. Please try again later.",
        )


@router.get("/get_device_by_id")
async def api_get_device_by_id(device_id: str = Query(..., description="Device ID")):
    try:
        data = get_device_by_id(device_id)
        if not data:
            raise HTTPException(
                status_code=404, detail=f"Device with ID {device_id} not found"
            )

        return {
            "success": True,
            "data": data,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        logger.error(f"Error in api_get_device_by_id: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching device. Please try again later.",
        )
