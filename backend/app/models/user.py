"""
app/models/user.py
──────────────────
Upgraded User model — UUID primary key, profile fields, soft-delete support,
and RBAC relationship hooks.

Design decisions:
  • UUID PK: globally unique across shards/services; safe to expose in URLs.
  • role (String): kept as a "primary role shorthand" for simple middleware
    checks (e.g. bearer token payload). Fine-grained RBAC uses user_roles M2M.
  • school_id: nullable — super admins are not scoped to any school. The FK
    constraint to schools.id is added in Migration 002 (after schools table
    is created) via ALTER TABLE. The column exists here as a bare UUID.
  • All relationships use string references to avoid circular imports.
  • back_populates are declared here; the inverse sides live in their own
    model files (roles.py, school.py, people.py, …).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.roles import UserRole
    from app.models.school import School
    from app.models.people import Student, Teacher, Parent
    from app.models.notification import Notification
    from app.models.document import Document
    from app.models.knowledge_base import KnowledgeBaseArticle


class User(TimestampMixin, SoftDeleteMixin, Base):
    """
    Central identity record for every actor in the system.

    One User row exists per human regardless of their role (student, teacher,
    parent, admin). Profile extension tables (students, teachers, parents) carry
    the role-specific details and back-reference user_id with a 1-to-1 FK.

    Sample record
    ─────────────
    id            : a1b2c3d4-…-uuid4
    email         : alice@nexora.school
    role          : teacher          ← shorthand for JWT / middleware
    is_active     : true
    first_name    : Alice
    last_name     : Johnson
    school_id     : <school UUID>    ← NULL for super admins
    is_deleted    : false
    created_at    : 2026-07-23T10:00:00Z
    """

    __tablename__ = "users"

    # ── Primary key ────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key.",
    )

    # ── Authentication ─────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique login email. Always stored lower-case.",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        doc="bcrypt hash of the user's password.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default="true",
        doc="False = account suspended; blocks login.",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
        doc="True = email verified via OTP.",
    )

    @property
    def email_verified(self) -> bool:
        return self.is_verified


    # ── Primary role (shorthand for JWT / quick permission checks) ────────────
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc=(
            "Primary role shorthand: super_admin | school_admin | teacher | "
            "student | parent | staff. Fine-grained RBAC lives in user_roles."
        ),
    )

    # ── Profile ────────────────────────────────────────────────────────────────
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="S3 / CDN URL to profile picture."
    )

    # ── School scoping ─────────────────────────────────────────────────────────
    # FK constraint to schools.id is added in Migration 002 via ALTER TABLE.
    # Declared as a bare UUID column here so the column exists before schools.
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
        doc="School this user belongs to. NULL = super admin.",
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    # School (many-to-one; FK constraint added by Migration 002)
    school: Mapped[Optional["School"]] = relationship(
        "School",
        back_populates="users",
        foreign_keys="[User.school_id]",
        lazy="select",
    )

    # Roles (many-to-many via user_roles join table)
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Profile extension tables (1-to-1, defined in people.py)
    student_profile: Mapped[Optional["Student"]] = relationship(
        "Student", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    teacher_profile: Mapped[Optional["Teacher"]] = relationship(
        "Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    parent_profile: Mapped[Optional["Parent"]] = relationship(
        "Parent", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    # Notifications (1-to-many, defined in notification.py)
    notifications_received: Mapped[List["Notification"]] = relationship(
        "Notification",
        foreign_keys="[Notification.recipient_id]",
        back_populates="recipient",
        cascade="all, delete-orphan",
    )

    # Documents uploaded by this user (1-to-many, defined in document.py)
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        foreign_keys="[Document.uploaded_by]",
        back_populates="uploader",
        cascade="all, delete-orphan",
    )

    # Knowledge base articles authored by this user (1-to-many)
    kb_articles: Mapped[List["KnowledgeBaseArticle"]] = relationship(
        "KnowledgeBaseArticle",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    # Convenience helpers
    @property
    def full_name(self) -> str:
        parts = filter(None, [self.first_name, self.last_name])
        return " ".join(parts) or self.email

    @full_name.setter
    def full_name(self, val: Optional[str]) -> None:
        if val:
            parts = val.strip().split(" ", 1)
            self.first_name = parts[0]
            self.last_name = parts[1] if len(parts) > 1 else ""
        else:
            self.first_name = None
            self.last_name = None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"