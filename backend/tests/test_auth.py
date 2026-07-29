import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_endpoint() -> None:
    """
    Test user registration successfully creates user record in DB.
    """
    payload = {
        "email": "testuser@example.com",
        "password": "strongpassword123",
        "full_name": "Test User",
        "role": "Student"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["role"] == "Student"
    assert data["full_name"] == "Test User"

def test_login_endpoint() -> None:
    """
    Test user login returns signed JWT access token and refresh token.
    """
    # 1. Register first
    reg_payload = {
        "email": "loginuser@example.com",
        "password": "strongpassword123",
        "full_name": "Login User",
        "role": "Teacher"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # 2. Login
    login_payload = {
        "email": "loginuser@example.com",
        "password": "strongpassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password() -> None:
    """
    Test login fails with 401 for incorrect password.
    """
    reg_payload = {
        "email": "wrongpwd@example.com",
        "password": "correctpassword123",
        "full_name": "Wrong Pwd User",
        "role": "Student"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrongpwd@example.com",
        "password": "wrongpassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401

def test_refresh_endpoint() -> None:
    """
    Test refreshing JWT access token with a valid refresh token.
    """
    # Register & Login
    reg_payload = {
        "email": "refreshuser@example.com",
        "password": "strongpassword123",
        "full_name": "Refresh User",
        "role": "Student"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_resp = client.post("/api/v1/auth/login", json={
        "email": "refreshuser@example.com",
        "password": "strongpassword123"
    })
    tokens = login_resp.json()

    # Refresh
    refresh_resp = client.post("/api/v1/auth/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })
    assert refresh_resp.status_code == 200
    refreshed_data = refresh_resp.json()
    assert "access_token" in refreshed_data
    assert "refresh_token" in refreshed_data

def test_me_endpoint() -> None:
    """
    Test retrieving active logged-in user profile details via GET /api/v1/auth/me.
    """
    reg_payload = {
        "email": "meuser@example.com",
        "password": "strongpassword123",
        "full_name": "Me User",
        "role": "Parent"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_resp = client.post("/api/v1/auth/login", json={
        "email": "meuser@example.com",
        "password": "strongpassword123"
    })
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert user_data["email"] == "meuser@example.com"
    assert user_data["role"] == "Parent"

def test_forgot_password_endpoint() -> None:
    """
    Test initiating forgot password recovery.
    """
    reg_payload = {
        "email": "forgotuser@example.com",
        "password": "strongpassword123",
        "full_name": "Forgot User",
        "role": "Student"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    response = client.post("/api/v1/auth/forgot-password", json={"email": "forgotuser@example.com"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_logout_endpoint() -> None:
    """
    Test user logout endpoint.
    """
    reg_payload = {
        "email": "logoutuser@example.com",
        "password": "strongpassword123",
        "full_name": "Logout User",
        "role": "Student"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_resp = client.post("/api/v1/auth/login", json={
        "email": "logoutuser@example.com",
        "password": "strongpassword123"
    })
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
