"""
app/models/assignment.py
─────────────────────────
Assignment and AssignmentSubmission ORM models.

Migrated to use app.database.base.Base (Alembic-tracked).
Tables created in Migration 006.
"""
import uuid
import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.people import Teacher, Student


class AssignmentStatus(str, enum.Enum):
    DRAFT     = "draft"
    PUBLISHED = "published"
    CLOSED    = "closed"


class SubmissionStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    LATE      = "late"
    GRADED    = "graded"
    RETURNED  = "returned"


class Assignment(TimestampMixin, Base):
    """Course assignment with deadline and scoring rules."""
    __tablename__ = "assignments"
    __table_args__ = (
        Index("ix_assignments_course_id",    "course_id"),
        Index("ix_assignments_created_by",   "created_by"),
        Index("ix_assignments_status",       "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id:   Mapped[uuid.UUID]          = mapped_column(PGUUID(as_uuid=True), ForeignKey("courses.id",  ondelete="CASCADE"),  nullable=False)
    created_by:  Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    title:                Mapped[str]            = mapped_column(String(255), nullable=False)
    description:          Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    instructions:         Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    max_score:            Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=100.0)
    due_date:             Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status:               Mapped[AssignmentStatus] = mapped_column(Enum(AssignmentStatus, name="assignmentstatus"), default=AssignmentStatus.DRAFT, nullable=False)
    allow_late_submission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")

    course:      Mapped["Course"]                    = relationship("Course",  back_populates="assignments")
    teacher:     Mapped[Optional["Teacher"]]         = relationship("Teacher", foreign_keys=[created_by], back_populates="assignments")
    submissions: Mapped[List["AssignmentSubmission"]] = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Assignment title={self.title!r} status={self.status}>"


class AssignmentSubmission(Base):
    """A student's submission for an assignment."""
    __tablename__ = "assignment_submissions"
    __table_args__ = (
        Index("ix_assignment_submissions_assignment_id", "assignment_id"),
        Index("ix_assignment_submissions_student_id",    "student_id"),
        Index("ix_assignment_submissions_status",        "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID]          = mapped_column(PGUUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"),  nullable=False)
    student_id:    Mapped[uuid.UUID]          = mapped_column(PGUUID(as_uuid=True), ForeignKey("students.id",    ondelete="CASCADE"),  nullable=False)
    graded_by:     Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("teachers.id",  ondelete="SET NULL"), nullable=True)

    content:      Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    file_url:     Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    score:        Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback:     Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    status:       Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus, name="submissionstatus"), default=SubmissionStatus.SUBMITTED, nullable=False)
    submitted_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    graded_at:    Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="submissions")
    student:    Mapped["Student"]    = relationship("Student",    back_populates="submissions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AssignmentSubmission assignment={self.assignment_id} student={self.student_id} status={self.status}>"
