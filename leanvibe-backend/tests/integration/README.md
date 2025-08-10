# LeanVibe AI Integration Test Suite

This comprehensive integration test suite validates the interaction between all major services and components in the LeanVibe AI system. The suite ensures that the consolidated architecture (14→6 service reduction) maintains functionality while providing better performance and maintainability.

## Overview

The integration test suite covers:

1. **Service Integration Testing** - End-to-end workflows across consolidated services
2. **Graph Database Integration** - Neo4j operations and data consistency  
3. **WebSocket & Real-time Features** - Communication protocols and event streaming
4. **Error Handling & Recovery** - Cross-service resilience and fault tolerance
5. **Performance & Health Monitoring** - SLA validation and resource optimization
6. **Service Consolidation Validation** - Ensuring consolidated services maintain full functionality

## Test Suite Structure

```
tests/integration/
├── README.md                                    # This documentation
├── test_comprehensive_service_integration.py    # Main integration framework
├── test_graph_database_integration.py          # Neo4j integration tests
├── test_websocket_realtime_features.py         # WebSocket & events tests
├── test_error_handling_recovery.py             # Error resilience tests
├── test_performance_health_monitoring.py       # Performance validation tests
├── fixtures/
│   └── integration_test_fixtures.py            # Test data generators
└── mocks/
    └── integration_mocks.py                    # Advanced service mocks
```

## Key Features

### 🔄 Service Consolidation Validation
- Validates that 14→6 service consolidation maintains functionality
- Tests unified MLX service strategy patterns
- Ensures enhanced services cover all original capabilities
- Validates performance improvements from consolidation

### 🎯 End-to-End Workflow Testing  
- Code Analysis → Graph Storage → API Retrieval workflows
- iOS App ↔ Backend WebSocket communication
- CLI ↔ Backend REST API interactions
- Voice commands → Backend processing pipelines

### 🏗️ Graph Database Integration
- Neo4j connection management and schema initialization
- Code entity storage and relationship mapping
- Architecture analysis and dependency querying
- Performance optimization and query validation

### 🌐 Real-time Communication Testing
- WebSocket connection establishment and management
- Message flow validation (bidirectional)
- Event streaming and notification delivery
- Client session management and reconnection

### 🛡️ Error Handling & Recovery
- Circuit breaker pattern implementation
- Service failover and fallback mechanisms
- Cross-service error propagation containment
- User-friendly error communication

### 📊 Performance & Health Monitoring
- Service performance benchmarking
- Real-time health monitoring validation
- Performance regression detection
- Resource usage and scalability testing

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure Neo4j is available (will use mocks if not)
# docker run --name neo4j-test -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/leanvibe123 neo4j:latest

# Set environment variables (optional - mocks used by default)
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j  
export NEO4J_PASSWORD=leanvibe123
```

### Running Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test categories
pytest tests/integration/test_comprehensive_service_integration.py -v
pytest tests/integration/test_graph_database_integration.py -v
pytest tests/integration/test_websocket_realtime_features.py -v
pytest tests/integration/test_error_handling_recovery.py -v
pytest tests/integration/test_performance_health_monitoring.py -v

# Run with coverage reporting
pytest tests/integration/ --cov=app --cov-report=html

# Run performance tests only
pytest tests/integration/ -m performance -v

# Run tests with specific scale
pytest tests/integration/ -k "test_large_scale" -v
```

## Test Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j database URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `leanvibe123` |
| `TEST_SCALE` | Test data scale (small/medium/large/enterprise) | `medium` |
| `INTEGRATION_TIMEOUT` | Test timeout in seconds | `300` |
| `MOCK_SERVICES` | Force service mocking | `true` |

### Test Markers

```bash
# Available pytest markers
pytest --markers

# Common markers:
# @pytest.mark.integration     - Integration tests
# @pytest.mark.performance     - Performance tests  
# @pytest.mark.slow           - Long-running tests
# @pytest.mark.enterprise     - Enterprise scale tests
# @pytest.mark.websocket      - WebSocket tests
# @pytest.mark.graph          - Graph database tests
```

## Test Data & Fixtures

### Project Data Generation

```python
from tests.fixtures.integration_test_fixtures import IntegrationTestFixtures, TestDataScale

fixtures = IntegrationTestFixtures()

# Generate project data at different scales
small_project = fixtures.generate_project_data("small_test", TestDataScale.SMALL)
enterprise_project = fixtures.generate_project_data("enterprise_test", TestDataScale.ENTERPRISE)

# Convert to graph nodes and relationships
nodes = project_data.to_graph_nodes()
relationships = project_data.to_graph_relationships()
```

### WebSocket Scenarios

```python
# Get predefined WebSocket test scenarios
scenarios = fixtures.generate_websocket_scenarios()

# Scenarios include:
# - iOS app launch and sync
# - CLI interactions
# - Real-time collaboration
# - High-frequency heartbeats
```

### Performance Test Data

```python
# Get performance testing configuration
perf_data = fixtures.generate_performance_test_data()

# Includes:
# - Load test scenarios (10-200 concurrent users)
# - Service benchmarks and SLA thresholds
# - Resource usage limits and alerting thresholds
```

## Advanced Mocking

### Realistic Service Mocks

The test suite includes sophisticated mocks that simulate realistic service behavior:

```python
from tests.mocks.integration_mocks import (
    AdvancedMLXServiceMock,
    Neo4jGraphDatabaseMock,
    WebSocketConnectionMock,
    EventStreamingMock
)

# MLX service with strategy switching
mlx_mock = AdvancedMLXServiceMock()
await mlx_mock.switch_strategy("pragmatic")  # Simulate fallback

# Neo4j with realistic query responses  
graph_mock = Neo4jGraphDatabaseMock()
dependencies = await graph_mock.get_dependencies("node_id", depth=3)

# WebSocket with state management
ws_mock = WebSocketConnectionMock()
await ws_mock.connect(websocket, "client_id")
await ws_mock.send_to_client("client_id", {"type": "notification"})
```

### Error Injection

```python
# Inject realistic errors for testing
error_scenarios = fixtures.generate_error_scenarios()

# Scenarios include:
# - MLX service timeouts
# - Neo4j connection failures  
# - WebSocket mass disconnects
# - Memory pressure situations
# - Cascading failure simulations
```

## Test Results & Reporting

### Success Metrics

Tests are considered successful when:

- **Overall Success Rate** ≥ 80%
- **Service Consolidation Coverage** ≥ 90% 
- **Performance SLA Compliance** ≥ 85%
- **Error Recovery Rate** ≥ 75%
- **Real-time Communication** ≥ 95% reliability

### Detailed Reporting

```bash
# Generate comprehensive test report
pytest tests/integration/ --html=integration-report.html --self-contained-html

# Performance metrics
pytest tests/integration/test_performance_health_monitoring.py --benchmark-only

# Coverage report
pytest tests/integration/ --cov=app --cov-report=term-missing --cov-report=html
```

### Sample Test Output

```
======================= Integration Test Results =======================

Service Integration Tests:
✅ Comprehensive Service Integration     - 92% success rate
✅ Graph Database Integration           - 88% success rate  
✅ WebSocket Real-time Features         - 94% success rate
✅ Error Handling & Recovery            - 78% success rate
✅ Performance & Health Monitoring      - 86% success rate

Service Consolidation Validation:
✅ Unified MLX Coverage                 - 98% functionality maintained
✅ Enhanced Graph Coverage              - 100% functionality maintained
✅ NLP Enhancement Coverage             - 95% functionality maintained
✅ Project-Task Integration             - 100% functionality maintained

Performance Metrics:
- Average Response Time: 1.2s (SLA: <2.0s) ✅
- Throughput: 45 RPS (SLA: >25 RPS) ✅  
- Error Rate: 2.1% (SLA: <5%) ✅
- Resource Usage: 65% CPU, 512MB RAM ✅

Overall Integration Health: 87% ✅
```

## Troubleshooting

### Common Issues

#### Neo4j Connection Failures
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Start Neo4j container
docker run --name neo4j-test -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/leanvibe123 neo4j:latest

# Use mock mode if database not available
export MOCK_SERVICES=true
```

#### Test Timeouts
```bash
# Increase timeout for large-scale tests
export INTEGRATION_TIMEOUT=600

# Run specific scale tests
pytest tests/integration/ -k "not enterprise" -v
```

#### Memory Issues
```bash
# Reduce test data scale
export TEST_SCALE=small

# Run tests individually
pytest tests/integration/test_graph_database_integration.py -v
```

### Debug Mode

```bash
# Enable debug logging
pytest tests/integration/ -v -s --log-cli-level=DEBUG

# Enable mock debugging
export MOCK_DEBUG=true
pytest tests/integration/ -v
```

## Performance Benchmarking

### Baseline Performance

| Service | Operation | Target Response Time | Throughput (RPS) |
|---------|-----------|---------------------|------------------|
| Unified MLX | Code Completion (Small) | <1.0s | >10 |
| Unified MLX | Code Completion (Large) | <3.0s | >5 |
| Graph Service | Simple Query | <0.5s | >20 |
| Graph Service | Complex Analysis | <2.0s | >5 |
| WebSocket | Message Processing | <0.1s | >50 |

### Load Testing Results

```bash
# Run load tests
pytest tests/integration/test_performance_health_monitoring.py::test_concurrent_load_handling -v

# Results example:
# 10 concurrent users:  95% success rate, 0.8s avg response
# 50 concurrent users:  92% success rate, 1.2s avg response  
# 100 concurrent users: 87% success rate, 2.1s avg response
```

## Contributing

### Adding New Integration Tests

1. **Create test file** in `/tests/integration/`
2. **Follow naming convention**: `test_[feature]_integration.py`
3. **Use provided fixtures** from `integration_test_fixtures.py`
4. **Include comprehensive assertions** for success criteria
5. **Add performance benchmarks** where applicable
6. **Document test scenarios** in docstrings

### Test Template

```python
"""
[Feature] Integration Test Suite

Tests [feature] integration with other LeanVibe components.
"""

import pytest
import asyncio
from tests.fixtures.integration_test_fixtures import integration_fixtures
from tests.mocks.integration_mocks import setup_integration_mocks

@pytest.mark.asyncio
async def test_[feature]_integration(test_project_data):
    """Test [feature] integration with comprehensive validation"""
    
    # Arrange - Set up test data and mocks
    mocks = setup_integration_mocks()
    
    # Act - Execute integration scenario
    result = await execute_integration_test(test_project_data)
    
    # Assert - Validate results against success criteria
    assert result['success_rate'] >= 80
    assert result['performance_rating'] in ['excellent', 'good']
    
    return result
```

### Best Practices

1. **Use realistic test data** - Generate data that resembles production workloads
2. **Test error scenarios** - Include failure conditions and recovery testing
3. **Validate performance** - Ensure tests include performance assertions
4. **Mock external dependencies** - Use sophisticated mocks for reliable testing
5. **Document test scenarios** - Clear documentation for maintenance
6. **Assert comprehensively** - Test both positive and negative outcomes

## Continuous Integration

### GitHub Actions Integration

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      neo4j:
        image: neo4j:latest
        env:
          NEO4J_AUTH: neo4j/leanvibe123
        ports:
          - 7474:7474
          - 7687:7687
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
        
    - name: Install dependencies
      run: pip install -r requirements.txt
      
    - name: Run Integration Tests
      run: |
        pytest tests/integration/ -v --cov=app
        
    - name: Upload Coverage
      uses: codecov/codecov-action@v1
```

## Support

For questions about the integration test suite:

1. **Check this documentation** for common issues and solutions
2. **Review test logs** for specific error messages
3. **Run tests in debug mode** with `-v -s --log-cli-level=DEBUG`
4. **Create GitHub issue** with test output and environment details

---

*This integration test suite ensures the LeanVibe AI system maintains high quality and reliability through comprehensive automated testing of service interactions and consolidated architecture validation.*