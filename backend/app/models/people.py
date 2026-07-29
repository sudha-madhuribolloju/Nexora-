"""
app/models/people.py
─────────────────────
ORM models for the People layer: Student, Teacher, Parent.

Why these tables exist
──────────────────────
• Student — Profile extension for Users with role='student'. Stores academic-
            specific data: section enrolment, roll number, admission date, blood
            group, etc. Links back to the User identity row via user_id (1-to-1).

• Teacher — Profile extension for Users with role='teacher'. Stores professional
            data: employee ID, department, qualification, joining date, etc.
            Teachers are referenced by sections.class_teacher_id (deferred FK
            from Migration 004 is resolved here).

• Parent  — Profile extension for Users with role='parent'. A parent can be
            linked to multiple students via the parent_student_links join table.

Design decisions
────────────────
• All three tables have a 1-to-1 FK to users.id (CASCADE DELETE). When a User
  row is hard-deleted (GDPR), the profile row is automatically removed.

• Student.section_id is nullable. A student may be registered but not yet
  assigned to a section (e.g. newly admitted, pending placement).

• Student.school_id is denormalised (mirrors the parent User.school_id) for
  fast school-scoped queries without joining through users.

• Teacher.is_class_teacher is a boolean flag. The *actual* section assignment
  lives in sections.class_teacher_id; this flag is a quick lookup index.

• ParentStudentLink is a many-to-many join table. One parent can have multiple
  children; one student can have multiple parent records (mother, father, guardian).

• admission_number / employee_id are unique per school (UNIQUE school_id + value).
  Using school-scoped uniqueness allows "STU-001" to exist in every school.

• All three profile tables support soft-delete so historical records (grades,
  attendance) can keep their FKs alive even after a student leaves the school.

Sample records
──────────────
students : { user_id: <UUID>, school_id: <UUID>, section_id: <UUID>,
             roll_number: "10-A-01", admission_number: "ADM-2026-001",
             date_of_birth: 2010-03-15, blood_group: "O+" }

teachers : { user_id: <UUID>, school_id: <UUID>, employee_id: "EMP-001",
             department: "Science", qualification: "M.Sc Physics",
             joining_date: 2022-06-01, is_class_teacher: true }

parents  : { user_id: <UUID>, occupation: "Engineer",
             relation_type: "Father", address: "42 Main St, Chennai" }
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.school import School
    from app.models.academic import Section
    from app.models.course import Course, CourseEnrollment
    from app.models.session import ClassSession
    from app.models.attendance import Attendance
    from app.models.assignment import Assignment, AssignmentSubmission
    from app.models.quiz import QuizAttempt


# ── Student ────────────────────────────────────────────────────────────────────

class Student(TimestampMixin, SoftDeleteMixin, Base):
    """
    Profile extension for a User with role='student'.

    One Student row exists per enrolled student. It back-references the central
    User identity row and carries all academic-specific profile data.
    """

    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint(
            "school_id", "admission_number",
            name="uq_students_school_admission_number",
        ),
        UniqueConstraint(
            "school_id", "roll_number",
            name="uq_students_school_roll_number",
        ),
        Index("ix_students_user_id",     "user_id"),
        Index("ix_students_school_id",   "school_id"),
        Index("ix_students_section_id",  "section_id"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign keys ───────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        doc="1-to-1 link to the central User record.",
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        doc="Denormalised from user.school_id for fast school-scoped queries.",
    )
    section_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
        doc="Current section enrolment. NULL = admitted but not yet placed.",
    )

    # ── Identity / admission ───────────────────────────────────────────────────
    admission_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        doc="School-issued admission ID, unique within the school.",
    )
    roll_number: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        doc="Class roll number, unique within the school.",
    )
    admission_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        doc="Date the student was formally admitted.",
    )

    # ── Personal ───────────────────────────────────────────────────────────────
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        doc="e.g. 'Male', 'Female', 'Non-binary', 'Prefer not to say'.",
    )
    blood_group: Mapped[Optional[str]] = mapped_column(
        String(5), nullable=True,
        doc="e.g. 'A+', 'O-', 'AB+'.",
    )
    nationality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Contact / address ──────────────────────────────────────────────────────
    address_line1:  Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2:  Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city:           Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state:          Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code:    Mapped[Optional[str]] = mapped_column(String(20),  nullable=True)

    # ── Status ─────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true",
        doc="False = student has left the school or graduated.",
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    user:    Mapped["User"]              = relationship("User",    back_populates="student_profile")
    school:  Mapped["School"]            = relationship("School",  foreign_keys=[school_id])
    section: Mapped[Optional["Section"]] = relationship("Section", foreign_keys=[section_id])
    parent_links: Mapped[List["ParentStudentLink"]] = relationship(
        "ParentStudentLink",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    # Migration 006 back-references (defined in course/attendance/assignment/quiz models)
    enrollments:       Mapped[List["CourseEnrollment"]]     = relationship("CourseEnrollment",      back_populates="student", cascade="all, delete-orphan")
    attendance_records: Mapped[List["Attendance"]]          = relationship("Attendance",           back_populates="student", cascade="all, delete-orphan")
    submissions:        Mapped[List["AssignmentSubmission"]] = relationship("AssignmentSubmission",  back_populates="student", cascade="all, delete-orphan")
    quiz_attempts:      Mapped[List["QuizAttempt"]]          = relationship("QuizAttempt",           back_populates="student", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Student user_id={self.user_id} roll={self.roll_number!r}>"


# ── Teacher ────────────────────────────────────────────────────────────────────

class Teacher(TimestampMixin, SoftDeleteMixin, Base):
    """
    Profile extension for a User with role='teacher'.

    Teacher.id is referenced by Section.class_teacher_id (FK constraint added
    in Migration 005 to resolve the deferred FK from Migration 004).
    """

    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint(
            "school_id", "employee_id",
            name="uq_teachers_school_employee_id",
        ),
        Index("ix_teachers_user_id",         "user_id"),
        Index("ix_teachers_school_id",        "school_id"),
        Index("ix_teachers_is_class_teacher", "is_class_teacher"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign keys ───────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        doc="1-to-1 link to the central User record.",
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        doc="School this teacher belongs to.",
    )

    # ── Professional details ───────────────────────────────────────────────────
    employee_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        doc="School-issued employee ID, unique within the school.",
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        doc="e.g. 'Mathematics', 'Science', 'Languages'.",
    )
    qualification: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        doc="e.g. 'B.Ed', 'M.Sc Physics', 'PhD Mathematics'.",
    )
    specialization: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        doc="Subject area of expertise.",
    )
    joining_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        doc="Date the teacher joined this school.",
    )
    is_class_teacher: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false",
        doc="True if the teacher is currently assigned as a class/homeroom teacher.",
    )

    # ── Personal ───────────────────────────────────────────────────────────────
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]]         = mapped_column(String(20), nullable=True)

    # ── Status ─────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true",
        doc="False = teacher is inactive/resigned.",
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    user:   Mapped["User"]   = relationship("User",   back_populates="teacher_profile")
    school: Mapped["School"] = relationship("School", foreign_keys=[school_id])
    # Migration 006 back-references (defined in course/session/assignment models)
    courses:     Mapped[List["Course"]]       = relationship("Course",       back_populates="teacher", foreign_keys="[Course.teacher_id]")
    sessions:    Mapped[List["ClassSession"]] = relationship("ClassSession", back_populates="teacher", foreign_keys="[ClassSession.teacher_id]")
    assignments: Mapped[List["Assignment"]]   = relationship("Assignment",   back_populates="teacher", foreign_keys="[Assignment.created_by]")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Teacher user_id={self.user_id} emp={self.employee_id!r}>"


# ── Parent ─────────────────────────────────────────────────────────────────────

class Parent(TimestampMixin, SoftDeleteMixin, Base):
    """
    Profile extension for a User with role='parent'.

    Parents are NOT school-scoped directly — a parent may have children in
    multiple schools. School scoping is implicit through their linked students.
    """

    __tablename__ = "parents"
    __table_args__ = (
        Index("ix_parents_user_id", "user_id"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign key ────────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        doc="1-to-1 link to the central User record.",
    )

    # ── Relation meta ──────────────────────────────────────────────────────────
    relation_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        doc="e.g. 'Father', 'Mother', 'Guardian', 'Grandparent'.",
    )
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Contact ────────────────────────────────────────────────────────────────
    address_line1:  Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2:  Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city:           Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state:          Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code:    Mapped[Optional[str]] = mapped_column(String(20),  nullable=True)
    alternate_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="parent_profile")
    student_links: Mapped[List["ParentStudentLink"]] = relationship(
        "ParentStudentLink",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Parent user_id={self.user_id} relation={self.relation_type!r}>"


# ── ParentStudentLink (M2M join table) ────────────────────────────────────────

class ParentStudentLink(TimestampMixin, Base):
    """
    Many-to-many join between Parent and Student.

    • One student can have multiple parents (mother + father + guardian).
    • One parent can have multiple students (siblings).
    • is_primary_contact: exactly one parent per student should be True
      (enforced at the service layer, not the DB level, to avoid complex partial
      unique indexes).
    """

    __tablename__ = "parent_student_links"
    __table_args__ = (
        UniqueConstraint("parent_id", "student_id", name="uq_parent_student_link"),
        Index("ix_psl_parent_id",  "parent_id"),
        Index("ix_psl_student_id", "student_id"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign keys ───────────────────────────────────────────────────────────
    parent_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("parents.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Metadata ───────────────────────────────────────────────────────────────
    is_primary_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false",
        doc="True = this parent is the first point of contact for the student.",
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    parent:  Mapped["Parent"]  = relationship("Parent",  back_populates="student_links")
    student: Mapped["Student"] = relationship("Student", back_populates="parent_links")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ParentStudentLink parent={self.parent_id} "
            f"student={self.student_id} primary={self.is_primary_contact}>"
        )
