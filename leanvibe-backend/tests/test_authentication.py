"""
Test for basic API key authentication
Following XP/TDD principles - test first, then implement
"""

import os
from fastapi.testclient import TestClient
import pytest


def test_endpoints_require_authentication():
    """Test that endpoints require API key authentication"""
    # Force production mode by setting an API key
    original_api_key = os.environ.get("LEANVIBE_API_KEY")
    os.environ["LEANVIBE_API_KEY"] = "test-production-key"
    
    try:
        # Set up test client without API key
        from app.main import app
        client = TestClient(app)
        
        # Test GET endpoints that should require authentication
        get_protected_endpoints = [
            "/api/projects/",
            "/api/tasks/",
        ]
        
        for endpoint in get_protected_endpoints:
            # GET request without API key should fail
            response = client.get(endpoint)
            assert response.status_code == 401, f"{endpoint} should require authentication (got {response.status_code})"
            assert "api key" in response.json().get("detail", "").lower() or \
                   "unauthorized" in response.json().get("detail", "").lower(), \
                   f"{endpoint} should return auth error message"
        
        # Test POST endpoints that should require authentication
        post_protected_endpoints = [
            ("/api/code-completion", {"intent": "suggest", "file_path": "test.py", "cursor_position": 10}),
            ("/api/v1/cli/query", {"query": "test query"}),
        ]
        
        for endpoint, payload in post_protected_endpoints:
            # POST request without API key should fail
            response = client.post(endpoint, json=payload)
            assert response.status_code == 401, f"{endpoint} should require authentication (got {response.status_code})"
            assert "api key" in response.json().get("detail", "").lower() or \
                   "unauthorized" in response.json().get("detail", "").lower(), \
                   f"{endpoint} should return auth error message"
    
    finally:
        # Restore original environment
        if original_api_key is not None:
            os.environ["LEANVIBE_API_KEY"] = original_api_key
        else:
            os.environ.pop("LEANVIBE_API_KEY", None)


def test_health_endpoint_no_auth_required():
    """Test that health endpoint doesn't require authentication"""
    from app.main import app
    client = TestClient(app)
    
    # Health endpoint should work without authentication
    response = client.get("/health")
    assert response.status_code == 200, "Health endpoint should not require auth"


def test_valid_api_key_allows_access():
    """Test that valid API key allows access to protected endpoints"""
    # Set test API key
    test_api_key = "test-api-key-12345"
    os.environ["LEANVIBE_API_KEY"] = test_api_key
    
    from app.main import app
    client = TestClient(app)
    
    # Request with valid API key should succeed
    headers = {"X-API-Key": test_api_key}
    
    # Test a protected endpoint with API key
    response = client.get("/api/projects/", headers=headers)
    # Should either succeed or return non-auth error
    assert response.status_code != 401, "Valid API key should allow access"


def test_invalid_api_key_denies_access():
    """Test that invalid API key denies access"""
    # Set test API key
    os.environ["LEANVIBE_API_KEY"] = "correct-key"
    
    from app.main import app
    client = TestClient(app)
    
    # Request with invalid API key should fail
    headers = {"X-API-Key": "wrong-key"}
    
    response = client.get("/api/projects/", headers=headers)
    assert response.status_code == 401, "Invalid API key should deny access"


def test_api_key_from_query_param():
    """Test that API key can be provided as query parameter"""
    test_api_key = "test-api-key-query"
    os.environ["LEANVIBE_API_KEY"] = test_api_key
    
    from app.main import app
    client = TestClient(app)
    
    # API key as query parameter should work
    response = client.get(f"/api/projects/?api_key={test_api_key}")
    assert response.status_code != 401, "API key in query param should work"


def test_no_api_key_env_var_allows_all():
    """Test that if no API key is set, system works without auth (dev mode)"""
    # Remove API key from environment
    if "LEANVIBE_API_KEY" in os.environ:
        del os.environ["LEANVIBE_API_KEY"]
    
    from app.main import app
    client = TestClient(app)
    
    # Without API key env var, should work (dev mode)
    response = client.get("/api/projects/")
    # In dev mode, should not require auth
    # This behavior is intentional for development
    pass  # We'll implement this based on requirements