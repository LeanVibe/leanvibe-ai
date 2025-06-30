# Task 2.3.4: Notification Configuration Management Plan

## Overview
Add comprehensive notification configuration management to the LeanVibe CLI, allowing users to configure, persist, and manage notification settings through dedicated CLI commands.

## Goals
1. Create a `config` command group for notification settings management
2. Implement persistent configuration storage (YAML format)
3. Add validation for configuration values
4. Provide interactive configuration wizard
5. Support configuration profiles for different environments

## Detailed Implementation Plan

### 1. Configuration Command Structure
```bash
leanvibe config                          # Show current configuration
leanvibe config set KEY VALUE            # Set a configuration value
leanvibe config get KEY                  # Get a specific configuration value
leanvibe config reset [KEY]              # Reset to defaults (all or specific)
leanvibe config wizard                   # Interactive configuration wizard
leanvibe config profile list             # List available profiles
leanvibe config profile create NAME      # Create a new profile
leanvibe config profile switch NAME      # Switch to a profile
leanvibe config profile delete NAME      # Delete a profile
leanvibe config export [--file PATH]     # Export configuration
leanvibe config import [--file PATH]     # Import configuration
```

### 2. Configuration Schema

#### Core Settings
```yaml
# ~/.leanvibe/config.yml
version: "1.0"
active_profile: "default"

profiles:
  default:
    # Connection settings
    backend_url: "http://localhost:8000"
    api_timeout: 30
    websocket_timeout: 300
    
    # Notification settings
    notifications:
      # Global toggles
      enabled: true
      desktop_enabled: true
      terminal_enabled: true
      sound_enabled: false
      
      # Priority filtering
      minimum_priority: "medium"  # debug, low, medium, high, critical
      
      # Rate limiting
      throttle_seconds: 30
      max_per_minute: 10
      
      # Event type filtering
      enabled_events:
        - code_quality_issue
        - architectural_violation
        - security_vulnerability
        - performance_regression
        - test_failure
        - build_failure
      
      disabled_events:
        - heartbeat
        - debug_trace
      
      # Desktop notification settings
      desktop:
        timeout_seconds: 5
        critical_sound: true
        high_sound: false
        position: "top-right"  # top-left, top-right, bottom-left, bottom-right
        
      # Terminal notification settings
      terminal:
        max_overlay_items: 5
        overlay_duration: 3
        show_timestamp: true
        show_source: true
        
    # File filtering
    file_filters:
      exclude_patterns:
        - "*.pyc"
        - "__pycache__/*"
        - ".git/*"
        - "node_modules/*"
        - ".venv/*"
        - "*.log"
      
      include_only_patterns: []  # If set, only these patterns are monitored
      
    # Display settings
    display:
      theme: "dark"  # dark, light, auto
      verbose: false
      show_progress: true
      timestamp_format: "relative"  # relative, absolute, iso
      
    # Performance settings
    performance:
      cache_enabled: true
      cache_ttl_seconds: 300
      parallel_connections: 5
      batch_size: 100

  # Additional profiles
  production:
    backend_url: "https://api.leanvibe.com"
    notifications:
      minimum_priority: "high"
      desktop_enabled: true
      sound_enabled: true
      
  quiet:
    notifications:
      enabled: false
      desktop_enabled: false
      terminal_enabled: false
```

### 3. File Structure

```
leanvibe_cli/
├── commands/
│   └── config.py                    # New: Config command group
├── config/
│   ├── __init__.py
│   ├── manager.py                   # Configuration manager
│   ├── schema.py                    # Configuration schema and validation
│   ├── profiles.py                  # Profile management
│   └── wizard.py                    # Interactive configuration wizard
├── utils/
│   └── yaml_helpers.py              # YAML serialization helpers
└── templates/
    └── default_config.yml           # Default configuration template
```

### 4. Implementation Components

#### 4.1 Configuration Manager (`config/manager.py`)
```python
class ConfigurationManager:
    """Manages LeanVibe CLI configuration with profiles and validation"""
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path.home() / ".leanvibe"
        self.config_file = self.config_dir / "config.yml"
        self.config_data: Dict[str, Any] = {}
        self.active_profile: str = "default"
        
    def load(self) -> Dict[str, Any]:
        """Load configuration from disk"""
        
    def save(self) -> None:
        """Save configuration to disk"""
        
    def get(self, key: str, profile: Optional[str] = None) -> Any:
        """Get configuration value with dot notation support"""
        
    def set(self, key: str, value: Any, profile: Optional[str] = None) -> None:
        """Set configuration value with validation"""
        
    def reset(self, key: Optional[str] = None) -> None:
        """Reset configuration to defaults"""
        
    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration against schema"""
        
    def merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with defaults"""
```

#### 4.2 Configuration Schema (`config/schema.py`)
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal

class NotificationSettings(BaseModel):
    enabled: bool = True
    desktop_enabled: bool = True
    terminal_enabled: bool = True
    sound_enabled: bool = False
    minimum_priority: Literal["debug", "low", "medium", "high", "critical"] = "medium"
    throttle_seconds: int = Field(30, ge=0, le=300)
    max_per_minute: int = Field(10, ge=1, le=100)
    enabled_events: List[str] = Field(default_factory=list)
    disabled_events: List[str] = Field(default_factory=list)

class ConfigSchema(BaseModel):
    """Complete configuration schema with validation"""
    version: str = "1.0"
    backend_url: str = "http://localhost:8000"
    notifications: NotificationSettings
    # ... other settings
    
    @validator('backend_url')
    def validate_url(cls, v):
        # URL validation logic
        return v
```

#### 4.3 Profile Manager (`config/profiles.py`)
```python
class ProfileManager:
    """Manages configuration profiles"""
    
    def list_profiles(self) -> List[str]:
        """List available profiles"""
        
    def create_profile(self, name: str, base_profile: str = "default") -> None:
        """Create new profile based on existing one"""
        
    def switch_profile(self, name: str) -> None:
        """Switch active profile"""
        
    def delete_profile(self, name: str) -> None:
        """Delete a profile (cannot delete default)"""
        
    def export_profile(self, name: str, path: Path) -> None:
        """Export profile to file"""
        
    def import_profile(self, path: Path, name: Optional[str] = None) -> None:
        """Import profile from file"""
```

#### 4.4 Configuration Wizard (`config/wizard.py`)
```python
class ConfigurationWizard:
    """Interactive configuration wizard"""
    
    def run(self) -> Dict[str, Any]:
        """Run interactive configuration wizard"""
        # Steps:
        # 1. Backend connection
        # 2. Notification preferences
        # 3. Priority and filtering
        # 4. Performance settings
        # 5. Review and save
```

#### 4.5 Config Commands (`commands/config.py`)
```python
@click.group()
@click.pass_context
def config(ctx):
    """Manage LeanVibe CLI configuration"""
    ctx.ensure_object(dict)
    ctx.obj['config_manager'] = ConfigurationManager()

@config.command()
@click.pass_context
def show(ctx):
    """Show current configuration"""
    # Display formatted configuration with highlighting

@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--profile', '-p', help='Target profile')
@click.pass_context
def set(ctx, key, value, profile):
    """Set a configuration value"""
    # Set with validation and feedback

@config.command()
@click.pass_context
def wizard(ctx):
    """Run interactive configuration wizard"""
    # Launch configuration wizard

# ... other commands
```

### 5. Integration Points

#### 5.1 Update CLIConfig class
- Add method to load from ConfigurationManager
- Support profile-based configuration
- Maintain backward compatibility

#### 5.2 Update existing commands
- Use ConfigurationManager for all config access
- Support --profile option globally
- Respect configuration precedence (CLI args > env vars > config file)

#### 5.3 Configuration precedence
1. Command-line arguments (highest priority)
2. Environment variables (LEANVIBE_*)
3. Profile-specific configuration
4. Default profile configuration
5. Built-in defaults (lowest priority)

### 6. User Experience Features

#### 6.1 Smart Defaults
- Detect common environments (Docker, CI/CD)
- Auto-suggest optimal settings based on system
- Provide templates for common use cases

#### 6.2 Validation and Feedback
- Real-time validation during `config set`
- Clear error messages with suggestions
- Dry-run mode for testing changes

#### 6.3 Migration Support
- Automatic migration from old config formats
- Backup before major changes
- Rollback capability

### 7. Testing Strategy

#### 7.1 Unit Tests
- Configuration loading/saving
- Validation logic
- Profile management
- Value merging and precedence

#### 7.2 Integration Tests
- Command execution
- File system operations
- Migration scenarios
- Error handling

#### 7.3 User Acceptance Tests
- Configuration wizard flow
- Common configuration scenarios
- Error recovery
- Performance with large configs

### 8. Documentation

#### 8.1 Command Help
- Comprehensive help for each subcommand
- Examples for common use cases
- Configuration key reference

#### 8.2 Configuration Guide
- Complete key reference
- Best practices
- Troubleshooting guide
- Migration guide

### 9. Implementation Steps

1. **Create config package structure** (30 min)
   - Create directories and __init__.py files
   - Set up basic imports

2. **Implement ConfigurationManager** (2 hours)
   - YAML loading/saving
   - Dot notation access
   - Validation framework
   - Default merging

3. **Implement Configuration Schema** (1 hour)
   - Pydantic models
   - Validation rules
   - Default values

4. **Implement ProfileManager** (1 hour)
   - Profile CRUD operations
   - Profile switching
   - Import/export

5. **Create config command group** (2 hours)
   - All subcommands
   - Options and arguments
   - Output formatting

6. **Implement Configuration Wizard** (1.5 hours)
   - Interactive prompts
   - Validation during input
   - Preview and confirmation

7. **Integration with existing code** (1 hour)
   - Update CLIConfig
   - Update existing commands
   - Test backward compatibility

8. **Testing** (2 hours)
   - Unit tests
   - Integration tests
   - Manual testing

9. **Documentation** (30 min)
   - Update command help
   - Add examples
   - Update README

**Total estimated time: 11.5 hours**

### 10. Success Criteria

✅ All config commands work as specified
✅ Configuration persists between sessions
✅ Validation prevents invalid configurations
✅ Profiles can be created, switched, and deleted
✅ Wizard provides smooth configuration experience
✅ Backward compatibility maintained
✅ All tests pass
✅ Documentation is complete and clear

### 11. Risk Mitigation

**Risk**: Breaking existing configurations
**Mitigation**: Automatic backup, migration support, rollback capability

**Risk**: Complex configuration schema
**Mitigation**: Smart defaults, wizard mode, clear documentation

**Risk**: Performance impact
**Mitigation**: Lazy loading, caching, minimal file I/O

### 12. Future Enhancements

- Cloud sync for configurations
- Team sharing capabilities
- Configuration templates marketplace
- Auto-tuning based on usage patterns
- Integration with IDE settings