import pytest
import uuid

def test_course_and_enrollment_full_flow(client):
    # 0. Create prerequisite School
    school_payload = {
        "name": "Course Test Academy",
        "code": "CTA001",
        "subscription_tier": "enterprise",
    }
    res = client.post("/api/v1/schools/", json=school_payload)
    assert res.status_code == 201, res.text
    school_id = res.json()["id"]

    # 1. Register Teacher User & Create Teacher Profile
    teacher_user_res = client.post("/api/v1/auth/register", json={
        "email": "course_teacher@example.com",
        "password": "Password123!",
        "role": "Teacher"
    })
    assert teacher_user_res.status_code == 201, teacher_user_res.text
    teacher_user_id = teacher_user_res.json()["id"]

    teacher_res = client.post("/api/v1/people/teachers/", json={
        "user_id": teacher_user_id,
        "school_id": school_id,
        "employee_id": "EMP-COURSE-01",
        "department": "Physics",
    })
    assert teacher_res.status_code == 201, teacher_res.text
    teacher_id = teacher_res.json()["id"]

    # 2. Register Student User & Create Student Profile
    student_user_res = client.post("/api/v1/auth/register", json={
        "email": "course_student@example.com",
        "password": "Password123!",
        "role": "Student"
    })
    assert student_user_res.status_code == 201, student_user_res.text
    student_user_id = student_user_res.json()["id"]

    student_res = client.post("/api/v1/people/students/", json={
        "user_id": student_user_id,
        "school_id": school_id,
        "admission_number": "ADM-COURSE-01",
    })
    assert student_res.status_code == 201, student_res.text
    student_id = student_res.json()["id"]

    # 3. Create Course
    course_payload = {
        "school_id": school_id,
        "teacher_id": teacher_id,
        "title": "Advanced Quantum Physics",
        "description": "Calculus-based quantum mechanics and atomic theory.",
        "code": "PHYS-301",
        "max_students": 30,
    }
    res = client.post("/courses/", json=course_payload)
    assert res.status_code == 201, res.text
    course_data = res.json()
    assert course_data["title"] == "Advanced Quantum Physics"
    assert course_data["code"] == "PHYS-301"
    course_id = course_data["id"]

    # 4. Get Course by ID
    res = client.get(f"/courses/{course_id}")
    assert res.status_code == 200
    assert res.json()["code"] == "PHYS-301"

    # 5. List Courses
    res = client.get("/courses/?is_active=true")
    assert res.status_code == 200
    courses_list = res.json()
    assert courses_list["total"] >= 1
    assert any(c["id"] == course_id for c in courses_list["data"])

    # 6. Enroll Student into Course
    enroll_payload = {"student_id": student_id}
    res = client.post(f"/courses/{course_id}/enroll", json=enroll_payload)
    assert res.status_code == 201, res.text
    enrollment_data = res.json()
    assert enrollment_data["student_id"] == student_id
    assert enrollment_data["course_id"] == course_id

    # 7. Duplicate Enrollment should return 409 Conflict
    res = client.post(f"/courses/{course_id}/enroll", json=enroll_payload)
    assert res.status_code == 409

    # 8. List Enrolled Students for Course
    res = client.get(f"/courses/{course_id}/students")
    assert res.status_code == 200
    students_data = res.json()
    assert len(students_data["data"]) == 1
    assert students_data["data"][0]["student_id"] == student_id

    # 9. Update Course Details
    update_payload = {"description": "Updated course description with lab modules."}
    res = client.put(f"/courses/{course_id}", json=update_payload)
    assert res.status_code == 200
    assert res.json()["description"] == "Updated course description with lab modules."

    # 10. Unenroll Student
    res = client.delete(f"/courses/{course_id}/enroll/{student_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    # 11. Delete Course
    res = client.delete(f"/courses/{course_id}")
    assert res.status_code == 204

    # 12. Verify deleted Course returns 404
    res = client.get(f"/courses/{course_id}")
    assert res.status_code == 404
