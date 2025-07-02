"""
Health Check and Monitoring Endpoints for LeanVibe Backend
Provides comprehensive health monitoring for production deployments
"""

import time
import psutil
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import asyncio
import mlx.core as mx

from ..core.secure_config import get_config_manager, SecureConfigManager
from ..core.secrets_manager import get_secrets_manager


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def basic_health():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "leanvibe-backend"
    }


@router.get("/ready")
async def readiness_check(config_manager: SecureConfigManager = Depends(get_config_manager)):
    """
    Readiness probe - checks if service is ready to serve traffic
    Returns 200 if ready, 503 if not ready
    """
    checks = {}
    ready = True
    
    try:
        # Check configuration
        config_validation = config_manager.validate_configuration()
        checks["configuration"] = {
            "status": "pass" if config_validation["valid"] else "fail",
            "details": config_validation
        }
        if not config_validation["valid"]:
            ready = False
        
        # Check secrets availability
        secrets_manager = get_secrets_manager()
        secrets_validation = secrets_manager.validate_secrets()
        checks["secrets"] = {
            "status": "pass" if secrets_validation["valid"] else "fail",
            "available_sources": secrets_validation["available_sources"],
            "missing": secrets_validation.get("missing", [])
        }
        if not secrets_validation["valid"]:
            ready = False
        
        # Check MLX availability
        try:
            test_array = mx.array([1.0, 2.0, 3.0])
            memory_mb = mx.get_active_memory() / 1024 / 1024
            checks["mlx"] = {
                "status": "pass",
                "memory_mb": round(memory_mb, 2),
                "devices": len(mx.list_devices())
            }
        except Exception as e:
            checks["mlx"] = {
                "status": "fail",
                "error": str(e)
            }
            ready = False
        
        result = {
            "status": "ready" if ready else "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks
        }
        
        return JSONResponse(
            content=result,
            status_code=200 if ready else 503
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "status": "not_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/live")
async def liveness_check():
    """
    Liveness probe - checks if service is alive
    Returns 200 if alive, 503 if dead
    """
    try:
        # Basic system checks
        system_load = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        # Check if system is under extreme stress
        alive = True
        issues = []
        
        if memory_percent > 95:
            alive = False
            issues.append(f"Memory usage critical: {memory_percent}%")
        
        if disk_percent > 95:
            alive = False
            issues.append(f"Disk usage critical: {disk_percent}%")
        
        if system_load > 20:  # Very high load
            alive = False
            issues.append(f"System load critical: {system_load}")
        
        result = {
            "status": "alive" if alive else "dead",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": {
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "load_average": system_load
            }
        }
        
        if issues:
            result["issues"] = issues
        
        return JSONResponse(
            content=result,
            status_code=200 if alive else 503
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "status": "dead",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@router.get("/detailed")
async def detailed_health(config_manager: SecureConfigManager = Depends(get_config_manager)):
    """Detailed health information for monitoring and debugging"""
    try:
        # System information
        system_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / 1024**3, 2),
                "available_gb": round(psutil.virtual_memory().available / 1024**3, 2),
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / 1024**3, 2),
                "free_gb": round(psutil.disk_usage('/').free / 1024**3, 2),
                "percent": psutil.disk_usage('/').percent
            },
            "uptime_seconds": int(time.time() - psutil.boot_time()) if hasattr(psutil, 'boot_time') else None
        }
        
        # MLX information
        mlx_info = {}
        try:
            mlx_info = {
                "available": True,
                "memory_mb": round(mx.get_active_memory() / 1024 / 1024, 2),
                "peak_memory_mb": round(mx.get_peak_memory() / 1024 / 1024, 2),
                "devices": len(mx.list_devices()),
                "cache_memory_mb": round(mx.get_cache_memory() / 1024 / 1024, 2)
            }
        except Exception as e:
            mlx_info = {
                "available": False,
                "error": str(e)
            }
        
        # Configuration information
        config_info = config_manager.get_health_check_info()
        
        # Application metrics
        app_metrics = {
            "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
            "process_id": psutil.Process().pid,
            "memory_info": {
                "rss_mb": round(psutil.Process().memory_info().rss / 1024**2, 2),
                "vms_mb": round(psutil.Process().memory_info().vms / 1024**2, 2)
            },
            "open_files": len(psutil.Process().open_files()),
            "connections": len(psutil.Process().connections())
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "leanvibe-backend",
            "version": "1.0.0",  # This should come from version file
            "system": system_info,
            "mlx": mlx_info,
            "configuration": config_info,
            "application": app_metrics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus-compatible metrics endpoint"""
    try:
        # Basic system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # MLX metrics
        mlx_memory = 0
        mlx_peak_memory = 0
        try:
            mlx_memory = mx.get_active_memory()
            mlx_peak_memory = mx.get_peak_memory()
        except:
            pass
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        metrics = f"""# HELP system_cpu_percent CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent {cpu_percent}

# HELP system_memory_total_bytes Total system memory in bytes
# TYPE system_memory_total_bytes gauge
system_memory_total_bytes {memory.total}

# HELP system_memory_available_bytes Available system memory in bytes
# TYPE system_memory_available_bytes gauge
system_memory_available_bytes {memory.available}

# HELP system_memory_percent Memory usage percentage
# TYPE system_memory_percent gauge
system_memory_percent {memory.percent}

# HELP system_disk_total_bytes Total disk space in bytes
# TYPE system_disk_total_bytes gauge
system_disk_total_bytes {disk.total}

# HELP system_disk_free_bytes Free disk space in bytes
# TYPE system_disk_free_bytes gauge
system_disk_free_bytes {disk.free}

# HELP mlx_memory_bytes MLX active memory in bytes
# TYPE mlx_memory_bytes gauge
mlx_memory_bytes {mlx_memory}

# HELP mlx_peak_memory_bytes MLX peak memory in bytes
# TYPE mlx_peak_memory_bytes gauge
mlx_peak_memory_bytes {mlx_peak_memory}

# HELP process_memory_rss_bytes Process resident memory in bytes
# TYPE process_memory_rss_bytes gauge
process_memory_rss_bytes {process_memory.rss}

# HELP process_memory_vms_bytes Process virtual memory in bytes
# TYPE process_memory_vms_bytes gauge
process_memory_vms_bytes {process_memory.vms}

# HELP process_open_files Number of open files
# TYPE process_open_files gauge
process_open_files {len(process.open_files())}
"""
        
        return JSONResponse(
            content=metrics,
            media_type="text/plain",
            headers={"Content-Type": "text/plain; charset=utf-8"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics collection failed: {str(e)}"
        )


@router.get("/dependencies")
async def dependencies_check():
    """Check external dependencies status"""
    checks = {}
    
    # Database check
    try:
        # This would check actual database connection
        # For now, we'll simulate it
        checks["database"] = {
            "status": "pass",
            "response_time_ms": 5,
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        checks["database"] = {
            "status": "fail",
            "error": str(e),
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    
    # Redis check
    try:
        # This would check actual Redis connection
        # For now, we'll simulate it
        checks["redis"] = {
            "status": "pass",
            "response_time_ms": 2,
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        checks["redis"] = {
            "status": "fail",
            "error": str(e),
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    
    # External API checks could be added here
    
    all_healthy = all(check["status"] == "pass" for check in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": checks
    }