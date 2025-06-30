"""
Unified Configuration System for LeanVibe

Consolidates all configuration classes and environment handling into a single,
consistent system to eliminate duplication across CLI and backend services.
"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class DeploymentMode(str, Enum):
    """Available deployment modes for services"""
    AUTO = "auto"
    DIRECT = "direct"
    SERVER = "server"
    MOCK = "mock"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class NotificationLevel(str, Enum):
    """Notification priority levels"""
    DEBUG = "debug"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MLXInferenceStrategy(str, Enum):
    """MLX inference strategies"""
    AUTO = "auto"
    PRODUCTION = "production"
    PRAGMATIC = "pragmatic"
    MOCK = "mock"
    FALLBACK = "fallback"


class DefaultValues:
    """Centralized default values for all configuration"""
    
    # Network and API defaults
    DEFAULT_BACKEND_URL = "http://localhost:8000"
    DEFAULT_MLX_SERVER_URL = "http://127.0.0.1:8082"
    DEFAULT_API_PORT = 8000
    DEFAULT_MLX_PORT = 8082
    
    # Timeout defaults
    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_NOTIFICATION_TIMEOUT = 5
    DEFAULT_THROTTLE_SECONDS = 30
    DEFAULT_CACHE_TTL = 300
    
    # Model defaults
    DEFAULT_MODEL_NAME = "microsoft/Phi-3-mini-128k-instruct"
    DEFAULT_MAX_TOKENS = 512
    DEFAULT_TEMPERATURE = 0.7
    
    # File and directory defaults
    DEFAULT_CACHE_DIR = "~/.cache/leanvibe"
    DEFAULT_CONFIG_DIR = "~/.config/leanvibe"
    DEFAULT_LOG_DIR = "~/.local/share/leanvibe/logs"
    
    # Notification defaults
    DEFAULT_MIN_PRIORITY = NotificationLevel.MEDIUM
    DEFAULT_MAX_PER_MINUTE = 10
    DEFAULT_OVERLAY_DURATION = 3
    DEFAULT_MAX_OVERLAY_ITEMS = 5
    
    # Event type defaults
    DEFAULT_ENABLED_EVENTS = [
        "code_quality_issue",
        "architectural_violation",
        "security_vulnerability", 
        "performance_regression",
        "test_failure",
        "build_failure",
        "deployment_status",
        "health_check_failure"
    ]
    
    # File filter defaults
    DEFAULT_EXCLUDE_PATTERNS = [
        "node_modules/", "build/", "dist/", ".git/", "__pycache__/",
        "*.pyc", "*.pyo", "*.pyd", ".DS_Store", "*.log"
    ]


class EnvironmentVariables:
    """Centralized environment variable definitions"""
    
    # Backend configuration
    BACKEND_URL = "LEANVIBE_BACKEND_URL"
    API_PORT = "LEANVIBE_API_PORT"
    
    # Model configuration
    MODEL_NAME = "LEANVIBE_MODEL_NAME"
    DEPLOYMENT_MODE = "LEANVIBE_DEPLOYMENT_MODE"
    MLX_SERVER_URL = "LEANVIBE_MLX_SERVER_URL"
    MAX_TOKENS = "LEANVIBE_MAX_TOKENS"
    TEMPERATURE = "LEANVIBE_TEMPERATURE"
    MLX_STRATEGY = "LEANVIBE_MLX_STRATEGY"
    
    # Directory configuration
    CACHE_DIR = "LEANVIBE_CACHE_DIR"
    CONFIG_DIR = "LEANVIBE_CONFIG_DIR"
    LOG_DIR = "LEANVIBE_LOG_DIR"
    
    # Feature flags
    NOTIFICATIONS_ENABLED = "LEANVIBE_NOTIFICATIONS_ENABLED"
    DEBUG_MODE = "LEANVIBE_DEBUG_MODE"
    DEVELOPMENT_MODE = "LEANVIBE_DEVELOPMENT_MODE"
    
    # Performance configuration
    TIMEOUT_SECONDS = "LEANVIBE_TIMEOUT_SECONDS"
    CACHE_TTL = "LEANVIBE_CACHE_TTL"
    
    @classmethod
    def get_env_vars(cls) -> Dict[str, str]:
        """Get all environment variables with their values"""
        env_vars = {}
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and attr_name.isupper():
                env_var_name = getattr(cls, attr_name)
                if isinstance(env_var_name, str):
                    env_vars[env_var_name] = os.getenv(env_var_name, "")
        return env_vars


class NetworkConfig(BaseModel):
    """Network and connectivity configuration"""
    backend_url: str = Field(default=DefaultValues.DEFAULT_BACKEND_URL)
    api_port: int = Field(default=DefaultValues.DEFAULT_API_PORT, ge=1, le=65535)
    timeout_seconds: int = Field(default=DefaultValues.DEFAULT_TIMEOUT_SECONDS, ge=1, le=300)
    
    @field_validator('backend_url')
    @classmethod 
    def validate_backend_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Backend URL must start with http:// or https://')
        return v.rstrip('/')


class ModelConfig(BaseModel):
    """Unified model configuration for all MLX services"""
    model_name: str = Field(default=DefaultValues.DEFAULT_MODEL_NAME)
    deployment_mode: DeploymentMode = Field(default=DeploymentMode.AUTO)
    mlx_strategy: MLXInferenceStrategy = Field(default=MLXInferenceStrategy.AUTO)
    server_url: str = Field(default=DefaultValues.DEFAULT_MLX_SERVER_URL)
    max_tokens: int = Field(default=DefaultValues.DEFAULT_MAX_TOKENS, ge=1, le=4096)
    temperature: float = Field(default=DefaultValues.DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    
    @field_validator('server_url')
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Server URL must start with http:// or https://')
        return v.rstrip('/')


class DirectoryConfig(BaseModel):
    """Directory and file path configuration"""
    cache_dir: Path = Field(default_factory=lambda: Path(DefaultValues.DEFAULT_CACHE_DIR).expanduser())
    config_dir: Path = Field(default_factory=lambda: Path(DefaultValues.DEFAULT_CONFIG_DIR).expanduser())
    log_dir: Path = Field(default_factory=lambda: Path(DefaultValues.DEFAULT_LOG_DIR).expanduser())
    
    @field_validator('cache_dir', 'config_dir', 'log_dir')
    @classmethod
    def expand_path(cls, v: Path) -> Path:
        return v.expanduser().resolve()


class NotificationConfig(BaseModel):
    """Unified notification configuration"""
    enabled: bool = Field(default=True)
    desktop_enabled: bool = Field(default=True)
    terminal_enabled: bool = Field(default=True)
    sound_enabled: bool = Field(default=False)
    
    # Priority and rate limiting
    minimum_priority: NotificationLevel = Field(default=DefaultValues.DEFAULT_MIN_PRIORITY)
    throttle_seconds: int = Field(default=DefaultValues.DEFAULT_THROTTLE_SECONDS, ge=0, le=300)
    max_per_minute: int = Field(default=DefaultValues.DEFAULT_MAX_PER_MINUTE, ge=1, le=100)
    
    # Display settings
    timeout_seconds: int = Field(default=DefaultValues.DEFAULT_NOTIFICATION_TIMEOUT, ge=1, le=30)
    position: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = "top-right"
    
    # Terminal settings
    max_overlay_items: int = Field(default=DefaultValues.DEFAULT_MAX_OVERLAY_ITEMS, ge=1, le=20)
    overlay_duration: int = Field(default=DefaultValues.DEFAULT_OVERLAY_DURATION, ge=1, le=10)
    show_timestamp: bool = Field(default=True)
    show_source: bool = Field(default=True)
    
    # Event filtering
    enabled_events: List[str] = Field(default_factory=lambda: DefaultValues.DEFAULT_ENABLED_EVENTS.copy())


class FileFilterConfig(BaseModel):
    """File filtering configuration"""
    exclude_patterns: List[str] = Field(default_factory=lambda: DefaultValues.DEFAULT_EXCLUDE_PATTERNS.copy())
    include_patterns: List[str] = Field(default_factory=list)
    max_file_size: int = Field(default=10485760, ge=1)  # 10MB default
    follow_symlinks: bool = Field(default=False)


class PerformanceConfig(BaseModel):
    """Performance and caching configuration"""
    cache_ttl: int = Field(default=DefaultValues.DEFAULT_CACHE_TTL, ge=1, le=3600)
    max_memory_usage: int = Field(default=1073741824, ge=100000000)  # 1GB default
    enable_caching: bool = Field(default=True)
    enable_profiling: bool = Field(default=False)
    thread_pool_size: int = Field(default=4, ge=1, le=32)


class DebugConfig(BaseModel):
    """Debug and development configuration"""
    debug_mode: bool = Field(default=False)
    development_mode: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    enable_tracing: bool = Field(default=False)
    save_request_logs: bool = Field(default=False)


class UnifiedConfig(BaseModel):
    """Main unified configuration class consolidating all settings"""
    
    # Core configuration sections
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    directories: DirectoryConfig = Field(default_factory=DirectoryConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    file_filters: FileFilterConfig = Field(default_factory=FileFilterConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    debug: DebugConfig = Field(default_factory=DebugConfig)
    
    # Metadata
    config_version: str = Field(default="1.0.0")
    profile_name: str = Field(default="default")
    
    @classmethod
    def from_env(cls) -> "UnifiedConfig":
        """Create configuration from environment variables"""
        env = EnvironmentVariables
        
        # Network configuration from env
        network_config = NetworkConfig(
            backend_url=os.getenv(env.BACKEND_URL, DefaultValues.DEFAULT_BACKEND_URL),
            api_port=int(os.getenv(env.API_PORT, str(DefaultValues.DEFAULT_API_PORT))),
            timeout_seconds=int(os.getenv(env.TIMEOUT_SECONDS, str(DefaultValues.DEFAULT_TIMEOUT_SECONDS)))
        )
        
        # Model configuration from env
        model_config = ModelConfig(
            model_name=os.getenv(env.MODEL_NAME, DefaultValues.DEFAULT_MODEL_NAME),
            deployment_mode=DeploymentMode(os.getenv(env.DEPLOYMENT_MODE, DeploymentMode.AUTO.value)),
            mlx_strategy=MLXInferenceStrategy(os.getenv(env.MLX_STRATEGY, MLXInferenceStrategy.AUTO.value)),
            server_url=os.getenv(env.MLX_SERVER_URL, DefaultValues.DEFAULT_MLX_SERVER_URL),
            max_tokens=int(os.getenv(env.MAX_TOKENS, str(DefaultValues.DEFAULT_MAX_TOKENS))),
            temperature=float(os.getenv(env.TEMPERATURE, str(DefaultValues.DEFAULT_TEMPERATURE)))
        )
        
        # Directory configuration from env
        directory_config = DirectoryConfig(
            cache_dir=Path(os.getenv(env.CACHE_DIR, DefaultValues.DEFAULT_CACHE_DIR)).expanduser(),
            config_dir=Path(os.getenv(env.CONFIG_DIR, DefaultValues.DEFAULT_CONFIG_DIR)).expanduser(),
            log_dir=Path(os.getenv(env.LOG_DIR, DefaultValues.DEFAULT_LOG_DIR)).expanduser()
        )
        
        # Debug configuration from env
        debug_config = DebugConfig(
            debug_mode=os.getenv(env.DEBUG_MODE, "false").lower() == "true",
            development_mode=os.getenv(env.DEVELOPMENT_MODE, "false").lower() == "true"
        )
        
        # Performance configuration from env
        performance_config = PerformanceConfig(
            cache_ttl=int(os.getenv(env.CACHE_TTL, str(DefaultValues.DEFAULT_CACHE_TTL)))
        )
        
        # Notification configuration from env
        notification_config = NotificationConfig(
            enabled=os.getenv(env.NOTIFICATIONS_ENABLED, "true").lower() == "true"
        )
        
        return cls(
            network=network_config,
            model=model_config,
            directories=directory_config,
            debug=debug_config,
            performance=performance_config,
            notifications=notification_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return self.model_dump()
    
    def get_backend_url(self) -> str:
        """Get the backend URL (legacy compatibility)"""
        return self.network.backend_url
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration (legacy compatibility)"""
        return self.model.model_dump()
    
    def is_development_mode(self) -> bool:
        """Check if in development mode"""
        return self.debug.development_mode or self.debug.debug_mode


class ConfigurationService:
    """Service for managing unified configuration"""
    
    def __init__(self):
        self._config: Optional[UnifiedConfig] = None
        self._env_override = False
    
    def load_config(self, config_path: Optional[Path] = None, use_env: bool = True) -> UnifiedConfig:
        """Load configuration from file or environment"""
        if use_env:
            self._config = UnifiedConfig.from_env()
            self._env_override = True
        else:
            # TODO: Implement file-based configuration loading
            self._config = UnifiedConfig()
        
        return self._config
    
    def get_config(self) -> UnifiedConfig:
        """Get current configuration, loading if needed"""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> UnifiedConfig:
        """Reload configuration"""
        self._config = None
        return self.load_config(use_env=self._env_override)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration"""
        config = self.get_config()
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate network connectivity
        try:
            import urllib.request
            urllib.request.urlopen(config.network.backend_url, timeout=5)
        except Exception:
            validation_results["warnings"].append(f"Backend URL {config.network.backend_url} not reachable")
        
        # Validate directories
        for dir_name, dir_path in [
            ("cache", config.directories.cache_dir),
            ("config", config.directories.config_dir),
            ("log", config.directories.log_dir)
        ]:
            if not dir_path.parent.exists():
                validation_results["warnings"].append(f"{dir_name} directory parent does not exist: {dir_path.parent}")
        
        return validation_results


# Global configuration service instance
config_service = ConfigurationService()

# Convenience functions for backward compatibility
def get_config() -> UnifiedConfig:
    """Get the global configuration instance"""
    return config_service.get_config()

def get_backend_url() -> str:
    """Get backend URL (legacy compatibility)"""
    return config_service.get_config().network.backend_url

def get_model_config() -> Dict[str, Any]:
    """Get model configuration (legacy compatibility)"""
    return config_service.get_config().model.model_dump()

def is_development_mode() -> bool:
    """Check if in development mode (legacy compatibility)"""
    return config_service.get_config().is_development_mode()