from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class TaskStatus(str, Enum):
    """Task status enumeration for Kanban board"""
    TODO = "todo"  # Aligned with iOS
    IN_PROGRESS = "in_progress" 
    TESTING = "testing"  # Backend-specific status
    DONE = "done"
    
    # Legacy support for iOS compatibility
    BACKLOG = "todo"  # Map to todo for compatibility

class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"  # Aligned with iOS
    
    # Legacy support
    CRITICAL = "urgent"  # Map to urgent for compatibility

class Task(BaseModel):
    """Core task model for Kanban board - aligned with iOS LeanVibeTask and multi-tenant"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Detailed task description")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Current task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    project_id: str = Field(..., description="Associated project ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Multi-tenant fields
    tenant_id: str = Field(..., description="Tenant identifier for data isolation")
    
    # AI-related fields
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="AI confidence score")
    agent_decision: Optional[Dict[str, Any]] = Field(None, description="Agent decision data")
    
    # Assignment and tracking
    client_id: str = Field(..., description="Client ID that created the task (legacy)")
    created_by: Optional[str] = Field(None, description="User who created the task")
    assigned_to: Optional[str] = Field(None, description="Agent or human assigned")
    estimated_effort: Optional[float] = Field(None, ge=0, description="Estimated effort in hours")
    actual_effort: Optional[float] = Field(None, ge=0, description="Actual time spent in hours")
    
    # Organization
    tags: List[str] = Field(default_factory=list, description="Task tags/labels")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this depends on")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Task attachments")
    
    # Legacy fields for backward compatibility
    confidence_score: Optional[float] = Field(None, description="Legacy field, use 'confidence' instead")
    estimated_hours: Optional[float] = Field(None, description="Legacy field, use 'estimated_effort' instead")
    actual_hours: Optional[float] = Field(None, description="Legacy field, use 'actual_effort' instead")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional task metadata")

class TaskCreate(BaseModel):
    """Schema for creating new tasks - aligned with iOS"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    project_id: str = Field(..., description="Associated project ID")
    client_id: str = Field(..., description="Client ID creating the task")
    assigned_to: Optional[str] = None
    estimated_effort: Optional[float] = Field(None, ge=0, description="Estimated effort in hours")
    tags: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    
    # Legacy fields for backward compatibility
    estimated_hours: Optional[float] = Field(None, ge=0, description="Legacy field, use 'estimated_effort' instead")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskUpdate(BaseModel):
    """Schema for updating existing tasks - aligned with iOS"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[str] = None
    estimated_effort: Optional[float] = Field(None, ge=0, description="Estimated effort in hours")
    actual_effort: Optional[float] = Field(None, ge=0, description="Actual time spent in hours")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence score")
    tags: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    agent_decision: Optional[Dict[str, Any]] = None
    
    # Legacy fields for backward compatibility
    estimated_hours: Optional[float] = Field(None, ge=0, description="Legacy field, use 'estimated_effort' instead")
    actual_hours: Optional[float] = Field(None, ge=0, description="Legacy field, use 'actual_effort' instead")
    confidence_score: Optional[float] = Field(None, description="Legacy field, use 'confidence' instead")
    metadata: Optional[Dict[str, Any]] = None

class TaskStatusUpdate(BaseModel):
    """Schema for status-only updates (drag and drop)"""
    status: TaskStatus

class KanbanColumn(BaseModel):
    """Kanban board column representation"""
    id: str
    title: str
    status: TaskStatus
    tasks: List[Task]
    task_count: int
    wip_limit: Optional[int] = None

class KanbanBoard(BaseModel):
    """Complete Kanban board state"""
    columns: List[KanbanColumn]
    total_tasks: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class TaskMoveRequest(BaseModel):
    """Schema for moving tasks between columns"""
    target_status: TaskStatus
    position: Optional[int] = Field(None, description="Target position in column")

class TaskFilters(BaseModel):
    """Filters for task queries"""
    project_id: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

class TaskSearchRequest(BaseModel):
    """Schema for task search requests"""
    query: Optional[str] = None
    filters: Optional[TaskFilters] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

class TaskStats(BaseModel):
    """Task statistics for dashboard"""
    total_tasks: int
    by_status: Dict[str, int]  # Use string keys for JSON serialization compatibility
    by_priority: Dict[str, int]  # Use string keys for JSON serialization compatibility
    avg_completion_time: Optional[float] = None
    completion_rate: float = Field(ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)