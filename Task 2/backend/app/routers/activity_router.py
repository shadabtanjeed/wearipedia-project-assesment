from fastapi import APIRouter, Depends, HTTPException
from typing import Tuple
from datetime import datetime

from app.controllers.activity_controller import (
    get_all_activity_data,
)
from app.utils.date_parser import parse_date_parameters

router = APIRouter(prefix="/api/activity", tags=["Activity"])


@router.get("/get_all_activity_data")
async def api_get_all_activity_data(
    params: Tuple[int, datetime, datetime] = Depends(parse_date_parameters),
):
    user_id, start_date, end_date = params

    try:
        data = get_all_activity_data(user_id, start_date, end_date)
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
            status_code=500, detail=f"Error fetching activity data: {str(e)}"
        )
