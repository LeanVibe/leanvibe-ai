"""
Generated Pydantic Models from Contract Schemas

This file is auto-generated from OpenAPI and AsyncAPI schemas.
Do not edit manually - regenerate using contracts/generate.py
"""

from datetime import datetime
from typing import List, Optional, Union, Any, Dict, Literal
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum

class HealthResponse(BaseModel):
    """Generated model for HealthResponse"""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(...)
    service: str = Field(...)
    version: str = Field(...)
    ai_ready: bool = Field(...)
    agent_framework: str = None
    sessions: Dict[str, Any] = None
    event_streaming: Dict[str, Any] = None
    error_recovery: Dict[str, Any] = None
    system_status: Dict[str, Any] = None
    llm_metrics: Dict[str, Any] = None


class MLXHealthResponse(BaseModel):
    """Generated model for MLXHealthResponse"""

    status: Literal["healthy", "uninitialized", "degraded"] = Field(...)
    model: str = Field(...)
    model_loaded: bool = Field(...)
    has_pretrained_weights: bool = None
    inference_ready: bool = Field(...)
    confidence_score: float = Field(..., ge=0, le=1)
    last_inference_time_ms: Optional[float] = None
    memory_usage_mb: float = None
    total_inferences: int = None
    service_status: str = None
    dependencies: Dict[str, Any] = None
    capabilities: Dict[str, Any] = None
    performance: Dict[str, Any] = None
    recommendations: List[str] = None


class ProjectMetrics(BaseModel):
    """Generated model for ProjectMetrics"""

    lines_of_code: int = None
    file_count: int = None
    complexity_score: float = None
    test_coverage: float = None
    maintainability_index: float = None


class Project(BaseModel):
    """Generated model for Project"""

    id: UUID = Field(...)
    name: str = Field(...)
    path: str = Field(...)
    status: Literal["active", "inactive", "archived"] = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = None
    language: str = None
    metrics: ProjectMetrics = None


class ProjectListResponse(BaseModel):
    """Generated model for ProjectListResponse"""

    projects: List[Project] = Field(...)
    total: int = Field(...)


class Task(BaseModel):
    """Generated model for Task"""

    id: UUID = Field(...)
    title: str = Field(...)
    description: str = None
    status: Literal["todo", "in_progress", "done", "cancelled"] = Field(...)
    priority: Literal["low", "medium", "high", "urgent"] = None
    created_at: datetime = Field(...)
    updated_at: datetime = None
    assigned_to: str = None
    project_id: UUID = None


class TaskListResponse(BaseModel):
    """Generated model for TaskListResponse"""

    tasks: List[Task] = Field(...)
    total: int = Field(...)


class CodeCompletionRequest(BaseModel):
    """Generated model for CodeCompletionRequest"""

    file_path: str = Field(..., description="Path to the file being edited", min_length=1)
    cursor_position: int = Field(default=0, description="Cursor position in the file", ge=0)
    intent: Literal["suggest", "explain", "refactor", "debug", "optimize"] = Field(default="suggest", description="Type of completion requested")
    content: Optional[str] = Field(default=None, description="Optional file content")
    language: Optional[str] = Field(default=None, description="Programming language (auto-detected if not provided)")


    @validator('file_path')
    def file_path_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('file_path cannot be empty')
        return v.strip()

class ContextUsed(BaseModel):
    """Generated model for ContextUsed"""

    language: str = Field(...)
    symbols_found: int = 0
    has_context: bool = False
    file_path: str = ""
    has_symbol_context: bool = False
    language_detected: str = ""


class CodeCompletionResponse(BaseModel):
    """Generated model for CodeCompletionResponse"""

    status: Literal["success", "error"] = Field(...)
    intent: str = Field(...)
    response: str = Field(..., description="AI-generated response")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)", ge=0, le=1)
    requires_review: bool = Field(..., description="Whether human review is recommended")
    suggestions: List[str] = Field(default=None, description="Follow-up suggestions")
    context_used: ContextUsed = Field(...)
    processing_time_ms: float = Field(..., description="Processing time in milliseconds", ge=0)
    explanation: Optional[str] = None
    refactoring_suggestions: Optional[str] = None
    debug_analysis: Optional[str] = None
    optimization_suggestions: Optional[str] = None


class CodeCompletionErrorResponse(BaseModel):
    """Generated model for CodeCompletionErrorResponse"""

    status: Literal["error"] = Field(...)
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code for programmatic handling")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds", ge=0)


class ErrorResponse(BaseModel):
    """Generated model for ErrorResponse"""

    status: str = Field(...)
    error: str = Field(...)
    message: str = Field(...)


class AgentMessagePayload(BaseModel):
    """Generated model for AgentMessagePayload"""

    type: str = Field(...)
    content: str = Field(..., description="Natural language query for the agent", min_length=1)
    workspace_path: str = Field(default=".", description="Path to the workspace directory")


    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('content cannot be empty')
        return v.strip()

class AgentResponsePayload(BaseModel):
    """Generated model for AgentResponsePayload"""

    status: Literal["success", "error"] = Field(...)
    message: str = Field(..., description="Agent response message")
    confidence: float = Field(..., ge=0, le=1)
    timestamp: float = Field(..., description="Unix timestamp")
    requires_review: bool = None
    suggestions: List[str] = None


class CodeCompletionRequestPayload(BaseModel):
    """Generated model for CodeCompletionRequestPayload"""

    type: str = Field(...)
    file_path: str = Field(..., description="Path to the file being edited", min_length=1)
    cursor_position: int = Field(default=0, ge=0)
    intent: Literal["suggest", "explain", "refactor", "debug", "optimize"] = "suggest"
    content: str = Field(default=None, description="Optional file content")
    language: str = Field(default=None, description="Programming language")


    @validator('file_path')
    def file_path_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('file_path cannot be empty')
        return v.strip()

class CodeCompletionResponsePayload(BaseModel):
    """Generated model for CodeCompletionResponsePayload"""

    status: Literal["success", "error"] = Field(...)
    type: str = Field(...)
    intent: Literal["suggest", "explain", "refactor", "debug", "optimize"] = Field(...)
    response: str = Field(..., description="AI-generated response")
    confidence: float = Field(..., ge=0, le=1)
    requires_review: bool = None
    suggestions: List[str] = None
    client_id: str = None
    timestamp: float = Field(..., description="Unix timestamp")
    explanation: str = Field(default=None, description="Present when intent is 'explain'")
    refactoring_suggestions: str = Field(default=None, description="Present when intent is 'refactor'")
    debug_analysis: str = Field(default=None, description="Present when intent is 'debug'")
    optimization_suggestions: str = Field(default=None, description="Present when intent is 'optimize'")


class HeartbeatPayload(BaseModel):
    """Generated model for HeartbeatPayload"""

    type: str = Field(...)
    timestamp: datetime = None


class HeartbeatAckPayload(BaseModel):
    """Generated model for HeartbeatAckPayload"""

    type: str = Field(...)
    timestamp: datetime = Field(...)


class CommandMessagePayload(BaseModel):
    """Generated model for CommandMessagePayload"""

    type: str = Field(...)
    content: str = Field(..., description="Slash command starting with '/'", pattern=r"^/.*")
    workspace_path: str = "."


class ReconnectionSyncPayload(BaseModel):
    """Generated model for ReconnectionSyncPayload"""

    type: str = Field(...)
    data: Dict[str, Any] = Field(...)
    timestamp: datetime = Field(...)


class EventNotificationPayload(BaseModel):
    """Generated model for EventNotificationPayload"""

    event_id: str = Field(...)
    event_type: Literal["system_ready", "task_created", "task_updated", "task_completed", "project_created", "project_updated", "code_generated", "analysis_complete", "agent_initialized", "connection_established"] = Field(...)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    channel: Literal["system", "development", "collaboration", "analytics"] = "system"
    timestamp: datetime = Field(...)
    source: str = None
    data: Dict[str, Any] = None
    metadata: Dict[str, Any] = None


class ErrorResponsePayload(BaseModel):
    """Generated model for ErrorResponsePayload"""

    status: str = Field(...)
    message: str = Field(..., description="Error message")
    confidence: float = None
    timestamp: float = Field(..., description="Unix timestamp")
    recovery_attempted: bool = Field(default=None, description="Whether error recovery was attempted")
    error_code: str = Field(default=None, description="Error code for programmatic handling")


