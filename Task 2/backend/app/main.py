from fastapi import FastAPI, Query, HTTPException
from datetime import datetime, timedelta
import pytz
from typing import Optional


app = FastAPI()


from routes.azm_routes import get_all_azm_data, get_daily_avg_azm_data


@app.get("/api/azm")
async def get_azm_data(
    user_id: int = Query(1, description="User ID to query"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    gmt6 = pytz.timezone("Asia/Dhaka")

    try:
        if end_date is None:
            end_date_parsed = datetime.now(gmt6)
        else:
            end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d")
            end_date_parsed = gmt6.localize(end_date_parsed)

        if start_date is None:
            start_date_parsed = end_date_parsed - timedelta(days=30)
        else:
            start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d")
            start_date_parsed = gmt6.localize(start_date_parsed)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format. Please use YYYY-MM-DD: {str(e)}",
        )

    try:
        all_data = get_all_azm_data(user_id, start_date_parsed, end_date_parsed)
        daily_data = get_daily_avg_azm_data(user_id, start_date_parsed, end_date_parsed)

        return {
            "success": True,
            "parameters": {
                "user_id": user_id,
                "start_date": start_date_parsed.isoformat(),
                "end_date": end_date_parsed.isoformat(),
            },
            "all_data_count": len(all_data),
            "daily_data_count": len(daily_data),
            "sample_all_data": all_data[0] if all_data else None,
            "sample_daily_data": daily_data[0] if daily_data else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error testing AZM routes: {str(e)}"
        )
