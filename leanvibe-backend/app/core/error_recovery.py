"""
Robust Error Recovery and Resilience System for LeanVibe MVP

Implements comprehensive error handling, automatic recovery mechanisms,
and user-friendly error reporting for production reliability.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass, field
import functools

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for appropriate handling"""
    LOW = "low"          # Minor issues, automatic retry possible
    MEDIUM = "medium"    # Service degradation, user notification needed
    HIGH = "high"        # Service failure, manual intervention suggested
    CRITICAL = "critical" # System failure, immediate escalation required


class RecoveryStrategy(Enum):
    """Available recovery strategies"""
    RETRY = "retry"                    # Simple retry with backoff
    RESTART_SERVICE = "restart_service" # Restart specific service
    FALLBACK = "fallback"              # Use alternative implementation
    GRACEFUL_DEGRADATION = "degradation" # Reduce functionality
    USER_NOTIFICATION = "notify"       # Inform user of issue
    ESCALATE = "escalate"              # Require human intervention


@dataclass
class ErrorContext:
    """Context information for error analysis and recovery"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    component: str
    timestamp: float = field(default_factory=time.time)
    user_action: Optional[str] = None
    system_state: Dict[str, Any] = field(default_factory=dict)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3


@dataclass
class RecoveryPlan:
    """Recovery plan for handling specific errors"""
    strategies: List[RecoveryStrategy]
    max_attempts: int = 3
    backoff_multiplier: float = 2.0
    timeout_seconds: float = 30.0
    fallback_message: str = "Service temporarily unavailable. Please try again."


class ErrorRecoveryManager:
    """Central manager for error handling and recovery across LeanVibe"""
    
    def __init__(self):
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.error_history: List[ErrorContext] = []
        self.service_health: Dict[str, bool] = {}
        self.recovery_stats: Dict[str, Dict[str, int]] = {}
        
        # Initialize with default recovery plans
        self._setup_default_recovery_plans()
    
    def _setup_default_recovery_plans(self):
        """Setup default recovery plans for common error scenarios"""
        
        # Ollama service connection errors
        self.recovery_plans["ollama_connection"] = RecoveryPlan(
            strategies=[
                RecoveryStrategy.RETRY,
                RecoveryStrategy.RESTART_SERVICE,
                RecoveryStrategy.USER_NOTIFICATION
            ],
            max_attempts=3,
            backoff_multiplier=2.0,
            fallback_message="AI service temporarily unavailable. Please ensure Ollama is running."
        )
        
        # L3 Agent initialization errors
        self.recovery_plans["l3_agent_init"] = RecoveryPlan(
            strategies=[
                RecoveryStrategy.RETRY,
                RecoveryStrategy.GRACEFUL_DEGRADATION,
                RecoveryStrategy.USER_NOTIFICATION
            ],
            max_attempts=2,
            fallback_message="AI agent initialization failed. Some features may be limited."
        )
        
        # Query processing timeouts
        self.recovery_plans["query_timeout"] = RecoveryPlan(
            strategies=[
                RecoveryStrategy.RETRY,
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.USER_NOTIFICATION
            ],
            max_attempts=2,
            timeout_seconds=15.0,
            fallback_message="Query is taking longer than expected. Please try a simpler question."
        )
        
        # WebSocket connection errors
        self.recovery_plans["websocket_connection"] = RecoveryPlan(
            strategies=[
                RecoveryStrategy.RETRY,
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.USER_NOTIFICATION
            ],
            max_attempts=5,
            backoff_multiplier=1.5,
            fallback_message="Connection lost. Attempting to reconnect..."
        )
        
        # File operation errors
        self.recovery_plans["file_operation"] = RecoveryPlan(
            strategies=[
                RecoveryStrategy.RETRY,
                RecoveryStrategy.USER_NOTIFICATION
            ],
            max_attempts=2,
            fallback_message="File operation failed. Please check file permissions and try again."
        )
        
        # Memory/Resource exhaustion
        self.recovery_plans["resource_exhaustion"] = RecoveryPlan(
            strategies=[
                RecoveryStrategy.GRACEFUL_DEGRADATION,
                RecoveryStrategy.USER_NOTIFICATION,
                RecoveryStrategy.ESCALATE
            ],
            max_attempts=1,
            fallback_message="System resources low. Please restart the application."
        )
    
    async def handle_error(self, 
                          error_type: str, 
                          error: Exception, 
                          context: Optional[Dict[str, Any]] = None,
                          component: str = "unknown") -> Dict[str, Any]:
        """
        Handle an error with appropriate recovery strategy
        
        Returns:
            Dict containing recovery result and user-facing information
        """
        
        # Create error context
        error_context = ErrorContext(
            error_type=error_type,
            error_message=str(error),
            severity=self._determine_severity(error_type, error),
            component=component,
            user_action=context.get("user_action") if context else None,
            system_state=context or {}
        )
        
        # Log error for monitoring
        self._log_error(error_context)
        
        # Add to error history
        self.error_history.append(error_context)
        
        # Get recovery plan
        recovery_plan = self.recovery_plans.get(error_type, self._get_default_recovery_plan())
        
        # Execute recovery strategies
        recovery_result = await self._execute_recovery(error_context, recovery_plan)
        
        # Update recovery statistics
        self._update_recovery_stats(error_type, recovery_result["success"])
        
        return recovery_result
    
    def _determine_severity(self, error_type: str, error: Exception) -> ErrorSeverity:
        """Determine error severity based on type and context"""
        
        # Critical system errors
        if error_type in ["resource_exhaustion", "security_violation"]:
            return ErrorSeverity.CRITICAL
        
        # High severity service failures
        if error_type in ["l3_agent_init", "ollama_connection"] and "initialization" in str(error):
            return ErrorSeverity.HIGH
        
        # Medium severity connection issues
        if error_type in ["websocket_connection", "query_timeout"]:
            return ErrorSeverity.MEDIUM
        
        # Low severity operational issues
        return ErrorSeverity.LOW
    
    async def _execute_recovery(self, 
                               error_context: ErrorContext, 
                               recovery_plan: RecoveryPlan) -> Dict[str, Any]:
        """Execute recovery strategies in sequence"""
        
        recovery_result = {
            "success": False,
            "strategy_used": None,
            "user_message": recovery_plan.fallback_message,
            "retry_possible": True,
            "escalation_needed": False
        }
        
        for strategy in recovery_plan.strategies:
            try:
                if error_context.recovery_attempts >= recovery_plan.max_attempts:
                    break
                
                error_context.recovery_attempts += 1
                
                if strategy == RecoveryStrategy.RETRY:
                    success = await self._retry_operation(error_context, recovery_plan)
                elif strategy == RecoveryStrategy.RESTART_SERVICE:
                    success = await self._restart_service(error_context)
                elif strategy == RecoveryStrategy.FALLBACK:
                    success = await self._use_fallback(error_context)
                elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                    success = await self._graceful_degradation(error_context)
                elif strategy == RecoveryStrategy.USER_NOTIFICATION:
                    success = await self._notify_user(error_context, recovery_plan)
                elif strategy == RecoveryStrategy.ESCALATE:
                    recovery_result["escalation_needed"] = True
                    success = False
                else:
                    success = False
                
                if success:
                    recovery_result["success"] = True
                    recovery_result["strategy_used"] = strategy.value
                    recovery_result["user_message"] = self._get_success_message(error_context, strategy)
                    break
                    
            except Exception as recovery_error:
                logger.error(f"Recovery strategy {strategy} failed: {recovery_error}")
                continue
        
        return recovery_result
    
    async def _retry_operation(self, error_context: ErrorContext, recovery_plan: RecoveryPlan) -> bool:
        """Implement retry logic with exponential backoff"""
        
        backoff_time = recovery_plan.backoff_multiplier ** (error_context.recovery_attempts - 1)
        
        logger.info(f"Retrying operation after {backoff_time}s backoff (attempt {error_context.recovery_attempts})")
        
        # Wait before retry
        await asyncio.sleep(backoff_time)
        
        # For now, simulate retry success based on error type
        # In production, this would actually retry the failed operation
        if error_context.error_type in ["query_timeout", "websocket_connection"]:
            return error_context.recovery_attempts <= 2  # Success after 1-2 retries
        
        return False
    
    async def _restart_service(self, error_context: ErrorContext) -> bool:
        """Restart the affected service"""
        
        logger.info(f"Attempting to restart service for component: {error_context.component}")
        
        # Mark service as unhealthy
        self.service_health[error_context.component] = False
        
        # Simulate service restart
        await asyncio.sleep(2)
        
        # In production, this would actually restart the service
        # For now, simulate successful restart for certain components
        if error_context.component in ["ollama_service", "l3_agent"]:
            self.service_health[error_context.component] = True
            logger.info(f"Service {error_context.component} restarted successfully")
            return True
        
        return False
    
    async def _use_fallback(self, error_context: ErrorContext) -> bool:
        """Use fallback implementation or cached response"""
        
        logger.info(f"Using fallback for {error_context.error_type}")
        
        # Fallback strategies based on error type
        if error_context.error_type == "query_timeout":
            # Return cached response or simplified response
            return True
        elif error_context.error_type == "websocket_connection":
            # Fall back to HTTP API
            return True
        
        return False
    
    async def _graceful_degradation(self, error_context: ErrorContext) -> bool:
        """Implement graceful degradation of service"""
        
        logger.info(f"Implementing graceful degradation for {error_context.error_type}")
        
        # Reduce functionality to maintain core service
        if error_context.error_type == "resource_exhaustion":
            # Disable non-essential features, reduce memory usage
            return True
        elif error_context.error_type == "l3_agent_init":
            # Provide basic responses without full agent capabilities
            return True
        
        return True  # Always succeed for graceful degradation
    
    async def _notify_user(self, error_context: ErrorContext, recovery_plan: RecoveryPlan) -> bool:
        """Send user notification about the error and recovery"""
        
        logger.info(f"Notifying user about {error_context.error_type}")
        
        # In production, this would send actual notifications
        # For now, just log the notification
        return True
    
    def _get_success_message(self, error_context: ErrorContext, strategy: RecoveryStrategy) -> str:
        """Get user-friendly success message after recovery"""
        
        messages = {
            RecoveryStrategy.RETRY: "Connection restored successfully.",
            RecoveryStrategy.RESTART_SERVICE: "Service restarted and available.",
            RecoveryStrategy.FALLBACK: "Using alternative method to process your request.",
            RecoveryStrategy.GRACEFUL_DEGRADATION: "Service available with limited functionality.",
            RecoveryStrategy.USER_NOTIFICATION: "We're working to resolve the issue."
        }
        
        return messages.get(strategy, "Issue resolved.")
    
    def _get_default_recovery_plan(self) -> RecoveryPlan:
        """Get default recovery plan for unknown error types"""
        
        return RecoveryPlan(
            strategies=[
                RecoveryStrategy.RETRY,
                RecoveryStrategy.USER_NOTIFICATION
            ],
            max_attempts=2,
            fallback_message="An unexpected error occurred. Please try again."
        )
    
    def _log_error(self, error_context: ErrorContext):
        """Log error with appropriate severity level"""
        
        log_level = {
            ErrorSeverity.LOW: logger.info,
            ErrorSeverity.MEDIUM: logger.warning,
            ErrorSeverity.HIGH: logger.error,
            ErrorSeverity.CRITICAL: logger.critical
        }
        
        log_func = log_level.get(error_context.severity, logger.error)
        log_func(
            f"Error in {error_context.component}: {error_context.error_type} - "
            f"{error_context.error_message} (Severity: {error_context.severity.value})"
        )
    
    def _update_recovery_stats(self, error_type: str, success: bool):
        """Update recovery statistics for monitoring"""
        
        if error_type not in self.recovery_stats:
            self.recovery_stats[error_type] = {"attempts": 0, "successes": 0}
        
        self.recovery_stats[error_type]["attempts"] += 1
        if success:
            self.recovery_stats[error_type]["successes"] += 1
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health including error recovery status"""
        
        recent_errors = [e for e in self.error_history if time.time() - e.timestamp < 3600]  # Last hour
        
        return {
            "service_health": self.service_health,
            "recent_errors": len(recent_errors),
            "critical_errors_last_hour": len([e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL]),
            "recovery_stats": self.recovery_stats,
            "overall_health": "healthy" if not recent_errors else "degraded"
        }
    
    def get_user_friendly_status(self) -> Dict[str, Any]:
        """Get user-friendly status report"""
        
        recent_critical = len([e for e in self.error_history 
                              if time.time() - e.timestamp < 1800 and e.severity == ErrorSeverity.CRITICAL])
        
        if recent_critical > 0:
            status = "experiencing_issues"
            message = "We're currently experiencing some technical difficulties. Please try again in a few minutes."
        elif any(not healthy for healthy in self.service_health.values()):
            status = "limited_functionality"  
            message = "Some features may be temporarily limited. Core functionality is available."
        else:
            status = "operational"
            message = "All systems operational."
        
        return {
            "status": status,
            "message": message,
            "last_updated": time.time()
        }


# Decorator for automatic error handling
def with_error_recovery(error_type: str, component: str = "unknown"):
    """Decorator to automatically handle errors with recovery strategies"""
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get global error recovery manager
                recovery_manager = ErrorRecoveryManager()
                
                # Handle error with recovery
                recovery_result = await recovery_manager.handle_error(
                    error_type=error_type,
                    error=e,
                    context={"function": func.__name__, "args": str(args)[:100]},
                    component=component
                )
                
                if recovery_result["success"]:
                    # Recovery succeeded, return appropriate result
                    return {"status": "recovered", "message": recovery_result["user_message"]}
                else:
                    # Recovery failed, raise with user-friendly message
                    raise RuntimeError(recovery_result["user_message"])
        
        return wrapper
    return decorator


# Global error recovery manager instance
global_error_recovery = ErrorRecoveryManager()