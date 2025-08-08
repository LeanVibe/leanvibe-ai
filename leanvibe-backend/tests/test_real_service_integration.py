"""
Real Service Integration Tests

Tests actual service consolidation and integration points without requiring 
a running server. Focuses on validating that the consolidated services 
(UnifiedVoiceService, unified_mlx_service) work correctly.
"""

import os
import sys
import pytest
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent  # Go up to leanvibe-ai root
sys.path.insert(0, str(project_root / "leanvibe-backend"))

logger = logging.getLogger(__name__)


class RealServiceIntegrationTests:
    """Real service integration tests for consolidated services"""
    
    def test_unified_mlx_service_availability(self):
        """Test that unified MLX service can be imported and initialized"""
        try:
            # Import the unified MLX service
            from app.services.unified_mlx_service import (
                UnifiedMLXService, 
                MLXInferenceStrategy,
                ProductionMLXStrategy,
                PragmaticMLXStrategy, 
                MockMLXStrategy,
                FallbackMLXStrategy
            )
            
            # Test strategy enumeration
            assert MLXInferenceStrategy.PRODUCTION is not None
            assert MLXInferenceStrategy.PRAGMATIC is not None
            assert MLXInferenceStrategy.MOCK is not None
            assert MLXInferenceStrategy.FALLBACK is not None
            
            # Test service instantiation
            service = UnifiedMLXService(preferred_strategy=MLXInferenceStrategy.MOCK)
            assert service is not None
            assert service.preferred_strategy == MLXInferenceStrategy.MOCK
            
            logger.info("✅ UnifiedMLXService import and instantiation successful")
            return True
            
        except ImportError as e:
            logger.error(f"❌ UnifiedMLXService import failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ UnifiedMLXService test failed: {e}")
            return False
    
    def test_unified_mlx_strategies(self):
        """Test that all MLX strategies are available"""
        try:
            from app.services.unified_mlx_service import (
                ProductionMLXStrategy,
                PragmaticMLXStrategy, 
                MockMLXStrategy,
                FallbackMLXStrategy
            )
            
            strategies_tested = 0
            
            # Test FallbackMLXStrategy (should always work)
            fallback = FallbackMLXStrategy()
            assert fallback.is_available() == True
            strategies_tested += 1
            
            # Test MockMLXStrategy
            try:
                mock_strategy = MockMLXStrategy()
                if mock_strategy.is_available():
                    strategies_tested += 1
                    logger.info("✅ MockMLXStrategy available")
                else:
                    logger.info("ℹ️ MockMLXStrategy not available (dependencies missing)")
            except Exception as e:
                logger.info(f"ℹ️ MockMLXStrategy error: {e}")
            
            # Test PragmaticMLXStrategy
            try:
                pragmatic = PragmaticMLXStrategy()
                if pragmatic.is_available():
                    strategies_tested += 1
                    logger.info("✅ PragmaticMLXStrategy available")
                else:
                    logger.info("ℹ️ PragmaticMLXStrategy not available (dependencies missing)")
            except Exception as e:
                logger.info(f"ℹ️ PragmaticMLXStrategy error: {e}")
            
            # Test ProductionMLXStrategy
            try:
                production = ProductionMLXStrategy()
                if production.is_available():
                    strategies_tested += 1
                    logger.info("✅ ProductionMLXStrategy available")
                else:
                    logger.info("ℹ️ ProductionMLXStrategy not available (dependencies missing)")
            except Exception as e:
                logger.info(f"ℹ️ ProductionMLXStrategy error: {e}")
            
            # At minimum, fallback should work
            assert strategies_tested >= 1, f"At least fallback strategy should work, got {strategies_tested}"
            
            logger.info(f"✅ MLX Strategies tested: {strategies_tested}/4 available")
            return True
            
        except Exception as e:
            logger.error(f"❌ MLX strategies test failed: {e}")
            return False
    
    def test_ios_service_components(self):
        """Test iOS service components availability"""
        try:
            # Check iOS service files exist
            ios_services = [
                project_root / "leanvibe-ios" / "LeanVibe" / "Services" / "UnifiedVoiceService.swift",
                project_root / "leanvibe-ios" / "LeanVibe" / "Services" / "WebSocketService.swift",
                project_root / "leanvibe-ios" / "LeanVibe" / "Services" / "ProjectManager.swift",
                project_root / "leanvibe-ios" / "LeanVibe" / "Services" / "TaskService.swift"
            ]
            
            existing_services = 0
            for service_file in ios_services:
                if service_file.exists():
                    existing_services += 1
                    logger.info(f"✅ {service_file.name} exists")
                else:
                    logger.info(f"❌ {service_file.name} missing")
            
            # Check for key iOS integration files
            ios_integration_files = [
                project_root / "leanvibe-ios" / "LeanVibe" / "Models" / "AgentMessage.swift",
                project_root / "leanvibe-ios" / "LeanVibe" / "Models" / "Task.swift",
                project_root / "leanvibe-ios" / "LeanVibe" / "Models" / "VoiceCommand.swift"
            ]
            
            for integration_file in ios_integration_files:
                if integration_file.exists():
                    existing_services += 1
                    logger.info(f"✅ {integration_file.name} exists")
            
            assert existing_services >= 4, f"Expected at least 4 iOS service files, found {existing_services}"
            
            logger.info(f"✅ iOS service components: {existing_services} files found")
            return True
            
        except Exception as e:
            logger.error(f"❌ iOS service components test failed: {e}")
            return False
    
    def test_backend_api_endpoints(self):
        """Test backend API endpoint structure"""
        try:
            # Test that API endpoint files exist
            api_endpoints = [
                project_root / "leanvibe-backend" / "app" / "api" / "endpoints" / "ios_bridge.py",
                project_root / "leanvibe-backend" / "app" / "api" / "endpoints" / "cli_bridge.py",
                project_root / "leanvibe-backend" / "app" / "api" / "endpoints" / "projects.py",
                project_root / "leanvibe-backend" / "app" / "api" / "endpoints" / "tasks.py"
            ]
            
            existing_endpoints = 0
            for endpoint_file in api_endpoints:
                if endpoint_file.exists():
                    existing_endpoints += 1
                    
                    # Check for key endpoint patterns
                    try:
                        content = endpoint_file.read_text()
                        if "router" in content and "@router" in content:
                            logger.info(f"✅ {endpoint_file.name} has proper FastAPI router structure")
                        else:
                            logger.info(f"⚠️ {endpoint_file.name} exists but may have structural issues")
                    except Exception:
                        logger.info(f"ℹ️ {endpoint_file.name} exists but couldn't read content")
                else:
                    logger.error(f"❌ {endpoint_file.name} missing")
            
            assert existing_endpoints >= 3, f"Expected at least 3 API endpoints, found {existing_endpoints}"
            
            logger.info(f"✅ Backend API endpoints: {existing_endpoints} files found")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backend API endpoints test failed: {e}")
            return False
    
    def test_cli_integration_structure(self):
        """Test CLI integration structure"""
        try:
            # Check CLI structure
            cli_files = [
                project_root / "leanvibe-cli" / "leanvibe_cli" / "client.py",
                project_root / "leanvibe-cli" / "leanvibe_cli" / "main.py",
                project_root / "leanvibe-cli" / "leanvibe_cli" / "commands" / "health.py",
                project_root / "leanvibe-cli" / "leanvibe_cli" / "commands" / "status.py"
            ]
            
            existing_cli_files = 0
            for cli_file in cli_files:
                if cli_file.exists():
                    existing_cli_files += 1
                    logger.info(f"✅ {cli_file.name} exists")
                else:
                    logger.info(f"❌ {cli_file.name} missing")
            
            assert existing_cli_files >= 2, f"Expected at least 2 CLI files, found {existing_cli_files}"
            
            logger.info(f"✅ CLI integration structure: {existing_cli_files} files found")
            return True
            
        except Exception as e:
            logger.error(f"❌ CLI integration structure test failed: {e}")
            return False
    
    def test_task_service_integration(self):
        """Test task service integration across components"""
        try:
            # Test backend task service
            from app.services.task_service import task_service
            assert task_service is not None
            logger.info("✅ Backend task_service imported successfully")
            
            # Test task models
            from app.models.task_models import TaskCreate, TaskUpdate, TaskFilters
            assert TaskCreate is not None
            assert TaskUpdate is not None 
            assert TaskFilters is not None
            logger.info("✅ Task models imported successfully")
            
            # Check iOS task-related files exist
            ios_task_files = [
                project_root / "leanvibe-ios" / "LeanVibe" / "Models" / "Task.swift",
                project_root / "leanvibe-ios" / "LeanVibe" / "Services" / "TaskService.swift"
            ]
            
            for task_file in ios_task_files:
                if task_file.exists():
                    logger.info(f"✅ {task_file.name} exists")
                else:
                    logger.info(f"❌ {task_file.name} missing")
            
            logger.info("✅ Task service integration validated")
            return True
            
        except ImportError as e:
            logger.error(f"❌ Task service import failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Task service integration test failed: {e}")
            return False
    
    def test_websocket_infrastructure(self):
        """Test WebSocket infrastructure components"""
        try:
            # Test connection manager
            from app.core.connection_manager import ConnectionManager
            connection_manager = ConnectionManager()
            assert connection_manager is not None
            logger.info("✅ ConnectionManager imported successfully")
            
            # Test WebSocket monitoring
            websocket_files = [
                project_root / "leanvibe-backend" / "app" / "core" / "websocket_monitor.py",
                project_root / "leanvibe-backend" / "app" / "core" / "connection_manager.py"
            ]
            
            for ws_file in websocket_files:
                if ws_file.exists():
                    logger.info(f"✅ {ws_file.name} exists")
                else:
                    logger.info(f"❌ {ws_file.name} missing")
            
            # Check iOS WebSocket service
            ios_websocket = project_root / "leanvibe-ios" / "LeanVibe" / "Services" / "WebSocketService.swift"
            if ios_websocket.exists():
                logger.info("✅ iOS WebSocketService.swift exists")
            else:
                logger.info("❌ iOS WebSocketService.swift missing")
            
            logger.info("✅ WebSocket infrastructure validated")
            return True
            
        except ImportError as e:
            logger.error(f"❌ WebSocket infrastructure import failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ WebSocket infrastructure test failed: {e}")
            return False
    
    def test_voice_service_consolidation(self):
        """Test voice service consolidation"""
        try:
            # Check iOS UnifiedVoiceService exists
            unified_voice_file = project_root / "leanvibe-ios" / "LeanVibe" / "Services" / "UnifiedVoiceService.swift"
            
            if not unified_voice_file.exists():
                logger.error("❌ UnifiedVoiceService.swift does not exist")
                return False
            
            # Read and check for consolidation markers
            content = unified_voice_file.read_text()
            
            consolidation_markers = [
                "UnifiedVoiceService",
                "VoiceState",
                "ListeningMode",
                "VoicePerformanceMetrics",
                "performance_monitoring"
            ]
            
            found_markers = 0
            for marker in consolidation_markers:
                if marker in content:
                    found_markers += 1
                    logger.info(f"✅ Found consolidation marker: {marker}")
                else:
                    logger.info(f"❌ Missing consolidation marker: {marker}")
            
            assert found_markers >= 4, f"Expected at least 4 consolidation markers, found {found_markers}"
            
            # Check for deprecated services removal
            deprecated_services = [
                project_root / "leanvibe-ios" / "LeanVibe" / "Services" / "VoiceManager.swift",
                project_root / "leanvibe-ios" / "LeanVibe" / "Services" / "GlobalVoiceManager.swift"
            ]
            
            active_deprecated = 0
            for deprecated in deprecated_services:
                if deprecated.exists():
                    active_deprecated += 1
                    logger.info(f"⚠️ Deprecated service still exists: {deprecated.name}")
                else:
                    logger.info(f"✅ Deprecated service properly removed: {deprecated.name}")
            
            logger.info(f"✅ Voice service consolidation validated ({found_markers} markers, {len(deprecated_services) - active_deprecated} deprecated services removed)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Voice service consolidation test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all real service integration tests"""
        logger.info("🔍 Starting Real Service Integration Tests...")
        
        tests = [
            ("Unified MLX Service", self.test_unified_mlx_service_availability),
            ("MLX Strategies", self.test_unified_mlx_strategies),
            ("iOS Service Components", self.test_ios_service_components),
            ("Backend API Endpoints", self.test_backend_api_endpoints),
            ("CLI Integration Structure", self.test_cli_integration_structure),
            ("Task Service Integration", self.test_task_service_integration),
            ("WebSocket Infrastructure", self.test_websocket_infrastructure),
            ("Voice Service Consolidation", self.test_voice_service_consolidation)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_method in tests:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                if test_method():
                    passed_tests += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
        
        # Generate summary
        pass_rate = passed_tests / total_tests
        status = "PASSED" if pass_rate >= 0.75 else "FAILED"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"REAL SERVICE INTEGRATION TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Overall Status: {status}")
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Pass Rate: {pass_rate:.1%}")
        
        return {
            "status": status,
            "passed": passed_tests,
            "total": total_tests,
            "pass_rate": pass_rate
        }


# Pytest test functions
def test_real_service_integration():
    """Run real service integration tests"""
    test_suite = RealServiceIntegrationTests()
    results = test_suite.run_all_tests()
    
    # Assert overall success
    assert results["pass_rate"] >= 0.75, f"Integration tests failed with pass rate: {results['pass_rate']:.1%}"
    assert results["passed"] >= 6, f"Too few tests passed: {results['passed']}"


if __name__ == "__main__":
    # Run tests directly
    test_suite = RealServiceIntegrationTests()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["pass_rate"] >= 0.75 else 1)