"""
Structured Logging Configuration for LeanVibe AI Backend

Provides comprehensive logging infrastructure with:
- JSON structured logging
- Request ID tracing
- Performance metrics
- Error tracking
- Centralized configuration
"""

import json
import logging
import logging.config
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import structlog
from structlog.stdlib import LoggerFactory


# Context variables for request tracing
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id_context: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class RequestIDProcessor:
    """Structlog processor to add request ID to log entries"""
    
    def __call__(self, logger, method_name, event_dict):
        request_id = request_id_context.get()
        if request_id:
            event_dict['request_id'] = request_id
        
        user_id = user_id_context.get()
        if user_id:
            event_dict['user_id'] = user_id
        
        session_id = session_id_context.get()
        if session_id:
            event_dict['session_id'] = session_id
        
        return event_dict


class PerformanceProcessor:
    """Structlog processor to add performance metrics"""
    
    def __call__(self, logger, method_name, event_dict):
        event_dict['timestamp'] = datetime.utcnow().isoformat()
        event_dict['level'] = method_name.upper()
        
        # Add memory usage if available
        try:
            import psutil
            process = psutil.Process()
            event_dict['memory_mb'] = round(process.memory_info().rss / 1024 / 1024, 2)
        except ImportError:
            pass
        
        return event_dict


class ServiceContextProcessor:
    """Structlog processor to add service context information"""
    
    def __call__(self, logger, method_name, event_dict):
        # Add service name from logger name
        logger_name = getattr(logger, 'name', 'unknown')
        if logger_name.startswith('app.'):
            service_parts = logger_name.split('.')
            if len(service_parts) >= 3:
                event_dict['service'] = service_parts[2]
                if len(service_parts) >= 4:
                    event_dict['component'] = service_parts[3]
        
        return event_dict


class JSONRenderer:
    """Custom JSON renderer for structured logs"""
    
    def __call__(self, logger, name, event_dict):
        # Ensure consistent field ordering
        ordered_dict = {
            'timestamp': event_dict.pop('timestamp', datetime.utcnow().isoformat()),
            'level': event_dict.pop('level', name.upper()),
            'service': event_dict.pop('service', 'unknown'),
            'component': event_dict.pop('component', None),
            'request_id': event_dict.pop('request_id', None),
            'user_id': event_dict.pop('user_id', None),
            'session_id': event_dict.pop('session_id', None),
            'message': event_dict.pop('event', ''),
            'data': event_dict if event_dict else None
        }
        
        # Remove None values
        ordered_dict = {k: v for k, v in ordered_dict.items() if v is not None}
        
        return json.dumps(ordered_dict, ensure_ascii=False, separators=(',', ':'))


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_json: bool = True,
    enable_console: bool = True
):
    """
    Configure structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging
        enable_json: Whether to use JSON formatting
        enable_console: Whether to log to console
    """
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        RequestIDProcessor(),
        ServiceContextProcessor(),
        PerformanceProcessor(),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if enable_json:
        processors.append(JSONRenderer())
    else:
        processors.extend([
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer()
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    handlers = []
    
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        handlers.append(console_handler)
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format="%(message)s",  # structlog will handle formatting
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """
    Set request context for logging
    
    Args:
        request_id: Unique request identifier
        user_id: User identifier
        session_id: Session identifier
    """
    if request_id:
        request_id_context.set(request_id)
    if user_id:
        user_id_context.set(user_id)
    if session_id:
        session_id_context.set(session_id)


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return f"req_{uuid.uuid4().hex[:12]}"


def clear_request_context():
    """Clear request context"""
    request_id_context.set(None)
    user_id_context.set(None)
    session_id_context.set(None)


class LoggingMiddleware:
    """Middleware to add request logging with timing"""
    
    def __init__(self, app, logger_name: str = "app.middleware.logging"):
        self.app = app
        self.logger = get_logger(logger_name)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Generate request ID
            request_id = generate_request_id()
            set_request_context(request_id=request_id)
            
            # Log request start
            method = scope["method"]
            path = scope["path"]
            query_string = scope.get("query_string", b"").decode()
            full_path = f"{path}{'?' + query_string if query_string else ''}"
            
            start_time = time.time()
            
            self.logger.info(
                "Request started",
                method=method,
                path=full_path,
                request_id=request_id
            )
            
            # Intercept response
            response_data = {}
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    response_data["status_code"] = message["status"]
                await send(message)
            
            try:
                await self.app(scope, receive, send_wrapper)
                
                # Log request completion
                duration = time.time() - start_time
                status_code = response_data.get("status_code", 0)
                
                log_level = "info"
                if status_code >= 400:
                    log_level = "error" if status_code >= 500 else "warning"
                
                getattr(self.logger, log_level)(
                    "Request completed",
                    method=method,
                    path=full_path,
                    status_code=status_code,
                    duration_ms=round(duration * 1000, 2),
                    request_id=request_id
                )
                
            except Exception as e:
                # Log request error
                duration = time.time() - start_time
                self.logger.error(
                    "Request failed",
                    method=method,
                    path=full_path,
                    error=str(e),
                    error_type=type(e).__name__,
                    duration_ms=round(duration * 1000, 2),
                    request_id=request_id,
                    exc_info=True
                )
                raise
            finally:
                clear_request_context()
        else:
            await self.app(scope, receive, send)


class TimingLogger:
    """Context manager for timing operations"""
    
    def __init__(self, logger: structlog.BoundLogger, operation: str, **extra_context):
        self.logger = logger
        self.operation = operation
        self.extra_context = extra_context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(
            f"{self.operation} started",
            operation=self.operation,
            **self.extra_context
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            self.logger.error(
                f"{self.operation} failed",
                operation=self.operation,
                duration_ms=round(duration * 1000, 2),
                error=str(exc_val) if exc_val else None,
                error_type=exc_type.__name__ if exc_type else None,
                **self.extra_context
            )
        else:
            self.logger.info(
                f"{self.operation} completed",
                operation=self.operation,
                duration_ms=round(duration * 1000, 2),
                **self.extra_context
            )


def log_performance_metrics(
    logger: structlog.BoundLogger,
    operation: str,
    metrics: Dict[str, Any],
    **extra_context
):
    """
    Log performance metrics for an operation
    
    Args:
        logger: Logger instance
        operation: Operation name
        metrics: Performance metrics dictionary
        **extra_context: Additional context data
    """
    logger.info(
        f"Performance metrics for {operation}",
        operation=operation,
        metrics=metrics,
        **extra_context
    )


# Initialize logging configuration
def init_logging():
    """Initialize logging configuration with default settings"""
    log_dir = Path("logs")
    configure_logging(
        log_level="INFO",
        log_file=log_dir / "leanvibe.log",
        enable_json=True,
        enable_console=True
    )


# Export main functions
__all__ = [
    'configure_logging',
    'get_logger',
    'set_request_context',
    'generate_request_id',
    'clear_request_context',
    'LoggingMiddleware',
    'TimingLogger',
    'log_performance_metrics',
    'init_logging'
]