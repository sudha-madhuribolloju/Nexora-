import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_chat_session_management_and_rag_flow() -> None:
    # 1. Register test user & login
    reg_payload = {
        "email": "aichatuser@example.com",
        "password": "Password123!",
        "full_name": "Chat User",
        "role": "Student"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_resp = client.post("/api/v1/auth/login", json={
        "email": "aichatuser@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Chat Session
    sess_resp = client.post("/api/v1/chat/sessions", json={"title": "Physics AI Tutor"}, headers=headers)
    assert sess_resp.status_code == 201, sess_resp.text
    session_data = sess_resp.json()
    assert session_data["title"] == "Physics AI Tutor"
    session_id = session_data["id"]

    # 3. List Chat Sessions
    list_resp = client.get("/api/v1/chat/sessions", headers=headers)
    assert list_resp.status_code == 200
    sessions_list = list_resp.json()
    assert len(sessions_list) >= 1

    # 4. RAG Chat Query within Session
    query_payload = {
        "message": "What is Newton's First Law of Motion?",
        "session_id": session_id,
        "top_k": 3
    }
    chat_resp = client.post("/api/v1/chat/query", json=query_payload, headers=headers)
    assert chat_resp.status_code == 200, chat_resp.text
    chat_data = chat_resp.json()["data"]

    assert "session_id" in chat_data
    assert "answer" in chat_data
    assert "confidence_score" in chat_data
    assert "confidence_label" in chat_data
    assert "sources" in chat_data
    assert "conversation_history" in chat_data

    # 5. Reload Chat Session History and verify persistence
    history_resp = client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers)
    assert history_resp.status_code == 200
    reloaded_session = history_resp.json()
    assert len(reloaded_session["messages"]) >= 2  # 1 user question + 1 AI answer

    # 6. Delete Chat Session
    del_resp = client.delete(f"/api/v1/chat/sessions/{session_id}", headers=headers)
    assert del_resp.status_code == 204

    # 7. Verify session deleted (404)
    verify_resp = client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers)
    assert verify_resp.status_code == 404
