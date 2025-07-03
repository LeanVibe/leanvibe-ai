from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional
import logging

from ...models.task_models import (
    Task, TaskCreate, TaskUpdate, TaskStatusUpdate, TaskMoveRequest,
    TaskFilters, TaskSearchRequest, TaskStats, KanbanBoard,
    TaskStatus, TaskPriority
)
from ...services.task_service import task_service
logger = logging.getLogger(__name__)

# Create router for task endpoints
router = APIRouter(
    prefix="/api/tasks", 
    tags=["tasks"],
    responses={
        404: {"description": "Task not found"},
        500: {"description": "Internal server error"},
    }
)

async def broadcast_task_update(action: str, task: Task, client_id: str = None):
    """Broadcast task updates to connected iOS clients"""
    try:
        # Import here to avoid circular imports
        from ...core.connection_manager import ConnectionManager
        
        update_message = {
            "type": "task_update",
            "action": action,  # "created", "updated", "deleted", "moved"
            "task": task.dict() if task else None,
            "timestamp": task.updated_at.isoformat() if task else None
        }
        
        # Get the global connection manager instance
        # Note: In production, this should be injected as a dependency
        connection_manager = ConnectionManager()
        
        # Broadcast to all connected clients or specific client
        if client_id:
            await connection_manager.send_personal_message(update_message, client_id)
        else:
            await connection_manager.broadcast(update_message)
            
    except Exception as e:
        logger.error(f"Failed to broadcast task update: {e}")

@router.post("/", response_model=Task)
async def create_task(task_data: TaskCreate, background_tasks: BackgroundTasks):
    """Create a new task for the Kanban board"""
    try:
        task = await task_service.create_task(task_data)
        
        # Broadcast task creation to connected clients
        background_tasks.add_task(broadcast_task_update, "created", task)
        
        return task
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@router.get("/", response_model=List[Task])
async def list_tasks(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    limit: int = Query(100, le=1000, description="Maximum number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip")
):
    """List all tasks with optional filtering"""
    try:
        filters = TaskFilters(
            project_id=project_id,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            tags=tags
        ) if any([project_id, status, priority, assigned_to, tags]) else None
        
        tasks = await task_service.list_tasks(filters)
        
        # Apply pagination
        return tasks[offset:offset + limit]
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")

@router.get("/project/{project_id}", response_model=List[Task])
async def get_tasks_by_project(project_id: str):
    """Get all tasks for a specific project"""
    try:
        filters = TaskFilters(project_id=project_id)
        tasks = await task_service.list_tasks(filters)
        return tasks
    except Exception as e:
        logger.error(f"Failed to get tasks for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tasks for project: {str(e)}")

@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get a specific task by ID"""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: str, updates: TaskUpdate, background_tasks: BackgroundTasks):
    """Update an existing task"""
    task = await task_service.update_task(task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Broadcast task update to connected clients
    background_tasks.add_task(broadcast_task_update, "updated", task)
    
    return task

@router.put("/{task_id}/status", response_model=Task)
async def update_task_status(task_id: str, status_update: TaskStatusUpdate, background_tasks: BackgroundTasks):
    """Update task status (for drag-and-drop operations)"""
    task = await task_service.update_task_status(task_id, status_update)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Broadcast status change to connected clients
    background_tasks.add_task(broadcast_task_update, "moved", task)
    
    return task

@router.delete("/{task_id}")
async def delete_task(task_id: str, background_tasks: BackgroundTasks):
    """Delete a task"""
    # Get task before deletion for broadcast
    task = await task_service.get_task(task_id)
    
    success = await task_service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Broadcast task deletion to connected clients
    if task:
        background_tasks.add_task(broadcast_task_update, "deleted", task)
    
    return {"success": True, "message": f"Task {task_id} deleted"}

@router.post("/{task_id}/move", response_model=Task)
async def move_task(task_id: str, move_request: TaskMoveRequest, background_tasks: BackgroundTasks):
    """Move task between Kanban columns"""
    task = await task_service.move_task(task_id, move_request)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Broadcast task move to connected clients
    background_tasks.add_task(broadcast_task_update, "moved", task)
    
    return task

@router.post("/search", response_model=List[Task])
async def search_tasks(search_request: TaskSearchRequest):
    """Search tasks with query and filters"""
    try:
        tasks = await task_service.search_tasks(search_request)
        return tasks
    except Exception as e:
        logger.error(f"Failed to search tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search tasks: {str(e)}")

@router.get("/stats/summary", response_model=TaskStats)
async def get_task_stats():
    """Get task statistics for dashboard"""
    try:
        stats = await task_service.get_task_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task stats: {str(e)}")

# Kanban Board Endpoints
@router.get("/kanban/board", response_model=KanbanBoard)
async def get_kanban_board():
    """Get complete Kanban board with all columns and tasks"""
    try:
        board = await task_service.get_kanban_board()
        return board
    except Exception as e:
        logger.error(f"Failed to get Kanban board: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Kanban board: {str(e)}")

@router.put("/kanban/tasks/{task_id}/move", response_model=Task)
async def move_kanban_task(task_id: str, move_request: TaskMoveRequest, background_tasks: BackgroundTasks):
    """Move task between Kanban columns (alternative endpoint)"""
    return await move_task(task_id, move_request, background_tasks)

# Bulk Operations
@router.post("/bulk/create", response_model=List[Task])
async def bulk_create_tasks(tasks_data: List[TaskCreate], background_tasks: BackgroundTasks):
    """Create multiple tasks at once"""
    try:
        created_tasks = []
        for task_data in tasks_data:
            task = await task_service.create_task(task_data)
            created_tasks.append(task)
        
        # Broadcast bulk creation
        for task in created_tasks:
            background_tasks.add_task(broadcast_task_update, "created", task)
        
        return created_tasks
        
    except Exception as e:
        logger.error(f"Failed to bulk create tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk create tasks: {str(e)}")

@router.put("/bulk/update-status")
async def bulk_update_status(
    task_ids: List[str], 
    status_update: TaskStatusUpdate, 
    background_tasks: BackgroundTasks
):
    """Update status for multiple tasks"""
    try:
        updated_tasks = []
        for task_id in task_ids:
            task = await task_service.update_task_status(task_id, status_update)
            if task:
                updated_tasks.append(task)
        
        # Broadcast bulk updates
        for task in updated_tasks:
            background_tasks.add_task(broadcast_task_update, "moved", task)
        
        return {
            "success": True,
            "updated_count": len(updated_tasks),
            "tasks": updated_tasks
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk update task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk update: {str(e)}")

# Utility Endpoints
@router.post("/cleanup")
async def cleanup_old_tasks(days: int = Query(90, ge=1, description="Days to keep completed tasks")):
    """Clean up old completed tasks"""
    try:
        await task_service.cleanup_old_tasks(days)
        return {"success": True, "message": f"Cleaned up tasks older than {days} days"}
    except Exception as e:
        logger.error(f"Failed to cleanup tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup tasks: {str(e)}")

@router.get("/export/json")
async def export_tasks_json(
    status: Optional[TaskStatus] = Query(None, description="Filter by status")
):
    """Export tasks as JSON"""
    try:
        filters = TaskFilters(status=status) if status else None
        tasks = await task_service.list_tasks(filters)
        
        return {
            "export_timestamp": task_service._tasks and max(t.updated_at for t in task_service._tasks.values()).isoformat(),
            "task_count": len(tasks),
            "tasks": [task.dict() for task in tasks]
        }
        
    except Exception as e:
        logger.error(f"Failed to export tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export tasks: {str(e)}")