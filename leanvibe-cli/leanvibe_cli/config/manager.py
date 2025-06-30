"""
Configuration manager for LeanVibe CLI

Handles loading, saving, and managing configuration with validation and profiles.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import yaml

from .schema import ConfigSchema, ProfileConfig


class ConfigurationManager:
    """Manages LeanVibe CLI configuration with profiles and validation"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".leanvibe"
        self.config_file = self.config_dir / "config.yml"
        self.backup_dir = self.config_dir / "backups"
        self.template_file = Path(__file__).parent.parent / "templates" / "default_config.yml"
        
        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Load or initialize configuration
        self._config: ConfigSchema = self._load_or_create()
    
    def _load_or_create(self) -> ConfigSchema:
        """Load existing configuration or create from template"""
        if self.config_file.exists():
            return self.load()
        else:
            # Create from template
            if self.template_file.exists():
                shutil.copy(self.template_file, self.config_file)
                return self.load()
            else:
                # Create minimal default
                config = ConfigSchema()
                self.save(config)
                return config
    
    def load(self) -> ConfigSchema:
        """Load configuration from disk"""
        try:
            with open(self.config_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Validate and create schema
            config = ConfigSchema.from_dict(data)
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")
    
    def save(self, config: Optional[ConfigSchema] = None) -> None:
        """Save configuration to disk"""
        if config:
            self._config = config
        
        # Create backup before saving
        self._create_backup()
        
        try:
            # Convert to dict and save
            data = self._config.to_dict()
            
            with open(self.config_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
                
        except Exception as e:
            # Restore from backup on failure
            self._restore_latest_backup()
            raise ValueError(f"Error saving configuration: {e}")
    
    def get(self, key: str, profile: Optional[str] = None) -> Any:
        """Get configuration value with dot notation support"""
        # Use specified profile or active profile
        profile_name = profile or self._config.active_profile
        
        if profile_name not in self._config.profiles:
            raise ValueError(f"Profile '{profile_name}' does not exist")
        
        profile_config = self._config.profiles[profile_name]
        
        # Navigate dot notation
        parts = key.split('.')
        value = profile_config.dict()
        
        try:
            for part in parts:
                if isinstance(value, dict):
                    value = value[part]
                else:
                    raise KeyError(f"Cannot access '{part}' in non-dict value")
            return value
        except KeyError:
            raise KeyError(f"Configuration key '{key}' not found")
    
    def set(self, key: str, value: Any, profile: Optional[str] = None) -> None:
        """Set configuration value with validation"""
        # Use specified profile or active profile
        profile_name = profile or self._config.active_profile
        
        if profile_name not in self._config.profiles:
            raise ValueError(f"Profile '{profile_name}' does not exist")
        
        # Get profile dict
        profile_dict = self._config.profiles[profile_name].dict()
        
        # Navigate to parent and set value
        parts = key.split('.')
        current = profile_dict
        
        # Navigate to parent
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value
        final_key = parts[-1]
        current[final_key] = self._parse_value(value)
        
        # Recreate profile with validation
        try:
            new_profile = ProfileConfig(**profile_dict)
            self._config.profiles[profile_name] = new_profile
            self.save()
        except Exception as e:
            raise ValueError(f"Invalid configuration value: {e}")
    
    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type"""
        # Try to parse as boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Try to parse as list
        if value.startswith('[') and value.endswith(']'):
            items = value[1:-1].split(',')
            return [item.strip() for item in items if item.strip()]
        
        # Return as string
        return value
    
    def reset(self, key: Optional[str] = None, profile: Optional[str] = None) -> None:
        """Reset configuration to defaults"""
        if key:
            # Reset specific key
            # TODO: Implement partial reset from defaults
            raise NotImplementedError("Partial reset not yet implemented")
        else:
            # Reset entire profile or all configuration
            if profile:
                if profile == "default":
                    self._config.profiles[profile] = ProfileConfig()
                else:
                    # Remove non-default profile
                    if profile in self._config.profiles:
                        del self._config.profiles[profile]
                        if self._config.active_profile == profile:
                            self._config.active_profile = "default"
            else:
                # Reset all configuration
                self._config = ConfigSchema()
            
            self.save()
    
    def validate(self, config: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        try:
            if config:
                ConfigSchema.from_dict(config)
            else:
                # Validate current config by recreating it
                ConfigSchema.from_dict(self._config.to_dict())
        except Exception as e:
            errors.append(str(e))
        
        return errors
    
    def get_profile_names(self) -> List[str]:
        """Get list of available profile names"""
        return list(self._config.profiles.keys())
    
    def get_active_profile(self) -> str:
        """Get active profile name"""
        return self._config.active_profile
    
    def set_active_profile(self, profile_name: str) -> None:
        """Set active profile"""
        if profile_name not in self._config.profiles:
            raise ValueError(f"Profile '{profile_name}' does not exist")
        
        self._config.active_profile = profile_name
        self.save()
    
    def export_config(self, path: Optional[Path] = None) -> Path:
        """Export configuration to file"""
        if not path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = Path(f"leanvibe_config_{timestamp}.yml")
        
        # Save current config to specified path
        data = self._config.to_dict()
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        return path
    
    def import_config(self, path: Path, merge: bool = False) -> None:
        """Import configuration from file"""
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Validate imported config
            imported_config = ConfigSchema.from_dict(data)
            
            if merge:
                # Merge profiles from imported config
                for name, profile in imported_config.profiles.items():
                    if name not in self._config.profiles:
                        self._config.profiles[name] = profile
            else:
                # Replace entire config
                self._config = imported_config
            
            self.save()
            
        except Exception as e:
            raise ValueError(f"Error importing configuration: {e}")
    
    def _create_backup(self) -> None:
        """Create backup of current configuration"""
        if self.config_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"config_{timestamp}.yml"
            shutil.copy(self.config_file, backup_file)
            
            # Keep only last 10 backups
            self._cleanup_old_backups(keep=10)
    
    def _restore_latest_backup(self) -> None:
        """Restore from latest backup"""
        backups = sorted(self.backup_dir.glob("config_*.yml"), reverse=True)
        if backups:
            shutil.copy(backups[0], self.config_file)
    
    def _cleanup_old_backups(self, keep: int = 10) -> None:
        """Remove old backup files"""
        backups = sorted(self.backup_dir.glob("config_*.yml"), reverse=True)
        for backup in backups[keep:]:
            backup.unlink()
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration metadata"""
        return {
            "config_file": str(self.config_file),
            "exists": self.config_file.exists(),
            "active_profile": self._config.active_profile,
            "profiles": self.get_profile_names(),
            "version": self._config.version,
            "backups": len(list(self.backup_dir.glob("config_*.yml")))
        }