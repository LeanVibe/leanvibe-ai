"""
Configuration management for LeenVibe CLI

Handles YAML configuration files, environment detection, and user preferences.
"""

import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any, List

import yaml
from rich.console import Console

console = Console()


@dataclass
class CLIConfig:
    """Configuration settings for LeenVibe CLI"""
    
    # Backend connection
    backend_url: str = "http://localhost:8000"
    websocket_url: str = "ws://localhost:8000/ws"
    timeout_seconds: int = 30
    api_timeout: int = 30  # Alias for timeout_seconds
    websocket_timeout: int = 300
    
    # User preferences
    verbose: bool = False
    auto_detect_project: bool = True
    show_notifications: bool = True
    notification_level: str = "medium"  # debug, low, medium, high, critical
    
    # Notification settings
    desktop_notifications: bool = True
    terminal_notifications: bool = True
    sound_notifications: bool = False
    notification_throttle_seconds: int = 30
    max_notifications_per_minute: int = 10
    
    # Notification filtering
    enabled_event_types: List[str] = None
    
    # Display settings
    max_lines_output: int = 50
    syntax_highlighting: bool = True
    show_timestamps: bool = True
    compact_mode: bool = False
    show_progress: bool = True  # Added for compatibility
    
    # Project settings
    project_root: Optional[str] = None
    exclude_patterns: List[str] = None
    
    def __post_init__(self):
        """Initialize default values after creation"""
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "*.pyc", "*.pyo", "__pycache__", ".git", ".svn",
                "node_modules", ".DS_Store", "*.log", ".env"
            ]
        
        if self.enabled_event_types is None:
            self.enabled_event_types = [
                "architectural_violation",
                "build_failure",
                "security_issue",
                "complexity_spike", 
                "circular_dependency",
                "test_failure",
                "performance_regression"
            ]
        
        # Derive WebSocket URL from backend URL if not explicitly set
        if self.websocket_url == "ws://localhost:8000/ws" and self.backend_url != "http://localhost:8000":
            self.websocket_url = self.backend_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CLIConfig':
        """Create config from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def get_config_path(config_path: Optional[str] = None) -> Path:
    """Get the configuration file path"""
    if config_path:
        return Path(config_path)
    
    # Try project-specific config first
    project_config = Path.cwd() / ".leenvibe" / "cli-config.yaml"
    if project_config.exists():
        return project_config
    
    # Fall back to user config
    home_config = Path.home() / ".leenvibe" / "cli-config.yaml"
    return home_config


def load_config(config_path: Optional[str] = None) -> CLIConfig:
    """Load configuration from file or create default"""
    
    # Try to use new configuration manager first
    try:
        from .config.manager import ConfigurationManager
        manager = ConfigurationManager()
        schema = manager._config
        
        # Create CLIConfig from active profile
        config = CLIConfig()
        schema.merge_with_cli_config(config)
        
        if config_path:
            console.print(f"[dim]Loaded configuration from profile: {schema.active_profile}[/dim]")
        
        return config
        
    except Exception:
        # Fall back to legacy config loading
        pass
    
    # Legacy configuration loading
    config_file = get_config_path(config_path)
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            return CLIConfig.from_dict(data)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load config from {config_file}: {e}[/yellow]")
            console.print("[yellow]Using default configuration[/yellow]")
    
    # Return default config
    config = CLIConfig()
    
    # Auto-detect backend if running in development
    config.backend_url = detect_backend_url()
    
    return config


def save_config(config: CLIConfig, config_path: Optional[str] = None) -> bool:
    """Save configuration to file"""
    config_file = get_config_path(config_path)
    
    try:
        # Ensure directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=True)
        
        return True
    except Exception as e:
        console.print(f"[red]Error saving config to {config_file}: {e}[/red]")
        return False


def detect_backend_url() -> str:
    """Auto-detect backend URL based on environment"""
    
    # Check environment variable
    env_url = os.getenv('LEENVIBE_BACKEND_URL')
    if env_url:
        return env_url
    
    # Check if we're in the development directory
    current_path = Path.cwd()
    
    # Look for backend directory indicators
    backend_indicators = [
        "leenvibe-backend",
        "app/main.py",
        "pyproject.toml"  # If it mentions leenvibe-backend
    ]
    
    # Search up the directory tree
    for parent in [current_path] + list(current_path.parents):
        for indicator in backend_indicators:
            if (parent / indicator).exists():
                # Found development environment, try local URL
                return "http://localhost:8000"
    
    # Default to local development server
    return "http://localhost:8000"


def detect_project_root() -> Optional[str]:
    """Detect project root by looking for common indicators"""
    current_path = Path.cwd()
    
    # Project indicators in order of preference
    indicators = [
        ".leenvibe",      # LeenVibe project
        ".git",           # Git repository
        "pyproject.toml", # Python project
        "package.json",   # Node.js project
        "Cargo.toml",     # Rust project
        "go.mod",         # Go project
        ".project",       # General project marker
    ]
    
    # Search up the directory tree
    for parent in [current_path] + list(current_path.parents):
        for indicator in indicators:
            if (parent / indicator).exists():
                return str(parent)
    
    # If no indicators found, use current directory
    return str(current_path)


def init_config(force: bool = False) -> bool:
    """Initialize configuration with interactive setup"""
    config_file = get_config_path()
    
    if config_file.exists() and not force:
        console.print(f"[yellow]Configuration already exists at {config_file}[/yellow]")
        console.print("[yellow]Use --force to overwrite[/yellow]")
        return False
    
    console.print("[bold cyan]LeenVibe CLI Configuration Setup[/bold cyan]\n")
    
    # Get backend URL
    default_url = detect_backend_url()
    backend_url = input(f"Backend URL [{default_url}]: ").strip() or default_url
    
    # Get notification preferences
    notification_levels = ["debug", "low", "medium", "high", "critical"]
    console.print(f"Notification levels: {', '.join(notification_levels)}")
    notification_level = input("Notification level [medium]: ").strip() or "medium"
    
    if notification_level not in notification_levels:
        notification_level = "medium"
    
    # Create configuration
    config = CLIConfig(
        backend_url=backend_url,
        notification_level=notification_level,
        project_root=detect_project_root()
    )
    
    # Save configuration
    if save_config(config):
        console.print(f"[green]Configuration saved to {config_file}[/green]")
        return True
    else:
        console.print("[red]Failed to save configuration[/red]")
        return False