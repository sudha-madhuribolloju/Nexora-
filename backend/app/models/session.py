"""
app/models/session.py
──────────────────────
ClassSession ORM model (live/recorded lessons).

Migrated to use app.database.base.Base (Alembic-tracked).
Table name: class_sessions (unchanged).
Tables created in Migration 006.
"""
import uuid
import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.people import Teacher
    from app.models.academic import Subject
    from app.models.attendance import Attendance


class SessionStatus(str, enum.Enum):
    SCHEDULED  = "scheduled"
    ACTIVE     = "active"
    COMPLETED  = "completed"
    CANCELLED  = "cancelled"


class ClassSession(TimestampMixin, Base):
    """
    A scheduled or live teaching session within a course.
    Attendance records are linked to sessions.
    """
    __tablename__ = "class_sessions"
    __table_args__ = (
        Index("ix_class_sessions_course_id",  "course_id"),
        Index("ix_class_sessions_teacher_id", "teacher_id"),
        Index("ix_class_sessions_status",     "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id:  Mapped[uuid.UUID]          = mapped_column(PGUUID(as_uuid=True), ForeignKey("courses.id",  ondelete="CASCADE"),  nullable=False)
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    title:        Mapped[str]            = mapped_column(String(255), nullable=False)
    description:  Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at:   Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status:       Mapped[SessionStatus]  = mapped_column(Enum(SessionStatus, name="sessionstatus"), default=SessionStatus.SCHEDULED, nullable=False)
    location:     Mapped[Optional[str]]  = mapped_column(String(255), nullable=True)
    meeting_url:  Mapped[Optional[str]]  = mapped_column(Text, nullable=True)

    course:             Mapped["Course"]          = relationship("Course",      back_populates="sessions")
    subject:            Mapped[Optional["Subject"]] = relationship("Subject",   foreign_keys=[subject_id])
    teacher:            Mapped[Optional["Teacher"]] = relationship("Teacher",   foreign_keys=[teacher_id], back_populates="sessions")
    attendance_records: Mapped[List["Attendance"]]  = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ClassSession title={self.title!r} status={self.status}>"
