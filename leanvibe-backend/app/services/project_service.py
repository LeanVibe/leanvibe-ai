"""
Project service for managing project data and operations
"""

import logging
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..models.project_models import (
    Project,
    ProjectLanguage,
    ProjectMetrics,
    ProjectStatus,
    ProjectTask,
)

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing projects"""
    
    def __init__(self):
        self.logger = logger
        # In-memory storage for MVP - replace with database in production
        self._projects: Dict[UUID, Project] = {}
        self._tasks: Dict[UUID, List[ProjectTask]] = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample project data"""
        # Default tenant ID for sample data
        default_tenant_id = UUID("00000000-0000-0000-0000-000000000001")
        
        # Sample project 1: LeanVibe Backend
        backend_id = UUID("E892771D-2D70-480C-B6AF-AB06980117C0")  # Fixed UUID for iOS app compatibility
        backend_project = Project(
            id=backend_id,
            tenant_id=default_tenant_id,  # Required multi-tenant field
            display_name="LeanVibe Backend",
            description="AI-powered backend with MLX integration",
            status=ProjectStatus.ACTIVE,
            tasks_count=8,
            completed_tasks_count=6,
            issues_count=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            path="/Users/bogdan/work/leanvibe-ai/leanvibe-backend",
            language=ProjectLanguage.PYTHON,
            last_activity=datetime.now(),
            metrics=ProjectMetrics(
                files_count=42,
                lines_of_code=12345,
                health_score=0.92,  # Dynamic health score
                issues_count=1,
                test_coverage=0.78,
                performance_score=0.89
            ),
            client_id="ios-client-main"
        )
        
        # Sample project 2: iOS Client
        ios_id = UUID("B8C9A1E2-4F7D-4A8B-9C5E-1F2E3D4C5B6A")
        ios_project = Project(
            id=ios_id,
            tenant_id=default_tenant_id,  # Required multi-tenant field
            display_name="iOS Client",
            description="Swift iOS app with real-time backend integration",
            status=ProjectStatus.ACTIVE,
            tasks_count=12,
            completed_tasks_count=9,
            issues_count=2,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            path="/Users/bogdan/work/leanvibe-ai/leanvibe-ios",
            language=ProjectLanguage.SWIFT,
            last_activity=datetime.now(),
            metrics=ProjectMetrics(
                files_count=30,
                lines_of_code=6789,
                health_score=0.87,  # Dynamic health score
                issues_count=2,
                test_coverage=0.65,
                performance_score=0.82
            ),
            client_id="ios-client-main"
        )
        
        self._projects[backend_id] = backend_project
        self._projects[ios_id] = ios_project
        
        # Add sample tasks for backend project
        backend_tasks = [
            ProjectTask(
                id=uuid4(),
                project_id=backend_id,
                title="Implement project metrics API",
                description="Create REST endpoints for project metrics",
                status="completed",
                priority="high",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                completed_at=datetime.now()
            ),
            ProjectTask(
                id=uuid4(),
                project_id=backend_id,
                title="Fix MLX model loading",
                description="Resolve production model initialization issues",
                status="completed",
                priority="high",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                completed_at=datetime.now()
            ),
            ProjectTask(
                id=uuid4(),
                project_id=backend_id,
                title="Add project tasks endpoint",
                description="Create API for project task management",
                status="in_progress",
                priority="medium",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        # Add sample tasks for iOS project
        ios_tasks = [
            ProjectTask(
                id=uuid4(),
                project_id=ios_id,
                title="Fix hard-coded health scores",
                description="Replace static values with dynamic backend data",
                status="in_progress",
                priority="high",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            ProjectTask(
                id=uuid4(),
                project_id=ios_id,
                title="Improve color contrast",
                description="Fix accessibility issues in project cards",
                status="pending",
                priority="medium",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            ProjectTask(
                id=uuid4(),
                project_id=ios_id,
                title="Implement functional quick actions",
                description="Make Agent Chat, Monitor, Settings actions work",
                status="pending",
                priority="medium",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        self._tasks[backend_id] = backend_tasks
        self._tasks[ios_id] = ios_tasks
    
    async def get_all_projects(self) -> List[Project]:
        """Get all projects"""
        return list(self._projects.values())
    
    async def get_project(self, project_id: UUID) -> Optional[Project]:
        """Get project by ID"""
        return self._projects.get(project_id)
    
    async def get_project_tasks(self, project_id: UUID) -> List[ProjectTask]:
        """Get tasks for a project"""
        return self._tasks.get(project_id, [])
    
    async def get_project_metrics(self, project_id: UUID) -> Optional[ProjectMetrics]:
        """Get metrics for a project with real-time calculation"""
        project = self._projects.get(project_id)
        if not project:
            return None
        
        # Calculate dynamic metrics based on project analysis
        metrics = await self._calculate_dynamic_metrics(project)
        
        # Update the stored project with new metrics
        project.metrics = metrics
        project.updated_at = datetime.now()
        
        return metrics
    
    async def _calculate_dynamic_metrics(self, project: Project) -> ProjectMetrics:
        """Calculate dynamic project metrics"""
        try:
            # Simulate real project analysis
            project_path = Path(project.path)
            
            # Count files and lines if path exists
            files_count = 0
            lines_of_code = 0
            if project_path.exists():
                files_count = len(list(project_path.rglob("*.py" if project.language == ProjectLanguage.PYTHON else "*.swift")))
                
                # Estimate lines of code
                for file_path in project_path.rglob("*.py" if project.language == ProjectLanguage.PYTHON else "*.swift"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines_of_code += len(f.readlines())
                    except Exception:
                        continue
            
            # Calculate health score based on multiple factors
            tasks = self._tasks.get(project.id, [])
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == "completed"])
            
            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 1.0
            issue_penalty = min(project.issues_count * 0.05, 0.3)  # Max 30% penalty for issues
            
            # Base health score calculation
            health_score = max(0.0, min(1.0, completion_rate - issue_penalty + 0.1))  # +0.1 base bonus
            
            # Add some realistic variation based on project type
            if project.language == ProjectLanguage.PYTHON:
                health_score = min(1.0, health_score + 0.05)  # Python projects get slight bonus
            
            return ProjectMetrics(
                files_count=files_count or project.metrics.files_count,
                lines_of_code=lines_of_code or project.metrics.lines_of_code,
                health_score=health_score,
                issues_count=project.issues_count,
                test_coverage=project.metrics.test_coverage,
                performance_score=project.metrics.performance_score,
                last_build_time=project.metrics.last_build_time
            )
            
        except Exception as e:
            self.logger.warning(f"Error calculating metrics for project {project.id}: {e}")
            # Return existing metrics if calculation fails
            return project.metrics
    
    async def analyze_project(self, project_id: UUID) -> Dict:
        """Analyze project and return insights"""
        project = self._projects.get(project_id)
        if not project:
            return {"error": "Project not found"}
        
        # Simulate project analysis
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Update metrics
        new_metrics = await self._calculate_dynamic_metrics(project)
        project.metrics = new_metrics
        project.updated_at = datetime.now()
        
        return {
            "status": "completed",
            "metrics_updated": True,
            "health_score": new_metrics.health_score,
            "recommendations": [
                "Consider adding more unit tests to improve coverage" if new_metrics.test_coverage and new_metrics.test_coverage < 0.8 else None,
                "Address open issues to improve health score" if project.issues_count > 0 else None,
                "Project is in good health" if new_metrics.health_score > 0.8 else None
            ],
            "analysis_timestamp": datetime.now()
        }
    
    async def delete_project(self, project_id: UUID) -> bool:
        """Delete a project"""
        if project_id in self._projects:
            del self._projects[project_id]
            if project_id in self._tasks:
                del self._tasks[project_id]
            self.logger.info(f"Project {project_id} deleted successfully")
            return True
        return False