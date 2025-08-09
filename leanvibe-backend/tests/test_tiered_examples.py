"""
Example tests demonstrating the tiered test system markers
These tests show how to properly mark tests for different tiers
"""

import pytest
import time


# TIER 0: Unit tests (fast, isolated)
@pytest.mark.unit
def test_basic_unit_example():
    """Basic unit test example - should be fast"""
    assert 1 + 1 == 2


@pytest.mark.unit 
def test_string_operations():
    """Test string operations - fast unit test"""
    text = "hello world"
    assert text.upper() == "HELLO WORLD"
    assert text.split() == ["hello", "world"]


# TIER 0: Contract tests
@pytest.mark.contract
def test_api_response_structure():
    """Test that API responses have correct structure"""
    response = {
        "status": "success",
        "data": {"items": []},
        "metadata": {"count": 0}
    }
    
    # Contract validation
    assert "status" in response
    assert "data" in response
    assert "metadata" in response
    assert isinstance(response["data"]["items"], list)


# TIER 1: Integration tests
@pytest.mark.integration
def test_service_integration_example():
    """Integration test example - tests service interaction"""
    # Simulate service interaction
    result = {"connected": True, "response_time": 0.1}
    assert result["connected"] is True
    assert result["response_time"] < 1.0


@pytest.mark.websocket
def test_websocket_connection():
    """WebSocket functionality test"""
    # Mock websocket connection
    connection_state = {"connected": True, "messages": []}
    assert connection_state["connected"]


@pytest.mark.smoke
def test_core_functionality():
    """Smoke test for core application functionality"""
    # Basic smoke test
    app_state = {"initialized": True, "services": ["db", "cache"]}
    assert app_state["initialized"]
    assert len(app_state["services"]) > 0


# TIER 2: E2E tests
@pytest.mark.e2e
def test_end_to_end_workflow():
    """End-to-end workflow test"""
    # Simulate E2E workflow
    steps = ["start", "process", "complete"]
    current_step = 0
    
    for step in steps:
        current_step += 1
        time.sleep(0.01)  # Small delay to simulate real work
    
    assert current_step == len(steps)


@pytest.mark.performance
def test_performance_benchmark():
    """Performance benchmark test"""
    start_time = time.time()
    
    # Simulate some work
    result = sum(range(1000))
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    assert result == 499500
    assert execution_time < 0.1  # Should complete in under 100ms


# TIER 3: Load tests
@pytest.mark.load
def test_load_simulation():
    """Load testing example"""
    # Simulate handling multiple requests
    requests_processed = 0
    max_requests = 10
    
    for i in range(max_requests):
        # Simulate request processing
        time.sleep(0.001)  # 1ms per request
        requests_processed += 1
    
    assert requests_processed == max_requests


@pytest.mark.security
def test_input_validation():
    """Security-related test for input validation"""
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../../etc/passwd"
    ]
    
    for input_data in malicious_inputs:
        # Simulate input sanitization
        sanitized = input_data.replace("<", "&lt;").replace(">", "&gt;")
        assert "<script>" not in sanitized
        # Check specific inputs contain expected content
        if "DROP TABLE" in input_data:
            assert "DROP TABLE" in sanitized   # SQL injection preserved in sanitized form


# Tests without markers (would default to unit tier in practice)
def test_unmarked_example():
    """Test without explicit marker - typically treated as unit test"""
    assert True


def test_basic_math():
    """Another unmarked test"""
    assert 2 * 3 == 6


# Tests that should be skipped in CI
@pytest.mark.skip_ci
def test_local_only():
    """Test that only runs locally, not in CI"""
    assert True


# Slow tests
@pytest.mark.slow
def test_slow_operation():
    """Test that takes a while to run"""
    time.sleep(0.1)  # 100ms delay
    assert True