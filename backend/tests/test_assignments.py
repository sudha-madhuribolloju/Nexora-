import pytest
import uuid

def test_assignments_and_grading_full_flow(client):
    # 0. Create prerequisite School
    school_payload = {
        "name": "Assignment Test High",
        "code": "ATH003",
        "subscription_tier": "enterprise",
    }
    res = client.post("/api/v1/schools/", json=school_payload)
    assert res.status_code == 201, res.text
    school_id = res.json()["id"]

    # 1. Register Teacher & Student users
    teacher_user_res = client.post("/api/v1/auth/register", json={
        "email": "asgn_teacher@example.com",
        "password": "Password123!",
        "role": "Teacher"
    })
    assert teacher_user_res.status_code == 201
    teacher_user_id = teacher_user_res.json()["id"]

    student_user_res = client.post("/api/v1/auth/register", json={
        "email": "asgn_student@example.com",
        "password": "Password123!",
        "role": "Student"
    })
    assert student_user_res.status_code == 201
    student_user_id = student_user_res.json()["id"]

    # 2. Create Teacher & Student profiles
    teacher_res = client.post("/api/v1/people/teachers/", json={
        "user_id": teacher_user_id,
        "school_id": school_id,
        "employee_id": "EMP-ASGN-01",
    })
    assert teacher_res.status_code == 201
    teacher_id = teacher_res.json()["id"]

    student_res = client.post("/api/v1/people/students/", json={
        "user_id": student_user_id,
        "school_id": school_id,
        "admission_number": "ADM-ASGN-01",
    })
    assert student_res.status_code == 201
    student_id = student_res.json()["id"]

    # 3. Create Course
    course_res = client.post("/courses/", json={
        "school_id": school_id,
        "teacher_id": teacher_id,
        "title": "Data Structures & Algorithms",
        "code": "CS-301",
    })
    assert course_res.status_code == 201
    course_id = course_res.json()["id"]

    # 4. Create Assignment (Default status: draft)
    asgn_payload = {
        "course_id": course_id,
        "title": "Homework 1: Binary Search Trees",
        "description": "Implement insertion, deletion, and traversal for a BST.",
        "max_score": 100.0,
        "due_date": "2026-12-31T23:59:59Z",
        "allow_late_submission": False,
    }
    res = client.post(f"/assignments/?teacher_id={teacher_id}", json=asgn_payload)
    assert res.status_code == 201, res.text
    asgn_data = res.json()
    assert asgn_data["title"] == "Homework 1: Binary Search Trees"
    assert asgn_data["status"] == "draft"
    asgn_id = asgn_data["id"]

    # 5. Try submitting while draft -> Expect 400 Bad Request
    sub_payload = {"content": "https://github.com/student/bst-impl"}
    res = client.post(f"/assignments/{asgn_id}/submit?student_id={student_id}", json=sub_payload)
    assert res.status_code == 400

    # 6. Publish Assignment
    res = client.put(f"/assignments/{asgn_id}", json={"status": "published"})
    assert res.status_code == 200
    assert res.json()["status"] == "published"

    # 7. Submit Assignment
    res = client.post(f"/assignments/{asgn_id}/submit?student_id={student_id}", json=sub_payload)
    assert res.status_code == 201, res.text
    submission = res.json()
    assert submission["status"] == "submitted"
    sub_id = submission["id"]

    # 8. Try Duplicate Submission -> Expect 409 Conflict
    res = client.post(f"/assignments/{asgn_id}/submit?student_id={student_id}", json=sub_payload)
    assert res.status_code == 409

    # 9. List Submissions
    res = client.get(f"/assignments/{asgn_id}/submissions")
    assert res.status_code == 200
    sub_list = res.json()
    assert sub_list["total"] == 1
    assert sub_list["data"][0]["id"] == sub_id

    # 10. Grade Submission
    grade_payload = {"score": 96.5, "feedback": "Great BST implementation!"}
    res = client.put(f"/assignments/{asgn_id}/submissions/{sub_id}/grade?teacher_id={teacher_id}", json=grade_payload)
    assert res.status_code == 200, res.text
    graded_sub = res.json()
    assert graded_sub["status"] == "graded"
    assert graded_sub["score"] == 96.5
    assert graded_sub["feedback"] == "Great BST implementation!"

    # 11. Delete Assignment
    res = client.delete(f"/assignments/{asgn_id}")
    assert res.status_code == 204

    # 12. Verify deleted Assignment returns 404
    res = client.get(f"/assignments/{asgn_id}")
    assert res.status_code == 404
