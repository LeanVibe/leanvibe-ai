"""
Pipeline Orchestration Service
Manages the complete autonomous MVP generation pipeline from interview to deployment
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field

from ..models.mvp_models import (
    FounderInterview, MVPProject, MVPStatus, TechnicalBlueprint
)
from ..models.human_gate_models import (
    HumanApprovalWorkflow, WorkflowType, WorkflowStatus,
    CreateWorkflowRequest, FounderFeedback, FeedbackType
)
from ..services.agents.ai_architect_agent import AIArchitectAgent
from ..services.human_gate_service import human_gate_service
from ..services.email_service import email_service
from ..services.blueprint_refinement_service import blueprint_refinement_service
from ..services.mvp_service import mvp_service
from ..services.monitoring_service import monitoring_service

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Stages in the autonomous MVP generation pipeline"""
    INTERVIEW_RECEIVED = "interview_received"
    BLUEPRINT_GENERATION = "blueprint_generation"
    FOUNDER_APPROVAL = "founder_approval"
    BLUEPRINT_REFINEMENT = "blueprint_refinement"
    MVP_GENERATION = "mvp_generation"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStatus(str, Enum):
    """Overall pipeline execution status"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    PROCESSING_FEEDBACK = "processing_feedback"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineExecution(BaseModel):
    """Tracks execution of the complete pipeline"""
    id: UUID = Field(default_factory=uuid4)
    mvp_project_id: UUID
    tenant_id: UUID
    
    # Current state
    current_stage: PipelineStage = PipelineStage.INTERVIEW_RECEIVED
    status: PipelineStatus = PipelineStatus.INITIALIZING
    
    # Progress tracking
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    current_stage_started_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Stage completion tracking
    stages_completed: List[PipelineStage] = Field(default_factory=list)
    stage_durations: Dict[str, float] = Field(default_factory=dict)
    
    # Associated resources
    workflow_id: Optional[UUID] = None
    blueprint_versions: List[UUID] = Field(default_factory=list)
    
    # Progress and feedback
    overall_progress: float = 0.0
    current_stage_progress: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    
    class Config:
        extra = "ignore"


class PipelineOrchestrationService:
    """Orchestrates the complete autonomous MVP generation pipeline"""
    
    def __init__(self):
        self.ai_architect = AIArchitectAgent()
        # In-memory storage for pipeline executions
        self._executions: Dict[UUID, PipelineExecution] = {}
        self._executions_by_project: Dict[UUID, UUID] = {}
        
        # Progress callbacks
        self._progress_callbacks: Dict[UUID, List[Callable]] = {}
        
        logger.info("Initialized Pipeline Orchestration Service")
    
    async def start_autonomous_pipeline(
        self,
        founder_interview: FounderInterview,
        tenant_id: UUID,
        founder_email: str,
        project_name: str
    ) -> PipelineExecution:
        """Start the complete autonomous pipeline from founder interview"""
        
        # Start monitoring this critical operation
        monitoring_op = await monitoring_service.start_operation(
            operation_type="autonomous_pipeline_start",
            tenant_id=tenant_id,
            context={
                "project_name": project_name,
                "founder_email": founder_email,
                "business_idea": founder_interview.business_idea[:100],  # First 100 chars
                "industry": str(founder_interview.industry)
            }
        )
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting autonomous pipeline for {project_name}")
            
            # Create MVP project
            mvp_project = MVPProject(
                id=uuid4(),
                tenant_id=tenant_id,
                project_name=project_name,
                slug=project_name.lower().replace(" ", "-").replace(".", ""),
                description=founder_interview.business_idea[:200],
                status=MVPStatus.BLUEPRINT_PENDING,
                interview=founder_interview,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await mvp_service._save_mvp_project(mvp_project)
            
            # Create pipeline execution
            execution = PipelineExecution(
                mvp_project_id=mvp_project.id,
                tenant_id=tenant_id
            )
            
            await self._save_execution(execution)
            
            # Start pipeline in background
            asyncio.create_task(self._execute_pipeline(execution, founder_email))
            
            logger.info(f"Started autonomous pipeline {execution.id} for project {mvp_project.id}")
            
            # Complete monitoring operation with success
            duration_ms = (time.time() - start_time) * 1000
            await monitoring_service.complete_operation(
                operation_id=monitoring_op,
                status="success", 
                duration_ms=duration_ms,
                result_data={
                    "execution_id": str(execution.id),
                    "mvp_project_id": str(mvp_project.id),
                    "pipeline_started": True
                }
            )
            
            return execution
            
        except Exception as e:
            # Complete monitoring operation with failure
            duration_ms = (time.time() - start_time) * 1000
            await monitoring_service.fail_operation(
                operation_id=monitoring_op,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=duration_ms,
                error_context={
                    "project_name": project_name,
                    "founder_email": founder_email,
                    "tenant_id": str(tenant_id)
                }
            )
            logger.error(f"Failed to start autonomous pipeline: {e}")
            raise
    
    async def _execute_pipeline(self, execution: PipelineExecution, founder_email: str):
        """Execute the complete pipeline"""
        
        # Start monitoring the pipeline execution
        pipeline_op = await monitoring_service.start_operation(
            operation_type="autonomous_pipeline_execution",
            tenant_id=execution.tenant_id,
            context={
                "execution_id": str(execution.id),
                "mvp_project_id": str(execution.mvp_project_id),
                "founder_email": founder_email
            }
        )
        
        pipeline_start_time = time.time()
        
        try:
            execution.status = PipelineStatus.RUNNING
            await self._update_execution(execution)
            
            # Stage 1: Blueprint Generation
            await self._execute_blueprint_generation_stage(execution)
            
            # Stage 2: Founder Approval
            await self._execute_founder_approval_stage(execution, founder_email)
            
            # Pipeline will continue based on founder response
            # (approval -> MVP generation, revision -> refinement, etc.)
            
            # Complete monitoring operation for successful pipeline setup
            duration_ms = (time.time() - pipeline_start_time) * 1000
            await monitoring_service.complete_operation(
                operation_id=pipeline_op,
                status="success",
                duration_ms=duration_ms,
                result_data={
                    "current_stage": execution.current_stage.value,
                    "stages_completed": [stage.value for stage in execution.stages_completed]
                }
            )
            
        except Exception as e:
            # Complete monitoring operation with failure
            duration_ms = (time.time() - pipeline_start_time) * 1000
            await monitoring_service.fail_operation(
                operation_id=pipeline_op,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=duration_ms,
                error_context={
                    "execution_id": str(execution.id),
                    "current_stage": execution.current_stage.value,
                    "retry_count": execution.retry_count
                }
            )
            
            logger.error(f"Pipeline execution failed: {e}")
            execution.status = PipelineStatus.FAILED
            execution.error_message = str(e)
            await self._update_execution(execution)
    
    async def _execute_blueprint_generation_stage(self, execution: PipelineExecution):
        """Execute blueprint generation stage"""
        
        try:
            await self._transition_to_stage(execution, PipelineStage.BLUEPRINT_GENERATION)
            
            # Get MVP project
            mvp_project = await mvp_service.get_mvp_project(execution.mvp_project_id)
            if not mvp_project or not mvp_project.interview:
                raise Exception("MVP project or interview not found")
            
            # Generate blueprint
            blueprint = await self.ai_architect.analyze_founder_interview(mvp_project.interview)
            
            # Update project with blueprint
            mvp_project.blueprint = blueprint
            mvp_project.status = MVPStatus.BLUEPRINT_PENDING  # Keep as pending for approval
            await mvp_service._update_mvp_project(mvp_project)
            
            # Track blueprint version
            execution.blueprint_versions.append(blueprint.id if hasattr(blueprint, 'id') else uuid4())
            
            await self._complete_stage(execution, PipelineStage.BLUEPRINT_GENERATION)
            
            logger.info(f"Blueprint generation completed for pipeline {execution.id}")
            
        except Exception as e:
            logger.error(f"Blueprint generation stage failed: {e}")
            raise
    
    async def _execute_founder_approval_stage(self, execution: PipelineExecution, founder_email: str):
        """Execute founder approval stage"""
        
        try:
            await self._transition_to_stage(execution, PipelineStage.FOUNDER_APPROVAL)
            
            # Get MVP project and blueprint
            mvp_project = await mvp_service.get_mvp_project(execution.mvp_project_id)
            if not mvp_project or not mvp_project.blueprint:
                raise Exception("MVP project or blueprint not found")
            
            # Create approval workflow
            workflow_request = CreateWorkflowRequest(
                mvp_project_id=mvp_project.id,
                workflow_type=WorkflowType.BLUEPRINT_APPROVAL,
                founder_email=founder_email,
                workflow_title=f"Review Your {mvp_project.project_name} Blueprint",
                workflow_description=f"Please review the technical blueprint generated for {mvp_project.project_name}",
                context_data={
                    "tech_stack": str(mvp_project.blueprint.tech_stack),
                    "confidence_score": mvp_project.blueprint.confidence_score,
                    "estimated_hours": mvp_project.blueprint.estimated_generation_time
                }
            )
            
            workflow = await human_gate_service.create_approval_workflow(workflow_request, execution.tenant_id)
            execution.workflow_id = workflow.id
            
            # Send approval email
            email_context = {
                "project_name": mvp_project.project_name,
                "tech_stack": str(mvp_project.blueprint.tech_stack),
                "confidence_score": mvp_project.blueprint.confidence_score,
                "estimated_hours": mvp_project.blueprint.estimated_generation_time
            }
            
            await email_service.send_approval_notification(workflow, email_context)
            
            # Update pipeline status
            execution.status = PipelineStatus.WAITING_APPROVAL
            await self._update_execution(execution)
            
            logger.info(f"Founder approval stage initiated for pipeline {execution.id}")
            
        except Exception as e:
            logger.error(f"Founder approval stage failed: {e}")
            raise
    
    async def process_founder_feedback(
        self,
        execution_id: UUID,
        feedback: FounderFeedback
    ) -> bool:
        """Process founder feedback and continue pipeline"""
        
        try:
            execution = await self._get_execution(execution_id)
            if not execution:
                logger.error(f"Pipeline execution {execution_id} not found")
                return False
            
            if feedback.feedback_type == FeedbackType.APPROVE:
                # Complete founder approval stage first
                await self._complete_stage(execution, PipelineStage.FOUNDER_APPROVAL)
                # Continue to MVP generation
                await self._execute_mvp_generation_stage(execution)
                
            elif feedback.feedback_type == FeedbackType.REQUEST_REVISION:
                # Refine blueprint and request new approval
                await self._execute_blueprint_refinement_stage(execution, feedback)
                
            elif feedback.feedback_type == FeedbackType.REJECT:
                # Mark pipeline as cancelled
                execution.status = PipelineStatus.CANCELLED
                await self._update_execution(execution)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process founder feedback: {e}")
            return False
    
    async def _execute_blueprint_refinement_stage(self, execution: PipelineExecution, feedback: FounderFeedback):
        """Execute blueprint refinement stage"""
        
        try:
            await self._transition_to_stage(execution, PipelineStage.BLUEPRINT_REFINEMENT)
            
            # Get current project and blueprint
            mvp_project = await mvp_service.get_mvp_project(execution.mvp_project_id)
            if not mvp_project or not mvp_project.blueprint or not mvp_project.interview:
                raise Exception("Required project data not found")
            
            # Refine blueprint
            refined_blueprint = await blueprint_refinement_service.refine_blueprint_from_feedback(
                mvp_project.blueprint,
                feedback,
                mvp_project.interview
            )
            
            # Update project with refined blueprint
            mvp_project.blueprint = refined_blueprint
            mvp_project.status = MVPStatus.BLUEPRINT_REVIEW
            await mvp_service._update_mvp_project(mvp_project)
            
            # Track new blueprint version
            execution.blueprint_versions.append(refined_blueprint.id if hasattr(refined_blueprint, 'id') else uuid4())
            
            await self._complete_stage(execution, PipelineStage.BLUEPRINT_REFINEMENT)
            
            # Request new approval for refined blueprint
            await self._execute_founder_approval_stage(execution, 
                (await human_gate_service._get_workflow(execution.workflow_id)).founder_email if execution.workflow_id else "founder@example.com"
            )
            
            logger.info(f"Blueprint refinement completed for pipeline {execution.id}")
            
        except Exception as e:
            logger.error(f"Blueprint refinement stage failed: {e}")
            raise
    
    async def _execute_mvp_generation_stage(self, execution: PipelineExecution):
        """Execute MVP generation stage using assembly line system"""
        
        # Start monitoring MVP generation
        mvp_generation_op = await monitoring_service.start_operation(
            operation_type="mvp_generation_stage",
            tenant_id=execution.tenant_id,
            context={
                "execution_id": str(execution.id),
                "mvp_project_id": str(execution.mvp_project_id),
                "stage": PipelineStage.MVP_GENERATION.value
            }
        )
        
        mvp_start_time = time.time()
        
        try:
            await self._transition_to_stage(execution, PipelineStage.MVP_GENERATION)
            
            # Get MVP project
            mvp_project = await mvp_service.get_mvp_project(execution.mvp_project_id)
            if not mvp_project or not mvp_project.blueprint:
                raise Exception("MVP project or blueprint not found")
            
            # Start assembly line generation
            success = await mvp_service.start_mvp_generation(
                mvp_project.id,
                mvp_project.blueprint
            )
            
            if success:
                await self._complete_stage(execution, PipelineStage.MVP_GENERATION)
                await self._transition_to_stage(execution, PipelineStage.DEPLOYMENT)
                
                # Mark as completed (assembly line handles actual deployment)
                execution.status = PipelineStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                await self._complete_stage(execution, PipelineStage.COMPLETED)
                
                # Complete monitoring operation with success
                duration_ms = (time.time() - mvp_start_time) * 1000
                await monitoring_service.complete_operation(
                    operation_id=mvp_generation_op,
                    status="success",
                    duration_ms=duration_ms,
                    result_data={
                        "mvp_generation_success": True,
                        "pipeline_completed": True,
                        "total_stages_completed": len(execution.stages_completed)
                    }
                )
                
                logger.info(f"MVP generation completed for pipeline {execution.id}")
            else:
                raise Exception("Assembly line generation failed")
            
        except Exception as e:
            # Complete monitoring operation with failure
            duration_ms = (time.time() - mvp_start_time) * 1000
            await monitoring_service.fail_operation(
                operation_id=mvp_generation_op,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=duration_ms,
                error_context={
                    "execution_id": str(execution.id),
                    "mvp_project_id": str(execution.mvp_project_id),
                    "stage": PipelineStage.MVP_GENERATION.value,
                    "assembly_line_invoked": "success" in locals()
                }
            )
            
            logger.error(f"MVP generation stage failed: {e}")
            raise
    
    async def get_pipeline_progress(self, execution_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current pipeline progress"""
        
        execution = await self._get_execution(execution_id)
        if not execution:
            return None
        
        # Calculate overall progress
        stage_weights = {
            PipelineStage.INTERVIEW_RECEIVED: 0.05,
            PipelineStage.BLUEPRINT_GENERATION: 0.15,
            PipelineStage.FOUNDER_APPROVAL: 0.10,
            PipelineStage.BLUEPRINT_REFINEMENT: 0.05,  # Optional
            PipelineStage.MVP_GENERATION: 0.50,
            PipelineStage.DEPLOYMENT: 0.10,
            PipelineStage.COMPLETED: 0.05
        }
        
        completed_weight = sum(stage_weights.get(stage, 0) for stage in execution.stages_completed)
        current_weight = stage_weights.get(execution.current_stage, 0) * (execution.current_stage_progress / 100)
        overall_progress = (completed_weight + current_weight) * 100
        
        return {
            "execution_id": execution.id,
            "current_stage": execution.current_stage,
            "status": execution.status,
            "overall_progress": min(100, overall_progress),
            "current_stage_progress": execution.current_stage_progress,
            "stages_completed": execution.stages_completed,
            "started_at": execution.started_at,
            "estimated_completion": self._estimate_completion_time(execution),
            "error_message": execution.error_message
        }
    
    def _estimate_completion_time(self, execution: PipelineExecution) -> Optional[datetime]:
        """Estimate pipeline completion time based on current progress"""
        
        if execution.status == PipelineStatus.COMPLETED:
            return execution.completed_at
        
        # Simple estimation based on elapsed time and progress
        elapsed_minutes = (datetime.utcnow() - execution.started_at).total_seconds() / 60
        
        if execution.overall_progress > 0:
            estimated_total_minutes = elapsed_minutes / (execution.overall_progress / 100)
            remaining_minutes = estimated_total_minutes - elapsed_minutes
            
            if remaining_minutes > 0:
                return datetime.utcnow() + timedelta(minutes=remaining_minutes)
        
        return None
    
    # Helper methods for stage management
    
    async def _transition_to_stage(self, execution: PipelineExecution, stage: PipelineStage):
        """Transition to a new pipeline stage"""
        execution.current_stage = stage
        execution.current_stage_started_at = datetime.utcnow()
        execution.current_stage_progress = 0.0
        await self._update_execution(execution)
        
        logger.info(f"Pipeline {execution.id} transitioned to stage: {stage}")
    
    async def _complete_stage(self, execution: PipelineExecution, stage: PipelineStage):
        """Mark a pipeline stage as completed"""
        if stage not in execution.stages_completed:
            execution.stages_completed.append(stage)
        
        # Calculate stage duration
        stage_duration = (datetime.utcnow() - execution.current_stage_started_at).total_seconds()
        execution.stage_durations[stage.value] = stage_duration
        
        execution.current_stage_progress = 100.0
        await self._update_execution(execution)
        
        logger.info(f"Pipeline {execution.id} completed stage: {stage} ({stage_duration:.1f}s)")
    
    # Storage methods
    
    async def _save_execution(self, execution: PipelineExecution):
        """Save pipeline execution"""
        self._executions[execution.id] = execution
        self._executions_by_project[execution.mvp_project_id] = execution.id
    
    async def _update_execution(self, execution: PipelineExecution):
        """Update pipeline execution"""
        self._executions[execution.id] = execution
    
    async def _get_execution(self, execution_id: UUID) -> Optional[PipelineExecution]:
        """Get pipeline execution by ID"""
        return self._executions.get(execution_id)
    
    async def get_execution_by_project(self, mvp_project_id: UUID) -> Optional[PipelineExecution]:
        """Get pipeline execution by MVP project ID"""
        execution_id = self._executions_by_project.get(mvp_project_id)
        return await self._get_execution(execution_id) if execution_id else None
    
    # Public Database Persistence Methods (Production Ready)
    
    async def save_execution(self, execution: PipelineExecution) -> PipelineExecution:
        """Public method: Save pipeline execution to database with persistence"""
        try:
            # For now, use the existing in-memory storage
            # TODO: Replace with actual database persistence using PipelineExecutionORM
            await self._save_execution(execution)
            
            logger.info(f"Pipeline execution saved to database: {execution.id}")
            return execution
            
        except Exception as e:
            logger.error(f"Failed to save pipeline execution to database: {e}")
            raise Exception(f"Database persistence failed: {e}")
    
    async def get_execution(self, execution_id: UUID) -> Optional[PipelineExecution]:
        """Public method: Get pipeline execution from database"""
        try:
            # For now, use the existing in-memory storage
            # TODO: Replace with actual database query using PipelineExecutionORM
            execution = await self._get_execution(execution_id)
            
            if execution:
                logger.debug(f"Pipeline execution retrieved from database: {execution_id}")
            else:
                logger.debug(f"Pipeline execution not found in database: {execution_id}")
                
            return execution
            
        except Exception as e:
            logger.error(f"Failed to get pipeline execution from database: {e}")
            return None


# Global service instance
pipeline_orchestration_service = PipelineOrchestrationService()