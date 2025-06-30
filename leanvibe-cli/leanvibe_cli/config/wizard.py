"""
Interactive configuration wizard for LeanVibe CLI

Provides a guided setup experience for configuring the CLI.
"""

from typing import Dict, Any, Optional, List
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table

from .schema import ConfigSchema, ProfileConfig
from .manager import ConfigurationManager


console = Console()


class ConfigurationWizard:
    """Interactive configuration wizard"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.config = {}
        
    def run(self, profile_name: Optional[str] = None) -> bool:
        """Run interactive configuration wizard"""
        console.clear()
        self._show_welcome()
        
        # Determine if we're creating new or editing
        if profile_name and profile_name in self.config_manager._config.profiles:
            self.config = self.config_manager._config.profiles[profile_name].dict()
            mode = "edit"
        else:
            self.config = ProfileConfig().dict()
            mode = "create"
            if not profile_name:
                profile_name = self._prompt_profile_name()
        
        try:
            # Step 1: Backend connection
            if self._configure_backend():
                console.print("[green]✓[/green] Backend configuration complete")
            
            # Step 2: Notification preferences
            if self._configure_notifications():
                console.print("[green]✓[/green] Notification configuration complete")
            
            # Step 3: File filtering
            if self._configure_file_filters():
                console.print("[green]✓[/green] File filter configuration complete")
            
            # Step 4: Display settings
            if self._configure_display():
                console.print("[green]✓[/green] Display configuration complete")
            
            # Step 5: Performance settings
            if self._configure_performance():
                console.print("[green]✓[/green] Performance configuration complete")
            
            # Step 6: Review and save
            if self._review_and_save(profile_name, mode):
                return True
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Configuration wizard cancelled[/yellow]")
            return False
        
        return False
    
    def _show_welcome(self):
        """Show welcome message"""
        welcome_text = Text()
        welcome_text.append("Welcome to LeanVibe CLI Configuration Wizard\n", style="bold cyan")
        welcome_text.append("This wizard will help you configure your LeanVibe CLI settings.\n")
        welcome_text.append("You can press Ctrl+C at any time to cancel.")
        
        panel = Panel(
            welcome_text,
            title="[bold]Configuration Wizard[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(panel)
        console.print()
    
    def _prompt_profile_name(self) -> str:
        """Prompt for profile name"""
        console.print("[bold cyan]Profile Setup[/bold cyan]")
        console.print("Enter a name for this configuration profile.")
        console.print("Existing profiles:", ", ".join(self.config_manager.get_profile_names()))
        
        while True:
            name = Prompt.ask("Profile name", default="custom")
            
            if name in self.config_manager.get_profile_names():
                if Confirm.ask(f"Profile '{name}' exists. Overwrite?"):
                    return name
            else:
                return name
    
    def _configure_backend(self) -> bool:
        """Configure backend connection"""
        console.print("\n[bold cyan]Backend Configuration[/bold cyan]")
        console.print("Configure the connection to your LeanVibe backend.")
        
        # Backend URL
        current_url = self.config.get('backend_url', 'http://localhost:8000')
        url = Prompt.ask(
            "Backend URL",
            default=current_url,
            show_default=True
        )
        self.config['backend_url'] = url.rstrip('/')
        
        # API timeout
        current_timeout = self.config.get('api_timeout', 30)
        timeout = IntPrompt.ask(
            "API timeout (seconds)",
            default=current_timeout,
            show_default=True
        )
        self.config['api_timeout'] = max(5, min(300, timeout))
        
        # WebSocket timeout
        current_ws_timeout = self.config.get('websocket_timeout', 300)
        ws_timeout = IntPrompt.ask(
            "WebSocket timeout (seconds)",
            default=current_ws_timeout,
            show_default=True
        )
        self.config['websocket_timeout'] = max(30, min(3600, ws_timeout))
        
        return True
    
    def _configure_notifications(self) -> bool:
        """Configure notification settings"""
        console.print("\n[bold cyan]Notification Configuration[/bold cyan]")
        console.print("Configure how you want to receive notifications.")
        
        if 'notifications' not in self.config:
            self.config['notifications'] = {}
        
        notif = self.config['notifications']
        
        # Global toggles
        notif['enabled'] = Confirm.ask(
            "Enable notifications",
            default=notif.get('enabled', True)
        )
        
        if notif['enabled']:
            notif['desktop_enabled'] = Confirm.ask(
                "Enable desktop notifications",
                default=notif.get('desktop_enabled', True)
            )
            
            notif['terminal_enabled'] = Confirm.ask(
                "Enable terminal notifications",
                default=notif.get('terminal_enabled', True)
            )
            
            notif['sound_enabled'] = Confirm.ask(
                "Enable notification sounds",
                default=notif.get('sound_enabled', False)
            )
            
            # Priority level
            console.print("\nMinimum notification priority:")
            priorities = ["debug", "low", "medium", "high", "critical"]
            for i, p in enumerate(priorities):
                console.print(f"  {i+1}. {p}")
            
            current_priority = notif.get('minimum_priority', 'medium')
            default_index = priorities.index(current_priority) + 1
            
            choice = IntPrompt.ask(
                "Choose priority level",
                default=default_index,
                choices=[str(i) for i in range(1, 6)]
            )
            notif['minimum_priority'] = priorities[choice - 1]
            
            # Rate limiting
            notif['throttle_seconds'] = IntPrompt.ask(
                "Notification throttle (seconds)",
                default=notif.get('throttle_seconds', 30)
            )
            
            notif['max_per_minute'] = IntPrompt.ask(
                "Maximum notifications per minute",
                default=notif.get('max_per_minute', 10)
            )
            
            # Event types
            self._configure_event_types(notif)
            
            # Desktop settings
            if notif.get('desktop_enabled'):
                self._configure_desktop_settings(notif)
            
            # Terminal settings
            if notif.get('terminal_enabled'):
                self._configure_terminal_settings(notif)
        
        return True
    
    def _configure_event_types(self, notif: Dict[str, Any]):
        """Configure enabled event types"""
        console.print("\nSelect event types to receive notifications for:")
        
        all_events = [
            "code_quality_issue",
            "architectural_violation",
            "security_vulnerability",
            "performance_regression",
            "test_failure",
            "build_failure",
            "file_change",
            "session_update",
            "heartbeat",
            "debug_trace",
            "connection_status"
        ]
        
        current_enabled = set(notif.get('enabled_events', []))
        
        # Show table of events
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Event Type", style="white")
        table.add_column("Enabled", style="green")
        
        for i, event in enumerate(all_events):
            enabled = "✓" if event in current_enabled else "✗"
            table.add_row(str(i+1), event, enabled)
        
        console.print(table)
        
        # Quick options
        console.print("\nQuick options:")
        console.print("  a - Enable all")
        console.print("  n - Disable all")
        console.print("  d - Use defaults")
        console.print("  1-11 - Toggle individual events")
        console.print("  Enter - Keep current settings")
        
        while True:
            choice = Prompt.ask("Your choice", default="")
            
            if choice == "":
                break
            elif choice == "a":
                current_enabled = set(all_events)
            elif choice == "n":
                current_enabled = set()
            elif choice == "d":
                current_enabled = set([
                    "code_quality_issue",
                    "architectural_violation",
                    "security_vulnerability",
                    "performance_regression",
                    "test_failure",
                    "build_failure",
                    "file_change",
                    "session_update"
                ])
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(all_events):
                    event = all_events[idx]
                    if event in current_enabled:
                        current_enabled.remove(event)
                    else:
                        current_enabled.add(event)
            
            # Refresh table
            console.clear()
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=3)
            table.add_column("Event Type", style="white")
            table.add_column("Enabled", style="green")
            
            for i, event in enumerate(all_events):
                enabled = "✓" if event in current_enabled else "✗"
                table.add_row(str(i+1), event, enabled)
            
            console.print(table)
        
        notif['enabled_events'] = list(current_enabled)
        notif['disabled_events'] = [e for e in all_events if e not in current_enabled]
    
    def _configure_desktop_settings(self, notif: Dict[str, Any]):
        """Configure desktop notification settings"""
        if 'desktop' not in notif:
            notif['desktop'] = {}
        
        desktop = notif['desktop']
        
        desktop['timeout_seconds'] = IntPrompt.ask(
            "Desktop notification timeout (seconds)",
            default=desktop.get('timeout_seconds', 5)
        )
        
        desktop['critical_sound'] = Confirm.ask(
            "Play sound for critical notifications",
            default=desktop.get('critical_sound', True)
        )
        
        desktop['high_sound'] = Confirm.ask(
            "Play sound for high priority notifications",
            default=desktop.get('high_sound', False)
        )
    
    def _configure_terminal_settings(self, notif: Dict[str, Any]):
        """Configure terminal notification settings"""
        if 'terminal' not in notif:
            notif['terminal'] = {}
        
        terminal = notif['terminal']
        
        terminal['max_overlay_items'] = IntPrompt.ask(
            "Maximum overlay notifications",
            default=terminal.get('max_overlay_items', 5)
        )
        
        terminal['overlay_duration'] = IntPrompt.ask(
            "Overlay duration (seconds)",
            default=terminal.get('overlay_duration', 3)
        )
        
        terminal['show_timestamp'] = Confirm.ask(
            "Show timestamps",
            default=terminal.get('show_timestamp', True)
        )
        
        terminal['show_source'] = Confirm.ask(
            "Show notification source",
            default=terminal.get('show_source', True)
        )
    
    def _configure_file_filters(self) -> bool:
        """Configure file filtering"""
        console.print("\n[bold cyan]File Filter Configuration[/bold cyan]")
        console.print("Configure which files to monitor or exclude.")
        
        if 'file_filters' not in self.config:
            self.config['file_filters'] = {}
        
        filters = self.config['file_filters']
        
        # Show current exclude patterns
        current_excludes = filters.get('exclude_patterns', [])
        if current_excludes:
            console.print("\nCurrent exclude patterns:")
            for pattern in current_excludes:
                console.print(f"  • {pattern}")
        
        if Confirm.ask("Modify exclude patterns", default=False):
            console.print("Enter patterns to exclude (one per line, empty line to finish):")
            new_excludes = []
            while True:
                pattern = Prompt.ask("Pattern", default="")
                if not pattern:
                    break
                new_excludes.append(pattern)
            
            if new_excludes:
                filters['exclude_patterns'] = new_excludes
        
        # Include only patterns
        if Confirm.ask("Set include-only patterns", default=False):
            console.print("Enter patterns to include (one per line, empty line to finish):")
            includes = []
            while True:
                pattern = Prompt.ask("Pattern", default="")
                if not pattern:
                    break
                includes.append(pattern)
            
            filters['include_only_patterns'] = includes
        
        return True
    
    def _configure_display(self) -> bool:
        """Configure display settings"""
        console.print("\n[bold cyan]Display Configuration[/bold cyan]")
        
        if 'display' not in self.config:
            self.config['display'] = {}
        
        display = self.config['display']
        
        # Theme
        themes = ["dark", "light", "auto"]
        current_theme = display.get('theme', 'dark')
        console.print("Theme options: " + ", ".join(themes))
        theme = Prompt.ask(
            "Theme",
            default=current_theme,
            choices=themes
        )
        display['theme'] = theme
        
        # Other display settings
        display['verbose'] = Confirm.ask(
            "Enable verbose output",
            default=display.get('verbose', False)
        )
        
        display['show_progress'] = Confirm.ask(
            "Show progress indicators",
            default=display.get('show_progress', True)
        )
        
        display['color_output'] = Confirm.ask(
            "Enable colored output",
            default=display.get('color_output', True)
        )
        
        # Timestamp format
        formats = ["relative", "absolute", "iso"]
        current_format = display.get('timestamp_format', 'relative')
        console.print("Timestamp formats: " + ", ".join(formats))
        timestamp_format = Prompt.ask(
            "Timestamp format",
            default=current_format,
            choices=formats
        )
        display['timestamp_format'] = timestamp_format
        
        return True
    
    def _configure_performance(self) -> bool:
        """Configure performance settings"""
        console.print("\n[bold cyan]Performance Configuration[/bold cyan]")
        
        if 'performance' not in self.config:
            self.config['performance'] = {}
        
        perf = self.config['performance']
        
        perf['cache_enabled'] = Confirm.ask(
            "Enable caching",
            default=perf.get('cache_enabled', True)
        )
        
        if perf['cache_enabled']:
            perf['cache_ttl_seconds'] = IntPrompt.ask(
                "Cache TTL (seconds)",
                default=perf.get('cache_ttl_seconds', 300)
            )
        
        perf['parallel_connections'] = IntPrompt.ask(
            "Parallel connections",
            default=perf.get('parallel_connections', 5)
        )
        
        perf['batch_size'] = IntPrompt.ask(
            "Batch size",
            default=perf.get('batch_size', 100)
        )
        
        return True
    
    def _review_and_save(self, profile_name: str, mode: str) -> bool:
        """Review configuration and save"""
        console.print("\n[bold cyan]Configuration Review[/bold cyan]")
        
        # Create a summary table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Setting", style="white")
        table.add_column("Value", style="green")
        
        # Backend settings
        table.add_row("Backend URL", self.config['backend_url'])
        table.add_row("API Timeout", f"{self.config['api_timeout']}s")
        
        # Notification settings
        notif = self.config.get('notifications', {})
        table.add_row("Notifications", "Enabled" if notif.get('enabled') else "Disabled")
        if notif.get('enabled'):
            table.add_row("Minimum Priority", notif.get('minimum_priority', 'medium'))
            table.add_row("Desktop Notifications", "Yes" if notif.get('desktop_enabled') else "No")
            table.add_row("Terminal Notifications", "Yes" if notif.get('terminal_enabled') else "No")
        
        # Display settings
        display = self.config.get('display', {})
        table.add_row("Theme", display.get('theme', 'dark'))
        table.add_row("Verbose Mode", "Yes" if display.get('verbose') else "No")
        
        console.print(table)
        
        # Confirm save
        if Confirm.ask(f"\n{mode.capitalize()} profile '{profile_name}'?", default=True):
            try:
                # Create ProfileConfig from our dict
                profile_config = ProfileConfig(**self.config)
                
                # Save to configuration
                if mode == "create" or profile_name not in self.config_manager._config.profiles:
                    self.config_manager._config.profiles[profile_name] = profile_config
                else:
                    # Update existing
                    self.config_manager._config.profiles[profile_name] = profile_config
                
                self.config_manager.save()
                
                # Ask if should make active
                if profile_name != self.config_manager.get_active_profile():
                    if Confirm.ask(f"Make '{profile_name}' the active profile?", default=True):
                        self.config_manager.set_active_profile(profile_name)
                
                console.print(f"\n[green]✓ Configuration saved to profile '{profile_name}'[/green]")
                return True
                
            except Exception as e:
                console.print(f"[red]Error saving configuration: {e}[/red]")
                return False
        
        return False