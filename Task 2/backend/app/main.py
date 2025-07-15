from fastapi import FastAPI, Query, HTTPException, Depends
from datetime import datetime, timedelta
import pytz
from typing import Optional, Tuple

# change this according to your timezone:
GMT6 = pytz.timezone("Asia/Dhaka")


app = FastAPI()


from routes.azm_routes import get_all_azm_data, get_daily_avg_azm_data


def parse_date_parameters(
    user_id: int = Query(1, description="User ID to query"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
) -> Tuple[int, datetime, datetime]:

    try:
        if end_date is None:
            end_date_parsed = datetime.strptime("2024-01-30", "%Y-%m-%d")
            end_date_parsed = GMT6.localize(end_date_parsed)
        else:
            end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d")
            end_date_parsed = GMT6.localize(end_date_parsed)

        if start_date is None:
            start_date_parsed = datetime.strptime("2024-01-01", "%Y-%m-%d")
            start_date_parsed = GMT6.localize(start_date_parsed)
        else:
            start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d")
            start_date_parsed = GMT6.localize(start_date_parsed)

        return user_id, start_date_parsed, end_date_parsed
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format. Please use YYYY-MM-DD: {str(e)}",
        )


@app.get("/api/azm/get_all_azm_data")
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


@app.get("/api/azm/get_daily_avg_azm_data")
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


@app.get("/api/azm")
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
