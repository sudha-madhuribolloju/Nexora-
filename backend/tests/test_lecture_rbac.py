"""
tests/test_lecture_rbac.py
───────────────────────────
Tests for lecture control RBAC permissions and FastAPI endpoint authorization.
"""

import pytest
from fastapi import HTTPException
from app.core.rbac import (
    has_lecture_control_permission,
    verify_lecture_control_role_string,
    require_lecture_control_permission,
    ALLOWED_LECTURE_CONTROL_ROLES,
)
from app.models.user import User


def test_has_lecture_control_permission_roles():
    """Verify that only Teachers, Institute Admins, and Super Admins have lecture control permission."""
    teacher_user = User(role="Teacher")
    inst_admin_user = User(role="Institute Admin")
    super_admin_user = User(role="Super Admin")

    student_user = User(role="Student")
    parent_user = User(role="Parent")
    principal_user = User(role="Principal")

    # Allowed roles
    assert has_lecture_control_permission(teacher_user) is True
    assert has_lecture_control_permission(inst_admin_user) is True
    assert has_lecture_control_permission(super_admin_user) is True

    # Forbidden roles
    assert has_lecture_control_permission(student_user) is False
    assert has_lecture_control_permission(parent_user) is False
    assert has_lecture_control_permission(principal_user) is False


def test_verify_lecture_control_role_string():
    """Verify role string checking helper."""
    assert verify_lecture_control_role_string("Teacher") is True
    assert verify_lecture_control_role_string("teacher") is True
    assert verify_lecture_control_role_string("Institute Admin") is True
    assert verify_lecture_control_role_string("Super Admin") is True

    assert verify_lecture_control_role_string("Student") is False
    assert verify_lecture_control_role_string("Parent") is False
    assert verify_lecture_control_role_string("Principal") is False


@pytest.mark.asyncio
async def test_require_lecture_control_permission_dependency():
    """Verify FastAPI dependency raises HTTP 403 Forbidden for unauthorized roles."""
    teacher_user = User(role="Teacher")
    student_user = User(role="Student")

    # Teacher passes
    res = await require_lecture_control_permission(teacher_user)
    assert res == teacher_user

    # Student raises 403 Forbidden with exact specified detail message
    with pytest.raises(HTTPException) as exc_info:
        await require_lecture_control_permission(student_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Only Teachers or Administrators can control lectures."
