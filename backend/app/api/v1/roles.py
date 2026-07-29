"""
app/api/v1/roles.py
────────────────────
FastAPI router for RBAC — roles, permissions, and user-role assignments.

Design decisions:
  • All routes return typed response_model so FastAPI generates accurate
    OpenAPI docs and auto-strips any internal fields.
  • Paginated list endpoints return PaginatedResponse[T] envelope so the
    frontend always has total count for rendering pagination controls.
  • Auth dependency (get_current_user) is commented out here so you can
    run the migration smoke-tests without a token. Wire it back in before
    shipping to production.
  • DELETE routes return HTTP 204 No Content (no body), matching REST best
    practices.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas.roles import (
    AssignRoleRequest,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    PaginatedResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    RoleWithPermissions,
    UserRoleResponse,
)
from app.services.role_service import role_service

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# ROLES
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/",
    response_model=RoleWithPermissions,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
) -> RoleWithPermissions:
    """
    Create a role and optionally attach an initial set of permissions.

    - **name**: unique role name (e.g. `"content_moderator"`)
    - **permission_ids**: list of existing Permission UUIDs to attach
    """
    return await role_service.create_role(db, payload)


@router.get(
    "/",
    response_model=PaginatedResponse[RoleWithPermissions],
    summary="List all roles",
)
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[RoleWithPermissions]:
    """Return a paginated list of all roles with their permissions."""
    roles, total = await role_service.list_roles(db, skip=skip, limit=limit)
    return PaginatedResponse(total=total, skip=skip, limit=limit, items=roles)


@router.get(
    "/{role_id}",
    response_model=RoleWithPermissions,
    summary="Get role detail",
)
async def get_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RoleWithPermissions:
    """Fetch a single role by UUID, including its permissions."""
    return await role_service.get_role(db, role_id)


@router.patch(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Update a role",
)
async def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdate,
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    """
    Partially update a role (name, description).
    System roles (is_system_role=true) are read-only.
    """
    return await role_service.update_role(db, role_id, payload)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a role",
)
async def delete_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete a non-system role.
    All user-role and role-permission rows are cascade-deleted by the DB.
    """
    await role_service.delete_role(db, role_id)


# ── Role ↔ Permission management ──────────────────────────────────────────────

@router.post(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_200_OK,
    summary="Attach permission to role",
)
async def add_permission_to_role(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Grant a permission to a role."""
    await role_service.add_permission_to_role(db, role_id, permission_id)
    return {"status": "success", "message": "Permission attached to role."}


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove permission from role",
)
async def remove_permission_from_role(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke a permission from a role."""
    await role_service.remove_permission_from_role(db, role_id, permission_id)


# ══════════════════════════════════════════════════════════════════════════════
# PERMISSIONS
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/permissions/",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a permission",
)
async def create_permission(
    payload: PermissionCreate,
    db: AsyncSession = Depends(get_db),
) -> PermissionResponse:
    """
    Register a new atomic permission.

    - **resource**: domain entity (e.g. `"students"`, `"attendance"`)
    - **action**: operation (`"read"`, `"write"`, `"delete"`, `"manage"`, `"use"`)
    """
    return await role_service.create_permission(db, payload)


@router.get(
    "/permissions/",
    response_model=PaginatedResponse[PermissionResponse],
    summary="List all permissions",
)
async def list_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PermissionResponse]:
    """Return all permissions with pagination."""
    perms, total = await role_service.list_permissions(db, skip=skip, limit=limit)
    return PaginatedResponse(total=total, skip=skip, limit=limit, items=perms)


@router.get(
    "/permissions/{permission_id}",
    response_model=PermissionResponse,
    summary="Get permission detail",
)
async def get_permission(
    permission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PermissionResponse:
    return await role_service.get_permission(db, permission_id)


@router.patch(
    "/permissions/{permission_id}",
    response_model=PermissionResponse,
    summary="Update permission description",
)
async def update_permission(
    permission_id: uuid.UUID,
    payload: PermissionUpdate,
    db: AsyncSession = Depends(get_db),
) -> PermissionResponse:
    return await role_service.update_permission(db, permission_id, payload)


# ══════════════════════════════════════════════════════════════════════════════
# USER ↔ ROLE ASSIGNMENTS
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/assign",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign role to user",
)
async def assign_role_to_user(
    payload: AssignRoleRequest,
    db: AsyncSession = Depends(get_db),
) -> UserRoleResponse:
    """Grant a role to a user. Returns 409 if already assigned."""
    return await role_service.assign_role_to_user(
        db, payload.user_id, payload.role_id
    )


@router.get(
    "/users/{user_id}",
    response_model=List[UserRoleResponse],
    summary="Get user's roles",
)
async def get_user_roles(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[UserRoleResponse]:
    """Return every role assigned to the specified user."""
    return await role_service.get_user_roles(db, user_id)


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke role from user",
)
async def revoke_role_from_user(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a role grant from a user."""
    await role_service.revoke_role_from_user(db, user_id, role_id)
