from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root() -> None:
    """
    Test root endpoint returns correct service status and metadata.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["service"] == "Nexora AI Backend"
    assert data["version"] == "1.0"

def test_read_health() -> None:
    """
    Test health check endpoint returns 200 and component configuration details.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "database" in data

