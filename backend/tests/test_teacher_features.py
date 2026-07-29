import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_phase_8_teacher_features_full_flow() -> None:
    # 1. Register teacher user & login
    teacher_payload = {
        "email": "teacher_phase8@example.com",
        "password": "Password123!",
        "full_name": "Dr. Sarah Jenkins",
        "role": "Teacher"
    }
    client.post("/api/v1/auth/register", json=teacher_payload)

    login_resp = client.post("/api/v1/auth/login", json={
        "email": "teacher_phase8@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Teacher Dashboard Stats
    stats_resp = client.get("/api/v1/teachers/dashboard/stats", headers=headers)
    assert stats_resp.status_code == 200, stats_resp.text
    stats_data = stats_resp.json()["data"]
    assert "active_courses" in stats_data
    assert "created_quizzes" in stats_data

    # 3. Generate AI Quiz via Gemini
    quiz_gen_payload = {
        "topic": "Thermodynamics and Heat Transfer",
        "num_questions": 3,
        "difficulty": "medium"
    }
    quiz_resp = client.post("/api/v1/teachers/quizzes/generate", json=quiz_gen_payload, headers=headers)
    assert quiz_resp.status_code == 200, quiz_resp.text
    assert quiz_resp.json()["data"]["topic"] == "Thermodynamics and Heat Transfer"

    # 4. Generate AI Lesson Plan via Gemini
    plan_gen_payload = {
        "subject": "Physics",
        "topic": "Laws of Motion",
        "grade_level": "Grade 11",
        "duration_mins": 45
    }
    plan_resp = client.post("/api/v1/teachers/lesson-plans/generate", json=plan_gen_payload, headers=headers)
    assert plan_resp.status_code == 200, plan_resp.text
    assert "lesson_plan" in plan_resp.json()["data"]

    # 5. Generate AI Summary via Gemini
    summary_gen_payload = {
        "text_or_topic": "Quantum entanglement occurs when pairs of particles interact in ways such that the quantum state of each particle cannot be described independently."
    }
    summary_resp = client.post("/api/v1/teachers/summaries/generate", json=summary_gen_payload, headers=headers)
    assert summary_resp.status_code == 200, summary_resp.text
    assert "summary" in summary_resp.json()["data"]
