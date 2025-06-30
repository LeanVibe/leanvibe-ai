"""
Real Phi-3 Inference Tests

Tests for validating actual pre-trained model inference capabilities.
These tests are marked as slow and require real model weights to be downloaded.

Run with: pytest -m mlx_real_inference -v
"""

import pytest
import asyncio
from app.services.phi3_mini_service import Phi3MiniService


@pytest.mark.mlx_real_inference
@pytest.mark.asyncio
async def test_phi3_real_inference():
    """Test real Phi-3 inference with pre-trained weights"""
    service = Phi3MiniService()
    await service.initialize()
    
    # Skip if real weights couldn't be loaded
    if not service.health_status.get("has_pretrained_weights", False):
        pytest.skip("Pre-trained weights not available")
    
    # Test actual inference
    response = await service.generate_text(
        "Write a simple Python function to add two numbers.",
        max_tokens=100
    )
    
    # Validate real inference (not random output)
    assert len(response) > 0
    assert "def " in response.lower()  # Should contain function definition
    assert "REAL PRE-TRAINED INFERENCE" in response  # Should indicate real weights
    assert "random weights" not in response.lower()  # Should not be random
    
    # Verify service status
    status = service.get_health_status()
    assert status["has_pretrained_weights"] == True
    assert status["status"] == "ready_pretrained"


@pytest.mark.mlx_real_inference  
@pytest.mark.asyncio
async def test_phi3_inference_quality():
    """Test inference quality and coherence"""
    service = Phi3MiniService()
    await service.initialize()
    
    if not service.health_status.get("has_pretrained_weights", False):
        pytest.skip("Pre-trained weights not available")
    
    # Test coherent response
    response = await service.generate_text(
        "Explain what is recursion in programming.",
        max_tokens=150
    )
    
    # Quality checks
    assert len(response) > 50  # Substantial response
    assert "recursion" in response.lower()  # On-topic
    assert "REAL PRE-TRAINED INFERENCE" in response  # Using real weights
    
    # Should be a meaningful explanation, not random tokens
    assert any(word in response.lower() for word in ["function", "call", "itself", "base", "case"])


@pytest.mark.mlx_real_inference
@pytest.mark.asyncio
async def test_phi3_code_generation():
    """Test code generation capabilities with real weights"""
    service = Phi3MiniService()
    await service.initialize()
    
    if not service.health_status.get("has_pretrained_weights", False):
        pytest.skip("Pre-trained weights not available")
    
    # Test code generation
    response = await service.generate_text(
        "Create a Python class for a simple calculator.",
        max_tokens=200
    )
    
    # Code generation checks
    assert len(response) > 100  # Should be substantial
    assert "class" in response.lower()  # Should contain class definition
    assert "def " in response.lower()  # Should contain method definitions
    assert "REAL PRE-TRAINED INFERENCE" in response  # Using real weights


@pytest.mark.mlx_real_inference
@pytest.mark.asyncio
async def test_phi3_performance_metrics():
    """Test performance metrics with real inference"""
    service = Phi3MiniService()
    await service.initialize()
    
    if not service.health_status.get("has_pretrained_weights", False):
        pytest.skip("Pre-trained weights not available")
    
    # Test inference with timing
    import time
    start_time = time.time()
    
    response = await service.generate_text(
        "Hello, world!",
        max_tokens=50
    )
    
    inference_time = time.time() - start_time
    
    # Performance checks
    assert inference_time < 10.0  # Should complete within 10 seconds
    assert len(response) > 0
    
    # Check health metrics updated
    status = service.get_health_status()
    assert status["last_inference_time"] is not None
    assert status["total_inferences"] > 0
    
    # Log performance metrics
    print(f"Inference time: {inference_time:.2f}s")
    print(f"Response length: {len(response)} characters")


@pytest.mark.mlx_real_inference
@pytest.mark.asyncio
async def test_phi3_service_health_with_real_weights():
    """Test service health reporting with real weights loaded"""
    service = Phi3MiniService()
    await service.initialize()
    
    if not service.health_status.get("has_pretrained_weights", False):
        pytest.skip("Pre-trained weights not available")
    
    # Get health status
    status = service.get_health_status()
    
    # Validate health status with real weights
    assert status["status"] == "ready_pretrained"
    assert status["has_pretrained_weights"] == True
    assert status["model_loaded"] == True
    assert status["mlx_lm_available"] == True
    assert status["hf_available"] == True
    
    # Test inference capability
    response = await service.generate_text("Test", max_tokens=10)
    
    # Verify metrics updated
    updated_status = service.get_health_status()
    assert updated_status["total_inferences"] > 0
    assert updated_status["last_inference_time"] is not None


@pytest.mark.mlx_real_inference
def test_phi3_fallback_behavior():
    """Test that service gracefully falls back when real weights unavailable"""
    # This test validates the fallback mechanism works correctly
    # when MLX-LM or weight loading fails
    
    # Mock MLX-LM unavailable
    import app.services.phi3_mini_service as phi3_module
    original_mlx_lm_available = phi3_module.MLX_LM_AVAILABLE
    
    try:
        # Temporarily disable MLX-LM
        phi3_module.MLX_LM_AVAILABLE = False
        
        service = Phi3MiniService()
        
        # Should initialize in fallback mode
        assert service.health_status["mlx_lm_available"] == False
        
    finally:
        # Restore original state
        phi3_module.MLX_LM_AVAILABLE = original_mlx_lm_available


@pytest.mark.mlx_real_inference
@pytest.mark.asyncio 
async def test_phi3_multiple_inferences():
    """Test multiple consecutive inferences for stability"""
    service = Phi3MiniService()
    await service.initialize()
    
    if not service.health_status.get("has_pretrained_weights", False):
        pytest.skip("Pre-trained weights not available")
    
    # Run multiple inferences
    prompts = [
        "What is Python?",
        "Write a hello world function.",
        "Explain variables in programming."
    ]
    
    responses = []
    for prompt in prompts:
        response = await service.generate_text(prompt, max_tokens=50)
        responses.append(response)
        
        # Each should be real inference
        assert "REAL PRE-TRAINED INFERENCE" in response
    
    # Verify all responses are different (not cached/identical)
    assert len(set(responses)) == len(responses)  # All unique
    
    # Check metrics updated correctly
    status = service.get_health_status()
    assert status["total_inferences"] >= len(prompts)