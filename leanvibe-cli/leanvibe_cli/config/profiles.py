"""
Profile management for LeanVibe CLI configuration

Handles creation, switching, and management of configuration profiles.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml

from .schema import ProfileConfig, ConfigSchema
from .manager import ConfigurationManager


class ProfileManager:
    """Manages configuration profiles"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self._config = config_manager._config
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """List available profiles with metadata"""
        profiles = []
        active = self._config.active_profile
        
        for name, profile in self._config.profiles.items():
            profiles.append({
                "name": name,
                "active": name == active,
                "backend_url": profile.backend_url,
                "notification_level": profile.notifications.minimum_priority,
                "notifications_enabled": profile.notifications.enabled
            })
        
        return profiles
    
    def create_profile(self, name: str, base_profile: Optional[str] = None) -> None:
        """Create new profile based on existing one"""
        if name in self._config.profiles:
            raise ValueError(f"Profile '{name}' already exists")
        
        if base_profile:
            if base_profile not in self._config.profiles:
                raise ValueError(f"Base profile '{base_profile}' does not exist")
            
            # Deep copy the base profile
            base_dict = self._config.profiles[base_profile].dict()
            new_profile = ProfileConfig(**base_dict)
        else:
            # Create default profile
            new_profile = ProfileConfig()
        
        # Add the new profile
        self._config.profiles[name] = new_profile
        self.config_manager.save()
    
    def switch_profile(self, name: str) -> None:
        """Switch active profile"""
        if name not in self._config.profiles:
            raise ValueError(f"Profile '{name}' does not exist")
        
        self._config.active_profile = name
        self.config_manager.save()
    
    def delete_profile(self, name: str) -> None:
        """Delete a profile (cannot delete default or active)"""
        if name == "default":
            raise ValueError("Cannot delete the default profile")
        
        if name == self._config.active_profile:
            raise ValueError(f"Cannot delete active profile '{name}'. Switch to another profile first.")
        
        if name not in self._config.profiles:
            raise ValueError(f"Profile '{name}' does not exist")
        
        del self._config.profiles[name]
        self.config_manager.save()
    
    def rename_profile(self, old_name: str, new_name: str) -> None:
        """Rename a profile"""
        if old_name == "default":
            raise ValueError("Cannot rename the default profile")
        
        if old_name not in self._config.profiles:
            raise ValueError(f"Profile '{old_name}' does not exist")
        
        if new_name in self._config.profiles:
            raise ValueError(f"Profile '{new_name}' already exists")
        
        # Copy profile to new name
        self._config.profiles[new_name] = self._config.profiles[old_name]
        
        # Update active profile if needed
        if self._config.active_profile == old_name:
            self._config.active_profile = new_name
        
        # Delete old profile
        del self._config.profiles[old_name]
        
        self.config_manager.save()
    
    def export_profile(self, name: str, path: Optional[Path] = None) -> Path:
        """Export profile to file"""
        if name not in self._config.profiles:
            raise ValueError(f"Profile '{name}' does not exist")
        
        if not path:
            path = Path(f"leanvibe_profile_{name}.yml")
        
        # Export just the profile
        profile_data = {
            "profile_name": name,
            "profile": self._config.profiles[name].dict()
        }
        
        with open(path, 'w') as f:
            yaml.dump(profile_data, f, default_flow_style=False, sort_keys=False)
        
        return path
    
    def import_profile(self, path: Path, name: Optional[str] = None) -> str:
        """Import profile from file"""
        if not path.exists():
            raise FileNotFoundError(f"Profile file not found: {path}")
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Validate format
            if "profile" not in data:
                raise ValueError("Invalid profile file format")
            
            # Use provided name or name from file
            profile_name = name or data.get("profile_name", path.stem)
            
            # Ensure unique name
            original_name = profile_name
            counter = 1
            while profile_name in self._config.profiles:
                profile_name = f"{original_name}_{counter}"
                counter += 1
            
            # Create and validate profile
            new_profile = ProfileConfig(**data["profile"])
            
            # Add to configuration
            self._config.profiles[profile_name] = new_profile
            self.config_manager.save()
            
            return profile_name
            
        except Exception as e:
            raise ValueError(f"Error importing profile: {e}")
    
    def duplicate_profile(self, source_name: str, target_name: str) -> None:
        """Duplicate an existing profile"""
        self.create_profile(target_name, base_profile=source_name)
    
    def get_profile_details(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a profile"""
        if name not in self._config.profiles:
            raise ValueError(f"Profile '{name}' does not exist")
        
        profile = self._config.profiles[name]
        return {
            "name": name,
            "active": name == self._config.active_profile,
            "configuration": profile.dict()
        }
    
    def compare_profiles(self, profile1: str, profile2: str) -> Dict[str, Any]:
        """Compare two profiles and return differences"""
        if profile1 not in self._config.profiles:
            raise ValueError(f"Profile '{profile1}' does not exist")
        if profile2 not in self._config.profiles:
            raise ValueError(f"Profile '{profile2}' does not exist")
        
        dict1 = self._config.profiles[profile1].dict()
        dict2 = self._config.profiles[profile2].dict()
        
        differences = self._compare_dicts(dict1, dict2)
        return {
            "profile1": profile1,
            "profile2": profile2,
            "differences": differences
        }
    
    def _compare_dicts(self, d1: Dict[str, Any], d2: Dict[str, Any], path: str = "") -> List[Dict[str, Any]]:
        """Recursively compare two dictionaries"""
        differences = []
        
        # Check keys in d1
        for key in d1:
            current_path = f"{path}.{key}" if path else key
            
            if key not in d2:
                differences.append({
                    "path": current_path,
                    "profile1": d1[key],
                    "profile2": None,
                    "type": "missing_in_profile2"
                })
            elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                # Recursive comparison for nested dicts
                differences.extend(self._compare_dicts(d1[key], d2[key], current_path))
            elif d1[key] != d2[key]:
                differences.append({
                    "path": current_path,
                    "profile1": d1[key],
                    "profile2": d2[key],
                    "type": "different"
                })
        
        # Check keys only in d2
        for key in d2:
            if key not in d1:
                current_path = f"{path}.{key}" if path else key
                differences.append({
                    "path": current_path,
                    "profile1": None,
                    "profile2": d2[key],
                    "type": "missing_in_profile1"
                })
        
        return differences