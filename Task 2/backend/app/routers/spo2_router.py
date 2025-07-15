from fastapi import APIRouter, Depends, HTTPException
from typing import Tuple
from datetime import datetime
import logging

from app.controllers.spo2_controller import get_all_spo2_data, get_daily_avg_spo2_data
from app.utils.date_parser import parse_date_parameters

router = APIRouter(prefix="/api/spo2", tags=["SpO2"])
logger = logging.getLogger("app")


@router.get("/get_all_spo2_data")
async def api_get_all_spo2_data(
    params: Tuple[int, datetime, datetime] = Depends(parse_date_parameters),
):
    user_id, start_date, end_date = params

    try:
        data = get_all_spo2_data(user_id, start_date, end_date)

        fallback_used = False
        warning_message = None

        if not data:
            warning_message = (
                f"No SpO2 data found for user {user_id} in the specified time range"
            )

        response = {
            "success": True,
            "parameters": {
                "user_id": user_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "data_count": len(data),
            "data": data,
        }

        if warning_message:
            response["warning"] = warning_message

        if fallback_used:
            response["fallback_used"] = True

        return response
    except ValueError as e:
        if "User" in str(e) and "does not exist" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback

        logger.error(f"Error in api_get_all_spo2_data: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching SpO2 data. Please try again later.",
        )


@router.get("/get_daily_avg_spo2_data")
async def api_get_daily_avg_spo2_data(
    params: Tuple[int, datetime, datetime] = Depends(parse_date_parameters),
):
    user_id, start_date, end_date = params

    try:
        data = get_daily_avg_spo2_data(user_id, start_date, end_date)

        fallback_used = False
        warning_message = None

        if not data:
            warning_message = f"No daily average SpO2 data found for user {user_id} in the specified time range"

        response = {
            "success": True,
            "parameters": {
                "user_id": user_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "data_count": len(data),
            "data": data,
        }

        if warning_message:
            response["warning"] = warning_message

        if fallback_used:
            response["fallback_used"] = True

        return response
    except ValueError as e:
        if "User" in str(e) and "does not exist" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback

        logger.error(f"Error in api_get_daily_avg_spo2_data: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching daily SpO2 data. Please try again later.",
        )
