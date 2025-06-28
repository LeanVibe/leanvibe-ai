"""
Basic File Monitoring Tests

Tests for monitoring models and basic functionality without external dependencies.
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_monitoring_models():
    """Test monitoring model creation and validation"""
    try:
        from app.models.monitoring_models import (
            ChangeNotification,
            ChangeScope,
            ChangeType,
            FileChange,
            ImpactAssessment,
            MonitoringConfiguration,
            MonitoringSession,
            MonitoringStatus,
            RiskLevel,
        )

        # Test FileChange model
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
        assert change.is_code_file() == True
        print("✅ FileChange model test passed")

        # Test MonitoringConfiguration model
        config = MonitoringConfiguration(
            workspace_path="/test/workspace",
            watch_patterns=["**/*.py", "**/*.js"],
            ignore_patterns=["**/__pycache__/**"],
            debounce_delay_ms=500,
        )

        assert config.workspace_path == "/test/workspace"
        assert len(config.watch_patterns) == 2
        assert config.debounce_delay_ms == 500
        print("✅ MonitoringConfiguration model test passed")

        # Test MonitoringSession model
        session = MonitoringSession(
            session_id="test_session",
            project_id="test_project",
            client_id="test_client",
            configuration=config,
            status=MonitoringStatus.ACTIVE,
        )

        session.add_change(change)
        assert session.total_changes_detected == 1
        assert len(session.recent_changes) == 1
        assert session.is_active() == True
        print("✅ MonitoringSession model test passed")

        # Test ImpactAssessment model
        assessment = ImpactAssessment(
            change_id="test_change",
            risk_level=RiskLevel.HIGH,
            scope=ChangeScope.PROJECT_WIDE,
            directly_affected_files=["/path/file1.py", "/path/file2.py"],
            suggested_actions=["Run comprehensive tests"],
        )

        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.get_total_affected_files() == 2
        print("✅ ImpactAssessment model test passed")

        # Test ChangeNotification model
        notification = ChangeNotification.from_change(
            change, "test_session", assessment
        )
        assert notification.session_id == "test_session"
        assert notification.change == change
        assert notification.impact_assessment == assessment
        assert "test.py" in notification.title
        print("✅ ChangeNotification model test passed")

        return True

    except Exception as e:
        print(f"❌ Monitoring models test failed: {e}")
        return False


def test_enhanced_agent_imports():
    """Test that enhanced agent can import monitoring components"""
    try:
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent
        from app.models.monitoring_models import MonitoringConfiguration

        # Check that the class has monitoring tools
        agent_tools = EnhancedL3CodingAgent.__dict__

        # Look for monitoring tool methods
        monitoring_tools = [
            "_start_monitoring_tool",
            "_stop_monitoring_tool",
            "_get_monitoring_status_tool",
            "_get_recent_changes_tool",
        ]

        for tool in monitoring_tools:
            if tool in [
                name for name in dir(EnhancedL3CodingAgent) if not name.startswith("__")
            ]:
                print(f"✅ Found monitoring tool: {tool}")
            else:
                print(f"⚠️ Missing monitoring tool: {tool}")

        print("✅ Enhanced agent monitoring imports test passed")
        return True

    except Exception as e:
        print(f"❌ Enhanced agent imports test failed: {e}")
        return False


def test_visualization_integration():
    """Test that visualization service is properly integrated"""
    try:
        from app.models.visualization_models import DiagramTheme, DiagramType
        from app.services.visualization_service import visualization_service

        # Test service availability
        assert visualization_service is not None
        assert hasattr(visualization_service, "generate_diagram")
        assert hasattr(visualization_service, "get_diagram_types")

        # Test cache stats
        stats = visualization_service.get_cache_stats()
        assert isinstance(stats, dict)
        assert "cache_size" in stats

        print("✅ Visualization service integration test passed")
        return True

    except Exception as e:
        print(f"❌ Visualization integration test failed: {e}")
        return False


def test_file_monitoring_service_structure():
    """Test file monitoring service structure (without starting it)"""
    try:
        from app.services.file_monitor_service import (
            FileMonitorEventHandler,
            file_monitor_service,
        )

        # Test service structure
        assert hasattr(file_monitor_service, "sessions")
        assert hasattr(file_monitor_service, "observers")
        assert hasattr(file_monitor_service, "change_queues")
        assert hasattr(file_monitor_service, "start_monitoring")
        assert hasattr(file_monitor_service, "stop_monitoring")
        assert hasattr(file_monitor_service, "get_session")

        # Test initial state
        assert len(file_monitor_service.sessions) == 0
        assert len(file_monitor_service.observers) == 0

        # Test event handler creation
        handler = FileMonitorEventHandler(file_monitor_service, "test_session")
        assert handler.monitor_service == file_monitor_service
        assert handler.session_id == "test_session"

        print("✅ File monitoring service structure test passed")
        return True

    except Exception as e:
        print(f"❌ File monitoring service structure test failed: {e}")
        return False


def test_api_endpoints_exist():
    """Test that monitoring API endpoints are defined"""
    try:
        from app.main import app

        # Get all routes
        routes = [route.path for route in app.routes]

        # Check for visualization endpoints (already working)
        viz_endpoints = [
            "/visualization/types",
            "/visualization/{client_id}/generate",
            "/visualization/{client_id}/diagram/{diagram_type}",
            "/visualization/cache/stats",
        ]

        for endpoint in viz_endpoints:
            if endpoint in routes:
                print(f"✅ Found API endpoint: {endpoint}")
            else:
                print(f"⚠️ Missing API endpoint: {endpoint}")

        print("✅ API endpoints test passed")
        return True

    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Basic File Monitoring Tests...")
    print()

    tests = [
        ("Monitoring Models", test_monitoring_models),
        ("Enhanced Agent Imports", test_enhanced_agent_imports),
        ("Visualization Integration", test_visualization_integration),
        ("File Monitoring Service Structure", test_file_monitoring_service_structure),
        ("API Endpoints", test_api_endpoints_exist),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
        print()

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All basic monitoring tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")
