"""
Pytest configuration and shared fixtures for LeanVibe backend tests.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add app directory to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def ai_service():
    """Create an AI service instance for testing."""
    from app.services.ai_service import AIService

    service = AIService()
    return service


@pytest.fixture
async def initialized_ai_service():
    """Create and initialize an AI service instance for testing."""
    from app.services.ai_service import AIService

    service = AIService()
    await service.initialize()
    return service


@pytest.fixture
def connection_manager():
    """Create a connection manager instance for testing."""
    from app.core.connection_manager import ConnectionManager

    return ConnectionManager()


@pytest.fixture
def sample_websocket_message():
    """Sample WebSocket message for testing."""
    return {"type": "command", "content": "/status", "client_id": "test-client"}


@pytest.fixture
def sample_agent_response():
    """Sample agent response for testing."""
    return {
        "status": "success",
        "message": "Test response",
        "data": None,
        "processing_time": 0.1,
    }


# Test environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Ensure we're in the correct directory
    os.chdir(PROJECT_ROOT)
    yield
    # Cleanup if needed
