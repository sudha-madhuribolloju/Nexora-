"""
app/models/school.py
─────────────────────
School and AcademicYear ORM models.

Why these tables exist
──────────────────────
• School   — Every piece of data in the system (students, attendance, exams,
             AI conversations) is scoped to a school. This table is the root
             multi-tenancy anchor. A school_id column or FK appears on almost
             every subsequent table.

• AcademicYear — Academic data (classes, sections, exams, attendance) changes
             every school year. Without explicit year scoping, it is impossible
             to compare performance across years or archive old data cleanly.
             One AcademicYear row may be marked is_current=True per school; the
             service layer enforces this uniqueness.

Design decisions
────────────────
• subscription_tier uses VARCHAR + CheckConstraint instead of a PostgreSQL
  ENUM type. PostgreSQL ENUM types require DROP TYPE CASCADE to rename or
  remove, making migrations brittle. VARCHAR + CHECK is equally safe and far
  easier to ALTER.

• AcademicYear has NO soft-delete. Once a school year ends it becomes read-
  only history. Archiving is handled by is_current=False, not deletion.

• The school_id FK on the users table was created as a bare column in
  Migration 000 and the actual FK constraint is added in Migration 002 (this
  migration) via ALTER TABLE. This "deferred FK" pattern is necessary because
  the referenced table (schools) must exist before the constraint is created.

Sample records
──────────────
schools       : { code: "GHS001", name: "Greenwood High School", country: "India",
                  timezone: "Asia/Kolkata", subscription_tier: "pro" }
academic_years: { school_id: <GHS001>, name: "2025-2026",
                  start_date: 2025-06-01, end_date: 2026-03-31, is_current: true }
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
    from app.models.academic import Class, Section, Subject  # Migration 003


# ── School ─────────────────────────────────────────────────────────────────────

class School(TimestampMixin, SoftDeleteMixin, Base):
    """
    Root multi-tenancy entity. Every school is an independent tenant.
    All subsequent tables carry a school_id FK for data isolation.
    """

    __tablename__ = "schools"
    __table_args__ = (
        UniqueConstraint("code", name="uq_schools_code"),
        CheckConstraint(
            "subscription_tier IN ('free', 'basic', 'pro', 'enterprise')",
            name="ck_schools_subscription_tier",
        ),
        Index("ix_schools_code",      "code"),
        Index("ix_schools_name",      "name"),
        Index("ix_schools_is_active", "is_active"),
    )

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Identity ───────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
        doc="Full legal name of the school.",
    )
    code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True,
        doc="Short unique school code used in URLs and reports (e.g. 'GHS001').",
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # ── Address ────────────────────────────────────────────────────────────────
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city:          Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state:         Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country:       Mapped[str]           = mapped_column(
        String(100), nullable=False, server_default="India"
    )
    postal_code:   Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # ── Operational ────────────────────────────────────────────────────────────
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Asia/Kolkata",
        doc="IANA timezone string: 'Asia/Kolkata', 'America/New_York', etc.",
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="CDN URL for the school's logo image."
    )
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Subscription ───────────────────────────────────────────────────────────
    subscription_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="free",
        doc="free | basic | pro | enterprise — governs feature access.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true",
        doc="False = school subscription lapsed or suspended.",
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    academic_years: Mapped[List["AcademicYear"]] = relationship(
        "AcademicYear",
        back_populates="school",
        cascade="all, delete-orphan",
        order_by="AcademicYear.start_date.desc()",
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="school",
        foreign_keys="[User.school_id]",
        lazy="select",
    )
    # Populated by Migration 003
    # classes:  relationship("Class",  ...)
    # sections: relationship("Section", ...)
    # subjects: relationship("Subject", ...)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<School code={self.code!r} name={self.name!r}>"


# ── AcademicYear ───────────────────────────────────────────────────────────────

class AcademicYear(TimestampMixin, Base):
    """
    Represents one academic year within a school (e.g. "2025-2026").

    Constraints:
      • Unique (school_id, name) — each school can have only one year with
        a given name.
      • At most one row per school with is_current=True — enforced by the
        service layer (set_current_year atomically flips all others to False).

    No soft-delete: academic years become immutable history once they end.
    Historical attendance, exams, and results reference them permanently.
    """

    __tablename__ = "academic_years"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_academic_years_school_name"),
        Index("ix_academic_years_school_id",  "school_id"),
        Index("ix_academic_years_is_current", "is_current"),
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
        String(100), nullable=False,
        doc="Human-readable label, e.g. '2025-2026'.",
    )
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False,
        doc="First day of the academic year (inclusive).",
    )
    end_date: Mapped[date] = mapped_column(
        Date, nullable=False,
        doc="Last day of the academic year (inclusive).",
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false",
        doc="True for the active year. Only one row per school should be True.",
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    school: Mapped["School"] = relationship("School", back_populates="academic_years")
    # classes added in Migration 003
    # classes: Mapped[List["Class"]] = relationship(...)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AcademicYear school={self.school_id} name={self.name!r} current={self.is_current}>"
