from fastapi import APIRouter, HTTPException, Query

from app.controllers.device_controller import get_all_devices, get_device_by_id

router = APIRouter(prefix="/api/devices", tags=["Devices"])


@router.get("/get_all_devices")
async def api_get_all_devices():
    try:
        data = get_all_devices()
        return {
            "success": True,
            "data_count": len(data),
            "data": data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching devices: {str(e)}")


@router.get("/get_device_by_id")
async def api_get_device_by_id(device_id: str = Query(..., description="Device ID")):
    try:
        data = get_device_by_id(device_id)
        if not data:
            raise HTTPException(status_code=404, detail="Device not found")

        return {
            "success": True,
            "data": data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching device: {str(e)}")
