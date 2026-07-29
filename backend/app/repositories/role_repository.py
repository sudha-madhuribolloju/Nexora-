"""
app/repositories/role_repository.py
─────────────────────────────────────
Async repositories for Role, Permission, and UserRole.

All three extend BaseRepository for generic CRUD and add domain-specific
query methods. Service layer calls these; routes call the service.
No business logic lives here — only SQL.
"""

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roles import Permission, Role, RolePermission, UserRole
from app.repositories.base_repository import BaseRepository


# ── RoleRepository ─────────────────────────────────────────────────────────────

class RoleRepository(BaseRepository[Role]):
    """Database operations for the roles table."""

    def __init__(self) -> None:
        super().__init__(Role)

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        """Return the role with this exact name, or None."""
        result = await db.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def get_role_permissions(
        self, db: AsyncSession, role_id: uuid.UUID
    ) -> Sequence[Permission]:
        """Return all Permission objects associated with a given role."""
        result = await db.execute(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == role_id)
        )
        return result.scalars().all()

    async def add_permission(
        self,
        db: AsyncSession,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> RolePermission:
        """Create a role ↔ permission link."""
        rp = RolePermission(role_id=role_id, permission_id=permission_id)
        db.add(rp)
        await db.commit()
        await db.refresh(rp)
        return rp

    async def remove_permission(
        self,
        db: AsyncSession,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> bool:
        """Remove a role ↔ permission link. Returns True if it existed."""
        result = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        rp = result.scalar_one_or_none()
        if rp:
            await db.delete(rp)
            await db.commit()
            return True
        return False


# ── PermissionRepository ───────────────────────────────────────────────────────

class PermissionRepository(BaseRepository[Permission]):
    """Database operations for the permissions table."""

    def __init__(self) -> None:
        super().__init__(Permission)

    async def get_by_resource_action(
        self, db: AsyncSession, resource: str, action: str
    ) -> Optional[Permission]:
        """Return permission by unique (resource, action) pair."""
        result = await db.execute(
            select(Permission).where(
                Permission.resource == resource,
                Permission.action == action,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_resource(
        self, db: AsyncSession, resource: str
    ) -> Sequence[Permission]:
        """Return all permissions for a given resource domain."""
        result = await db.execute(
            select(Permission).where(Permission.resource == resource)
        )
        return result.scalars().all()


# ── UserRoleRepository ─────────────────────────────────────────────────────────

class UserRoleRepository:
    """Database operations for the user_roles join table."""

    async def assign_role(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        granted_by: Optional[uuid.UUID] = None,
    ) -> UserRole:
        """Grant a role to a user."""
        ur = UserRole(user_id=user_id, role_id=role_id, granted_by=granted_by)
        db.add(ur)
        await db.commit()
        await db.refresh(ur)
        return ur

    async def revoke_role(
        self, db: AsyncSession, user_id: uuid.UUID, role_id: uuid.UUID
    ) -> bool:
        """Revoke a role from a user. Returns True if the grant existed."""
        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        ur = result.scalar_one_or_none()
        if ur:
            await db.delete(ur)
            await db.commit()
            return True
        return False

    async def get_user_roles(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Sequence[UserRole]:
        """Return all UserRole rows for a user with role eagerly loaded."""
        result = await db.execute(
            select(UserRole)
            .where(UserRole.user_id == user_id)
            .options(selectinload(UserRole.role))
        )
        return result.scalars().all()

    async def get_role_users(
        self, db: AsyncSession, role_id: uuid.UUID
    ) -> Sequence[UserRole]:
        """Return all UserRole rows for a role with user eagerly loaded."""
        result = await db.execute(
            select(UserRole)
            .where(UserRole.role_id == role_id)
            .options(selectinload(UserRole.user))
        )
        return result.scalars().all()

    async def user_has_role(
        self, db: AsyncSession, user_id: uuid.UUID, role_name: str
    ) -> bool:
        """Quick check: does this user have a role with the given name?"""
        result = await db.execute(
            select(UserRole)
            .join(Role, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                Role.name == role_name,
            )
        )
        return result.scalar_one_or_none() is not None


# ── Module-level singletons (imported by service layer) ───────────────────────
role_repo = RoleRepository()
permission_repo = PermissionRepository()
user_role_repo = UserRoleRepository()
