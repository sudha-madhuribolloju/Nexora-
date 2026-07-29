import pytest
import uuid

def test_quiz_and_assessment_full_flow(client):
    # 0. Create prerequisite School
    school_payload = {
        "name": "Quiz Test Academy",
        "code": "QTA004",
        "subscription_tier": "enterprise",
    }
    res = client.post("/api/v1/schools/", json=school_payload)
    assert res.status_code == 201, res.text
    school_id = res.json()["id"]

    # 1. Register Teacher & Student users
    teacher_user_res = client.post("/api/v1/auth/register", json={
        "email": "quiz_teacher@example.com",
        "password": "Password123!",
        "role": "Teacher"
    })
    assert teacher_user_res.status_code == 201
    teacher_user_id = teacher_user_res.json()["id"]

    student_user_res = client.post("/api/v1/auth/register", json={
        "email": "quiz_student@example.com",
        "password": "Password123!",
        "role": "Student"
    })
    assert student_user_res.status_code == 201
    student_user_id = student_user_res.json()["id"]

    # 2. Create Teacher & Student profiles
    teacher_res = client.post("/api/v1/people/teachers/", json={
        "user_id": teacher_user_id,
        "school_id": school_id,
        "employee_id": "EMP-QUIZ-01",
    })
    assert teacher_res.status_code == 201
    teacher_id = teacher_res.json()["id"]

    student_res = client.post("/api/v1/people/students/", json={
        "user_id": student_user_id,
        "school_id": school_id,
        "admission_number": "ADM-QUIZ-01",
    })
    assert student_res.status_code == 201
    student_id = student_res.json()["id"]

    # 3. Create Course
    course_res = client.post("/courses/", json={
        "school_id": school_id,
        "teacher_id": teacher_id,
        "title": "Quantum Physics",
        "code": "PHYS-401",
    })
    assert course_res.status_code == 201
    course_id = course_res.json()["id"]

    # 4. Create Quiz (Default status: draft)
    quiz_payload = {
        "course_id": course_id,
        "title": "Midterm Quiz: Wave Mechanics",
        "description": "Assessment covering wave-particle duality and Schrodinger equation.",
        "duration_minutes": 30,
        "max_attempts": 1,
        "pass_score": 70.0,
    }
    res = client.post(f"/quizzes/?teacher_id={teacher_id}", json=quiz_payload)
    assert res.status_code == 201, res.text
    quiz_data = res.json()
    assert quiz_data["title"] == "Midterm Quiz: Wave Mechanics"
    assert quiz_data["status"] == "draft"
    quiz_id = quiz_data["id"]

    # 5. Add Questions to Quiz
    q1_payload = {
        "question_text": "What is light?",
        "question_type": "mcq",
        "options": ["Particle", "Wave", "Both Wave and Particle", "Neither"],
        "correct_answer": "Both Wave and Particle",
        "marks": 50.0,
        "order": 1,
    }
    q1_res = client.post(f"/quizzes/{quiz_id}/questions", json=q1_payload)
    assert q1_res.status_code == 201, q1_res.text
    q1_id = q1_res.json()["id"]

    q2_payload = {
        "question_text": "Is the speed of light in vacuum constant for all observers?",
        "question_type": "true_false",
        "options": ["True", "False"],
        "correct_answer": "True",
        "marks": 50.0,
        "order": 2,
    }
    q2_res = client.post(f"/quizzes/{quiz_id}/questions", json=q2_payload)
    assert q2_res.status_code == 201, q2_res.text
    q2_id = q2_res.json()["id"]

    # 6. Try starting attempt while draft -> Expect 400 Bad Request
    res = client.post(f"/quizzes/{quiz_id}/attempt?student_id={student_id}")
    assert res.status_code == 400

    # 7. Publish Quiz
    res = client.put(f"/quizzes/{quiz_id}", json={"status": "published"})
    assert res.status_code == 200
    assert res.json()["status"] == "published"

    # 8. Start Quiz Attempt
    res = client.post(f"/quizzes/{quiz_id}/attempt?student_id={student_id}")
    assert res.status_code == 201, res.text
    attempt_data = res.json()
    attempt_id = attempt_data["id"]

    # 9. Submit Quiz Attempt with correct answers
    submit_payload = {
        "answers": {
            q1_id: "Both Wave and Particle",
            q2_id: "True",
        }
    }
    res = client.put(f"/quizzes/{quiz_id}/attempt/{attempt_id}/submit?student_id={student_id}", json=submit_payload)
    assert res.status_code == 200, res.text
    graded_attempt = res.json()
    assert graded_attempt["score"] == 100.0
    assert graded_attempt["passed"] is True

    # 10. Second attempt should be rejected with 409 Conflict
    res = client.post(f"/quizzes/{quiz_id}/attempt?student_id={student_id}")
    assert res.status_code == 409

    # 11. Fetch Quiz Results
    res = client.get(f"/quizzes/{quiz_id}/results")
    assert res.status_code == 200, res.text
    results = res.json()
    assert results["total_attempts"] == 1
    assert results["average_score"] == 100.0
    assert results["pass_rate"] == 100.0

    # 12. Delete Quiz
    res = client.delete(f"/quizzes/{quiz_id}")
    assert res.status_code == 204

    # 13. Verify deleted Quiz returns 404
    res = client.get(f"/quizzes/{quiz_id}")
    assert res.status_code == 404
