import pytest
import uuid

def test_teacher_management_full_flow(client):
    # 0. Create prerequisite School and Academic Year
    school_payload = {
        "name": "Teacher Test School",
        "code": "TTS001",
        "subscription_tier": "enterprise",
    }
    res = client.post("/api/v1/schools/", json=school_payload)
    assert res.status_code == 201, res.text
    school_id = res.json()["id"]

    ay_payload = {
        "name": "2025-2026",
        "start_date": "2025-06-01",
        "end_date": "2026-03-31",
        "is_current": True,
    }
    res = client.post(f"/api/v1/schools/{school_id}/academic-years/", json=ay_payload)
    assert res.status_code == 201
    ay_id = res.json()["id"]

    # 1. Register User accounts for Teachers
    teacher_user_res1 = client.post("/api/v1/auth/register", json={
        "email": "teacher1_test@example.com",
        "password": "Password123!",
        "first_name": "Alan",
        "last_name": "Turing",
        "role": "Teacher"
    })
    assert teacher_user_res1.status_code == 201, teacher_user_res1.text
    teacher_user_id1 = teacher_user_res1.json()["id"]

    teacher_user_res2 = client.post("/api/v1/auth/register", json={
        "email": "teacher2_test@example.com",
        "password": "Password123!",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "role": "Teacher"
    })
    assert teacher_user_res2.status_code == 201
    teacher_user_id2 = teacher_user_res2.json()["id"]

    # 2. Create Teacher Profile
    teacher_payload1 = {
        "user_id": teacher_user_id1,
        "school_id": school_id,
        "employee_id": "EMP-2026-001",
        "department": "Mathematics",
        "qualification": "Ph.D. Mathematics",
        "specialization": "Algebra & Cryptography",
        "joining_date": "2023-01-15",
        "is_class_teacher": True,
    }
    res = client.post("/api/v1/people/teachers/", json=teacher_payload1)
    assert res.status_code == 201, res.text
    teacher_data1 = res.json()
    assert teacher_data1["employee_id"] == "EMP-2026-001"
    assert teacher_data1["department"] == "Mathematics"
    assert teacher_data1["is_class_teacher"] is True
    teacher_id1 = teacher_data1["id"]

    # 3. Duplicate Teacher profile for same User should fail with 409 Conflict
    res = client.post("/api/v1/people/teachers/", json=teacher_payload1)
    assert res.status_code == 409

    # 4. Duplicate Employee ID in same school should fail with 409 Conflict
    teacher_payload_dup_emp = {
        "user_id": teacher_user_id2,
        "school_id": school_id,
        "employee_id": "EMP-2026-001",  # Collision!
        "department": "Physics",
    }
    res = client.post("/api/v1/people/teachers/", json=teacher_payload_dup_emp)
    assert res.status_code == 409

    # 5. Create second Teacher profile with unique employee ID
    teacher_payload2 = {
        "user_id": teacher_user_id2,
        "school_id": school_id,
        "employee_id": "EMP-2026-002",
        "department": "Computer Science",
        "qualification": "M.Sc Computer Science",
        "is_class_teacher": False,
    }
    res = client.post("/api/v1/people/teachers/", json=teacher_payload2)
    assert res.status_code == 201
    teacher_id2 = res.json()["id"]

    # 6. List Teachers for School
    res = client.get(f"/api/v1/people/teachers/?school_id={school_id}")
    assert res.status_code == 200
    teachers_list = res.json()
    assert teachers_list["total"] == 2
    assert len(teachers_list["items"]) == 2

    # 7. Fetch Teacher detail by ID (with embedded user summary)
    res = client.get(f"/api/v1/people/teachers/{teacher_id1}")
    assert res.status_code == 200
    teacher_detail = res.json()
    assert teacher_detail["id"] == teacher_id1
    assert teacher_detail["user"]["email"] == "teacher1_test@example.com"
    assert teacher_detail["user"]["role"] == "Teacher"

    # 8. Fetch Teacher profile by User ID
    res = client.get(f"/api/v1/people/teachers/by-user/{teacher_user_id2}")
    assert res.status_code == 200
    assert res.json()["id"] == teacher_id2
    assert res.json()["user"]["email"] == "teacher2_test@example.com"

    # 9. Update Teacher Profile
    res = client.patch(
        f"/api/v1/people/teachers/{teacher_id1}",
        json={"department": "Advanced Mathematics", "specialization": "Quantum Computing"}
    )
    assert res.status_code == 200
    updated_teacher = res.json()
    assert updated_teacher["department"] == "Advanced Mathematics"
    assert updated_teacher["specialization"] == "Quantum Computing"

    # 10. Soft-delete Teacher
    res = client.delete(f"/api/v1/people/teachers/{teacher_id1}")
    assert res.status_code == 204

    # 11. Verify deleted Teacher returns 404
    res = client.get(f"/api/v1/people/teachers/{teacher_id1}")
    assert res.status_code == 404

    # 12. List Teachers now returns 1 active teacher
    res = client.get(f"/api/v1/people/teachers/?school_id={school_id}")
    assert res.status_code == 200
    assert res.json()["total"] == 1
