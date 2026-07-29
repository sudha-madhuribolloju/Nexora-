import pytest
import uuid

def test_rbac_full_flow(client):
    # 1. Create a Permission
    perm_payload = {
        "resource": "students",
        "action": "write",
        "description": "Permission to edit student profiles"
    }
    response = client.post("/api/v1/roles/permissions/", json=perm_payload)
    assert response.status_code == 201, response.text
    perm_data = response.json()
    assert perm_data["resource"] == "students"
    assert perm_data["action"] == "write"
    perm_id = perm_data["id"]

    # 2. Duplicate Permission creation should fail with 409 Conflict
    response = client.post("/api/v1/roles/permissions/", json=perm_payload)
    assert response.status_code == 409

    # 3. List Permissions
    response = client.get("/api/v1/roles/permissions/")
    assert response.status_code == 200
    assert response.json()["total"] >= 1

    # 4. Create a custom Role with attached permission
    role_payload = {
        "name": "academic_officer",
        "description": "Officer managing academic records",
        "is_system_role": False,
        "permission_ids": [perm_id]
    }
    response = client.post("/api/v1/roles/", json=role_payload)
    assert response.status_code == 201, response.text
    role_data = response.json()
    assert role_data["name"] == "academic_officer"
    assert role_data["is_system_role"] is False
    assert len(role_data["permissions"]) == 1
    assert role_data["permissions"][0]["id"] == perm_id
    role_id = role_data["id"]

    # 5. Duplicate Role creation should fail with 409 Conflict
    response = client.post("/api/v1/roles/", json=role_payload)
    assert response.status_code == 409

    # 6. Update non-system Role
    update_payload = {"description": "Updated academic officer description"}
    response = client.patch(f"/api/v1/roles/{role_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["description"] == "Updated academic officer description"

    # 7. Create a system Role
    sys_role_payload = {
        "name": "super_admin",
        "description": "System Super Admin",
        "is_system_role": True
    }
    response = client.post("/api/v1/roles/", json=sys_role_payload)
    assert response.status_code == 201
    sys_role_id = response.json()["id"]

    # 8. Attempting to update system role should return 403 Forbidden
    response = client.patch(f"/api/v1/roles/{sys_role_id}", json={"description": "Hack"})
    assert response.status_code == 403

    # 9. Attempting to delete system role should return 403 Forbidden
    response = client.delete(f"/api/v1/roles/{sys_role_id}")
    assert response.status_code == 403

    # 10. Register a user for role assignment testing
    user_payload = {
        "email": "rbac_test_user@example.com",
        "password": "Password123!",
        "role": "Student"
    }
    res = client.post("/api/v1/auth/register", json=user_payload)
    assert res.status_code == 201
    user_id = res.json()["id"]

    # 11. Assign custom role to user
    assign_payload = {
        "user_id": user_id,
        "role_id": role_id
    }
    response = client.post("/api/v1/roles/assign", json=assign_payload)
    assert response.status_code == 201, response.text
    assert response.json()["role_id"] == role_id

    # 12. Check user roles
    response = client.get(f"/api/v1/roles/users/{user_id}")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # 13. Revoke role from user
    response = client.delete(f"/api/v1/roles/users/{user_id}/roles/{role_id}")
    assert response.status_code == 204

    # 14. Verify role is revoked
    response = client.get(f"/api/v1/roles/users/{user_id}")
    assert response.status_code == 200
    assert len(response.json()) == 0

    # 15. Delete non-system role
    response = client.delete(f"/api/v1/roles/{role_id}")
    assert response.status_code == 204
