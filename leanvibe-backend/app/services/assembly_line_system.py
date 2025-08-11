"""
Assembly Line System for MVP Generation
AI Agent Orchestration for Autonomous MVP Creation
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..models.mvp_models import MVPProject, MVPStatus, TechnicalBlueprint
from ..models.tenant_models import TenantType
# Import tenant service only when needed to avoid circular dependencies
# from ..services.tenant_service import tenant_service

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of AI agents in the assembly line"""
    AI_ARCHITECT = "ai_architect"  # AI Architect - converts interviews to blueprints
    BACKEND = "backend"           # Backend Coder - generates FastAPI backend
    FRONTEND = "frontend"         # Frontend Coder - generates React/Lit frontend  
    INFRASTRUCTURE = "infrastructure"  # Infrastructure - Docker, deployment configs
    OBSERVABILITY = "observability"   # Observability - monitoring, health checks


class AgentStatus(str, Enum):
    """Agent execution status"""
    PENDING = "pending"           # Waiting to start
    RUNNING = "running"           # Currently executing
    COMPLETED = "completed"       # Successfully completed
    FAILED = "failed"             # Execution failed
    RETRYING = "retrying"         # Retrying after failure
    CANCELLED = "cancelled"       # Execution cancelled


class AgentResult(BaseModel):
    """Result from an AI agent execution"""
    agent_type: AgentType
    status: AgentStatus
    output: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list, description="Generated file paths")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")
    error_message: Optional[str] = None
    execution_time: float = 0.0
    confidence_score: float = 0.0
    
    model_config = {"extra": "ignore"}


class QualityGateCheck(BaseModel):
    """Quality gate validation between agent handoffs"""
    check_name: str
    passed: bool
    score: float = Field(ge=0, le=1, description="Quality score 0-1")
    details: str = ""
    fix_suggestions: List[str] = Field(default_factory=list)
    
    model_config = {"extra": "ignore"}


class QualityGateResult(BaseModel):
    """Result of quality gate validation"""
    overall_passed: bool
    overall_score: float
    checks: List[QualityGateCheck] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    model_config = {"extra": "ignore"}


class GenerationProgress(BaseModel):
    """Real-time progress tracking for MVP generation"""
    mvp_project_id: UUID
    current_stage: AgentType
    overall_progress: float = Field(ge=0, le=100, description="Overall progress percentage")
    stage_progress: float = Field(ge=0, le=100, description="Current stage progress")
    
    # Stage statuses
    blueprint_status: AgentStatus = AgentStatus.PENDING
    backend_status: AgentStatus = AgentStatus.PENDING
    frontend_status: AgentStatus = AgentStatus.PENDING
    infrastructure_status: AgentStatus = AgentStatus.PENDING
    observability_status: AgentStatus = AgentStatus.PENDING
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    current_stage_started_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion_at: Optional[datetime] = None
    
    # Error recovery
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    
    model_config = {"extra": "ignore"}


class BaseAIAgent:
    """Base class for all AI agents in the assembly line"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"agent.{agent_type.value}")
        
    async def execute(
        self,
        mvp_project_id: UUID,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> AgentResult:
        """Execute the agent's primary function"""
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Starting {self.agent_type} agent for project {mvp_project_id}")
            
            # Update progress
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.RUNNING, 0)
            
            # Execute agent-specific logic
            result = await self._execute_agent(mvp_project_id, input_data, progress_callback)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            self.logger.info(
                f"Completed {self.agent_type} agent in {execution_time:.2f}s "
                f"(confidence: {result.confidence_score:.2f})"
            )
            
            # Final progress update
            if progress_callback:
                await progress_callback(self.agent_type, result.status, 100)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = str(e)
            
            self.logger.error(f"Agent {self.agent_type} failed: {error_msg}")
            
            if progress_callback:
                await progress_callback(self.agent_type, AgentStatus.FAILED, 0)
            
            return AgentResult(
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error_message=error_msg,
                execution_time=execution_time
            )
    
    async def _execute_agent(
        self,
        mvp_project_id: UUID,
        input_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> AgentResult:
        """Agent-specific implementation - must be overridden"""
        raise NotImplementedError("Agent must implement _execute_agent method")
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for this agent"""
        return True
    
    async def quality_check(self, result: AgentResult) -> QualityGateResult:
        """Perform quality checks on agent output"""
        return QualityGateResult(
            overall_passed=True,
            overall_score=result.confidence_score
        )


class AssemblyLineOrchestrator:
    """Main orchestrator for the MVP generation assembly line"""
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAIAgent] = {}
        self.quality_gates: Dict[AgentType, List[Callable]] = {}
        self.progress_tracking: Dict[UUID, GenerationProgress] = {}
        
    def register_agent(self, agent: BaseAIAgent):
        """Register an AI agent with the orchestrator"""
        self.agents[agent.agent_type] = agent
        logger.info(f"Registered {agent.agent_type} agent")
    
    def register_all_agents(self):
        """Register all available agents with the orchestrator"""
        from .agents import (
            BackendCoderAgent,
            FrontendCoderAgent, 
            InfrastructureAgent,
            ObservabilityAgent
        )
        
        # Register all agents
        self.register_agent(BackendCoderAgent())
        self.register_agent(FrontendCoderAgent())
        self.register_agent(InfrastructureAgent())
        self.register_agent(ObservabilityAgent())
        
        logger.info(f"Successfully registered {len(self.agents)} agents")
    
    def register_quality_gate(self, agent_type: AgentType, quality_check: Callable):
        """Register a quality gate for an agent"""
        if agent_type not in self.quality_gates:
            self.quality_gates[agent_type] = []
        self.quality_gates[agent_type].append(quality_check)
    
    async def start_mvp_generation(
        self,
        mvp_project_id: UUID,
        blueprint: TechnicalBlueprint,
        priority: str = "normal"
    ) -> bool:
        """Start the complete MVP generation process"""
        try:
            # Validate MVP project exists and tenant has quota
            if not await self._validate_generation_request(mvp_project_id):
                return False
            
            # Initialize progress tracking
            progress = GenerationProgress(
                mvp_project_id=mvp_project_id,
                current_stage=AgentType.BACKEND,
                estimated_completion_at=self._estimate_completion_time(blueprint)
            )
            self.progress_tracking[mvp_project_id] = progress
            
            # Execute assembly line
            success = await self._execute_assembly_line(mvp_project_id, blueprint, priority)
            
            if success:
                logger.info(f"MVP generation completed successfully for project {mvp_project_id}")
                await self._update_mvp_status(mvp_project_id, MVPStatus.TESTING)
            else:
                logger.error(f"MVP generation failed for project {mvp_project_id}")
                await self._update_mvp_status(mvp_project_id, MVPStatus.FAILED)
            
            return success
            
        except Exception as e:
            logger.error(f"Assembly line orchestration failed: {e}")
            await self._update_mvp_status(mvp_project_id, MVPStatus.FAILED)
            return False
    
    async def _execute_assembly_line(
        self,
        mvp_project_id: UUID,
        blueprint: TechnicalBlueprint,
        priority: str
    ) -> bool:
        """Execute the complete assembly line sequence"""
        
        # Define execution order
        execution_order = [
            AgentType.BACKEND,
            AgentType.FRONTEND,
            AgentType.INFRASTRUCTURE,
            AgentType.OBSERVABILITY
        ]
        
        # Accumulated output from all agents
        accumulated_output = {"blueprint": blueprint.model_dump()}
        
        for agent_type in execution_order:
            success = await self._execute_agent_with_quality_gates(
                mvp_project_id, agent_type, accumulated_output, priority
            )
            
            if not success:
                logger.error(f"Assembly line failed at {agent_type} stage")
                return False
            
            # Update progress
            progress = self.progress_tracking[mvp_project_id]
            progress.current_stage = agent_type
            progress.overall_progress = self._calculate_overall_progress(execution_order, agent_type)
        
        return True
    
    async def _execute_agent_with_quality_gates(
        self,
        mvp_project_id: UUID,
        agent_type: AgentType,
        input_data: Dict[str, Any],
        priority: str
    ) -> bool:
        """Execute an agent with quality gate validation"""
        
        if agent_type not in self.agents:
            logger.error(f"Agent {agent_type} not registered")
            return False
        
        agent = self.agents[agent_type]
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Execute agent
                result = await agent.execute(
                    mvp_project_id,
                    input_data,
                    lambda at, status, progress: self._update_progress(mvp_project_id, at, status, progress)
                )
                
                # Check if agent succeeded
                if result.status != AgentStatus.COMPLETED:
                    logger.warning(f"Agent {agent_type} did not complete successfully: {result.error_message}")
                    retry_count += 1
                    continue
                
                # Run quality gates
                quality_result = await self._run_quality_gates(agent_type, result)
                
                if quality_result.overall_passed:
                    # Quality gates passed - update accumulated output
                    input_data[f"{agent_type.value}_output"] = result.output
                    input_data[f"{agent_type.value}_artifacts"] = result.artifacts
                    
                    # Update progress tracking
                    await self._update_agent_status(mvp_project_id, agent_type, AgentStatus.COMPLETED)
                    
                    return True
                else:
                    # Quality gates failed
                    logger.warning(
                        f"Quality gates failed for {agent_type}: "
                        f"Score: {quality_result.overall_score:.2f}, "
                        f"Blockers: {quality_result.blockers}"
                    )
                    retry_count += 1
                    
                    if retry_count < max_retries:
                        await self._update_agent_status(mvp_project_id, agent_type, AgentStatus.RETRYING)
                        await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Agent {agent_type} execution failed: {e}")
                retry_count += 1
                
                if retry_count < max_retries:
                    await self._update_agent_status(mvp_project_id, agent_type, AgentStatus.RETRYING)
                    await asyncio.sleep(2 ** retry_count)
        
        # All retries exhausted
        await self._update_agent_status(mvp_project_id, agent_type, AgentStatus.FAILED)
        return False
    
    async def _run_quality_gates(self, agent_type: AgentType, result: AgentResult) -> QualityGateResult:
        """Run all quality gates for an agent"""
        
        if agent_type not in self.quality_gates:
            # No quality gates defined - use agent's own quality check
            return await self.agents[agent_type].quality_check(result)
        
        all_checks = []
        overall_score = 0.0
        blockers = []
        warnings = []
        
        # Run agent's own quality check
        agent_quality = await self.agents[agent_type].quality_check(result)
        all_checks.extend(agent_quality.checks)
        
        # Run registered quality gates
        for quality_gate in self.quality_gates[agent_type]:
            try:
                gate_result = await quality_gate(result)
                if isinstance(gate_result, QualityGateResult):
                    all_checks.extend(gate_result.checks)
                    blockers.extend(gate_result.blockers)
                    warnings.extend(gate_result.warnings)
            except Exception as e:
                logger.warning(f"Quality gate failed to run: {e}")
                all_checks.append(QualityGateCheck(
                    check_name="quality_gate_execution",
                    passed=False,
                    score=0.0,
                    details=f"Quality gate execution failed: {e}"
                ))
        
        # Calculate overall score and pass/fail
        if all_checks:
            overall_score = sum(check.score for check in all_checks) / len(all_checks)
            overall_passed = all(check.passed for check in all_checks) and not blockers
        else:
            overall_score = result.confidence_score
            overall_passed = True
        
        return QualityGateResult(
            overall_passed=overall_passed,
            overall_score=overall_score,
            checks=all_checks,
            blockers=blockers,
            warnings=warnings
        )
    
    async def get_generation_progress(self, mvp_project_id: UUID) -> Optional[GenerationProgress]:
        """Get current progress for MVP generation"""
        return self.progress_tracking.get(mvp_project_id)
    
    async def cancel_generation(self, mvp_project_id: UUID) -> bool:
        """Cancel ongoing MVP generation"""
        if mvp_project_id in self.progress_tracking:
            progress = self.progress_tracking[mvp_project_id]
            # Update all pending/running stages to cancelled
            for agent_type in [AgentType.BACKEND, AgentType.FRONTEND, AgentType.INFRASTRUCTURE, AgentType.OBSERVABILITY]:
                status_attr = f"{agent_type.value}_status"
                if hasattr(progress, status_attr):
                    current_status = getattr(progress, status_attr)
                    if current_status in [AgentStatus.PENDING, AgentStatus.RUNNING, AgentStatus.RETRYING]:
                        setattr(progress, status_attr, AgentStatus.CANCELLED)
            
            await self._update_mvp_status(mvp_project_id, MVPStatus.PAUSED)
            logger.info(f"Cancelled MVP generation for project {mvp_project_id}")
            return True
        
        return False
    
    # Helper methods
    async def _validate_generation_request(self, mvp_project_id: UUID) -> bool:
        """Validate that MVP generation can proceed"""
        try:
            # This would integrate with the MVP project service
            # For now, assume validation passes
            return True
        except Exception as e:
            logger.error(f"Generation request validation failed: {e}")
            return False
    
    def _estimate_completion_time(self, blueprint: TechnicalBlueprint) -> datetime:
        """Estimate completion time based on blueprint complexity"""
        # Simple estimation - would be more sophisticated in production
        estimated_minutes = blueprint.estimated_generation_time
        return datetime.utcnow().replace(microsecond=0).replace(second=0) + \
               timedelta(minutes=estimated_minutes)
    
    def _calculate_overall_progress(self, execution_order: List[AgentType], current_agent: AgentType) -> float:
        """Calculate overall progress percentage"""
        if current_agent not in execution_order:
            return 0.0
        
        current_index = execution_order.index(current_agent)
        return (current_index / len(execution_order)) * 100
    
    async def _update_progress(self, mvp_project_id: UUID, agent_type: AgentType, status: AgentStatus, progress: float):
        """Update progress tracking"""
        if mvp_project_id in self.progress_tracking:
            tracking = self.progress_tracking[mvp_project_id]
            tracking.stage_progress = progress
            
            # Update agent status
            status_attr = f"{agent_type.value}_status"
            if hasattr(tracking, status_attr):
                setattr(tracking, status_attr, status)
    
    async def _update_agent_status(self, mvp_project_id: UUID, agent_type: AgentType, status: AgentStatus):
        """Update specific agent status"""
        if mvp_project_id in self.progress_tracking:
            tracking = self.progress_tracking[mvp_project_id]
            status_attr = f"{agent_type.value}_status"
            if hasattr(tracking, status_attr):
                setattr(tracking, status_attr, status)
    
    async def _update_mvp_status(self, mvp_project_id: UUID, status: MVPStatus):
        """Update MVP project status"""
        # This would integrate with the MVP project service
        logger.info(f"MVP project {mvp_project_id} status updated to {status}")


# Singleton orchestrator
assembly_line = AssemblyLineOrchestrator()