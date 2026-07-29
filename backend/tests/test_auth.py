from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    """
    Fixture to mock the Supabase client interface for state-free auth testing.
    """
    mock_client = MagicMock()
    mock_auth = MagicMock()
    
    # 1. Mock Sign Up Response
    mock_signup_response = MagicMock()
    mock_signup_response.user = MagicMock(
        id="00000000-0000-0000-0000-000000000001",
        email="testuser@example.com"
    )
    mock_auth.sign_up.return_value = mock_signup_response
    
    # 2. Mock Sign In Response
    mock_signin_response = MagicMock()
    mock_signin_response.user = MagicMock(
        id="00000000-0000-0000-0000-000000000001",
        email="testuser@example.com",
        user_metadata={"full_name": "Test User", "role": "Student"}
    )
    mock_signin_response.session = MagicMock(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token"
    )
    mock_auth.sign_in_with_password.return_value = mock_signin_response
    
    # 3. Mock Refresh Session Response
    mock_refresh_response = MagicMock()
    mock_refresh_response.user = MagicMock(
        id="00000000-0000-0000-0000-000000000001",
        email="testuser@example.com",
        user_metadata={"full_name": "Test User", "role": "Student"}
    )
    mock_refresh_response.session = MagicMock(
        access_token="new_mock_access_token",
        refresh_token="new_mock_refresh_token"
    )
    mock_auth.refresh_session.return_value = mock_refresh_response
    
    # 4. Mock Get User Response
    mock_getuser_response = MagicMock()
    mock_getuser_response.user = MagicMock(
        id="00000000-0000-0000-0000-000000000001",
        email="testuser@example.com",
        user_metadata={"full_name": "Test User", "role": "Student"}
    )
    mock_auth.get_user.return_value = mock_getuser_response
    
    mock_client.auth = mock_auth
    
    # Apply monkeypatching across files importing supabase client
    import app.database.supabase
    monkeypatch.setattr(app.database.supabase, "supabase", mock_client)
    import app.services.auth_service
    monkeypatch.setattr(app.services.auth_service, "supabase", mock_client)
    import app.api.dependencies
    monkeypatch.setattr(app.api.dependencies, "supabase", mock_client)
    
    return mock_client

def test_register_endpoint() -> None:
    """
    Test user registration successfully calls Supabase sign_up and registers user profile.
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
    Test user login returns mock JWT access token, refresh token, and synced profile.
    """
    payload = {
        "email": "testuser@example.com",
        "password": "strongpassword123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "mock_access_token"
    assert data["refresh_token"] == "mock_refresh_token"
    assert data["user"]["email"] == "testuser@example.com"
    assert data["user"]["full_name"] == "Test User"

def test_logout_endpoint() -> None:
    """
    Test user logout API endpoint with authorization token.
    """
    headers = {"Authorization": "Bearer mock_access_token"}
    response = client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_refresh_endpoint() -> None:
    """
    Test token refresh API endpoint.
    """
    payload = {"refresh_token": "mock_refresh_token"}
    response = client.post("/api/v1/auth/refresh", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "new_mock_access_token"
    assert data["refresh_token"] == "new_mock_refresh_token"
    assert data["user"]["email"] == "testuser@example.com"

def test_me_endpoint() -> None:
    """
    Test retrieving active logged-in user details.
    """
    headers = {"Authorization": "Bearer mock_access_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"
