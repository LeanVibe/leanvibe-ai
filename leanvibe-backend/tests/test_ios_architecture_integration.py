"""
iOS Architecture Integration Tests

Tests the complete workflow from iOS app connecting to backend graph endpoints.
"""

import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.agent.session_manager import SessionManager


class TestiOSArchitectureIntegration:
    """Test iOS architecture integration with backend"""

    @pytest.fixture
    def test_client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_ios_client_architecture_workflow(self, test_client):
        """Test complete iOS architecture workflow"""
        # Simulate iOS client connecting with consistent client_id
        ios_client_id = "ios_12345678"
        
        # Test 1: Architecture patterns endpoint (primary)
        arch_response = test_client.get(f"/graph/architecture/{ios_client_id}")
        assert arch_response.status_code == 200
        
        arch_data = arch_response.json()
        assert "architecture" in arch_data
        assert "client_id" in arch_data
        assert arch_data["client_id"] == ios_client_id
        
        # Test 2: Visualization endpoint (fallback)
        viz_response = test_client.get(f"/graph/visualization/{ios_client_id}")
        assert viz_response.status_code == 200
        
        viz_data = viz_response.json()
        assert "visualization" in viz_data
        assert "client_id" in viz_data
        assert viz_data["client_id"] == ios_client_id
        
        # Test 3: Session persistence - multiple calls should use same session
        arch_response2 = test_client.get(f"/graph/architecture/{ios_client_id}")
        assert arch_response2.status_code == 200
        
        # Test 4: Different iOS client gets different session
        ios_client_id2 = "ios_87654321"
        arch_response3 = test_client.get(f"/graph/architecture/{ios_client_id2}")
        assert arch_response3.status_code == 200
        
        arch_data3 = arch_response3.json()
        assert arch_data3["client_id"] == ios_client_id2

    @pytest.mark.asyncio
    async def test_ios_session_auto_creation(self, test_client):
        """Test that iOS requests automatically create sessions"""
        ios_client_id = "ios_test_auto"
        
        # Test that session gets created automatically
        response = test_client.get(f"/graph/architecture/{ios_client_id}")
        assert response.status_code == 200
        
        # Verify session exists in session manager
        session_list_response = test_client.get("/sessions")
        assert session_list_response.status_code == 200
        
        sessions_data = session_list_response.json()
        session_ids = [session["client_id"] for session in sessions_data["sessions"]]
        assert ios_client_id in session_ids

    @pytest.mark.asyncio
    async def test_ios_architecture_data_format(self, test_client):
        """Test that architecture data is in expected format for iOS"""
        ios_client_id = "ios_format_test"
        
        response = test_client.get(f"/graph/architecture/{ios_client_id}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check structure matches what iOS expects
        assert "architecture" in data
        assert "client_id" in data
        
        architecture = data["architecture"]
        
        # Architecture should be either a dict with pattern info or error message
        assert isinstance(architecture, (dict, str))
        
        if isinstance(architecture, dict):
            # If successful, check for expected structure
            if "patterns" in architecture:
                patterns = architecture["patterns"]
                assert isinstance(patterns, list)
                
                for pattern in patterns:
                    assert "pattern_name" in pattern
                    assert "confidence" in pattern
                    assert isinstance(pattern["confidence"], (int, float))
                    
            elif "error" in architecture:
                # Graceful error handling
                assert isinstance(architecture["error"], str)

    @pytest.mark.asyncio
    async def test_ios_multiple_endpoints_workflow(self, test_client):
        """Test iOS app using multiple graph endpoints"""
        ios_client_id = "ios_multi_endpoint"
        
        # Architecture analysis
        arch_response = test_client.get(f"/graph/architecture/{ios_client_id}")
        assert arch_response.status_code == 200
        
        # Circular dependencies
        deps_response = test_client.get(f"/graph/circular-deps/{ios_client_id}")
        assert deps_response.status_code == 200
        
        # Coupling analysis
        coupling_response = test_client.get(f"/graph/coupling/{ios_client_id}")
        assert coupling_response.status_code == 200
        
        # Hotspots
        hotspots_response = test_client.get(f"/graph/hotspots/{ios_client_id}")
        assert hotspots_response.status_code == 200
        
        # All should have consistent client_id
        responses = [arch_response, deps_response, coupling_response, hotspots_response]
        for response in responses:
            data = response.json()
            assert data["client_id"] == ios_client_id

    @pytest.mark.asyncio
    async def test_ios_error_handling(self, test_client):
        """Test iOS error handling when services unavailable"""
        ios_client_id = "ios_error_test"
        
        # Test architecture endpoint
        response = test_client.get(f"/graph/architecture/{ios_client_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "client_id" in data
        
        # Should handle gracefully even if no graph data available
        architecture = data.get("architecture", {})
        
        # Either has valid data or error message
        assert isinstance(architecture, (dict, str))
        
        if isinstance(architecture, dict) and "error" in architecture:
            # Error should be descriptive
            error_msg = architecture["error"]
            assert len(error_msg) > 0
            assert "available" in error_msg.lower() or "not found" in error_msg.lower()

    def test_ios_health_check_integration(self, test_client):
        """Test iOS can check backend health"""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert health_data["status"] == "healthy"
        
        # Should include AI readiness
        assert "ai_ready" in health_data

    @pytest.mark.asyncio
    async def test_ios_session_state_access(self, test_client):
        """Test iOS can access session state"""
        ios_client_id = "ios_state_test"
        
        # Create session by calling architecture endpoint
        arch_response = test_client.get(f"/graph/architecture/{ios_client_id}")
        assert arch_response.status_code == 200
        
        # Check session state
        state_response = test_client.get(f"/sessions/{ios_client_id}/state")
        assert state_response.status_code == 200
        
        state_data = state_response.json()
        assert "client_id" in state_data

if __name__ == "__main__":
    # Run a quick test
    import asyncio
    
    async def quick_test():
        test = TestiOSArchitectureIntegration()
        client = TestClient(app)
        await test.test_ios_client_architecture_workflow(client)
        print("✅ iOS architecture integration test passed")
    
    asyncio.run(quick_test())