import pytest
import uuid

def test_parent_portal_and_relationship_full_flow(client):
    # 0. Create prerequisite School, Academic Year, Class, Section
    school_payload = {
        "name": "Parent Portal School",
        "code": "PPS001",
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

    class_payload = {
        "name": "Grade 8",
        "grade_level": 8,
        "school_id": school_id,
        "academic_year_id": ay_id,
    }
    res = client.post("/api/v1/academic/classes/", json=class_payload)
    assert res.status_code == 201
    class_id = res.json()["id"]

    section_payload = {
        "name": "A",
        "capacity": 35,
        "class_id": class_id,
    }
    res = client.post(f"/api/v1/academic/classes/{class_id}/sections/", json=section_payload)
    assert res.status_code == 201
    section_id = res.json()["id"]

    # 1. Register User accounts for Parent and 2 Children (Students)
    parent_user_res = client.post("/api/v1/auth/register", json={
        "email": "father_test@example.com",
        "password": "Password123!",
        "role": "Parent"
    })
    assert parent_user_res.status_code == 201, parent_user_res.text
    parent_user_id = parent_user_res.json()["id"]

    child1_user_res = client.post("/api/v1/auth/register", json={
        "email": "child1_test@example.com",
        "password": "Password123!",
        "role": "Student"
    })
    assert child1_user_res.status_code == 201
    child1_user_id = child1_user_res.json()["id"]

    child2_user_res = client.post("/api/v1/auth/register", json={
        "email": "child2_test@example.com",
        "password": "Password123!",
        "role": "Student"
    })
    assert child2_user_res.status_code == 201
    child2_user_id = child2_user_res.json()["id"]

    # 2. Create Student profiles for Child 1 and Child 2
    child1_res = client.post("/api/v1/people/students/", json={
        "user_id": child1_user_id,
        "school_id": school_id,
        "section_id": section_id,
        "admission_number": "ADM-CHILD-01",
        "roll_number": "08-A-01",
    })
    assert child1_res.status_code == 201, child1_res.text
    child1_id = child1_res.json()["id"]

    child2_res = client.post("/api/v1/people/students/", json={
        "user_id": child2_user_id,
        "school_id": school_id,
        "section_id": section_id,
        "admission_number": "ADM-CHILD-02",
        "roll_number": "08-A-02",
    })
    assert child2_res.status_code == 201
    child2_id = child2_res.json()["id"]

    # 3. Create Parent Profile
    parent_payload = {
        "user_id": parent_user_id,
        "relation_type": "Father",
        "occupation": "Software Engineer",
        "address_line1": "100 Innovation Way",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560001",
        "alternate_phone": "+919876543210",
    }
    res = client.post("/api/v1/people/parents/", json=parent_payload)
    assert res.status_code == 201, res.text
    parent_data = res.json()
    assert parent_data["relation_type"] == "Father"
    assert parent_data["occupation"] == "Software Engineer"
    parent_id = parent_data["id"]

    # 4. Duplicate Parent profile creation for same User should fail with 409 Conflict
    res = client.post("/api/v1/people/parents/", json=parent_payload)
    assert res.status_code == 409

    # 5. Link Parent to both Child 1 and Child 2
    res1 = client.post("/api/v1/people/links/", json={
        "parent_id": parent_id,
        "student_id": child1_id,
        "is_primary_contact": True,
    })
    assert res1.status_code == 201

    res2 = client.post("/api/v1/people/links/", json={
        "parent_id": parent_id,
        "student_id": child2_id,
        "is_primary_contact": True,
    })
    assert res2.status_code == 201

    # 6. Fetch Parent detail by ID (with embedded user summary)
    res = client.get(f"/api/v1/people/parents/{parent_id}")
    assert res.status_code == 200
    parent_detail = res.json()
    assert parent_detail["id"] == parent_id
    assert parent_detail["user"]["email"] == "father_test@example.com"
    assert parent_detail["user"]["role"] == "Parent"

    # 7. Fetch Parent profile by User ID
    res = client.get(f"/api/v1/people/parents/by-user/{parent_user_id}")
    assert res.status_code == 200
    assert res.json()["id"] == parent_id

    # 8. Fetch Linked Children for Parent (Multi-child Parent Portal view)
    res = client.get(f"/api/v1/people/parents/{parent_id}/students")
    assert res.status_code == 200
    linked_students = res.json()
    assert len(linked_students) == 2
    student_ids = [link["student_id"] for link in linked_students]
    assert child1_id in student_ids
    assert child2_id in student_ids

    # 9. Update Parent profile information
    res = client.patch(
        f"/api/v1/people/parents/{parent_id}",
        json={"occupation": "Director of Engineering", "city": "Bengaluru East"}
    )
    assert res.status_code == 200
    updated_parent = res.json()
    assert updated_parent["occupation"] == "Director of Engineering"
    assert updated_parent["city"] == "Bengaluru East"

    # 10. Soft-delete Parent Profile
    res = client.delete(f"/api/v1/people/parents/{parent_id}")
    assert res.status_code == 204

    # 11. Verify deleted Parent returns 404
    res = client.get(f"/api/v1/people/parents/{parent_id}")
    assert res.status_code == 404
