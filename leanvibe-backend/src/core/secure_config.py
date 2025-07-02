"""
Secure Configuration Management for LeanVibe Backend
Integrates with secrets manager for production-ready configuration
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from .secrets_manager import get_secrets_manager, SecretConfig

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class MLXConfig:
    """MLX model configuration"""
    model_name: str
    strategy: str
    cache_dir: Optional[str] = None
    quantization: str = "4bit"
    max_tokens: int = 32768


@dataclass
class APIConfig:
    """API server configuration"""
    host: str
    port: int
    debug: bool
    cors_origins: list
    request_timeout: int = 30


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600
    rate_limit_per_minute: int = 60
    enable_https: bool = False


@dataclass
class MonitoringConfig:
    """Monitoring and logging configuration"""
    log_level: str
    enable_metrics: bool
    metrics_port: int
    sentry_dsn: Optional[str] = None


class SecureConfigManager:
    """Secure configuration manager using secrets management"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv("LEANVIBE_ENV", "development")
        self.secrets_manager = get_secrets_manager()
        self._config_cache = {}
        
        logger.info(f"Initializing secure config for environment: {self.environment}")
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        if "database" not in self._config_cache:
            self._config_cache["database"] = DatabaseConfig(
                url=self.secrets_manager.get_required_secret("LEANVIBE_DATABASE_URL"),
                pool_size=int(self.secrets_manager.get_secret("LEANVIBE_DB_POOL_SIZE", "10")),
                max_overflow=int(self.secrets_manager.get_secret("LEANVIBE_DB_MAX_OVERFLOW", "20")),
                pool_timeout=int(self.secrets_manager.get_secret("LEANVIBE_DB_POOL_TIMEOUT", "30")),
                pool_recycle=int(self.secrets_manager.get_secret("LEANVIBE_DB_POOL_RECYCLE", "3600"))
            )
        return self._config_cache["database"]
    
    def get_mlx_config(self) -> MLXConfig:
        """Get MLX configuration"""
        if "mlx" not in self._config_cache:
            mlx_config = self.secrets_manager.get_mlx_config()
            self._config_cache["mlx"] = MLXConfig(
                model_name=mlx_config["model"],
                strategy=mlx_config["strategy"],
                cache_dir=self.secrets_manager.get_secret("LEANVIBE_MLX_CACHE_DIR"),
                quantization=self.secrets_manager.get_secret("LEANVIBE_MLX_QUANTIZATION", "4bit"),
                max_tokens=int(self.secrets_manager.get_secret("LEANVIBE_MLX_MAX_TOKENS", "32768"))
            )
        return self._config_cache["mlx"]
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
        if "api" not in self._config_cache:
            api_config = self.secrets_manager.get_api_config()
            self._config_cache["api"] = APIConfig(
                host=api_config["host"],
                port=api_config["port"],
                debug=self.environment == "development",
                cors_origins=self._get_cors_origins(),
                request_timeout=int(self.secrets_manager.get_secret("LEANVIBE_REQUEST_TIMEOUT", "30"))
            )
        return self._config_cache["api"]
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        if "security" not in self._config_cache:
            self._config_cache["security"] = SecurityConfig(
                secret_key=self.secrets_manager.get_required_secret("LEANVIBE_SECRET_KEY"),
                jwt_algorithm=self.secrets_manager.get_secret("LEANVIBE_JWT_ALGORITHM", "HS256"),
                jwt_expiration=int(self.secrets_manager.get_secret("LEANVIBE_JWT_EXPIRATION", "3600")),
                rate_limit_per_minute=int(self.secrets_manager.get_secret("LEANVIBE_RATE_LIMIT", "60")),
                enable_https=self.environment == "production"
            )
        return self._config_cache["security"]
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        if "monitoring" not in self._config_cache:
            log_level = "DEBUG" if self.environment == "development" else "INFO"
            if self.environment == "production":
                log_level = "WARNING"
            
            self._config_cache["monitoring"] = MonitoringConfig(
                log_level=self.secrets_manager.get_secret("LEANVIBE_LOG_LEVEL", log_level),
                enable_metrics=self.secrets_manager.get_secret("LEANVIBE_ENABLE_MONITORING", "false").lower() == "true",
                metrics_port=int(self.secrets_manager.get_secret("LEANVIBE_METRICS_PORT", "9090")),
                sentry_dsn=self.secrets_manager.get_secret("LEANVIBE_SENTRY_DSN")
            )
        return self._config_cache["monitoring"]
    
    def _get_cors_origins(self) -> list:
        """Get CORS origins based on environment"""
        if self.environment == "development":
            return ["http://localhost:3000", "http://localhost:8001", "http://127.0.0.1:3000"]
        elif self.environment == "staging":
            return [
                "https://staging.leanvibe.ai",
                "https://staging-api.leanvibe.ai"
            ]
        else:  # production
            return [
                "https://leanvibe.ai",
                "https://api.leanvibe.ai",
                "https://app.leanvibe.ai"
            ]
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate all configuration"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "environment": self.environment
        }
        
        try:
            # Validate secrets
            secrets_validation = self.secrets_manager.validate_secrets()
            if not secrets_validation["valid"]:
                results["valid"] = False
                results["errors"].extend([f"Missing secret: {s}" for s in secrets_validation["missing"]])
            
            # Validate configurations
            configs_to_test = [
                ("database", self.get_database_config),
                ("mlx", self.get_mlx_config),
                ("api", self.get_api_config),
                ("security", self.get_security_config),
                ("monitoring", self.get_monitoring_config)
            ]
            
            for config_name, config_func in configs_to_test:
                try:
                    config = config_func()
                    logger.debug(f"✅ {config_name} configuration valid")
                except Exception as e:
                    results["valid"] = False
                    results["errors"].append(f"{config_name} configuration error: {e}")
            
            # Environment-specific validations
            if self.environment == "production":
                security_config = self.get_security_config()
                if len(security_config.secret_key) < 32:
                    results["warnings"].append("Production secret key should be at least 32 characters")
                
                if not security_config.enable_https:
                    results["warnings"].append("HTTPS should be enabled in production")
            
        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Configuration validation failed: {e}")
        
        return results
    
    def get_health_check_info(self) -> Dict[str, Any]:
        """Get health check information"""
        return {
            "environment": self.environment,
            "secrets_available": len(self.secrets_manager.sources),
            "configs_cached": len(self._config_cache),
            "validation": self.validate_configuration()
        }


# Global instance
_config_manager: Optional[SecureConfigManager] = None


def get_config_manager() -> SecureConfigManager:
    """Get global configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = SecureConfigManager()
    return _config_manager


def get_database_config() -> DatabaseConfig:
    """Convenience function to get database config"""
    return get_config_manager().get_database_config()


def get_mlx_config() -> MLXConfig:
    """Convenience function to get MLX config"""
    return get_config_manager().get_mlx_config()


def get_api_config() -> APIConfig:
    """Convenience function to get API config"""
    return get_config_manager().get_api_config()


def get_security_config() -> SecurityConfig:
    """Convenience function to get security config"""
    return get_config_manager().get_security_config()


def get_monitoring_config() -> MonitoringConfig:
    """Convenience function to get monitoring config"""
    return get_config_manager().get_monitoring_config()