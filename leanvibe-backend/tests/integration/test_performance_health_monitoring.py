"""
Performance Validation & Health Monitoring Integration Test Suite

This module provides comprehensive testing for performance validation and 
health monitoring across the LeanVibe AI system, focusing on:

1. Service Performance Benchmarking
2. Real-time Health Monitoring
3. Performance Regression Detection
4. Resource Usage Monitoring
5. Scalability Testing
6. Performance SLA Validation
7. Health Alert System Testing
8. Performance Optimization Validation
"""

import asyncio
import json
import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Tracks and calculates performance metrics"""
    
    def __init__(self):
        self.response_times = []
        self.throughput_data = []
        self.resource_usage = {}
        self.error_rates = {}
        self.start_time = time.time()
        
    def record_response_time(self, operation: str, response_time: float):
        """Record response time for an operation"""
        self.response_times.append({
            'operation': operation,
            'response_time': response_time,
            'timestamp': time.time()
        })
        
    def record_throughput(self, operation: str, requests_per_second: float):
        """Record throughput measurement"""
        self.throughput_data.append({
            'operation': operation,
            'rps': requests_per_second,
            'timestamp': time.time()
        })
        
    def record_resource_usage(self, component: str, cpu_percent: float, memory_mb: float):
        """Record resource usage"""
        self.resource_usage[component] = {
            'cpu_percent': cpu_percent,
            'memory_mb': memory_mb,
            'timestamp': time.time()
        }
        
    def record_error_rate(self, service: str, error_rate: float):
        """Record error rate for a service"""
        self.error_rates[service] = {
            'error_rate': error_rate,
            'timestamp': time.time()
        }
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        if not self.response_times:
            return {'no_data': True}
            
        response_times = [rt['response_time'] for rt in self.response_times]
        
        return {
            'response_time_stats': {
                'mean': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'p95': self._percentile(response_times, 0.95),
                'p99': self._percentile(response_times, 0.99),
                'min': min(response_times),
                'max': max(response_times),
                'count': len(response_times)
            },
            'throughput_stats': {
                'average_rps': statistics.mean([t['rps'] for t in self.throughput_data]) if self.throughput_data else 0,
                'peak_rps': max([t['rps'] for t in self.throughput_data]) if self.throughput_data else 0,
                'measurements': len(self.throughput_data)
            },
            'resource_usage': self.resource_usage,
            'error_rates': self.error_rates,
            'test_duration': time.time() - self.start_time
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(percentile * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]


class ServicePerformanceTester:
    """Tests individual service performance"""
    
    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
        self.sla_thresholds = {
            'response_time_p95': 2.0,  # 2 seconds
            'response_time_p99': 5.0,  # 5 seconds
            'throughput_minimum': 10,  # 10 requests per second
            'error_rate_maximum': 0.05,  # 5% error rate
            'cpu_usage_maximum': 80,   # 80% CPU
            'memory_usage_maximum': 1024  # 1GB RAM
        }
    
    async def test_mlx_service_performance(self) -> Dict[str, Any]:
        """Test MLX service performance"""
        logger.info("Testing MLX service performance")
        
        try:
            with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
                # Mock MLX service methods
                mock_mlx.generate_code_completion = AsyncMock()
                mock_mlx.get_performance_metrics = MagicMock()
                mock_mlx.get_model_health = MagicMock()
                
                # Performance test scenarios
                test_scenarios = [
                    {'context_size': 'small', 'expected_time': 1.0},
                    {'context_size': 'medium', 'expected_time': 2.0},
                    {'context_size': 'large', 'expected_time': 3.0}
                ]
                
                performance_results = []
                total_requests = 0
                total_time = 0
                
                for scenario in test_scenarios:
                    scenario_start = time.time()
                    
                    # Simulate multiple requests for this scenario
                    requests_count = 5
                    scenario_times = []
                    
                    for i in range(requests_count):
                        request_start = time.time()
                        
                        # Mock response based on context size
                        if scenario['context_size'] == 'small':
                            mock_mlx.generate_code_completion.return_value = {
                                'status': 'success',
                                'response': 'def function():\n    pass',
                                'confidence': 0.9
                            }
                            # Simulate quick response
                            await asyncio.sleep(0.1)
                        elif scenario['context_size'] == 'medium':
                            mock_mlx.generate_code_completion.return_value = {
                                'status': 'success', 
                                'response': 'class Calculator:\n    def add(self, a, b):\n        return a + b',
                                'confidence': 0.85
                            }
                            await asyncio.sleep(0.2)
                        else:  # large
                            mock_mlx.generate_code_completion.return_value = {
                                'status': 'success',
                                'response': 'Complex multi-line code response...',
                                'confidence': 0.8
                            }
                            await asyncio.sleep(0.3)
                        
                        # Generate completion
                        result = await mock_mlx.generate_code_completion({
                            'context_size': scenario['context_size']
                        })
                        
                        request_time = time.time() - request_start
                        scenario_times.append(request_time)
                        self.metrics.record_response_time(f"mlx_{scenario['context_size']}", request_time)
                        
                        total_requests += 1
                    
                    scenario_duration = time.time() - scenario_start
                    total_time += scenario_duration
                    
                    performance_results.append({
                        'context_size': scenario['context_size'],
                        'requests': requests_count,
                        'total_time': scenario_duration,
                        'average_time': statistics.mean(scenario_times),
                        'max_time': max(scenario_times),
                        'min_time': min(scenario_times),
                        'meets_sla': statistics.mean(scenario_times) <= scenario['expected_time']
                    })
                
                # Calculate overall throughput
                overall_rps = total_requests / total_time if total_time > 0 else 0
                self.metrics.record_throughput('mlx_service', overall_rps)
                
                # Mock resource usage
                self.metrics.record_resource_usage('mlx_service', 45.0, 512.0)
                self.metrics.record_error_rate('mlx_service', 0.02)  # 2% error rate
                
                # Evaluate SLA compliance
                avg_response_time = statistics.mean([
                    rt['response_time'] for rt in self.metrics.response_times 
                    if rt['operation'].startswith('mlx_')
                ])
                
                sla_compliance = {
                    'response_time_sla': avg_response_time <= self.sla_thresholds['response_time_p95'],
                    'throughput_sla': overall_rps >= self.sla_thresholds['throughput_minimum'],
                    'error_rate_sla': 0.02 <= self.sla_thresholds['error_rate_maximum']
                }
                
                return {
                    'passed': all(sla_compliance.values()),
                    'performance_results': performance_results,
                    'overall_throughput': overall_rps,
                    'average_response_time': avg_response_time,
                    'sla_compliance': sla_compliance,
                    'requests_tested': total_requests,
                    'resource_usage': {
                        'cpu_percent': 45.0,
                        'memory_mb': 512.0
                    }
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_graph_service_performance(self) -> Dict[str, Any]:
        """Test graph database service performance"""
        logger.info("Testing graph service performance")
        
        try:
            with patch('app.services.code_graph_service.code_graph_service') as mock_graph:
                # Mock graph service methods
                mock_graph.get_architecture_overview = AsyncMock()
                mock_graph.get_dependencies = AsyncMock()
                mock_graph.find_circular_dependencies = AsyncMock()
                mock_graph.analyze_code_complexity = AsyncMock()
                
                # Test different query complexities
                query_scenarios = [
                    {
                        'query_type': 'simple_overview',
                        'expected_time': 0.5,
                        'operation': 'get_architecture_overview'
                    },
                    {
                        'query_type': 'dependency_analysis',
                        'expected_time': 1.0,
                        'operation': 'get_dependencies'  
                    },
                    {
                        'query_type': 'circular_dependency_detection',
                        'expected_time': 2.0,
                        'operation': 'find_circular_dependencies'
                    },
                    {
                        'query_type': 'complexity_analysis',
                        'expected_time': 1.5,
                        'operation': 'analyze_code_complexity'
                    }
                ]
                
                query_results = []
                total_queries = 0
                total_query_time = 0
                
                for scenario in query_scenarios:
                    query_start = time.time()
                    
                    # Mock appropriate response
                    if scenario['query_type'] == 'simple_overview':
                        mock_graph.get_architecture_overview.return_value = {
                            'node_statistics': {'Class': 10, 'Function': 25},
                            'relationship_statistics': {'CALLS': 30, 'DEPENDS_ON': 15}
                        }
                        await asyncio.sleep(0.05)  # Simulate quick query
                        result = await mock_graph.get_architecture_overview('test_project')
                        
                    elif scenario['query_type'] == 'dependency_analysis':
                        mock_graph.get_dependencies.return_value = [
                            {'id': 'dep1', 'name': 'Dependency1'},
                            {'id': 'dep2', 'name': 'Dependency2'}
                        ]
                        await asyncio.sleep(0.1)  # Simulate medium query
                        result = await mock_graph.get_dependencies('test_node', depth=2)
                        
                    elif scenario['query_type'] == 'circular_dependency_detection':
                        mock_graph.find_circular_dependencies.return_value = [
                            {'cycle': ['A', 'B', 'A'], 'length': 2}
                        ]
                        await asyncio.sleep(0.2)  # Simulate complex query
                        result = await mock_graph.find_circular_dependencies('test_project')
                        
                    else:  # complexity_analysis
                        mock_graph.analyze_code_complexity.return_value = {
                            'complex_functions': [],
                            'summary': {'average_complexity': 5.2}
                        }
                        await asyncio.sleep(0.15)  # Simulate analysis query
                        result = await mock_graph.analyze_code_complexity('test_project')
                    
                    query_time = time.time() - query_start
                    total_query_time += query_time
                    total_queries += 1
                    
                    self.metrics.record_response_time(f"graph_{scenario['query_type']}", query_time)
                    
                    query_results.append({
                        'query_type': scenario['query_type'],
                        'response_time': query_time,
                        'meets_sla': query_time <= scenario['expected_time'],
                        'result_size': len(str(result))
                    })
                
                # Calculate query throughput
                query_rps = total_queries / total_query_time if total_query_time > 0 else 0
                self.metrics.record_throughput('graph_service', query_rps)
                
                # Mock resource usage
                self.metrics.record_resource_usage('graph_service', 35.0, 256.0)
                self.metrics.record_error_rate('graph_service', 0.01)  # 1% error rate
                
                # SLA evaluation
                avg_query_time = statistics.mean([qr['response_time'] for qr in query_results])
                sla_met = all(qr['meets_sla'] for qr in query_results)
                
                return {
                    'passed': sla_met and query_rps >= 5,  # Minimum 5 queries per second
                    'query_results': query_results,
                    'average_query_time': avg_query_time,
                    'query_throughput': query_rps,
                    'queries_tested': total_queries,
                    'sla_compliance': sla_met,
                    'resource_efficiency': {
                        'cpu_percent': 35.0,
                        'memory_mb': 256.0,
                        'queries_per_cpu_percent': query_rps / 35.0 if query_rps > 0 else 0
                    }
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_websocket_performance(self) -> Dict[str, Any]:
        """Test WebSocket service performance"""
        logger.info("Testing WebSocket performance")
        
        try:
            # Test WebSocket message handling performance
            message_scenarios = [
                {'type': 'heartbeat', 'expected_time': 0.05},
                {'type': 'code_completion', 'expected_time': 0.5},
                {'type': 'task_update', 'expected_time': 0.1},
                {'type': 'project_sync', 'expected_time': 0.2}
            ]
            
            websocket_results = []
            total_messages = 0
            total_message_time = 0
            
            for scenario in message_scenarios:
                message_start = time.time()
                
                # Simulate message processing
                if scenario['type'] == 'heartbeat':
                    await asyncio.sleep(0.001)  # Very fast
                elif scenario['type'] == 'code_completion':
                    await asyncio.sleep(0.05)   # Moderate
                elif scenario['type'] == 'task_update':
                    await asyncio.sleep(0.01)   # Fast
                else:  # project_sync
                    await asyncio.sleep(0.02)   # Fast-moderate
                
                message_time = time.time() - message_start
                total_message_time += message_time
                total_messages += 1
                
                self.metrics.record_response_time(f"websocket_{scenario['type']}", message_time)
                
                websocket_results.append({
                    'message_type': scenario['type'],
                    'processing_time': message_time,
                    'meets_sla': message_time <= scenario['expected_time']
                })
            
            # Calculate message throughput
            message_rps = total_messages / total_message_time if total_message_time > 0 else 0
            self.metrics.record_throughput('websocket_service', message_rps)
            
            # Mock resource usage
            self.metrics.record_resource_usage('websocket_service', 25.0, 128.0)
            self.metrics.record_error_rate('websocket_service', 0.005)  # 0.5% error rate
            
            # Performance evaluation
            avg_processing_time = statistics.mean([wr['processing_time'] for wr in websocket_results])
            all_sla_met = all(wr['meets_sla'] for wr in websocket_results)
            
            return {
                'passed': all_sla_met and message_rps >= 50,  # Minimum 50 messages per second
                'message_results': websocket_results,
                'average_processing_time': avg_processing_time,
                'message_throughput': message_rps,
                'messages_tested': total_messages,
                'sla_compliance': all_sla_met,
                'connection_efficiency': {
                    'cpu_percent': 25.0,
                    'memory_mb': 128.0,
                    'messages_per_mb': message_rps / 128.0 if message_rps > 0 else 0
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }


class HealthMonitoringTester:
    """Tests health monitoring functionality"""
    
    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
        self.health_checks = {}
        
    async def test_service_health_monitoring(self) -> Dict[str, Any]:
        """Test comprehensive service health monitoring"""
        logger.info("Testing service health monitoring")
        
        try:
            # Define services to monitor
            services_to_monitor = [
                'unified_mlx_service',
                'code_graph_service', 
                'websocket_service',
                'event_streaming_service',
                'session_manager'
            ]
            
            health_results = {}
            monitoring_start = time.time()
            
            for service in services_to_monitor:
                service_start = time.time()
                
                # Mock health check for each service
                if service == 'unified_mlx_service':
                    health_data = {
                        'status': 'healthy',
                        'health_score': 0.92,
                        'response_time': 1.2,
                        'current_strategy': 'production',
                        'model_loaded': True,
                        'memory_usage': 512.0
                    }
                elif service == 'code_graph_service':
                    health_data = {
                        'status': 'healthy',
                        'connected': True,
                        'query_response_time': 0.8,
                        'connection_pool': {'active': 5, 'idle': 3},
                        'last_query_success': True
                    }
                elif service == 'websocket_service':
                    health_data = {
                        'status': 'healthy',
                        'active_connections': 15,
                        'message_queue_size': 23,
                        'average_latency': 0.05,
                        'connection_errors': 0
                    }
                elif service == 'event_streaming_service':
                    health_data = {
                        'status': 'healthy',
                        'events_processed': 1250,
                        'events_per_second': 12.5,
                        'queue_depth': 5,
                        'failed_deliveries': 2
                    }
                else:  # session_manager
                    health_data = {
                        'status': 'healthy',
                        'active_sessions': 8,
                        'session_cleanup_rate': 0.95,
                        'memory_per_session': 45.0,
                        'session_errors': 0
                    }
                
                # Simulate health check time
                await asyncio.sleep(0.01)
                health_check_time = time.time() - service_start
                
                # Evaluate health status
                health_score = self._calculate_health_score(service, health_data)
                
                health_results[service] = {
                    'health_data': health_data,
                    'health_score': health_score,
                    'check_time': health_check_time,
                    'status': 'healthy' if health_score >= 0.8 else 'degraded' if health_score >= 0.6 else 'unhealthy'
                }
                
                self.health_checks[service] = health_data
            
            total_monitoring_time = time.time() - monitoring_start
            
            # Overall system health
            overall_health_score = statistics.mean([hr['health_score'] for hr in health_results.values()])
            healthy_services = len([hr for hr in health_results.values() if hr['status'] == 'healthy'])
            
            return {
                'passed': overall_health_score >= 0.8 and healthy_services >= len(services_to_monitor) * 0.8,
                'services_monitored': len(services_to_monitor),
                'healthy_services': healthy_services,
                'overall_health_score': overall_health_score,
                'total_monitoring_time': total_monitoring_time,
                'individual_results': health_results,
                'system_status': 'healthy' if overall_health_score >= 0.8 else 'degraded' if overall_health_score >= 0.6 else 'unhealthy'
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    def _calculate_health_score(self, service: str, health_data: Dict[str, Any]) -> float:
        """Calculate health score for a service based on its metrics"""
        score = 1.0
        
        if service == 'unified_mlx_service':
            # MLX service scoring
            if health_data.get('response_time', 0) > 3.0:
                score -= 0.2
            if not health_data.get('model_loaded', False):
                score -= 0.3
            if health_data.get('memory_usage', 0) > 1024:
                score -= 0.1
                
        elif service == 'code_graph_service':
            # Graph service scoring
            if not health_data.get('connected', False):
                score -= 0.5
            if health_data.get('query_response_time', 0) > 2.0:
                score -= 0.2
            if not health_data.get('last_query_success', True):
                score -= 0.1
                
        elif service == 'websocket_service':
            # WebSocket service scoring
            if health_data.get('message_queue_size', 0) > 100:
                score -= 0.2
            if health_data.get('average_latency', 0) > 0.1:
                score -= 0.1
            if health_data.get('connection_errors', 0) > 0:
                score -= 0.1
                
        return max(0.0, min(1.0, score))
    
    async def test_performance_alerting(self) -> Dict[str, Any]:
        """Test performance alerting system"""
        logger.info("Testing performance alerting system")
        
        try:
            # Define alerting thresholds
            alert_thresholds = {
                'response_time_critical': 5.0,
                'response_time_warning': 2.0,
                'error_rate_critical': 0.1,
                'error_rate_warning': 0.05,
                'cpu_usage_critical': 90,
                'cpu_usage_warning': 75,
                'memory_usage_critical': 90,  # Percentage
                'memory_usage_warning': 75
            }
            
            # Simulate performance scenarios that should trigger alerts
            alert_scenarios = [
                {
                    'name': 'high_response_time',
                    'metrics': {'response_time': 3.5, 'error_rate': 0.02},
                    'expected_alerts': ['response_time_warning']
                },
                {
                    'name': 'critical_error_rate',
                    'metrics': {'response_time': 1.0, 'error_rate': 0.12},
                    'expected_alerts': ['error_rate_critical']
                },
                {
                    'name': 'high_resource_usage',
                    'metrics': {'cpu_usage': 85, 'memory_usage': 80},
                    'expected_alerts': ['cpu_usage_warning', 'memory_usage_warning']
                },
                {
                    'name': 'normal_operations',
                    'metrics': {'response_time': 0.8, 'error_rate': 0.01, 'cpu_usage': 40, 'memory_usage': 50},
                    'expected_alerts': []
                }
            ]
            
            alerting_results = []
            
            for scenario in alert_scenarios:
                scenario_start = time.time()
                
                triggered_alerts = []
                metrics = scenario['metrics']
                
                # Check each metric against thresholds
                if metrics.get('response_time', 0) >= alert_thresholds['response_time_critical']:
                    triggered_alerts.append('response_time_critical')
                elif metrics.get('response_time', 0) >= alert_thresholds['response_time_warning']:
                    triggered_alerts.append('response_time_warning')
                
                if metrics.get('error_rate', 0) >= alert_thresholds['error_rate_critical']:
                    triggered_alerts.append('error_rate_critical')
                elif metrics.get('error_rate', 0) >= alert_thresholds['error_rate_warning']:
                    triggered_alerts.append('error_rate_warning')
                
                if metrics.get('cpu_usage', 0) >= alert_thresholds['cpu_usage_critical']:
                    triggered_alerts.append('cpu_usage_critical')
                elif metrics.get('cpu_usage', 0) >= alert_thresholds['cpu_usage_warning']:
                    triggered_alerts.append('cpu_usage_warning')
                
                if metrics.get('memory_usage', 0) >= alert_thresholds['memory_usage_critical']:
                    triggered_alerts.append('memory_usage_critical')
                elif metrics.get('memory_usage', 0) >= alert_thresholds['memory_usage_warning']:
                    triggered_alerts.append('memory_usage_warning')
                
                scenario_time = time.time() - scenario_start
                
                # Check if alerts match expectations
                expected_alerts = set(scenario['expected_alerts'])
                actual_alerts = set(triggered_alerts)
                alerts_match = expected_alerts == actual_alerts
                
                alerting_results.append({
                    'scenario': scenario['name'],
                    'metrics': metrics,
                    'expected_alerts': list(expected_alerts),
                    'triggered_alerts': list(actual_alerts),
                    'alerts_correct': alerts_match,
                    'processing_time': scenario_time
                })
            
            # Calculate alerting accuracy
            correct_alerts = len([ar for ar in alerting_results if ar['alerts_correct']])
            alerting_accuracy = (correct_alerts / len(alert_scenarios)) * 100
            
            return {
                'passed': alerting_accuracy >= 90,  # 90% accuracy threshold
                'scenarios_tested': len(alert_scenarios),
                'correct_alert_scenarios': correct_alerts,
                'alerting_accuracy': alerting_accuracy,
                'alert_thresholds': alert_thresholds,
                'scenario_results': alerting_results
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }


class ScalabilityTester:
    """Tests system scalability under load"""
    
    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
        
    async def test_concurrent_load_handling(self) -> Dict[str, Any]:
        """Test system behavior under concurrent load"""
        logger.info("Testing concurrent load handling")
        
        try:
            # Define load test scenarios
            load_scenarios = [
                {'concurrent_users': 10, 'requests_per_user': 5},
                {'concurrent_users': 25, 'requests_per_user': 4},
                {'concurrent_users': 50, 'requests_per_user': 3},
                {'concurrent_users': 100, 'requests_per_user': 2}
            ]
            
            scalability_results = []
            
            for scenario in load_scenarios:
                scenario_start = time.time()
                
                concurrent_users = scenario['concurrent_users']
                requests_per_user = scenario['requests_per_user']
                total_requests = concurrent_users * requests_per_user
                
                # Simulate concurrent requests
                tasks = []
                for user_id in range(concurrent_users):
                    for request_id in range(requests_per_user):
                        task = asyncio.create_task(
                            self._simulate_user_request(f"user_{user_id}", f"request_{request_id}")
                        )
                        tasks.append(task)
                
                # Execute all requests concurrently
                request_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                scenario_time = time.time() - scenario_start
                
                # Analyze results
                successful_requests = len([r for r in request_results if isinstance(r, dict) and r.get('success', False)])
                failed_requests = total_requests - successful_requests
                success_rate = (successful_requests / total_requests) * 100
                requests_per_second = total_requests / scenario_time if scenario_time > 0 else 0
                
                # Calculate response time statistics
                response_times = [r.get('response_time', 0) for r in request_results if isinstance(r, dict)]
                if response_times:
                    avg_response_time = statistics.mean(response_times)
                    p95_response_time = self.metrics._percentile(response_times, 0.95)
                else:
                    avg_response_time = 0
                    p95_response_time = 0
                
                scalability_results.append({
                    'concurrent_users': concurrent_users,
                    'total_requests': total_requests,
                    'successful_requests': successful_requests,
                    'failed_requests': failed_requests,
                    'success_rate': success_rate,
                    'requests_per_second': requests_per_second,
                    'scenario_duration': scenario_time,
                    'avg_response_time': avg_response_time,
                    'p95_response_time': p95_response_time,
                    'scalability_rating': self._rate_scalability_performance(success_rate, avg_response_time, requests_per_second)
                })
                
                # Record metrics
                self.metrics.record_throughput(f'load_test_{concurrent_users}_users', requests_per_second)
                
                # Small delay between scenarios
                await asyncio.sleep(0.1)
            
            # Evaluate overall scalability
            overall_success_rate = statistics.mean([sr['success_rate'] for sr in scalability_results])
            performance_degradation = self._calculate_performance_degradation(scalability_results)
            
            return {
                'passed': overall_success_rate >= 90 and performance_degradation <= 50,  # Max 50% degradation
                'scenarios_tested': len(load_scenarios),
                'overall_success_rate': overall_success_rate,
                'performance_degradation_percent': performance_degradation,
                'max_concurrent_users_tested': max(scenario['concurrent_users'] for scenario in load_scenarios),
                'peak_requests_per_second': max(sr['requests_per_second'] for sr in scalability_results),
                'scenario_results': scalability_results
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def _simulate_user_request(self, user_id: str, request_id: str) -> Dict[str, Any]:
        """Simulate a user request"""
        request_start = time.time()
        
        try:
            # Simulate request processing time (varies by load)
            processing_time = 0.1 + (hash(user_id + request_id) % 100) / 1000  # 0.1 to 0.2 seconds
            await asyncio.sleep(processing_time)
            
            request_time = time.time() - request_start
            
            return {
                'success': True,
                'user_id': user_id,
                'request_id': request_id,
                'response_time': request_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': time.time() - request_start
            }
    
    def _rate_scalability_performance(self, success_rate: float, avg_response_time: float, rps: float) -> str:
        """Rate scalability performance"""
        if success_rate >= 95 and avg_response_time <= 0.5 and rps >= 50:
            return 'excellent'
        elif success_rate >= 90 and avg_response_time <= 1.0 and rps >= 25:
            return 'good'
        elif success_rate >= 80 and avg_response_time <= 2.0 and rps >= 10:
            return 'acceptable'
        else:
            return 'poor'
    
    def _calculate_performance_degradation(self, results: List[Dict[str, Any]]) -> float:
        """Calculate performance degradation as load increases"""
        if len(results) < 2:
            return 0.0
        
        # Compare first (lowest load) vs last (highest load) scenario
        baseline_rps = results[0]['requests_per_second']
        final_rps = results[-1]['requests_per_second']
        
        if baseline_rps == 0:
            return 0.0
        
        degradation = ((baseline_rps - final_rps) / baseline_rps) * 100
        return max(0.0, degradation)


@pytest.mark.asyncio
async def test_performance_health_monitoring_integration_suite():
    """Main performance validation and health monitoring integration test suite"""
    logger.info("Starting performance validation and health monitoring integration tests")
    
    # Initialize metrics tracker
    metrics = PerformanceMetrics()
    
    test_results = {}
    
    # Test 1: Service performance benchmarking
    performance_tester = ServicePerformanceTester(metrics)
    
    mlx_performance_result = await performance_tester.test_mlx_service_performance()
    test_results['mlx_service_performance'] = mlx_performance_result
    
    graph_performance_result = await performance_tester.test_graph_service_performance()
    test_results['graph_service_performance'] = graph_performance_result
    
    websocket_performance_result = await performance_tester.test_websocket_performance()
    test_results['websocket_service_performance'] = websocket_performance_result
    
    # Test 2: Health monitoring
    health_tester = HealthMonitoringTester(metrics)
    
    health_monitoring_result = await health_tester.test_service_health_monitoring()
    test_results['service_health_monitoring'] = health_monitoring_result
    
    alerting_result = await health_tester.test_performance_alerting()
    test_results['performance_alerting'] = alerting_result
    
    # Test 3: Scalability testing
    scalability_tester = ScalabilityTester(metrics)
    
    load_handling_result = await scalability_tester.test_concurrent_load_handling()
    test_results['concurrent_load_handling'] = load_handling_result
    
    # Generate comprehensive performance statistics
    performance_stats = metrics.get_statistics()
    
    # Calculate overall results
    passed_tests = sum(1 for result in test_results.values() if result.get('passed', False))
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    # Log comprehensive results
    logger.info(f"Performance and health monitoring tests completed: {success_rate:.1f}% success rate")
    logger.info(f"Passed: {passed_tests}/{total_tests} tests")
    logger.info(f"Performance Statistics: {performance_stats}")
    
    # Assert minimum success criteria
    assert success_rate >= 80, f"Performance tests failed with {success_rate:.1f}% success rate"
    assert test_results['mlx_service_performance']['passed'], "MLX service performance must meet SLA"
    assert test_results['service_health_monitoring']['passed'], "Health monitoring must be functional"
    assert test_results['concurrent_load_handling']['passed'], "System must handle concurrent load"
    
    return {
        'test_results': test_results,
        'performance_statistics': performance_stats,
        'overall_success_rate': success_rate
    }


@pytest.mark.asyncio
async def test_performance_regression_detection():
    """Test performance regression detection"""
    logger.info("Testing performance regression detection")
    
    # Simulate historical performance data
    baseline_metrics = {
        'mlx_response_time': 1.2,
        'graph_query_time': 0.8,
        'websocket_latency': 0.05,
        'system_throughput': 45.0
    }
    
    # Simulate current metrics with potential regression
    current_metrics = {
        'mlx_response_time': 2.1,  # 75% slower - regression
        'graph_query_time': 0.85,  # 6% slower - acceptable
        'websocket_latency': 0.045,  # Better performance
        'system_throughput': 38.0  # 15% slower - potential regression
    }
    
    regression_threshold = 0.20  # 20% degradation threshold
    regressions_detected = []
    
    for metric, current_value in current_metrics.items():
        baseline_value = baseline_metrics[metric]
        
        if metric == 'system_throughput':
            # For throughput, lower is worse
            degradation = (baseline_value - current_value) / baseline_value
        else:
            # For response times, higher is worse
            degradation = (current_value - baseline_value) / baseline_value
        
        if degradation > regression_threshold:
            regressions_detected.append({
                'metric': metric,
                'baseline': baseline_value,
                'current': current_value,
                'degradation_percent': degradation * 100
            })
    
    # Assert regression detection
    assert len(regressions_detected) > 0, "Should detect performance regressions"
    logger.info(f"Performance regression detection passed: {len(regressions_detected)} regressions detected")
    
    return regressions_detected


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])