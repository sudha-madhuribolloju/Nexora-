import pytest
import uuid

def test_attendance_tracking_full_flow(client):
    # 0. Create prerequisite School
    school_payload = {
        "name": "Attendance Test School",
        "code": "ATS002",
        "subscription_tier": "enterprise",
    }
    res = client.post("/api/v1/schools/", json=school_payload)
    assert res.status_code == 201, res.text
    school_id = res.json()["id"]

    # 1. Register Teacher & Students
    teacher_user_res = client.post("/api/v1/auth/register", json={
        "email": "att_teacher@example.com",
        "password": "Password123!",
        "role": "Teacher"
    })
    assert teacher_user_res.status_code == 201
    teacher_user_id = teacher_user_res.json()["id"]

    student1_user_res = client.post("/api/v1/auth/register", json={
        "email": "att_student1@example.com",
        "password": "Password123!",
        "role": "Student"
    })
    assert student1_user_res.status_code == 201
    student1_user_id = student1_user_res.json()["id"]

    student2_user_res = client.post("/api/v1/auth/register", json={
        "email": "att_student2@example.com",
        "password": "Password123!",
        "role": "Student"
    })
    assert student2_user_res.status_code == 201
    student2_user_id = student2_user_res.json()["id"]

    # 2. Create Teacher & Student profiles
    teacher_res = client.post("/api/v1/people/teachers/", json={
        "user_id": teacher_user_id,
        "school_id": school_id,
        "employee_id": "EMP-ATT-01",
    })
    assert teacher_res.status_code == 201
    teacher_id = teacher_res.json()["id"]

    student1_res = client.post("/api/v1/people/students/", json={
        "user_id": student1_user_id,
        "school_id": school_id,
        "admission_number": "ADM-ATT-01",
    })
    assert student1_res.status_code == 201
    student1_id = student1_res.json()["id"]

    student2_res = client.post("/api/v1/people/students/", json={
        "user_id": student2_user_id,
        "school_id": school_id,
        "admission_number": "ADM-ATT-02",
    })
    assert student2_res.status_code == 201
    student2_id = student2_res.json()["id"]

    # 3. Create Course & Class Session
    course_res = client.post("/courses/", json={
        "school_id": school_id,
        "teacher_id": teacher_id,
        "title": "Calculus I",
        "code": "MATH-201",
    })
    assert course_res.status_code == 201
    course_id = course_res.json()["id"]

    session_res = client.post("/sessions/", json={
        "course_id": course_id,
        "teacher_id": teacher_id,
        "title": "Derivatives & Limits",
    })
    assert session_res.status_code == 201
    session_id = session_res.json()["id"]

    # 4. Mark Single Attendance for Student 1
    mark_payload = {
        "session_id": session_id,
        "student_id": student1_id,
        "status": "present",
        "notes": "Arrived on time",
    }
    res = client.post("/attendance/", json=mark_payload)
    assert res.status_code == 201, res.text
    att_data1 = res.json()
    assert att_data1["status"] == "present"
    att_id1 = att_data1["id"]

    # 5. Duplicate Single Attendance should fail with 409 Conflict
    res = client.post("/attendance/", json=mark_payload)
    assert res.status_code == 409

    # 6. Bulk Mark Attendance (Updates Student 1, Creates Student 2)
    bulk_payload = {
        "session_id": session_id,
        "records": [
            {"student_id": student1_id, "status": "late", "notes": "10 mins late"},
            {"student_id": student2_id, "status": "present", "notes": "On time"},
        ]
    }
    res = client.post("/attendance/bulk", json=bulk_payload)
    assert res.status_code == 201, res.text
    bulk_res = res.json()
    assert bulk_res["status"] == "success"
    assert bulk_res["count"] == 2

    # 7. List Attendance records for Session
    res = client.get(f"/attendance/?session_id={session_id}")
    assert res.status_code == 200
    att_list = res.json()
    assert att_list["total"] == 2

    # 8. Get Single Attendance detail by ID
    res = client.get(f"/attendance/{att_id1}")
    assert res.status_code == 200
    assert res.json()["status"] == "late"

    # 9. Get Attendance Aggregated Report
    res = client.get(f"/attendance/report?session_id={session_id}")
    assert res.status_code == 200
    report = res.json()
    assert len(report) == 2
    student1_report = next(r for r in report if r["student_id"] == student1_id)
    assert student1_report["total_sessions"] == 1
    assert student1_report["late"] == 1

    # 10. Update Attendance Record
    res = client.put(f"/attendance/{att_id1}", json={"status": "excused", "notes": "Medical note verified"})
    assert res.status_code == 200
    assert res.json()["status"] == "excused"
    assert res.json()["notes"] == "Medical note verified"

    # 11. Delete Attendance Record
    res = client.delete(f"/attendance/{att_id1}")
    assert res.status_code == 204

    # 12. Verify deleted Attendance returns 404
    res = client.get(f"/attendance/{att_id1}")
    assert res.status_code == 404
