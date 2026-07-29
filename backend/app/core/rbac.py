"""
app/core/rbac.py
────────────────
Centralized Role-Based Access Control (RBAC) definitions and permission checkers.
"""

from enum import Enum
from typing import Optional, Set
from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user
from app.models.user import User

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
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency that enforces lecture control authorization.
    Raises HTTP 403 Forbidden if user's role is not authorized.
    """
    if not has_lecture_control_permission(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Teachers or Administrators can control lectures."
        )
    return current_user

# Alias for backward compatibility / flexibility
verify_teacher_permission = require_lecture_control_permission
