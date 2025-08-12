"""
Synthetic Probes for LeanVibe Backend Monitoring

Implements synthetic probes following XP principles - simple, fast, actionable monitoring
that detects issues in <60s and provides clear actionable results.

Each probe validates critical system health with specific SLAs:
- HealthProbe: /health endpoint validation (<1s)
- MetricsProbe: /metrics endpoint validation (<2s)  
- WebSocketProbe: WebSocket handshake validation (<5s)
- APIProbe: Core API endpoints with auth (<3s each)
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import aiohttp
import websockets
from dataclasses import dataclass, field
from pydantic import BaseModel

from ..core.logging_config import get_logger

logger = get_logger(__name__)


class ProbeStatus(Enum):
    """Probe execution status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    TIMEOUT = "timeout"
    ERROR = "error"


class ProbeResult(BaseModel):
    """Result of a synthetic probe execution"""
    probe_name: str
    status: ProbeStatus
    response_time_ms: float
    timestamp: datetime
    message: str
    details: Dict[str, Any] = {}
    error: Optional[str] = None


class SLABudget(BaseModel):
    """SLA budget configuration"""
    target_response_time_ms: float
    timeout_ms: float
    success_rate_threshold: float = 0.95  # 95% success rate required


@dataclass
class ProbeHistory:
    """Track probe execution history for trend analysis"""
    results: List[ProbeResult] = field(default_factory=list)
    max_history: int = 100
    
    def add_result(self, result: ProbeResult):
        """Add probe result to history"""
        self.results.append(result)
        if len(self.results) > self.max_history:
            self.results.pop(0)
    
    def get_success_rate(self, minutes: int = 5) -> float:
        """Calculate success rate over last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_results = [r for r in self.results if r.timestamp >= cutoff]
        
        if not recent_results:
            return 1.0
            
        healthy_count = len([r for r in recent_results if r.status == ProbeStatus.HEALTHY])
        return healthy_count / len(recent_results)
    
    def get_avg_response_time(self, minutes: int = 5) -> float:
        """Calculate average response time over last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_results = [r for r in self.results if r.timestamp >= cutoff]
        
        if not recent_results:
            return 0.0
            
        return sum(r.response_time_ms for r in recent_results) / len(recent_results)


class BaseSyntheticProbe:
    """Base class for all synthetic probes"""
    
    def __init__(self, name: str, sla_budget: SLABudget):
        self.name = name
        self.sla_budget = sla_budget
        self.history = ProbeHistory()
    
    async def execute(self) -> ProbeResult:
        """Execute the probe and return result"""
        start_time = time.time()
        
        try:
            # Execute probe-specific logic
            result = await self._probe_logic()
            response_time_ms = (time.time() - start_time) * 1000
            
            # Evaluate result against SLA
            status = self._evaluate_sla(response_time_ms, result)
            
            probe_result = ProbeResult(
                probe_name=self.name,
                status=status,
                response_time_ms=response_time_ms,
                timestamp=datetime.now(),
                message=result.get("message", f"{self.name} completed"),
                details=result.get("details", {}),
                error=result.get("error")
            )
            
            self.history.add_result(probe_result)
            return probe_result
            
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            probe_result = ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.TIMEOUT,
                response_time_ms=response_time_ms,
                timestamp=datetime.now(),
                message=f"{self.name} timed out after {self.sla_budget.timeout_ms}ms",
                error="Timeout exceeded"
            )
            self.history.add_result(probe_result)
            return probe_result
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            probe_result = ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.ERROR,
                response_time_ms=response_time_ms,
                timestamp=datetime.now(),
                message=f"{self.name} failed with error",
                error=str(e)
            )
            self.history.add_result(probe_result)
            return probe_result
    
    async def _probe_logic(self) -> Dict[str, Any]:
        """Implement probe-specific logic in subclasses"""
        raise NotImplementedError
    
    def _evaluate_sla(self, response_time_ms: float, result: Dict[str, Any]) -> ProbeStatus:
        """Evaluate probe result against SLA budget"""
        if result.get("error"):
            return ProbeStatus.ERROR
            
        if response_time_ms >= self.sla_budget.timeout_ms:
            return ProbeStatus.TIMEOUT
            
        if response_time_ms > self.sla_budget.target_response_time_ms * 2:
            return ProbeStatus.DEGRADED
        elif response_time_ms > self.sla_budget.target_response_time_ms:
            return ProbeStatus.DEGRADED
        else:
            return ProbeStatus.HEALTHY


class HealthProbe(BaseSyntheticProbe):
    """Health probe validates /health endpoint (<1s SLA)"""
    
    def __init__(self, base_url: str = "http://localhost:8765"):
        super().__init__(
            name="health_probe",
            sla_budget=SLABudget(
                target_response_time_ms=1000,  # 1s target
                timeout_ms=3000  # 3s timeout
            )
        )
        self.base_url = base_url
        self.health_url = f"{base_url}/health"
    
    async def _probe_logic(self) -> Dict[str, Any]:
        """Check health endpoint availability and response format"""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
            async with session.get(self.health_url) as response:
                if response.status != 200:
                    return {
                        "error": f"Health endpoint returned status {response.status}",
                        "message": "Health check failed"
                    }
                
                data = await response.json()
                
                # Validate expected health response format
                required_fields = ["status", "service", "version"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return {
                        "error": f"Health response missing fields: {missing_fields}",
                        "message": "Health response format invalid"
                    }
                
                return {
                    "message": "Health endpoint responding correctly",
                    "details": {
                        "status": data.get("status"),
                        "service": data.get("service"),
                        "version": data.get("version"),
                        "ai_ready": data.get("ai_ready", False)
                    }
                }


class MetricsProbe(BaseSyntheticProbe):
    """Metrics probe validates /monitoring/health endpoint (<2s SLA)"""
    
    def __init__(self, base_url: str = "http://localhost:8765"):
        super().__init__(
            name="metrics_probe", 
            sla_budget=SLABudget(
                target_response_time_ms=2000,  # 2s target
                timeout_ms=5000  # 5s timeout
            )
        )
        self.base_url = base_url
        self.metrics_url = f"{base_url}/monitoring/health"
    
    async def _probe_logic(self) -> Dict[str, Any]:
        """Check metrics endpoint and validate monitoring data"""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.get(self.metrics_url) as response:
                if response.status not in [200, 503]:  # 503 is acceptable for degraded state
                    return {
                        "error": f"Metrics endpoint returned status {response.status}",
                        "message": "Metrics endpoint failed"
                    }
                
                data = await response.json()
                
                # Extract key metrics for validation
                overall_status = data.get("overall_health", {}).get("status", "unknown")
                active_alerts = data.get("active_alerts", [])
                
                return {
                    "message": f"Metrics endpoint responding - system {overall_status}",
                    "details": {
                        "overall_status": overall_status,
                        "active_alerts_count": len(active_alerts),
                        "monitoring_active": data.get("monitoring_status", {}).get("health_monitoring", False)
                    }
                }


class WebSocketProbe(BaseSyntheticProbe):
    """WebSocket probe validates WebSocket handshake (<5s SLA)"""
    
    def __init__(self, base_url: str = "ws://localhost:8765"):
        super().__init__(
            name="websocket_probe",
            sla_budget=SLABudget(
                target_response_time_ms=5000,  # 5s target
                timeout_ms=10000  # 10s timeout
            )
        )
        self.base_url = base_url
        self.websocket_url = f"{base_url}/ws/probe_client"
    
    async def _probe_logic(self) -> Dict[str, Any]:
        """Test WebSocket connection and basic message exchange"""
        try:
            async with websockets.connect(
                self.websocket_url,
                ping_interval=None,  # Disable ping for test
                timeout=10
            ) as websocket:
                
                # Send test message
                test_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(str(test_message))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    return {
                        "message": "WebSocket handshake and message exchange successful",
                        "details": {
                            "connection_state": "connected",
                            "response_received": bool(response),
                            "response_length": len(str(response))
                        }
                    }
                except asyncio.TimeoutError:
                    return {
                        "error": "WebSocket connected but no response to test message",
                        "message": "WebSocket response timeout"
                    }
                    
        except Exception as e:
            return {
                "error": f"WebSocket connection failed: {str(e)}",
                "message": "WebSocket connection failed"
            }


class APIProbe(BaseSyntheticProbe):
    """API probe validates core API endpoints (<3s each)"""
    
    def __init__(self, base_url: str = "http://localhost:8765"):
        super().__init__(
            name="api_probe",
            sla_budget=SLABudget(
                target_response_time_ms=3000,  # 3s target
                timeout_ms=8000  # 8s timeout (multiple endpoints)
            )
        )
        self.base_url = base_url
        self.endpoints_to_test = [
            {"path": "/", "method": "GET", "expected_status": 200},
            {"path": "/api/projects/", "method": "GET", "expected_status": 200},
            {"path": "/streaming/stats", "method": "GET", "expected_status": 200},
            {"path": "/connections", "method": "GET", "expected_status": 200}
        ]
    
    async def _probe_logic(self) -> Dict[str, Any]:
        """Test multiple API endpoints for availability"""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
            results = {}
            total_response_time = 0
            failed_endpoints = []
            
            for endpoint in self.endpoints_to_test:
                endpoint_start = time.time()
                
                try:
                    url = f"{self.base_url}{endpoint['path']}"
                    
                    async with session.request(endpoint["method"], url) as response:
                        endpoint_time = (time.time() - endpoint_start) * 1000
                        total_response_time += endpoint_time
                        
                        if response.status == endpoint["expected_status"]:
                            results[endpoint["path"]] = {
                                "status": "healthy",
                                "response_time_ms": endpoint_time,
                                "http_status": response.status
                            }
                        else:
                            results[endpoint["path"]] = {
                                "status": "unhealthy",
                                "response_time_ms": endpoint_time,
                                "http_status": response.status,
                                "expected_status": endpoint["expected_status"]
                            }
                            failed_endpoints.append(endpoint["path"])
                            
                except Exception as e:
                    endpoint_time = (time.time() - endpoint_start) * 1000
                    total_response_time += endpoint_time
                    results[endpoint["path"]] = {
                        "status": "error",
                        "response_time_ms": endpoint_time,
                        "error": str(e)
                    }
                    failed_endpoints.append(endpoint["path"])
            
            if failed_endpoints:
                return {
                    "error": f"Failed endpoints: {failed_endpoints}",
                    "message": f"API probe failed on {len(failed_endpoints)}/{len(self.endpoints_to_test)} endpoints",
                    "details": {
                        "endpoint_results": results,
                        "total_response_time_ms": total_response_time,
                        "failed_endpoints": failed_endpoints
                    }
                }
            else:
                return {
                    "message": f"All {len(self.endpoints_to_test)} API endpoints healthy",
                    "details": {
                        "endpoint_results": results,
                        "total_response_time_ms": total_response_time,
                        "avg_response_time_ms": total_response_time / len(self.endpoints_to_test)
                    }
                }


class SyntheticProbeRunner:
    """Orchestrates execution of all synthetic probes"""
    
    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url
        self.websocket_url = base_url.replace("http://", "ws://")
        
        self.probes = {
            "health": HealthProbe(base_url),
            "metrics": MetricsProbe(base_url), 
            "websocket": WebSocketProbe(self.websocket_url),
            "api": APIProbe(base_url)
        }
        
        # Track system health trends
        self.system_health_history = []
    
    async def run_all_probes(self) -> Dict[str, ProbeResult]:
        """Run all probes and return results"""
        results = {}
        
        # Execute probes concurrently
        probe_tasks = {
            name: probe.execute() 
            for name, probe in self.probes.items()
        }
        
        # Wait for all probes to complete
        completed_results = await asyncio.gather(
            *probe_tasks.values(),
            return_exceptions=True
        )
        
        # Map results back to probe names
        for i, (probe_name, _) in enumerate(probe_tasks.items()):
            result = completed_results[i]
            if isinstance(result, Exception):
                # Handle probe execution exceptions
                results[probe_name] = ProbeResult(
                    probe_name=probe_name,
                    status=ProbeStatus.ERROR,
                    response_time_ms=0,
                    timestamp=datetime.now(),
                    message=f"Probe execution failed",
                    error=str(result)
                )
            else:
                results[probe_name] = result
        
        # Update system health history
        self._update_system_health(results)
        
        return results
    
    def _update_system_health(self, results: Dict[str, ProbeResult]):
        """Update system health based on probe results"""
        healthy_probes = sum(1 for result in results.values() if result.status == ProbeStatus.HEALTHY)
        total_probes = len(results)
        
        system_health = {
            "timestamp": datetime.now(),
            "healthy_probes": healthy_probes,
            "total_probes": total_probes,
            "health_percentage": (healthy_probes / total_probes) * 100,
            "overall_status": self._determine_overall_status(results)
        }
        
        self.system_health_history.append(system_health)
        
        # Keep only last 100 health records
        if len(self.system_health_history) > 100:
            self.system_health_history.pop(0)
    
    def _determine_overall_status(self, results: Dict[str, ProbeResult]) -> ProbeStatus:
        """Determine overall system status from probe results"""
        # If any critical probes fail, system is unhealthy
        critical_probes = ["health", "websocket"]
        for probe_name in critical_probes:
            if probe_name in results and results[probe_name].status in [ProbeStatus.ERROR, ProbeStatus.TIMEOUT]:
                return ProbeStatus.UNHEALTHY
        
        # If majority of probes are unhealthy, system is unhealthy
        unhealthy_count = sum(
            1 for result in results.values() 
            if result.status in [ProbeStatus.ERROR, ProbeStatus.TIMEOUT, ProbeStatus.UNHEALTHY]
        )
        
        if unhealthy_count >= len(results) // 2:
            return ProbeStatus.UNHEALTHY
        
        # If any probe is degraded, system is degraded
        if any(result.status == ProbeStatus.DEGRADED for result in results.values()):
            return ProbeStatus.DEGRADED
        
        return ProbeStatus.HEALTHY
    
    def get_probe_summary(self) -> Dict[str, Any]:
        """Get summary of all probe health and trends"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "probes": {},
            "system_trends": {}
        }
        
        # Add individual probe summaries
        for name, probe in self.probes.items():
            if probe.history.results:
                latest_result = probe.history.results[-1]
                summary["probes"][name] = {
                    "status": latest_result.status.value,
                    "last_check": latest_result.timestamp.isoformat(),
                    "response_time_ms": latest_result.response_time_ms,
                    "success_rate_5m": probe.history.get_success_rate(5),
                    "avg_response_time_5m": probe.history.get_avg_response_time(5)
                }
            else:
                summary["probes"][name] = {
                    "status": "not_run",
                    "last_check": None,
                    "response_time_ms": 0,
                    "success_rate_5m": 0,
                    "avg_response_time_5m": 0
                }
        
        # Add system trends
        if self.system_health_history:
            recent_health = self.system_health_history[-10:]  # Last 10 measurements
            avg_health = sum(h["health_percentage"] for h in recent_health) / len(recent_health)
            
            summary["system_trends"] = {
                "avg_health_percentage": avg_health,
                "measurements_count": len(self.system_health_history),
                "trend": "stable"  # Could add trend analysis here
            }
        
        return summary


# Global probe runner instance
probe_runner = SyntheticProbeRunner()


async def run_synthetic_probes() -> Dict[str, ProbeResult]:
    """Convenience function to run all synthetic probes"""
    return await probe_runner.run_all_probes()


def get_probe_summary() -> Dict[str, Any]:
    """Convenience function to get probe summary"""
    return probe_runner.get_probe_summary()