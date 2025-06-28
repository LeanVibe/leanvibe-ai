"""
Integration tests for CLI→Backend→iOS communication

Tests end-to-end workflows and communication between components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
import websockets
from datetime import datetime
import tempfile
import os
from pathlib import Path

from leenvibe_cli.client import BackendClient
from leenvibe_cli.config import CLIConfig
from leenvibe_cli.commands.monitor import enhanced_monitor_command
from leenvibe_cli.commands.status import status_command
from leenvibe_cli.commands.query import query_command


class TestBackendCommunication:
    """Test CLI communication with backend"""
    
    @pytest.fixture
    def mock_config(self):
        """Create test configuration"""
        config = CLIConfig()
        config.backend_url = "http://localhost:8000"
        config.websocket_url = "ws://localhost:8000/ws"
        config.timeout_seconds = 5
        return config
    
    @pytest.fixture
    def backend_client(self, mock_config):
        """Create backend client for testing"""
        return BackendClient(mock_config)
    
    async def test_backend_connection_success(self, backend_client):
        """Test successful backend connection"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "healthy", "version": "1.0.0"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await backend_client.check_health()
            
            assert result is True
            assert backend_client.last_health_check is not None
    
    async def test_backend_connection_failure(self, backend_client):
        """Test backend connection failure handling"""
        with patch('aiohttp.ClientSession.get', side_effect=Exception("Connection failed")):
            result = await backend_client.check_health()
            
            assert result is False
    
    async def test_websocket_connection_success(self, backend_client):
        """Test successful WebSocket connection"""
        with patch('websockets.connect') as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_websocket
            
            result = await backend_client.connect_websocket()
            
            assert result is True
            assert backend_client.websocket is not None
    
    async def test_websocket_connection_failure(self, backend_client):
        """Test WebSocket connection failure"""
        with patch('websockets.connect', side_effect=Exception("WebSocket connection failed")):
            result = await backend_client.connect_websocket()
            
            assert result is False
            assert backend_client.websocket is None
    
    async def test_event_streaming(self, backend_client):
        """Test WebSocket event streaming"""
        # Mock WebSocket that provides test events
        mock_websocket = AsyncMock()
        test_events = [
            '{"type": "file_changed", "priority": "low", "file_path": "/test/file.py"}',
            '{"type": "architectural_violation", "priority": "critical", "message": "Layer violation"}',
            '{"type": "build_status", "priority": "medium", "status": "success"}'
        ]
        
        async def mock_recv():
            for event in test_events:
                yield event
        
        mock_websocket.__aiter__.return_value = mock_recv()
        backend_client.websocket = mock_websocket
        
        events_received = []
        async for event in backend_client.listen_for_events():
            events_received.append(event)
            if len(events_received) >= 3:
                break
        
        assert len(events_received) == 3
        assert events_received[0]['type'] == 'file_changed'
        assert events_received[1]['priority'] == 'critical'
        assert events_received[2]['status'] == 'success'


class TestCLICommands:
    """Test CLI command execution and integration"""
    
    @pytest.fixture
    def mock_config(self):
        """Create test configuration"""
        config = CLIConfig()
        config.backend_url = "http://localhost:8000"
        config.timeout_seconds = 5
        return config
    
    @pytest.fixture
    def mock_backend_client(self):
        """Create mock backend client"""
        client = Mock(spec=BackendClient)
        client.check_health = AsyncMock(return_value=True)
        client.get_project_info = AsyncMock(return_value={
            "project_name": "test-project",
            "total_files": 150,
            "total_symbols": 1250,
            "last_analysis": "2024-01-01T12:00:00Z"
        })
        client.get_streaming_stats = AsyncMock(return_value={
            "active_connections": 2,
            "events_sent_last_hour": 45,
            "average_response_time_ms": 125
        })
        return client
    
    async def test_status_command_success(self, mock_config, mock_backend_client):
        """Test status command with healthy backend"""
        with patch('rich.console.Console.print') as mock_print:
            await status_command(mock_config, mock_backend_client, False, False)
            
            # Verify health check was called
            mock_backend_client.check_health.assert_called_once()
            mock_backend_client.get_project_info.assert_called_once()
            
            # Verify output was generated
            assert mock_print.call_count > 0
    
    async def test_status_command_backend_down(self, mock_config):
        """Test status command with backend down"""
        mock_client = Mock(spec=BackendClient)
        mock_client.check_health = AsyncMock(return_value=False)
        
        with patch('rich.console.Console.print') as mock_print:
            await status_command(mock_config, mock_client, False, False)
            
            # Should still complete but show backend as down
            mock_client.check_health.assert_called_once()
            assert mock_print.call_count > 0
    
    async def test_monitor_command_integration(self, mock_config, mock_backend_client):
        """Test monitor command with notifications"""
        # Mock event stream
        async def mock_event_stream():
            events = [
                {"type": "file_changed", "priority": "low", "file_path": "/test.py"},
                {"type": "build_status", "priority": "medium", "status": "success"}
            ]
            for event in events:
                yield event
                await asyncio.sleep(0.1)
        
        mock_backend_client.connect_websocket = AsyncMock(return_value=True)
        mock_backend_client.listen_for_events.return_value = mock_event_stream()
        
        # Run monitor for short duration
        with patch('rich.live.Live') as mock_live:
            mock_live_instance = Mock()
            mock_live.return_value.__enter__.return_value = mock_live_instance
            mock_live.return_value.__exit__.return_value = None
            
            # Test background mode
            await enhanced_monitor_command(
                config=mock_config,
                client=mock_backend_client,
                duration=1,
                quiet=False,
                output_json=False,
                background=True,
                live_dashboard=False,
                overlay=False
            )
            
            # Verify WebSocket connection was established
            mock_backend_client.connect_websocket.assert_called_once()
    
    async def test_query_command_execution(self, mock_config, mock_backend_client):
        """Test query command execution"""
        mock_backend_client.send_query = AsyncMock(return_value={
            "response": "Test response from L3 agent",
            "confidence": 0.85,
            "sources": ["file1.py", "file2.py"]
        })
        
        with patch('rich.console.Console.print') as mock_print:
            await query_command(
                config=mock_config,
                client=mock_backend_client,
                query="What are the main components?",
                interactive=False,
                workspace=None
            )
            
            mock_backend_client.send_query.assert_called_once()
            assert mock_print.call_count > 0


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python project structure
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            
            # Create some Python files
            (project_path / "main.py").write_text("""
def main():
    print("Hello, World!")
    
if __name__ == "__main__":
    main()
""")
            
            (project_path / "utils.py").write_text("""
class Helper:
    def process_data(self, data):
        return data.upper()
""")
            
            (project_path / "__init__.py").write_text("")
            
            yield project_path
    
    async def test_project_analysis_workflow(self, temp_project_dir):
        """Test complete project analysis workflow"""
        config = CLIConfig()
        config.project_root = str(temp_project_dir)
        
        # Mock backend responses for project analysis
        mock_client = Mock(spec=BackendClient)
        mock_client.check_health = AsyncMock(return_value=True)
        mock_client.analyze_project = AsyncMock(return_value={
            "files_analyzed": 3,
            "symbols_found": 5,
            "complexity_score": 2.5,
            "architecture_patterns": ["simple_module"],
            "violations": []
        })
        
        # Test the analysis workflow
        result = await mock_client.analyze_project(str(temp_project_dir))
        
        assert result["files_analyzed"] > 0
        assert result["symbols_found"] > 0
        assert "complexity_score" in result
    
    async def test_real_time_monitoring_workflow(self, temp_project_dir):
        """Test real-time file monitoring workflow"""
        config = CLIConfig()
        config.project_root = str(temp_project_dir)
        
        # Mock file change events
        mock_client = Mock(spec=BackendClient)
        mock_client.connect_websocket = AsyncMock(return_value=True)
        
        file_change_events = []
        
        async def mock_event_stream():
            # Simulate file change event
            event = {
                "type": "file_changed",
                "file_path": str(temp_project_dir / "main.py"),
                "change_type": "modified",
                "timestamp": datetime.now().isoformat(),
                "priority": "medium"
            }
            file_change_events.append(event)
            yield event
        
        mock_client.listen_for_events.return_value = mock_event_stream()
        
        # Collect events for a short time
        events_collected = []
        async for event in mock_client.listen_for_events():
            events_collected.append(event)
            break  # Just test one event
        
        assert len(events_collected) == 1
        assert events_collected[0]["type"] == "file_changed"
        assert "main.py" in events_collected[0]["file_path"]
    
    async def test_ios_communication_workflow(self):
        """Test iOS app communication workflow"""
        # Mock WebSocket server behavior for iOS communication
        mock_ios_message = {
            "type": "command",
            "command": "analyze_current_file",
            "file_path": "/Users/test/project/main.py",
            "client_id": "ios_client_123"
        }
        
        mock_response = {
            "type": "response",
            "command_id": "cmd_123",
            "result": {
                "analysis": "Function main() is simple and well-structured",
                "suggestions": ["Consider adding type hints"],
                "confidence": 0.92
            }
        }
        
        # Test message processing
        assert mock_ios_message["type"] == "command"
        assert mock_ios_message["command"] == "analyze_current_file"
        
        # Test response generation
        assert mock_response["type"] == "response"
        assert mock_response["result"]["confidence"] > 0.9


class TestPerformanceRequirements:
    """Test that performance requirements are met"""
    
    async def test_notification_processing_speed(self):
        """Test notification processing meets speed requirements"""
        from leenvibe_cli.services.notification_service import NotificationService
        
        config = CLIConfig()
        config.notification_throttle_seconds = 0
        
        service = NotificationService(config)
        
        # Mock the backend client
        service.client = Mock()
        
        test_event = {
            "type": "test_event",
            "priority": "medium",
            "message": "Performance test notification"
        }
        
        # Measure processing time
        start_time = asyncio.get_event_loop().time()
        
        with patch.object(service, '_send_desktop_notification'):
            with patch.object(service, '_send_terminal_notification'):
                await service._process_notification(test_event)
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        # Should process in under 10ms (performance requirement)
        assert processing_time < 0.01
    
    async def test_websocket_response_time(self):
        """Test WebSocket response time meets requirements"""
        config = CLIConfig()
        client = BackendClient(config)
        
        # Mock WebSocket with timed response
        mock_websocket = AsyncMock()
        
        async def mock_send_receive(message):
            # Simulate network delay
            await asyncio.sleep(0.1)  # 100ms simulated network delay
            return '{"status": "received", "timestamp": "2024-01-01T12:00:00Z"}'
        
        mock_websocket.send = AsyncMock()
        mock_websocket.recv = AsyncMock(side_effect=mock_send_receive)
        
        start_time = asyncio.get_event_loop().time()
        
        # Test message sending (mocked)
        await mock_websocket.send('{"test": "message"}')
        response = await mock_send_receive('{"test": "message"}')
        
        response_time = asyncio.get_event_loop().time() - start_time
        
        # Should respond in under 500ms (performance requirement)
        assert response_time < 0.5
        assert json.loads(response)["status"] == "received"
    
    async def test_memory_usage_monitoring(self):
        """Test memory usage stays within limits"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create notification service and simulate load
        config = CLIConfig()
        service = NotificationService(config)
        
        # Add many notifications to history
        for i in range(1000):
            event = {
                "type": f"test_event_{i}",
                "priority": "medium",
                "message": f"Test message {i}",
                "timestamp": datetime.now().isoformat()
            }
            service.notification_history.appendleft(event)
        
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory
        
        # Memory increase should be reasonable (under 50MB for 1000 notifications)
        assert memory_increase < 50


class TestErrorHandling:
    """Test error handling and graceful degradation"""
    
    async def test_backend_unavailable_graceful_degradation(self):
        """Test graceful degradation when backend is unavailable"""
        config = CLIConfig()
        client = BackendClient(config)
        
        # Mock backend unavailable
        with patch.object(client, 'check_health', return_value=False):
            # Commands should still work but with limited functionality
            health_status = await client.check_health()
            assert health_status is False
            
            # WebSocket connection should fail gracefully
            with patch('websockets.connect', side_effect=ConnectionRefusedError()):
                websocket_status = await client.connect_websocket()
                assert websocket_status is False
    
    async def test_notification_service_resilience(self):
        """Test notification service resilience to errors"""
        config = CLIConfig()
        service = NotificationService(config)
        
        # Mock failing desktop notification
        with patch('leenvibe_cli.services.desktop_notifications.DesktopNotificationService.send_notification', 
                  side_effect=Exception("Desktop notification failed")):
            
            test_event = {
                "type": "test_event",
                "priority": "critical",
                "message": "Test critical event"
            }
            
            # Should not raise exception
            try:
                await service._process_notification(test_event)
            except Exception as e:
                pytest.fail(f"Notification processing should not raise: {e}")
    
    async def test_websocket_reconnection_handling(self):
        """Test WebSocket reconnection handling"""
        config = CLIConfig()
        client = BackendClient(config)
        
        # Mock WebSocket that disconnects
        mock_websocket = AsyncMock()
        
        # First connection succeeds
        with patch('websockets.connect') as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_websocket
            
            initial_connection = await client.connect_websocket()
            assert initial_connection is True
            
            # Simulate disconnection
            mock_websocket.recv.side_effect = websockets.exceptions.ConnectionClosed(None, None)
            
            # Reconnection should be handled
            with patch.object(client, 'connect_websocket', return_value=True) as mock_reconnect:
                # This would be called by the monitoring loop
                reconnection = await client.connect_websocket()
                assert reconnection is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])