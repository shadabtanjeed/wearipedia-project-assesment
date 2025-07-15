from fastapi import APIRouter, HTTPException, Query

from app.controllers.user_controller import (
    get_all_users,
    get_user_by_id,
    get_user_devices,
)

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/get_all_users")
async def api_get_all_users():
    try:
        data = get_all_users()
        return {
            "success": True,
            "data_count": len(data),
            "data": data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


@router.get("/get_user_by_id")
async def api_get_user_by_id(user_id: int = Query(..., description="User ID")):
    try:
        data = get_user_by_id(user_id)
        if not data:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "data": data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


@router.get("/get_user_devices")
async def api_get_user_devices(user_id: int = Query(..., description="User ID")):
    try:
        data = get_user_devices(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "data_count": len(data),
            "data": data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching user devices: {str(e)}"
        )
