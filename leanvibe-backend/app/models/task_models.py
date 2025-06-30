from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class TaskStatus(str, Enum):
    """Task status enumeration for Kanban board"""
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress" 
    TESTING = "testing"
    DONE = "done"

class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Task(BaseModel):
    """Core task model for Kanban board"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Detailed task description")
    status: TaskStatus = Field(default=TaskStatus.BACKLOG, description="Current task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="AI confidence score")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_to: Optional[str] = Field(None, description="Agent or human assigned")
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated effort in hours")
    actual_hours: Optional[float] = Field(None, ge=0, description="Actual time spent")
    tags: List[str] = Field(default_factory=list, description="Task tags/labels")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional task metadata")

class TaskCreate(BaseModel):
    """Schema for creating new tasks"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskUpdate(BaseModel):
    """Schema for updating existing tasks"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    tags: Optional[List[str]] = None
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
    by_status: Dict[TaskStatus, int]
    by_priority: Dict[TaskPriority, int]
    avg_completion_time: Optional[float] = None
    completion_rate: float = Field(ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)