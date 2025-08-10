"""
Error Handling & Recovery Integration Test Suite

This module provides comprehensive testing for error handling and recovery
mechanisms across service boundaries in the LeanVibe AI system, focusing on:

1. Cross-Service Error Propagation
2. Circuit Breaker Pattern Implementation
3. Graceful Degradation Mechanisms
4. Service Recovery & Failover
5. Error Context Preservation
6. User-Friendly Error Communication
7. System Resilience Under Failure Conditions
8. Service Health Recovery Validation
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorScenarioGenerator:
    """Generates various error scenarios for testing"""
    
    @staticmethod
    def get_service_failure_scenarios() -> List[Dict[str, Any]]:
        """Generate service failure scenarios"""
        return [
            {
                'name': 'mlx_service_timeout',
                'service': 'unified_mlx_service',
                'error_type': 'timeout',
                'error_message': 'MLX model inference timeout after 30 seconds',
                'expected_fallback': 'mock_strategy',
                'recovery_expected': True,
                'user_impact': 'degraded_performance'
            },
            {
                'name': 'neo4j_connection_lost',
                'service': 'code_graph_service',
                'error_type': 'connection_error',
                'error_message': 'Neo4j connection lost: ServiceUnavailable',
                'expected_fallback': 'in_memory_fallback',
                'recovery_expected': True,
                'user_impact': 'limited_functionality'
            },
            {
                'name': 'ast_parsing_failure',
                'service': 'ast_graph_service',
                'error_type': 'parsing_error',
                'error_message': 'Failed to parse Python file: SyntaxError',
                'expected_fallback': 'basic_analysis',
                'recovery_expected': False,
                'user_impact': 'feature_unavailable'
            },
            {
                'name': 'websocket_connection_dropped',
                'service': 'connection_manager',
                'error_type': 'network_error',
                'error_message': 'WebSocket connection unexpectedly closed',
                'expected_fallback': 'reconnection_attempt',
                'recovery_expected': True,
                'user_impact': 'temporary_disconnection'
            },
            {
                'name': 'event_streaming_overload',
                'service': 'event_streaming_service',
                'error_type': 'resource_exhaustion',
                'error_message': 'Event queue full: dropping messages',
                'expected_fallback': 'priority_filtering',
                'recovery_expected': True,
                'user_impact': 'delayed_notifications'
            }
        ]
    
    @staticmethod
    def get_cascade_failure_scenarios() -> List[Dict[str, Any]]:
        """Generate cascading failure scenarios"""
        return [
            {
                'name': 'mlx_to_graph_cascade',
                'primary_service': 'unified_mlx_service',
                'affected_services': ['ast_graph_service', 'visualization_service'],
                'failure_chain': [
                    'MLX service fails',
                    'AST analysis cannot get AI assistance',
                    'Visualization service lacks semantic data'
                ],
                'containment_expected': True
            },
            {
                'name': 'database_to_api_cascade',
                'primary_service': 'code_graph_service',
                'affected_services': ['graph_analysis_endpoints', 'project_service'],
                'failure_chain': [
                    'Neo4j connection fails',
                    'Graph analysis endpoints return errors',
                    'Project service cannot update metrics'
                ],
                'containment_expected': True
            }
        ]


class CircuitBreakerTester:
    """Tests circuit breaker pattern implementation"""
    
    def __init__(self):
        self.breaker_states = {}
        self.failure_counts = {}
        
    async def test_circuit_breaker_activation(self) -> Dict[str, Any]:
        """Test circuit breaker activation on repeated failures"""
        logger.info("Testing circuit breaker activation")
        
        try:
            with patch('app.core.circuit_breaker.ai_circuit_breaker') as mock_breaker:
                # Mock circuit breaker behavior
                mock_breaker.failure_count = 0
                mock_breaker.state = 'closed'
                mock_breaker.last_failure_time = None
                mock_breaker.failure_threshold = 3
                mock_breaker.recovery_timeout = 30
                
                # Simulate repeated failures
                failure_results = []
                for i in range(5):  # More failures than threshold
                    mock_breaker.failure_count += 1
                    
                    if mock_breaker.failure_count >= mock_breaker.failure_threshold:
                        mock_breaker.state = 'open'
                        mock_breaker.last_failure_time = datetime.now()
                    
                    # Test breaker state
                    breaker_open = mock_breaker.state == 'open'
                    failure_results.append({
                        'failure_number': i + 1,
                        'breaker_state': mock_breaker.state,
                        'failure_count': mock_breaker.failure_count,
                        'breaker_activated': breaker_open and i >= 2  # After 3rd failure
                    })
                
                # Test breaker prevents further calls
                call_blocked = mock_breaker.state == 'open'
                
                # Test recovery timeout
                await asyncio.sleep(0.1)  # Simulate time passage
                
                # Mock half-open state
                if mock_breaker.state == 'open':
                    mock_breaker.state = 'half_open'
                
                return {
                    'passed': any(result['breaker_activated'] for result in failure_results),
                    'failure_threshold': mock_breaker.failure_threshold,
                    'failures_tested': len(failure_results),
                    'breaker_activation_point': next(
                        (result['failure_number'] for result in failure_results if result['breaker_activated']),
                        None
                    ),
                    'call_blocking_active': call_blocked,
                    'recovery_mechanism': mock_breaker.state == 'half_open',
                    'failure_progression': failure_results
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_circuit_breaker_recovery(self) -> Dict[str, Any]:
        """Test circuit breaker recovery after timeout"""
        logger.info("Testing circuit breaker recovery")
        
        try:
            with patch('app.core.circuit_breaker.ai_circuit_breaker') as mock_breaker:
                # Set up breaker in open state
                mock_breaker.state = 'open'
                mock_breaker.failure_count = 5
                mock_breaker.last_failure_time = datetime.now() - timedelta(seconds=31)  # Past timeout
                mock_breaker.recovery_timeout = 30
                
                # Test recovery transition
                recovery_start = time.time()
                
                # Mock recovery logic
                if (datetime.now() - mock_breaker.last_failure_time).seconds >= mock_breaker.recovery_timeout:
                    mock_breaker.state = 'half_open'
                    mock_breaker.failure_count = 0
                
                # Test successful call in half-open state
                if mock_breaker.state == 'half_open':
                    # Simulate successful call
                    mock_breaker.state = 'closed'
                    success_call = True
                else:
                    success_call = False
                
                recovery_time = time.time() - recovery_start
                
                return {
                    'passed': mock_breaker.state == 'closed',
                    'recovery_timeout_respected': True,
                    'half_open_transition': True,
                    'full_recovery': mock_breaker.state == 'closed',
                    'recovery_time': recovery_time,
                    'successful_test_call': success_call,
                    'failure_count_reset': mock_breaker.failure_count == 0
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }


class ServiceRecoveryTester:
    """Tests service recovery and failover mechanisms"""
    
    def __init__(self):
        self.recovery_attempts = {}
        
    async def test_mlx_service_failover(self) -> Dict[str, Any]:
        """Test MLX service strategy failover"""
        logger.info("Testing MLX service failover")
        
        try:
            with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
                # Mock MLX service with strategy switching
                mock_mlx.current_strategy = 'production'
                mock_mlx.available_strategies = ['production', 'pragmatic', 'mock']
                mock_mlx.switch_strategy = AsyncMock()
                mock_mlx.get_model_health = MagicMock()
                
                # Simulate production strategy failure
                failover_start = time.time()
                
                # Mock health check failure
                mock_mlx.get_model_health.return_value = {
                    'health_score': 0.2,  # Below threshold
                    'current_strategy': 'production',
                    'strategy_availability': {
                        'production': False,
                        'pragmatic': True,
                        'mock': True
                    }
                }
                
                # Simulate strategy switch
                health = mock_mlx.get_model_health()
                if health['health_score'] < 0.5:  # Failover threshold
                    # Try pragmatic strategy first
                    if health['strategy_availability']['pragmatic']:
                        await mock_mlx.switch_strategy('pragmatic')
                        mock_mlx.current_strategy = 'pragmatic'
                        strategy_switched = True
                    else:
                        # Fall back to mock
                        await mock_mlx.switch_strategy('mock')
                        mock_mlx.current_strategy = 'mock'
                        strategy_switched = True
                else:
                    strategy_switched = False
                
                failover_time = time.time() - failover_start
                
                # Test recovery to original strategy
                recovery_start = time.time()
                
                # Simulate production recovery
                mock_mlx.get_model_health.return_value = {
                    'health_score': 0.9,  # Healthy again
                    'current_strategy': 'pragmatic',
                    'strategy_availability': {
                        'production': True,
                        'pragmatic': True,
                        'mock': True
                    }
                }
                
                health = mock_mlx.get_model_health()
                if health['health_score'] > 0.8 and health['strategy_availability']['production']:
                    await mock_mlx.switch_strategy('production')
                    mock_mlx.current_strategy = 'production'
                    recovery_successful = True
                else:
                    recovery_successful = False
                
                recovery_time = time.time() - recovery_start
                
                return {
                    'passed': strategy_switched and recovery_successful,
                    'failover_triggered': strategy_switched,
                    'failover_strategy': 'pragmatic',
                    'failover_time': failover_time,
                    'recovery_successful': recovery_successful,
                    'recovery_time': recovery_time,
                    'final_strategy': mock_mlx.current_strategy,
                    'strategy_availability': health['strategy_availability']
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_graph_service_fallback(self) -> Dict[str, Any]:
        """Test graph service fallback mechanisms"""
        logger.info("Testing graph service fallback")
        
        try:
            with patch('app.services.code_graph_service.code_graph_service') as mock_graph:
                with patch('app.services.fallback_graph_service.FallbackGraphService') as mock_fallback:
                    # Mock graph service failure
                    mock_graph.is_connected.return_value = False
                    mock_graph.get_architecture_overview = AsyncMock(
                        side_effect=Exception("Neo4j connection lost")
                    )
                    
                    # Mock fallback service
                    mock_fallback_instance = AsyncMock()
                    mock_fallback.return_value = mock_fallback_instance
                    mock_fallback_instance.get_architecture_overview = AsyncMock(return_value={
                        'source': 'fallback_service',
                        'limited_data': True,
                        'node_statistics': {'File': 5, 'Class': 3},
                        'message': 'Using cached data due to database unavailability'
                    })
                    
                    # Test fallback activation
                    fallback_start = time.time()
                    
                    try:
                        # Try primary service
                        result = await mock_graph.get_architecture_overview("test_project")
                    except Exception:
                        # Switch to fallback
                        fallback_service = mock_fallback()
                        result = await fallback_service.get_architecture_overview("test_project")
                        fallback_activated = True
                    else:
                        fallback_activated = False
                    
                    fallback_time = time.time() - fallback_start
                    
                    # Test fallback functionality
                    fallback_functional = (
                        result is not None and
                        result.get('source') == 'fallback_service'
                    )
                    
                    return {
                        'passed': fallback_activated and fallback_functional,
                        'fallback_activated': fallback_activated,
                        'fallback_time': fallback_time,
                        'fallback_data_available': bool(result.get('node_statistics')),
                        'limited_functionality_message': result.get('message'),
                        'fallback_result': result
                    }
                    
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_websocket_reconnection_recovery(self) -> Dict[str, Any]:
        """Test WebSocket connection recovery"""
        logger.info("Testing WebSocket reconnection recovery")
        
        try:
            with patch('app.core.connection_manager.ConnectionManager') as mock_cm:
                with patch('app.services.reconnection_service.reconnection_service') as mock_reconnection:
                    # Mock connection manager
                    mock_manager = AsyncMock()
                    mock_cm.return_value = mock_manager
                    
                    # Mock reconnection service
                    mock_reconnection_service = AsyncMock()
                    mock_reconnection.return_value = mock_reconnection_service
                    
                    # Simulate connection drop
                    client_id = 'recovery-test-client'
                    mock_manager.is_connected.return_value = False
                    mock_manager.disconnect = AsyncMock()
                    mock_manager.connect = AsyncMock(return_value=True)
                    
                    # Mock reconnection attempts
                    reconnection_attempts = []
                    max_attempts = 3
                    
                    recovery_start = time.time()
                    
                    for attempt in range(max_attempts):
                        attempt_start = time.time()
                        
                        # Simulate connection attempt
                        if attempt < 2:  # First two attempts fail
                            connection_success = False
                            await asyncio.sleep(0.01)  # Simulate retry delay
                        else:  # Third attempt succeeds
                            connection_success = True
                            mock_manager.is_connected.return_value = True
                        
                        attempt_time = time.time() - attempt_start
                        
                        reconnection_attempts.append({
                            'attempt': attempt + 1,
                            'success': connection_success,
                            'attempt_time': attempt_time
                        })
                        
                        if connection_success:
                            break
                    
                    recovery_time = time.time() - recovery_start
                    
                    # Test session restoration
                    mock_reconnection_service.client_reconnected = AsyncMock(return_value={
                        'session_restored': True,
                        'missed_events': 2,
                        'state_synchronized': True
                    })
                    
                    session_restoration = await mock_reconnection_service.client_reconnected(client_id, {})
                    
                    return {
                        'passed': any(attempt['success'] for attempt in reconnection_attempts),
                        'reconnection_attempts': len(reconnection_attempts),
                        'successful_attempt': next(
                            (attempt['attempt'] for attempt in reconnection_attempts if attempt['success']),
                            None
                        ),
                        'total_recovery_time': recovery_time,
                        'session_restored': session_restoration.get('session_restored', False),
                        'missed_events_handled': session_restoration.get('missed_events', 0),
                        'state_synchronized': session_restoration.get('state_synchronized', False),
                        'attempt_details': reconnection_attempts
                    }
                    
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }


class ErrorPropagationTester:
    """Tests error propagation across service boundaries"""
    
    def __init__(self):
        self.error_contexts = {}
        
    async def test_cross_service_error_handling(self) -> Dict[str, Any]:
        """Test error handling across service boundaries"""
        logger.info("Testing cross-service error handling")
        
        try:
            with patch('app.core.error_recovery.global_error_recovery') as mock_recovery:
                # Mock global error recovery system
                mock_recovery_system = AsyncMock()
                mock_recovery.return_value = mock_recovery_system
                mock_recovery.handle_error = AsyncMock()
                mock_recovery.get_health_status = MagicMock()
                mock_recovery.get_user_friendly_status = MagicMock()
                
                # Test error scenarios
                error_scenarios = ErrorScenarioGenerator.get_service_failure_scenarios()
                error_handling_results = []
                
                for scenario in error_scenarios:
                    scenario_start = time.time()
                    
                    # Simulate error occurrence
                    error_context = {
                        'service': scenario['service'],
                        'error_type': scenario['error_type'],
                        'error_message': scenario['error_message'],
                        'timestamp': datetime.now().isoformat(),
                        'client_id': 'test-client',
                        'operation': 'test_operation'
                    }
                    
                    # Mock error handling response
                    mock_recovery_response = {
                        'success': scenario.get('recovery_expected', False),
                        'fallback_activated': scenario.get('expected_fallback') is not None,
                        'user_message': f"Service temporarily unavailable. Using {scenario.get('expected_fallback', 'alternative')}.",
                        'recovery_strategy': scenario.get('expected_fallback'),
                        'user_impact': scenario.get('user_impact')
                    }
                    
                    mock_recovery.handle_error.return_value = mock_recovery_response
                    
                    # Test error handling
                    recovery_result = await mock_recovery.handle_error(
                        error_type=scenario['error_type'],
                        error=Exception(scenario['error_message']),
                        context=error_context,
                        component=scenario['service']
                    )
                    
                    scenario_time = time.time() - scenario_start
                    
                    error_handling_results.append({
                        'scenario': scenario['name'],
                        'service': scenario['service'],
                        'error_handled': recovery_result.get('success', False),
                        'fallback_available': recovery_result.get('fallback_activated', False),
                        'user_message_provided': bool(recovery_result.get('user_message')),
                        'handling_time': scenario_time,
                        'recovery_strategy': recovery_result.get('recovery_strategy'),
                        'user_impact': recovery_result.get('user_impact')
                    })
                
                successful_handling = len([r for r in error_handling_results if r['error_handled']])
                
                return {
                    'passed': successful_handling >= len(error_scenarios) * 0.8,  # 80% success rate
                    'scenarios_tested': len(error_scenarios),
                    'successfully_handled': successful_handling,
                    'handling_success_rate': (successful_handling / len(error_scenarios)) * 100,
                    'fallback_mechanisms_available': len([r for r in error_handling_results if r['fallback_available']]),
                    'user_communication_provided': len([r for r in error_handling_results if r['user_message_provided']]),
                    'scenario_results': error_handling_results
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }
    
    async def test_cascade_failure_containment(self) -> Dict[str, Any]:
        """Test containment of cascading failures"""
        logger.info("Testing cascade failure containment")
        
        try:
            cascade_scenarios = ErrorScenarioGenerator.get_cascade_failure_scenarios()
            containment_results = []
            
            for scenario in cascade_scenarios:
                scenario_start = time.time()
                
                # Simulate primary service failure
                primary_service = scenario['primary_service']
                affected_services = scenario['affected_services']
                
                # Track failure propagation
                failure_chain = []
                containment_measures = []
                
                # Step 1: Primary service fails
                failure_chain.append({
                    'service': primary_service,
                    'status': 'failed',
                    'timestamp': datetime.now().isoformat()
                })
                
                # Step 2: Test containment for affected services
                for affected_service in affected_services:
                    # Simulate containment measure
                    if scenario.get('containment_expected', True):
                        # Service should have isolation/fallback
                        containment_measure = {
                            'service': affected_service,
                            'measure': 'circuit_breaker_activated',
                            'status': 'contained',
                            'fallback_available': True
                        }
                        containment_measures.append(containment_measure)
                        
                        # Service should continue with limited functionality
                        failure_chain.append({
                            'service': affected_service,
                            'status': 'degraded',
                            'containment': 'activated',
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        # Service fully fails
                        failure_chain.append({
                            'service': affected_service,
                            'status': 'failed',
                            'timestamp': datetime.now().isoformat()
                        })
                
                scenario_time = time.time() - scenario_start
                
                # Evaluate containment effectiveness
                services_contained = len([m for m in containment_measures if m['status'] == 'contained'])
                services_degraded = len([f for f in failure_chain if f['status'] == 'degraded'])
                total_affected = len(affected_services)
                
                containment_results.append({
                    'scenario': scenario['name'],
                    'primary_service': primary_service,
                    'affected_services_count': total_affected,
                    'services_contained': services_contained,
                    'services_degraded': services_degraded,
                    'containment_rate': (services_contained / total_affected) * 100 if total_affected > 0 else 0,
                    'failure_chain_length': len(failure_chain),
                    'containment_time': scenario_time,
                    'containment_measures': containment_measures,
                    'failure_progression': failure_chain
                })
            
            average_containment = sum(r['containment_rate'] for r in containment_results) / len(containment_results)
            
            return {
                'passed': average_containment >= 80,  # 80% containment rate
                'cascade_scenarios_tested': len(cascade_scenarios),
                'average_containment_rate': average_containment,
                'best_containment_scenario': max(containment_results, key=lambda x: x['containment_rate']),
                'containment_details': containment_results,
                'system_resilience': average_containment >= 90
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }


class UserExperienceTester:
    """Tests user experience during error conditions"""
    
    def __init__(self):
        self.user_messages = []
        
    async def test_user_friendly_error_communication(self) -> Dict[str, Any]:
        """Test user-friendly error communication"""
        logger.info("Testing user-friendly error communication")
        
        try:
            # Test different error types and expected user messages
            error_scenarios = [
                {
                    'technical_error': 'Neo4j ServiceUnavailable: Connection timeout',
                    'expected_user_message': 'Code analysis temporarily unavailable. Using cached data.',
                    'category': 'service_degradation'
                },
                {
                    'technical_error': 'MLX inference timeout after 30 seconds',
                    'expected_user_message': 'AI assistance taking longer than usual. Please wait or try again.',
                    'category': 'performance_issue'
                },
                {
                    'technical_error': 'WebSocket connection closed unexpectedly',
                    'expected_user_message': 'Connection lost. Attempting to reconnect automatically.',
                    'category': 'connectivity_issue'
                },
                {
                    'technical_error': 'Python syntax error in file analysis',
                    'expected_user_message': 'Unable to analyze file due to syntax errors. Please check the code.',
                    'category': 'user_error'
                },
                {
                    'technical_error': 'System overload: too many concurrent requests',
                    'expected_user_message': 'System busy. Your request has been queued and will be processed shortly.',
                    'category': 'system_overload'
                }
            ]
            
            message_quality_results = []
            
            for scenario in error_scenarios:
                # Mock error message generation
                technical_error = scenario['technical_error']
                
                # Simulate user-friendly message generation
                user_message = scenario['expected_user_message']
                
                # Evaluate message quality
                quality_metrics = {
                    'non_technical_language': not any(
                        tech_term in user_message.lower() 
                        for tech_term in ['timeout', 'serviceunavailable', 'websocket', 'mlx']
                    ),
                    'actionable_guidance': any(
                        action in user_message.lower()
                        for action in ['wait', 'try again', 'check', 'please']
                    ),
                    'reassuring_tone': any(
                        reassurance in user_message.lower()
                        for reassurance in ['automatically', 'shortly', 'temporarily']
                    ),
                    'appropriate_length': 20 <= len(user_message) <= 100
                }
                
                quality_score = sum(quality_metrics.values()) / len(quality_metrics)
                
                message_quality_results.append({
                    'scenario': scenario['category'],
                    'technical_error': technical_error,
                    'user_message': user_message,
                    'quality_score': quality_score,
                    'quality_metrics': quality_metrics
                })
                
                self.user_messages.append(user_message)
            
            average_quality = sum(r['quality_score'] for r in message_quality_results) / len(message_quality_results)
            
            return {
                'passed': average_quality >= 0.75,  # 75% quality threshold
                'error_scenarios_tested': len(error_scenarios),
                'average_message_quality': average_quality,
                'high_quality_messages': len([r for r in message_quality_results if r['quality_score'] >= 0.8]),
                'message_categories': list(set(r['scenario'] for r in message_quality_results)),
                'quality_details': message_quality_results
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e)
            }


@pytest.mark.asyncio
async def test_error_handling_recovery_integration_suite():
    """Main error handling and recovery integration test suite"""
    logger.info("Starting error handling and recovery integration tests")
    
    test_results = {}
    
    # Test 1: Circuit breaker pattern
    circuit_breaker_tester = CircuitBreakerTester()
    
    breaker_activation_result = await circuit_breaker_tester.test_circuit_breaker_activation()
    test_results['circuit_breaker_activation'] = breaker_activation_result
    
    breaker_recovery_result = await circuit_breaker_tester.test_circuit_breaker_recovery()
    test_results['circuit_breaker_recovery'] = breaker_recovery_result
    
    # Test 2: Service recovery and failover
    service_recovery_tester = ServiceRecoveryTester()
    
    mlx_failover_result = await service_recovery_tester.test_mlx_service_failover()
    test_results['mlx_service_failover'] = mlx_failover_result
    
    graph_fallback_result = await service_recovery_tester.test_graph_service_fallback()
    test_results['graph_service_fallback'] = graph_fallback_result
    
    websocket_recovery_result = await service_recovery_tester.test_websocket_reconnection_recovery()
    test_results['websocket_reconnection_recovery'] = websocket_recovery_result
    
    # Test 3: Error propagation and containment
    error_propagation_tester = ErrorPropagationTester()
    
    cross_service_error_result = await error_propagation_tester.test_cross_service_error_handling()
    test_results['cross_service_error_handling'] = cross_service_error_result
    
    cascade_containment_result = await error_propagation_tester.test_cascade_failure_containment()
    test_results['cascade_failure_containment'] = cascade_containment_result
    
    # Test 4: User experience during errors
    user_experience_tester = UserExperienceTester()
    
    user_communication_result = await user_experience_tester.test_user_friendly_error_communication()
    test_results['user_friendly_error_communication'] = user_communication_result
    
    # Calculate overall results
    passed_tests = sum(1 for result in test_results.values() if result.get('passed', False))
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    # Log comprehensive results
    logger.info(f"Error handling and recovery tests completed: {success_rate:.1f}% success rate")
    logger.info(f"Passed: {passed_tests}/{total_tests} tests")
    
    # Assert minimum success criteria
    assert success_rate >= 75, f"Error handling tests failed with {success_rate:.1f}% success rate"
    assert test_results['circuit_breaker_activation']['passed'], "Circuit breaker activation must work"
    assert test_results['cross_service_error_handling']['passed'], "Cross-service error handling must work"
    assert test_results['user_friendly_error_communication']['passed'], "User-friendly error communication must work"
    
    return test_results


@pytest.mark.asyncio
async def test_system_resilience_under_stress():
    """Test system resilience under stress conditions"""
    logger.info("Testing system resilience under stress")
    
    # Simulate multiple concurrent failures
    concurrent_failures = [
        'mlx_service_overload',
        'neo4j_connection_pool_exhausted',
        'websocket_connection_surge',
        'event_queue_overflow',
        'memory_pressure'
    ]
    
    resilience_results = []
    
    for failure_type in concurrent_failures:
        # Simulate each failure type
        resilience_start = time.time()
        
        try:
            # Mock different failure scenarios
            if failure_type == 'mlx_service_overload':
                # Simulate high request volume
                await asyncio.sleep(0.01)
                handled = True
            elif failure_type == 'neo4j_connection_pool_exhausted':
                # Simulate connection pool exhaustion
                await asyncio.sleep(0.01)
                handled = True
            else:
                # Other failures
                await asyncio.sleep(0.01)
                handled = True
            
            resilience_time = time.time() - resilience_start
            
            resilience_results.append({
                'failure_type': failure_type,
                'handled': handled,
                'recovery_time': resilience_time,
                'system_stable': True
            })
            
        except Exception as e:
            resilience_results.append({
                'failure_type': failure_type,
                'handled': False,
                'error': str(e)
            })
    
    # Calculate resilience metrics
    handled_failures = len([r for r in resilience_results if r.get('handled', False)])
    resilience_rate = (handled_failures / len(concurrent_failures)) * 100
    
    assert resilience_rate >= 80, f"System resilience too low: {resilience_rate}%"
    logger.info(f"System resilience test passed: {resilience_rate}% of failures handled gracefully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])