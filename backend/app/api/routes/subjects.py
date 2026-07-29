"""
Subjects router — CRUD for academic subjects.
"""
import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.subject_service import SubjectService
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, SubjectListResponse

router = APIRouter()


@router.get("/", response_model=SubjectListResponse, summary="List subjects")
async def list_subjects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    course_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve a paginated list of subjects, optionally filtered by course.
    """
    total, subjects = await SubjectService.list_subjects(db, skip, limit, course_id)
    return SubjectListResponse(total=total, skip=skip, limit=limit, data=subjects)


@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED, summary="Create a subject")
async def create_subject(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Create a new subject linked to a course.
    """
    return await SubjectService.create_subject(db, data)


@router.get("/{subject_id}", response_model=SubjectResponse, summary="Get subject by ID")
async def get_subject(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve a specific subject by its ID.
    """
    return await SubjectService.get_subject(db, subject_id)


@router.put("/{subject_id}", response_model=SubjectResponse, summary="Update a subject")
async def update_subject(
    subject_id: uuid.UUID,
    data: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Update the details of an existing subject.
    """
    return await SubjectService.update_subject(db, subject_id, data)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a subject")
async def delete_subject(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    """
    Delete a subject permanently.
    """
    await SubjectService.delete_subject(db, subject_id)
