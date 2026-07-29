"""
app/models/attendance.py
─────────────────────────
Attendance ORM model.

Migrated to use app.database.base.Base (Alembic-tracked).
Tables created in Migration 006.
"""
import uuid
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.session import ClassSession
    from app.models.people import Student
    from app.models.user import User


class AttendanceStatus(str, enum.Enum):
    PRESENT  = "present"
    ABSENT   = "absent"
    LATE     = "late"
    EXCUSED  = "excused"


class Attendance(Base):
    """
    Attendance record for one student in one class session.
    UNIQUE(session_id, student_id) prevents duplicate marks.
    """
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_attendance_session_student"),
        Index("ix_attendance_session_id",  "session_id"),
        Index("ix_attendance_student_id",  "student_id"),
        Index("ix_attendance_status",      "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    session_id: Mapped[uuid.UUID]          = mapped_column(PGUUID(as_uuid=True), ForeignKey("class_sessions.id", ondelete="CASCADE"),  nullable=False)
    student_id: Mapped[uuid.UUID]          = mapped_column(PGUUID(as_uuid=True), ForeignKey("students.id",       ondelete="CASCADE"),  nullable=False)
    marked_by:  Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id",         ondelete="SET NULL"), nullable=True)

    status:    Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus, name="attendancestatus"), nullable=False, default=AttendanceStatus.ABSENT)
    notes:     Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    marked_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    session: Mapped["ClassSession"] = relationship("ClassSession", back_populates="attendance_records")
    student: Mapped["Student"]      = relationship("Student",      back_populates="attendance_records")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Attendance session={self.session_id} student={self.student_id} status={self.status}>"
