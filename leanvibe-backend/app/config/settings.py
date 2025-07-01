"""
Environment-aware configuration settings for LeanVibe backend.
Supports development, staging, and production environments.
"""
import os
from enum import Enum
from typing import List, Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings


class Environment(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class MLXStrategy(str, Enum):
    """MLX service strategy options."""
    MOCK = "MOCK"
    PRAGMATIC = "PRAGMATIC"
    PRODUCTION = "PRODUCTION"


class LeanVibeSettings(BaseSettings):
    """LeanVibe backend configuration settings."""
    
    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        env="LEANVIBE_ENV",
        description="Current environment"
    )
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="LEANVIBE_HOST")
    port: int = Field(default=8001, env="LEANVIBE_PORT")
    
    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        env="LEANVIBE_SECRET_KEY",
        description="Secret key for JWT tokens and encryption"
    )
    
    # Database
    database_url: Optional[str] = Field(default=None, env="LEANVIBE_DATABASE_URL")
    redis_url: Optional[str] = Field(default=None, env="LEANVIBE_REDIS_URL")
    
    # MLX AI Configuration
    mlx_model: str = Field(
        default="microsoft/Phi-3.5-mini-instruct",
        env="LEANVIBE_MLX_MODEL"
    )
    mlx_strategy: MLXStrategy = Field(
        default=MLXStrategy.MOCK,
        env="LEANVIBE_MLX_STRATEGY"
    )
    
    # API Configuration
    api_url: str = Field(default="http://localhost:8001", env="LEANVIBE_API_URL")
    
    # Feature Flags
    enable_logging: bool = Field(default=True, env="LEANVIBE_ENABLE_LOGGING")
    enable_monitoring: bool = Field(default=False, env="LEANVIBE_ENABLE_MONITORING")
    enable_rate_limiting: bool = Field(default=False, env="LEANVIBE_ENABLE_RATE_LIMITING")
    enable_api_key_auth: bool = Field(default=False, env="LEANVIBE_ENABLE_API_KEY_AUTH")
    disable_analytics: bool = Field(default=True, env="LEANVIBE_DISABLE_ANALYTICS")
    
    # Performance
    metrics_port: int = Field(default=9090, env="LEANVIBE_METRICS_PORT")
    log_level: str = Field(default="INFO", env="LEANVIBE_LOG_LEVEL")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == Environment.STAGING
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS allowed origins based on environment."""
        if self.is_production:
            return [
                "https://app.leanvibe.ai",
                "https://leanvibe.ai"
            ]
        elif self.is_staging:
            return [
                "https://staging.leanvibe.ai",
                "https://app-staging.leanvibe.ai"
            ]
        else:
            # Development - allow localhost and iOS simulator
            return [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080"
            ]
    
    @property
    def websocket_url(self) -> str:
        """Get WebSocket URL based on API URL."""
        if self.api_url.startswith("https://"):
            return self.api_url.replace("https://", "wss://") + "/ws"
        else:
            return self.api_url.replace("http://", "ws://") + "/ws"
    
    def validate_production_config(self) -> None:
        """Validate production configuration requirements."""
        if not self.is_production:
            return
            
        errors = []
        
        if self.secret_key == "dev-secret-key-change-in-production":
            errors.append("LEANVIBE_SECRET_KEY must be set for production")
            
        if not self.database_url:
            errors.append("LEANVIBE_DATABASE_URL must be set for production")
            
        if self.mlx_strategy == MLXStrategy.MOCK:
            errors.append("MLX_STRATEGY should not be MOCK in production")
            
        if not self.api_url.startswith("https://"):
            errors.append("API_URL must use HTTPS in production")
            
        if errors:
            raise ValueError(f"Production configuration errors: {', '.join(errors)}")
    
    class Config:
        env_file = "../.env"  # Look for .env in parent directory
        case_sensitive = False


# Global settings instance
settings = LeanVibeSettings()

# Validate production configuration on import
if settings.is_production:
    settings.validate_production_config()