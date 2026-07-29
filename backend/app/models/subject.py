"""
app/models/subject.py
──────────────────────
CourseSubject — links a school-level Subject catalogue entry (academic.Subject)
to a specific Course, optionally assigning a teacher and credit hours for that
course-specific delivery of the subject.

Why this table exists
─────────────────────
• academic.Subject (Migration 004) is the school-wide subject catalogue:
  "Mathematics", "Physics", "English Literature".

• CourseSubject is the *assignment* of a subject to a specific course
  (e.g. "Mathematics delivered in Grade 10-A Science stream 2025-26").
  One Subject can appear in many courses; one course can teach many subjects.

• This replaces the old app.models.subject.Subject which used base_class.Base
  (un-tracked by Alembic) and had a table name collision with academic.Subject.

Table name: course_subjects (renamed from old `subjects` to avoid collision)
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.people import Teacher
    from app.models.academic import Subject as CatalogueSubject


class CourseSubject(Base):
    """
    Assignment of a catalogue Subject to a specific Course.
    Replaces the legacy 'subjects' table (base_class era).
    """

    __tablename__ = "course_subjects"
    __table_args__ = (
        Index("ix_course_subjects_course_id",   "course_id"),
        Index("ix_course_subjects_subject_id",  "subject_id"),
        Index("ix_course_subjects_teacher_id",  "teacher_id"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign keys ───────────────────────────────────────────────────────────
    course_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        doc="FK to academic.subjects (school-level catalogue).",
    )
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Fields ─────────────────────────────────────────────────────────────────
    credits:     Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active:   Mapped[bool]          = mapped_column(Boolean, default=True, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    course:  Mapped["Course"]             = relationship("Course",  back_populates="course_subjects")
    teacher: Mapped[Optional["Teacher"]]  = relationship("Teacher", foreign_keys=[teacher_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CourseSubject course={self.course_id} subject={self.subject_id}>"
