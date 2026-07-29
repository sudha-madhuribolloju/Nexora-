import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_phase_11_admin_features_full_flow() -> None:
    # 1. Register admin user & login
    admin_payload = {
        "email": "superadmin_phase11@example.com",
        "password": "Password123!",
        "full_name": "Super Admin User",
        "role": "Super Admin"
    }
    client.post("/api/v1/auth/register", json=admin_payload)

    login_resp = client.post("/api/v1/auth/login", json={
        "email": "superadmin_phase11@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get System Analytics Dashboard
    analytics_resp = client.get("/api/v1/dashboard/", headers=headers)
    assert analytics_resp.status_code == 200, analytics_resp.text
    analytics_data = analytics_resp.json()["data"]
    assert "total_users" in analytics_data
    assert "total_schools" in analytics_data
    assert "system_health" in analytics_data

    # 3. Get Storage Statistics
    storage_resp = client.get("/api/v1/dashboard/storage", headers=headers)
    assert storage_resp.status_code == 200, storage_resp.text
    storage_data = storage_resp.json()["data"]
    assert "total_storage_mb" in storage_data
    assert "total_vector_chunks_indexed" in storage_data

    # 4. Get AI Usage Analytics
    ai_usage_resp = client.get("/api/v1/dashboard/ai-usage", headers=headers)
    assert ai_usage_resp.status_code == 200, ai_usage_resp.text
    ai_data = ai_usage_resp.json()["data"]
    assert "total_ai_queries_processed" in ai_data
    assert "gemini_chat_model" in ai_data

    # 5. Get Audit Logs
    audit_resp = client.get("/api/v1/dashboard/audit-logs", headers=headers)
    assert audit_resp.status_code == 200, audit_resp.text
    assert "logs" in audit_resp.json()["data"]
