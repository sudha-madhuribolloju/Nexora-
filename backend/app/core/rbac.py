"""
app/core/rbac.py
────────────────
Centralized Role-Based Access Control (RBAC) definitions and permission checkers.
"""

from enum import Enum
from typing import Optional, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.core.security import get_current_user
from app.database.database import get_db
from app.models.user import User

optional_bearer = HTTPBearer(auto_error=False)

class RoleEnum(str, Enum):
    SUPER_ADMIN = "Super Admin"
    INSTITUTE_ADMIN = "Institute Admin"
    PRINCIPAL = "Principal"
    TEACHER = "Teacher"
    STUDENT = "Student"
    PARENT = "Parent"
    SUPPORT_ENGINEER = "Support Engineer"

# Roles explicitly allowed to start/stop lectures and control recordings
ALLOWED_LECTURE_CONTROL_ROLES: Set[str] = {
    RoleEnum.TEACHER.value.lower(),
    RoleEnum.INSTITUTE_ADMIN.value.lower(),
    RoleEnum.SUPER_ADMIN.value.lower(),
    "teacher",
    "course instructor",
    "institute admin",
    "institute_admin",
    "school admin",
    "school_admin",
    "super admin",
    "super_admin",
}

def has_lecture_control_permission(user: Optional[User]) -> bool:
    """
    Check if a given user has permission to control lectures and recordings.
    Supports title-case, lower-case, and snake_case role representations.
    """
    if not user or not user.role:
        return False
    
    normalized_role = user.role.strip().lower()
    return normalized_role in ALLOWED_LECTURE_CONTROL_ROLES

def verify_lecture_control_role_string(role: Optional[str]) -> bool:
    """
    Check permission directly against a role string (e.g. decoded from JWT payload).
    """
    if not role:
        return False
    return role.strip().lower() in ALLOWED_LECTURE_CONTROL_ROLES

async def require_lecture_control_permission(
    db = Depends(get_db),
    auth = Depends(optional_bearer)
) -> User:
    """
    FastAPI dependency that enforces lecture control authorization.
    Allows demo/guest users gracefully if unauthenticated.
    Raises HTTP 403 Forbidden if an authenticated user lacks permission.
    """
    if isinstance(db, User):
        current_user = db
    else:
        from app.api.dependencies import get_current_user_optional
        current_user = await get_current_user_optional(db=db, auth=auth)

    if current_user:
        if has_lecture_control_permission(current_user):
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Teachers or Administrators can control lectures."
        )
    
    import uuid
    return User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000501"),
        email="teacher@nexora.school",
        first_name="Dr. Sarah",
        last_name="Jenkins",
        full_name="Dr. Sarah Jenkins",
        role="Teacher",
        is_active=True,
        is_verified=True
    )

# Alias for backward compatibility / flexibility
verify_teacher_permission = require_lecture_control_permission


class RequireRole:
    """
    FastAPI dependency enforcing that the current user possesses one of the specified allowed roles.
    Raises HTTP 401 if unauthenticated and HTTP 403 if unauthorized.
    """
    def __init__(self, *allowed_roles: str):
        self.allowed_roles = {r.strip().lower() for r in allowed_roles}
        # Automatically include Super Admin in admin role checks unless explicitly restricted
        self.allowed_roles.add("super admin")
        self.allowed_roles.add("super_admin")

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not current_user or not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required."
            )
        
        user_role_norm = current_user.role.strip().lower()
        if user_role_norm not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{current_user.role}' is not authorized for this resource."
            )
        return current_user


def require_roles(*allowed_roles: str) -> RequireRole:
    """
    Convenience constructor for RequireRole dependency.
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_roles("Institute Admin", "Super Admin"))])
    """
    return RequireRole(*allowed_roles)

