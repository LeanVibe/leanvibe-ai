"""
Configuration management package for LeenVibe CLI

Provides comprehensive configuration management with profiles, validation,
and interactive configuration wizard.
"""

from .manager import ConfigurationManager
from .schema import ConfigSchema, NotificationSettings, DesktopSettings, TerminalSettings
from .profiles import ProfileManager
from .legacy import CLIConfig, load_config, save_config

__all__ = [
    "ConfigurationManager",
    "ConfigSchema", 
    "NotificationSettings",
    "DesktopSettings",
    "TerminalSettings",
    "ProfileManager",
    "CLIConfig",
    "load_config",
    "save_config"
]