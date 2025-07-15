from fastapi import APIRouter, Depends, HTTPException
from typing import Tuple
from datetime import datetime

from app.controllers.hr_controller import (
    get_all_heart_rate_data,
    get_daily_avg_heart_rate_data,
    get_heart_rate_zones_data,
)
from app.utils.date_parser import parse_date_parameters

router = APIRouter(prefix="/api/heart_rate", tags=["Heart Rate"])


@router.get("/get_all_heart_rate_data")
async def api_get_all_heart_rate_data(
    params: Tuple[int, datetime, datetime] = Depends(parse_date_parameters),
):
    user_id, start_date, end_date = params

    try:
        data = get_all_heart_rate_data(user_id, start_date, end_date)
        return {
            "success": True,
            "parameters": {
                "user_id": user_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "data_count": len(data),
            "data": data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching heart rate data: {str(e)}"
        )


@router.get("/get_daily_avg_heart_rate_data")
async def api_get_daily_avg_heart_rate_data(
    params: Tuple[int, datetime, datetime] = Depends(parse_date_parameters),
):
    user_id, start_date, end_date = params

    try:
        data = get_daily_avg_heart_rate_data(user_id, start_date, end_date)
        return {
            "success": True,
            "parameters": {
                "user_id": user_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "data_count": len(data),
            "data": data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching daily heart rate data: {str(e)}"
        )


@router.get("/get_heart_rate_zones_data")
async def api_get_heart_rate_zones_data(
    params: Tuple[int, datetime, datetime] = Depends(parse_date_parameters),
):
    user_id, start_date, end_date = params

    try:
        data = get_heart_rate_zones_data(user_id, start_date, end_date)
        return {
            "success": True,
            "parameters": {
                "user_id": user_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "data_count": len(data),
            "data": data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching heart rate zones data: {str(e)}"
        )
