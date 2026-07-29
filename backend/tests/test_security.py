import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_phase_13_security_hardening() -> None:
    # 1. Verify Security Headers present on responses
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers

    # 2. JWT Validation: Request with invalid/tampered token returns 401
    bad_token_headers = {"Authorization": "Bearer invalid.jwt.token.here"}
    unauth_resp = client.get("/api/v1/chat/sessions", headers=bad_token_headers)
    assert unauth_resp.status_code == 401

    # 3. Request with missing Authorization header returns 401
    missing_auth_resp = client.get("/api/v1/chat/sessions")
    assert missing_auth_resp.status_code == 401

    # 4. File Upload Security: Rejecting unauthorized extension
    bad_file_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("exploit.exe", b"MZ fake executable binary data", "application/x-msdownload")}
    )
    assert bad_file_resp.status_code == 400

    # 5. Input Sanitization & SQL Injection Protection
    sqli_payload = {
        "email": "' OR '1'='1",
        "password": "Password123!"
    }
    sqli_resp = client.post("/api/v1/auth/login", json=sqli_payload)
    assert sqli_resp.status_code in (400, 401, 422)
