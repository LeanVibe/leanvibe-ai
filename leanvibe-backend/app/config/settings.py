"""
Environment-aware configuration settings for LeanVibe backend.
Supports development, staging, and production environments.
"""
import os
from enum import Enum
from typing import List, Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
    SettingsConfigDict = None

# Explicitly load .env file
from dotenv import load_dotenv
load_dotenv()


class Environment(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class MLXStrategy(str, Enum):
    """MLX service strategy options."""
    MOCK = "mock"
    PRAGMATIC = "pragmatic"
    PRODUCTION = "production"


class LeanVibeSettings(BaseSettings):
    """LeanVibe backend configuration settings."""
    
    # Use modern pydantic-settings configuration
    if SettingsConfigDict:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_prefix="LEANVIBE_",
            extra="ignore",
            case_sensitive=False
        )
    
    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Current environment"
    )
    
    # Server Configuration  
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001)
    
    # Security - CRITICAL: NO DEFAULT VALUES for production secrets
    secret_key: str = Field(
        env="LEANVIBE_SECRET_KEY",
        description="Secret key for JWT tokens and encryption (REQUIRED - no default)"
    )
    
    # Database
    database_url: Optional[str] = Field(default=None)
    
    # Neo4j Graph Database Configuration
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        env="NEO4J_URI",
        description="Neo4j connection URI"
    )
    neo4j_user: str = Field(
        default="neo4j",
        env="NEO4J_USER", 
        description="Neo4j username"
    )
    neo4j_password: Optional[str] = Field(
        default=None,
        env="NEO4J_PASSWORD",
        description="Neo4j password (REQUIRED for production - optional for development)"
    )
    neo4j_database: str = Field(
        default="neo4j",
        env="NEO4J_DATABASE",
        description="Neo4j database name"
    )
    redis_url: Optional[str] = Field(default=None)
    
    # Stripe Configuration
    stripe_secret_key: str = Field(
        default="sk_test_mock_key_for_development",
        description="Stripe secret key for payment processing"
    )
    stripe_publishable_key: str = Field(
        default="pk_test_mock_key_for_development", 
        description="Stripe publishable key for client-side"
    )
    stripe_webhook_secret: str = Field(
        default="whsec_mock_webhook_secret",
        description="Stripe webhook endpoint secret"
    )
    
    # MLX AI Configuration
    mlx_model: str = Field(default="microsoft/Phi-3.5-mini-instruct")
    mlx_strategy: MLXStrategy = Field(default=MLXStrategy.MOCK)
    
    # API Configuration
    api_url: str = Field(default="http://localhost:8001")
    api_base_url: str = Field(default="http://localhost:8001", env="API_BASE_URL")
    
    # Feature Flags
    enable_logging: bool = Field(default=True)
    enable_monitoring: bool = Field(default=False)
    enable_rate_limiting: bool = Field(default=False)
    enable_api_key_auth: bool = Field(default=False)
    disable_analytics: bool = Field(default=True)
    
    # iOS App Feature Flags  
    voice_features_enabled: bool = Field(default=True, env="VOICE_FEATURES_ENABLED")
    code_completion_enabled: bool = Field(default=True, env="CODE_COMPLETION_ENABLED")
    
    # Performance
    metrics_port: int = Field(default=9090)
    log_level: str = Field(default="INFO")
    
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
        
        # Secret key validation removed - now required via env var
            
        if not self.database_url:
            errors.append("LEANVIBE_DATABASE_URL must be set for production")
            
        if self.stripe_secret_key == "sk_test_mock_key_for_development":
            errors.append("LEANVIBE_STRIPE_SECRET_KEY must be set for production")
            
        if self.stripe_webhook_secret == "whsec_mock_webhook_secret":
            errors.append("LEANVIBE_STRIPE_WEBHOOK_SECRET must be set for production")
            
        if self.mlx_strategy == MLXStrategy.MOCK:
            errors.append("MLX_STRATEGY should not be MOCK in production")
            
        if not self.api_url.startswith("https://"):
            errors.append("API_URL must use HTTPS in production")
        
        if not self.neo4j_password:
            errors.append("NEO4J_PASSWORD must be set for production")
            
        if errors:
            raise ValueError(f"Production configuration errors: {', '.join(errors)}")


# Global settings instance - created after dotenv loading
settings = LeanVibeSettings()

# Validate production configuration on import
if settings.is_production:
    settings.validate_production_config()