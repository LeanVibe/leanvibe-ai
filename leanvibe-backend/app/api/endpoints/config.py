"""
Configuration API endpoints for iOS app backend integration.
Provides dynamic configuration to eliminate hardcoded values in the mobile app.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import json
from datetime import datetime

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])

# Configuration Models
class AppConfig(BaseModel):
    """Application configuration for iOS app"""
    app_version: str = "0.2.0"
    build_number: str = "1"
    app_name: str = "LeanVibe AI"
    onboarding_message: str = "Connect to your LeanVibe agent and start analyzing your codebase"
    support_email: str = "support@leanvibe.ai"
    docs_url: str = "https://docs.leanvibe.ai"
    
class FeatureFlags(BaseModel):
    """Feature flags for dynamic feature enabling"""
    voice_features: bool = True
    wake_phrase_detection: bool = True
    voice_recognition: bool = True
    beta_feedback: bool = True
    beta_analytics: bool = True
    advanced_settings: bool = True
    debug_settings: bool = True
    network_diagnostics: bool = True
    performance_monitoring: bool = True
    document_intelligence: bool = False  # Coming soon
    code_completion: bool = True
    architecture_analysis: bool = True
    real_time_sync: bool = True

class ThemeConfig(BaseModel):
    """Theme and UI configuration"""
    primary_color: str = "#007AFF"
    secondary_color: str = "#FF9500"
    success_color: str = "#34C759"
    error_color: str = "#FF3B30"
    warning_color: str = "#FF9500"
    
    # Language colors for syntax highlighting
    language_colors: Dict[str, str] = {
        "swift": "#FA7343",
        "python": "#3776AB", 
        "javascript": "#F7DF1E",
        "typescript": "#3178C6",
        "rust": "#000000",
        "go": "#00ADD8",
        "java": "#ED8B00",
        "kotlin": "#7F52FF",
        "dart": "#0175C2",
        "c": "#A8B9CC",
        "cpp": "#00599C",
        "csharp": "#239120",
        "php": "#777BB4",
        "ruby": "#CC342D",
        "html": "#E34F26",
        "css": "#1572B6",
        "unknown": "#8E8E93"
    }

class VoiceConfig(BaseModel):
    """Voice and speech configuration"""
    default_wake_phrase: str = "Hey LeanVibe"
    wake_phrase_sensitivity: float = 0.7
    voice_timeout_seconds: int = 30
    speech_recognition_language: str = "en-US"
    
    # Quick voice commands for project management
    quick_commands: list[str] = [
        "Show project status",
        "List current tasks", 
        "Open project dashboard",
        "Start voice recording",
        "Connect to agent",
        "Check system health"
    ]
    
    # Voice command templates
    command_templates: Dict[str, str] = {
        "project": "Open project {project_name}",
        "task": "Create task {task_description}",
        "status": "Show status for {project_name}",
        "connect": "Connect to {agent_name}",
        "analyze": "Analyze {file_name}"
    }

class PerformanceConfig(BaseModel):
    """Performance and monitoring configuration"""
    metrics_update_interval: int = 5  # seconds
    max_memory_usage_mb: int = 500
    max_cpu_usage_percent: float = 80.0
    websocket_ping_interval: int = 30  # seconds
    connection_timeout: int = 10  # seconds
    retry_attempts: int = 3
    
class UILayoutConfig(BaseModel):
    """UI layout and responsive design configuration"""
    grid_columns_portrait: int = 2
    grid_columns_landscape: int = 3
    card_corner_radius: float = 16.0
    animation_duration: float = 0.3
    haptic_feedback_enabled: bool = True

class FullConfiguration(BaseModel):
    """Complete app configuration"""
    app: AppConfig
    features: FeatureFlags  
    theme: ThemeConfig
    voice: VoiceConfig
    performance: PerformanceConfig
    ui: UILayoutConfig
    last_updated: datetime = Field(default_factory=datetime.now)

# In-memory configuration store (in production, use database)
_configuration_store: Dict[str, FullConfiguration] = {}

def get_default_configuration() -> FullConfiguration:
    """Get default configuration for new users"""
    return FullConfiguration(
        app=AppConfig(),
        features=FeatureFlags(),
        theme=ThemeConfig(),
        voice=VoiceConfig(),
        performance=PerformanceConfig(),
        ui=UILayoutConfig()
    )

@router.get("/", response_model=FullConfiguration)
async def get_configuration(user_id: Optional[str] = "default"):
    """
    Get complete app configuration for a user.
    If no user-specific config exists, returns default configuration.
    """
    if user_id in _configuration_store:
        return _configuration_store[user_id]
    
    # Return default configuration
    default_config = get_default_configuration()
    _configuration_store[user_id] = default_config
    return default_config

@router.get("/app", response_model=AppConfig)
async def get_app_config(user_id: Optional[str] = "default"):
    """Get app-specific configuration"""
    config = await get_configuration(user_id)
    return config.app

@router.get("/features", response_model=FeatureFlags)
async def get_feature_flags(user_id: Optional[str] = "default"):
    """Get feature flags configuration"""
    config = await get_configuration(user_id)
    return config.features

@router.get("/theme", response_model=ThemeConfig)
async def get_theme_config(user_id: Optional[str] = "default"):
    """Get theme and color configuration"""
    config = await get_configuration(user_id)
    return config.theme

@router.get("/voice", response_model=VoiceConfig)
async def get_voice_config(user_id: Optional[str] = "default"):
    """Get voice and speech configuration"""
    config = await get_configuration(user_id)
    return config.voice

@router.get("/performance", response_model=PerformanceConfig)
async def get_performance_config(user_id: Optional[str] = "default"):
    """Get performance monitoring configuration"""
    config = await get_configuration(user_id)
    return config.performance

@router.put("/features", response_model=FeatureFlags)
async def update_feature_flags(
    feature_flags: FeatureFlags,
    user_id: Optional[str] = "default"
):
    """Update feature flags for a user"""
    if user_id not in _configuration_store:
        _configuration_store[user_id] = get_default_configuration()
    
    _configuration_store[user_id].features = feature_flags
    _configuration_store[user_id].last_updated = datetime.now()
    
    return feature_flags

@router.put("/theme", response_model=ThemeConfig)
async def update_theme_config(
    theme_config: ThemeConfig,
    user_id: Optional[str] = "default"
):
    """Update theme configuration for a user"""
    if user_id not in _configuration_store:
        _configuration_store[user_id] = get_default_configuration()
    
    _configuration_store[user_id].theme = theme_config
    _configuration_store[user_id].last_updated = datetime.now()
    
    return theme_config

@router.put("/voice", response_model=VoiceConfig)
async def update_voice_config(
    voice_config: VoiceConfig,
    user_id: Optional[str] = "default"
):
    """Update voice configuration for a user"""
    if user_id not in _configuration_store:
        _configuration_store[user_id] = get_default_configuration()
    
    _configuration_store[user_id].voice = voice_config
    _configuration_store[user_id].last_updated = datetime.now()
    
    return voice_config

@router.get("/language-color/{language}")
async def get_language_color(
    language: str,
    user_id: Optional[str] = "default"
):
    """Get color for a specific programming language"""
    config = await get_configuration(user_id)
    color = config.theme.language_colors.get(language.lower(), config.theme.language_colors["unknown"])
    
    return {
        "language": language,
        "color": color,
        "hex_color": color
    }

@router.post("/reset")
async def reset_configuration(user_id: Optional[str] = "default"):
    """Reset user configuration to defaults"""
    _configuration_store[user_id] = get_default_configuration()
    return {"message": f"Configuration reset to defaults for user {user_id}"}

@router.get("/version")
async def get_version_info():
    """Get current app version information"""
    return {
        "api_version": "1.0.0",
        "app_version": "0.2.0", 
        "build_number": "1",
        "release_date": "2025-07-06",
        "features": {
            "voice_enabled": True,
            "real_time_sync": True,
            "architecture_analysis": True,
            "advanced_monitoring": True
        }
    }