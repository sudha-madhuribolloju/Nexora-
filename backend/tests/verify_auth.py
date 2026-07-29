import unittest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.database import get_db
from app.database.base import Base

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

class TestAuthModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create database tables in the loop
        loop = asyncio.get_event_loop()
        async def create_tables():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        loop.run_until_complete(create_tables())

    @classmethod
    def tearDownClass(cls):
        # Drop database tables in the loop
        loop = asyncio.get_event_loop()
        async def drop_tables():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        loop.run_until_complete(drop_tables())

    def test_e2e_flow(self):
        client = TestClient(app)

        # 1. Register a new user
        register_payload = {
            "email": "testuser@example.com",
            "password": "strongpassword123",
            "role": "Student"
        }
        response = client.post("/api/v1/auth/register", json=register_payload)
        self.assertEqual(response.status_code, 201)
        user_data = response.json()
        self.assertEqual(user_data["email"], "testuser@example.com")
        self.assertEqual(user_data["role"], "Student")

        # 2. Duplicate registration should fail
        response = client.post("/api/v1/auth/register", json=register_payload)
        self.assertEqual(response.status_code, 400)

        # 3. Login
        login_payload = {
            "email": "testuser@example.com",
            "password": "strongpassword123"
        }
        response = client.post("/api/v1/auth/login", json=login_payload)
        self.assertEqual(response.status_code, 200)
        token_data = response.json()
        token = token_data["access_token"]

        # 4. Get Current User Profile
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        me_data = response.json()
        self.assertEqual(me_data["email"], "testuser@example.com")

        # 5. Update Profile
        update_payload = {
            "email": "newemail@example.com",
            "role": "Teacher"
        }
        response = client.put("/api/v1/users/me", json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        updated_data = response.json()
        self.assertEqual(updated_data["email"], "newemail@example.com")
        self.assertEqual(updated_data["role"], "Teacher")

if __name__ == '__main__':
    unittest.main()
