"""
Comprehensive Test Suite for Unified MLX Service

Tests strategy switching, service consolidation, and backward compatibility.
"""

import asyncio
import pytest
import warnings
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.services.unified_mlx_service import (
    UnifiedMLXService,
    MLXInferenceStrategy,
    ProductionMLXStrategy,
    PragmaticMLXStrategy,
    MockMLXStrategy,
    FallbackMLXStrategy,
    unified_mlx_service,
)


class TestUnifiedMLXService:
    """Test the unified MLX service consolidation and strategy switching"""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance for testing"""
        return UnifiedMLXService(preferred_strategy=MLXInferenceStrategy.AUTO)

    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization and strategy selection"""
        # Mock availability checks
        with patch.object(ProductionMLXStrategy, 'is_available', return_value=True), \
             patch.object(PragmaticMLXStrategy, 'is_available', return_value=True), \
             patch.object(MockMLXStrategy, 'is_available', return_value=True):
            
            # Mock initialization
            with patch.object(ProductionMLXStrategy, 'initialize', new_callable=AsyncMock, return_value=True):
                result = await service.initialize()
                
                assert result is True
                assert service.is_initialized
                assert service.current_strategy is not None
                assert isinstance(service.current_strategy, ProductionMLXStrategy)

    @pytest.mark.asyncio
    async def test_strategy_fallback_chain(self, service):
        """Test strategy fallback behavior when preferred strategies fail"""
        # Production fails, should fallback to pragmatic
        with patch.object(ProductionMLXStrategy, 'is_available', return_value=False), \
             patch.object(PragmaticMLXStrategy, 'is_available', return_value=True), \
             patch.object(PragmaticMLXStrategy, 'initialize', new_callable=AsyncMock, return_value=True):
            
            result = await service.initialize()
            
            assert result is True
            assert isinstance(service.current_strategy, PragmaticMLXStrategy)

    @pytest.mark.asyncio
    async def test_mock_strategy_fallback(self, service):
        """Test fallback to mock strategy when all real strategies fail"""
        with patch.object(ProductionMLXStrategy, 'is_available', return_value=False), \
             patch.object(PragmaticMLXStrategy, 'is_available', return_value=False), \
             patch.object(MockMLXStrategy, 'initialize', new_callable=AsyncMock, return_value=True):
            
            result = await service.initialize()
            
            assert result is True
            assert isinstance(service.current_strategy, MockMLXStrategy)

    @pytest.mark.asyncio
    async def test_code_completion_delegation(self, service):
        """Test that code completion is properly delegated to strategy"""
        # Mock strategy
        mock_strategy = AsyncMock()
        mock_strategy.generate_code_completion = AsyncMock(return_value={
            "status": "success",
            "response": "test response",
            "confidence": 0.8
        })
        
        service.current_strategy = mock_strategy
        service.is_initialized = True
        
        context = {"file_path": "test.py", "language": "python"}
        result = await service.generate_code_completion(context, "suggest")
        
        assert result["status"] == "success"
        assert result["response"] == "test response"
        mock_strategy.generate_code_completion.assert_called_once_with(context, "suggest")

    def test_available_strategies(self, service):
        """Test getting available strategies"""
        with patch.object(ProductionMLXStrategy, 'is_available', return_value=True), \
             patch.object(PragmaticMLXStrategy, 'is_available', return_value=False), \
             patch.object(MockMLXStrategy, 'is_available', return_value=True):
            
            strategies = service.get_available_strategies()
            
            assert "production" in strategies
            assert "pragmatic" not in strategies
            assert "mock" in strategies
            assert "fallback" in strategies  # Always available

    def test_model_health(self, service):
        """Test model health reporting"""
        mock_strategy = MagicMock()
        mock_strategy.get_model_health.return_value = {
            "status": "healthy",
            "strategy": "production",
            "initialized": True
        }
        
        service.current_strategy = mock_strategy
        service.is_initialized = True
        
        health = service.get_model_health()
        
        assert health["strategy"] == "production"
        assert health["status"] == "healthy"
        assert health["initialized"] is True

    def test_performance_metrics(self, service):
        """Test performance metrics collection"""
        # Setup mock strategy with performance data
        mock_strategy = MagicMock()
        mock_strategy.get_model_health.return_value = {
            "performance": {
                "avg_response_time": 1.5,
                "total_requests": 10,
                "within_target": True
            }
        }
        
        service.current_strategy = mock_strategy
        service.is_initialized = True
        
        metrics = service.get_performance_metrics()
        
        assert "avg_response_time" in metrics
        assert "total_requests" in metrics
        assert "performance_status" in metrics

    @pytest.mark.asyncio
    async def test_strategy_switching(self, service):
        """Test dynamic strategy switching"""
        # Initialize with production strategy
        with patch.object(ProductionMLXStrategy, 'is_available', return_value=True), \
             patch.object(ProductionMLXStrategy, 'initialize', new_callable=AsyncMock, return_value=True):
            
            await service.initialize()
            assert isinstance(service.current_strategy, ProductionMLXStrategy)
            
            # Switch to mock strategy
            with patch.object(MockMLXStrategy, 'initialize', new_callable=AsyncMock, return_value=True):
                result = await service.switch_strategy(MLXInferenceStrategy.MOCK)
                
                assert result is True
                assert isinstance(service.current_strategy, MockMLXStrategy)

    def test_error_handling_uninitialized_service(self, service):
        """Test error handling when service is not initialized"""
        
        @asyncio.coroutine
        def test_coroutine():
            return service.generate_code_completion({}, "suggest")
        
        # Use asyncio.run to handle the coroutine properly
        result = asyncio.run(test_coroutine())
        
        assert result["status"] == "error"
        assert "not initialized" in result["error"].lower()


class TestStrategyImplementations:
    """Test individual strategy implementations"""

    @pytest.mark.asyncio
    async def test_production_strategy(self):
        """Test production strategy with real model service"""
        strategy = ProductionMLXStrategy()
        
        # Mock the production model service
        with patch('app.services.unified_mlx_service.ProductionModelService') as MockService:
            mock_instance = AsyncMock()
            MockService.return_value = mock_instance
            mock_instance.initialize.return_value = True
            mock_instance.deployment_mode = "direct"
            mock_instance.generate_text.return_value = "Generated response"
            mock_instance.config.model_name = "test-model"
            mock_instance.get_health_status.return_value = {"memory_usage_mb": 500}
            
            # Initialize strategy
            result = await strategy.initialize()
            assert result is True
            
            # Test code completion
            context = {"file_path": "test.py", "language": "python"}
            completion = await strategy.generate_code_completion(context, "suggest")
            
            assert completion["status"] == "success"
            assert completion["model"] == "test-model"
            assert completion["deployment_mode"] == "direct"

    @pytest.mark.asyncio
    async def test_pragmatic_strategy(self):
        """Test pragmatic strategy implementation"""
        strategy = PragmaticMLXStrategy()
        
        # Mock the pragmatic service
        with patch('app.services.unified_mlx_service.PragmaticMLXService') as MockService:
            mock_instance = AsyncMock()
            MockService.return_value = mock_instance
            mock_instance.initialize.return_value = True
            mock_instance.generate_code_completion.return_value = {
                "status": "success",
                "response": "Pragmatic response",
                "confidence": 0.7
            }
            
            # Initialize strategy
            result = await strategy.initialize()
            assert result is True
            
            # Test code completion
            context = {"file_path": "test.py", "language": "python"}
            completion = await strategy.generate_code_completion(context, "suggest")
            
            assert completion["status"] == "success"
            assert "Pragmatic response" in completion["response"]

    @pytest.mark.asyncio
    async def test_mock_strategy(self):
        """Test mock strategy implementation"""
        strategy = MockMLXStrategy()
        
        # Mock the mock service
        with patch('app.services.unified_mlx_service.MockMLXService') as MockService:
            mock_instance = AsyncMock()
            MockService.return_value = mock_instance
            mock_instance.initialize.return_value = True
            mock_instance.generate_code_completion.return_value = {
                "status": "success",
                "response": "Mock response",
                "confidence": 0.5
            }
            
            # Initialize strategy
            result = await strategy.initialize()
            assert result is True
            
            # Test code completion
            context = {"file_path": "test.py", "language": "python"}
            completion = await strategy.generate_code_completion(context, "suggest")
            
            assert completion["status"] == "success"
            assert "Mock response" in completion["response"]

    @pytest.mark.asyncio
    async def test_fallback_strategy(self):
        """Test fallback strategy implementation"""
        strategy = FallbackMLXStrategy()
        
        # Fallback should always initialize successfully
        result = await strategy.initialize()
        assert result is True
        
        # Test code completion
        context = {"file_path": "test.py", "language": "python"}
        completion = await strategy.generate_code_completion(context, "suggest")
        
        assert completion["status"] == "success"
        assert "fallback" in completion["response"].lower()
        assert completion["confidence"] < 0.5  # Low confidence for fallback


class TestDeprecatedServiceAliases:
    """Test backward compatibility and deprecation warnings"""

    def test_deprecated_service_warnings(self):
        """Test that deprecated service aliases emit warnings"""
        from app.services.unified_mlx_service import (
            real_mlx_service,
            enhanced_ai_service,
            ai_service,
        )
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Access deprecated services
            _ = real_mlx_service.current_strategy
            _ = enhanced_ai_service.is_initialized
            _ = ai_service.get_model_health
            
            # Check that warnings were emitted
            assert len(w) >= 3
            for warning in w:
                assert issubclass(warning.category, DeprecationWarning)
                assert "deprecated" in str(warning.message)
                assert "unified_mlx_service" in str(warning.message)

    def test_deprecated_service_delegation(self):
        """Test that deprecated services delegate to unified service"""
        from app.services.unified_mlx_service import (
            real_mlx_service,
            unified_mlx_service,
        )
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Ignore deprecation warnings for test
            
            # These should delegate to the unified service
            assert real_mlx_service._service_name == "real_mlx_service"


class TestGlobalServiceInstance:
    """Test the global unified service instance"""

    def test_global_service_configuration(self):
        """Test that global service is properly configured"""
        assert unified_mlx_service is not None
        assert isinstance(unified_mlx_service, UnifiedMLXService)
        assert unified_mlx_service.preferred_strategy in MLXInferenceStrategy

    @pytest.mark.asyncio
    async def test_global_service_functionality(self):
        """Test that global service works end-to-end"""
        # Mock strategy initialization
        with patch.object(MockMLXStrategy, 'is_available', return_value=True), \
             patch.object(MockMLXStrategy, 'initialize', new_callable=AsyncMock, return_value=True):
            
            # Reset initialization state for test
            unified_mlx_service.is_initialized = False
            unified_mlx_service.current_strategy = None
            
            result = await unified_mlx_service.initialize()
            assert result is True


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""

    @pytest.mark.asyncio
    async def test_strategy_failover_during_completion(self):
        """Test strategy failover during code completion"""
        service = UnifiedMLXService(preferred_strategy=MLXInferenceStrategy.PRODUCTION)
        
        # Mock a failing strategy
        mock_strategy = AsyncMock()
        mock_strategy.generate_code_completion = AsyncMock(side_effect=Exception("Strategy failed"))
        
        service.current_strategy = mock_strategy
        service.is_initialized = True
        
        # Mock successful fallback strategy
        with patch.object(service, '_initialize_fallback_strategy') as mock_fallback:
            fallback_strategy = AsyncMock()
            fallback_strategy.generate_code_completion = AsyncMock(return_value={
                "status": "success",
                "response": "Fallback response",
                "confidence": 0.3
            })
            mock_fallback.return_value = (True, fallback_strategy)
            
            context = {"file_path": "test.py"}
            result = await service.generate_code_completion(context, "suggest")
            
            # Should succeed with fallback
            assert result["status"] == "success"
            assert "Fallback response" in result["response"]

    def test_service_health_aggregation(self):
        """Test health status aggregation from different strategies"""
        service = UnifiedMLXService()
        
        # Mock different health states
        healthy_strategy = MagicMock()
        healthy_strategy.get_model_health.return_value = {
            "status": "healthy",
            "initialized": True,
            "model_loaded": True,
            "performance": {"avg_response_time": 1.0}
        }
        
        service.current_strategy = healthy_strategy
        service.is_initialized = True
        
        health = service.get_model_health()
        
        assert health["status"] == "healthy"
        assert health["initialized"] is True
        
        # Test performance metrics aggregation
        metrics = service.get_performance_metrics()
        assert "overall_health_score" in metrics
        assert "strategy_performance" in metrics

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        service = UnifiedMLXService()
        
        # Mock strategy that introduces delays
        mock_strategy = AsyncMock()
        mock_strategy.generate_code_completion = AsyncMock(side_effect=lambda ctx, intent: 
            asyncio.sleep(0.1) or {
                "status": "success",
                "response": f"Response for {ctx['file_path']}",
                "confidence": 0.8
            }
        )
        
        service.current_strategy = mock_strategy
        service.is_initialized = True
        
        # Submit concurrent requests
        contexts = [{"file_path": f"test{i}.py"} for i in range(5)]
        tasks = [
            service.generate_code_completion(ctx, "suggest") 
            for ctx in contexts
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["status"] == "success"
            assert f"test{i}.py" in result["response"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])