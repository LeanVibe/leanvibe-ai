"""
Project models for LeanVibe backend API
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectLanguage(str, Enum):
    """Supported project languages"""
    SWIFT = "Swift"
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"
    KOTLIN = "Kotlin"
    JAVA = "Java"
    CSHARP = "C#"
    GO = "Go"
    RUST = "Rust"
    UNKNOWN = "Unknown"


class ProjectStatus(str, Enum):
    """Project status values"""
    PLANNING = "planning"
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectMetrics(BaseModel):
    """Project metrics data"""
    files_count: int = Field(default=0, description="Number of files in project")
    lines_of_code: int = Field(default=0, description="Total lines of code")
    last_build_time: Optional[float] = Field(default=None, description="Last build time in seconds")
    test_coverage: Optional[float] = Field(default=None, description="Test coverage percentage (0.0-1.0)")
    health_score: float = Field(default=0.0, description="Overall health score (0.0-1.0)")
    issues_count: int = Field(default=0, description="Number of open issues")
    performance_score: Optional[float] = Field(default=None, description="Performance score (0.0-1.0)")
    
    class Config:
        extra = "ignore"


class Project(BaseModel):
    """Project model with multi-tenant support"""
    id: UUID = Field(description="Project unique identifier")
    display_name: str = Field(description="Project display name")
    description: Optional[str] = Field(default=None, description="Project description")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="Project status")
    tasks_count: int = Field(default=0, description="Total number of tasks")
    completed_tasks_count: int = Field(default=0, description="Number of completed tasks")
    issues_count: int = Field(default=0, description="Number of issues")
    created_at: datetime = Field(description="Project creation timestamp")
    updated_at: datetime = Field(description="Project last update timestamp")
    path: str = Field(description="Project file system path")
    language: ProjectLanguage = Field(description="Primary programming language")
    last_activity: datetime = Field(description="Last activity timestamp")
    metrics: ProjectMetrics = Field(description="Project metrics")
    
    # Multi-tenant fields
    tenant_id: UUID = Field(description="Tenant identifier for data isolation")
    client_id: Optional[str] = Field(default=None, description="Associated client ID (legacy)")
    created_by: Optional[UUID] = Field(default=None, description="User who created the project")
    
    class Config:
        extra = "ignore"


class ProjectTask(BaseModel):
    """Project task model"""
    id: UUID = Field(description="Task unique identifier")
    project_id: UUID = Field(description="Associated project ID")
    title: str = Field(description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    status: str = Field(default="pending", description="Task status")
    priority: str = Field(default="medium", description="Task priority")
    assignee: Optional[str] = Field(default=None, description="Task assignee")
    created_at: datetime = Field(description="Task creation timestamp")
    updated_at: datetime = Field(description="Task last update timestamp")
    due_date: Optional[datetime] = Field(default=None, description="Task due date")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")
    
    class Config:
        extra = "ignore"


class ProjectListResponse(BaseModel):
    """Response model for project list endpoint"""
    projects: List[Project] = Field(description="List of projects")
    total: int = Field(description="Total number of projects")
    
    class Config:
        extra = "ignore"


class ProjectTasksResponse(BaseModel):
    """Response model for project tasks endpoint"""
    tasks: List[ProjectTask] = Field(description="List of project tasks")
    total: int = Field(description="Total number of tasks")
    project_id: UUID = Field(description="Project ID")
    
    class Config:
        extra = "ignore"


class ProjectMetricsResponse(BaseModel):
    """Response model for project metrics endpoint"""
    metrics: ProjectMetrics = Field(description="Project metrics")
    project_id: UUID = Field(description="Project ID")
    updated_at: datetime = Field(description="Metrics last update timestamp")
    
    class Config:
        extra = "ignore"