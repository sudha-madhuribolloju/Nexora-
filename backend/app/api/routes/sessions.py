"""
Sessions router — CRUD + start/end lifecycle management.
"""
import uuid
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user, require_lecture_control_permission
from app.models.user import User
from app.models.session import SessionStatus
from app.services.session_service import SessionService
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse

router = APIRouter()


@router.get("/", response_model=SessionListResponse, summary="List sessions")
async def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    course_id: Optional[uuid.UUID] = Query(None),
    teacher_id: Optional[uuid.UUID] = Query(None),
    session_status: Optional[SessionStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve paginated class sessions with optional filtering.
    """
    total, sessions = await SessionService.list_sessions(db, skip, limit, course_id, teacher_id, session_status)
    return SessionListResponse(total=total, skip=skip, limit=limit, data=sessions)


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, summary="Create a session")
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_lecture_control_permission),
) -> Any:
    """
    Create a new class session. Only Teachers/Admins can create sessions.
    """
    return await SessionService.create_session(db, data)


@router.get("/{session_id}", response_model=SessionResponse, summary="Get session by ID")
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve a specific session by its ID.
    """
    return await SessionService.get_session(db, session_id)


@router.put("/{session_id}", response_model=SessionResponse, summary="Update a session")
async def update_session(
    session_id: uuid.UUID,
    data: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_lecture_control_permission),
) -> Any:
    """
    Update details of an existing session. Only Teachers/Admins can update sessions.
    """
    return await SessionService.update_session(db, session_id, data)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a session")
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_lecture_control_permission),
) -> None:
    """
    Delete a session permanently. Only Teachers/Admins can delete sessions.
    """
    await SessionService.delete_session(db, session_id)


@router.post("/{session_id}/start", response_model=SessionResponse, summary="Start a session")
async def start_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_lecture_control_permission),
) -> Any:
    """
    Mark a scheduled session as active (started). Only Teachers/Admins can start sessions.
    """
    return await SessionService.start_session(db, session_id)


@router.post("/{session_id}/end", response_model=SessionResponse, summary="End a session")
async def end_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_lecture_control_permission),
) -> Any:
    """
    Mark an active session as completed (ended). Only Teachers/Admins can end sessions.
    """
    return await SessionService.end_session(db, session_id)
