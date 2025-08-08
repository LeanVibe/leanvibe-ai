"""
Simple API key authentication for production security.
Following YAGNI principle - just enough security to be safe.
"""

import os
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery
import logging

logger = logging.getLogger(__name__)

# API key can be in header or query parameter
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


def get_api_key(
    api_key_from_header: Optional[str] = Security(api_key_header),
    api_key_from_query: Optional[str] = Security(api_key_query),
) -> Optional[str]:
    """Get API key from header or query parameter"""
    return api_key_from_header or api_key_from_query


def verify_api_key(api_key: Optional[str] = Security(get_api_key)) -> bool:
    """
    Verify API key for protected endpoints.
    
    If LEANVIBE_API_KEY env var is not set, allows all (dev mode).
    If set, requires matching API key.
    """
    expected_key = os.environ.get("LEANVIBE_API_KEY")
    
    # Dev mode - no API key required
    if not expected_key:
        logger.debug("No API key configured - running in dev mode")
        return True
    
    # Production mode - API key required
    if not api_key:
        logger.warning("API key required but not provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide via X-API-Key header or api_key query parameter."
        )
    
    if api_key != expected_key:
        logger.warning(f"Invalid API key attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True


# Dependency for endpoints that should be protected
api_key_dependency = verify_api_key