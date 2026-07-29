import pytest
import uuid

def test_student_and_people_full_flow(client):
    # 0. Create prerequisite School, Academic Year, Class, Section
    school_payload = {
        "name": "People Test School",
        "code": "PTS001",
        "subscription_tier": "pro",
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

    class_payload = {
        "name": "Grade 10",
        "grade_level": 10,
        "school_id": school_id,
        "academic_year_id": ay_id,
    }
    res = client.post("/api/v1/academic/classes/", json=class_payload)
    assert res.status_code == 201
    class_id = res.json()["id"]

    section_payload = {
        "name": "A",
        "capacity": 40,
        "class_id": class_id,
    }
    res = client.post(f"/api/v1/academic/classes/{class_id}/sections/", json=section_payload)
    assert res.status_code == 201
    section_id = res.json()["id"]

    # 1. Register User accounts for Student, Teacher, and Parent
    student_user_res = client.post("/api/v1/auth/register", json={
        "email": "student_test@example.com",
        "password": "Password123!",
        "role": "Student"
    })
    assert student_user_res.status_code == 201, student_user_res.text
    student_user_id = student_user_res.json()["id"]

    teacher_user_res = client.post("/api/v1/auth/register", json={
        "email": "teacher_test@example.com",
        "password": "Password123!",
        "role": "Teacher"
    })
    assert teacher_user_res.status_code == 201
    teacher_user_id = teacher_user_res.json()["id"]

    parent_user_res = client.post("/api/v1/auth/register", json={
        "email": "parent_test@example.com",
        "password": "Password123!",
        "role": "Parent"
    })
    assert parent_user_res.status_code == 201
    parent_user_id = parent_user_res.json()["id"]

    # 2. Create Student Profile
    student_payload = {
        "user_id": student_user_id,
        "school_id": school_id,
        "section_id": section_id,
        "admission_number": "ADM-2026-001",
        "roll_number": "10-A-01",
        "admission_date": "2025-06-01",
        "date_of_birth": "2010-03-15",
        "gender": "Female",
        "blood_group": "O+",
        "city": "Chennai",
    }
    res = client.post("/api/v1/people/students/", json=student_payload)
    assert res.status_code == 201, res.text
    student_data = res.json()
    assert student_data["admission_number"] == "ADM-2026-001"
    assert student_data["roll_number"] == "10-A-01"
    student_id = student_data["id"]

    # 3. Duplicate Student profile for same User should fail with 409
    res = client.post("/api/v1/people/students/", json=student_payload)
    assert res.status_code == 409

    # 4. List Students for school and section
    res = client.get(f"/api/v1/people/students/?school_id={school_id}")
    assert res.status_code == 200
    assert res.json()["total"] == 1

    res = client.get(f"/api/v1/people/students/?school_id={school_id}&section_id={section_id}")
    assert res.status_code == 200
    assert res.json()["total"] == 1

    # 5. Fetch Student detail by ID and by User ID
    res = client.get(f"/api/v1/people/students/{student_id}")
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "student_test@example.com"

    res = client.get(f"/api/v1/people/students/by-user/{student_user_id}")
    assert res.status_code == 200
    assert res.json()["id"] == student_id

    # 6. Create Teacher Profile
    teacher_payload = {
        "user_id": teacher_user_id,
        "school_id": school_id,
        "employee_id": "EMP-2026-001",
        "department": "Science",
        "qualification": "M.Sc Physics",
        "joining_date": "2022-06-01",
        "is_class_teacher": True,
    }
    res = client.post("/api/v1/people/teachers/", json=teacher_payload)
    assert res.status_code == 201, res.text
    teacher_id = res.json()["id"]

    # 7. Create Parent Profile
    parent_payload = {
        "user_id": parent_user_id,
        "relation_type": "Mother",
        "occupation": "Engineer",
        "city": "Chennai",
    }
    res = client.post("/api/v1/people/parents/", json=parent_payload)
    assert res.status_code == 201, res.text
    parent_id = res.json()["id"]

    # 8. Link Parent to Student
    link_payload = {
        "parent_id": parent_id,
        "student_id": student_id,
        "is_primary_contact": True,
    }
    res = client.post("/api/v1/people/links/", json=link_payload)
    assert res.status_code == 201, res.text
    link_data = res.json()
    assert link_data["is_primary_contact"] is True

    # 9. Get Student with embedded Parents
    res = client.get(f"/api/v1/people/students/{student_id}/with-parents")
    assert res.status_code == 200
    student_parents = res.json()
    assert len(student_parents["parent_links"]) == 1

    # 10. Get Parents for Student
    res = client.get(f"/api/v1/people/students/{student_id}/parents")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 11. Update Student Profile
    res = client.patch(f"/api/v1/people/students/{student_id}", json={"remarks": "Top performer"})
    assert res.status_code == 200
    assert res.json()["remarks"] == "Top performer"

    # 12. Unlink Parent from Student
    res = client.delete(f"/api/v1/people/links/?parent_id={parent_id}&student_id={student_id}")
    assert res.status_code == 204

    # 13. Verify unlinked
    res = client.get(f"/api/v1/people/students/{student_id}/parents")
    assert res.status_code == 200
    assert len(res.json()) == 0

    # 14. Soft-delete Student profile
    res = client.delete(f"/api/v1/people/students/{student_id}")
    assert res.status_code == 204

    # 15. Verify soft-deleted Student returns 404
    res = client.get(f"/api/v1/people/students/{student_id}")
    assert res.status_code == 404
