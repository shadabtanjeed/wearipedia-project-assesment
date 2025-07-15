from fastapi import Query, HTTPException
from datetime import datetime
from typing import Optional, Tuple

from app.config.timezone import GMT6


# Parse and validate date parameters for API requests


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
