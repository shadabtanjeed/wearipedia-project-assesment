from fastapi import APIRouter, HTTPException, Query
import logging

from app.controllers.user_controller import (
    get_all_users,
    get_user_by_id,
    get_user_devices,
)

router = APIRouter(prefix="/api/users", tags=["Users"])
logger = logging.getLogger("app")


@router.get("/get_all_users")
async def api_get_all_users():
    try:
        data = get_all_users()

        warning_message = None
        if not data:
            warning_message = "No users found in the database"

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

        logger.error(f"Error in api_get_all_users: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching users. Please try again later.",
        )


@router.get("/get_user_by_id")
async def api_get_user_by_id(user_id: int = Query(..., description="User ID")):
    try:
        data = get_user_by_id(user_id)
        if not data:
            raise HTTPException(
                status_code=404, detail=f"User with ID {user_id} not found"
            )

        return {
            "success": True,
            "data": data,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        logger.error(f"Error in api_get_user_by_id: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching user. Please try again later.",
        )


@router.get("/get_user_devices")
async def api_get_user_devices(user_id: int = Query(..., description="User ID")):
    try:
        data = get_user_devices(user_id)

        warning_message = None
        if not data:
            warning_message = f"No devices found for user {user_id}"

        response = {
            "success": True,
            "user_id": user_id,
            "data_count": len(data),
            "data": data,
        }

        if warning_message:
            response["warning"] = warning_message

        return response
    except Exception as e:
        import traceback

        logger.error(f"Error in api_get_user_devices: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching devices for user {user_id}. Please try again later.",
        )
