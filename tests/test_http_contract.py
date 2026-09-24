from fastapi.testclient import TestClient

from app.main import app


def test_root_and_health_expose_request_correlation():
    with TestClient(app) as client:
        root = client.get("/", headers={"X-Request-Id": "req-root-001"})
        health = client.get("/api/v1/health", headers={"X-Request-Id": "req-health-001"})
    assert root.status_code == 200
    assert root.headers["X-Request-Id"] == "req-root-001"
    assert health.status_code == 200
    assert health.headers["X-Request-Id"] == "req-health-001"


def test_request_validation_uses_structured_error_contract():
    with TestClient(app) as client:
        response = client.post("/api/v1/imports", headers={"X-Request-Id": "req-invalid-001"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["request_id"] == "req-invalid-001"
