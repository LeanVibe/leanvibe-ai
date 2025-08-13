"""
MVP Service - Integration between Assembly Line System and LeanVibe Platform
Handles MVP project lifecycle, assembly line orchestration, and tenant management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

# from ..core.database import get_db  # Will be imported when needed to avoid circular dependencies
from ..models.mvp_models import MVPProject, MVPStatus, TechnicalBlueprint, FounderInterview
from ..models.orm_models import MVPProjectORM  # ORM model for persistence
from ..models.tenant_models import TenantType, TenantPlan
from ..services.assembly_line_system import AssemblyLineOrchestrator, AgentType, AgentStatus
from ..core.database import get_database_session
# from ..services.tenant_service import tenant_service  # Will be imported when proper integration is added

logger = logging.getLogger(__name__)


class MVPServiceError(Exception):
    """Custom exception for MVP service errors"""
    pass


class MVPService:
    """Service for managing MVP projects and assembly line integration"""
    
    def __init__(self):
        self.orchestrator = AssemblyLineOrchestrator()
        self.orchestrator.register_all_agents()
        self._generation_progress: Dict[UUID, Dict[str, Any]] = {}
        self._generation_logs: Dict[UUID, List[Dict[str, Any]]] = {}
        # In-memory storage retained as fallback; primary persistence via database
        self._projects_storage: Dict[UUID, MVPProject] = {}
        self._projects_by_tenant: Dict[UUID, List[UUID]] = {}
        # In-memory blueprint version history per project (newest last)
        self._blueprint_history: Dict[UUID, List[TechnicalBlueprint]] = {}
    
    async def create_mvp_project(
        self,
        tenant_id: UUID,
        founder_interview: FounderInterview,
        priority: str = "normal"
    ) -> MVPProject:
        """Create a new MVP project from founder interview"""
        try:
            # Validate tenant can create MVP projects
            await self._validate_mvp_creation_quota(tenant_id)
            
            # Generate project ID and slug
            project_id = uuid4()
            project_name = f"MVP Project {project_id.hex[:8]}"  # Extract name from business idea if needed
            slug = f"mvp-{project_id.hex[:8]}"
            
            # Create MVP project record
            mvp_project = MVPProject(
                id=project_id,
                tenant_id=tenant_id,
                project_name=project_name,
                slug=slug,
                description=founder_interview.business_idea[:200] + "..." if len(founder_interview.business_idea) > 200 else founder_interview.business_idea,
                status=MVPStatus.BLUEPRINT_PENDING,
                interview=founder_interview,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Persist
            await self._save_mvp_project(mvp_project)
            
            logger.info(f"Created MVP project {project_id} for tenant {tenant_id}")
            return mvp_project
            
        except Exception as e:
            logger.error(f"Failed to create MVP project: {e}")
            raise MVPServiceError(f"MVP project creation failed: {str(e)}")
    
    async def start_mvp_generation(
        self,
        mvp_project_id: UUID,
        technical_blueprint: TechnicalBlueprint
    ) -> bool:
        """Start the MVP generation process using the assembly line system"""
        try:
            # Validate project exists and is in correct state
            mvp_project = await self._get_mvp_project(mvp_project_id)
            if not mvp_project:
                raise MVPServiceError(f"MVP project {mvp_project_id} not found")
            
            if mvp_project.status not in [MVPStatus.BLUEPRINT_PENDING, MVPStatus.FAILED]:
                raise MVPServiceError(f"MVP project is in {mvp_project.status} state, cannot start generation")
            
            # Validate tenant quota
            await self._validate_generation_quota(mvp_project.tenant_id)
            
            # Update project status and blueprint
            mvp_project.status = MVPStatus.GENERATING
            mvp_project.blueprint = technical_blueprint
            mvp_project.updated_at = datetime.utcnow()
            
            await self._update_mvp_project(mvp_project)
            
            # Initialize progress tracking
            self._generation_progress[mvp_project_id] = {
                "current_stage": "initializing",
                "overall_progress": 0.0,
                "stage_progress": 0.0,
                "estimated_completion": datetime.utcnow() + timedelta(
                    hours=technical_blueprint.estimated_generation_time
                ),
                "stages_completed": [],
                "current_stage_details": "Initializing assembly line system..."
            }
            self._generation_logs[mvp_project_id] = []
            self._add_log(mvp_project_id, level="INFO", message="Pipeline start requested", stage="blueprint_generation")
            
            # Start assembly line in background
            asyncio.create_task(self._run_assembly_line(mvp_project_id, technical_blueprint))
            
            logger.info(f"Started MVP generation for project {mvp_project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MVP generation: {e}")
            # Update project status to failed
            try:
                mvp_project = await self._get_mvp_project(mvp_project_id)
                if mvp_project:
                    mvp_project.status = MVPStatus.FAILED
                    mvp_project.error_message = str(e)
                    await self._update_mvp_project(mvp_project)
            except Exception as update_error:
                logger.error(f"Failed to update project status after error: {update_error}")
            
            raise MVPServiceError(f"Failed to start MVP generation: {str(e)}")

    # Blueprint revision history API (in-memory, best-effort)
    def record_blueprint_revision(self, mvp_project_id: UUID, blueprint: TechnicalBlueprint) -> None:
        try:
            if mvp_project_id not in self._blueprint_history:
                self._blueprint_history[mvp_project_id] = []
            self._blueprint_history[mvp_project_id].append(blueprint)
        except Exception:
            pass

    def get_blueprint_history_inmemory(self, mvp_project_id: UUID) -> List[TechnicalBlueprint]:
        return list(self._blueprint_history.get(mvp_project_id, []))
    
    async def get_mvp_project(self, mvp_project_id: UUID) -> Optional[MVPProject]:
        """Get MVP project by ID"""
        return await self._get_mvp_project(mvp_project_id)
    
    async def get_tenant_mvp_projects(
        self,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[MVPProject]:
        """Get all MVP projects for a tenant"""
        try:
            # Primary: load from database
            projects: List[MVPProject] = []
            try:
                async for session in get_database_session():
                    stmt = (
                        select(MVPProjectORM)
                        .where(MVPProjectORM.tenant_id == tenant_id)
                        .order_by(MVPProjectORM.created_at.desc())
                        .offset(offset)
                        .limit(limit)
                    )
                    result = await session.execute(stmt)
                    rows = result.scalars().all()
                    for row in rows:
                        projects.append(self._orm_to_model(row))
                    break
            except Exception:
                # Fallback to in-memory if DB not available
                project_ids = self._projects_by_tenant.get(tenant_id, [])
                paginated_ids = project_ids[offset:offset + limit]
                for project_id in paginated_ids:
                    if project_id in self._projects_storage:
                        projects.append(self._projects_storage[project_id])
            return projects
                
        except Exception as e:
            logger.error(f"Failed to get tenant MVP projects: {e}")
            raise MVPServiceError(f"Failed to retrieve MVP projects: {str(e)}")
    
    async def get_generation_progress(self, mvp_project_id: UUID) -> Optional[Dict[str, Any]]:
        """Get real-time generation progress for an MVP project"""
        if mvp_project_id in self._generation_progress:
            return self._generation_progress[mvp_project_id].copy()
        
        # If not in memory, check if project is completed/failed
        mvp_project = await self._get_mvp_project(mvp_project_id)
        if not mvp_project:
            return None
            
        if mvp_project.status == MVPStatus.DEPLOYED:
            return {
                "current_stage": "completed",
                "overall_progress": 100.0,
                "stage_progress": 100.0,
                "estimated_completion": mvp_project.completed_at,
                "stages_completed": ["backend", "frontend", "infrastructure", "observability"],
                "current_stage_details": "MVP generation completed successfully"
            }
        elif mvp_project.status == MVPStatus.FAILED:
            return {
                "current_stage": "failed",
                "overall_progress": 0.0,
                "stage_progress": 0.0,
                "estimated_completion": None,
                "stages_completed": [],
                "current_stage_details": f"Generation failed: {mvp_project.error_message}"
            }
        
        return None
    
    async def cancel_mvp_generation(self, mvp_project_id: UUID) -> bool:
        """Cancel ongoing MVP generation"""
        try:
            mvp_project = await self._get_mvp_project(mvp_project_id)
            if not mvp_project:
                return False
                
            if mvp_project.status != MVPStatus.GENERATING:
                return False
            
            # Update project status
            mvp_project.status = MVPStatus.CANCELLED
            mvp_project.cancelled_at = datetime.utcnow()
            await self._update_mvp_project(mvp_project)
            
            # Clean up progress tracking
            if mvp_project_id in self._generation_progress:
                del self._generation_progress[mvp_project_id]
            
            logger.info(f"Cancelled MVP generation for project {mvp_project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel MVP generation: {e}")
            return False

    async def pause_mvp_generation(self, mvp_project_id: UUID) -> bool:
        """Pause generation between agent stages."""
        try:
            mvp_project = await self._get_mvp_project(mvp_project_id)
            if not mvp_project or mvp_project.status != MVPStatus.GENERATING:
                return False
            paused = await self.orchestrator.pause_generation(mvp_project_id)
            if paused:
                mvp_project.status = MVPStatus.PAUSED
                await self._update_mvp_project(mvp_project)
                self._add_log(mvp_project_id, level="INFO", message="Pipeline paused", stage="backend_development")
            return paused
        except Exception as e:
            logger.error(f"Failed to pause MVP generation: {e}")
            return False

    async def resume_mvp_generation(self, mvp_project_id: UUID) -> bool:
        """Resume generation after pause."""
        try:
            mvp_project = await self._get_mvp_project(mvp_project_id)
            if not mvp_project or mvp_project.status != MVPStatus.PAUSED:
                return False
            resumed = await self.orchestrator.resume_generation(mvp_project_id)
            if resumed:
                mvp_project.status = MVPStatus.GENERATING
                await self._update_mvp_project(mvp_project)
                self._add_log(mvp_project_id, level="INFO", message="Pipeline resumed", stage="backend_development")
            return resumed
        except Exception as e:
            logger.error(f"Failed to resume MVP generation: {e}")
            return False
    
    # Private methods
    
    async def _run_assembly_line(
        self,
        mvp_project_id: UUID,
        technical_blueprint: TechnicalBlueprint
    ):
        """Run the assembly line system for MVP generation"""
        try:
            # Set up progress callback
            async def progress_callback(agent_type: AgentType, status: AgentStatus, progress: float):
                await self._update_generation_progress(
                    mvp_project_id, agent_type, status, progress
                )
            
            # Execute assembly line
            success = await self.orchestrator.start_mvp_generation(
                mvp_project_id,
                technical_blueprint,
                priority="normal"
            )
            
            # Update final status
            mvp_project = await self._get_mvp_project(mvp_project_id)
            if mvp_project:
                if success:
                    mvp_project.status = MVPStatus.DEPLOYED
                    mvp_project.completed_at = datetime.utcnow()
                    # generation_started_at may not be set in mock; protect calculation
                    try:
                        mvp_project.generation_duration = (
                            datetime.utcnow() - mvp_project.generation_started_at
                        ).total_seconds()  # type: ignore[attr-defined]
                    except Exception:
                        pass
                    self._add_log(mvp_project_id, level="INFO", message="Pipeline completed successfully", stage="deployment")
                else:
                    mvp_project.status = MVPStatus.FAILED
                    mvp_project.error_message = "Assembly line execution failed"
                    self._add_log(mvp_project_id, level="ERROR", message=mvp_project.error_message, stage="backend_development")
                
                await self._update_mvp_project(mvp_project)
            
            # Clean up progress tracking
            if mvp_project_id in self._generation_progress:
                del self._generation_progress[mvp_project_id]
            
            logger.info(f"Assembly line completed for project {mvp_project_id} with success: {success}")
            
        except Exception as e:
            logger.error(f"Assembly line execution failed: {e}")
            
            # Update project status to failed
            try:
                mvp_project = await self._get_mvp_project(mvp_project_id)
                if mvp_project:
                    mvp_project.status = MVPStatus.FAILED
                    mvp_project.error_message = str(e)
                    await self._update_mvp_project(mvp_project)
                    self._add_log(mvp_project_id, level="ERROR", message=f"Pipeline failed: {e}", stage="backend_development")
            except Exception as update_error:
                logger.error(f"Failed to update project after assembly line failure: {update_error}")
    
    async def _update_generation_progress(
        self,
        mvp_project_id: UUID,
        agent_type: AgentType,
        status: AgentStatus,
        progress: float
    ):
        """Update generation progress tracking"""
        if mvp_project_id not in self._generation_progress:
            return
        
        progress_data = self._generation_progress[mvp_project_id]
        
        # Update current stage
        progress_data["current_stage"] = agent_type.value
        progress_data["stage_progress"] = progress
        
        # Calculate overall progress based on stage
        stage_weights = {
            AgentType.BACKEND: 0.30,
            AgentType.FRONTEND: 0.30, 
            AgentType.INFRASTRUCTURE: 0.25,
            AgentType.OBSERVABILITY: 0.15
        }
        
        completed_stages = progress_data["stages_completed"]
        completed_weight = sum(stage_weights.get(stage, 0) for stage in completed_stages)
        current_weight = stage_weights.get(agent_type, 0) * (progress / 100.0)
        
        progress_data["overall_progress"] = (completed_weight + current_weight) * 100
        
        # Update stage details and add logs
        if status == AgentStatus.RUNNING:
            progress_data["current_stage_details"] = f"Executing {agent_type.value} agent ({progress:.1f}%)"
            self._add_log(mvp_project_id, level="INFO", message=progress_data["current_stage_details"], stage=agent_type.value)
        elif status == AgentStatus.COMPLETED:
            if agent_type not in completed_stages:
                progress_data["stages_completed"].append(agent_type)
            progress_data["current_stage_details"] = f"Completed {agent_type.value} agent"
            self._add_log(mvp_project_id, level="INFO", message=progress_data["current_stage_details"], stage=agent_type.value)
        elif status == AgentStatus.FAILED:
            progress_data["current_stage_details"] = f"Failed at {agent_type.value} agent"
            self._add_log(mvp_project_id, level="ERROR", message=progress_data["current_stage_details"], stage=agent_type.value)

        # Persist progress to database (best-effort)
        try:
            async for session in get_database_session():
                stmt = select(MVPProjectORM).where(MVPProjectORM.id == mvp_project_id)
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row:
                    # Map enum keys to strings for JSON
                    row.generation_progress = {
                        "current_stage": agent_type.value,
                        "stage_progress": progress_data.get("stage_progress", 0.0),
                        "overall_progress": progress_data.get("overall_progress", 0.0),
                        "stages_completed": [s.value if hasattr(s, 'value') else str(s) for s in progress_data.get("stages_completed", [])],
                        "current_stage_details": progress_data.get("current_stage_details", ""),
                    }
                    await session.flush()
                break
        except Exception:
            pass
    
    async def _validate_mvp_creation_quota(self, tenant_id: UUID):
        """Validate that tenant can create new MVP projects"""
        # TODO: Replace with proper tenant service integration
        logger.info(f"Validating MVP creation quota for tenant {tenant_id} (mock implementation)")
        
        # Mock validation - assume tenant is valid MVP Factory for testing
        current_projects = len(await self.get_tenant_mvp_projects(tenant_id))
        max_projects = 10  # Mock quota
        
        if current_projects >= max_projects:
            raise MVPServiceError(f"MVP project quota exceeded ({current_projects}/{max_projects})")
    
    async def _validate_generation_quota(self, tenant_id: UUID):
        """Validate that tenant can start MVP generation"""
        # TODO: Replace with proper tenant service integration
        logger.info(f"Validating generation quota for tenant {tenant_id} (mock implementation)")
        
        # Check concurrent generation quota
        generating_projects = [
            p for p in await self.get_tenant_mvp_projects(tenant_id) 
            if p.status == MVPStatus.GENERATING
        ]
        
        max_concurrent = 3  # Mock quota
        if len(generating_projects) >= max_concurrent:
            raise MVPServiceError(
                f"Concurrent generation quota exceeded ({len(generating_projects)}/{max_concurrent})"
            )
    
    async def _save_mvp_project(self, mvp_project: MVPProject):
        """Save MVP project to database"""
        # Persist to database
        try:
            async for session in get_database_session():
                orm = MVPProjectORM(
                    id=mvp_project.id,
                    tenant_id=mvp_project.tenant_id,
                    project_name=mvp_project.project_name,
                    slug=mvp_project.slug,
                    description=mvp_project.description,
                    status=mvp_project.status.value if hasattr(mvp_project.status, 'value') else str(mvp_project.status),
                    interview_data=(mvp_project.interview.model_dump() if mvp_project.interview else None),
                    blueprint_data=(mvp_project.blueprint.model_dump() if mvp_project.blueprint else None),
                    generation_progress=mvp_project.generation_progress.model_dump() if mvp_project.generation_progress else {},
                    deployment_url=mvp_project.deployment_url,
                    created_at=mvp_project.created_at,
                    updated_at=mvp_project.updated_at,
                    completed_at=mvp_project.completed_at,
                    deployed_at=mvp_project.deployed_at,
                )
                session.add(orm)
                await session.flush()
                break
            logger.info(f"Saved MVP project {mvp_project.id} to database")
        except Exception:
            # Fallback to in-memory
            self._projects_storage[mvp_project.id] = mvp_project
            if mvp_project.tenant_id not in self._projects_by_tenant:
                self._projects_by_tenant[mvp_project.tenant_id] = []
            if mvp_project.id not in self._projects_by_tenant[mvp_project.tenant_id]:
                self._projects_by_tenant[mvp_project.tenant_id].append(mvp_project.id)
            logger.info(f"Saved MVP project {mvp_project.id} to in-memory storage (DB unavailable)")

    # In-memory logs API with DB persistence (best-effort)
    def _add_log(self, mvp_project_id: UUID, *, level: str, message: str, stage: str):
        """Append a log entry in-memory and persist to DB best-effort.

        DB persistence resolves latest pipeline execution for the project
        and writes a PipelineExecutionLogORM row. If DB is unavailable or no
        execution exists yet for this project, only in-memory storage is used.
        """
        # Always keep in-memory fallback
        try:
            from datetime import datetime as _dt
            if mvp_project_id not in self._generation_logs:
                self._generation_logs[mvp_project_id] = []
            self._generation_logs[mvp_project_id].append({
                "timestamp": _dt.utcnow(),
                "level": str(level).upper(),
                "message": str(message),
                "stage": str(stage),
            })
        except Exception:
            # Swallow any in-memory logging errors
            pass

        # Best-effort async DB persistence (do not block caller)
        try:
            import asyncio as _asyncio
            _asyncio.create_task(self._persist_log_db(
                mvp_project_id=mvp_project_id,
                level=str(level).upper(),
                message=str(message),
                stage=str(stage)
            ))
        except Exception:
            # If no event loop or scheduling fails, ignore silently
            pass

    async def _persist_log_db(self, mvp_project_id: UUID, *, level: str, message: str, stage: str):
        """Persist a log entry to the database if possible.

        Resolves the latest PipelineExecutionORM for the given project to obtain
        execution_id and tenant_id. If no execution exists, attempts to fetch
        tenant_id from MVPProjectORM and skips DB write if execution is missing.
        """
        try:
            from sqlalchemy import select, desc
            from ..models.orm_models import (
                MVPProjectORM,
                PipelineExecutionORM,
                PipelineExecutionLogORM,
            )
            from ..core.database import get_database_session

            async for session in get_database_session():
                # Find latest execution for this project
                exec_stmt = (
                    select(PipelineExecutionORM)
                    .where(PipelineExecutionORM.mvp_project_id == mvp_project_id)
                    .order_by(desc(PipelineExecutionORM.started_at))
                    .limit(1)
                )
                exec_result = await session.execute(exec_stmt)
                exec_row = exec_result.scalar_one_or_none()

                if not exec_row:
                    # No execution available yet; skip DB persistence
                    break

                tenant_id = exec_row.tenant_id
                # Insert log row
                log_row = PipelineExecutionLogORM(
                    execution_id=exec_row.id,
                    tenant_id=tenant_id,
                    mvp_project_id=mvp_project_id,
                    level=level,
                    message=message,
                    stage=stage,
                )
                session.add(log_row)
                # Flush then commit to persist outside session scope
                await session.flush()
                try:
                    await session.commit()
                except Exception:
                    # Some engines autocommit; ignore commit failures
                    pass
                break
        except Exception:
            # Best-effort: ignore DB errors to avoid impacting runtime
            pass

    async def get_generation_logs(self, mvp_project_id: UUID) -> List[Dict[str, Any]]:
        return list(self._generation_logs.get(mvp_project_id, []))
    
    async def _update_mvp_project(self, mvp_project: MVPProject):
        """Update MVP project in database"""
        try:
            async for session in get_database_session():
                stmt = select(MVPProjectORM).where(MVPProjectORM.id == mvp_project.id)
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if not row:
                    # Create if missing
                    await self._save_mvp_project(mvp_project)
                    break
                row.project_name = mvp_project.project_name
                row.slug = mvp_project.slug
                row.description = mvp_project.description
                row.status = mvp_project.status.value if hasattr(mvp_project.status, 'value') else str(mvp_project.status)
                row.interview_data = (mvp_project.interview.model_dump() if mvp_project.interview else None)
                row.blueprint_data = (mvp_project.blueprint.model_dump() if mvp_project.blueprint else None)
                row.generation_progress = mvp_project.generation_progress.model_dump() if mvp_project.generation_progress else {}
                row.deployment_url = mvp_project.deployment_url
                row.completed_at = mvp_project.completed_at
                row.deployed_at = mvp_project.deployed_at
                await session.flush()
                logger.info(f"Updated MVP project {mvp_project.id} in database")
                break
        except Exception:
            # Fallback to in-memory
            self._projects_storage[mvp_project.id] = mvp_project
            logger.info(f"Updated MVP project {mvp_project.id} in memory")
    
    async def _get_mvp_project(self, mvp_project_id: UUID) -> Optional[MVPProject]:
        """Get MVP project from database (best-effort), fallback to in-memory."""
        try:
            async for session in get_database_session():
                stmt = select(MVPProjectORM).where(MVPProjectORM.id == mvp_project_id)
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row:
                    return self._orm_to_model(row)
                break
        except Exception:
            # Ignore DB engine/driver issues in light tests
            return self._projects_storage.get(mvp_project_id)
        return self._projects_storage.get(mvp_project_id)
    
    # ORM conversion method will be added when proper database integration is implemented
    def _orm_to_model(self, orm: MVPProjectORM) -> MVPProject:
        """Convert ORM to domain model MVPProject"""
        try:
            interview = None
            blueprint = None
            if orm.interview_data:
                interview = FounderInterview(**orm.interview_data)
            if orm.blueprint_data:
                blueprint = TechnicalBlueprint(**orm.blueprint_data)
            progress = orm.generation_progress or {}
            mvp = MVPProject(
                id=orm.id,
                tenant_id=orm.tenant_id,
                project_name=orm.project_name,
                slug=orm.slug,
                description=orm.description,
                status=MVPStatus(orm.status) if orm.status else MVPStatus.BLUEPRINT_PENDING,
                created_at=orm.created_at,
                updated_at=orm.updated_at,
                completed_at=orm.completed_at,
                deployed_at=orm.deployed_at,
                interview=interview,
                blueprint=blueprint,
            )
            # Populate progress
            if progress:
                try:
                    mvp.generation_progress.overall_progress_percent = int(progress.get("overall_progress", 0))
                    mvp.generation_progress.current_stage = str(progress.get("current_stage", "blueprint"))
                except Exception:
                    pass
            return mvp
        except Exception as e:
            logger.warning(f"Failed to convert ORM to model: {e}")
            return MVPProject(
                id=orm.id,
                tenant_id=orm.tenant_id,
                project_name=orm.project_name,
                slug=orm.slug,
                description=orm.description,
                status=MVPStatus(orm.status) if orm.status else MVPStatus.BLUEPRINT_PENDING,
                created_at=orm.created_at,
                updated_at=orm.updated_at,
            )
    
    # Public Database Persistence Methods (Production Ready)
    
    async def save_mvp_project(self, mvp_project: MVPProject) -> MVPProject:
        """Public method: Save MVP project to database with persistence"""
        try:
            # For now, use the existing in-memory storage
            # TODO: Replace with actual database persistence using MVPProjectORM
            await self._save_mvp_project(mvp_project)
            
            logger.info(f"MVP project saved to database: {mvp_project.project_name}")
            return mvp_project
            
        except Exception as e:
            logger.error(f"Failed to save MVP project to database: {e}")
            raise MVPServiceError(f"Database persistence failed: {e}")
    
    async def update_mvp_project(self, mvp_project: MVPProject) -> MVPProject:
        """Public method: Update MVP project in database"""
        try:
            # For now, use the existing in-memory storage
            # TODO: Replace with actual database persistence using MVPProjectORM
            mvp_project.updated_at = datetime.utcnow()
            await self._update_mvp_project(mvp_project)
            
            logger.info(f"MVP project updated in database: {mvp_project.id}")
            return mvp_project
            
        except Exception as e:
            logger.error(f"Failed to update MVP project in database: {e}")
            raise MVPServiceError(f"Database update failed: {e}")


# Global MVP service instance
mvp_service = MVPService()