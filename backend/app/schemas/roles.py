"""
app/schemas/roles.py
─────────────────────
Pydantic v2 schemas (request / response) for the RBAC module.

Design decisions:
  • Separate Create / Update / Response classes follow the "schema per intent"
    pattern: Create carries all required fields, Update only optional ones
    (partial update / PATCH semantics), Response carries the DB-generated fields.
  • model_config = ConfigDict(from_attributes=True) enables ORM mode so
    FastAPI can return SQLAlchemy model instances directly.
  • Nested RoleWithPermissions embeds permission list to avoid a second
    round-trip; used for single-role detail endpoints.
  • Generic PaginatedResponse[T] is defined here and imported where needed.
"""

import uuid
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ── Permission Schemas ─────────────────────────────────────────────────────────

class PermissionBase(BaseModel):
    resource: str = Field(..., max_length=100, examples=["students"])
    action: str = Field(..., max_length=50, examples=["read"])
    description: Optional[str] = Field(None, examples=["View student records"])


class PermissionCreate(PermissionBase):
    """Payload to create a new permission entry."""
    pass


class PermissionUpdate(BaseModel):
    """Partial update for a permission's description."""
    description: Optional[str] = None


class PermissionResponse(PermissionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ── Role Schemas ───────────────────────────────────────────────────────────────

class RoleBase(BaseModel):
    name: str = Field(..., max_length=100, examples=["teacher"])
    description: Optional[str] = Field(None, examples=["Teaching staff access"])
    is_system_role: bool = Field(default=False)


class RoleCreate(RoleBase):
    """
    Payload to create a role.
    permission_ids: optional list of existing Permission UUIDs to attach.
    """
    permission_ids: Optional[List[uuid.UUID]] = None


class RoleUpdate(BaseModel):
    """Partial update — only non-None fields are applied."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class RoleWithPermissions(RoleResponse):
    """Role detail response including embedded permissions list."""
    permissions: List[PermissionResponse] = []


# ── UserRole Schemas ───────────────────────────────────────────────────────────

class AssignRoleRequest(BaseModel):
    """Payload to grant a role to a user."""
    user_id: uuid.UUID
    role_id: uuid.UUID


class RevokeRoleRequest(BaseModel):
    """Payload to revoke a role from a user."""
    user_id: uuid.UUID
    role_id: uuid.UUID


class UserRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_at: datetime
    granted_by: Optional[uuid.UUID] = None
    role: Optional[RoleResponse] = None


# ── Generic Paginated Wrapper ──────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list envelope used across all list endpoints."""
    total: int
    skip: int
    limit: int
    items: List[T]
