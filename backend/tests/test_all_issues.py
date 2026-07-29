import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.database import get_db
from app.database.base import Base
from app.models.user import User

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

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
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

def test_jwt_auth_refresh_profile_and_recordings():
    # 1. Register User
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "teacher@nexora.school",
        "password": "password123",
        "role": "Teacher",
        "full_name": "Prof Srinivas"
    })
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    # 2. Login -> verify access_token AND refresh_token returned (Issue 1)
    login_res = client.post("/api/v1/auth/login", json={
        "email": "teacher@nexora.school",
        "password": "password123"
    })
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 3. GET /api/v1/auth/me returns 200 OK (Issue 1)
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "teacher@nexora.school"
    assert me_res.json()["id"] == user_id

    # 4. Token refresh via POST /api/v1/auth/refresh (Issue 1)
    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    new_tokens = ref_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # 5. Profile update via PUT /api/v1/users/me (Issue 2)
    update_res = client.put("/api/v1/users/me", json={
        "full_name": "Prof Srinivas B",
        "phone": "+1555019283",
        "bio": "Quantum Mechanics & Superposition Professor"
    }, headers=headers)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["full_name"] == "Prof Srinivas B"
    assert updated["phone"] == "+1555019283"
    assert updated["bio"] == "Quantum Mechanics & Superposition Professor"

    # 6. Lecture Recording Start, Chunk, Stop (Issue 5 & 6)
    start_rec = client.post("/api/v1/lecture/lec_101/recording/start", headers=headers)
    assert start_rec.status_code == 200
    rec_id = start_rec.json()["recording_id"]

    # Chunk upload
    chunk_res = client.post(
        "/api/v1/lecture/lec_101/recording/chunk",
        data={"recording_id": rec_id},
        files={"chunk": ("chunk1.webm", b"\x00\x01\x02\x03", "video/webm")},
        headers=headers
    )
    assert chunk_res.status_code == 200

    # Stop recording -> saves to PostgreSQL
    stop_rec = client.post(
        "/api/v1/lecture/lec_101/recording/stop",
        data={"recording_id": rec_id, "duration": 12.5},
        headers=headers
    )
    assert stop_rec.status_code == 200
    rec_record = stop_rec.json()
    assert rec_record["duration"] == 12.5
    assert "filename" in rec_record

    # List recordings
    list_rec = client.get("/api/v1/lecture/recordings", headers=headers)
    assert list_rec.status_code == 200
    assert len(list_rec.json()) >= 1
