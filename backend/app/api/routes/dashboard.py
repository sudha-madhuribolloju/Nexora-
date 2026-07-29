from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.api.dependencies import get_db
from app.utils.helpers import format_response

router = APIRouter()

@router.get("/", response_model=Any)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get aggregated dashboard stats for Students, Teachers, Parents, and Admins.
    """
    # Placeholder stats
    metrics = {
        "students_count": 0,
        "teachers_count": 0,
        "parents_count": 0,
        "average_attendance": 0.0,
        "notifications": []
    }
    return format_response(status="success", message="Dashboard metrics stub", data=metrics)
