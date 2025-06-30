"""
Unified Configuration Module for LeanVibe

Provides a single, consistent configuration system for all LeanVibe components,
eliminating duplication and providing centralized environment variable management.
"""

from .unified_config import (
    # Main configuration classes
    UnifiedConfig,
    ConfigurationService,
    
    # Component configuration classes
    NetworkConfig,
    ModelConfig,
    DirectoryConfig,
    NotificationConfig,
    FileFilterConfig,
    PerformanceConfig,
    DebugConfig,
    
    # Enums and constants
    DeploymentMode,
    NotificationLevel,
    MLXInferenceStrategy,
    DefaultValues,
    EnvironmentVariables,
    
    # Service instance and convenience functions
    config_service,
    get_config,
    get_backend_url,
    get_model_config,
    is_development_mode,
)

__all__ = [
    # Main classes
    "UnifiedConfig",
    "ConfigurationService",
    
    # Component configs
    "NetworkConfig",
    "ModelConfig", 
    "DirectoryConfig",
    "NotificationConfig",
    "FileFilterConfig",
    "PerformanceConfig",
    "DebugConfig",
    
    # Enums
    "DeploymentMode",
    "NotificationLevel", 
    "MLXInferenceStrategy",
    
    # Constants
    "DefaultValues",
    "EnvironmentVariables",
    
    # Service and functions
    "config_service",
    "get_config",
    "get_backend_url",
    "get_model_config",
    "is_development_mode",
]