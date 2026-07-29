"""
Attendance router — mark, bulk mark, update, and reporting.
"""
import uuid
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.attendance_service import AttendanceService
from app.schemas.attendance import (
    AttendanceCreate, AttendanceBulkCreate, AttendanceUpdate,
    AttendanceResponse, AttendanceListResponse, AttendanceReportEntry,
)

router = APIRouter()


@router.get("/", response_model=AttendanceListResponse, summary="List attendance records")
async def list_attendance(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session_id: Optional[uuid.UUID] = Query(None),
    student_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve attendance records with optional filtering by session or student.
    """
    total, records = await AttendanceService.list_attendance(db, skip, limit, session_id, student_id)
    return AttendanceListResponse(total=total, skip=skip, limit=limit, data=records)


@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED, summary="Mark attendance")
async def mark_attendance(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark attendance for a single student in a session.
    """
    return await AttendanceService.mark_attendance(db, data, None)


@router.post("/bulk", summary="Bulk mark attendance", status_code=status.HTTP_201_CREATED)
async def bulk_mark_attendance(
    data: AttendanceBulkCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark attendance for multiple students in a session at once.
    Existing records are updated; new ones are created.
    """
    records = await AttendanceService.bulk_mark_attendance(db, data, None)
    return {"status": "success", "count": len(records), "data": [AttendanceResponse.model_validate(r) for r in records]}


@router.get("/report", response_model=List[AttendanceReportEntry], summary="Attendance report")
async def attendance_report(
    student_id: Optional[uuid.UUID] = Query(None),
    session_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Generate an aggregated attendance report, grouped by student.
    """
    return await AttendanceService.get_report(db, student_id, session_id)


@router.get("/{attendance_id}", response_model=AttendanceResponse, summary="Get attendance record")
async def get_attendance(
    attendance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific attendance record by ID.
    """
    return await AttendanceService.get_attendance(db, attendance_id)


@router.put("/{attendance_id}", response_model=AttendanceResponse, summary="Update attendance record")
async def update_attendance(
    attendance_id: uuid.UUID,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update the status or notes of an existing attendance record.
    """
    return await AttendanceService.update_attendance(db, attendance_id, data)


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete attendance record")
async def delete_attendance(
    attendance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete an attendance record.
    """
    await AttendanceService.delete_attendance(db, attendance_id)
