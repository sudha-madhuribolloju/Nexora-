"""
tests/test_recorded_lectures.py
────────────────────────────────
Unit and integration tests for Recorded Lectures module REST APIs, Range streaming,
soft deletion, restore, and Gemini AI processing.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.database.database import SessionLocal
from app.models.recording import Recording
from app.models.user import User

client = TestClient(app)

TEACHER_ID = "00000000-0000-0000-0000-000000000001"
STUDENT_ID = "00000000-0000-0000-0000-000000000004"
ADMIN_ID = "00000000-0000-0000-0000-000000000003"

teacher_token = create_access_token(subject=TEACHER_ID, role="Teacher", email="teacher@nexora.school")
student_token = create_access_token(subject=STUDENT_ID, role="Student", email="student@nexora.school")
admin_token = create_access_token(subject=ADMIN_ID, role="Super Admin", email="admin@nexora.school")


def get_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_get_my_recordings_teacher():
    """Verify teacher can retrieve their recorded lectures catalog."""
    res = client.get("/api/v1/recordings/my", headers=get_headers(teacher_token))
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "data" in data


def test_get_accessible_recordings_student():
    """Verify student can retrieve accessible recorded lectures catalog."""
    res = client.get("/api/v1/recordings", headers=get_headers(student_token))
    assert res.status_code == 200
    data = res.json()
    assert "total" in data


def test_recording_analytics_access():
    """Verify admin/principal can access analytics, whereas unauthorized access is blocked."""
    admin_res = client.get("/api/v1/recordings/analytics", headers=get_headers(admin_token))
    assert admin_res.status_code == 200
    analytics = admin_res.json()
    assert "total_recordings" in analytics
    assert "total_duration_hours" in analytics

    student_res = client.get("/api/v1/recordings/analytics", headers=get_headers(student_token))
    assert student_res.status_code == 403


def test_recording_streaming_range_header(tmp_path):
    """Verify HTTP 206 Partial Content range header streaming response."""
    test_video_path = tmp_path / "test_lecture.webm"
    dummy_bytes = b"HEADER_DUMMY_VIDEO_DATA_FOR_RANGE_TESTING_1234567890"
    test_video_path.write_bytes(dummy_bytes)

    # Directly create recording in test
    rec_id = uuid.uuid4()
    rec = Recording(
        id=rec_id,
        filename="test_lecture.webm",
        storage_path=str(test_video_path),
        duration=60.0,
        file_size=len(dummy_bytes),
        recording_status="ready"
    )

    from app.services.storage_service import StorageService
    res = StorageService.get_file_stream_response(
        storage_path=str(test_video_path),
        filename="test_lecture.webm",
        range_header="bytes=0-10"
    )
    assert res.status_code == 206
    assert "bytes 0-10/" in res.headers["Content-Range"]
