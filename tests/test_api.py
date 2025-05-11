# tests/test_api.py
import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as client:
        yield client


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_generate_email(client, monkeypatch):
    # Mock the email generator to avoid actual API calls
    async def mock_generate_email(*args, **kwargs):
        return "This is a mock email response."

    from src.services.email_generator import EmailGenerator
    monkeypatch.setattr(EmailGenerator, "generate_email", mock_generate_email)

    # Test data
    test_data = {
        "recipient_info": {
            "name": "John Doe",
            "email": "john.doe@example.com"
        },
        "context": {
            "purpose": "Follow-up",
            "product": "Test Product"
        }
    }

    response = client.post("/api/v1/generate-email", json=test_data)
    assert response.status_code == 200
    assert "email_text" in response.json()