from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
import uuid

from app.api.dependencies import get_db
from app.schemas.student import StudentResponse, StudentCreate, StudentUpdate
from app.utils.helpers import format_response

router = APIRouter()

@router.get("/", response_model=Any)
async def get_students(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all students.
    """
    return format_response(status="success", message="Get students stub", data={"students": []})

@router.get("/{student_id}", response_model=Any)
async def get_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get student details.
    """
    return format_response(status="success", message="Get student stub", data={"student_id": str(student_id)})

@router.post("/", response_model=Any, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_in: StudentCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new student entry.
    """
    return format_response(status="success", message="Create student stub", data=student_in.model_dump())

@router.put("/{student_id}", response_model=Any)
async def update_student(
    student_id: uuid.UUID,
    student_in: StudentUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update student details.
    """
    return format_response(status="success", message="Update student stub", data={"student_id": str(student_id)})

@router.delete("/{student_id}", response_model=Any)
async def delete_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Remove student.
    """
    return format_response(status="success", message="Delete student stub")
