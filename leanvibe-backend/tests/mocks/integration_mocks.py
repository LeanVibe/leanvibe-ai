"""
Enhanced Integration Testing Mocks

This module provides sophisticated mock implementations for integration testing
that simulate realistic service behavior, including:

1. Advanced MLX Service Mocks with Strategy Patterns
2. Neo4j Graph Database Mocks with Realistic Query Responses
3. WebSocket Connection Mocks with State Management
4. Event Streaming Mocks with Real-time Simulation
5. Performance-aware Mocks with Configurable Delays
6. Error Injection and Recovery Simulation
7. Multi-tenant Isolation Mocks
8. Health Monitoring Mocks with State Transitions
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from unittest.mock import AsyncMock, MagicMock, Mock
from dataclasses import dataclass
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class MockServiceState(Enum):
    """Mock service states for realistic behavior simulation"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    RECOVERING = "recovering"
    OFFLINE = "offline"


@dataclass
class MockServiceConfig:
    """Configuration for mock service behavior"""
    name: str
    base_response_time: float
    error_rate: float
    state: MockServiceState
    health_score: float
    resource_usage: Dict[str, float]
    capabilities: List[str]


class AdvancedMLXServiceMock:
    """Advanced MLX service mock with strategy pattern simulation"""
    
    def __init__(self):
        self.current_strategy = "production"
        self.available_strategies = {
            "production": MockServiceConfig(
                name="production",
                base_response_time=1.2,
                error_rate=0.02,
                state=MockServiceState.HEALTHY,
                health_score=0.95,
                resource_usage={"cpu": 45.0, "memory": 512.0},
                capabilities=["code_completion", "code_explanation", "refactoring"]
            ),
            "pragmatic": MockServiceConfig(
                name="pragmatic",
                base_response_time=0.8,
                error_rate=0.05,
                state=MockServiceState.HEALTHY,
                health_score=0.85,
                resource_usage={"cpu": 30.0, "memory": 256.0},
                capabilities=["code_completion", "basic_explanation"]
            ),
            "mock": MockServiceConfig(
                name="mock",
                base_response_time=0.1,
                error_rate=0.01,
                state=MockServiceState.HEALTHY,
                health_score=0.75,
                resource_usage={"cpu": 10.0, "memory": 64.0},
                capabilities=["code_completion"]
            )
        }
        
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "strategy_switches": 0
        }
        
        self.is_initialized = True
        
    async def initialize(self) -> bool:
        """Initialize the mock MLX service"""
        await asyncio.sleep(0.1)  # Simulate initialization time
        self.is_initialized = True
        return True
    
    async def generate_code_completion(self, context: Dict[str, Any], intent: str = "suggest") -> Dict[str, Any]:
        """Generate mock code completion response"""
        start_time = time.time()
        config = self.available_strategies[self.current_strategy]
        
        # Simulate processing time
        processing_time = config.base_response_time + random.uniform(-0.2, 0.3)
        await asyncio.sleep(processing_time * 0.01)  # Scale down for testing
        
        self.performance_metrics["total_requests"] += 1
        
        # Simulate error based on error rate
        if random.random() < config.error_rate:
            self.performance_metrics["failed_requests"] += 1
            return {
                "status": "error",
                "message": f"MLX {self.current_strategy} strategy failed",
                "confidence": 0.0
            }
        
        # Generate mock response based on intent and context
        response = self._generate_mock_response(intent, context)
        
        self.performance_metrics["successful_requests"] += 1
        actual_time = time.time() - start_time
        self._update_average_response_time(actual_time)
        
        return response
    
    def _generate_mock_response(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate appropriate mock response based on intent"""
        context_size = context.get("context_size", "medium")
        
        if intent == "suggest":
            if context_size == "small":
                response = "def function():\n    pass"
                confidence = 0.9
            elif context_size == "large":
                response = """class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f'{a} + {b} = {result}')
        return result"""
                confidence = 0.85
            else:
                response = "def calculate_sum(a, b):\n    return a + b"
                confidence = 0.88
                
        elif intent == "explain":
            response = f"This code implements a {context_size} complexity function that processes the given input and returns the appropriate result."
            confidence = 0.82
            
        elif intent == "refactor":
            response = "Consider extracting the business logic into a separate method and adding input validation."
            confidence = 0.79
            
        elif intent == "debug":
            response = "Potential issue: Missing null check on line 15. Consider adding input validation."
            confidence = 0.75
            
        else:
            response = f"Mock response for {intent} intent"
            confidence = 0.70
        
        return {
            "status": "success",
            "response": response,
            "confidence": confidence,
            "strategy": self.current_strategy,
            "processing_time": self.available_strategies[self.current_strategy].base_response_time
        }
    
    async def switch_strategy(self, new_strategy: str) -> bool:
        """Switch MLX strategy"""
        if new_strategy in self.available_strategies:
            old_strategy = self.current_strategy
            self.current_strategy = new_strategy
            self.performance_metrics["strategy_switches"] += 1
            logger.info(f"MLX strategy switched from {old_strategy} to {new_strategy}")
            return True
        return False
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get comprehensive model health information"""
        current_config = self.available_strategies[self.current_strategy]
        
        return {
            "health_score": current_config.health_score,
            "current_strategy": self.current_strategy,
            "strategy_availability": {
                name: config.state == MockServiceState.HEALTHY
                for name, config in self.available_strategies.items()
            },
            "enhanced_metrics": {
                "success_rate": self._calculate_success_rate(),
                "average_response_time": self.performance_metrics["average_response_time"],
                "strategy_switches": self.performance_metrics["strategy_switches"]
            },
            "capabilities": current_config.capabilities,
            "resource_usage": current_config.resource_usage
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        return self.performance_metrics.copy()
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate"""
        total = self.performance_metrics["total_requests"]
        if total == 0:
            return 1.0
        return self.performance_metrics["successful_requests"] / total
    
    def _update_average_response_time(self, new_time: float):
        """Update rolling average response time"""
        current_avg = self.performance_metrics["average_response_time"]
        total_requests = self.performance_metrics["total_requests"]
        
        # Simple rolling average
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total_requests - 1) + new_time) / total_requests
        )


class Neo4jGraphDatabaseMock:
    """Advanced Neo4j mock with realistic query responses"""
    
    def __init__(self):
        self.connected = False
        self.query_count = 0
        self.schema_initialized = False
        
        # Mock graph data
        self.nodes = {}
        self.relationships = []
        self.query_performance = {
            "simple_queries": [],
            "complex_queries": [],
            "failed_queries": 0
        }
        
        # Pre-populate with some test data
        self._initialize_test_data()
    
    async def connect(self) -> bool:
        """Mock database connection with realistic delay"""
        connection_time = random.uniform(0.5, 2.0)
        await asyncio.sleep(connection_time * 0.01)  # Scale down for testing
        
        # Simulate occasional connection failures
        if random.random() < 0.1:  # 10% failure rate
            self.connected = False
            return False
        
        self.connected = True
        await self._initialize_schema()
        return True
    
    async def disconnect(self):
        """Mock database disconnection"""
        self.connected = False
        self.schema_initialized = False
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connected
    
    async def _initialize_schema(self):
        """Mock schema initialization"""
        if not self.connected:
            return
        
        await asyncio.sleep(0.05)  # Simulate schema setup time
        self.schema_initialized = True
    
    async def add_code_node(self, node_data: Dict[str, Any]) -> bool:
        """Mock adding code node"""
        if not self.connected:
            return False
        
        node_id = node_data.get("id")
        if node_id:
            self.nodes[node_id] = node_data
            return True
        return False
    
    async def add_relationship(self, relationship_data: Dict[str, Any]) -> bool:
        """Mock adding relationship"""
        if not self.connected:
            return False
        
        self.relationships.append(relationship_data)
        return True
    
    async def get_dependencies(self, node_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        """Mock dependency query with realistic response"""
        query_start = time.time()
        
        if not self.connected:
            return []
        
        # Simulate query processing time
        await asyncio.sleep(0.1 * depth * 0.01)  # Deeper queries take longer
        
        # Generate mock dependencies
        dependencies = []
        dependency_count = min(random.randint(3, 15), depth * 5)
        
        for i in range(dependency_count):
            dep = {
                "id": f"dep_{i}_{node_id}",
                "name": f"Dependency{i}",
                "type": random.choice(["Class", "Function", "Module"]),
                "file_path": f"/project/src/dep_{i}.py",
                "distance": random.randint(1, depth),
                "relationships": [random.choice(["DEPENDS_ON", "CALLS", "USES"])]
            }
            dependencies.append(dep)
        
        query_time = time.time() - query_start
        self.query_performance["simple_queries"].append(query_time)
        self.query_count += 1
        
        return dependencies
    
    async def get_architecture_overview(self, project_id: str = None) -> Dict[str, Any]:
        """Mock architecture overview query"""
        query_start = time.time()
        
        if not self.connected:
            return {"error": "Not connected to database"}
        
        # Simulate complex query processing
        await asyncio.sleep(0.2 * 0.01)  # Scale down for testing
        
        # Generate comprehensive mock architecture data
        node_counts = {
            "File": random.randint(20, 100),
            "Class": random.randint(30, 150),
            "Function": random.randint(100, 400),
            "Method": random.randint(150, 600)
        }
        
        relationship_counts = {
            "CONTAINS": sum(node_counts.values()) // 2,
            "CALLS": random.randint(200, 800),
            "DEPENDS_ON": random.randint(150, 600),
            "USES": random.randint(100, 400)
        }
        
        # Generate hotspots (highly connected nodes)
        hotspots = []
        for i in range(random.randint(5, 15)):
            total_connections = random.randint(10, 50)
            hotspot = {
                "id": f"hotspot_{i}",
                "name": f"CentralComponent{i}",
                "type": random.choice(["Class", "Service", "Manager"]),
                "file_path": f"/project/core/central_{i}.py",
                "total_connections": total_connections,
                "outgoing_connections": random.randint(5, total_connections // 2),
                "incoming_connections": total_connections - random.randint(5, total_connections // 2)
            }
            hotspots.append(hotspot)
        
        # Calculate metrics
        total_nodes = sum(node_counts.values())
        total_relationships = sum(relationship_counts.values())
        density = total_relationships / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0
        
        query_time = time.time() - query_start
        self.query_performance["complex_queries"].append(query_time)
        self.query_count += 1
        
        return {
            "node_statistics": node_counts,
            "relationship_statistics": relationship_counts,
            "hotspots": hotspots,
            "metrics": {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "graph_density": density,
                "average_degree": (2 * total_relationships) / total_nodes if total_nodes > 0 else 0
            },
            "project_id": project_id
        }
    
    async def find_circular_dependencies(self, project_id: str = None, max_depth: int = 10) -> List[Dict[str, Any]]:
        """Mock circular dependency detection"""
        query_start = time.time()
        
        if not self.connected:
            return []
        
        # Simulate complex analysis
        await asyncio.sleep(0.3 * 0.01)  # Scale down for testing
        
        # Generate mock circular dependencies
        cycles = []
        cycle_count = random.randint(0, 5)  # Most projects have few cycles
        
        for i in range(cycle_count):
            cycle_length = random.randint(2, 6)
            cycle_nodes = []
            
            for j in range(cycle_length):
                cycle_nodes.append({
                    "id": f"cycle_{i}_node_{j}",
                    "name": f"Component{i}{j}",
                    "type": "Class"
                })
            
            # Close the cycle
            cycle_nodes.append(cycle_nodes[0])
            
            severity = "high" if cycle_length <= 3 else "medium" if cycle_length <= 5 else "low"
            
            cycles.append({
                "cycle": cycle_nodes,
                "length": cycle_length,
                "severity": severity
            })
        
        query_time = time.time() - query_start
        self.query_performance["complex_queries"].append(query_time)
        self.query_count += 1
        
        return cycles
    
    async def analyze_code_complexity(self, project_id: str = None) -> Dict[str, Any]:
        """Mock code complexity analysis"""
        query_start = time.time()
        
        if not self.connected:
            return {"error": "Not connected to database"}
        
        await asyncio.sleep(0.15 * 0.01)  # Scale down for testing
        
        # Generate mock complexity data
        complex_functions = []
        function_count = random.randint(10, 30)
        
        for i in range(function_count):
            complexity = random.randint(8, 25)  # Higher complexity functions
            complex_functions.append({
                "name": f"complex_function_{i}",
                "type": "Function",
                "file_path": f"/project/src/complex_{i}.py",
                "complexity": complexity,
                "lines_of_code": random.randint(50, 200)
            })
        
        # Sort by complexity
        complex_functions.sort(key=lambda x: x["complexity"], reverse=True)
        
        # File complexity
        complex_files = []
        for i in range(random.randint(5, 15)):
            avg_complexity = random.uniform(6.0, 15.0)
            complex_files.append({
                "file_path": f"/project/src/file_{i}.py",
                "symbol_count": random.randint(5, 20),
                "average_complexity": avg_complexity,
                "lines_of_code": random.randint(100, 500)
            })
        
        query_time = time.time() - query_start
        self.query_performance["complex_queries"].append(query_time)
        self.query_count += 1
        
        total_complexity = sum(f["complexity"] for f in complex_functions)
        
        return {
            "complex_functions": complex_functions[:20],  # Top 20
            "complex_files": complex_files,
            "summary": {
                "average_function_complexity": total_complexity / len(complex_functions) if complex_functions else 0,
                "total_functions_analyzed": len(complex_functions),
                "high_complexity_threshold": 10,
                "functions_above_threshold": len([f for f in complex_functions if f["complexity"] > 10])
            }
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Mock comprehensive health status"""
        if not self.connected:
            return {
                "status": "disconnected",
                "connected": False,
                "error": "Mock database not connected"
            }
        
        # Calculate performance metrics
        all_queries = self.query_performance["simple_queries"] + self.query_performance["complex_queries"]
        avg_query_time = sum(all_queries) / len(all_queries) if all_queries else 0
        
        return {
            "status": "connected",
            "connected": True,
            "schema_initialized": self.schema_initialized,
            "performance": {
                "query_response_time_ms": avg_query_time * 1000,
                "rating": "excellent" if avg_query_time < 0.1 else "good" if avg_query_time < 0.5 else "poor"
            },
            "statistics": {
                "total_nodes": len(self.nodes),
                "total_relationships": len(self.relationships),
                "queries_executed": self.query_count,
                "failed_queries": self.query_performance["failed_queries"]
            }
        }
    
    def _initialize_test_data(self):
        """Initialize mock test data"""
        # Add some sample nodes and relationships for testing
        sample_nodes = {
            "main_py": {"id": "main_py", "name": "main.py", "type": "File"},
            "user_class": {"id": "user_class", "name": "User", "type": "Class"},
            "get_user_func": {"id": "get_user_func", "name": "get_user", "type": "Function"}
        }
        
        self.nodes.update(sample_nodes)
        
        sample_relationships = [
            {"from_node": "main_py", "to_node": "user_class", "type": "CONTAINS"},
            {"from_node": "user_class", "to_node": "get_user_func", "type": "CONTAINS"}
        ]
        
        self.relationships.extend(sample_relationships)


class WebSocketConnectionMock:
    """Advanced WebSocket connection mock with state management"""
    
    def __init__(self):
        self.connections = {}
        self.message_queue = {}
        self.connection_states = {}
        self.performance_metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "connection_errors": 0
        }
        
    async def connect(self, websocket, client_id: str, is_reconnection: bool = False):
        """Mock WebSocket connection"""
        connection_start = time.time()
        
        # Simulate connection setup time
        await asyncio.sleep(0.05)
        
        # Simulate occasional connection failures
        if random.random() < 0.02:  # 2% connection failure rate
            self.performance_metrics["connection_errors"] += 1
            raise ConnectionError("Mock connection failed")
        
        self.connections[client_id] = {
            "websocket": websocket,
            "connected_at": datetime.now(),
            "is_reconnection": is_reconnection,
            "connection_time": time.time() - connection_start,
            "last_activity": datetime.now()
        }
        
        self.message_queue[client_id] = []
        self.connection_states[client_id] = "connected"
        
        self.performance_metrics["total_connections"] += 1
        self.performance_metrics["active_connections"] += 1
        
        logger.info(f"Mock WebSocket connection established for {client_id}")
    
    def disconnect(self, client_id: str):
        """Mock WebSocket disconnection"""
        if client_id in self.connections:
            del self.connections[client_id]
            if client_id in self.message_queue:
                del self.message_queue[client_id]
            if client_id in self.connection_states:
                self.connection_states[client_id] = "disconnected"
            
            self.performance_metrics["active_connections"] = max(0, self.performance_metrics["active_connections"] - 1)
            logger.info(f"Mock WebSocket connection closed for {client_id}")
    
    def is_connected(self, client_id: str) -> bool:
        """Check if client is connected"""
        return client_id in self.connections
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Mock sending message to specific client"""
        if not self.is_connected(client_id):
            raise ConnectionError(f"Client {client_id} not connected")
        
        # Simulate network latency
        await asyncio.sleep(random.uniform(0.001, 0.01))
        
        # Add message to client's queue
        self.message_queue[client_id].append({
            "message": message,
            "timestamp": datetime.now(),
            "direction": "outbound"
        })
        
        self.performance_metrics["messages_sent"] += 1
        
        # Update last activity
        if client_id in self.connections:
            self.connections[client_id]["last_activity"] = datetime.now()
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Mock broadcasting message to all connected clients"""
        broadcast_tasks = []
        
        for client_id in self.connections.keys():
            task = asyncio.create_task(self.send_to_client(client_id, message))
            broadcast_tasks.append(task)
        
        if broadcast_tasks:
            await asyncio.gather(*broadcast_tasks, return_exceptions=True)
    
    def receive_message(self, client_id: str, message: Dict[str, Any]):
        """Mock receiving message from client"""
        if client_id not in self.message_queue:
            self.message_queue[client_id] = []
        
        self.message_queue[client_id].append({
            "message": message,
            "timestamp": datetime.now(),
            "direction": "inbound"
        })
        
        self.performance_metrics["messages_received"] += 1
        
        # Update last activity
        if client_id in self.connections:
            self.connections[client_id]["last_activity"] = datetime.now()
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get comprehensive connection information"""
        return {
            "total_connections": self.performance_metrics["total_connections"],
            "active_connections": self.performance_metrics["active_connections"],
            "connected_clients": list(self.connections.keys()),
            "connection_states": self.connection_states.copy(),
            "performance_metrics": self.performance_metrics.copy(),
            "message_queues": {
                client_id: len(queue) 
                for client_id, queue in self.message_queue.items()
            }
        }
    
    def get_client_messages(self, client_id: str) -> List[Dict[str, Any]]:
        """Get messages for a specific client"""
        return self.message_queue.get(client_id, []).copy()


class EventStreamingMock:
    """Advanced event streaming mock with real-time simulation"""
    
    def __init__(self):
        self.started = False
        self.subscribers = {}
        self.event_queue = []
        self.processing_stats = {
            "total_events": 0,
            "events_processed": 0,
            "events_failed": 0,
            "events_per_second": 0.0,
            "last_processed": None
        }
        
        # Background event processing
        self._processing_task = None
        
    async def start(self):
        """Start the event streaming service"""
        if not self.started:
            self.started = True
            self._processing_task = asyncio.create_task(self._process_events())
            logger.info("Mock event streaming service started")
    
    async def stop(self):
        """Stop the event streaming service"""
        self.started = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        logger.info("Mock event streaming service stopped")
    
    async def emit_event(self, event_data: Dict[str, Any]):
        """Emit an event to the stream"""
        event = {
            "event_id": event_data.get("event_id", f"evt_{int(time.time() * 1000)}"),
            "event_type": event_data.get("event_type", "generic"),
            "priority": event_data.get("priority", "medium"),
            "timestamp": datetime.now(),
            "data": event_data.get("data", {}),
            "metadata": event_data.get("metadata", {})
        }
        
        self.event_queue.append(event)
        self.processing_stats["total_events"] += 1
        
    def subscribe(self, client_id: str, event_types: List[str], callback: Callable = None):
        """Subscribe client to specific event types"""
        self.subscribers[client_id] = {
            "event_types": event_types,
            "callback": callback,
            "subscribed_at": datetime.now(),
            "events_received": 0
        }
    
    def unsubscribe(self, client_id: str):
        """Unsubscribe client from events"""
        if client_id in self.subscribers:
            del self.subscribers[client_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event streaming statistics"""
        return {
            "service_started": self.started,
            "connected_clients": len(self.subscribers),
            "total_events_processed": self.processing_stats["events_processed"],
            "events_in_queue": len(self.event_queue),
            "events_per_second": self.processing_stats["events_per_second"],
            "failed_events": self.processing_stats["events_failed"],
            "last_processed": self.processing_stats["last_processed"]
        }
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about connected clients"""
        return {
            client_id: {
                "event_types": info["event_types"],
                "subscribed_at": info["subscribed_at"].isoformat(),
                "events_received": info["events_received"]
            }
            for client_id, info in self.subscribers.items()
        }
    
    async def _process_events(self):
        """Background task to process events"""
        while self.started:
            try:
                if self.event_queue:
                    # Process events in batches
                    batch_size = min(10, len(self.event_queue))
                    events_to_process = self.event_queue[:batch_size]
                    self.event_queue = self.event_queue[batch_size:]
                    
                    # Simulate event processing
                    for event in events_to_process:
                        await self._process_single_event(event)
                    
                    # Update statistics
                    self.processing_stats["events_processed"] += len(events_to_process)
                    self.processing_stats["last_processed"] = datetime.now()
                    self._update_events_per_second()
                
                # Process events every 100ms
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in event processing: {e}")
                self.processing_stats["events_failed"] += 1
    
    async def _process_single_event(self, event: Dict[str, Any]):
        """Process a single event"""
        event_type = event["event_type"]
        
        # Find interested subscribers
        interested_subscribers = [
            client_id for client_id, info in self.subscribers.items()
            if event_type in info["event_types"] or "*" in info["event_types"]
        ]
        
        # Deliver to subscribers
        for client_id in interested_subscribers:
            # Simulate event delivery
            await asyncio.sleep(0.001)  # Small delivery delay
            
            # Call callback if provided
            callback = self.subscribers[client_id].get("callback")
            if callback and asyncio.iscoroutinefunction(callback):
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback for {client_id}: {e}")
            
            self.subscribers[client_id]["events_received"] += 1
    
    def _update_events_per_second(self):
        """Update events per second calculation"""
        # Simple moving average over last 10 seconds
        now = time.time()
        if not hasattr(self, '_last_calculation_time'):
            self._last_calculation_time = now
            return
        
        time_diff = now - self._last_calculation_time
        if time_diff >= 1.0:  # Update every second
            events_in_period = self.processing_stats["events_processed"] - getattr(self, '_last_events_count', 0)
            self.processing_stats["events_per_second"] = events_in_period / time_diff
            self._last_calculation_time = now
            self._last_events_count = self.processing_stats["events_processed"]


class PerformanceMonitoringMock:
    """Mock for performance monitoring with realistic metrics"""
    
    def __init__(self):
        self.metrics_history = {
            "response_times": [],
            "throughput": [],
            "error_rates": [],
            "resource_usage": []
        }
        
        self.current_metrics = {
            "cpu_usage": 45.0,
            "memory_usage": 512.0,
            "disk_usage": 2048.0,
            "network_io": 150.0
        }
        
        # Simulate realistic metric variations
        self._start_metric_simulation()
    
    def record_response_time(self, service: str, operation: str, time_ms: float):
        """Record response time metric"""
        metric = {
            "timestamp": datetime.now(),
            "service": service,
            "operation": operation,
            "response_time_ms": time_ms
        }
        self.metrics_history["response_times"].append(metric)
        
        # Keep only last 1000 entries
        if len(self.metrics_history["response_times"]) > 1000:
            self.metrics_history["response_times"] = self.metrics_history["response_times"][-1000:]
    
    def record_throughput(self, service: str, requests_per_second: float):
        """Record throughput metric"""
        metric = {
            "timestamp": datetime.now(),
            "service": service,
            "rps": requests_per_second
        }
        self.metrics_history["throughput"].append(metric)
        
        if len(self.metrics_history["throughput"]) > 1000:
            self.metrics_history["throughput"] = self.metrics_history["throughput"][-1000:]
    
    def record_error_rate(self, service: str, error_rate: float):
        """Record error rate metric"""
        metric = {
            "timestamp": datetime.now(),
            "service": service,
            "error_rate": error_rate
        }
        self.metrics_history["error_rates"].append(metric)
        
        if len(self.metrics_history["error_rates"]) > 1000:
            self.metrics_history["error_rates"] = self.metrics_history["error_rates"][-1000:]
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        return self.current_metrics.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        # Calculate averages
        recent_response_times = self.metrics_history["response_times"][-100:]  # Last 100 entries
        avg_response_time = sum(m["response_time_ms"] for m in recent_response_times) / len(recent_response_times) if recent_response_times else 0
        
        recent_throughput = self.metrics_history["throughput"][-100:]
        avg_throughput = sum(m["rps"] for m in recent_throughput) / len(recent_throughput) if recent_throughput else 0
        
        recent_error_rates = self.metrics_history["error_rates"][-100:]
        avg_error_rate = sum(m["error_rate"] for m in recent_error_rates) / len(recent_error_rates) if recent_error_rates else 0
        
        return {
            "response_time": {
                "average_ms": avg_response_time,
                "p95_ms": self._calculate_percentile([m["response_time_ms"] for m in recent_response_times], 0.95),
                "p99_ms": self._calculate_percentile([m["response_time_ms"] for m in recent_response_times], 0.99)
            },
            "throughput": {
                "average_rps": avg_throughput,
                "peak_rps": max([m["rps"] for m in recent_throughput], default=0)
            },
            "reliability": {
                "average_error_rate": avg_error_rate,
                "uptime_percentage": 99.5 + random.uniform(-0.5, 0.5)  # Mock uptime
            },
            "resource_usage": self.current_metrics
        }
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from data"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(percentile * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _start_metric_simulation(self):
        """Start background metric simulation"""
        def update_metrics():
            while True:
                # Simulate realistic metric fluctuations
                self.current_metrics["cpu_usage"] = max(5.0, min(95.0, 
                    self.current_metrics["cpu_usage"] + random.uniform(-5, 5)))
                
                self.current_metrics["memory_usage"] = max(100.0, min(2048.0,
                    self.current_metrics["memory_usage"] + random.uniform(-50, 50)))
                
                self.current_metrics["disk_usage"] = max(1000.0, min(10000.0,
                    self.current_metrics["disk_usage"] + random.uniform(-100, 100)))
                
                self.current_metrics["network_io"] = max(10.0, min(1000.0,
                    self.current_metrics["network_io"] + random.uniform(-20, 20)))
                
                time.sleep(5)  # Update every 5 seconds
        
        # Start background thread
        thread = threading.Thread(target=update_metrics, daemon=True)
        thread.start()


# Global mock instances
mlx_service_mock = AdvancedMLXServiceMock()
neo4j_mock = Neo4jGraphDatabaseMock()
websocket_mock = WebSocketConnectionMock()
event_streaming_mock = EventStreamingMock()
performance_mock = PerformanceMonitoringMock()


def setup_integration_mocks():
    """Set up all integration test mocks"""
    logger.info("Setting up integration test mocks")
    
    # Initialize async mocks if needed
    asyncio.create_task(event_streaming_mock.start())
    
    return {
        "mlx_service": mlx_service_mock,
        "neo4j_service": neo4j_mock,
        "websocket_service": websocket_mock,
        "event_streaming": event_streaming_mock,
        "performance_monitor": performance_mock
    }


def teardown_integration_mocks():
    """Tear down integration test mocks"""
    logger.info("Tearing down integration test mocks")
    
    # Cleanup async resources
    try:
        asyncio.create_task(event_streaming_mock.stop())
    except Exception as e:
        logger.warning(f"Error stopping event streaming mock: {e}")


# Pytest fixtures for easy access
import pytest

@pytest.fixture
def advanced_mlx_mock():
    return mlx_service_mock

@pytest.fixture
def neo4j_database_mock():
    return neo4j_mock

@pytest.fixture
def websocket_connection_mock():
    return websocket_mock

@pytest.fixture
def event_streaming_mock_fixture():
    return event_streaming_mock

@pytest.fixture
def performance_monitoring_mock():
    return performance_mock

@pytest.fixture(scope="session")
def integration_mocks():
    mocks = setup_integration_mocks()
    yield mocks
    teardown_integration_mocks()


# Additional Mock Services for E2E Testing
class MockEmailService:
    """Mock email service for testing email verification and notifications"""
    
    def __init__(self):
        self.sent_emails = []
        self.verification_tokens = {}
        self.delivery_delay = 0.01
    
    async def send_verification_email(self, email: str, token: str) -> bool:
        """Send email verification"""
        self.verification_tokens[email] = token
        await asyncio.sleep(self.delivery_delay)
        self.sent_emails.append({
            "recipient": email,
            "subject": "Verify Your Email",
            "token": token,
            "sent_at": time.time()
        })
        return True
    
    async def get_verification_token(self, email: str) -> str:
        """Get verification token for email"""
        return self.verification_tokens.get(email, "mock_token_123")
    
    async def check_error_notifications(self, tenant_id: str) -> bool:
        """Check if error notifications were sent"""
        return True  # Mock always returns True
    
    def clear_emails(self):
        """Clear sent emails"""
        self.sent_emails.clear()
        self.verification_tokens.clear()


class MockAIService:
    """Mock AI service for testing ML/AI interactions"""
    
    def __init__(self):
        self.response_delay = 0.1
        self.generation_history = []
    
    async def analyze_interview(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock interview analysis"""
        await asyncio.sleep(self.response_delay)
        return {
            "complexity_score": 85.0,
            "feasibility_score": 90.0,
            "technical_requirements": {
                "estimated_dev_time": 6,
                "complexity_level": "medium"
            }
        }
    
    async def generate_blueprint(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Mock blueprint generation"""
        await asyncio.sleep(self.response_delay * 2)
        return {
            "architecture_type": "microservices",
            "components": [
                {"name": "frontend", "type": "React"},
                {"name": "backend", "type": "Node.js"},
                {"name": "database", "type": "PostgreSQL"}
            ]
        }
    
    async def generate_code_files(self, blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock code generation"""
        await asyncio.sleep(self.response_delay * 3)
        return [
            {
                "name": "app.js",
                "type": "source",
                "content": "// Mock generated code",
                "lines_of_code": 50
            },
            {
                "name": "app.test.js",
                "type": "test",
                "content": "// Mock test code",
                "lines_of_code": 25
            }
        ]
    
    def clear_history(self):
        """Clear generation history"""
        self.generation_history.clear()


class MockWebSocketClient:
    """Mock WebSocket client for testing real-time communication"""
    
    def __init__(self):
        self.connected = False
        self.messages = []
    
    async def connect(self, url: str) -> bool:
        """Mock WebSocket connection"""
        await asyncio.sleep(0.1)
        self.connected = True
        return True
    
    async def send(self, message: Dict[str, Any]) -> bool:
        """Send message"""
        if not self.connected:
            return False
        self.messages.append({"type": "sent", "data": message})
        return True
    
    async def receive(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Receive message"""
        await asyncio.sleep(0.1)
        return {"type": "ack", "status": "received"}
    
    async def disconnect(self):
        """Disconnect"""
        self.connected = False


class MockRedisClient:
    """Mock Redis client for caching"""
    
    def __init__(self):
        self.data = {}
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to Redis"""
        self.connected = True
        return True
    
    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        """Set value"""
        self.data[key] = value
        return True
    
    async def get(self, key: str) -> Any:
        """Get value"""
        return self.data.get(key)
    
    def clear_all(self):
        """Clear all data"""
        self.data.clear()


class MockFileSystemService:
    """Mock file system service"""
    
    def __init__(self):
        self.files = {}
    
    async def write_file(self, path: str, content: bytes) -> bool:
        """Write file"""
        self.files[path] = content
        return True
    
    async def read_file(self, path: str) -> bytes:
        """Read file"""
        return self.files.get(path, b"mock file content")
    
    def clear_all(self):
        """Clear all files"""
        self.files.clear()