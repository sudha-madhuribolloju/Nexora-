"""
app/models/course.py
─────────────────────
Course and CourseEnrollment ORM models.

Migrated to use app.database.base.Base (Alembic-tracked).
Tables created in Migration 006.
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.people import Teacher, Student
    from app.models.subject import CourseSubject
    from app.models.session import ClassSession
    from app.models.assignment import Assignment
    from app.models.quiz import Quiz
    from app.models.document import Document


class CourseEnrollment(TimestampMixin, Base):
    """
    Many-to-many link between Students and Courses.
    A student can enrol in multiple courses; each course has many students.
    """
    __tablename__ = "course_enrollments"
    __table_args__ = (
        UniqueConstraint("course_id", "student_id", name="uq_course_enrollment"),
        Index("ix_course_enrollments_course_id",   "course_id"),
        Index("ix_course_enrollments_student_id",  "student_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id:  Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("courses.id",  ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    is_active:  Mapped[bool]      = mapped_column(Boolean, default=True, nullable=False, server_default="true")

    course:  Mapped["Course"]  = relationship("Course",  back_populates="enrollments")
    student: Mapped["Student"] = relationship("Student", back_populates="enrollments")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CourseEnrollment course={self.course_id} student={self.student_id}>"


class Course(TimestampMixin, Base):
    """
    A course offered by a school — the primary academic container.
    Students enrol in courses; sessions, assignments, and quizzes belong to courses.
    """
    __tablename__ = "courses"
    __table_args__ = (
        Index("ix_courses_teacher_id", "teacher_id"),
        Index("ix_courses_school_id",  "school_id"),
        Index("ix_courses_is_active",  "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id:  Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), ForeignKey("schools.id",  ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    title:       Mapped[str]            = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    code:        Mapped[Optional[str]]  = mapped_column(String(50), nullable=True, index=True)
    is_active:   Mapped[bool]           = mapped_column(Boolean, default=True, nullable=False, server_default="true")
    max_students: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    teacher:         Mapped[Optional["Teacher"]]      = relationship("Teacher", foreign_keys=[teacher_id], back_populates="courses")
    enrollments:     Mapped[List["CourseEnrollment"]] = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    course_subjects: Mapped[List["CourseSubject"]]    = relationship("CourseSubject",    back_populates="course", cascade="all, delete-orphan")
    sessions:        Mapped[List["ClassSession"]]     = relationship("ClassSession",     back_populates="course", cascade="all, delete-orphan")
    assignments:     Mapped[List["Assignment"]]       = relationship("Assignment",       back_populates="course", cascade="all, delete-orphan")
    quizzes:         Mapped[List["Quiz"]]             = relationship("Quiz",             back_populates="course", cascade="all, delete-orphan")
    documents:       Mapped[List["Document"]]         = relationship("Document",         back_populates="course")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Course code={self.code!r} title={self.title!r}>"
