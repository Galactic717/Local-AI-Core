import pytest
from fastapi.testclient import TestClient
from src.services.brain_router import app

client = TestClient(app)

def test_health_endpoint():
    """Verify that the brain router health check returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Brain Router"}

def test_chat_validation():
    """Verify that the chat router rejects empty messages."""
    response = client.post("/api/v1/chat", json={"messages": []})
    assert response.status_code == 400
    assert "messages must not be empty" in response.text
