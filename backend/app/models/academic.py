"""
app/models/academic.py
───────────────────────
ORM models for the academic structure layer: Class, Section, Subject.

Why these tables exist
──────────────────────
• Class   — Represents a grade level within a school and academic year
            (e.g. "Grade 10 — 2025-2026"). Scoping to academic_year_id
            lets the system archive old class data while keeping a clean
            current view.

• Section — A division of a class (e.g. "Grade 10-A", "Grade 10-B").
            Sections are the primary unit for attendance tracking, timetabling,
            and student enrolment. Denormalising school_id here avoids an
            extra join on every school-level query.

• Subject — School-level subject catalogue ("Mathematics", "Physics").
            Subjects are NOT scoped to a year; they persist across years.
            Linking subjects to specific years/sections is done via the
            Timetable table (Migration 005).

Design decisions
────────────────
• class_teacher_id on Section is stored as a bare UUID column here. The FK
  constraint pointing to teachers.id is added in Migration 004 when the
  teachers table exists ("deferred FK" pattern used throughout this schema).

• Section.school_id is a denormalised FK to schools.id kept in sync with
  its parent Class.school_id by the service layer. This allows fast
  "give me all sections for school X" queries without a JOIN through classes.

• Subject.color is a 7-char hex string ("#RRGGBB") for UI badge rendering —
  no constraint on the DB side; validated by Pydantic schema.

• All three tables support soft-delete so historical records (attendance,
  results) can safely keep their FKs alive even after a class/section is
  retired.

Sample records
──────────────
classes  : { name: "Grade 10", grade_level: 10, school_id: …, academic_year_id: … }
sections : { name: "A", class_id: …, school_id: …, capacity: 40, room_number: "101" }
subjects : { name: "Mathematics", code: "MATH", school_id: …, credits: 5.0,
             color: "#4F46E5", is_elective: false }
"""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.school import AcademicYear, School
    from app.models.people import Student, Teacher   # Migration 004


# ── Class ──────────────────────────────────────────────────────────────────────

class Class(TimestampMixin, SoftDeleteMixin, Base):
    """
    A grade level within one school for one academic year.
    e.g. "Grade 10 — Greenwood High — 2025-2026"
    """

    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint(
            "school_id", "academic_year_id", "name",
            name="uq_classes_school_year_name",
        ),
        Index("ix_classes_school_id",        "school_id"),
        Index("ix_classes_academic_year_id", "academic_year_id"),
        Index("ix_classes_grade_level",      "grade_level"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign keys ───────────────────────────────────────────────────────────
    school_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Fields ─────────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(50), nullable=False,
        doc="Human-readable grade/class name, e.g. 'Grade 10', 'Class 1', 'Form 5'.",
    )
    grade_level: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        doc="Numeric grade for sorting (1–12). NULL for pre-primary or custom labels.",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    school: Mapped["School"] = relationship(
        "School", foreign_keys=[school_id], lazy="select"
    )
    academic_year: Mapped["AcademicYear"] = relationship(
        "AcademicYear", foreign_keys=[academic_year_id], lazy="select"
    )
    sections: Mapped[List["Section"]] = relationship(
        "Section",
        back_populates="class_",
        cascade="all, delete-orphan",
        order_by="Section.name",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Class name={self.name!r} school={self.school_id}>"


# ── Section ────────────────────────────────────────────────────────────────────

class Section(TimestampMixin, SoftDeleteMixin, Base):
    """
    A division of a Class (e.g. "Grade 10-A").
    The atomic unit for:
      • Student enrolment (one student → one section at a time)
      • Attendance marking
      • Timetable slots
    """

    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("class_id", "name", name="uq_sections_class_name"),
        Index("ix_sections_class_id",  "class_id"),
        Index("ix_sections_school_id", "school_id"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign keys ───────────────────────────────────────────────────────────
    class_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Denormalised for performance — kept in sync with class_.school_id
    school_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )
    # FK to teachers.id added in Migration 004
    class_teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        doc="Homeroom teacher UUID. FK constraint to teachers.id added in Migration 004.",
    )

    # ── Fields ─────────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(10), nullable=False,
        doc="Section label, e.g. 'A', 'B', 'C', 'Alpha'.",
    )
    capacity: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        doc="Maximum number of students allowed in this section.",
    )
    room_number: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        doc="Physical classroom identifier.",
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    class_: Mapped["Class"] = relationship(
        "Class", back_populates="sections", lazy="select"
    )
    school: Mapped["School"] = relationship(
        "School", foreign_keys=[school_id], lazy="select"
    )
    # Populated by Migration 004
    # students: Mapped[List["Student"]] = relationship(...)
    # class_teacher: Mapped[Optional["Teacher"]] = relationship(...)

    @property
    def full_name(self) -> str:
        """e.g. 'Grade 10-A' — assembled at runtime, never stored."""
        return f"{self.class_.name}-{self.name}" if self.class_ else self.name

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Section name={self.name!r} class={self.class_id}>"


# ── Subject ────────────────────────────────────────────────────────────────────

class Subject(TimestampMixin, SoftDeleteMixin, Base):
    """
    School-level subject catalogue entry.

    Subjects are reused across academic years. Assigning a subject to a
    specific section/year is done via timetable entries (Migration 005).
    Exam results reference subject_id directly.
    """

    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_subjects_school_code"),
        Index("ix_subjects_school_id", "school_id"),
        Index("ix_subjects_name",      "name"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign key ────────────────────────────────────────────────────────────
    school_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Fields ─────────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
        doc="Full subject name, e.g. 'Mathematics', 'English Literature'.",
    )
    code: Mapped[str] = mapped_column(
        String(20), nullable=False,
        doc="Short code unique within the school, e.g. 'MATH', 'ENGLIT'.",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credits: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(4, 1), nullable=True,
        doc="Credit hours / weightage for result calculation.",
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(7), nullable=True,
        doc="Hex colour for UI badges, e.g. '#4F46E5'.",
    )
    is_elective: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false",
        doc="True = optional subject; False = compulsory.",
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    school: Mapped["School"] = relationship(
        "School", foreign_keys=[school_id], lazy="select"
    )
    # timetable_entries added in Migration 005
    # exam_results added in Migration 005

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Subject code={self.code!r} name={self.name!r}>"
