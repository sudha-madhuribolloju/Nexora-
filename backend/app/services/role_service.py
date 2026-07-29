"""
app/services/role_service.py
─────────────────────────────
Business logic for roles, permissions, and user-role assignments.

Design decisions:
  • All validation (duplicate check, system-role guard) lives HERE, not in the
    repository or route. Routes are thin; repositories are SQL-only.
  • System roles (is_system_role=True) cannot be updated or deleted via API to
    prevent accidental lock-out of the super_admin role.
  • assign_role_to_user is idempotent: if the user already has the role, a
    409 is returned rather than creating a duplicate row.
  • A module-level singleton (role_service = RoleService()) is imported by
    routes to avoid re-instantiating on every request.
"""

import uuid
from typing import List, Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roles import Permission, Role, UserRole
from app.repositories.role_repository import (
    permission_repo,
    role_repo,
    user_role_repo,
)
from app.schemas.roles import (
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    RoleWithPermissions,
    UserRoleResponse,
)


class RoleService:
    """Orchestrates RBAC operations across Role, Permission, and UserRole."""

    # ── Roles ──────────────────────────────────────────────────────────────────

    async def get_role_with_permissions(
        self, db: AsyncSession, role_id: uuid.UUID
    ) -> RoleWithPermissions:
        role = await role_repo.get_by_id(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found."
            )
        perms = await role_repo.get_role_permissions(db, role.id)
        perm_responses = [PermissionResponse.model_validate(p) for p in perms]
        return RoleWithPermissions(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system_role=role.is_system_role,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=perm_responses,
        )

    async def create_role(self, db: AsyncSession, data: RoleCreate) -> RoleWithPermissions:
        existing = await role_repo.get_by_name(db, data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role '{data.name}' already exists.",
            )
        try:
            role = await role_repo.create(
                db, data.model_dump(exclude={"permission_ids"})
            )
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role '{data.name}' already exists.",
            )

        # Attach requested permissions
        if data.permission_ids:
            for pid in data.permission_ids:
                perm = await permission_repo.get_by_id(db, pid)
                if not perm:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Permission {pid} not found.",
                    )
                await role_repo.add_permission(db, role.id, pid)

        return await self.get_role_with_permissions(db, role.id)

    async def get_role(self, db: AsyncSession, role_id: uuid.UUID) -> RoleWithPermissions:
        return await self.get_role_with_permissions(db, role_id)

    async def list_roles(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> tuple[Sequence[RoleWithPermissions], int]:
        roles = await role_repo.get_all(db, skip=skip, limit=limit)
        total = await role_repo.count(db)
        items = []
        for r in roles:
            items.append(await self.get_role_with_permissions(db, r.id))
        return items, total

    async def update_role(
        self, db: AsyncSession, role_id: uuid.UUID, data: RoleUpdate
    ) -> Role:
        role = await role_repo.get_by_id(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found."
            )
        if role.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System roles cannot be modified.",
            )
        return await role_repo.update(db, role, data.model_dump(exclude_none=True))

    async def delete_role(self, db: AsyncSession, role_id: uuid.UUID) -> None:
        role = await role_repo.get_by_id(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found."
            )
        if role.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System roles cannot be deleted.",
            )
        await role_repo.hard_delete(db, role)

    # ── Permissions ────────────────────────────────────────────────────────────

    async def create_permission(
        self, db: AsyncSession, data: PermissionCreate
    ) -> Permission:
        existing = await permission_repo.get_by_resource_action(
            db, data.resource, data.action
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Permission '{data.resource}:{data.action}' already exists.",
            )
        return await permission_repo.create(db, data.model_dump())

    async def get_permission(
        self, db: AsyncSession, permission_id: uuid.UUID
    ) -> Permission:
        perm = await permission_repo.get_by_id(db, permission_id)
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found."
            )
        return perm

    async def list_permissions(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 200
    ) -> tuple[Sequence[Permission], int]:
        perms = await permission_repo.get_all(db, skip=skip, limit=limit)
        total = await permission_repo.count(db)
        return perms, total

    async def update_permission(
        self, db: AsyncSession, permission_id: uuid.UUID, data: PermissionUpdate
    ) -> Permission:
        perm = await permission_repo.get_by_id(db, permission_id)
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found."
            )
        return await permission_repo.update(db, perm, data.model_dump(exclude_none=True))

    async def add_permission_to_role(
        self,
        db: AsyncSession,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> None:
        if not await role_repo.get_by_id(db, role_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found."
            )
        if not await permission_repo.get_by_id(db, permission_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found."
            )
        try:
            await role_repo.add_permission(db, role_id, permission_id)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Permission is already assigned to this role.",
            )

    async def remove_permission_from_role(
        self,
        db: AsyncSession,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> None:
        removed = await role_repo.remove_permission(db, role_id, permission_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This role does not have that permission.",
            )

    # ── User Role Assignments ──────────────────────────────────────────────────

    async def assign_role_to_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        granted_by: Optional[uuid.UUID] = None,
    ) -> UserRoleResponse:
        role = await role_repo.get_by_id(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found."
            )
        try:
            ur = await user_role_repo.assign_role(db, user_id, role_id, granted_by)
            role_resp = RoleResponse.model_validate(role)
            return UserRoleResponse(
                id=ur.id,
                user_id=ur.user_id,
                role_id=ur.role_id,
                granted_at=ur.granted_at,
                granted_by=ur.granted_by,
                role=role_resp,
            )
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has this role.",
            )

    async def revoke_role_from_user(
        self, db: AsyncSession, user_id: uuid.UUID, role_id: uuid.UUID
    ) -> None:
        removed = await user_role_repo.revoke_role(db, user_id, role_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User does not have this role.",
            )

    async def get_user_roles(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> List[UserRoleResponse]:
        user_roles = await user_role_repo.get_user_roles(db, user_id)
        resps = []
        for ur in user_roles:
            role = await role_repo.get_by_id(db, ur.role_id)
            role_resp = RoleResponse.model_validate(role) if role else None
            resps.append(
                UserRoleResponse(
                    id=ur.id,
                    user_id=ur.user_id,
                    role_id=ur.role_id,
                    granted_at=ur.granted_at,
                    granted_by=ur.granted_by,
                    role=role_resp,
                )
            )
        return resps

    async def check_user_permission(
        self, db: AsyncSession, user_id: uuid.UUID, resource: str, action: str
    ) -> bool:
        """
        Return True if the user has any role that grants resource:action.
        Used by dependency-injection permission guards.
        """
        user_roles = await user_role_repo.get_user_roles(db, user_id)
        for ur in user_roles:
            perms = await role_repo.get_role_permissions(db, ur.role_id)
            for p in perms:
                if p.resource == resource and p.action == action:
                    return True
        return False


# Module-level singleton
role_service = RoleService()
