# DELTA Agent - Task 02: Backend Task Management APIs Implementation

**Assignment Date**: Critical Blocker Resolution  
**Worktree**: Create new worktree `../leenvibe-backend-task-apis`  
**Branch**: `feature/backend-task-apis`  
**Status**: 🚨 **CRITICAL PRIORITY** - Unblocks Kanban Integration

## Mission Brief

Critical discovery! While reviewing system integration, we found that **KAPPA's completed Kanban Board UI** (2,662+ lines of iOS code) cannot be integrated because the **Backend Task Management APIs are missing**. This is blocking a major MVP feature that's ready to deploy.

## Context & Critical Impact

- ✅ **KAPPA's Kanban UI**: Complete iOS implementation ready for integration
- ✅ **iOS Dashboard**: Fully integrated and functional
- ✅ **Voice System**: Integrated with wake phrase detection
- ❌ **MISSING**: Backend Task Management APIs that Kanban UI expects
- 🚨 **BLOCKING**: Cannot integrate 2,662+ lines of completed Kanban work

## Your Critical Mission

Implement the **Backend Task Management APIs** that the iOS Kanban Board expects, enabling immediate integration of KAPPA's completed UI work and unblocking this major MVP feature.

## 🔍 Required API Analysis

### APIs Expected by iOS Kanban Board
Based on KAPPA's iOS implementation in `/Users/bogdan/work/leenvibe-ios-kanban`, the following APIs are expected:

```python
# Task Management Endpoints (Missing)
POST   /api/tasks                     # Create new task
GET    /api/tasks                     # List all tasks  
GET    /api/tasks/{task_id}           # Get specific task
PUT    /api/tasks/{task_id}           # Update task
DELETE /api/tasks/{task_id}           # Delete task
PUT    /api/tasks/{task_id}/status    # Update task status
PUT    /api/tasks/{task_id}/column    # Move task between columns

# Kanban Board Endpoints (Missing)
GET    /api/kanban/board              # Get full board state
POST   /api/kanban/tasks              # Create task in specific column
PUT    /api/kanban/tasks/{task_id}/move # Move task between columns

# Agent Decision Endpoints (Missing) 
GET    /api/decisions                 # List pending decisions
POST   /api/decisions/{decision_id}/approve   # Approve decision
POST   /api/decisions/{decision_id}/reject    # Reject decision
```

## 🛠️ Backend Implementation Plan

### 1. Task Data Models
**File**: `leenvibe-backend/app/models/task.py`
```python
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid
from datetime import datetime

class Task(Base):
    """Task model matching iOS Kanban expectations"""
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False)  # backlog, in_progress, testing, done
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to = Column(String(100))
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    tags = Column(Text)  # JSON string of tags
    
    # Agent decision tracking
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)

class AgentDecision(Base):
    """Agent decision model for approval workflow"""
    __tablename__ = "agent_decisions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), nullable=True)
    decision_type = Column(String(50), nullable=False)  # task_creation, status_change, etc.
    description = Column(Text)
    confidence_score = Column(Float)
    reasoning = Column(Text)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime)
    decided_by = Column(String(100))
```

### 2. API Endpoints Implementation
**File**: `leenvibe-backend/app/api/endpoints/tasks.py`
```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...database import get_db
from ...models.task import Task, AgentDecision
from ...schemas.task import TaskCreate, TaskUpdate, TaskResponse, KanbanBoard

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create new task for Kanban board"""
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List tasks with optional filtering"""
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    return query.all()

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, db: Session = Depends(get_db)):
    """Get specific task details"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: UUID, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update task details"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task

@router.put("/{task_id}/status")
async def update_task_status(task_id: UUID, new_status: str, db: Session = Depends(get_db)):
    """Update task status (for drag-and-drop)"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = new_status
    task.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "updated", "task_id": task_id, "new_status": new_status}
```

### 3. Kanban Board Endpoints
**File**: `leenvibe-backend/app/api/endpoints/kanban.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List

from ...database import get_db
from ...models.task import Task
from ...schemas.task import KanbanBoard, KanbanColumn

router = APIRouter(prefix="/api/kanban", tags=["kanban"])

@router.get("/board", response_model=KanbanBoard)
async def get_kanban_board(db: Session = Depends(get_db)):
    """Get full Kanban board state with all columns"""
    tasks = db.query(Task).all()
    
    # Group tasks by status/column
    columns = {
        "backlog": [],
        "in_progress": [],
        "testing": [],
        "done": []
    }
    
    for task in tasks:
        if task.status in columns:
            columns[task.status].append(task)
    
    return KanbanBoard(
        columns=[
            KanbanColumn(id="backlog", title="Backlog", tasks=columns["backlog"]),
            KanbanColumn(id="in_progress", title="In Progress", tasks=columns["in_progress"]),
            KanbanColumn(id="testing", title="Testing", tasks=columns["testing"]),
            KanbanColumn(id="done", title="Done", tasks=columns["done"])
        ]
    )

@router.put("/tasks/{task_id}/move")
async def move_task(task_id: UUID, target_column: str, position: int = 0, db: Session = Depends(get_db)):
    """Move task between Kanban columns"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = target_column
    task.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "status": "moved", 
        "task_id": task_id, 
        "from_column": task.status,
        "to_column": target_column,
        "position": position
    }
```

### 4. Integration with Main FastAPI App
**Update**: `leenvibe-backend/app/main.py`
```python
# Add to existing imports
from .api.endpoints.tasks import router as tasks_router
from .api.endpoints.kanban import router as kanban_router

# Add to existing router registration
app.include_router(tasks_router)
app.include_router(kanban_router)
```

## 🔌 iOS Integration Points

### WebSocket Real-time Updates
```python
# Add to WebSocket handler in main.py
async def broadcast_task_update(task_id: str, action: str, data: dict):
    """Broadcast task updates to iOS app"""
    message = {
        "type": "task_update",
        "task_id": task_id,
        "action": action,  # created, updated, moved, deleted
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Broadcast to all connected iOS clients
    for client_id, websocket in active_connections.items():
        try:
            await websocket.send_json(message)
        except:
            # Handle disconnected clients
            pass
```

### Backend Event Integration
```python
# Integration with existing backend AI services
class TaskEventHandler:
    """Handle task events from AI agent"""
    
    def on_analysis_complete(self, analysis_result):
        """Create task when AI analysis suggests action"""
        if analysis_result.requires_action:
            task = Task(
                title=f"Address: {analysis_result.issue}",
                description=analysis_result.recommendation,
                confidence_score=analysis_result.confidence,
                requires_approval=True if analysis_result.confidence < 0.8 else False
            )
            # Save and broadcast to iOS
            
    def on_code_change_detected(self, file_path, change_type):
        """Create tasks for code changes that need review"""
        # Auto-generate tasks based on code analysis
```

## 📊 Success Criteria

### Critical Integration Goals
- [ ] All iOS Kanban Board API calls work without errors
- [ ] Tasks can be created, read, updated, deleted via API
- [ ] Drag-and-drop functionality works with backend persistence
- [ ] Real-time WebSocket updates reach iOS app
- [ ] Agent decision approval workflow functional
- [ ] Database persistence working with proper migrations

### iOS Kanban Integration
- [ ] KAPPA's Kanban UI successfully connects to new APIs
- [ ] Task creation from iOS saves to backend database
- [ ] Drag-and-drop between columns updates backend state
- [ ] Real-time updates appear instantly in iOS interface
- [ ] Confidence indicators and approval flows working

## 🚨 Critical Priority Context

**This is the #1 blocker preventing Kanban integration:**
- KAPPA delivered 2,662+ lines of sophisticated Kanban UI
- iOS implementation is complete and tested
- **Only missing piece**: Backend APIs you're implementing
- **Immediate Impact**: Unlocks major MVP feature for production

## Timeline & Urgency

**Week 1 - CRITICAL**: Core Task Management APIs, basic CRUD operations
**Week 2**: Advanced features, agent integration, real-time updates

## Expected Outcome

**Immediate Kanban Integration**: KAPPA's completed iOS Kanban Board becomes fully functional with backend persistence, unlocking a major MVP feature and demonstrating the complete iOS ↔ Backend integration.

Your backend API expertise is **critical** for completing the MVP promise and enabling the sophisticated iOS features the team has built! 🚀💻⚡️

## Priority

**🚨 CRITICAL** - This unblocks 2,662+ lines of completed iOS work and enables immediate integration of a major MVP feature. Your success directly enables the team's iOS achievements to reach production.

**Task 2**: Backend Task Management APIs - Bridge the final gap between iOS excellence and backend functionality!