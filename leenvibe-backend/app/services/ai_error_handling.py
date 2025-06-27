import logging
from typing import Dict, Any, Optional, Callable
import asyncio
import traceback
from functools import wraps
import time

logger = logging.getLogger(__name__)

class AIErrorHandler:
    """Comprehensive error handling for AI service operations"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_history = []
        self.max_history = 100
    
    def track_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Track error occurrence for monitoring"""
        timestamp = time.time()
        
        # Increment error count
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Add to history
        error_record = {
            "type": error_type,
            "message": error_message,
            "timestamp": timestamp,
            "context": context or {}
        }
        
        self.error_history.append(error_record)
        
        # Maintain history size limit
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
        
        logger.error(f"AI Service Error [{error_type}]: {error_message}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "recent_errors": len([e for e in self.error_history 
                                if e["timestamp"] > time.time() - 3600]),  # Last hour
            "error_history_size": len(self.error_history)
        }

def ai_error_handler(error_handler: AIErrorHandler, operation_name: str):
    """Decorator for handling AI service errors"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ImportError as e:
                error_msg = f"Missing dependency in {operation_name}: {str(e)}"
                error_handler.track_error("dependency_error", error_msg, {
                    "operation": operation_name,
                    "missing_module": str(e)
                })
                return {
                    "status": "error",
                    "message": "Service dependency not available",
                    "error_type": "dependency_error",
                    "suggestion": "Check if all required packages are installed"
                }
            except FileNotFoundError as e:
                error_msg = f"File not found in {operation_name}: {str(e)}"
                error_handler.track_error("file_error", error_msg, {
                    "operation": operation_name,
                    "file_path": str(e)
                })
                return {
                    "status": "error",
                    "message": "Required file not found",
                    "error_type": "file_error",
                    "suggestion": "Check file path and permissions"
                }
            except MemoryError as e:
                error_msg = f"Memory error in {operation_name}: {str(e)}"
                error_handler.track_error("memory_error", error_msg, {
                    "operation": operation_name
                })
                return {
                    "status": "error",
                    "message": "Insufficient memory for operation",
                    "error_type": "memory_error",
                    "suggestion": "Try with smaller files or restart the service"
                }
            except asyncio.TimeoutError as e:
                error_msg = f"Timeout in {operation_name}: {str(e)}"
                error_handler.track_error("timeout_error", error_msg, {
                    "operation": operation_name
                })
                return {
                    "status": "error",
                    "message": "Operation timed out",
                    "error_type": "timeout_error",
                    "suggestion": "Try again or check system performance"
                }
            except UnicodeDecodeError as e:
                error_msg = f"Encoding error in {operation_name}: {str(e)}"
                error_handler.track_error("encoding_error", error_msg, {
                    "operation": operation_name,
                    "encoding": e.encoding
                })
                return {
                    "status": "error",
                    "message": "File encoding not supported",
                    "error_type": "encoding_error",
                    "suggestion": "Ensure file is in UTF-8 encoding"
                }
            except Exception as e:
                error_msg = f"Unexpected error in {operation_name}: {str(e)}"
                error_handler.track_error("unexpected_error", error_msg, {
                    "operation": operation_name,
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                })
                return {
                    "status": "error",
                    "message": f"Unexpected error occurred: {str(e)}",
                    "error_type": "unexpected_error",
                    "suggestion": "Check logs for detailed error information"
                }
        return wrapper
    return decorator

class ServiceHealthChecker:
    """Monitor health of AI service components"""
    
    def __init__(self):
        self.service_status = {}
        self.last_check = {}
    
    async def check_mlx_health(self, mlx_service) -> Dict[str, Any]:
        """Check MLX service health"""
        try:
            health_status = mlx_service.get_health_status()
            self.service_status["mlx"] = {
                "status": "healthy" if health_status.get("is_initialized") else "unhealthy",
                "details": health_status,
                "last_check": time.time()
            }
            return self.service_status["mlx"]
        except Exception as e:
            self.service_status["mlx"] = {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }
            return self.service_status["mlx"]
    
    async def check_ast_health(self, ast_service) -> Dict[str, Any]:
        """Check AST service health"""
        try:
            status = ast_service.get_status()
            self.service_status["ast"] = {
                "status": "healthy" if status.get("initialized") else "unhealthy",
                "details": status,
                "last_check": time.time()
            }
            return self.service_status["ast"]
        except Exception as e:
            self.service_status["ast"] = {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }
            return self.service_status["ast"]
    
    async def check_vector_health(self, vector_service) -> Dict[str, Any]:
        """Check vector store health"""
        try:
            status = vector_service.get_status()
            self.service_status["vector"] = {
                "status": "healthy" if status.get("initialized") else "unhealthy",
                "details": status,
                "last_check": time.time()
            }
            return self.service_status["vector"]
        except Exception as e:
            self.service_status["vector"] = {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }
            return self.service_status["vector"]
    
    async def run_full_health_check(self, mlx_service, ast_service, vector_service) -> Dict[str, Any]:
        """Run comprehensive health check on all services"""
        health_results = {}
        
        # Run health checks in parallel
        mlx_task = asyncio.create_task(self.check_mlx_health(mlx_service))
        ast_task = asyncio.create_task(self.check_ast_health(ast_service))
        vector_task = asyncio.create_task(self.check_vector_health(vector_service))
        
        health_results["mlx"] = await mlx_task
        health_results["ast"] = await ast_task
        health_results["vector"] = await vector_task
        
        # Calculate overall health
        healthy_services = sum(1 for service in health_results.values() 
                             if service.get("status") == "healthy")
        total_services = len(health_results)
        
        overall_status = {
            "overall_health": "healthy" if healthy_services == total_services else "degraded",
            "healthy_services": healthy_services,
            "total_services": total_services,
            "health_percentage": round((healthy_services / total_services) * 100, 1),
            "services": health_results,
            "timestamp": time.time()
        }
        
        return overall_status

class PerformanceMonitor:
    """Monitor performance metrics for AI operations"""
    
    def __init__(self):
        self.metrics = {}
        self.operation_history = []
        self.max_history = 1000
    
    def record_operation(self, operation_name: str, duration: float, success: bool, 
                        metadata: Dict[str, Any] = None):
        """Record performance metrics for an operation"""
        
        # Initialize metrics for this operation if needed
        if operation_name not in self.metrics:
            self.metrics[operation_name] = {
                "total_operations": 0,
                "successful_operations": 0,
                "total_duration": 0,
                "average_duration": 0,
                "min_duration": float('inf'),
                "max_duration": 0,
                "success_rate": 0
            }
        
        metric = self.metrics[operation_name]
        
        # Update metrics
        metric["total_operations"] += 1
        if success:
            metric["successful_operations"] += 1
        
        metric["total_duration"] += duration
        metric["average_duration"] = metric["total_duration"] / metric["total_operations"]
        metric["min_duration"] = min(metric["min_duration"], duration)
        metric["max_duration"] = max(metric["max_duration"], duration)
        metric["success_rate"] = (metric["successful_operations"] / metric["total_operations"]) * 100
        
        # Add to history
        operation_record = {
            "operation": operation_name,
            "duration": duration,
            "success": success,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        
        self.operation_history.append(operation_record)
        
        # Maintain history size
        if len(self.operation_history) > self.max_history:
            self.operation_history = self.operation_history[-self.max_history:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "metrics": self.metrics.copy(),
            "recent_operations": len([op for op in self.operation_history 
                                    if op["timestamp"] > time.time() - 3600]),
            "total_recorded_operations": len(self.operation_history)
        }

def performance_monitor(monitor: PerformanceMonitor, operation_name: str):
    """Decorator for monitoring operation performance"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            result = None
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                
                # Extract metadata from result if available
                metadata = {}
                if result and isinstance(result, dict):
                    metadata = {
                        "status": result.get("status"),
                        "confidence": result.get("confidence"),
                        "service_status": result.get("service_status")
                    }
                
                monitor.record_operation(operation_name, duration, success, metadata)
        return wrapper
    return decorator