import pytest
import uuid

def test_school_and_multitenancy_full_flow(client):
    # 1. Create a School
    school_payload = {
        "name": "Greenwood High School",
        "code": "GHS001",
        "email": "contact@greenwood.edu",
        "phone": "+919876543210",
        "city": "Bengaluru",
        "country": "India",
        "timezone": "Asia/Kolkata",
        "subscription_tier": "pro",
    }
    response = client.post("/api/v1/schools/", json=school_payload)
    assert response.status_code == 201, response.text
    school_data = response.json()
    assert school_data["name"] == "Greenwood High School"
    assert school_data["code"] == "GHS001"
    assert school_data["subscription_tier"] == "pro"
    school_id = school_data["id"]

    # 2. Case-insensitivity check & duplicate code conflict
    duplicate_payload = {
        "name": "Duplicate Greenwood",
        "code": "ghs001",  # lowercase, should collide with GHS001
    }
    response = client.post("/api/v1/schools/", json=duplicate_payload)
    assert response.status_code == 409

    # 3. List active schools
    response = client.get("/api/v1/schools/")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["total"] == 1
    assert res_data["items"][0]["code"] == "GHS001"

    # 4. Fetch school by code
    response = client.get("/api/v1/schools/code/ghs001")
    assert response.status_code == 200
    assert response.json()["id"] == school_id

    # 5. Fetch school detail by UUID
    response = client.get(f"/api/v1/schools/{school_id}")
    assert response.status_code == 200
    assert response.json()["city"] == "Bengaluru"

    # 6. Update school details
    update_payload = {"city": "Mumbai", "website": "https://greenwood.edu"}
    response = client.patch(f"/api/v1/schools/{school_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["city"] == "Mumbai"
    assert response.json()["website"] == "https://greenwood.edu"

    # 7. Create an Academic Year (2025-2026)
    ay1_payload = {
        "name": "2025-2026",
        "start_date": "2025-06-01",
        "end_date": "2026-03-31",
        "is_current": True,
    }
    response = client.post(f"/api/v1/schools/{school_id}/academic-years/", json=ay1_payload)
    assert response.status_code == 201, response.text
    ay1_data = response.json()
    assert ay1_data["name"] == "2025-2026"
    assert ay1_data["is_current"] is True
    ay1_id = ay1_data["id"]

    # 8. Create a second Academic Year (2026-2027)
    ay2_payload = {
        "name": "2026-2027",
        "start_date": "2026-06-01",
        "end_date": "2027-03-31",
        "is_current": False,
    }
    response = client.post(f"/api/v1/schools/{school_id}/academic-years/", json=ay2_payload)
    assert response.status_code == 201
    ay2_id = response.json()["id"]

    # 9. List Academic Years for the school
    response = client.get(f"/api/v1/schools/{school_id}/academic-years/")
    assert response.status_code == 200
    years = response.json()
    assert len(years) == 2

    # 10. Fetch current Academic Year
    response = client.get(f"/api/v1/schools/{school_id}/academic-years/current")
    assert response.status_code == 200
    assert response.json()["id"] == ay1_id

    # 11. Promote 2026-2027 to current
    response = client.post(f"/api/v1/schools/{school_id}/academic-years/{ay2_id}/set-current")
    assert response.status_code == 200
    assert response.json()["is_current"] is True

    # 12. Verify 2026-2027 is now current and 2025-2026 is demoted
    response = client.get(f"/api/v1/schools/{school_id}/academic-years/current")
    assert response.status_code == 200
    assert response.json()["id"] == ay2_id

    response = client.get(f"/api/v1/schools/{school_id}/academic-years/{ay1_id}")
    assert response.status_code == 200
    assert response.json()["is_current"] is False

    # 13. Fetch school full response (with nested academic years)
    response = client.get(f"/api/v1/schools/{school_id}/full")
    assert response.status_code == 200
    full_data = response.json()
    assert len(full_data["academic_years"]) == 2

    # 14. Soft-delete school
    response = client.delete(f"/api/v1/schools/{school_id}")
    assert response.status_code == 204

    # 15. Verify soft-deleted school returns 404
    response = client.get(f"/api/v1/schools/{school_id}")
    assert response.status_code == 404
