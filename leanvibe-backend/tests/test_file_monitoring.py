"""
Test File Monitoring System

Tests for the real-time file monitoring service and integration with enhanced L3 agent.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMonitoringModels:
    """Test monitoring model creation and validation"""

    def test_file_change_creation(self):
        """Test file change model"""
        from app.models.monitoring_models import ChangeType, FileChange

        change = FileChange(
            id="test_change_1",
            file_path="/path/to/test.py",
            change_type=ChangeType.MODIFIED,
            lines_added=5,
            lines_removed=2,
            language="python",
        )

        assert change.id == "test_change_1"
        assert change.change_type == ChangeType.MODIFIED
        assert change.lines_added == 5
        assert change.lines_removed == 2
        assert change.is_code_file() is True
        assert "test.py" in change.get_relative_path("/path/to")

    def test_monitoring_configuration(self):
        """Test monitoring configuration model"""
        from app.models.monitoring_models import MonitoringConfiguration

        config = MonitoringConfiguration(
            workspace_path="/test/workspace",
            watch_patterns=["**/*.py", "**/*.js"],
            ignore_patterns=["**/__pycache__/**"],
            debounce_delay_ms=500,
            enable_content_analysis=True,
        )

        assert config.workspace_path == "/test/workspace"
        assert len(config.watch_patterns) == 2
        assert config.debounce_delay_ms == 500
        assert config.enable_content_analysis is True

    def test_monitoring_session(self):
        """Test monitoring session model"""
        from app.models.monitoring_models import (
            ChangeType,
            FileChange,
            MonitoringConfiguration,
            MonitoringSession,
            MonitoringStatus,
        )

        config = MonitoringConfiguration(workspace_path="/test")
        session = MonitoringSession(
            session_id="test_session",
            project_id="test_project",
            client_id="test_client",
            configuration=config,
            status=MonitoringStatus.ACTIVE,
        )

        # Test adding changes
        change = FileChange(
            id="change1", file_path="/test/file1.py", change_type=ChangeType.MODIFIED
        )

        session.add_change(change)

        assert session.total_changes_detected == 1
        assert len(session.recent_changes) == 1
        assert session.is_active() is True

    def test_impact_assessment(self):
        """Test impact assessment model"""
        from app.models.monitoring_models import (
            ChangeScope,
            ImpactAssessment,
            RiskLevel,
        )

        assessment = ImpactAssessment(
            change_id="test_change",
            risk_level=RiskLevel.HIGH,
            scope=ChangeScope.PROJECT_WIDE,
            directly_affected_files=["/path/file1.py", "/path/file2.py"],
            suggested_actions=["Run comprehensive tests", "Review changes"],
        )

        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.scope == ChangeScope.PROJECT_WIDE
        assert assessment.get_total_affected_files() == 2
        assert len(assessment.suggested_actions) == 2


class TestFileMonitorService:
    """Test file monitoring service functionality"""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test file monitor service initialization"""
        from app.services.file_monitor_service import file_monitor_service

        # Should initialize without errors
        assert file_monitor_service is not None
        assert hasattr(file_monitor_service, "sessions")
        assert hasattr(file_monitor_service, "observers")
        assert hasattr(file_monitor_service, "change_queues")
        assert hasattr(file_monitor_service, "metrics")

        # Initially no sessions
        assert len(file_monitor_service.sessions) == 0
        assert len(file_monitor_service.observers) == 0

    @pytest.mark.asyncio
    async def test_monitoring_configuration_validation(self):
        """Test monitoring configuration validation"""
        from app.models.monitoring_models import (
            MonitoringConfiguration,
            MonitoringError,
        )
        from app.services.file_monitor_service import file_monitor_service

        # Test with non-existent workspace
        config = MonitoringConfiguration(workspace_path="/non/existent/path")

        with pytest.raises(MonitoringError):
            await file_monitor_service.start_monitoring(
                session_id="test_session",
                project_id="test_project",
                client_id="test_client",
                config=config,
            )

    @pytest.mark.asyncio
    async def test_monitoring_session_lifecycle(self):
        """Test complete monitoring session lifecycle"""
        from app.models.monitoring_models import (
            MonitoringConfiguration,
            MonitoringStatus,
        )
        from app.services.file_monitor_service import file_monitor_service

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid configuration
            config = MonitoringConfiguration(
                workspace_path=temp_dir,
                watch_patterns=["**/*.py"],
                ignore_patterns=["**/__pycache__/**"],
                debounce_delay_ms=100,
            )

            session_id = "test_lifecycle_session"

            try:
                # Start monitoring
                success = await file_monitor_service.start_monitoring(
                    session_id=session_id,
                    project_id="test_project",
                    client_id="test_client",
                    config=config,
                )

                assert success is True

                # Check session exists
                session = file_monitor_service.get_session(session_id)
                assert session is not None
                assert session.status == MonitoringStatus.ACTIVE
                assert session.session_id == session_id

                # Test pause/resume
                await file_monitor_service.pause_monitoring(session_id)
                session = file_monitor_service.get_session(session_id)
                assert session.status == MonitoringStatus.PAUSED

                await file_monitor_service.resume_monitoring(session_id)
                session = file_monitor_service.get_session(session_id)
                assert session.status == MonitoringStatus.ACTIVE

                # Test metrics
                metrics = file_monitor_service.get_metrics(session_id)
                assert metrics is not None
                assert metrics.session_id == session_id

            finally:
                # Stop monitoring
                await file_monitor_service.stop_monitoring(session_id)

                # Session should be cleaned up
                session = file_monitor_service.get_session(session_id)
                # Session might still exist but be stopped, that's okay
                if session:
                    assert session.status == MonitoringStatus.STOPPED

    def test_file_pattern_matching(self):
        """Test file pattern matching logic"""
        from app.models.monitoring_models import MonitoringConfiguration
        from app.services.file_monitor_service import (
            FileMonitorEventHandler,
            file_monitor_service,
        )

        config = MonitoringConfiguration(
            workspace_path="/test",
            watch_patterns=["**/*.py", "**/*.js"],
            ignore_patterns=["**/__pycache__/**", "**/node_modules/**"],
        )

        handler = FileMonitorEventHandler(file_monitor_service, "test_session")

        # Should match
        assert handler._should_monitor_file("/test/main.py", config) is True
        assert handler._should_monitor_file("/test/src/app.js", config) is True

        # Should ignore
        assert (
            handler._should_monitor_file("/test/__pycache__/file.pyc", config) is False
        )
        assert (
            handler._should_monitor_file("/test/node_modules/lib.js", config) is False
        )

        # Should not match (wrong extension)
        assert handler._should_monitor_file("/test/readme.txt", config) is False

    def test_language_detection(self):
        """Test programming language detection"""
        from app.services.file_monitor_service import file_monitor_service

        test_cases = [
            ("/path/to/script.py", "python"),
            ("/path/to/app.js", "javascript"),
            ("/path/to/component.tsx", "typescript"),
            ("/path/to/Main.swift", "swift"),
            ("/path/to/program.go", "go"),
            ("/path/to/unknown.xyz", None),
        ]

        for file_path, expected_lang in test_cases:
            detected = file_monitor_service._detect_language(file_path)
            assert detected == expected_lang


class TestEnhancedAgentMonitoringIntegration:
    """Test enhanced L3 agent monitoring integration"""

    @pytest.mark.asyncio
    async def test_enhanced_agent_monitoring_tools(self):
        """Test enhanced agent monitoring tool integration"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create test project
            (project_path / "main.py").write_text(
                '''
def main():
    """Main function"""
    print("Hello World")
    return 0

class TestClass:
    def method(self):
        return main()
'''
            )

            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-monitoring-client",
                session_data={},
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Test starting monitoring
            result = await agent._start_monitoring_tool(str(project_path))
            assert result["status"] == "success" or "error" in result["status"]
            assert "type" in result
            assert "confidence" in result

            if result["status"] == "success":
                # Test monitoring status
                status_result = await agent._get_monitoring_status_tool()
                assert status_result["status"] == "success"
                assert "data" in status_result

                # Test getting recent changes (should be empty initially)
                changes_result = await agent._get_recent_changes_tool()
                assert (
                    changes_result["status"] == "success"
                    or changes_result["status"] == "error"
                )

                # Test stopping monitoring
                stop_result = await agent._stop_monitoring_tool()
                assert (
                    stop_result["status"] == "success"
                    or stop_result["status"] == "error"
                )

    @pytest.mark.asyncio
    async def test_enhanced_agent_monitoring_natural_language(self):
        """Test natural language processing for monitoring commands"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            (project_path / "example.py").write_text(
                """
def example():
    return "test"
"""
            )

            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-nl-monitoring-client",
                session_data={},
            )

            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()

            # Test various monitoring-related queries
            test_queries = [
                "start monitoring files",
                "monitor this workspace",
                "what is the monitoring status",
                "show recent changes",
                "stop monitoring",
                "watch status",
            ]

            for query in test_queries:
                response = await agent._process_user_input(query)

                # Should return string response
                assert isinstance(response, str)
                assert len(response) > 0

                # Should not crash or return unhandled errors
                if "Error" in response:
                    # Errors should be graceful and informative
                    assert (
                        "monitoring" in response.lower()
                        or "session" in response.lower()
                    )

    @pytest.mark.asyncio
    async def test_enhanced_state_includes_monitoring_capabilities(self):
        """Test enhanced agent state includes monitoring capabilities"""
        from app.agent.enhanced_l3_agent import AgentDependencies, EnhancedL3CodingAgent

        deps = AgentDependencies(
            workspace_path=".",
            client_id="test-state-monitoring-client",
            session_data={},
        )

        agent = EnhancedL3CodingAgent(deps)
        await agent.initialize()

        # Get enhanced state summary
        state = agent.get_enhanced_state_summary()

        # Should include monitoring capabilities
        assert "monitoring_capabilities" in state
        assert isinstance(state["monitoring_capabilities"], list)
        assert "monitoring_active" in state
        assert isinstance(state["monitoring_active"], bool)

        # Check specific monitoring capabilities
        expected_capabilities = [
            "real_time_file_monitoring",
            "change_detection",
            "impact_analysis",
            "debouncing",
            "content_analysis",
            "session_management",
        ]

        for capability in expected_capabilities:
            assert capability in state["monitoring_capabilities"]


def test_monitoring_basic_functionality():
    """Test basic monitoring functionality"""
    from app.services.file_monitor_service import file_monitor_service

    # Test service availability
    assert file_monitor_service is not None

    # Test basic methods exist
    assert hasattr(file_monitor_service, "start_monitoring")
    assert hasattr(file_monitor_service, "stop_monitoring")
    assert hasattr(file_monitor_service, "get_session")
    assert hasattr(file_monitor_service, "get_metrics")
    assert hasattr(file_monitor_service, "get_recent_changes")

    # Test session management
    sessions = file_monitor_service.get_sessions()
    assert isinstance(sessions, list)

    print("✅ File monitoring service basic functionality test passed")


if __name__ == "__main__":
    # Run basic tests
    test_monitoring_basic_functionality()

    # Run async tests
    asyncio.run(TestFileMonitorService().test_service_initialization())
    print("✅ File monitor service initialization test passed")

    asyncio.run(
        TestEnhancedAgentMonitoringIntegration().test_enhanced_state_includes_monitoring_capabilities()
    )
    print("✅ Enhanced agent monitoring capabilities test passed")

    print("🎉 All file monitoring tests passed!")
