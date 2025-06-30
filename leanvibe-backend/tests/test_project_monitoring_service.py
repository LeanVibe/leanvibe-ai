"""
Tests for Project Monitoring Service

Comprehensive test suite for the extracted monitoring service functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from pathlib import Path

from app.services.project_monitoring_service import ProjectMonitoringService
from app.models.monitoring_models import MonitoringStatus, ChangeType


class TestProjectMonitoringService:
    """Test the core ProjectMonitoringService functionality"""
    
    @pytest.fixture
    def monitoring_service(self):
        """Create a fresh monitoring service instance"""
        return ProjectMonitoringService()
    
    @pytest.fixture
    def mock_file_monitor_service(self):
        """Mock the file monitor service dependency"""
        mock = MagicMock()
        mock.initialized = True
        mock.initialize = AsyncMock(return_value=True)
        mock.start_monitoring = AsyncMock(return_value=True)
        mock.stop_monitoring = AsyncMock(return_value=True)
        mock.get_session = MagicMock()
        mock.get_metrics = MagicMock()
        mock.get_recent_changes = AsyncMock(return_value=[])
        mock.analyze_impact = AsyncMock(return_value={})
        return mock
    
    @pytest.fixture
    def mock_incremental_indexer(self):
        """Mock the incremental indexer dependency"""
        mock = MagicMock()
        mock.get_or_create_project_index = AsyncMock()
        mock.get_metrics = MagicMock(return_value={
            'incremental_updates': 42,
            'files_reanalyzed': 15,
            'symbols_updated': 128,
            'cache_hits': 85,
            'cache_misses': 12,
            'average_update_time_ms': 250.5,
            'total_indexing_time_ms': 1500.2,
            'index_size_mb': 8.5,
            'memory_usage_mb': 45.2,
            'success_rate': 0.95,
            'error_rate': 0.05
        })
        return mock

    async def test_service_initialization(self, monitoring_service, mock_file_monitor_service):
        """Test service initialization"""
        with patch('app.services.project_monitoring_service.file_monitor_service', mock_file_monitor_service):
            result = await monitoring_service.initialize()
            
            assert result is True
            assert monitoring_service._initialized is True
            mock_file_monitor_service.initialize.assert_called_once()

    def test_get_capabilities(self, monitoring_service):
        """Test service capabilities listing"""
        capabilities = monitoring_service.get_capabilities()
        
        expected_capabilities = [
            "real_time_monitoring",
            "change_detection", 
            "impact_analysis",
            "project_indexing",
            "performance_metrics",
            "session_management"
        ]
        
        assert all(cap in capabilities for cap in expected_capabilities)

    def test_get_health_status(self, monitoring_service):
        """Test health status reporting"""
        # Before initialization
        status = monitoring_service.get_health_status()
        assert status["service"] == "project_monitoring"
        assert status["initialized"] is False
        assert status["active_sessions"] == 0
        
        # After adding a session
        monitoring_service.active_sessions["test-client"] = "test-session"
        monitoring_service._initialized = True
        
        status = monitoring_service.get_health_status()
        assert status["initialized"] is True
        assert status["active_sessions"] == 1

    async def test_start_monitoring_success(self, monitoring_service, mock_file_monitor_service):
        """Test successful monitoring start"""
        workspace_path = "/test/workspace"
        client_id = "test-client"
        
        with patch('app.services.project_monitoring_service.file_monitor_service', mock_file_monitor_service):
            result = await monitoring_service.start_monitoring(
                client_id=client_id,
                workspace_path=workspace_path
            )
            
            assert result["status"] == "success"
            assert result["type"] == "monitoring_started"
            assert workspace_path in result["data"]["workspace_path"]
            assert client_id in monitoring_service.active_sessions
            
            # Verify file monitor service was called correctly
            mock_file_monitor_service.start_monitoring.assert_called_once()
            call_args = mock_file_monitor_service.start_monitoring.call_args
            assert call_args[1]["client_id"] == client_id

    async def test_start_monitoring_no_workspace_path(self, monitoring_service):
        """Test monitoring start without workspace path"""
        result = await monitoring_service.start_monitoring(
            client_id="test-client",
            workspace_path=None
        )
        
        assert result["status"] == "error"
        assert "required" in result["message"]

    async def test_start_monitoring_service_failure(self, monitoring_service, mock_file_monitor_service):
        """Test monitoring start when file monitor service fails"""
        mock_file_monitor_service.start_monitoring.return_value = False
        
        with patch('app.services.project_monitoring_service.file_monitor_service', mock_file_monitor_service):
            result = await monitoring_service.start_monitoring(
                client_id="test-client",
                workspace_path="/test/workspace"
            )
            
            assert result["status"] == "error"
            assert "Failed to start" in result["message"]

    async def test_stop_monitoring_success(self, monitoring_service, mock_file_monitor_service):
        """Test successful monitoring stop"""
        client_id = "test-client"
        session_id = "test-session"
        
        # Setup active session
        monitoring_service.active_sessions[client_id] = session_id
        
        # Mock session data
        mock_session = MagicMock()
        mock_session.started_at = datetime.now() - timedelta(minutes=5)
        mock_session.total_changes_detected = 3
        mock_session.total_files_analyzed = 15
        mock_session.total_errors = 0
        mock_session.configuration.workspace_path = "/test/workspace"
        mock_session.dict.return_value = {"session": "data"}
        
        mock_file_monitor_service.get_session.return_value = mock_session
        
        with patch('app.services.project_monitoring_service.file_monitor_service', mock_file_monitor_service):
            result = await monitoring_service.stop_monitoring(client_id)
            
            assert result["status"] == "success"
            assert result["type"] == "monitoring_stopped"
            assert client_id not in monitoring_service.active_sessions
            
            mock_file_monitor_service.stop_monitoring.assert_called_once_with(session_id)

    async def test_stop_monitoring_no_session(self, monitoring_service):
        """Test stop monitoring with no active session"""
        result = await monitoring_service.stop_monitoring("nonexistent-client")
        
        assert result["status"] == "error"
        assert "No active monitoring session" in result["message"]

    async def test_get_monitoring_status_no_session(self, monitoring_service):
        """Test monitoring status with no active session"""
        result = await monitoring_service.get_monitoring_status("test-client")
        
        assert result["status"] == "success"
        assert result["data"]["active"] is False
        assert "No active monitoring session" in result["data"]["summary"]

    async def test_get_monitoring_status_active_session(self, monitoring_service, mock_file_monitor_service):
        """Test monitoring status with active session"""
        client_id = "test-client"
        session_id = "test-session"
        
        # Setup active session
        monitoring_service.active_sessions[client_id] = session_id
        
        # Mock session and metrics
        mock_session = MagicMock()
        mock_session.status = MonitoringStatus.ACTIVE
        mock_session.started_at = datetime.now() - timedelta(hours=1, minutes=30)
        mock_session.total_changes_detected = 5
        mock_session.total_files_analyzed = 25
        mock_session.total_errors = 1
        mock_session.configuration.workspace_path = "/test/workspace"
        mock_session.last_activity = datetime.now() - timedelta(minutes=5)
        
        mock_metrics = MagicMock()
        mock_metrics.changes_per_minute = 2.5
        mock_metrics.average_analysis_time_ms = 150.0
        mock_metrics.queue_depth = 0
        mock_metrics.dict.return_value = {"metrics": "data"}
        
        mock_file_monitor_service.get_session.return_value = mock_session
        mock_file_monitor_service.get_metrics.return_value = mock_metrics
        
        with patch('app.services.project_monitoring_service.file_monitor_service', mock_file_monitor_service):
            result = await monitoring_service.get_monitoring_status(client_id)
            
            assert result["status"] == "success"
            assert result["data"]["active"] is True
            assert result["data"]["session_id"] == session_id
            assert result["data"]["total_changes"] == 5
            assert "1h 30m" in result["data"]["summary"]

    async def test_get_recent_changes_success(self, monitoring_service, mock_file_monitor_service):
        """Test getting recent changes successfully"""
        client_id = "test-client"
        session_id = "test-session"
        
        # Setup active session
        monitoring_service.active_sessions[client_id] = session_id
        
        # Mock change data
        mock_change = MagicMock()
        mock_change.file_path = "/test/workspace/file.py"
        mock_change.timestamp = datetime.now() - timedelta(minutes=2)
        mock_change.change_type = ChangeType.MODIFIED
        mock_change.lines_added = 5
        mock_change.lines_removed = 2
        mock_change.lines_modified = 3
        mock_change.language = "python"
        mock_change.is_binary = False
        mock_change.file_size = 1024
        mock_change.id = "change-1"
        
        mock_file_monitor_service.get_recent_changes.return_value = [mock_change]
        
        with patch('app.services.project_monitoring_service.file_monitor_service', mock_file_monitor_service):
            result = await monitoring_service.get_recent_changes(client_id, limit=10)
            
            assert result["status"] == "success"
            assert result["type"] == "recent_changes"
            assert len(result["data"]["changes"]) == 1
            assert result["data"]["changes"][0]["file_name"] == "file.py"
            assert "Recent File Changes" in result["data"]["summary"]

    async def test_get_recent_changes_no_changes(self, monitoring_service, mock_file_monitor_service):
        """Test getting recent changes when none exist"""
        client_id = "test-client"
        session_id = "test-session"
        
        monitoring_service.active_sessions[client_id] = session_id
        mock_file_monitor_service.get_recent_changes.return_value = []
        
        with patch('app.services.project_monitoring_service.file_monitor_service', mock_file_monitor_service):
            result = await monitoring_service.get_recent_changes(client_id)
            
            assert result["status"] == "success"
            assert len(result["data"]["changes"]) == 0
            assert "No recent file changes" in result["data"]["summary"]

    async def test_refresh_project_index_success(self, monitoring_service, mock_incremental_indexer):
        """Test successful project index refresh"""
        workspace_path = "/test/workspace"
        
        # Mock project index
        mock_project_index = MagicMock()
        mock_project_index.total_files = 20
        mock_project_index.supported_files = 15
        mock_project_index.symbols = {"symbol1": "data", "symbol2": "data"}
        mock_project_index.parsing_errors = 1
        
        mock_incremental_indexer.get_or_create_project_index.return_value = mock_project_index
        
        with patch('app.services.project_monitoring_service.incremental_indexer', mock_incremental_indexer):
            result = await monitoring_service.refresh_project_index(workspace_path)
            
            assert result["status"] == "success"
            assert result["type"] == "index_updated"
            assert result["data"]["supported_files"] == 15
            assert result["data"]["total_symbols"] == 2
            assert "Project Index Updated" in result["data"]["summary"]

    async def test_refresh_project_index_failure(self, monitoring_service, mock_incremental_indexer):
        """Test project index refresh failure"""
        workspace_path = "/test/workspace"
        mock_incremental_indexer.get_or_create_project_index.return_value = None
        
        with patch('app.services.project_monitoring_service.incremental_indexer', mock_incremental_indexer):
            result = await monitoring_service.refresh_project_index(workspace_path)
            
            assert result["status"] == "error"
            assert "Failed to update" in result["message"]

    async def test_get_indexer_metrics(self, monitoring_service, mock_incremental_indexer):
        """Test getting indexer metrics"""
        with patch('app.services.project_monitoring_service.incremental_indexer', mock_incremental_indexer):
            result = await monitoring_service.get_indexer_metrics()
            
            assert result["status"] == "success"
            assert result["type"] == "indexer_metrics"
            assert result["data"]["metrics"]["incremental_updates"] == 42
            assert "Performance Metrics" in result["data"]["summary"]

    async def test_analyze_impact_success(self, monitoring_service, mock_file_monitor_service):
        """Test successful impact analysis"""
        client_id = "test-client"
        session_id = "test-session"
        file_path = "/test/workspace/important_file.py"
        
        monitoring_service.active_sessions[client_id] = session_id
        
        mock_impact = {
            "direct_dependencies": ["file1.py", "file2.py"],
            "indirect_dependencies": ["file3.py"],
            "risk_level": "medium",
            "potential_issues": ["Breaking change possible"],
            "recommendations": ["Run tests before deploying"]
        }
        
        mock_file_monitor_service.analyze_impact.return_value = mock_impact
        
        with patch('app.services.project_monitoring_service.file_monitor_service', mock_file_monitor_service):
            result = await monitoring_service.analyze_impact(client_id, file_path)
            
            assert result["status"] == "success"
            assert result["type"] == "impact_analysis"
            assert "Direct dependencies: 2" in result["data"]["summary"]
            assert "medium" in result["data"]["summary"]

    async def test_analyze_impact_no_session(self, monitoring_service):
        """Test impact analysis with no active session"""
        result = await monitoring_service.analyze_impact("test-client", "/test/file.py")
        
        assert result["status"] == "error"
        assert "No active monitoring session" in result["message"]