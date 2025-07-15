from fastapi import APIRouter, Depends, HTTPException
from typing import Tuple
from datetime import datetime

from app.controllers.azm_controller import get_all_azm_data, get_daily_avg_azm_data
from app.utils.date_parser import parse_date_parameters

router = APIRouter(prefix="/api/azm", tags=["Active Zone Minutes"])


@router.get("/get_all_azm_data")
async def api_get_all_azm_data(
    params: Tuple[int, datetime, datetime] = Depends(parse_date_parameters),
):
    user_id, start_date, end_date = params

    try:
        data = get_all_azm_data(user_id, start_date, end_date)
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
            status_code=500, detail=f"Error fetching all AZM data: {str(e)}"
        )


@router.get("/get_daily_avg_azm_data")
async def api_get_daily_avg_azm_data(
    params: Tuple[int, datetime, datetime] = Depends(parse_date_parameters),
):
    user_id, start_date, end_date = params

    try:
        data = get_daily_avg_azm_data(user_id, start_date, end_date)
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
            status_code=500, detail=f"Error fetching daily average AZM data: {str(e)}"
        )


@router.get("")
async def get_azm_data(
    params: Tuple[int, datetime, datetime] = Depends(parse_date_parameters),
):
    user_id, start_date, end_date = params

    try:
        all_data = get_all_azm_data(user_id, start_date, end_date)
        daily_data = get_daily_avg_azm_data(user_id, start_date, end_date)

        return {
            "success": True,
            "parameters": {
                "user_id": user_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "all_data_count": len(all_data),
            "daily_data_count": len(daily_data),
            "sample_all_data": all_data[0] if all_data else None,
            "sample_daily_data": daily_data[0] if daily_data else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching AZM data: {str(e)}"
        )
