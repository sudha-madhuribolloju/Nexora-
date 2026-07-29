import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_phase_10_parent_portal_full_flow() -> None:
    # 1. Register parent user & login
    parent_payload = {
        "email": "parent_phase10@example.com",
        "password": "Password123!",
        "full_name": "Eleanor Mercer",
        "role": "Parent"
    }
    client.post("/api/v1/auth/register", json=parent_payload)

    login_resp = client.post("/api/v1/auth/login", json={
        "email": "parent_phase10@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Parent Dashboard Stats
    stats_resp = client.get("/api/v1/parents/dashboard/stats", headers=headers)
    assert stats_resp.status_code == 200, stats_resp.text
    stats_data = stats_resp.json()["data"]
    assert "attendance_rate_pct" in stats_data
    assert "overall_academic_status" in stats_data

    # 3. Generate AI Progress Summary
    summary_payload = {
        "student_name": "Alex Mercer",
        "gpa": 3.90,
        "attendance_pct": 98.0,
        "recent_quiz_score": 95.0
    }
    summary_resp = client.post("/api/v1/parents/progress-summary", json=summary_payload, headers=headers)
    assert summary_resp.status_code == 200, summary_resp.text
    assert "ai_progress_summary" in summary_resp.json()["data"]
    assert summary_resp.json()["data"]["student_name"] == "Alex Mercer"
