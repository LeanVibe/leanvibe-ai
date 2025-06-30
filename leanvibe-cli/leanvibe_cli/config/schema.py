"""
Configuration schema and validation for LeenVibe CLI

Defines the complete configuration structure with validation rules using Pydantic.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, HttpUrl, validator
from pathlib import Path


class DesktopSettings(BaseModel):
    """Desktop notification settings"""
    timeout_seconds: int = Field(5, ge=1, le=30)
    critical_sound: bool = True
    high_sound: bool = False
    position: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = "top-right"


class TerminalSettings(BaseModel):
    """Terminal notification settings"""
    max_overlay_items: int = Field(5, ge=1, le=20)
    overlay_duration: int = Field(3, ge=1, le=10)
    show_timestamp: bool = True
    show_source: bool = True


class NotificationSettings(BaseModel):
    """Notification configuration"""
    # Global toggles
    enabled: bool = True
    desktop_enabled: bool = True
    terminal_enabled: bool = True
    sound_enabled: bool = False
    
    # Priority filtering
    minimum_priority: Literal["debug", "low", "medium", "high", "critical"] = "medium"
    
    # Rate limiting
    throttle_seconds: int = Field(30, ge=0, le=300)
    max_per_minute: int = Field(10, ge=1, le=100)
    
    # Event filtering
    enabled_events: List[str] = Field(default_factory=lambda: [
        "code_quality_issue",
        "architectural_violation", 
        "security_vulnerability",
        "performance_regression",
        "test_failure",
        "build_failure",
        "file_change",
        "session_update"
    ])
    disabled_events: List[str] = Field(default_factory=lambda: [
        "heartbeat",
        "debug_trace",
        "connection_status"
    ])
    
    # Nested settings
    desktop: DesktopSettings = Field(default_factory=DesktopSettings)
    terminal: TerminalSettings = Field(default_factory=TerminalSettings)
    
    @field_validator('disabled_events')
    @classmethod 
    def no_overlap_events(cls, v):
        """Ensure no event is both enabled and disabled"""
        # Simplified validation for Pydantic v2
        return v


class FileFilters(BaseModel):
    """File filtering configuration"""
    exclude_patterns: List[str] = Field(default_factory=lambda: [
        "*.pyc", "__pycache__/*", ".git/*", "node_modules/*",
        ".venv/*", "venv/*", "*.log", ".DS_Store", "*.swp", "*.swo",
        ".idea/*", ".vscode/*"
    ])
    include_only_patterns: List[str] = Field(default_factory=list)
    
    @field_validator('include_only_patterns')
    @classmethod
    def validate_patterns(cls, v):
        """Validate glob patterns"""
        # Basic validation - could be enhanced
        for pattern in v:
            if not pattern or pattern.isspace():
                raise ValueError(f"Invalid pattern: '{pattern}'")
        return v


class DisplaySettings(BaseModel):
    """Display and UI settings"""
    theme: Literal["dark", "light", "auto"] = "dark"
    verbose: bool = False
    show_progress: bool = True
    timestamp_format: Literal["relative", "absolute", "iso"] = "relative"
    color_output: bool = True


class PerformanceSettings(BaseModel):
    """Performance tuning settings"""
    cache_enabled: bool = True
    cache_ttl_seconds: int = Field(300, ge=0, le=3600)
    parallel_connections: int = Field(5, ge=1, le=20)
    batch_size: int = Field(100, ge=10, le=1000)


class ProfileConfig(BaseModel):
    """Configuration for a single profile"""
    # Connection settings
    backend_url: str = "http://localhost:8000"
    api_timeout: int = Field(30, ge=5, le=300)
    websocket_timeout: int = Field(300, ge=30, le=3600)
    
    # Feature settings
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    file_filters: FileFilters = Field(default_factory=FileFilters)
    display: DisplaySettings = Field(default_factory=DisplaySettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    
    @field_validator('backend_url')
    @classmethod
    def validate_backend_url(cls, v):
        """Validate backend URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Backend URL must start with http:// or https://")
        # Remove trailing slash for consistency
        return v.rstrip('/')


class ConfigSchema(BaseModel):
    """Root configuration schema"""
    version: str = "1.0"
    active_profile: str = "default"
    profiles: Dict[str, ProfileConfig] = Field(default_factory=lambda: {
        "default": ProfileConfig()
    })
    
    @field_validator('profiles')
    @classmethod
    def validate_profiles(cls, v):
        """Ensure at least one profile exists"""
        if not v:
            raise ValueError("At least one profile must be defined")
        if "default" not in v:
            raise ValueError("Default profile must exist")
        return v
    
    @field_validator('active_profile')
    @classmethod
    def validate_active_profile(cls, v):
        """Ensure active profile exists"""
        # Simplified validation for Pydantic v2
        return v
    
    def get_active_config(self) -> ProfileConfig:
        """Get the active profile configuration"""
        return self.profiles[self.active_profile]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization"""
        return self.dict(exclude_unset=True, exclude_defaults=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSchema":
        """Create from dictionary (e.g., loaded from YAML)"""
        return cls(**data)
    
    def merge_with_cli_config(self, cli_config: Any) -> None:
        """Merge with existing CLIConfig object for backward compatibility"""
        active = self.get_active_config()
        
        # Map configuration to CLIConfig attributes
        cli_config.backend_url = active.backend_url
        cli_config.api_timeout = active.api_timeout
        cli_config.websocket_timeout = active.websocket_timeout
        
        # Notification settings
        cli_config.desktop_notifications = active.notifications.desktop_enabled
        cli_config.terminal_notifications = active.notifications.terminal_enabled
        cli_config.sound_notifications = active.notifications.sound_enabled
        cli_config.notification_level = active.notifications.minimum_priority
        cli_config.notification_throttle_seconds = active.notifications.throttle_seconds
        cli_config.max_notifications_per_minute = active.notifications.max_per_minute
        cli_config.enabled_event_types = active.notifications.enabled_events
        
        # Display settings
        cli_config.verbose = active.display.verbose
        cli_config.show_progress = active.display.show_progress
        
        # File filters
        cli_config.exclude_patterns = active.file_filters.exclude_patterns