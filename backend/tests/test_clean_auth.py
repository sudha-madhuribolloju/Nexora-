import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.database import get_db
from app.database.base import Base
from app.models.user import User

# In-memory SQLite for asynchronous testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

# Overrides get_db dependency to direct traffic to test DB
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Synchronously run create_all on startup
    loop = asyncio.get_event_loop()
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    loop.run_until_complete(create_tables())
    yield
    async def drop_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    loop.run_until_complete(drop_tables())

def test_auth_and_user_endpoints():
    """
    Performs end-to-end integration tests of registration, duplicate handling,
    credentials authentication, profile fetching, and profile updating.
    """
    # 1. Register a new user
    register_payload = {
        "email": "testuser@example.com",
        "password": "strongpassword123",
        "role": "Student"
    }
    response = client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "testuser@example.com"
    assert user_data["role"] == "Student"
    assert user_data["is_active"] is True
    assert "id" in user_data

    # 2. Duplicate registration checks
    response = client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["message"]

    # 3. Login with incorrect password
    login_payload = {
        "email": "testuser@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401

    # 5. Login with correct password
    login_payload["password"] = "strongpassword123"
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    token_data = response.json()
    assert token_data["token_type"] == "bearer"
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 6. Fetch /me profile details
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    me_data = response.json()
    assert me_data["email"] == "testuser@example.com"
    assert me_data["id"] == user_data["id"]

    # 7. Update user profile (email and role)
    update_payload = {
        "email": "newemail@example.com",
        "role": "Teacher"
    }
    response = client.put("/api/v1/users/me", json=update_payload, headers=headers)
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["email"] == "newemail@example.com"
    assert updated_data["role"] == "Teacher"
