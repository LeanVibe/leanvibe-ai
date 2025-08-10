"""
Integration Test Fixtures

This module provides comprehensive test fixtures and mock data for integration
testing across the LeanVibe AI system. These fixtures support realistic 
testing scenarios for:

1. Code Analysis & Graph Data
2. WebSocket Communication Scenarios  
3. Service Performance Test Data
4. Error & Recovery Scenarios
5. Health Monitoring Test Data
6. Multi-tenant Test Data
7. iOS Integration Test Data
8. Real-time Event Test Data
"""

import asyncio
import json
import random
import string
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pytest

from app.services.code_graph_service import CodeNode, CodeRelationship, NodeType, RelationType


class TestDataScale(Enum):
    """Test data scale levels"""
    SMALL = "small"      # 10-50 items
    MEDIUM = "medium"    # 50-200 items  
    LARGE = "large"      # 200-1000 items
    ENTERPRISE = "enterprise"  # 1000+ items


@dataclass
class ProjectTestData:
    """Test data for a complete project structure"""
    project_id: str
    project_name: str
    files: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    created_at: datetime
    
    def to_graph_nodes(self) -> List[CodeNode]:
        """Convert to graph nodes for Neo4j testing"""
        nodes = []
        
        # Add file nodes
        for file_data in self.files:
            nodes.append(CodeNode(
                id=file_data['id'],
                name=file_data['name'],
                type=NodeType.FILE,
                file_path=file_data['path'],
                start_line=1,
                end_line=file_data.get('lines', 100),
                properties={
                    'language': file_data.get('language', 'python'),
                    'size_bytes': file_data.get('size', 1024),
                    'project_id': self.project_id
                }
            ))
        
        # Add class nodes
        for class_data in self.classes:
            nodes.append(CodeNode(
                id=class_data['id'],
                name=class_data['name'],
                type=NodeType.CLASS,
                file_path=class_data['file_path'],
                start_line=class_data.get('start_line', 10),
                end_line=class_data.get('end_line', 50),
                properties={
                    'methods_count': class_data.get('methods', 3),
                    'complexity': class_data.get('complexity', 5),
                    'project_id': self.project_id
                }
            ))
        
        # Add function nodes
        for func_data in self.functions:
            nodes.append(CodeNode(
                id=func_data['id'],
                name=func_data['name'],
                type=NodeType.FUNCTION,
                file_path=func_data['file_path'],
                start_line=func_data.get('start_line', 20),
                end_line=func_data.get('end_line', 30),
                properties={
                    'parameters': func_data.get('parameters', []),
                    'complexity': func_data.get('complexity', 3),
                    'project_id': self.project_id
                }
            ))
        
        return nodes
    
    def to_graph_relationships(self) -> List[CodeRelationship]:
        """Convert to graph relationships for Neo4j testing"""
        relationships = []
        
        for dep in self.dependencies:
            relationships.append(CodeRelationship(
                from_node=dep['from_node'],
                to_node=dep['to_node'],
                type=RelationType(dep['type']),
                properties={
                    'strength': dep.get('strength', 1),
                    'project_id': self.project_id
                }
            ))
        
        return relationships


class IntegrationTestFixtures:
    """Main class for generating integration test fixtures"""
    
    def __init__(self):
        self.generated_projects = {}
        self.generated_users = {}
        self.generated_sessions = {}
        
    def generate_project_data(
        self, 
        project_name: str,
        scale: TestDataScale = TestDataScale.MEDIUM,
        language: str = "python"
    ) -> ProjectTestData:
        """Generate realistic project test data"""
        
        project_id = f"proj_{self._generate_id()}"
        
        # Scale-based data generation
        if scale == TestDataScale.SMALL:
            file_count = random.randint(5, 15)
            class_count = random.randint(10, 30)
            function_count = random.randint(20, 60)
        elif scale == TestDataScale.MEDIUM:
            file_count = random.randint(20, 50)
            class_count = random.randint(40, 120)
            function_count = random.randint(80, 250)
        elif scale == TestDataScale.LARGE:
            file_count = random.randint(50, 150)
            class_count = random.randint(150, 400)
            function_count = random.randint(300, 800)
        else:  # ENTERPRISE
            file_count = random.randint(200, 500)
            class_count = random.randint(500, 1500)
            function_count = random.randint(1000, 3000)
        
        # Generate files
        files = []
        file_paths = self._generate_file_structure(project_name, file_count, language)
        for i, path in enumerate(file_paths):
            files.append({
                'id': f'file_{i}_{self._generate_id()}',
                'name': path.split('/')[-1],
                'path': path,
                'language': language,
                'lines': random.randint(50, 500),
                'size': random.randint(1000, 50000)
            })
        
        # Generate classes
        classes = []
        for i in range(class_count):
            file_path = random.choice(file_paths)
            classes.append({
                'id': f'class_{i}_{self._generate_id()}',
                'name': self._generate_class_name(),
                'file_path': file_path,
                'start_line': random.randint(10, 100),
                'end_line': random.randint(150, 300),
                'methods': random.randint(2, 10),
                'complexity': random.randint(3, 15)
            })
        
        # Generate functions
        functions = []
        for i in range(function_count):
            file_path = random.choice(file_paths)
            functions.append({
                'id': f'func_{i}_{self._generate_id()}',
                'name': self._generate_function_name(),
                'file_path': file_path,
                'start_line': random.randint(20, 200),
                'end_line': random.randint(250, 350),
                'parameters': [f'param_{j}' for j in range(random.randint(0, 5))],
                'complexity': random.randint(1, 10)
            })
        
        # Generate dependencies
        dependencies = self._generate_dependencies(classes, functions, scale)
        
        # Generate project metrics
        metrics = {
            'total_lines': sum(f['lines'] for f in files),
            'total_files': len(files),
            'total_classes': len(classes),
            'total_functions': len(functions),
            'total_dependencies': len(dependencies),
            'average_complexity': sum(c['complexity'] for c in classes + functions) / (len(classes) + len(functions)),
            'test_coverage': random.uniform(0.6, 0.95),
            'technical_debt_ratio': random.uniform(0.05, 0.25)
        }
        
        project_data = ProjectTestData(
            project_id=project_id,
            project_name=project_name,
            files=files,
            classes=classes,
            functions=functions,
            dependencies=dependencies,
            metrics=metrics,
            created_at=datetime.now()
        )
        
        self.generated_projects[project_id] = project_data
        return project_data
    
    def generate_websocket_scenarios(self) -> List[Dict[str, Any]]:
        """Generate WebSocket communication test scenarios"""
        return [
            {
                'scenario_name': 'ios_app_launch',
                'client_type': 'ios',
                'client_id': 'ios_primary_client',
                'messages': [
                    {
                        'type': 'connection_init',
                        'payload': {
                            'client_type': 'ios',
                            'app_version': '1.0.0',
                            'device_info': {
                                'platform': 'iOS',
                                'version': '17.0',
                                'device': 'iPhone 15 Pro'
                            }
                        },
                        'expected_response': 'connection_ack'
                    },
                    {
                        'type': 'sync_request',
                        'payload': {
                            'sync_types': ['projects', 'tasks', 'notifications'],
                            'last_sync': (datetime.now() - timedelta(hours=1)).isoformat()
                        },
                        'expected_response': 'sync_data'
                    }
                ]
            },
            {
                'scenario_name': 'cli_interaction',
                'client_type': 'cli',
                'client_id': 'cli_session_1',
                'messages': [
                    {
                        'type': 'command',
                        'payload': {
                            'command': '/status',
                            'workspace_path': '/project/workspace'
                        },
                        'expected_response': 'command_response'
                    },
                    {
                        'type': 'code_completion',
                        'payload': {
                            'file_path': '/project/src/main.py',
                            'cursor_position': 150,
                            'intent': 'suggest',
                            'context': 'def calculate_'
                        },
                        'expected_response': 'code_completion_response'
                    }
                ]
            },
            {
                'scenario_name': 'real_time_collaboration',
                'client_type': 'web',
                'client_id': 'web_dashboard_1',
                'messages': [
                    {
                        'type': 'subscribe_updates',
                        'payload': {
                            'channels': ['project_updates', 'task_changes', 'system_alerts'],
                            'user_preferences': {
                                'priority_filter': 'medium',
                                'notification_types': ['task', 'project', 'system']
                            }
                        },
                        'expected_response': 'subscription_ack'
                    },
                    {
                        'type': 'task_create',
                        'payload': {
                            'task': {
                                'title': 'Integration test task',
                                'description': 'Test task for integration testing',
                                'priority': 'high',
                                'project_id': 'proj_test_123'
                            }
                        },
                        'expected_response': 'task_created'
                    }
                ]
            },
            {
                'scenario_name': 'high_frequency_heartbeat',
                'client_type': 'mobile',
                'client_id': 'mobile_app_client',
                'messages': [
                    {
                        'type': 'heartbeat',
                        'payload': {
                            'timestamp': datetime.now().isoformat(),
                            'client_status': 'active'
                        },
                        'expected_response': 'heartbeat_ack',
                        'frequency': 5  # Every 5 seconds
                    }
                ]
            }
        ]
    
    def generate_performance_test_data(self) -> Dict[str, Any]:
        """Generate performance testing data"""
        return {
            'load_test_scenarios': [
                {
                    'name': 'baseline_load',
                    'concurrent_users': 10,
                    'requests_per_user': 5,
                    'ramp_up_time': 2,
                    'expected_response_time': 1.0,
                    'expected_throughput': 25
                },
                {
                    'name': 'moderate_load',
                    'concurrent_users': 50,
                    'requests_per_user': 10,
                    'ramp_up_time': 10,
                    'expected_response_time': 2.0,
                    'expected_throughput': 100
                },
                {
                    'name': 'stress_load',
                    'concurrent_users': 100,
                    'requests_per_user': 8,
                    'ramp_up_time': 20,
                    'expected_response_time': 3.0,
                    'expected_throughput': 150
                },
                {
                    'name': 'spike_load',
                    'concurrent_users': 200,
                    'requests_per_user': 5,
                    'ramp_up_time': 5,  # Rapid spike
                    'expected_response_time': 5.0,
                    'expected_throughput': 200
                }
            ],
            'service_benchmarks': {
                'unified_mlx_service': {
                    'code_completion_small': {'max_time': 1.0, 'typical_time': 0.5},
                    'code_completion_large': {'max_time': 3.0, 'typical_time': 1.5},
                    'code_explanation': {'max_time': 2.0, 'typical_time': 1.0},
                    'code_refactoring': {'max_time': 4.0, 'typical_time': 2.0}
                },
                'code_graph_service': {
                    'simple_query': {'max_time': 0.5, 'typical_time': 0.2},
                    'complex_analysis': {'max_time': 2.0, 'typical_time': 1.0},
                    'architecture_overview': {'max_time': 1.5, 'typical_time': 0.8},
                    'circular_dependencies': {'max_time': 3.0, 'typical_time': 1.5}
                },
                'websocket_service': {
                    'message_processing': {'max_time': 0.1, 'typical_time': 0.05},
                    'connection_setup': {'max_time': 0.5, 'typical_time': 0.2},
                    'broadcast_message': {'max_time': 0.2, 'typical_time': 0.1}
                }
            },
            'resource_limits': {
                'cpu_warning_threshold': 75,
                'cpu_critical_threshold': 90,
                'memory_warning_threshold': 1024,  # MB
                'memory_critical_threshold': 2048,  # MB
                'disk_warning_threshold': 5000,    # MB
                'disk_critical_threshold': 1000    # MB
            }
        }
    
    def generate_error_scenarios(self) -> List[Dict[str, Any]]:
        """Generate error and recovery test scenarios"""
        return [
            {
                'scenario_name': 'mlx_service_timeout',
                'error_type': 'timeout',
                'affected_service': 'unified_mlx_service',
                'trigger_conditions': {
                    'large_context_size': True,
                    'high_concurrent_requests': True
                },
                'expected_fallback': 'mock_strategy',
                'expected_recovery_time': 30,
                'user_impact': 'degraded_performance'
            },
            {
                'scenario_name': 'neo4j_connection_failure',
                'error_type': 'connection_error',
                'affected_service': 'code_graph_service',
                'trigger_conditions': {
                    'database_unavailable': True,
                    'network_partition': False
                },
                'expected_fallback': 'cached_data',
                'expected_recovery_time': 60,
                'user_impact': 'limited_functionality'
            },
            {
                'scenario_name': 'websocket_mass_disconnect',
                'error_type': 'network_error',
                'affected_service': 'connection_manager',
                'trigger_conditions': {
                    'network_instability': True,
                    'load_balancer_restart': True
                },
                'expected_fallback': 'automatic_reconnection',
                'expected_recovery_time': 10,
                'user_impact': 'temporary_disconnection'
            },
            {
                'scenario_name': 'memory_pressure',
                'error_type': 'resource_exhaustion',
                'affected_service': 'system_wide',
                'trigger_conditions': {
                    'high_memory_usage': True,
                    'memory_leak': False
                },
                'expected_fallback': 'resource_cleanup',
                'expected_recovery_time': 45,
                'user_impact': 'performance_degradation'
            },
            {
                'scenario_name': 'cascade_failure_simulation',
                'error_type': 'cascade_failure',
                'affected_service': 'multiple',
                'trigger_conditions': {
                    'primary_service_down': 'unified_mlx_service',
                    'dependent_services': ['ast_graph_service', 'visualization_service']
                },
                'expected_fallback': 'circuit_breaker_activation',
                'expected_recovery_time': 120,
                'user_impact': 'multiple_features_degraded'
            }
        ]
    
    def generate_health_monitoring_data(self) -> Dict[str, Any]:
        """Generate health monitoring test data"""
        return {
            'healthy_service_states': {
                'unified_mlx_service': {
                    'health_score': 0.95,
                    'response_time': 1.2,
                    'model_loaded': True,
                    'strategy': 'production',
                    'memory_usage': 512,
                    'cpu_usage': 45,
                    'request_success_rate': 0.99
                },
                'code_graph_service': {
                    'health_score': 0.92,
                    'connected': True,
                    'query_response_time': 0.8,
                    'connection_pool_active': 8,
                    'connection_pool_idle': 2,
                    'memory_usage': 256,
                    'cpu_usage': 30,
                    'query_success_rate': 0.98
                },
                'websocket_service': {
                    'health_score': 0.97,
                    'active_connections': 45,
                    'message_queue_depth': 12,
                    'average_latency': 0.05,
                    'connection_errors': 0,
                    'memory_usage': 128,
                    'cpu_usage': 20
                },
                'event_streaming_service': {
                    'health_score': 0.94,
                    'events_processed_per_second': 15.5,
                    'queue_depth': 8,
                    'failed_deliveries': 1,
                    'subscriber_count': 23,
                    'memory_usage': 96,
                    'cpu_usage': 25
                }
            },
            'degraded_service_states': {
                'unified_mlx_service': {
                    'health_score': 0.65,
                    'response_time': 3.8,
                    'model_loaded': True,
                    'strategy': 'pragmatic',  # Degraded strategy
                    'memory_usage': 1024,
                    'cpu_usage': 85,
                    'request_success_rate': 0.89
                },
                'code_graph_service': {
                    'health_score': 0.58,
                    'connected': True,
                    'query_response_time': 2.5,
                    'connection_pool_active': 10,
                    'connection_pool_idle': 0,  # Pool exhausted
                    'memory_usage': 512,
                    'cpu_usage': 80,
                    'query_success_rate': 0.85
                }
            },
            'unhealthy_service_states': {
                'unified_mlx_service': {
                    'health_score': 0.25,
                    'response_time': 10.0,
                    'model_loaded': False,  # Critical failure
                    'strategy': 'mock',
                    'memory_usage': 2048,
                    'cpu_usage': 95,
                    'request_success_rate': 0.45
                },
                'code_graph_service': {
                    'health_score': 0.15,
                    'connected': False,  # Database unreachable
                    'query_response_time': 0,
                    'connection_pool_active': 0,
                    'connection_pool_idle': 0,
                    'memory_usage': 64,
                    'cpu_usage': 5,
                    'query_success_rate': 0.0
                }
            }
        }
    
    def generate_multi_tenant_data(self) -> Dict[str, Any]:
        """Generate multi-tenant test data"""
        tenants = []
        
        tenant_types = ['startup', 'enterprise', 'individual', 'team']
        
        for i in range(10):  # Generate 10 test tenants
            tenant_type = random.choice(tenant_types)
            
            if tenant_type == 'startup':
                user_count = random.randint(5, 25)
                project_count = random.randint(2, 8)
                api_calls_per_day = random.randint(1000, 10000)
            elif tenant_type == 'enterprise':
                user_count = random.randint(50, 500)
                project_count = random.randint(20, 100)
                api_calls_per_day = random.randint(50000, 500000)
            elif tenant_type == 'individual':
                user_count = 1
                project_count = random.randint(1, 5)
                api_calls_per_day = random.randint(100, 1000)
            else:  # team
                user_count = random.randint(3, 15)
                project_count = random.randint(3, 12)
                api_calls_per_day = random.randint(2000, 20000)
            
            tenant = {
                'tenant_id': f'tenant_{i}_{self._generate_id()}',
                'name': f'Test {tenant_type.title()} {i+1}',
                'type': tenant_type,
                'user_count': user_count,
                'project_count': project_count,
                'api_calls_per_day': api_calls_per_day,
                'subscription_tier': self._get_subscription_tier(tenant_type),
                'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
                'last_active': datetime.now() - timedelta(hours=random.randint(1, 48)),
                'resource_limits': self._get_resource_limits(tenant_type),
                'feature_flags': self._get_feature_flags(tenant_type)
            }
            
            tenants.append(tenant)
        
        return {
            'tenants': tenants,
            'isolation_test_scenarios': [
                {
                    'name': 'resource_isolation',
                    'description': 'Verify tenant resource usage does not affect others',
                    'test_tenants': ['tenant_0', 'tenant_1'],
                    'load_tenant': 'tenant_0',
                    'monitor_tenant': 'tenant_1'
                },
                {
                    'name': 'data_isolation',
                    'description': 'Verify tenant data is completely isolated',
                    'test_tenants': ['tenant_2', 'tenant_3'],
                    'data_types': ['projects', 'users', 'api_keys', 'usage_metrics']
                }
            ]
        }
    
    def _generate_id(self, length: int = 8) -> str:
        """Generate a random ID"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def _generate_file_structure(self, project_name: str, file_count: int, language: str) -> List[str]:
        """Generate realistic file structure"""
        if language == 'python':
            base_dirs = ['src', 'tests', 'docs', 'scripts', 'config']
            extensions = ['.py']
        elif language == 'javascript':
            base_dirs = ['src', 'test', 'docs', 'scripts', 'config']
            extensions = ['.js', '.ts']
        else:
            base_dirs = ['src', 'test', 'docs']
            extensions = ['.txt']
        
        files = []
        for i in range(file_count):
            base_dir = random.choice(base_dirs)
            
            # Generate subdirectories occasionally
            if random.random() < 0.3:
                sub_dir = random.choice(['utils', 'models', 'services', 'components'])
                dir_path = f"/{project_name}/{base_dir}/{sub_dir}"
            else:
                dir_path = f"/{project_name}/{base_dir}"
            
            filename = f"{self._generate_filename()}{random.choice(extensions)}"
            files.append(f"{dir_path}/{filename}")
        
        return files
    
    def _generate_class_name(self) -> str:
        """Generate realistic class names"""
        prefixes = ['User', 'Project', 'Task', 'Service', 'Manager', 'Handler', 'Controller', 'Model']
        suffixes = ['Manager', 'Service', 'Handler', 'Controller', 'Processor', 'Factory', 'Builder']
        
        if random.random() < 0.7:
            return random.choice(prefixes)
        else:
            return f"{random.choice(prefixes)}{random.choice(suffixes)}"
    
    def _generate_function_name(self) -> str:
        """Generate realistic function names"""
        verbs = ['get', 'set', 'create', 'update', 'delete', 'process', 'handle', 'validate', 'calculate', 'generate']
        nouns = ['user', 'project', 'task', 'data', 'result', 'response', 'request', 'config', 'status', 'info']
        
        return f"{random.choice(verbs)}_{random.choice(nouns)}"
    
    def _generate_filename(self) -> str:
        """Generate realistic file names"""
        names = ['main', 'utils', 'config', 'models', 'services', 'handlers', 'controllers', 'helpers', 'constants', 'types']
        return random.choice(names)
    
    def _generate_dependencies(self, classes: List[Dict], functions: List[Dict], scale: TestDataScale) -> List[Dict[str, Any]]:
        """Generate realistic dependencies between code entities"""
        dependencies = []
        
        # Determine dependency density based on scale
        if scale == TestDataScale.SMALL:
            dependency_ratio = 0.3
        elif scale == TestDataScale.MEDIUM:
            dependency_ratio = 0.4
        elif scale == TestDataScale.LARGE:
            dependency_ratio = 0.5
        else:  # ENTERPRISE
            dependency_ratio = 0.6
        
        all_entities = classes + functions
        total_possible_deps = len(all_entities) * len(all_entities)
        target_deps = int(total_possible_deps * dependency_ratio)
        
        relation_types = ['CALLS', 'DEPENDS_ON', 'USES', 'IMPLEMENTS', 'INHERITS']
        
        for i in range(min(target_deps, total_possible_deps)):
            from_entity = random.choice(all_entities)
            to_entity = random.choice(all_entities)
            
            if from_entity['id'] != to_entity['id']:  # No self-dependencies
                dependencies.append({
                    'from_node': from_entity['id'],
                    'to_node': to_entity['id'],
                    'type': random.choice(relation_types),
                    'strength': random.uniform(0.1, 1.0)
                })
        
        return dependencies
    
    def _get_subscription_tier(self, tenant_type: str) -> str:
        """Get subscription tier based on tenant type"""
        tier_mapping = {
            'individual': 'free',
            'team': 'pro',
            'startup': 'business',
            'enterprise': 'enterprise'
        }
        return tier_mapping.get(tenant_type, 'free')
    
    def _get_resource_limits(self, tenant_type: str) -> Dict[str, int]:
        """Get resource limits based on tenant type"""
        limits = {
            'individual': {
                'api_calls_per_day': 1000,
                'projects_max': 5,
                'users_max': 1,
                'storage_mb': 100
            },
            'team': {
                'api_calls_per_day': 10000,
                'projects_max': 20,
                'users_max': 10,
                'storage_mb': 1000
            },
            'startup': {
                'api_calls_per_day': 50000,
                'projects_max': 50,
                'users_max': 25,
                'storage_mb': 5000
            },
            'enterprise': {
                'api_calls_per_day': 1000000,
                'projects_max': 1000,
                'users_max': 1000,
                'storage_mb': 100000
            }
        }
        return limits.get(tenant_type, limits['individual'])
    
    def _get_feature_flags(self, tenant_type: str) -> Dict[str, bool]:
        """Get feature flags based on tenant type"""
        features = {
            'individual': {
                'advanced_analytics': False,
                'api_access': False,
                'priority_support': False,
                'custom_integrations': False
            },
            'team': {
                'advanced_analytics': True,
                'api_access': True,
                'priority_support': False,
                'custom_integrations': False
            },
            'startup': {
                'advanced_analytics': True,
                'api_access': True,
                'priority_support': True,
                'custom_integrations': True
            },
            'enterprise': {
                'advanced_analytics': True,
                'api_access': True,
                'priority_support': True,
                'custom_integrations': True,
                'white_label': True,
                'sso': True,
                'audit_logs': True
            }
        }
        return features.get(tenant_type, features['individual'])


# Global fixtures instance
integration_fixtures = IntegrationTestFixtures()


@pytest.fixture
def test_project_data():
    """Pytest fixture for project test data"""
    return integration_fixtures.generate_project_data("test_integration_project", TestDataScale.MEDIUM)


@pytest.fixture
def websocket_scenarios():
    """Pytest fixture for WebSocket test scenarios"""
    return integration_fixtures.generate_websocket_scenarios()


@pytest.fixture
def performance_test_data():
    """Pytest fixture for performance test data"""
    return integration_fixtures.generate_performance_test_data()


@pytest.fixture
def error_scenarios():
    """Pytest fixture for error and recovery scenarios"""
    return integration_fixtures.generate_error_scenarios()


@pytest.fixture
def health_monitoring_data():
    """Pytest fixture for health monitoring data"""
    return integration_fixtures.generate_health_monitoring_data()


@pytest.fixture
def multi_tenant_data():
    """Pytest fixture for multi-tenant test data"""
    return integration_fixtures.generate_multi_tenant_data()


@pytest.fixture
def large_scale_project():
    """Pytest fixture for large-scale project testing"""
    return integration_fixtures.generate_project_data("large_enterprise_project", TestDataScale.LARGE)


@pytest.fixture
def enterprise_scale_project():
    """Pytest fixture for enterprise-scale project testing"""
    return integration_fixtures.generate_project_data("enterprise_mega_project", TestDataScale.ENTERPRISE)


# Utility functions for test data manipulation
def create_test_graph_data(project_data: ProjectTestData) -> Tuple[List[CodeNode], List[CodeRelationship]]:
    """Create Neo4j test data from project data"""
    nodes = project_data.to_graph_nodes()
    relationships = project_data.to_graph_relationships()
    return nodes, relationships


def simulate_real_time_events(event_count: int = 50) -> List[Dict[str, Any]]:
    """Generate real-time event data for testing"""
    event_types = ['task_created', 'task_updated', 'project_updated', 'user_joined', 'system_alert']
    priorities = ['low', 'medium', 'high', 'critical']
    
    events = []
    for i in range(event_count):
        event = {
            'event_id': f'event_{i}_{integration_fixtures._generate_id()}',
            'event_type': random.choice(event_types),
            'priority': random.choice(priorities),
            'timestamp': datetime.now() - timedelta(seconds=random.randint(0, 3600)),
            'data': {
                'entity_id': f'entity_{random.randint(1, 100)}',
                'changes': [f'field_{j}' for j in range(random.randint(1, 5))],
                'user_id': f'user_{random.randint(1, 20)}'
            }
        }
        events.append(event)
    
    return events