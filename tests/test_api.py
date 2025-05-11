# tests/test_api.py
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from src.main import create_app
from src.config import settings


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as client:
        yield client


def test_health_check(client):
    """Test the basic health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["version"] == settings.API_VERSION


@patch("src.api.routes.email_generator")
def test_deep_health_check_success(mock_email_generator, client):
    """Test the deep health check endpoint with successful OpenAI connection"""
    # Setup mock
    mock_email_generator.client.models.list.return_value = MagicMock()

    # Make request
    response = client.get("/api/v1/health/deep")

    # Assert response
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["version"] == settings.API_VERSION

    # Verify OpenAI client was called
    mock_email_generator.client.models.list.assert_called_once_with(limit=1)


@patch("src.api.routes.email_generator")
def test_deep_health_check_failure(mock_email_generator, client):
    """Test the deep health check endpoint with failed OpenAI connection"""
    # Setup mock to raise an exception
    mock_email_generator.client.models.list.side_effect = Exception("OpenAI connection failed")

    # Make request
    response = client.get("/api/v1/health/deep")

    # Assert response
    assert response.status_code == 503
    assert "Service unavailable" in response.json()["detail"]


@patch("src.services.email_generator.EmailGenerator.generate_email")
def test_generate_email_success(mock_generate_email, client):
    """Test the email generation endpoint with successful response"""
    # Mock the email generator's response
    mock_response = {
        "theme_used": "growth",
        "anchor_signal": "30% YoY growth and hiring burst",
        "subject_line": "Your growth trajectory at TechNova",
        "email_body": "Hi Sarah,\n\nCongratulations on exceeding your Q1 targets by 27%!"
    }
    mock_generate_email.return_value = mock_response

    # Test request data
    test_data = {
        "prospect": {
            "first_name": "Sarah",
            "last_name": "Johnson",
            "job_title": "VP of Sales",
            "department": "Sales",
            "tenure_months": 18,
            "notable_achievement": "Exceeded Q1 targets by 27%"
        },
        "company": {
            "company_name": "TechNova Solutions",
            "industry": "SaaS",
            "employee_count": 250,
            "annual_revenue": "$45M",
            "funding_stage": "Series B",
            "growth_signals": "30% YoY growth, hiring burst in sales",
            "recent_news": "Launched new enterprise product line",
            "technography": "Salesforce, Marketo, Outreach.io",
            "description": "Cloud-based project management software"
        },
        "cta": {
            "ask": "15-min chat next Tuesday?",
            "calendar_link": "calendly.com/ingren/demo"
        }
    }

    # Make request
    response = client.post("/api/v1/generate-email", json=test_data)

    # Assert response
    assert response.status_code == 200
    assert response.json() == mock_response

    # Verify the email generator was called with the correct data
    mock_generate_email.assert_called_once()
    # Convert the arg to dict for comparison
    call_arg = mock_generate_email.call_args[0][0]
    assert call_arg["prospect"]["first_name"] == "Sarah"
    assert call_arg["company"]["company_name"] == "TechNova Solutions"


@patch("src.services.email_generator.EmailGenerator.generate_email")
def test_generate_email_error(mock_generate_email, client):
    """Test the email generation endpoint with an error response"""
    # Mock the email generator to raise an exception
    mock_generate_email.side_effect = Exception("Test error")

    # Test request data (minimal valid data)
    test_data = {
        "prospect": {
            "first_name": "John",
            "last_name": "Doe",
            "job_title": "CTO"
        },
        "company": {
            "company_name": "Test Company"
        }
    }

    # Make request
    response = client.post("/api/v1/generate-email", json=test_data)

    # Assert response
    assert response.status_code == 500
    assert "Email generation failed" in response.json()["detail"]