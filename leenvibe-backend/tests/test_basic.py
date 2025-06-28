import asyncio

import pytest
from fastapi.testclient import TestClient


def test_placeholder():
    """Placeholder test to ensure test structure works"""
    assert True


def test_health_endpoint(test_client):
    """Test the health endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["service"] == "leenvibe-backend"


def test_root_endpoint(test_client):
    """Test the root endpoint"""
    response = test_client.get("/")
    assert response.status_code == 200


def test_status_endpoint(test_client):
    """Test the health endpoint (status functionality)"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_ai_service_initialization():
    from app.services.ai_service import AIService

    ai_service = AIService()
    await ai_service.initialize()
    assert ai_service.is_initialized == True


@pytest.mark.asyncio
async def test_basic_command_processing():
    from app.services.ai_service import AIService

    ai_service = AIService()
    await ai_service.initialize()

    test_command = {"type": "command", "content": "/status"}
    response = await ai_service.process_command(test_command)

    assert response["status"] == "success"
    assert "agent_status" in response["type"]
