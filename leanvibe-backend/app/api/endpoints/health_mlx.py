"""
MLX Health Check Endpoint

Provides detailed health status for MLX services including model loading status,
memory usage, and inference capabilities.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health/mlx")
async def mlx_health_check() -> Dict[str, Any]:
    """
    Check MLX service health and model status
    
    Returns comprehensive MLX service health including:
    - Model loading status (pretrained vs random weights)
    - Memory usage and performance metrics
    - Inference readiness and capabilities
    - Service availability and errors
    """
    try:
        # Import unified MLX service
        from app.services.unified_mlx_service import unified_mlx_service
        
        # Get health status from unified service
        health = unified_mlx_service.get_model_health()
        
        # Determine overall status based on unified service health
        status = health.get("status", "unknown")
        if status == "healthy":
            overall_status = "healthy"
        elif status == "uninitialized":
            overall_status = "uninitialized"
        else:
            overall_status = "degraded"
        
        # Determine inference capability
        inference_ready = health.get("initialized", False)
        model_loaded = health.get("model_loaded", False)
        
        # Determine if model has real pretrained weights
        strategy = health.get("strategy", "unknown")
        has_real_weights = strategy in ["production", "pragmatic"] and model_loaded
        
        # Calculate confidence score based on strategy and health
        if strategy in ["production", "pragmatic"] and model_loaded:
            confidence_score = 0.9
        elif strategy == "mock":
            confidence_score = 0.6  # Mock has decent confidence for testing
        elif strategy == "fallback":
            confidence_score = 0.3
        else:
            confidence_score = 0.0
        
        return {
            "status": overall_status,
            "model": health.get("model_name", "unknown"),
            "model_loaded": health.get("model_loaded", False),
            "has_pretrained_weights": has_real_weights,
            "inference_ready": inference_ready,
            "confidence_score": confidence_score,
            "last_inference_time_ms": (health.get("last_inference_time", 0) * 1000) if health.get("last_inference_time") else None,
            "memory_usage_mb": health.get("memory_usage_mb", 0),
            "total_inferences": health.get("total_inferences", 0),
            "service_status": health.get("status", "unknown"),
            "dependencies": {
                "hf_available": health.get("hf_available", False),
                "mlx_lm_available": health.get("mlx_lm_available", False),
            },
            "capabilities": {
                "text_generation": inference_ready,
                "code_completion": inference_ready and has_real_weights,
                "chat_interface": inference_ready and has_real_weights,
                "production_ready": has_real_weights,
            },
            "performance": {
                "last_inference_time_ms": (health.get("last_inference_time", 0) * 1000) if health.get("last_inference_time") else None,
                "average_tokens_per_second": None,  # TODO: Add when available
                "memory_efficiency": "good" if health.get("memory_usage_mb", 0) < 1000 else "moderate",
            },
            "recommendations": _get_unified_health_recommendations(health),
        }
        
    except ImportError as e:
        logger.error(f"MLX service import failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "service_unavailable",
                "error": "MLX service not available",
                "message": str(e),
            }
        )
    except Exception as e:
        logger.error(f"MLX health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "health_check_failed",
                "error": "Unable to determine MLX service health",
                "message": str(e),
            }
        )


def _get_health_recommendations(health: Dict[str, Any]) -> list[str]:
    """Generate health recommendations based on service status (legacy)"""
    recommendations = []
    
    if not health.get("has_pretrained_weights", False):
        if health.get("mlx_lm_available", False):
            recommendations.append("Initialize service to download pre-trained weights")
        else:
            recommendations.append("Install mlx-lm: pip install mlx-lm")
    
    if not health.get("hf_available", False):
        recommendations.append("Install transformers: pip install transformers")
    
    if health.get("memory_usage_mb", 0) > 2000:
        recommendations.append("High memory usage detected - consider model optimization")
    
    if health.get("status") == "ready_fallback":
        recommendations.append("Service running in fallback mode - check MLX-LM installation")
    
    if health.get("total_inferences", 0) == 0:
        recommendations.append("Run test inference to validate functionality")
    
    if not recommendations:
        recommendations.append("Service operating optimally")
    
    return recommendations


def _get_unified_health_recommendations(health: Dict[str, Any]) -> list[str]:
    """Generate health recommendations for unified MLX service"""
    recommendations = []
    
    strategy = health.get("strategy", "unknown")
    status = health.get("status", "unknown")
    service_details = health.get("service_details", {})
    performance = health.get("performance", {})
    
    if status == "uninitialized":
        recommendations.append("Initialize unified MLX service to begin inference")
    elif status == "unavailable":
        recommendations.append("Check service configuration and dependencies")
    
    if strategy == "fallback":
        recommendations.append("Service using fallback strategy - check production dependencies")
    elif strategy == "mock":
        recommendations.append("Service in mock mode - switch to PRODUCTION or PRAGMATIC for real inference")
    
    # Performance recommendations
    if not performance.get("within_target", True):
        recommendations.append("Response time exceeding target - consider optimizing or switching strategies")
    
    # Memory recommendations
    memory_usage = service_details.get("memory_usage_mb", 0)
    if memory_usage > 2000:
        recommendations.append("High memory usage detected - consider model optimization")
    elif memory_usage == 0 and strategy in ["production", "pragmatic"]:
        recommendations.append("Memory usage not reported - check model loading")
    
    # Strategy recommendations
    available_strategies = len(health.get("dependencies", {}).get("strategies_available", []))
    if available_strategies == 1:
        recommendations.append("Only one strategy available - install MLX dependencies for more options")
    
    if not recommendations:
        recommendations.append(f"Unified MLX service operating optimally with {strategy} strategy")
    
    return recommendations


@router.get("/health/mlx/detailed")
async def mlx_detailed_health() -> Dict[str, Any]:
    """
    Get detailed MLX health information including model configuration
    """
    try:
        from app.services.unified_mlx_service import unified_mlx_service
        
        # Get detailed health from unified service
        full_status = unified_mlx_service.get_model_health()
        performance_metrics = unified_mlx_service.get_performance_metrics()
        
        return {
            "service_info": {
                "name": "UnifiedMLXService",
                "version": "1.0.0",
                "mode": "unified_strategy",
                "current_strategy": full_status.get("strategy", "unknown"),
            },
            "model_info": {
                "strategies_available": unified_mlx_service.get_available_strategies(),
                "current_strategy_details": full_status.get("service_details", {}),
            },
            "runtime_status": full_status,
            "performance_metrics": performance_metrics,
            "system_info": {
                "mlx_available": True,  # If we got here, MLX is available
                "apple_silicon": True,  # MLX requires Apple Silicon
                "unified_service": True,
                "strategy_switching": len(unified_mlx_service.get_available_strategies()) > 1,
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed MLX health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to get detailed MLX health",
                "message": str(e),
            }
        )