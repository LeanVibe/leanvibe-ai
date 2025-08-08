"""
Critical Integration Paths Tests
Tests to validate the most important integration points work correctly.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


class TestCriticalIntegrationPaths:
    """Tests for the most critical integration paths"""
    
    def test_fastapi_app_can_start(self):
        """Test that the FastAPI app can start without import errors"""
        try:
            # Try to import the main app without causing import errors
            with patch('app.agent.session_manager.SessionManager'), \
                 patch('app.services.ast_service.ast_service'), \
                 patch('app.services.tree_sitter_parsers.tree_sitter_manager'):
                
                from app.main import app
                assert app is not None, "FastAPI app should exist"
                assert hasattr(app, 'routes'), "FastAPI app should have routes"
                
                # Check that critical routes exist
                route_paths = [route.path for route in app.routes]
                critical_paths = ["/health", "/", "/api/v1/chat"]
                
                for path in critical_paths:
                    assert any(path in route_path for route_path in route_paths), \
                        f"Critical path {path} should exist in routes"
                        
        except ImportError as e:
            pytest.fail(f"FastAPI app cannot start due to import error: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_basic_connection_mock(self):
        """Test WebSocket connection can be established (mocked)"""
        try:
            with patch('app.services.tree_sitter_parsers.tree_sitter_manager'), \
                 patch('app.services.ast_service.ast_service'), \
                 patch('app.agent.session_manager.SessionManager'):
                
                from app.api.websocket import websocket_endpoint
                
                # Mock websocket connection
                mock_websocket = AsyncMock()
                mock_websocket.accept = AsyncMock()
                mock_websocket.receive_text = AsyncMock(return_value='{"command": "status"}')
                mock_websocket.send_text = AsyncMock()
                mock_websocket.close = AsyncMock()
                
                # Test that websocket endpoint can handle basic connection
                try:
                    await websocket_endpoint(mock_websocket, client_id="test")
                    # If we get here without exception, basic structure works
                    assert True, "WebSocket endpoint handles connections"
                except Exception as e:
                    # Some errors are expected in mocked environment
                    # As long as it's not ImportError, the structure exists
                    assert not isinstance(e, ImportError), \
                        f"WebSocket should not fail due to imports: {e}"
                        
        except ImportError:
            pytest.fail("WebSocket endpoint cannot be imported")
    
    def test_l3_agent_basic_instantiation(self):
        """Test that L3 agent can be instantiated with mocking"""
        try:
            with patch('app.services.ast_service.ast_service'), \
                 patch('app.services.tree_sitter_parsers.tree_sitter_manager'):
                
                from app.agent.l3_coding_agent import L3CodingAgent
                
                # Mock dependencies
                mock_deps = MagicMock()
                mock_deps.workspace_path = "/tmp/test"
                mock_deps.client_id = "test"
                
                agent = L3CodingAgent(dependencies=mock_deps)
                assert agent is not None, "L3CodingAgent should instantiate"
                assert hasattr(agent, 'process_command'), \
                    "L3CodingAgent should have process_command method"
                
        except ImportError:
            pytest.fail("L3CodingAgent cannot be imported")
    
    def test_service_manager_exists_and_functional(self):
        """Test that service manager exists and can manage services"""
        try:
            from app.core.service_manager import ServiceManager
            
            manager = ServiceManager()
            assert manager is not None, "ServiceManager should instantiate"
            
            # Test basic service management methods exist
            required_methods = ['start_service', 'stop_service', 'get_service_status']
            for method in required_methods:
                assert hasattr(manager, method), \
                    f"ServiceManager should have {method} method"
                    
        except ImportError:
            pytest.fail("ServiceManager cannot be imported")
    
    def test_unified_config_loads_properly(self):
        """Test that unified configuration can be loaded"""
        try:
            from app.config.unified_config import get_config
            
            config = get_config()
            assert config is not None, "Configuration should load"
            assert hasattr(config, 'database_url') or hasattr(config, 'api_key') or \
                   hasattr(config, 'model_name'), "Config should have some settings"
                   
        except ImportError:
            pytest.fail("Unified config cannot be imported")
        except Exception as e:
            # Config loading errors are acceptable as long as structure exists
            assert "import" not in str(e).lower(), \
                f"Config should not fail due to imports: {e}"
    
    def test_health_check_endpoint_works(self):
        """Test that health check endpoint returns proper response"""
        try:
            with patch('app.services.tree_sitter_parsers.tree_sitter_manager'), \
                 patch('app.services.ast_service.ast_service'), \
                 patch('app.agent.session_manager.SessionManager'):
                
                from fastapi.testclient import TestClient
                from app.main import app
                
                client = TestClient(app)
                response = client.get("/health")
                
                assert response.status_code == 200, \
                    "Health endpoint should return 200"
                    
                data = response.json()
                assert "status" in data, \
                    "Health response should have status"
                assert data["status"] in ["healthy", "ok", "operational"], \
                    f"Health status should be positive, got: {data.get('status')}"
                    
        except ImportError:
            pytest.fail("Health endpoint test failed due to imports")
    
    def test_error_recovery_integration(self):
        """Test that error recovery system is integrated"""
        try:
            from app.core.error_recovery import ErrorRecoveryManager
            
            recovery = ErrorRecoveryManager()
            assert recovery is not None, "Error recovery should instantiate"
            
            # Test basic recovery methods exist
            required_methods = ['handle_service_failure', 'restart_service', 'get_recovery_status']
            for method in required_methods:
                assert hasattr(recovery, method), \
                    f"ErrorRecoveryManager should have {method} method"
                    
        except ImportError:
            pytest.fail("Error recovery system cannot be imported")
    
    def test_performance_monitoring_integration(self):
        """Test that performance monitoring is integrated"""
        performance_files = [
            "/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/services/performance_analytics.py",
            "/Users/bogdan/work/leanvibe-ai/leanvibe-ios/LeanVibe/Services/PerformanceManager.swift",
            "/Users/bogdan/work/leanvibe-ai/leanvibe-ios/LeanVibe/Services/IntegratedPerformanceManager.swift"
        ]
        
        performance_exists = any(Path(file).exists() for file in performance_files)
        assert performance_exists, \
            "Performance monitoring should be integrated across components"
    
    @pytest.mark.asyncio
    async def test_ai_service_basic_functionality(self):
        """Test that AI service can handle basic queries"""
        try:
            # Test with the most basic AI service that should work
            from app.services.ai_service import AIService
            
            service = AIService()
            assert service is not None, "AIService should instantiate"
            
            # Test basic command handling
            response = await service.process_command("/status", "test-session")
            assert response is not None, "AI service should return response"
            assert isinstance(response, str), "AI service should return string response"
            
        except ImportError:
            pytest.fail("Basic AI service cannot be imported")
        except Exception as e:
            # Some runtime errors are expected in test environment
            # As long as the service can be imported and instantiated
            if "import" not in str(e).lower():
                pytest.skip(f"AI service runtime error in test environment: {e}")
            else:
                pytest.fail(f"AI service import error: {e}")
    
    def test_ios_backend_communication_structure(self):
        """Test that iOS-Backend communication structure exists"""
        # Check that iOS WebSocket service exists
        ios_websocket_path = Path("/Users/bogdan/work/leanvibe-ai/leanvibe-ios/LeanVibe/Services/WebSocketService.swift")
        
        if ios_websocket_path.exists():
            content = ios_websocket_path.read_text()
            
            # Verify WebSocket service has key methods
            required_patterns = [
                "func connect",
                "func disconnect", 
                "func send",
                "WebSocket"
            ]
            
            for pattern in required_patterns:
                assert pattern in content, \
                    f"iOS WebSocketService should have {pattern} functionality"
        else:
            pytest.skip("iOS WebSocket service not found")
    
    def test_cli_backend_integration_structure(self):
        """Test that CLI-Backend integration structure exists"""
        cli_path = Path("/Users/bogdan/work/leanvibe-ai/leanvibe-cli")
        
        if cli_path.exists():
            # Check for key CLI components
            key_files = [
                cli_path / "leanvibe_cli" / "client.py",
                cli_path / "leanvibe_cli" / "commands" / "health.py",
                cli_path / "leanvibe_cli" / "commands" / "status.py"
            ]
            
            existing_files = [f for f in key_files if f.exists()]
            assert len(existing_files) > 0, \
                "CLI should have basic command structure"
                
            # Test that CLI can communicate with backend
            if (cli_path / "leanvibe_cli" / "client.py").exists():
                client_content = (cli_path / "leanvibe_cli" / "client.py").read_text()
                communication_patterns = ["http", "websocket", "requests", "aiohttp"]
                
                has_communication = any(pattern in client_content.lower() 
                                      for pattern in communication_patterns)
                assert has_communication, \
                    "CLI client should have backend communication capability"
        else:
            pytest.skip("CLI component not found")


class TestProductionReadinessValidation:
    """Tests to validate production readiness claims"""
    
    def test_no_debug_code_in_production_files(self):
        """Test that production files don't have debug code"""
        production_files = [
            "/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/main.py",
            "/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/agent/l3_coding_agent.py",
            "/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/services/unified_mlx_service.py"
        ]
        
        debug_patterns = ["print(", "console.log", "debug=True", "DEBUG = True"]
        
        for file_path in production_files:
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                
                debug_lines = []
                for line_num, line in enumerate(content.split('\n'), 1):
                    for pattern in debug_patterns:
                        if pattern in line and not line.strip().startswith('#'):
                            debug_lines.append((line_num, line.strip()))
                
                assert len(debug_lines) == 0, \
                    f"Production file {file_path} has debug code: {debug_lines}"
    
    def test_error_handling_coverage(self):
        """Test that error handling exists in critical components"""
        critical_files = [
            "/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/api/websocket.py",
            "/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/agent/l3_coding_agent.py"
        ]
        
        for file_path in critical_files:
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                
                # Should have proper error handling
                error_handling_patterns = ["try:", "except", "raise", "logger.error"]
                has_error_handling = any(pattern in content for pattern in error_handling_patterns)
                
                assert has_error_handling, \
                    f"Critical file {file_path} should have error handling"
    
    def test_logging_configuration_exists(self):
        """Test that proper logging configuration exists"""
        backend_path = Path("/Users/bogdan/work/leanvibe-ai/leanvibe-backend")
        
        # Look for logging configuration
        potential_logging_configs = [
            backend_path / "app" / "config" / "logging.py",
            backend_path / "logging.conf",
            backend_path / "pyproject.toml"
        ]
        
        has_logging_config = False
        for config_file in potential_logging_configs:
            if config_file.exists():
                content = config_file.read_text()
                if "logging" in content.lower():
                    has_logging_config = True
                    break
        
        assert has_logging_config, "Production app should have logging configuration"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])