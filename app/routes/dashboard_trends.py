"""Dashboard trend API routes via FastAPI."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services import trend_service
from app.utils.auth import auth_guard

router = APIRouter(
    prefix="/api",
    tags=["Dashboard"],
    dependencies=[Depends(auth_guard)],
)


@router.get("/dashboard/trends")
def get_dashboard_trends(period: Optional[List[str]] = Query(default=None)):
    """Return materialized dashboard trend data."""
    periods = [value.strip().lower() for value in period or [] if value.strip()]

    try:
        data = trend_service.fetch_trend_payload(periods or None)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"periods": data}
