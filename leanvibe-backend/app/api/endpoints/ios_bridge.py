"""
iOS App Integration API Endpoints

Provides seamless integration between the backend and iOS companion app,
enabling real-time synchronization, notifications, and cross-platform workflows.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router for iOS integration endpoints
router = APIRouter(
    prefix="/api/ios",
    tags=["ios"],
    responses={
        404: {"description": "iOS resource not found"},
        500: {"description": "iOS integration error"},
    }
)

# Pydantic models for iOS integration
class IOSNotificationRequest(BaseModel):
    message: str
    title: Optional[str] = "LeanVibe"
    priority: str = "medium"
    category: Optional[str] = "general"
    action_url: Optional[str] = None
    timestamp: Optional[str] = None
    source: str = "backend"

class IOSSyncRequest(BaseModel):
    force: bool = False
    timestamp: Optional[str] = None

class IOSProjectPushRequest(BaseModel):
    projects: List[Dict[str, Any]]

class IOSTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    project_id: Optional[str] = None
    created_by: str = "system"

class IOSTaskUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    updated_by: str = "system"

class IOSLaunchRequest(BaseModel):
    screen: Optional[str] = None
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    source: str = "backend"

# Mock iOS state management (in production, this would be a proper database)
ios_state = {
    "connected_devices": {},
    "sync_status": {
        "projects": {"last_sync": None, "count": 0},
        "tasks": {"last_sync": None, "count": 0},
        "metrics": {"last_sync": None, "count": 0}
    },
    "notifications": [],
    "events": []
}

@router.get("/status")
async def get_ios_status():
    """
    Get iOS app connection status
    
    Returns information about connected iOS devices and sync status.
    """
    try:
        connected_count = len(ios_state["connected_devices"])
        
        return {
            "connected": connected_count > 0,
            "device_count": connected_count,
            "devices": list(ios_state["connected_devices"].keys()),
            "sync_status": ios_state["sync_status"],
            "last_activity": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting iOS status: {e}")
        return {"connected": False, "error": str(e)}

@router.get("/details")
async def get_ios_details():
    """
    Get detailed iOS connection information
    
    Provides comprehensive details about connected iOS devices and their capabilities.
    """
    try:
        details = {}
        
        for device_id, device_info in ios_state["connected_devices"].items():
            details[device_id] = {
                **device_info,
                "connection_time": device_info.get("connected_at", "Unknown"),
                "last_sync": device_info.get("last_sync", "Never"),
                "capabilities": device_info.get("capabilities", []),
                "app_version": device_info.get("app_version", "Unknown")
            }
        
        return {
            "devices": details,
            "total_notifications_sent": len(ios_state["notifications"]),
            "total_events": len(ios_state["events"]),
            "sync_statistics": ios_state["sync_status"]
        }
    except Exception as e:
        logger.error(f"Error getting iOS details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get iOS details: {str(e)}")

@router.post("/notify")
async def send_ios_notification(notification: IOSNotificationRequest, background_tasks: BackgroundTasks):
    """
    Send notification to iOS app
    
    Sends a push notification or in-app notification to connected iOS devices.
    """
    try:
        notification_data = {
            "id": len(ios_state["notifications"]) + 1,
            "message": notification.message,
            "title": notification.title,
            "priority": notification.priority,
            "category": notification.category,
            "action_url": notification.action_url,
            "timestamp": notification.timestamp or datetime.now().isoformat(),
            "source": notification.source,
            "sent_at": datetime.now().isoformat(),
            "recipients": list(ios_state["connected_devices"].keys())
        }
        
        # Store notification
        ios_state["notifications"].append(notification_data)
        
        # In production, this would send actual push notifications
        background_tasks.add_task(mock_send_notification, notification_data)
        
        return {
            "success": True,
            "notification_id": notification_data["id"],
            "recipients": len(notification_data["recipients"]),
            "message": f"Notification sent: {notification.message}"
        }
    except Exception as e:
        logger.error(f"Error sending iOS notification: {e}")
        return {"success": False, "error": str(e)}

@router.get("/projects")
async def get_ios_projects():
    """
    Get projects from iOS app
    
    Retrieves the current list of projects as known by the iOS app.
    """
    try:
        # In production, this would query the iOS app state
        # For now, return mock data that matches backend projects
        from ...services.project_service import ProjectService
        project_service = ProjectService()
        
        backend_projects = await project_service.get_all_projects()
        
        # Convert to iOS-compatible format
        ios_projects = []
        for project in backend_projects:
            ios_projects.append({
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "health_score": project.health_score,
                "last_updated": project.updated_at.isoformat(),
                "ios_sync_status": "synced"
            })
        
        return {
            "projects": ios_projects,
            "total": len(ios_projects),
            "last_sync": ios_state["sync_status"]["projects"]["last_sync"]
        }
    except Exception as e:
        logger.error(f"Error getting iOS projects: {e}")
        return {"projects": [], "total": 0, "error": str(e)}

@router.post("/sync/projects")
async def sync_ios_projects(request: IOSSyncRequest):
    """
    Sync projects with iOS app
    
    Synchronizes project data between backend and iOS app.
    """
    try:
        # Update sync status
        ios_state["sync_status"]["projects"]["last_sync"] = datetime.now().isoformat()
        
        # In production, this would perform actual synchronization
        from ...services.project_service import ProjectService
        project_service = ProjectService()
        projects = await project_service.get_all_projects()
        
        ios_state["sync_status"]["projects"]["count"] = len(projects)
        
        return {
            "success": True,
            "count": len(projects),
            "last_sync": ios_state["sync_status"]["projects"]["last_sync"],
            "forced": request.force
        }
    except Exception as e:
        logger.error(f"Error syncing iOS projects: {e}")
        return {"success": False, "error": str(e)}

@router.post("/sync/tasks")
async def sync_ios_tasks(request: IOSSyncRequest):
    """
    Sync tasks with iOS app
    
    Synchronizes task data between backend and iOS app.
    """
    try:
        # Update sync status
        ios_state["sync_status"]["tasks"]["last_sync"] = datetime.now().isoformat()
        
        # In production, this would perform actual synchronization
        from ...services.task_service import task_service
        tasks = await task_service.list_tasks()
        
        ios_state["sync_status"]["tasks"]["count"] = len(tasks)
        
        return {
            "success": True,
            "count": len(tasks),
            "last_sync": ios_state["sync_status"]["tasks"]["last_sync"],
            "forced": request.force
        }
    except Exception as e:
        logger.error(f"Error syncing iOS tasks: {e}")
        return {"success": False, "error": str(e)}

@router.post("/sync/metrics")
async def sync_ios_metrics(request: IOSSyncRequest):
    """
    Sync metrics with iOS app
    
    Synchronizes metrics and analytics data between backend and iOS app.
    """
    try:
        # Update sync status
        ios_state["sync_status"]["metrics"]["last_sync"] = datetime.now().isoformat()
        ios_state["sync_status"]["metrics"]["count"] = 100  # Mock metric count
        
        return {
            "success": True,
            "count": 100,  # Mock metric count
            "last_sync": ios_state["sync_status"]["metrics"]["last_sync"],
            "forced": request.force
        }
    except Exception as e:
        logger.error(f"Error syncing iOS metrics: {e}")
        return {"success": False, "error": str(e)}

@router.post("/projects/push")
async def push_projects_to_ios(request: IOSProjectPushRequest):
    """
    Push projects to iOS app
    
    Sends project updates from backend to iOS app.
    """
    try:
        # In production, this would push to actual iOS devices
        pushed_count = len(request.projects)
        
        # Update sync status
        ios_state["sync_status"]["projects"]["last_sync"] = datetime.now().isoformat()
        ios_state["sync_status"]["projects"]["count"] = pushed_count
        
        return {
            "success": True,
            "count": pushed_count,
            "pushed_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error pushing projects to iOS: {e}")
        return {"success": False, "error": str(e)}

@router.post("/projects/pull")
async def pull_projects_from_ios():
    """
    Pull projects from iOS app
    
    Retrieves project updates from iOS app to backend.
    """
    try:
        # In production, this would pull from actual iOS devices
        # For now, return current backend projects as if they came from iOS
        from ...services.project_service import ProjectService
        project_service = ProjectService()
        projects = await project_service.get_all_projects()
        
        # Convert to dict format
        project_dicts = []
        for project in projects:
            project_dicts.append({
                "id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "health_score": project.health_score,
                "updated_at": project.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "count": len(project_dicts),
            "projects": project_dicts,
            "pulled_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error pulling projects from iOS: {e}")
        return {"success": False, "error": str(e)}

@router.post("/tasks")
async def create_ios_task(task: IOSTaskRequest):
    """
    Create task on iOS app
    
    Creates a new task that will be synchronized with the iOS app.
    """
    try:
        # Use the existing task service to create the task
        from ...services.task_service import task_service
        from ...models.task_models import TaskCreate
        
        task_data = TaskCreate(
            title=task.title,
            description=task.description or "",
            status=task.status,
            priority=task.priority,
            project_id=task.project_id
        )
        
        created_task = await task_service.create_task(task_data)
        
        return {
            "success": True,
            "task_id": created_task.id,
            "message": f"Task created: {task.title}"
        }
    except Exception as e:
        logger.error(f"Error creating iOS task: {e}")
        return {"success": False, "error": str(e)}

@router.put("/tasks/{task_id}")
async def update_ios_task(task_id: str, update: IOSTaskUpdateRequest):
    """
    Update task on iOS app
    
    Updates an existing task that will be synchronized with the iOS app.
    """
    try:
        # Use the existing task service to update the task
        from ...services.task_service import task_service
        from ...models.task_models import TaskUpdate
        
        # Build update data, only including non-None fields
        update_data = {}
        if update.status is not None:
            update_data["status"] = update.status
        if update.priority is not None:
            update_data["priority"] = update.priority
        if update.title is not None:
            update_data["title"] = update.title
        if update.description is not None:
            update_data["description"] = update.description
        
        task_update = TaskUpdate(**update_data)
        updated_task = await task_service.update_task(task_id, task_update)
        
        if updated_task:
            return {
                "success": True,
                "task_id": task_id,
                "message": "Task updated successfully"
            }
        else:
            return {"success": False, "error": "Task not found"}
    except Exception as e:
        logger.error(f"Error updating iOS task: {e}")
        return {"success": False, "error": str(e)}

@router.get("/tasks")
async def get_ios_tasks(status: Optional[str] = None):
    """
    Get tasks from iOS app
    
    Retrieves tasks that are synchronized with the iOS app.
    """
    try:
        # Use the existing task service to get tasks
        from ...services.task_service import task_service
        from ...models.task_models import TaskFilters
        
        filters = None
        if status:
            filters = TaskFilters(status=status)
        
        tasks = await task_service.list_tasks(filters)
        
        # Convert to iOS-compatible format
        ios_tasks = []
        for task in tasks:
            ios_tasks.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            })
        
        return {
            "tasks": ios_tasks,
            "total": len(ios_tasks),
            "filter": status
        }
    except Exception as e:
        logger.error(f"Error getting iOS tasks: {e}")
        return {"tasks": [], "total": 0, "error": str(e)}

@router.post("/launch")
async def launch_ios_app(request: IOSLaunchRequest):
    """
    Launch iOS app with specific screen or content
    
    Sends a launch request to the iOS app to open a specific screen or content.
    """
    try:
        # In production, this would send an actual launch intent to iOS
        launch_data = {
            "screen": request.screen,
            "project_id": request.project_id,
            "task_id": request.task_id,
            "source": request.source,
            "launched_at": datetime.now().isoformat()
        }
        
        # Store launch event
        ios_state["events"].append({
            "type": "app_launch",
            "data": launch_data,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "message": "iOS app launch request sent",
            "target": request.screen or "default"
        }
    except Exception as e:
        logger.error(f"Error launching iOS app: {e}")
        return {"success": False, "error": str(e)}

# Background task functions
async def mock_send_notification(notification_data: Dict[str, Any]):
    """Mock function to simulate sending notifications to iOS devices"""
    logger.info(f"Mock notification sent: {notification_data['message']}")
    # In production, this would integrate with APNs or similar service