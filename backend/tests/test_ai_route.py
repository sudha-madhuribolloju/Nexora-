import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_chat_endpoint_unauthenticated() -> None:
    """
    Test POST /api/v1/ai/chat returns 200 OK for unauthenticated/guest users.
    """
    payload = {"message": "Hello Nexora AI", "stream": False}
    response = client.post("/api/v1/ai/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data or "reply" in data



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


def test_voice_processing_endpoint_success() -> None:
    """
    Test POST /api/v1/ai/voice-processing returns 200 and valid VoiceProcessingResponse structure.
    """
    payload = {"speakerName": "Dr. Sarah Jenkins"}
    response = client.post("/api/v1/ai/voice-processing", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["speaker"] == "Dr. Sarah Jenkins"
    assert "voicePrintId" in data
    assert "confidence" in data
    assert "clarityScore" in data
    assert "noiseReducedTranscript" in data


def test_summarize_endpoint_success() -> None:
    """
    Test POST /api/v1/ai/summarize returns 200 and valid Summary response.
    """
    payload = {"transcript": "Today we are discussing quantum mechanics and entanglement."}
    response = client.post("/api/v1/ai/summarize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert len(data["summary"]) > 0


def test_nlp_endpoint_success() -> None:
    """
    Test POST /api/v1/ai/nlp returns 200 and valid NLPResponse structure.
    """
    payload = {"transcript": "CRISPR-Cas9 acts as molecular scissors using guide RNA to edit target genes."}
    response = client.post("/api/v1/ai/nlp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data
    assert "topics" in data
    assert "definitions" in data
    assert "actionItems" in data


def test_research_endpoint_success() -> None:
    """
    Test POST /api/v1/ai/research returns 200 and valid ResearchResponse structure.
    """
    payload = {"query": "Quantum entanglement in distributed computing"}
    response = client.post("/api/v1/ai/research", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "findings" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)


def test_notes_endpoint_success() -> None:
    """
    Test POST /api/v1/ai/notes returns 200 and valid NotesResponse structure.
    """
    payload = {"topic": "Demand-pull Inflation", "subject": "Economics"}
    response = client.post("/api/v1/ai/notes", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "notes" in data
    assert len(data["notes"]) > 0


def test_generate_quiz_endpoint_success() -> None:
    """
    Test POST /api/v1/quizzes/generate returns 200 and valid Quiz list.
    """
    payload = {"topic": "Quantum Mechanics", "difficulty": "Intermediate", "questionCount": 5}
    response = client.post("/api/v1/quizzes/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "quiz" in data
    assert len(data["quiz"]) > 0
    assert "question" in data["quiz"][0]
    assert "options" in data["quiz"][0]


def test_generate_assignment_endpoint_success() -> None:
    """
    Test POST /api/v1/assignments/generate returns 200 and valid reply text.
    """
    payload = {"topic": "CRISPR-Cas9 Editing"}
    response = client.post("/api/v1/assignments/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 0



