import asyncio
import json
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import logging
from pathlib import Path
import aiofiles

from ..models.task_models import (
    Task, TaskCreate, TaskUpdate, TaskStatusUpdate, TaskMoveRequest,
    TaskFilters, TaskSearchRequest, TaskStats, KanbanBoard, KanbanColumn,
    TaskStatus, TaskPriority
)

logger = logging.getLogger(__name__)

class TaskService:
    """Service for managing tasks and Kanban board operations"""
    
    def __init__(self, data_dir: str = ".leanvibe_cache"):
        self.data_dir = Path(data_dir)
        self.tasks_file = self.data_dir / "tasks.json"
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialize the task service and load existing tasks"""
        try:
            await self._load_tasks()
            logger.info(f"TaskService initialized with {len(self._tasks)} tasks")
        except Exception as e:
            logger.error(f"Failed to initialize TaskService: {e}")
            # Initialize with empty tasks if loading fails
            self._tasks = {}
    
    async def _load_tasks(self):
        """Load tasks from persistent storage"""
        if not self.tasks_file.exists():
            self._tasks = {}
            return
        
        try:
            async with aiofiles.open(self.tasks_file, 'r') as f:
                content = await f.read()
                if content.strip():
                    data = json.loads(content)
                    self._tasks = {}
                    for task_id, task_data in data.items():
                        try:
                            # Handle legacy tasks by adding required fields
                            if 'project_id' not in task_data:
                                task_data['project_id'] = 'legacy-project'
                            if 'client_id' not in task_data:
                                task_data['client_id'] = 'legacy-client'
                            if 'confidence' not in task_data and 'confidence_score' in task_data:
                                task_data['confidence'] = task_data['confidence_score']
                            elif 'confidence' not in task_data:
                                task_data['confidence'] = 1.0
                            
                            # Map legacy status values
                            if task_data.get('status') == 'backlog':
                                task_data['status'] = 'todo'
                            if task_data.get('priority') == 'critical':
                                task_data['priority'] = 'urgent'
                            
                            # Ensure all required fields exist
                            task_data.setdefault('dependencies', [])
                            task_data.setdefault('attachments', [])
                            task_data.setdefault('tags', [])
                            
                            task = Task.parse_obj(task_data)
                            self._tasks[task_id] = task
                        except Exception as e:
                            logger.warning(f"Could not load task {task_id}: {e}")
                            continue
                else:
                    self._tasks = {}
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Could not load tasks from {self.tasks_file}: {e}")
            self._tasks = {}
    
    async def _save_tasks(self):
        """Save tasks to persistent storage"""
        try:
            # Convert tasks to serializable format
            data = {
                task_id: task.dict()
                for task_id, task in self._tasks.items()
            }
            
            async with aiofiles.open(self.tasks_file, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.error(f"Failed to save tasks to {self.tasks_file}: {e}")
    
    async def create_task(self, task_data: TaskCreate) -> Task:
        """Create a new task"""
        async with self._lock:
            # Handle legacy fields mapping
            estimated_effort = task_data.estimated_effort or task_data.estimated_hours
            
            task = Task(
                title=task_data.title,
                description=task_data.description,
                priority=task_data.priority,
                project_id=task_data.project_id,
                client_id=task_data.client_id,
                assigned_to=task_data.assigned_to,
                estimated_effort=estimated_effort,
                tags=task_data.tags,
                dependencies=task_data.dependencies,
                metadata=task_data.metadata
            )
            
            self._tasks[task.id] = task
            await self._save_tasks()
            
            logger.info(f"Created task: {task.id} - {task.title}")
            return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID"""
        return self._tasks.get(task_id)
    
    async def list_tasks(self, filters: Optional[TaskFilters] = None) -> List[Task]:
        """List all tasks with optional filtering"""
        tasks = list(self._tasks.values())
        
        if not filters:
            return tasks
        
        # Apply filters
        if filters.project_id:
            tasks = [t for t in tasks if getattr(t, 'project_id', None) == filters.project_id]
            
        if filters.status:
            tasks = [t for t in tasks if t.status == filters.status]
        
        if filters.priority:
            tasks = [t for t in tasks if t.priority == filters.priority]
        
        if filters.assigned_to:
            tasks = [t for t in tasks if t.assigned_to == filters.assigned_to]
        
        if filters.tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in filters.tags)]
        
        if filters.created_after:
            tasks = [t for t in tasks if t.created_at >= filters.created_after]
        
        if filters.created_before:
            tasks = [t for t in tasks if t.created_at <= filters.created_before]
        
        return tasks
    
    async def update_task(self, task_id: str, updates: TaskUpdate) -> Optional[Task]:
        """Update an existing task"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            
            # Apply updates
            update_data = updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(task, field, value)
            
            task.updated_at = datetime.utcnow()
            await self._save_tasks()
            
            logger.info(f"Updated task: {task_id}")
            return task
    
    async def update_task_status(self, task_id: str, status_update: TaskStatusUpdate) -> Optional[Task]:
        """Update task status (for drag and drop operations)"""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            
            old_status = task.status
            task.status = status_update.status
            task.updated_at = datetime.utcnow()
            
            await self._save_tasks()
            
            logger.info(f"Task {task_id} moved from {old_status} to {status_update.status}")
            return task
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                await self._save_tasks()
                logger.info(f"Deleted task: {task_id}")
                return True
            return False
    
    async def move_task(self, task_id: str, move_request: TaskMoveRequest) -> Optional[Task]:
        """Move task to different column/status"""
        return await self.update_task_status(task_id, TaskStatusUpdate(status=move_request.target_status))
    
    async def get_kanban_board(self) -> KanbanBoard:
        """Get complete Kanban board state"""
        tasks_by_status = {status: [] for status in TaskStatus}
        
        # Group tasks by status
        for task in self._tasks.values():
            tasks_by_status[task.status].append(task)
        
        # Create columns
        columns = []
        column_configs = [
            (TaskStatus.TODO, "To Do"),
            (TaskStatus.IN_PROGRESS, "In Progress"), 
            (TaskStatus.TESTING, "Testing"),
            (TaskStatus.DONE, "Done")
        ]
        
        for status, title in column_configs:
            column_tasks = sorted(tasks_by_status[status], key=lambda t: t.updated_at, reverse=True)
            columns.append(KanbanColumn(
                id=status.value,
                title=title,
                status=status,
                tasks=column_tasks,
                task_count=len(column_tasks)
            ))
        
        return KanbanBoard(
            columns=columns,
            total_tasks=len(self._tasks)
        )
    
    async def search_tasks(self, search_request: TaskSearchRequest) -> List[Task]:
        """Search tasks with query and filters"""
        tasks = await self.list_tasks(search_request.filters)
        
        # Apply text search if query provided
        if search_request.query:
            query = search_request.query.lower()
            tasks = [
                task for task in tasks
                if (query in task.title.lower() or 
                    (task.description and query in task.description.lower()) or
                    any(query in tag.lower() for tag in task.tags))
            ]
        
        # Apply pagination
        start = search_request.offset
        end = start + search_request.limit
        return tasks[start:end]
    
    async def get_task_stats(self) -> TaskStats:
        """Get task statistics for dashboard"""
        tasks = list(self._tasks.values())
        total_tasks = len(tasks)
        
        if total_tasks == 0:
            return TaskStats(
                total_tasks=0,
                by_status={status.value: 0 for status in TaskStatus},
                by_priority={priority.value: 0 for priority in TaskPriority},
                completion_rate=0.0
            )
        
        # Count by status - using string values for JSON compatibility
        by_status = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            status_key = task.status.value if hasattr(task.status, 'value') else str(task.status)
            if status_key in by_status:
                by_status[status_key] += 1
        
        # Count by priority - using string values for JSON compatibility
        by_priority = {priority.value: 0 for priority in TaskPriority}
        for task in tasks:
            priority_key = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
            if priority_key in by_priority:
                by_priority[priority_key] += 1
        
        # Calculate completion rate
        completed_tasks = by_status.get(TaskStatus.DONE.value, 0)
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0
        
        # Calculate average completion time for done tasks
        done_tasks = [t for t in tasks if t.status == TaskStatus.DONE]
        avg_completion_time = None
        if done_tasks:
            completion_times = [
                (task.updated_at - task.created_at).total_seconds() / 3600  # hours
                for task in done_tasks
                if task.updated_at and task.created_at
            ]
            if completion_times:
                avg_completion_time = sum(completion_times) / len(completion_times)
        
        return TaskStats(
            total_tasks=total_tasks,
            by_status=by_status,
            by_priority=by_priority,
            avg_completion_time=avg_completion_time,
            completion_rate=completion_rate
        )
    
    async def cleanup_old_tasks(self, days: int = 90):
        """Clean up tasks older than specified days"""
        if days <= 0:
            return
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with self._lock:
            tasks_to_remove = [
                task_id for task_id, task in self._tasks.items()
                if str(task.status) == TaskStatus.DONE.value and task.updated_at < cutoff_date
            ]
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
            
            if tasks_to_remove:
                await self._save_tasks()
                logger.info(f"Cleaned up {len(tasks_to_remove)} old completed tasks")

# Global task service instance
task_service = TaskService()