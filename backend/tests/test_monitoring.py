import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_phase_15_monitoring_and_metrics() -> None:
    # 1. Root Metadata Endpoint
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    assert root_resp.json()["status"] == "success"

    # 2. Health Endpoint with DB Check
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["status"] == "success"
    assert "database" in health_data

    # 3. Prometheus Metrics Endpoint
    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    metrics_text = metrics_resp.text
    assert "nexora_app_up" in metrics_text
    assert "nexora_db_up" in metrics_text
    assert "nexora_http_requests_total" in metrics_text

    # 4. Response Timing Header
    assert "X-Process-Time" in health_resp.headers
