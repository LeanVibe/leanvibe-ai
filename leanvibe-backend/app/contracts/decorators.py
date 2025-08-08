"""
Generated FastAPI Validation Decorators from Contract Schemas

This file is auto-generated from OpenAPI schemas.
Do not edit manually - regenerate using contracts/generate.py
"""

import functools
from typing import Callable, Any
from fastapi import HTTPException
from pydantic import ValidationError
from .models import *

def validate_response(response_model: type):
    """Decorator to validate response against schema."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # Validate response against model
                if response_model:
                    if isinstance(result, dict):
                        validated_result = response_model(**result)
                        return validated_result.dict()
                    elif isinstance(result, response_model):
                        return result.dict()
                    else:
                        # Try to create model from result
                        validated_result = response_model.parse_obj(result)
                        return validated_result.dict()
                
                return result
            except ValidationError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Response validation failed: {str(e)}"
                )
            except Exception as e:
                raise e
        return wrapper
    return decorator

def validate_get_health_response():
    """Validation decorator for GET /health"""
    return validate_response(HealthResponse)

def validate_get_health_mlx_response():
    """Validation decorator for GET /health/mlx"""
    return validate_response(MLXHealthResponse)

def validate_get_api_projects_response():
    """Validation decorator for GET /api/projects"""
    return validate_response(ProjectListResponse)

def validate_get_api_tasks_response():
    """Validation decorator for GET /api/tasks"""
    return validate_response(TaskListResponse)

def validate_post_api_code_completion_response():
    """Validation decorator for POST /api/code-completion"""
    return validate_response(CodeCompletionResponse)

