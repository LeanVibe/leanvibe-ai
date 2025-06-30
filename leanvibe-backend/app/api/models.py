"""
API Models for Code Completion Endpoint

Pydantic models for request/response validation.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, validator


class CodeCompletionRequest(BaseModel):
    """Request model for code completion endpoint"""

    file_path: str = Field(..., description="Path to the file being edited")
    cursor_position: int = Field(default=0, description="Cursor position in the file")
    intent: Literal["suggest", "explain", "refactor", "debug", "optimize"] = Field(
        default="suggest", description="Type of completion requested"
    )
    content: Optional[str] = Field(default=None, description="Optional file content")
    language: Optional[str] = Field(
        default=None, description="Programming language (auto-detected if not provided)"
    )

    @validator("file_path")
    def file_path_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("file_path cannot be empty")
        return v.strip()

    @validator("cursor_position")
    def normalize_cursor_position(cls, v):
        # Ensure cursor position is non-negative
        return max(0, v)


class ContextUsed(BaseModel):
    """Information about the context used for completion"""

    language: str
    symbols_found: int = 0
    has_context: bool = False
    file_path: str = ""
    has_symbol_context: bool = False
    language_detected: str = ""


class CodeCompletionResponse(BaseModel):
    """Response model for code completion endpoint"""

    status: Literal["success", "error"]
    intent: str
    response: str = Field(description="AI-generated response")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    requires_review: bool = Field(description="Whether human review is recommended")
    suggestions: List[str] = Field(
        default_factory=list, description="Follow-up suggestions"
    )
    context_used: ContextUsed
    processing_time_ms: float = Field(
        ge=0, description="Processing time in milliseconds"
    )

    # Intent-specific fields (optional)
    explanation: Optional[str] = None
    refactoring_suggestions: Optional[str] = None
    debug_analysis: Optional[str] = None
    optimization_suggestions: Optional[str] = None


class CodeCompletionErrorResponse(BaseModel):
    """Error response model for code completion endpoint"""

    status: Literal["error"]
    error: str = Field(description="Error message")
    error_code: Optional[str] = Field(
        default=None, description="Error code for programmatic handling"
    )
    processing_time_ms: float = Field(
        ge=0, description="Processing time in milliseconds"
    )
