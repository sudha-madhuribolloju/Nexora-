import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_phase_9_student_features_full_flow() -> None:
    # 1. Register student user & login
    student_payload = {
        "email": "student_phase9@example.com",
        "password": "Password123!",
        "full_name": "Alex Mercer",
        "role": "Student"
    }
    client.post("/api/v1/auth/register", json=student_payload)

    login_resp = client.post("/api/v1/auth/login", json={
        "email": "student_phase9@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Student Dashboard Stats
    stats_resp = client.get("/api/v1/students/dashboard/stats", headers=headers)
    assert stats_resp.status_code == 200, stats_resp.text
    stats_data = stats_resp.json()["data"]
    assert "enrolled_courses" in stats_data
    assert "overall_gpa" in stats_data

    # 3. Request AI Homework Help
    hw_payload = {
        "question": "How do you calculate force using Newton's Second Law?",
        "subject": "Physics"
    }
    hw_resp = client.post("/api/v1/students/homework-help", json=hw_payload, headers=headers)
    assert hw_resp.status_code == 200, hw_resp.text
    assert "explanation" in hw_resp.json()["data"]

    # 4. Request AI Study Recommendations
    rec_resp = client.post("/api/v1/students/study-recommendations", headers=headers)
    assert rec_resp.status_code == 200, rec_resp.text
    assert "recommendations" in rec_resp.json()["data"]
