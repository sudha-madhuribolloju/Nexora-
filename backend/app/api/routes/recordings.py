"""
app/api/routes/recordings.py
──────────────────────────────
REST API endpoints for Recorded Lectures management, video streaming, downloads,
RBAC security, and AI transcript/summary generation.
"""

import uuid
import os
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, Header, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.recording import (
    RecordingResponse,
    RecordingListResponse,
    RecordingAnalyticsResponse,
)
from app.services.recording_service import RecordingService
from app.services.storage_service import StorageService

router = APIRouter()


# ── Teacher & Student Recording Endpoints ─────────────────────────────────────

@router.get("/my", response_model=RecordingListResponse, summary="Get current teacher's recordings")
async def get_my_recordings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    subject_id: Optional[uuid.UUID] = None,
    class_id: Optional[uuid.UUID] = None,
    recording_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve recordings created by the logged-in teacher."""
    total, data = await RecordingService.list_teacher_recordings(
        db=db,
        teacher_user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search,
        subject_id=subject_id,
        class_id=class_id,
        recording_status=recording_status,
    )
    return RecordingListResponse(total=total, skip=skip, limit=limit, data=data)


@router.get("", response_model=RecordingListResponse, summary="List recordings accessible to current user")
async def list_recordings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    subject_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List recordings available to enrolled students or users."""
    if current_user.role in ("Teacher", "teacher"):
        total, data = await RecordingService.list_teacher_recordings(
            db=db, teacher_user_id=current_user.id, skip=skip, limit=limit, search=search, subject_id=subject_id
        )
    elif current_user.role in ("Super Admin", "Institute Admin", "Principal", "super_admin", "school_admin"):
        total, data = await RecordingService.list_admin_recordings(
            db=db, skip=skip, limit=limit, search=search, subject_id=subject_id
        )
    else:
        total, data = await RecordingService.list_student_recordings(
            db=db, student_user=current_user, skip=skip, limit=limit, search=search, subject_id=subject_id
        )
    return RecordingListResponse(total=total, skip=skip, limit=limit, data=data)


@router.get("/analytics", response_model=RecordingAnalyticsResponse, summary="Get recording analytics for Principal & Admins")
async def get_recording_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return aggregated recording statistics for Principal and Administrators."""
    if current_user.role not in ("Super Admin", "Institute Admin", "Principal", "super_admin", "school_admin", "principal"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics view restricted to Principals and Administrators."
        )
    return await RecordingService.get_recording_analytics(db)


@router.get("/{id}", response_model=RecordingResponse, summary="Get recording metadata & AI summary")
async def get_recording_by_id(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve detailed metadata, transcript, and AI summary for a single recording."""
    rec = await RecordingService.get_recording(db, id)
    return RecordingService._annotate_recording(rec)


@router.get("/{id}/stream", summary="Stream recording video with Range header support")
async def stream_recording_video(
    id: uuid.UUID,
    range: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream HTML5 video using HTTP 206 Partial Content range requests."""
    rec = await RecordingService.get_recording(db, id)
    return StorageService.get_file_stream_response(rec.storage_path, rec.filename, range_header=range)


@router.get("/{id}/download", summary="Download recording file")
async def download_recording_file(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Download lecture recording video file."""
    rec = await RecordingService.get_recording(db, id)
    if not os.path.exists(rec.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on storage."
        )
    return FileResponse(
        rec.storage_path,
        media_type="application/octet-stream",
        filename=rec.filename
    )


@router.delete("/{id}", response_model=RecordingResponse, summary="Soft delete a recording")
async def delete_recording(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Soft delete recording (Allowed for owner teacher or admin)."""
    return await RecordingService.soft_delete_recording(db, id, current_user)


@router.post("/{id}/ai-process", response_model=RecordingResponse, summary="Generate AI Transcript & Summary using Gemini")
async def process_recording_ai(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Trigger Gemini AI processing for recording transcript and summary."""
    return await RecordingService.process_ai_for_recording(db, id)


# ── Admin Recording Endpoints ──────────────────────────────────────────────────

@router.get("/admin/all", response_model=RecordingListResponse, summary="Admin view all recordings")
async def admin_list_all_recordings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    teacher_id: Optional[uuid.UUID] = None,
    subject_id: Optional[uuid.UUID] = None,
    class_id: Optional[uuid.UUID] = None,
    recording_status: Optional[str] = None,
    include_deleted: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all recordings across school/system with pagination & filters (Admin / Principal)."""
    if current_user.role not in ("Super Admin", "Institute Admin", "Principal", "super_admin", "school_admin", "principal"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin recording management restricted to Administrators and Principals."
        )
    total, data = await RecordingService.list_admin_recordings(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        teacher_id=teacher_id,
        subject_id=subject_id,
        class_id=class_id,
        recording_status=recording_status,
        include_deleted=include_deleted
    )
    return RecordingListResponse(total=total, skip=skip, limit=limit, data=data)


@router.post("/admin/{id}/restore", response_model=RecordingResponse, summary="Restore soft-deleted recording")
async def admin_restore_recording(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Restore a soft deleted recording (Admin only)."""
    if current_user.role not in ("Super Admin", "Institute Admin", "super_admin", "school_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Administrators can restore soft-deleted recordings."
        )
    return await RecordingService.restore_recording(db, id, current_user)
