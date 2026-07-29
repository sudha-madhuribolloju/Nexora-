from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.api.dependencies import get_db
from app.utils.helpers import format_response

router = APIRouter()

@router.get("/", response_model=Any)
async def get_classes(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all classrooms/courses.
    """
    return format_response(status="success", message="Get classes stub", data={"classes": []})

@router.post("/", response_model=Any)
async def create_class(
    class_data: dict,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new classroom.
    """
    return format_response(status="success", message="Class created successfully stub", data=class_data)
