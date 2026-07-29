from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
import uuid

from app.api.dependencies import get_db
from app.schemas.teacher import TeacherResponse, TeacherCreate, TeacherUpdate
from app.utils.helpers import format_response

router = APIRouter()

@router.get("/", response_model=Any)
async def get_teachers(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all teachers.
    """
    return format_response(status="success", message="Get teachers stub", data={"teachers": []})

@router.get("/{teacher_id}", response_model=Any)
async def get_teacher(
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get teacher details.
    """
    return format_response(status="success", message="Get teacher stub", data={"teacher_id": str(teacher_id)})

@router.post("/", response_model=Any, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_in: TeacherCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new teacher profile.
    """
    return format_response(status="success", message="Create teacher stub", data=teacher_in.model_dump())

@router.put("/{teacher_id}", response_model=Any)
async def update_teacher(
    teacher_id: uuid.UUID,
    teacher_in: TeacherUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update teacher details.
    """
    return format_response(status="success", message="Update teacher stub", data={"teacher_id": str(teacher_id)})

@router.delete("/{teacher_id}", response_model=Any)
async def delete_teacher(
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Remove teacher.
    """
    return format_response(status="success", message="Delete teacher stub")
