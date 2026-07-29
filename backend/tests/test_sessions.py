import pytest
import uuid

def test_session_management_full_flow(client):
    # 0. Create prerequisite School
    school_payload = {
        "name": "Session Test Academy",
        "code": "STA001",
        "subscription_tier": "pro",
    }
    res = client.post("/api/v1/schools/", json=school_payload)
    assert res.status_code == 201, res.text
    school_id = res.json()["id"]

    # 1. Register Teacher User & Profile
    teacher_user_res = client.post("/api/v1/auth/register", json={
        "email": "session_teacher@example.com",
        "password": "Password123!",
        "role": "Teacher"
    })
    assert teacher_user_res.status_code == 201, teacher_user_res.text
    teacher_user_id = teacher_user_res.json()["id"]

    teacher_res = client.post("/api/v1/people/teachers/", json={
        "user_id": teacher_user_id,
        "school_id": school_id,
        "employee_id": "EMP-SESS-01",
    })
    assert teacher_res.status_code == 201
    teacher_id = teacher_res.json()["id"]

    # 2. Create Course
    course_res = client.post("/courses/", json={
        "school_id": school_id,
        "teacher_id": teacher_id,
        "title": "Classical Mechanics",
        "code": "PHYS-101",
    })
    assert course_res.status_code == 201, course_res.text
    course_id = course_res.json()["id"]

    # 3. Create Class Session
    session_payload = {
        "course_id": course_id,
        "teacher_id": teacher_id,
        "title": "Lecture 1: Motion in One Dimension",
        "description": "Introduction to displacement, velocity, and acceleration.",
        "scheduled_at": "2026-08-01T09:00:00Z",
        "location": "Room 101",
    }
    res = client.post("/sessions/", json=session_payload)
    assert res.status_code == 201, res.text
    session_data = res.json()
    assert session_data["title"] == "Lecture 1: Motion in One Dimension"
    assert session_data["status"] == "scheduled"
    session_id = session_data["id"]

    # 4. Get Session details
    res = client.get(f"/sessions/{session_id}")
    assert res.status_code == 200
    assert res.json()["location"] == "Room 101"

    # 5. List Sessions filtered by course and status
    res = client.get(f"/sessions/?course_id={course_id}&status=scheduled")
    assert res.status_code == 200
    sessions_list = res.json()
    assert sessions_list["total"] == 1
    assert sessions_list["data"][0]["id"] == session_id

    # 6. Start Session
    res = client.post(f"/sessions/{session_id}/start")
    assert res.status_code == 200, res.text
    active_session = res.json()
    assert active_session["status"] == "active"
    assert active_session["started_at"] is not None

    # 7. Start already active session should fail with 409 Conflict
    res = client.post(f"/sessions/{session_id}/start")
    assert res.status_code == 409

    # 8. End Session
    res = client.post(f"/sessions/{session_id}/end")
    assert res.status_code == 200, res.text
    completed_session = res.json()
    assert completed_session["status"] == "completed"
    assert completed_session["ended_at"] is not None

    # 9. End already non-active session should fail with 409 Conflict
    res = client.post(f"/sessions/{session_id}/end")
    assert res.status_code == 409

    # 10. Update Session
    res = client.put(f"/sessions/{session_id}", json={"description": "Covered 1D and 2D motion with examples."})
    assert res.status_code == 200
    assert res.json()["description"] == "Covered 1D and 2D motion with examples."

    # 11. Delete Session
    res = client.delete(f"/sessions/{session_id}")
    assert res.status_code == 204

    # 12. Verify deleted Session returns 404
    res = client.get(f"/sessions/{session_id}")
    assert res.status_code == 404
