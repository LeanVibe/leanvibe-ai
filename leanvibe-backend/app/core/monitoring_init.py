"""
Monitoring System Initialization

Centralizes the initialization and configuration of all monitoring systems:
- Structured logging setup
- Health monitoring activation
- Performance monitoring startup
- Error tracking initialization
- WebSocket monitoring setup
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .logging_config import init_logging, configure_logging, get_logger
from .health_monitor import health_monitor
from .performance_monitor import start_performance_monitoring
from .error_tracker import start_error_tracking
from .websocket_monitor import start_websocket_monitoring


logger = get_logger(__name__)


class MonitoringSystem:
    """
    Comprehensive monitoring system manager
    
    Handles initialization, configuration, and lifecycle management
    of all monitoring subsystems.
    """
    
    def __init__(self):
        self.initialized = False
        self.monitoring_config = {
            'enable_json_logging': True,
            'enable_file_logging': True,
            'log_level': 'INFO',
            'log_directory': 'logs',
            'enable_health_monitoring': True,
            'enable_performance_monitoring': True,
            'enable_error_tracking': True,
            'enable_websocket_monitoring': True,
            'enable_console_logging': True
        }
    
    async def initialize_monitoring(self, config_overrides: Optional[Dict[str, Any]] = None):
        """
        Initialize all monitoring systems
        
        Args:
            config_overrides: Optional configuration overrides
        """
        if self.initialized:
            logger.warning("Monitoring system already initialized")
            return
        
        # Apply configuration overrides
        if config_overrides:
            self.monitoring_config.update(config_overrides)
        
        logger.info("Initializing comprehensive monitoring system")
        
        try:
            # 1. Initialize structured logging first
            await self._setup_logging()
            
            # 2. Initialize error tracking (needed by other systems)
            if self.monitoring_config['enable_error_tracking']:
                await self._setup_error_tracking()
            
            # 3. Initialize performance monitoring
            if self.monitoring_config['enable_performance_monitoring']:
                await self._setup_performance_monitoring()
            
            # 4. Initialize health monitoring
            if self.monitoring_config['enable_health_monitoring']:
                await self._setup_health_monitoring()
            
            # 5. Initialize WebSocket monitoring
            if self.monitoring_config['enable_websocket_monitoring']:
                await self._setup_websocket_monitoring()
            
            self.initialized = True
            
            logger.info(
                "Monitoring system initialization completed",
                **{f"enabled_{k}": v for k, v in self.monitoring_config.items() if k.startswith('enable_')}
            )
            
            # Log system status
            await self._log_system_status()
            
        except Exception as e:
            logger.error("Failed to initialize monitoring system", error=str(e))
            raise
    
    async def _setup_logging(self):
        """Setup structured logging system"""
        try:
            log_level = self.monitoring_config['log_level']
            log_dir = Path(self.monitoring_config['log_directory'])
            
            # Ensure log directory exists
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure logging
            configure_logging(
                log_level=log_level,
                log_file=log_dir / "leanvibe.log" if self.monitoring_config['enable_file_logging'] else None,
                enable_json=self.monitoring_config['enable_json_logging'],
                enable_console=self.monitoring_config['enable_console_logging']
            )
            
            # Create logger after configuration
            global logger
            logger = get_logger(__name__)
            
            logger.info("Structured logging initialized", log_level=log_level, log_directory=str(log_dir))
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")  # Fallback to print since logger may not be available
            raise
    
    async def _setup_error_tracking(self):
        """Setup error tracking system"""
        try:
            await start_error_tracking()
            logger.info("Error tracking system initialized")
        except Exception as e:
            logger.error("Failed to setup error tracking", error=str(e))
            raise
    
    async def _setup_performance_monitoring(self):
        """Setup performance monitoring system"""
        try:
            await start_performance_monitoring()
            logger.info("Performance monitoring system initialized")
        except Exception as e:
            logger.error("Failed to setup performance monitoring", error=str(e))
            raise
    
    async def _setup_health_monitoring(self):
        """Setup health monitoring system"""
        try:
            # Health monitor doesn't need async initialization, but we run checks
            await health_monitor.run_all_checks()
            logger.info("Health monitoring system initialized")
        except Exception as e:
            logger.error("Failed to setup health monitoring", error=str(e))
            raise
    
    async def _setup_websocket_monitoring(self):
        """Setup WebSocket monitoring system"""
        try:
            await start_websocket_monitoring()
            logger.info("WebSocket monitoring system initialized")
        except Exception as e:
            logger.error("Failed to setup WebSocket monitoring", error=str(e))
            raise
    
    async def _log_system_status(self):
        """Log initial system status after initialization"""
        try:
            # Get health status
            health_status = await health_monitor.run_all_checks()
            
            # Log key system information
            logger.info(
                "Monitoring system status",
                overall_health=health_status.get('status', 'unknown'),
                healthy_services=health_status.get('healthy_services', 0),
                total_services=health_status.get('total_services', 0),
                uptime_seconds=health_status.get('uptime_seconds', 0),
                monitoring_active=self.initialized
            )
            
        except Exception as e:
            logger.error("Failed to log system status", error=str(e))
    
    async def shutdown_monitoring(self):
        """Gracefully shutdown all monitoring systems"""
        if not self.initialized:
            logger.warning("Monitoring system not initialized, nothing to shutdown")
            return
        
        logger.info("Shutting down monitoring systems")
        
        try:
            # Shutdown in reverse order of initialization
            
            # 1. WebSocket monitoring
            if self.monitoring_config['enable_websocket_monitoring']:
                try:
                    from .websocket_monitor import stop_websocket_monitoring
                    await stop_websocket_monitoring()
                    logger.info("WebSocket monitoring shutdown completed")
                except Exception as e:
                    logger.error("Failed to shutdown WebSocket monitoring", error=str(e))
            
            # 2. Performance monitoring
            if self.monitoring_config['enable_performance_monitoring']:
                try:
                    from .performance_monitor import stop_performance_monitoring
                    await stop_performance_monitoring()
                    logger.info("Performance monitoring shutdown completed")
                except Exception as e:
                    logger.error("Failed to shutdown performance monitoring", error=str(e))
            
            # 3. Error tracking
            if self.monitoring_config['enable_error_tracking']:
                try:
                    from .error_tracker import stop_error_tracking
                    await stop_error_tracking()
                    logger.info("Error tracking shutdown completed")
                except Exception as e:
                    logger.error("Failed to shutdown error tracking", error=str(e))
            
            self.initialized = False
            logger.info("Monitoring system shutdown completed")
            
        except Exception as e:
            logger.error("Failed to shutdown monitoring systems", error=str(e))
            raise
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status"""
        return {
            'initialized': self.initialized,
            'configuration': self.monitoring_config,
            'subsystems': {
                'logging': True,  # Always available if we can log this
                'health_monitoring': self.monitoring_config['enable_health_monitoring'],
                'performance_monitoring': self.monitoring_config['enable_performance_monitoring'],
                'error_tracking': self.monitoring_config['enable_error_tracking'],
                'websocket_monitoring': self.monitoring_config['enable_websocket_monitoring']
            }
        }
    
    def update_configuration(self, config_updates: Dict[str, Any]):
        """Update monitoring configuration (requires restart to take effect)"""
        logger.info("Updating monitoring configuration", updates=config_updates)
        self.monitoring_config.update(config_updates)


# Global monitoring system instance
monitoring_system = MonitoringSystem()


# Convenience functions
async def initialize_all_monitoring(config_overrides: Optional[Dict[str, Any]] = None):
    """Initialize all monitoring systems"""
    await monitoring_system.initialize_monitoring(config_overrides)


async def shutdown_all_monitoring():
    """Shutdown all monitoring systems"""
    await monitoring_system.shutdown_monitoring()


def get_monitoring_status() -> Dict[str, Any]:
    """Get monitoring system status"""
    return monitoring_system.get_monitoring_status()


def configure_monitoring(**kwargs):
    """Update monitoring configuration"""
    monitoring_system.update_configuration(kwargs)


# Environment-based configuration
def load_monitoring_config_from_env() -> Dict[str, Any]:
    """Load monitoring configuration from environment variables"""
    config = {}
    
    # Logging configuration
    if os.getenv('LEANVIBE_LOG_LEVEL'):
        config['log_level'] = os.getenv('LEANVIBE_LOG_LEVEL', 'INFO').upper()
    
    if os.getenv('LEANVIBE_LOG_JSON'):
        config['enable_json_logging'] = os.getenv('LEANVIBE_LOG_JSON', 'true').lower() == 'true'
    
    if os.getenv('LEANVIBE_LOG_FILE'):
        config['enable_file_logging'] = os.getenv('LEANVIBE_LOG_FILE', 'true').lower() == 'true'
    
    if os.getenv('LEANVIBE_LOG_CONSOLE'):
        config['enable_console_logging'] = os.getenv('LEANVIBE_LOG_CONSOLE', 'true').lower() == 'true'
    
    if os.getenv('LEANVIBE_LOG_DIR'):
        config['log_directory'] = os.getenv('LEANVIBE_LOG_DIR', 'logs')
    
    # Monitoring system toggles
    if os.getenv('LEANVIBE_HEALTH_MONITORING'):
        config['enable_health_monitoring'] = os.getenv('LEANVIBE_HEALTH_MONITORING', 'true').lower() == 'true'
    
    if os.getenv('LEANVIBE_PERFORMANCE_MONITORING'):
        config['enable_performance_monitoring'] = os.getenv('LEANVIBE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
    
    if os.getenv('LEANVIBE_ERROR_TRACKING'):
        config['enable_error_tracking'] = os.getenv('LEANVIBE_ERROR_TRACKING', 'true').lower() == 'true'
    
    if os.getenv('LEANVIBE_WEBSOCKET_MONITORING'):
        config['enable_websocket_monitoring'] = os.getenv('LEANVIBE_WEBSOCKET_MONITORING', 'true').lower() == 'true'
    
    return config


# FastAPI integration
async def setup_monitoring_for_fastapi(app, config_overrides: Optional[Dict[str, Any]] = None):
    """
    Setup monitoring for FastAPI application
    
    Args:
        app: FastAPI application instance
        config_overrides: Optional configuration overrides
    """
    
    # Load configuration from environment
    env_config = load_monitoring_config_from_env()
    
    # Merge configurations (overrides take precedence)
    final_config = env_config
    if config_overrides:
        final_config.update(config_overrides)
    
    # Initialize monitoring
    await initialize_all_monitoring(final_config)
    
    # Add monitoring middleware if logging is enabled
    if final_config.get('enable_json_logging', True):
        from .logging_config import LoggingMiddleware
        app.add_middleware(LoggingMiddleware)
    
    # Add startup and shutdown event handlers
    @app.on_event("startup")
    async def startup_monitoring():
        """Ensure monitoring is fully started"""
        if not monitoring_system.initialized:
            await initialize_all_monitoring(final_config)
    
    @app.on_event("shutdown") 
    async def shutdown_monitoring():
        """Gracefully shutdown monitoring"""
        await shutdown_all_monitoring()
    
    logger.info("Monitoring system integrated with FastAPI application")


# Development utilities
async def run_monitoring_diagnostics():
    """Run comprehensive monitoring system diagnostics"""
    
    logger.info("Running monitoring system diagnostics")
    
    diagnostics = {
        'timestamp': logger._context.get('timestamp', 'unknown'),
        'system_status': get_monitoring_status(),
        'health_check': None,
        'performance_stats': None,
        'error_summary': None,
        'websocket_stats': None
    }
    
    try:
        # Health check
        diagnostics['health_check'] = await health_monitor.run_all_checks()
    except Exception as e:
        logger.error("Health check diagnostic failed", error=str(e))
        diagnostics['health_check'] = {'error': str(e)}
    
    try:
        # Performance stats
        from .performance_monitor import get_performance_stats
        diagnostics['performance_stats'] = get_performance_stats()
    except Exception as e:
        logger.error("Performance stats diagnostic failed", error=str(e))
        diagnostics['performance_stats'] = {'error': str(e)}
    
    try:
        # Error summary
        from .error_tracker import get_error_summary
        diagnostics['error_summary'] = get_error_summary()
    except Exception as e:
        logger.error("Error summary diagnostic failed", error=str(e))
        diagnostics['error_summary'] = {'error': str(e)}
    
    try:
        # WebSocket stats
        from .websocket_monitor import get_websocket_stats
        diagnostics['websocket_stats'] = get_websocket_stats()
    except Exception as e:
        logger.error("WebSocket stats diagnostic failed", error=str(e))
        diagnostics['websocket_stats'] = {'error': str(e)}
    
    logger.info("Monitoring diagnostics completed", diagnostics_summary={
        k: 'success' if not isinstance(v, dict) or 'error' not in v else 'failed'
        for k, v in diagnostics.items()
        if k not in ['timestamp', 'system_status']
    })
    
    return diagnostics