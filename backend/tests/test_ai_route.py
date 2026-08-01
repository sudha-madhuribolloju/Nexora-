import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_chat_endpoint_unauthorized() -> None:
    """
    Test POST /api/v1/ai/chat returns 401 when token is missing.
    """
    payload = {"message": "Hello Nexora AI", "stream": False}
    response = client.post("/api/v1/ai/chat", json=payload)
    assert response.status_code == 401


def test_ai_chat_endpoint_success() -> None:
    """
    Test POST /api/v1/ai/chat returns 200 and valid response structure for authenticated user.
    """
    email = "aichattestuser@example.com"
    password = "Password123!"

    # 1. Register test user
    reg_payload = {
        "email": email,
        "password": password,
        "full_name": "AI Chat Test User",
        "role": "Student"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # 2. Login to obtain JWT
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Call POST /api/v1/ai/chat
    chat_payload = {
        "message": "What services does Nexora provide?",
        "stream": False
    }
    chat_resp = client.post("/api/v1/ai/chat", json=chat_payload, headers=headers)
    assert chat_resp.status_code == 200, chat_resp.text

    data = chat_resp.json()
    assert "response" in data
    assert "conversation_id" in data
    assert "sources" in data
    assert "tokens_used" in data
    assert isinstance(data["response"], str)
    assert isinstance(data["conversation_id"], str)
    assert isinstance(data["sources"], list)
    assert isinstance(data["tokens_used"], int)

    conversation_id = data["conversation_id"]

    # 4. Multi-turn continuation with conversation_id
    followup_payload = {
        "message": "Can you elaborate more?",
        "conversation_id": conversation_id,
        "stream": False
    }
    followup_resp = client.post("/api/v1/ai/chat", json=followup_payload, headers=headers)
    assert followup_resp.status_code == 200, followup_resp.text
    followup_data = followup_resp.json()
    assert followup_data["conversation_id"] == conversation_id
