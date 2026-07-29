import pytest
import uuid

def test_academic_structure_full_flow(client):
    # 0. Create prerequisite School and Academic Year
    school_payload = {
        "name": "Academic Test School",
        "code": "ATS001",
        "subscription_tier": "basic",
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
    assert res.status_code == 201, res.text
    academic_year_id = res.json()["id"]

    # 1. Create a Class
    class_payload = {
        "name": "Grade 10",
        "grade_level": 10,
        "description": "Sophomore grade level",
        "school_id": school_id,
        "academic_year_id": academic_year_id,
    }
    res = client.post("/api/v1/academic/classes/", json=class_payload)
    assert res.status_code == 201, res.text
    class_data = res.json()
    assert class_data["name"] == "Grade 10"
    assert class_data["grade_level"] == 10
    class_id = class_data["id"]

    # 2. Duplicate Class creation in same year should fail with 409 Conflict
    res = client.post("/api/v1/academic/classes/", json=class_payload)
    assert res.status_code == 409

    # 3. List Classes for school & year
    res = client.get(f"/api/v1/academic/classes/?school_id={school_id}&academic_year_id={academic_year_id}")
    assert res.status_code == 200
    classes_list = res.json()
    assert classes_list["total"] == 1
    assert classes_list["items"][0]["id"] == class_id

    # 4. Create Section under Class
    section_payload = {
        "name": "A",
        "capacity": 40,
        "room_number": "101",
        "class_id": class_id,
    }
    res = client.post(f"/api/v1/academic/classes/{class_id}/sections/", json=section_payload)
    assert res.status_code == 201, res.text
    section_data = res.json()
    assert section_data["name"] == "A"
    assert section_data["school_id"] == school_id
    section_id = section_data["id"]

    # 5. Duplicate Section in same class should fail with 409 Conflict
    res = client.post(f"/api/v1/academic/classes/{class_id}/sections/", json=section_payload)
    assert res.status_code == 409

    # 6. List Sections for Class
    res = client.get(f"/api/v1/academic/classes/{class_id}/sections/")
    assert res.status_code == 200
    sections = res.json()
    assert len(sections) == 1
    assert sections[0]["id"] == section_id

    # 7. List Sections for School (flat)
    res = client.get(f"/api/v1/academic/sections/?school_id={school_id}")
    assert res.status_code == 200
    assert res.json()["total"] == 1

    # 8. Fetch Class full detail (with embedded sections)
    res = client.get(f"/api/v1/academic/classes/{class_id}/full")
    assert res.status_code == 200
    class_full = res.json()
    assert len(class_full["sections"]) == 1
    assert class_full["sections"][0]["name"] == "A"

    # 9. Create a Subject
    subject_payload = {
        "name": "Mathematics",
        "code": "math",  # should auto-uppercase to MATH
        "description": "Core mathematics curriculum",
        "credits": 4.0,
        "color": "#4F46E5",
        "is_elective": False,
        "school_id": school_id,
    }
    res = client.post("/api/v1/academic/subjects/", json=subject_payload)
    assert res.status_code == 201, res.text
    subject_data = res.json()
    assert subject_data["code"] == "MATH"
    assert subject_data["color"] == "#4F46E5"
    subject_id = subject_data["id"]

    # 10. Duplicate Subject code should fail with 409 Conflict
    res = client.post("/api/v1/academic/subjects/", json=subject_payload)
    assert res.status_code == 409

    # 11. Search Subject by code/name prefix
    res = client.get(f"/api/v1/academic/subjects/?school_id={school_id}&search=mat")
    assert res.status_code == 200
    subjects_found = res.json()
    assert subjects_found["total"] == 1
    assert subjects_found["items"][0]["code"] == "MATH"

    # 12. Update Section and Subject
    res = client.patch(f"/api/v1/academic/sections/{section_id}", json={"room_number": "102"})
    assert res.status_code == 200
    assert res.json()["room_number"] == "102"

    res = client.patch(f"/api/v1/academic/subjects/{subject_id}", json={"description": "Advanced Math"})
    assert res.status_code == 200
    assert res.json()["description"] == "Advanced Math"

    # 13. Soft-delete Class (also soft-deletes child sections)
    res = client.delete(f"/api/v1/academic/classes/{class_id}")
    assert res.status_code == 204

    # 14. Verify Class and Section are deleted
    res = client.get(f"/api/v1/academic/classes/{class_id}")
    assert res.status_code == 404

    res = client.get(f"/api/v1/academic/sections/{section_id}")
    assert res.status_code == 404

    # 15. Soft-delete Subject
    res = client.delete(f"/api/v1/academic/subjects/{subject_id}")
    assert res.status_code == 204

    res = client.get(f"/api/v1/academic/subjects/{subject_id}")
    assert res.status_code == 404
