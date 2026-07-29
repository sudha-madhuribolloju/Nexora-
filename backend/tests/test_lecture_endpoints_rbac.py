"""
tests/test_lecture_endpoints_rbac.py
─────────────────────────────────────
Integration tests for protected lecture control endpoints in FastAPI.
Verifies JWT authentication, RBAC authorization, HTTP 403 Forbidden responses,
and complete lecture lifecycle handling.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.user import User

client = TestClient(app)

# Test User Data & Tokens
TEACHER_ID = "00000000-0000-0000-0000-000000000001"
INSTITUTE_ADMIN_ID = "00000000-0000-0000-0000-000000000002"
SUPER_ADMIN_ID = "00000000-0000-0000-0000-000000000003"
STUDENT_ID = "00000000-0000-0000-0000-000000000004"
PARENT_ID = "00000000-0000-0000-0000-000000000005"
PRINCIPAL_ID = "00000000-0000-0000-0000-000000000006"

teacher_token = create_access_token(subject=TEACHER_ID, role="Teacher", email="teacher@nexora.school")
inst_admin_token = create_access_token(subject=INSTITUTE_ADMIN_ID, role="Institute Admin", email="admin@nexora.school")
super_admin_token = create_access_token(subject=SUPER_ADMIN_ID, role="Super Admin", email="superadmin@nexora.school")

student_token = create_access_token(subject=STUDENT_ID, role="Student", email="student@nexora.school")
parent_token = create_access_token(subject=PARENT_ID, role="Parent", email="parent@nexora.school")
principal_token = create_access_token(subject=PRINCIPAL_ID, role="Principal", email="principal@nexora.school")


def get_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


# ── 1. Forbidden Role Tests (Student, Parent, Principal) ──────────────────────

@pytest.mark.parametrize("token, role_name", [
    (student_token, "Student"),
    (parent_token, "Parent"),
    (principal_token, "Principal"),
])
def test_start_lecture_forbidden_for_unauthorized_roles(token, role_name):
    """Students, Parents, and Principals MUST receive 403 Forbidden on POST /api/v1/lecture/start."""
    response = client.post("/api/v1/lecture/start", headers=get_headers(token), json={"title": "Unauthorized Start"})
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Only Teachers or Administrators can control lectures."


@pytest.mark.parametrize("token, role_name", [
    (student_token, "Student"),
    (parent_token, "Parent"),
    (principal_token, "Principal"),
])
def test_stop_lecture_forbidden_for_unauthorized_roles(token, role_name):
    """Students, Parents, and Principals MUST receive 403 Forbidden on POST /api/v1/lecture/stop."""
    response = client.post("/api/v1/lecture/stop", headers=get_headers(token), json={"duration": 120.0})
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Only Teachers or Administrators can control lectures."


@pytest.mark.parametrize("token, role_name", [
    (student_token, "Student"),
    (parent_token, "Parent"),
    (principal_token, "Principal"),
])
def test_start_recording_forbidden_for_unauthorized_roles(token, role_name):
    """Students, Parents, and Principals MUST receive 403 Forbidden on POST /api/v1/lecture/default/recording/start."""
    response = client.post("/api/v1/lecture/default/recording/start", headers=get_headers(token))
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Only Teachers or Administrators can control lectures."


# ── 2. Authorized Role Tests (Teacher, Institute Admin, Super Admin) ──────────

@pytest.mark.parametrize("token, role_name", [
    (teacher_token, "Teacher"),
    (inst_admin_token, "Institute Admin"),
    (super_admin_token, "Super Admin"),
])
def test_start_lecture_allowed_for_authorized_roles(token, role_name):
    """Teachers, Institute Admins, and Super Admins MUST be allowed to start lectures."""
    response = client.post("/api/v1/lecture/start", headers=get_headers(token), json={"title": "Physics 101"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["is_active"] is True


@pytest.mark.parametrize("token, role_name", [
    (teacher_token, "Teacher"),
    (inst_admin_token, "Institute Admin"),
    (super_admin_token, "Super Admin"),
])
def test_start_and_stop_recording_allowed_for_authorized_roles(token, role_name):
    """Teachers, Institute Admins, and Super Admins MUST be allowed to start recording."""
    # Start recording
    start_res = client.post("/api/v1/lecture/default/recording/start", headers=get_headers(token))
    assert start_res.status_code == 200
    start_data = start_res.json()
    assert start_data["status"] == "success"
    assert "recording_id" in start_data
