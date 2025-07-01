# ALPHA Agent - Task 04: Backend Task Management APIs (Critical Blocker)

**Assignment Date**: Emergency Redistribution - DELTA Holiday Departure  
**Worktree**: Create `../leanvibe-backend-task-apis`  
**Branch**: `feature/backend-task-apis`  
**Status**: 🚨 **CRITICAL EMERGENCY** - Unblocks 2,662+ lines of completed Kanban UI

## Mission Brief

**EMERGENCY REASSIGNMENT**: DELTA departed for holiday before implementing critical Backend Task Management APIs. This is blocking **KAPPA's completed Kanban Board UI** (2,662+ lines) from integration. Your backend experience makes you the best candidate to resolve this critical blocker.

## Critical Context

- ✅ **KAPPA's Kanban UI**: Complete iOS implementation (2,662+ lines) waiting for backend
- ✅ **Your iOS Foundation**: Dashboard complete, perfect foundation for this work
- ✅ **Your Xcode Experience**: Can handle both backend APIs and iOS integration
- 🚨 **BLOCKING**: Major MVP feature cannot deploy without these APIs

## Your Critical Mission

Implement the **missing Backend Task Management APIs** that KAPPA's iOS Kanban Board expects, enabling immediate integration of completed UI work.

## Required APIs (From KAPPA's iOS Implementation)

### Core Task Management
```python
# FastAPI Endpoints Needed
POST   /api/tasks                     # Create new task
GET    /api/tasks                     # List all tasks  
GET    /api/tasks/{task_id}           # Get specific task
PUT    /api/tasks/{task_id}           # Update task
DELETE /api/tasks/{task_id}           # Delete task
PUT    /api/tasks/{task_id}/status    # Update task status (drag-and-drop)

# Kanban Board State
GET    /api/kanban/board              # Get full board with columns
PUT    /api/kanban/tasks/{task_id}/move # Move between columns
```

## Rapid Implementation Strategy

### 1. Database Models (SQLAlchemy)
```python
# leanvibe-backend/app/models/task.py
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="backlog")  # backlog, in_progress, testing, done
    priority = Column(String(20), default="medium")
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    assigned_to = Column(String(100))
```

### 2. FastAPI Endpoints
```python
# leanvibe-backend/app/api/endpoints/tasks.py
@router.post("/api/tasks")
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create task for Kanban board"""
    
@router.get("/api/tasks")
async def list_tasks(db: Session = Depends(get_db)):
    """List all tasks"""
    
@router.put("/api/tasks/{task_id}/status")
async def update_task_status(task_id: UUID, status: str, db: Session = Depends(get_db)):
    """Update for drag-and-drop"""

@router.get("/api/kanban/board")
async def get_kanban_board(db: Session = Depends(get_db)):
    """Get board state with columns"""
    # Return: {columns: [{id: "backlog", tasks: []}, ...]}
```

### 3. Integration Points
```python
# Add to main.py
from .api.endpoints.tasks import router as tasks_router
app.include_router(tasks_router)

# WebSocket integration for real-time updates
async def broadcast_task_update(task_id, action, data):
    # Notify iOS app of task changes
```

## Success Criteria

### Critical Integration Goals
- [ ] KAPPA's iOS Kanban UI connects successfully to APIs
- [ ] Tasks can be created, moved, updated via drag-and-drop
- [ ] Real-time WebSocket updates reach iOS app
- [ ] Database persistence working with migrations
- [ ] **IMMEDIATE**: Kanban feature unblocked for integration

## Why ALPHA is Perfect for This

1. **Backend Experience**: Your dashboard work involved backend integration
2. **iOS Understanding**: You know how the iOS side expects APIs to work  
3. **Integration Expertise**: You've successfully integrated dashboard with backend
4. **Available**: Xcode project can be delayed slightly for this critical blocker
5. **Full Stack**: Can handle both API implementation and iOS integration testing

## Timeline - EMERGENCY SPRINT

**Week 1**: Core CRUD APIs, basic Kanban endpoints, iOS integration testing
**Result**: KAPPA's 2,662+ line Kanban UI becomes fully functional

## Priority

**🚨 CRITICAL EMERGENCY** - This is the #1 blocker preventing integration of major completed feature. Your success unblocks significant completed work and enables MVP completion.

**Task 4**: Backend Task APIs - Emergency implementation to unblock completed iOS work! 🚨⚡🚀