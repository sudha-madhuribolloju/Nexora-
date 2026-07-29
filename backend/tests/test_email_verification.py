"""
tests/test_email_verification.py
──────────────────────────────────
Integration tests for environment-configurable email verification workflow.
Tests both Development mode (EMAIL_VERIFICATION_REQUIRED=False) and
Production mode (EMAIL_VERIFICATION_REQUIRED=True with HTTP 403 enforcement).
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dev_mode_email_verification_disabled(monkeypatch):
    """
    In Development Mode (EMAIL_VERIFICATION_REQUIRED=False):
    - Users register and are automatically activated.
    - verification_required is False.
    - Immediate login succeeds.
    """
    import app.core.config
    import app.services.auth_service
    monkeypatch.setattr(app.core.config.settings, "EMAIL_VERIFICATION_REQUIRED", False)
    monkeypatch.setattr(app.services.auth_service.settings, "EMAIL_VERIFICATION_REQUIRED", False)

    unique_email = f"devuser_{uuid.uuid4().hex[:8]}@nexora.school"
    reg_payload = {
        "email": unique_email,
        "password": "password123",
        "full_name": "Dev User",
        "role": "Student"
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["verification_required"] is False
    assert data["email"] == unique_email

    # Immediate Login
    login_payload = {
        "email": unique_email,
        "password": "password123"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_prod_mode_email_verification_required(monkeypatch):
    """
    In Production Mode (EMAIL_VERIFICATION_REQUIRED=True):
    - Registration returns verification_required = True.
    - Login prior to OTP verification returns HTTP 403 Forbidden with exact detail message.
    """
    import app.core.config
    import app.services.auth_service
    monkeypatch.setattr(app.core.config.settings, "EMAIL_VERIFICATION_REQUIRED", True)
    monkeypatch.setattr(app.services.auth_service.settings, "EMAIL_VERIFICATION_REQUIRED", True)

    unique_email = f"produser_{uuid.uuid4().hex[:8]}@nexora.school"
    reg_payload = {
        "email": unique_email,
        "password": "password123",
        "full_name": "Prod User",
        "role": "Student"
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["verification_required"] is True

    # Unverified login attempt MUST fail with HTTP 403 Forbidden
    login_payload = {
        "email": unique_email,
        "password": "password123"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 403
    assert login_res.json()["detail"] == "Please verify your email before logging in."
