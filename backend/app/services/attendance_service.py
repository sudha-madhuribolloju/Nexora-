"""
Attendance service — CRUD, bulk marking, and reporting.
"""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceBulkCreate,
    AttendanceUpdate,
    AttendanceReportEntry,
)


class AttendanceService:

    @staticmethod
    async def list_attendance(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        session_id: Optional[uuid.UUID] = None,
        student_id: Optional[uuid.UUID] = None,
    ) -> Tuple[int, List[Attendance]]:
        q = select(Attendance)
        if session_id:
            q = q.where(Attendance.session_id == session_id)
        if student_id:
            q = q.where(Attendance.student_id == student_id)
        total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        records = (await db.execute(q.offset(skip).limit(limit))).scalars().all()
        return total, list(records)

    @staticmethod
    async def get_attendance(db: AsyncSession, attendance_id: uuid.UUID) -> Attendance:
        result = await db.execute(select(Attendance).where(Attendance.id == attendance_id))
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
        return record

    @staticmethod
    async def mark_attendance(
        db: AsyncSession, data: AttendanceCreate, marked_by: Optional[User] = None
    ) -> Attendance:
        # Check for duplicate
        existing = (await db.execute(
            select(Attendance).where(
                and_(
                    Attendance.session_id == data.session_id,
                    Attendance.student_id == data.student_id
                )
            )
        )).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attendance already marked for this student in this session"
            )
        marked_by_id = marked_by.id if marked_by else None
        record = Attendance(**data.model_dump(), marked_by=marked_by_id)
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def bulk_mark_attendance(
        db: AsyncSession, data: AttendanceBulkCreate, marked_by: Optional[User] = None
    ) -> List[Attendance]:
        created = []
        marked_by_id = marked_by.id if marked_by else None
        for item in data.records:
            existing = (await db.execute(
                select(Attendance).where(
                    and_(
                        Attendance.session_id == data.session_id,
                        Attendance.student_id == item.student_id
                    )
                )
            )).scalar_one_or_none()
            if existing:
                existing.status = item.status
                existing.notes = item.notes
                existing.marked_by = marked_by_id
                created.append(existing)
            else:
                record = Attendance(
                    session_id=data.session_id,
                    student_id=item.student_id,
                    status=item.status,
                    notes=item.notes,
                    marked_by=marked_by_id,
                )
                db.add(record)
                created.append(record)
        await db.commit()
        for r in created:
            await db.refresh(r)
        return created

    @staticmethod
    async def update_attendance(
        db: AsyncSession, attendance_id: uuid.UUID, data: AttendanceUpdate
    ) -> Attendance:
        record = await AttendanceService.get_attendance(db, attendance_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def delete_attendance(db: AsyncSession, attendance_id: uuid.UUID) -> None:
        record = await AttendanceService.get_attendance(db, attendance_id)
        await db.delete(record)
        await db.commit()

    @staticmethod
    async def get_report(
        db: AsyncSession,
        student_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
    ) -> List[AttendanceReportEntry]:
        """Aggregate attendance report grouped by student."""
        q = select(
            Attendance.student_id,
            func.count(Attendance.id).label("total"),
            func.sum((Attendance.status == AttendanceStatus.PRESENT).cast(__import__("sqlalchemy").Integer)).label("present"),
            func.sum((Attendance.status == AttendanceStatus.ABSENT).cast(__import__("sqlalchemy").Integer)).label("absent"),
            func.sum((Attendance.status == AttendanceStatus.LATE).cast(__import__("sqlalchemy").Integer)).label("late"),
            func.sum((Attendance.status == AttendanceStatus.EXCUSED).cast(__import__("sqlalchemy").Integer)).label("excused"),
        ).group_by(Attendance.student_id)

        if student_id:
            q = q.where(Attendance.student_id == student_id)
        if session_id:
            q = q.where(Attendance.session_id == session_id)

        rows = (await db.execute(q)).all()
        report = []
        for row in rows:
            total = row.total or 0
            present = row.present or 0
            report.append(AttendanceReportEntry(
                student_id=row.student_id,
                total_sessions=total,
                present=present,
                absent=row.absent or 0,
                late=row.late or 0,
                excused=row.excused or 0,
                attendance_percentage=round((present / total * 100), 2) if total > 0 else 0.0,
            ))
        return report
