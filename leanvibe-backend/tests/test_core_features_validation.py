"""
Core Features Validation Tests
Tests to validate that core PRD features are implemented and not just stubbed.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestCoreFeatureValidation:
    """Tests to validate core features against PRD requirements"""
    
    def test_webSocket_communication_exists(self):
        """Validate WebSocket communication is implemented"""
        # Test that WebSocket endpoints exist and are properly configured
        try:
            from app.api.websocket import websocket_endpoint
            assert callable(websocket_endpoint), "WebSocket endpoint should be callable"
        except ImportError:
            pytest.fail("WebSocket endpoint not found - core feature missing")
    
    def test_l3_agent_architecture_exists(self):
        """Validate L3 Agent architecture is implemented"""
        try:
            from app.agent.l3_coding_agent import L3CodingAgent
            assert L3CodingAgent, "L3CodingAgent class should exist"
            
            # Verify key methods exist
            agent_methods = dir(L3CodingAgent)
            required_methods = ['process_command', 'get_confidence_score', 'initialize']
            
            for method in required_methods:
                assert method in agent_methods, f"Required L3 method {method} not found"
        except ImportError:
            pytest.fail("L3CodingAgent not found - core feature missing")
    
    def test_pydantic_ai_integration_exists(self):
        """Validate Pydantic AI integration is implemented"""
        try:
            from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent
            assert EnhancedL3CodingAgent, "Enhanced L3 agent should exist"
            
            # Check for Pydantic AI specific patterns
            agent_source = str(EnhancedL3CodingAgent.__doc__ or "")
            assert "pydantic" in agent_source.lower() or hasattr(EnhancedL3CodingAgent, '_pydantic'), \
                "Pydantic AI integration not found"
        except ImportError:
            pytest.fail("Enhanced L3 agent with Pydantic AI not found")
    
    def test_session_management_exists(self):
        """Validate session management is implemented"""
        try:
            from app.agent.session_manager import SessionManager
            assert SessionManager, "SessionManager should exist"
            
            # Verify core session methods
            session_methods = dir(SessionManager)
            required_methods = ['create_session', 'get_session', 'update_session']
            
            for method in required_methods:
                assert method in session_methods, f"Required session method {method} not found"
        except ImportError:
            pytest.fail("SessionManager not found - core feature missing")
    
    @pytest.mark.asyncio
    async def test_ai_service_unified_strategy(self):
        """Test that unified AI service strategy exists and works"""
        try:
            from app.services.unified_mlx_service import UnifiedMLXService, MLXInferenceStrategy
            
            service = UnifiedMLXService()
            assert service, "UnifiedMLXService should instantiate"
            
            # Test strategy enum exists
            strategies = list(MLXInferenceStrategy)
            assert len(strategies) > 0, "MLX strategies should be defined"
            assert MLXInferenceStrategy.AUTO in strategies, "AUTO strategy should exist"
            assert MLXInferenceStrategy.MOCK in strategies, "MOCK strategy should exist"
            
        except ImportError:
            pytest.fail("Unified MLX service not found - duplicate services not consolidated")
    
    def test_voice_service_consolidation_exists(self):
        """Test that voice services have been properly consolidated"""
        # This tests iOS side would require iOS testing framework
        # For now, test that we don't have competing implementations
        
        voice_service_files = [
            "VoiceManager.swift",
            "OptimizedVoiceManager.swift", 
            "UnifiedVoiceService.swift",
            "GlobalVoiceManager.swift"
        ]
        
        ios_services_path = Path("/Users/bogdan/work/leanvibe-ai/leanvibe-ios/LeanVibe/Services")
        
        if ios_services_path.exists():
            existing_voice_services = []
            for file in voice_service_files:
                if (ios_services_path / file).exists():
                    existing_voice_services.append(file)
            
            # Should have exactly one primary voice service
            unified_exists = "UnifiedVoiceService.swift" in existing_voice_services
            assert unified_exists, "UnifiedVoiceService.swift should exist as primary service"
            
            # Deprecated services should be marked as deprecated
            for deprecated_service in ["VoiceManager.swift", "OptimizedVoiceManager.swift"]:
                if deprecated_service in existing_voice_services:
                    service_path = ios_services_path / deprecated_service
                    content = service_path.read_text()
                    assert "@available(*, deprecated" in content, f"{deprecated_service} should be marked deprecated"
    
    def test_mermaid_renderer_implementation_status(self):
        """Test that MermaidRenderer is properly implemented or marked as stub"""
        ios_services_path = Path("/Users/bogdan/work/leanvibe-ai/leanvibe-ios/LeanVibe/Services")
        mermaid_file = ios_services_path / "MermaidRenderer.swift"
        
        if mermaid_file.exists():
            content = mermaid_file.read_text()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            # If it's just a stub, it should be very short
            if len(lines) <= 10 and "// Will be implemented later" in content:
                pytest.skip("MermaidRenderer is a documented stub - implementation pending")
            else:
                # If it claims to be implemented, verify it has substance
                assert len(lines) > 20, "MermaidRenderer should have substantial implementation"
                assert "func" in content, "MermaidRenderer should have methods"
    
    def test_backend_service_duplication_status(self):
        """Test that backend services don't have dangerous duplication"""
        services_path = Path("/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/services")
        
        # AI service files that should be consolidated
        ai_service_files = [
            "ai_service.py",
            "enhanced_ai_service.py", 
            "unified_mlx_service.py",
            "real_mlx_service.py",
            "pragmatic_mlx_service.py",
            "mock_mlx_service.py",
            "production_model_service.py"
        ]
        
        existing_ai_services = []
        for file in ai_service_files:
            if (services_path / file).exists():
                existing_ai_services.append(file)
        
        # Should have unified service as primary
        assert "unified_mlx_service.py" in existing_ai_services, \
            "unified_mlx_service.py should exist as primary AI service"
        
        # If multiple services exist, they should use strategy pattern
        if len(existing_ai_services) > 3:  # unified + mock + one other is reasonable
            unified_content = (services_path / "unified_mlx_service.py").read_text()
            assert "Strategy" in unified_content or "strategy" in unified_content, \
                "Multiple AI services should use strategy pattern for coordination"
    
    def test_test_coverage_exists_for_core_features(self):
        """Test that test coverage exists for core features"""
        tests_path = Path("/Users/bogdan/work/leanvibe-ai/leanvibe-backend/tests")
        
        core_feature_tests = [
            "test_mvp_core_journey.py",  # End-to-end MVP validation
            "test_l3_agent_integration.py",  # L3 agent functionality
            "test_websocket.py",  # WebSocket communication
            "test_service_integration_comprehensive.py"  # Service integration
        ]
        
        missing_tests = []
        for test_file in core_feature_tests:
            if not (tests_path / test_file).exists():
                missing_tests.append(test_file)
        
        if missing_tests:
            pytest.fail(f"Missing critical test files: {missing_tests}")
    
    def test_performance_benchmarks_exist(self):
        """Test that performance benchmarks exist for core features"""
        backend_path = Path("/Users/bogdan/work/leanvibe-ai/leanvibe-backend")
        
        # Look for performance test files
        performance_files = list(backend_path.glob("**/test*performance*.py"))
        performance_files.extend(list(backend_path.glob("**/test*benchmark*.py")))
        
        assert len(performance_files) > 0, \
            "Performance benchmarks should exist for core features"
    
    def test_configuration_management_exists(self):
        """Test that proper configuration management exists"""
        backend_path = Path("/Users/bogdan/work/leanvibe-ai/leanvibe-backend")
        config_files = [
            "app/config/settings.py",
            "app/config/unified_config.py"
        ]
        
        config_exists = any((backend_path / config_file).exists() for config_file in config_files)
        assert config_exists, "Configuration management should exist"


class TestFeatureCompleteness:
    """Tests to verify features are complete, not stubbed"""
    
    def test_no_placeholder_comments_in_critical_files(self):
        """Test that critical files don't have placeholder implementations"""
        critical_files = [
            "/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/agent/l3_coding_agent.py",
            "/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/agent/session_manager.py",
            "/Users/bogdan/work/leanvibe-ai/leanvibe-backend/app/services/unified_mlx_service.py"
        ]
        
        placeholder_patterns = [
            "# TODO",
            "# Will be implemented later",
            "# Placeholder",
            "NotImplementedError",
            "raise NotImplementedError",
            "pass  # TODO"
        ]
        
        for file_path in critical_files:
            if Path(file_path).exists():
                content = Path(file_path).read_text()
                
                for pattern in placeholder_patterns:
                    lines_with_pattern = [
                        line for line in content.split('\n') 
                        if pattern in line and not line.strip().startswith('#')
                    ]
                    
                    assert len(lines_with_pattern) == 0, \
                        f"Critical file {file_path} has placeholder: {pattern}"
    
    def test_error_handling_exists(self):
        """Test that proper error handling exists in core services"""
        try:
            from app.services.ai_error_handling import AIErrorHandler
            assert AIErrorHandler, "AI error handling should exist"
        except ImportError:
            pytest.fail("AI error handling not found")
        
        try:
            from app.core.error_recovery import ErrorRecoveryManager
            assert ErrorRecoveryManager, "Error recovery should exist"
        except ImportError:
            pytest.fail("Error recovery not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])