import logging
import uuid
from typing import List, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, oauth2_scheme
from app.database.database import get_db
from app.models.school import AcademicYear, School
from app.models.user import User
from app.core.rbac import require_lecture_control_permission, verify_teacher_permission, has_lecture_control_permission, ALLOWED_LECTURE_CONTROL_ROLES


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

optional_bearer = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    auth: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer)
) -> Optional[User]:
    """
    Optional authentication dependency. Returns User if valid token present, otherwise None.
    """
    if not auth or not auth.credentials:
        return None
    try:
        from app.core.security import decode_access_token
        from sqlalchemy import select
        payload = decode_access_token(auth.credentials)
        if not payload or "sub" not in payload:
            return None
        user_id = uuid.UUID(payload["sub"])
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if user:
            return user
        role_claim = payload.get("role")
        email_claim = payload.get("email", "user@nexora.school")
        if role_claim:
            return User(id=user_id, role=role_claim, email=email_claim, is_active=True, is_verified=True)
    except Exception:
        return None
    return None


class RoleChecker:
    """
    Role-based access control dependency check.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user


class PermissionChecker:
    """
    Fine-grained permission check dependency.
    Validates that current user holds a role with resource:action permission.
    """
    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db = Depends(get_db),
    ) -> User:
        from app.services.role_service import role_service

        has_perm = await role_service.check_user_permission(
            db, current_user.id, self.resource, self.action
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: missing required '{self.resource}:{self.action}' permission.",
            )
        return current_user


async def get_current_tenant_school(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_school_code: Optional[str] = Header(None, alias="X-School-Code"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> School:
    """
    Resolve the current multi-tenant School entity.
    Order of resolution:
      1. X-Tenant-ID header (UUID)
      2. X-School-Code header (String)
      3. current_user.school_id (if user is authenticated & assigned to a school)
    """
    from app.services.school_service import school_service

    school: Optional[School] = None

    if x_tenant_id:
        try:
            school_uuid = uuid.UUID(x_tenant_id)
            school = await school_service.get_school(db, school_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Tenant-ID header format; must be UUID.",
            )
        except HTTPException:
            school = None

    if not school and x_school_code:
        try:
            school = await school_service.get_school_by_code(db, x_school_code)
        except HTTPException:
            school = None

    if not school and current_user and current_user.school_id:
        try:
            school = await school_service.get_school(db, current_user.school_id)
        except HTTPException:
            school = None

    if not school:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant school context is required. Provide X-Tenant-ID or X-School-Code header.",
        )

    if not school.is_active or school.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant school account is suspended or inactive.",
        )

    return school


async def get_current_tenant_academic_year(
    tenant_school: School = Depends(get_current_tenant_school),
    db: AsyncSession = Depends(get_db),
) -> AcademicYear:
    """
    Resolve the current active AcademicYear for the current tenant school.
    """
    from app.services.school_service import school_service

    ay = await school_service.get_current_academic_year(db, tenant_school.id)
    if not ay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active academic year configured for school '{tenant_school.name}'.",
        )
    return ay

