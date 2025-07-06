"""
Tests for the simplified Service Manager

Validates that the service manager correctly initializes, manages,
and provides access to core LeanVibe services.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.service_manager import ServiceManager, service_manager
from app.core.service_manager import get_ai_service, get_vector_service, get_graph_service
from app.core.service_manager import initialize_backend, shutdown_backend

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestServiceManager:
    """Test suite for the simplified service manager"""
    
    async def test_service_manager_initialization(self):
        """Test that service manager initializes correctly"""
        manager = ServiceManager()
        
        # Test initial state
        assert not manager.initialized
        assert len(manager.services) == 0
        assert len(manager.service_status) == 0
        
        # Test initialization
        results = await manager.initialize_all_services()
        
        # Validate results
        assert isinstance(results, dict)
        assert manager.initialized
        
        # Check core services
        expected_services = ['graph', 'vector', 'ai', 'project', 'monitor']
        for service_name in expected_services:
            assert service_name in results
            assert isinstance(results[service_name], bool)
        
        # At least vector and AI should be attempted
        assert 'vector' in manager.service_status
        assert 'ai' in manager.service_status
        
        print(f"\n📊 Service Initialization Results:")
        for service, status in results.items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {service}: {status}")
        
        # Cleanup
        await manager.graceful_shutdown()
    
    async def test_service_availability_checks(self):
        """Test service availability checking"""
        manager = ServiceManager()
        
        # Before initialization
        assert not manager.is_service_available('vector')
        assert not manager.is_service_available('ai')
        assert len(manager.get_available_services()) == 0
        
        # After initialization
        await manager.initialize_all_services()
        
        available_services = manager.get_available_services()
        print(f"\n🔍 Available services: {available_services}")
        
        # Test availability for each service
        for service_name in ['graph', 'vector', 'ai', 'project', 'monitor']:
            is_available = manager.is_service_available(service_name)
            print(f"   {service_name}: {'✅' if is_available else '❌'}")
        
        # Core services should be checked
        vector_available = manager.is_service_available('vector')
        ai_available = manager.is_service_available('ai')
        
        # At least one core service should be available for a functional system
        assert vector_available or ai_available, "No core services available"
        
        await manager.graceful_shutdown()
    
    async def test_service_access_methods(self):
        """Test service access and retrieval"""
        manager = ServiceManager()
        
        # Before initialization - should return None
        assert manager.get_service('vector') is None
        assert manager.get_service('ai') is None
        
        # Initialize services
        await manager.initialize_all_services()
        
        # Test service retrieval
        vector_service = manager.get_service('vector')
        ai_service = manager.get_service('ai')
        graph_service = manager.get_service('graph')
        
        print(f"\n🔧 Service Access Results:")
        print(f"   Vector service: {'✅' if vector_service else '❌'}")
        print(f"   AI service: {'✅' if ai_service else '❌'}")
        print(f"   Graph service: {'✅' if graph_service else '❌'}")
        
        # Test service functionality if available
        if vector_service:
            status = vector_service.get_status()
            assert 'initialized' in status
            print(f"   Vector service status: {status.get('initialized')}")
        
        if ai_service:
            assert hasattr(ai_service, 'is_ready')
            is_ready = ai_service.is_ready()
            print(f"   AI service ready: {is_ready}")
        
        await manager.graceful_shutdown()
    
    async def test_health_check_functionality(self):
        """Test comprehensive health checking"""
        manager = ServiceManager()
        await manager.initialize_all_services()
        
        # Perform health check
        health_status = await manager.health_check_all()
        
        # Validate health check structure
        assert 'timestamp' in health_status
        assert 'overall_status' in health_status
        assert 'services' in health_status
        assert 'summary' in health_status
        
        # Validate overall status
        overall_status = health_status['overall_status']
        assert overall_status in ['healthy', 'degraded', 'unhealthy']
        
        # Validate summary
        summary = health_status['summary']
        assert 'total_services' in summary
        assert 'available_services' in summary
        assert 'core_services_available' in summary
        
        print(f"\n🩺 Health Check Results:")
        print(f"   Overall status: {overall_status}")
        print(f"   Available services: {summary['available_services']}/{summary['total_services']}")
        print(f"   Core services: {summary['core_services_available']}/2")
        
        # Validate individual service health
        for service_name, service_health in health_status['services'].items():
            is_available = service_health.get('available', False)
            icon = "✅" if is_available else "❌"
            print(f"   {icon} {service_name}: {service_health}")
        
        await manager.graceful_shutdown()
    
    async def test_graceful_degradation(self):
        """Test that system handles missing services gracefully"""
        manager = ServiceManager()
        
        # Test accessing services before initialization
        vector_service = manager.get_service('vector')
        ai_service = manager.get_service('ai')
        
        assert vector_service is None
        assert ai_service is None
        
        # Initialize (some services may fail)
        await manager.initialize_all_services()
        
        # Test that manager handles failed services gracefully
        nonexistent_service = manager.get_service('nonexistent')
        assert nonexistent_service is None
        
        # Test service summary
        summary = manager.get_service_summary()
        assert 'initialized' in summary
        assert 'total_services' in summary
        assert 'available_services' in summary
        
        print(f"\n📋 Service Summary:")
        print(f"   Initialized: {summary['initialized']}")
        print(f"   Total services: {summary['total_services']}")
        print(f"   Available: {summary['available_services']}")
        print(f"   Core services: {summary['core_services_status']}")
        
        await manager.graceful_shutdown()
    
    async def test_global_service_functions(self):
        """Test global convenience functions"""
        # Initialize backend
        results = await initialize_backend()
        
        assert isinstance(results, dict)
        print(f"\n🌍 Global Backend Initialization:")
        for service, status in results.items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {service}")
        
        # Test global service access functions
        ai_service = get_ai_service()
        vector_service = get_vector_service()
        graph_service = get_graph_service()
        
        print(f"\n🔗 Global Service Access:")
        print(f"   AI service: {'✅' if ai_service else '❌'}")
        print(f"   Vector service: {'✅' if vector_service else '❌'}")
        print(f"   Graph service: {'✅' if graph_service else '❌'}")
        
        # Test availability checking
        from app.core.service_manager import is_service_available
        
        ai_available = is_service_available('ai')
        vector_available = is_service_available('vector')
        
        print(f"   AI available: {ai_available}")
        print(f"   Vector available: {vector_available}")
        
        # Shutdown backend
        await shutdown_backend()
        
        # After shutdown, services should not be available
        assert get_ai_service() is None
        assert get_vector_service() is None
    
    async def test_service_manager_error_handling(self):
        """Test error handling in service manager"""
        manager = ServiceManager()
        
        # Test getting service summary before initialization
        summary = manager.get_service_summary()
        assert summary['status'] == 'not_initialized'
        
        # Test health check before initialization
        health = await manager.health_check_all()
        assert 'timestamp' in health
        
        # Test shutdown before initialization (should not crash)
        await manager.graceful_shutdown()
        
        print("✅ Error handling tests completed successfully")


if __name__ == "__main__":
    # Allow running this test file directly
    import subprocess
    
    print("🧪 Running service manager tests...")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        __file__,
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ])
    
    sys.exit(result.returncode)