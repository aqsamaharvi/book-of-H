"""
Unit Tests for simplified FastAPI Application
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Root endpoint returns Hello World"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_root_endpoint_returns_json():
    """Verify response is valid JSON with correct structure"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)

