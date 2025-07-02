"""
Centralized Secrets Management for LeanVibe Backend
Provides secure secret retrieval from multiple sources with fallback mechanisms
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
import base64
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


@dataclass
class SecretConfig:
    """Configuration for secret management"""
    environment: str
    use_encryption: bool = True
    fallback_to_env: bool = True
    cache_secrets: bool = False
    secret_sources: list = None


class SecretSource(ABC):
    """Abstract base class for secret sources"""
    
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret by key"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this secret source is available"""
        pass


class EnvironmentSecretSource(SecretSource):
    """Retrieves secrets from environment variables"""
    
    def get_secret(self, key: str) -> Optional[str]:
        return os.getenv(key)
    
    def is_available(self) -> bool:
        return True


class FileSecretSource(SecretSource):
    """Retrieves secrets from encrypted JSON file"""
    
    def __init__(self, file_path: Path, encryption_key: Optional[str] = None):
        self.file_path = file_path
        self.encryption_key = encryption_key
        self._cache = {}
        self._loaded = False
    
    def get_secret(self, key: str) -> Optional[str]:
        if not self._loaded:
            self._load_secrets()
        return self._cache.get(key)
    
    def is_available(self) -> bool:
        return self.file_path.exists()
    
    def _load_secrets(self):
        """Load and decrypt secrets from file"""
        try:
            if not self.file_path.exists():
                logger.warning(f"Secret file not found: {self.file_path}")
                return
            
            content = self.file_path.read_text()
            
            if self.encryption_key:
                # Decrypt content
                fernet = Fernet(self.encryption_key.encode())
                content = fernet.decrypt(base64.b64decode(content)).decode()
            
            self._cache = json.loads(content)
            self._loaded = True
            logger.info(f"Loaded {len(self._cache)} secrets from file")
            
        except Exception as e:
            logger.error(f"Failed to load secrets from file: {e}")
            self._cache = {}


class DockerSecretSource(SecretSource):
    """Retrieves secrets from Docker secrets (/run/secrets/)"""
    
    def __init__(self, secrets_dir: Path = Path("/run/secrets")):
        self.secrets_dir = secrets_dir
    
    def get_secret(self, key: str) -> Optional[str]:
        secret_file = self.secrets_dir / key.lower()
        if secret_file.exists():
            try:
                return secret_file.read_text().strip()
            except Exception as e:
                logger.error(f"Failed to read Docker secret {key}: {e}")
        return None
    
    def is_available(self) -> bool:
        return self.secrets_dir.exists()


class SecretsManager:
    """Central secrets management with multiple source support"""
    
    def __init__(self, config: SecretConfig):
        self.config = config
        self.sources: List[SecretSource] = []
        self._setup_sources()
        
        # Cache for performance
        self._cache = {} if config.cache_secrets else None
    
    def _setup_sources(self):
        """Initialize secret sources based on configuration"""
        
        # Docker secrets (production)
        if self.config.environment == "production":
            docker_source = DockerSecretSource()
            if docker_source.is_available():
                self.sources.append(docker_source)
                logger.info("✅ Docker secrets source available")
        
        # Encrypted file source (staging/production)
        if self.config.environment in ["staging", "production"]:
            secrets_file = Path("secrets.enc")
            encryption_key = os.getenv("LEANVIBE_ENCRYPTION_KEY")
            if secrets_file.exists() and encryption_key:
                file_source = FileSecretSource(secrets_file, encryption_key)
                self.sources.append(file_source)
                logger.info("✅ Encrypted file secrets source available")
        
        # Environment variables (all environments)
        if self.config.fallback_to_env:
            self.sources.append(EnvironmentSecretSource())
            logger.info("✅ Environment variables source available")
        
        logger.info(f"Initialized {len(self.sources)} secret sources")
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret with fallback through multiple sources
        
        Args:
            key: Secret key to retrieve
            default: Default value if secret not found
            
        Returns:
            Secret value or default
        """
        
        # Check cache first
        if self._cache and key in self._cache:
            return self._cache[key]
        
        # Try each source in order
        for source in self.sources:
            try:
                value = source.get_secret(key)
                if value is not None:
                    # Cache the result
                    if self._cache is not None:
                        self._cache[key] = value
                    
                    logger.debug(f"Secret '{key}' retrieved from {type(source).__name__}")
                    return value
            except Exception as e:
                logger.warning(f"Failed to get secret '{key}' from {type(source).__name__}: {e}")
        
        logger.warning(f"Secret '{key}' not found in any source")
        return default
    
    def get_required_secret(self, key: str) -> str:
        """
        Retrieve a required secret, raising an error if not found
        
        Args:
            key: Secret key to retrieve
            
        Returns:
            Secret value
            
        Raises:
            ValueError: If secret is not found
        """
        value = self.get_secret(key)
        if value is None:
            raise ValueError(f"Required secret '{key}' not found")
        return value
    
    def get_database_url(self) -> str:
        """Get database URL with proper fallbacks"""
        return self.get_required_secret("LEANVIBE_DATABASE_URL")
    
    def get_secret_key(self) -> str:
        """Get application secret key"""
        return self.get_required_secret("LEANVIBE_SECRET_KEY")
    
    def get_mlx_config(self) -> Dict[str, str]:
        """Get MLX-related configuration"""
        return {
            "model": self.get_secret("LEANVIBE_MLX_MODEL", "microsoft/Phi-3.5-mini-instruct"),
            "strategy": self.get_secret("LEANVIBE_MLX_STRATEGY", "MOCK"),
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return {
            "host": self.get_secret("LEANVIBE_HOST", "0.0.0.0"),
            "port": int(self.get_secret("LEANVIBE_PORT", "8001")),
            "api_url": self.get_secret("LEANVIBE_API_URL", "http://localhost:8001"),
        }
    
    def validate_secrets(self) -> Dict[str, Any]:
        """
        Validate that all required secrets are available
        
        Returns:
            Validation report
        """
        required_secrets = [
            "LEANVIBE_SECRET_KEY",
            "LEANVIBE_DATABASE_URL",
        ]
        
        results = {
            "valid": True,
            "missing": [],
            "available_sources": len(self.sources),
            "environment": self.config.environment
        }
        
        for secret in required_secrets:
            if self.get_secret(secret) is None:
                results["missing"].append(secret)
                results["valid"] = False
        
        return results


def create_secrets_manager(environment: str = None) -> SecretsManager:
    """
    Factory function to create a SecretsManager with appropriate configuration
    
    Args:
        environment: Environment name (development, staging, production)
        
    Returns:
        Configured SecretsManager instance
    """
    if environment is None:
        environment = os.getenv("LEANVIBE_ENV", "development")
    
    config = SecretConfig(
        environment=environment,
        use_encryption=environment in ["staging", "production"],
        fallback_to_env=True,
        cache_secrets=environment == "production"
    )
    
    return SecretsManager(config)


# Global instance for easy access
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = create_secrets_manager()
    return _secrets_manager


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a secret"""
    return get_secrets_manager().get_secret(key, default)


def get_required_secret(key: str) -> str:
    """Convenience function to get a required secret"""
    return get_secrets_manager().get_required_secret(key)