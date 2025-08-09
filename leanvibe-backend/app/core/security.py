"""
Security utilities for LeanVibe Enterprise SaaS Platform
Provides API key verification, JWT handling, and security middleware
"""

import secrets
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class SecurityConfig:
    """Security configuration settings"""
    
    def __init__(self):
        self.api_key_header = "X-API-Key"
        self.jwt_secret = "leanvibe-jwt-secret-key"  # Should be loaded from environment
        self.jwt_algorithm = "HS256"
        self.token_expiry_seconds = 3600


security_config = SecurityConfig()


async def verify_api_key(api_key: str) -> bool:
    """
    Verify API key for external integrations
    
    Args:
        api_key: API key to verify
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Mock implementation - in production, this would check against database
    valid_keys = {
        "leanvibe-dev-key": {"name": "Development Key", "tenant_id": None},
        "leanvibe-test-key": {"name": "Test Key", "tenant_id": None}
    }
    
    return api_key in valid_keys


def generate_api_key(prefix: str = "lv") -> str:
    """
    Generate a new API key
    
    Args:
        prefix: Prefix for the API key
        
    Returns:
        str: Generated API key
    """
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}_{random_part}"


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for secure storage
    
    Args:
        api_key: Plain text API key
        
    Returns:
        str: Hashed API key
    """
    import hashlib
    return hashlib.sha256(api_key.encode()).hexdigest()


class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            "valid": True,
            "score": 0,
            "issues": []
        }
        
        if len(password) < 8:
            result["issues"].append("Password must be at least 8 characters")
            result["valid"] = False
        else:
            result["score"] += 1
            
        if not any(c.isupper() for c in password):
            result["issues"].append("Password must contain at least one uppercase letter")
            result["valid"] = False
        else:
            result["score"] += 1
            
        if not any(c.islower() for c in password):
            result["issues"].append("Password must contain at least one lowercase letter")
            result["valid"] = False
        else:
            result["score"] += 1
            
        if not any(c.isdigit() for c in password):
            result["issues"].append("Password must contain at least one digit")
            result["valid"] = False
        else:
            result["score"] += 1
            
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            result["issues"].append("Password must contain at least one special character")
            result["valid"] = False
        else:
            result["score"] += 1
            
        return result
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: list = None) -> bool:
        """
        Check if redirect URL is safe (prevents open redirects)
        
        Args:
            url: URL to validate
            allowed_hosts: List of allowed hostnames
            
        Returns:
            bool: True if safe, False otherwise
        """
        if not url:
            return False
            
        # Allow relative URLs
        if url.startswith('/') and not url.startswith('//'):
            return True
            
        # Check against allowed hosts if provided
        if allowed_hosts:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.hostname in allowed_hosts
            
        return False


def require_permissions(permissions: list):
    """
    Decorator to require specific permissions for API endpoints
    
    Args:
        permissions: List of required permissions
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would integrate with the JWT token validation
            # For now, mock implementation
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(requests_per_minute: int = 60):
    """
    Rate limiting decorator
    
    Args:
        requests_per_minute: Maximum requests allowed per minute
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would implement rate limiting logic
            # For now, mock implementation
            return await func(*args, **kwargs)
        return wrapper
    return decorator