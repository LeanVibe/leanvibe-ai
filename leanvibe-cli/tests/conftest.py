"""
Test Configuration and Fixtures for LeanVibe CLI

Provides common test fixtures, mocks, and utilities for comprehensive CLI testing.
Based on the successful backend testing infrastructure pattern.
"""

import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch
from click.testing import CliRunner
from pathlib import Path

from leanvibe_cli.client import BackendClient
from leanvibe_cli.config import CLIConfig
from leanvibe_cli.main import cli


@pytest.fixture
def cli_runner():
    """Click CLI test runner for command testing"""
    return CliRunner()


@pytest.fixture
def mock_backend_client():
    """Mock BackendClient for isolated testing"""
    client = MagicMock(spec=BackendClient)
    
    # Mock async methods
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.is_connected = True
    
    # Mock API responses
    client.get_health = AsyncMock(return_value={
        "status": "healthy",
        "uptime": "1h 23m",
        "version": "0.2.0",
        "services": {
            "ai_service": "running",
            "task_service": "running",
            "event_streaming": "running"
        }
    })
    
    client.health_check = AsyncMock(return_value={
        "status": "healthy",
        "uptime": "1h 23m",
        "version": "0.2.0",
        "service": "leanvibe-backend",
        "ai_ready": True,
        "agent_framework": "pydantic.ai",
        "sessions": {
            "active_sessions": 0,
            "total_requests": 0,
            "avg_response_time_ms": 0.0
        },
        "event_streaming": {
            "connected_clients": 0,
            "total_events_sent": 0,
            "events_per_second": 0.0,
            "failed_deliveries": 0
        },
        "llm_metrics": {
            "model_info": {
                "name": "Phi-3-Mini",
                "status": "ready",
                "parameter_count": "3.8B",
                "context_length": 131072,
                "estimated_memory_gb": 8.0
            },
            "performance": {
                "uptime_seconds": 5400,
                "recent_average_speed_tokens_per_sec": 50.0,
                "recent_average_latency_seconds": 0.5
            },
            "session_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_tokens": 0
            }
        }
    })
    
    client.get_analysis = AsyncMock(return_value={
        "file_count": 25,
        "complexity_score": 7.2,
        "issues": ["High cyclomatic complexity in user.py"],
        "suggestions": ["Consider breaking down large functions"],
        "metrics": {
            "total_lines": 2500,
            "test_coverage": 85.5
        }
    })
    
    client.query_agent = AsyncMock(return_value={
        "response": "Based on the analysis, your codebase has good structure with some areas for improvement.",
        "confidence": 0.85,
        "sources": ["ast_analysis", "dependency_graph"],
        "follow_up_questions": ["Would you like specific refactoring suggestions?"]
    })
    
    client.get_info = AsyncMock(return_value={
        "name": "LeanVibe Backend",
        "version": "0.2.0",
        "capabilities": ["ast_analysis", "graph_db", "ai_agent", "task_management"],
        "endpoints": ["/health", "/analyze", "/query", "/tasks"],
        "ai_models": ["Phi-3-Mini", "SimpleModel"],
        "deployment_mode": "production"
    })
    
    # Mock monitoring events
    async def mock_monitor_events():
        events = [
            {"type": "file_changed", "path": "/test/file.py", "timestamp": "2024-12-30T12:00:00Z"},
            {"type": "analysis_complete", "result": "success", "duration_ms": 150},
            {"type": "task_created", "task_id": "task-123", "title": "New Feature"}
        ]
        for event in events:
            yield event
            await asyncio.sleep(0.1)
    
    client.monitor_events = AsyncMock(return_value=mock_monitor_events())
    
    return client


@pytest.fixture
def test_config():
    """Test CLI configuration with realistic settings"""
    return CLIConfig(
        backend_url="http://localhost:8000",
        websocket_url="ws://localhost:8000/ws",
        timeout=30,
        verbose=False,
        client_id="test-client-123"
    )


@pytest.fixture
def test_config_verbose():
    """Test CLI configuration with verbose enabled"""
    return CLIConfig(
        backend_url="http://localhost:8000",
        websocket_url="ws://localhost:8000/ws",
        timeout=30,
        verbose=True,
        client_id="test-client-verbose"
    )


@pytest.fixture
def temp_config_file():
    """Temporary configuration file for testing"""
    config_content = """
backend:
  url: "http://localhost:8000"
  websocket_url: "ws://localhost:8000/ws"
  timeout: 30

client:
  id: "test-client"
  verbose: false

notifications:
  enabled: true
  desktop: true
  priority_filter: "medium"

monitoring:
  auto_connect: true
  reconnect_interval: 5
  max_events_per_second: 10
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_project_dir():
    """Temporary project directory for analysis testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create sample project structure
        (project_path / "src").mkdir()
        (project_path / "tests").mkdir()
        (project_path / "docs").mkdir()
        
        # Create sample Python files
        (project_path / "src" / "main.py").write_text("""
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")
        
        (project_path / "src" / "utils.py").write_text("""
def calculate_complexity(code):
    # Simulate complexity calculation
    return len(code.split('\n'))

def format_output(data):
    return json.dumps(data, indent=2)
""")
        
        (project_path / "tests" / "test_main.py").write_text("""
import pytest
from src.main import main

def test_main():
    # Basic test
    assert main() is None
""")
        
        yield project_path


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing"""
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock()
    mock_ws.close = AsyncMock()
    
    # Mock WebSocket message responses
    async def mock_recv_side_effect():
        messages = [
            json.dumps({"type": "connection_ack", "client_id": "test-client"}),
            json.dumps({"type": "file_changed", "path": "/test/file.py"}),
            json.dumps({"type": "analysis_complete", "status": "success"})
        ]
        for msg in messages:
            yield msg
    
    mock_ws.recv.side_effect = mock_recv_side_effect()
    return mock_ws


@pytest.fixture
def isolated_filesystem():
    """Isolated filesystem for CLI tests"""
    with CliRunner().isolated_filesystem():
        yield


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for API testing"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        
        # Mock HTTP responses
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        mock_instance.get.return_value = mock_response
        mock_instance.post.return_value = mock_response
        mock_instance.put.return_value = mock_response
        mock_instance.delete.return_value = mock_response
        
        mock_client.return_value.__aenter__.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_desktop_notifications():
    """Mock desktop notification system"""
    with patch('leanvibe_cli.services.desktop_notifications.DesktopNotificationService') as mock_service:
        mock_instance = MagicMock()
        mock_instance.send_notification = MagicMock(return_value=True)
        mock_instance.is_supported = MagicMock(return_value=True)
        mock_service.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def performance_metrics():
    """Performance metrics tracking for tests"""
    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.memory_usage = []
            
        def start(self):
            import time
            self.start_time = time.time()
            
        def stop(self):
            import time
            self.end_time = time.time()
            
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
            
        def record_memory(self):
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_usage.append(memory_mb)
            
        def max_memory(self):
            return max(self.memory_usage) if self.memory_usage else 0
    
    return PerformanceTracker()


@pytest.fixture(autouse=True)
def cleanup_async_tasks():
    """Automatically cleanup async tasks after each test"""
    yield
    
    # Cancel any remaining async tasks
    try:
        loop = asyncio.get_running_loop()
        tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
        for task in tasks:
            task.cancel()
        
        if tasks:
            asyncio.gather(*tasks, return_exceptions=True)
    except RuntimeError:
        # No running loop, nothing to cleanup
        pass


# Test utility functions
def assert_cli_success(result, expected_text=None):
    """Assert CLI command executed successfully"""
    assert result.exit_code == 0, f"CLI command failed with output: {result.output}"
    if expected_text:
        assert expected_text.lower() in result.output.lower()


def assert_cli_error(result, expected_error=None):
    """Assert CLI command failed as expected"""
    assert result.exit_code != 0, f"CLI command should have failed but succeeded: {result.output}"
    if expected_error:
        assert expected_error.lower() in result.output.lower()


def create_mock_analysis_response(complexity=7.0, issues_count=3):
    """Create realistic mock analysis response"""
    return {
        "file_count": 15,
        "complexity_score": complexity,
        "issues": [f"Issue {i}: Sample code quality issue" for i in range(issues_count)],
        "suggestions": [
            "Consider refactoring large functions",
            "Add more unit tests",
            "Improve documentation coverage"
        ],
        "metrics": {
            "total_lines": 1500,
            "code_lines": 1200,
            "comment_lines": 150,
            "test_coverage": 78.5,
            "duplication_percentage": 12.3
        },
        "analysis_duration_ms": 250
    }


def create_mock_health_response(status="healthy"):
    """Create realistic mock health response"""
    return {
        "status": status,
        "uptime": "2h 45m",
        "version": "0.2.0",
        "services": {
            "ai_service": "running" if status == "healthy" else "degraded",
            "task_service": "running",
            "event_streaming": "running",
            "graph_service": "running"
        },
        "metrics": {
            "total_requests": 1247,
            "avg_response_time_ms": 125,
            "error_rate": 0.02,
            "active_connections": 5
        },
        "ai_models": {
            "primary": "Phi-3-Mini",
            "fallback": "SimpleModel",
            "status": "loaded"
        }
    }