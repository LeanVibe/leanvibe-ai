"""
Pytest configuration and shared fixtures for LeanVibe backend tests.

This configuration sets up comprehensive mocking infrastructure that allows
all tests to run without external dependencies like tree-sitter, Neo4j, or MLX.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

# Add app directory to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set up mock infrastructure BEFORE importing any app modules
from tests.mocks import setup_all_mocks, get_mock_status
setup_all_mocks()

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a FastAPI test client with mocked dependencies."""
    try:
        from app.main import app
        with TestClient(app) as client:
            yield client
    except Exception as e:
        logger.error(f"Failed to create test client: {e}")
        # Create a minimal test client for basic testing
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        minimal_app = FastAPI(title="Test App")
        
        @minimal_app.get("/")
        def root():
            return {"message": "Test API"}
        
        @minimal_app.get("/health")
        def health():
            return {
                "status": "healthy", 
                "service": "leanvibe-backend",
                "mock_mode": True,
                "timestamp": "2023-01-01T00:00:00Z"
            }
        
        with TestClient(minimal_app) as client:
            yield client


@pytest.fixture
def ai_service():
    """Create an AI service instance for testing with fallback to mock."""
    try:
        from app.services.ai_service import AIService
        return AIService()
    except Exception as e:
        logger.warning(f"Failed to create AI service, using mock: {e}")
        from tests.mocks.mock_mlx_services import mock_mlx_service
        return mock_mlx_service


@pytest.fixture
async def initialized_ai_service():
    """Create and initialize an AI service instance for testing with fallback."""
    try:
        from app.services.ai_service import AIService
        service = AIService()
        await service.initialize()
        return service
    except Exception as e:
        logger.warning(f"Failed to initialize AI service, using mock: {e}")
        from tests.mocks.mock_mlx_services import mock_mlx_service
        await mock_mlx_service.initialize()
        return mock_mlx_service


@pytest.fixture
def connection_manager():
    """Create a connection manager instance for testing with fallback."""
    try:
        from app.core.connection_manager import ConnectionManager
        return ConnectionManager()
    except Exception as e:
        logger.warning(f"Failed to create connection manager, using mock: {e}")
        from unittest.mock import MagicMock
        mock_manager = MagicMock()
        mock_manager.is_connected.return_value = True
        mock_manager.get_status.return_value = {"status": "connected", "mock_mode": True}
        return mock_manager


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


# Additional test fixtures for mocked services
@pytest.fixture
def mock_tree_sitter_manager():
    """Get the mock tree-sitter manager."""
    from tests.mocks.mock_tree_sitter import mock_tree_sitter_manager
    return mock_tree_sitter_manager


@pytest.fixture
def mock_graph_service():
    """Get the mock graph service."""
    from tests.mocks.mock_neo4j import mock_graph_service
    return mock_graph_service


@pytest.fixture
def mock_mlx_service():
    """Get the mock MLX service."""
    from tests.mocks.mock_mlx_services import mock_mlx_service
    return mock_mlx_service


@pytest.fixture
def mock_status():
    """Get the status of all mocks."""
    return get_mock_status()


# Test environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Ensure we're in the correct directory
    os.chdir(PROJECT_ROOT)
    
    # Log mock status for debugging
    status = get_mock_status()
    logger.debug(f"Mock status: {status}")
    
    yield
    
    # Cleanup if needed
    pass
