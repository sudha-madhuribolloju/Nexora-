"""
app/models/roles.py
───────────────────
RBAC tables: roles, permissions, role_permissions, user_roles.

Design decisions:
  • Role.is_system_role = True  → seeded by migration; cannot be deleted via
    API. Prevents accidental removal of core roles (super_admin, student, …).
  • Permission is modeled as resource + action pairs rather than a flat string
    so permission audits can filter by resource ("students") or action ("read")
    independently.
  • RolePermission and UserRole are explicit join tables (not association_proxy)
    because both may carry metadata:
      - RolePermission: could carry "scope" (school-level override) in future.
      - UserRole: carries granted_at + granted_by for a full grant audit trail.
  • No school_id scoping on roles: roles are system-wide definitions.
    School-specific customisation is handled at the service layer by filtering
    permissions the school's subscription tier grants access to.

Sample records
──────────────
roles        : { name: "teacher",      is_system_role: true  }
permissions  : { resource: "attendance", action: "write" }
role_perms   : { role_id: <teacher>, permission_id: <attendance:write> }
user_roles   : { user_id: <alice>, role_id: <teacher>, granted_by: <admin> }
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


# ── Role ───────────────────────────────────────────────────────────────────────

class Role(TimestampMixin, Base):
    """
    Defines a named set of permissions (e.g. teacher, student, school_admin).
    System roles are seeded by Migration 001 and protected from API deletion.
    """

    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("name", name="uq_roles_name"),
        Index("ix_roles_name", "name"),
        Index("ix_roles_is_system_role", "is_system_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Unique role identifier: super_admin | school_admin | teacher | student | parent | staff",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
        doc="True = seeded by migration; cannot be renamed or deleted via API.",
    )

    # Relationships
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan", lazy="selectin"
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    @property
    def permissions(self) -> List["Permission"]:
        """Extract Permission objects from role_permissions join records."""
        try:
            return [rp.permission for rp in self.role_permissions if rp.permission is not None]
        except Exception:
            return []

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role name={self.name!r} system={self.is_system_role}>"


# ── Permission ─────────────────────────────────────────────────────────────────

class Permission(TimestampMixin, Base):
    """
    Atomic capability: e.g. resource='students', action='read'.

    Unique constraint on (resource, action) prevents duplicate entries.
    Applications check permissions as f"{resource}:{action}" strings.
    """

    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
        Index("ix_permissions_resource", "resource"),
        Index("ix_permissions_action", "action"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="The domain entity this permission applies to: students, attendance, exams, …",
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="The operation allowed: read | write | delete | manage | use",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    @property
    def code(self) -> str:
        """Convenience shorthand: 'students:read'."""
        return f"{self.resource}:{self.action}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Permission {self.code!r}>"


# ── RolePermission (join table) ────────────────────────────────────────────────

class RolePermission(Base):
    """
    Many-to-many join: which permissions belong to which role.
    Cascade delete: removing a Role also removes all its RolePermission rows.
    """

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship(
        "Permission", back_populates="role_permissions", lazy="joined"
    )


# ── UserRole (join table) ──────────────────────────────────────────────────────

class UserRole(Base):
    """
    Many-to-many join: which roles are assigned to which user.

    Tracks who granted the role (granted_by) for full audit trail.
    granted_by is stored as a bare UUID (no FK) to avoid circular dependency
    and to survive user hard-deletes without breaking the audit record.
    """

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles"),
        Index("ix_user_roles_user_id", "user_id"),
        Index("ix_user_roles_role_id", "role_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    granted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        doc="UUID of the admin who granted this role. Stored bare for audit durability.",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserRole user={self.user_id} role={self.role_id}>"
