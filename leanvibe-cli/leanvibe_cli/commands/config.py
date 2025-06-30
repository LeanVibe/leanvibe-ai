"""
Configuration management commands for LeanVibe CLI

Provides comprehensive configuration management through CLI commands.
"""

from pathlib import Path
from typing import Optional
import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax

from ..config import ConfigurationManager, ProfileManager
from ..config.wizard import ConfigurationWizard


console = Console()


@click.group()
@click.pass_context
def config(ctx):
    """Manage LeanVibe CLI configuration"""
    ctx.ensure_object(dict)
    config_manager = ConfigurationManager()
    ctx.obj['config_manager'] = config_manager
    ctx.obj['profile_manager'] = ProfileManager(config_manager)


@config.command()
@click.option('--profile', '-p', help='Show specific profile configuration')
@click.option('--format', '-f', type=click.Choice(['table', 'yaml', 'json']), 
              default='table', help='Output format')
@click.pass_context
def show(ctx, profile: Optional[str], format: str):
    """Show current configuration"""
    config_manager = ctx.obj['config_manager']
    
    # Get configuration info
    info = config_manager.get_config_info()
    
    # Show header
    header_text = Text()
    header_text.append("Configuration File: ", style="bold")
    header_text.append(info['config_file'] + "\n", style="dim")
    header_text.append("Active Profile: ", style="bold")
    header_text.append(info['active_profile'], style="green")
    
    console.print(Panel(header_text, title="[bold]LeanVibe Configuration[/bold]", 
                       border_style="cyan"))
    
    # Get profile to display
    profile_name = profile or config_manager.get_active_profile()
    
    if profile_name not in config_manager._config.profiles:
        console.print(f"[red]Profile '{profile_name}' not found[/red]")
        return
    
    profile_config = config_manager._config.profiles[profile_name]
    
    if format == 'yaml':
        # Show as YAML with syntax highlighting
        yaml_str = yaml.dump(profile_config.dict(), default_flow_style=False, sort_keys=False)
        syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
        console.print(syntax)
        
    elif format == 'json':
        # Show as JSON
        import json
        json_str = json.dumps(profile_config.dict(), indent=2)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        console.print(syntax)
        
    else:
        # Show as formatted table
        _show_config_table(profile_config.dict(), profile_name)


def _show_config_table(config: dict, profile_name: str):
    """Display configuration as a formatted table"""
    # Connection settings
    conn_table = Table(show_header=True, header_style="bold cyan", title="Connection Settings")
    conn_table.add_column("Setting", style="white")
    conn_table.add_column("Value", style="green")
    
    conn_table.add_row("Backend URL", config.get('backend_url', ''))
    conn_table.add_row("API Timeout", f"{config.get('api_timeout', 30)}s")
    conn_table.add_row("WebSocket Timeout", f"{config.get('websocket_timeout', 300)}s")
    
    console.print(conn_table)
    console.print()
    
    # Notification settings
    notif = config.get('notifications', {})
    notif_table = Table(show_header=True, header_style="bold cyan", title="Notification Settings")
    notif_table.add_column("Setting", style="white")
    notif_table.add_column("Value", style="green")
    
    notif_table.add_row("Enabled", "✓" if notif.get('enabled', True) else "✗")
    notif_table.add_row("Desktop Notifications", "✓" if notif.get('desktop_enabled', True) else "✗")
    notif_table.add_row("Terminal Notifications", "✓" if notif.get('terminal_enabled', True) else "✗")
    notif_table.add_row("Sound Notifications", "✓" if notif.get('sound_enabled', False) else "✗")
    notif_table.add_row("Minimum Priority", notif.get('minimum_priority', 'medium'))
    notif_table.add_row("Throttle (seconds)", str(notif.get('throttle_seconds', 30)))
    notif_table.add_row("Max per Minute", str(notif.get('max_per_minute', 10)))
    
    console.print(notif_table)
    console.print()
    
    # Display settings
    display = config.get('display', {})
    display_table = Table(show_header=True, header_style="bold cyan", title="Display Settings")
    display_table.add_column("Setting", style="white")
    display_table.add_column("Value", style="green")
    
    display_table.add_row("Theme", display.get('theme', 'dark'))
    display_table.add_row("Verbose", "✓" if display.get('verbose', False) else "✗")
    display_table.add_row("Show Progress", "✓" if display.get('show_progress', True) else "✗")
    display_table.add_row("Color Output", "✓" if display.get('color_output', True) else "✗")
    display_table.add_row("Timestamp Format", display.get('timestamp_format', 'relative'))
    
    console.print(display_table)


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--profile', '-p', help='Target profile (default: active profile)')
@click.pass_context
def set(ctx, key: str, value: str, profile: Optional[str]):
    """Set a configuration value
    
    Examples:
        leanvibe config set backend_url http://localhost:8000
        leanvibe config set notifications.enabled true
        leanvibe config set notifications.minimum_priority high
        leanvibe config set display.theme dark
    """
    config_manager = ctx.obj['config_manager']
    
    try:
        config_manager.set(key, value, profile)
        console.print(f"[green]✓[/green] Set {key} = {value}")
        
        # Show which profile was updated
        target_profile = profile or config_manager.get_active_profile()
        if target_profile != config_manager.get_active_profile():
            console.print(f"[dim]Updated profile: {target_profile}[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Exit(1)


@config.command()
@click.argument('key')
@click.option('--profile', '-p', help='Target profile (default: active profile)')
@click.pass_context
def get(ctx, key: str, profile: Optional[str]):
    """Get a specific configuration value"""
    config_manager = ctx.obj['config_manager']
    
    try:
        value = config_manager.get(key, profile)
        console.print(f"{key} = {value}")
    except KeyError:
        console.print(f"[red]Configuration key '{key}' not found[/red]")
        raise click.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Exit(1)


@config.command()
@click.argument('key', required=False)
@click.option('--profile', '-p', help='Target profile')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
@click.pass_context
def reset(ctx, key: Optional[str], profile: Optional[str], force: bool):
    """Reset configuration to defaults"""
    config_manager = ctx.obj['config_manager']
    
    if key:
        # Reset specific key
        if not force:
            if not click.confirm(f"Reset '{key}' to default value?"):
                return
        
        try:
            config_manager.reset(key, profile)
            console.print(f"[green]✓[/green] Reset {key} to default")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise click.Exit(1)
    else:
        # Reset entire profile or all config
        if profile:
            msg = f"Reset profile '{profile}' to defaults?"
        else:
            msg = "Reset entire configuration to defaults?"
        
        if not force:
            if not click.confirm(msg):
                return
        
        try:
            config_manager.reset(profile=profile)
            console.print("[green]✓[/green] Configuration reset to defaults")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise click.Exit(1)


@config.command()
@click.option('--profile', '-p', help='Profile name to configure')
@click.pass_context
def wizard(ctx, profile: Optional[str]):
    """Run interactive configuration wizard"""
    config_manager = ctx.obj['config_manager']
    wizard = ConfigurationWizard(config_manager)
    
    if wizard.run(profile):
        console.print("\n[green]Configuration wizard completed successfully![/green]")
    else:
        console.print("\n[yellow]Configuration wizard cancelled[/yellow]")


# Profile management commands
@config.group()
def profile():
    """Manage configuration profiles"""
    pass


@profile.command('list')
@click.pass_context
def profile_list(ctx):
    """List available profiles"""
    profile_manager = ctx.obj['profile_manager']
    
    profiles = profile_manager.list_profiles()
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Profile", style="white")
    table.add_column("Active", style="green")
    table.add_column("Backend URL", style="dim")
    table.add_column("Notifications", style="dim")
    
    for profile in profiles:
        active = "✓" if profile['active'] else ""
        notif_status = "On" if profile['notifications_enabled'] else "Off"
        
        table.add_row(
            profile['name'],
            active,
            profile['backend_url'],
            f"{notif_status} ({profile['notification_level']})"
        )
    
    console.print(table)


@profile.command('create')
@click.argument('name')
@click.option('--base', '-b', help='Base profile to copy from')
@click.pass_context
def profile_create(ctx, name: str, base: Optional[str]):
    """Create a new profile"""
    profile_manager = ctx.obj['profile_manager']
    
    try:
        profile_manager.create_profile(name, base)
        console.print(f"[green]✓[/green] Created profile '{name}'")
        
        if base:
            console.print(f"[dim]Based on profile: {base}[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Exit(1)


@profile.command('switch')
@click.argument('name')
@click.pass_context
def profile_switch(ctx, name: str):
    """Switch to a different profile"""
    profile_manager = ctx.obj['profile_manager']
    
    try:
        profile_manager.switch_profile(name)
        console.print(f"[green]✓[/green] Switched to profile '{name}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Exit(1)


@profile.command('delete')
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
@click.pass_context
def profile_delete(ctx, name: str, force: bool):
    """Delete a profile"""
    profile_manager = ctx.obj['profile_manager']
    
    if not force:
        if not click.confirm(f"Delete profile '{name}'?"):
            return
    
    try:
        profile_manager.delete_profile(name)
        console.print(f"[green]✓[/green] Deleted profile '{name}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Exit(1)


@profile.command('export')
@click.argument('name')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def profile_export(ctx, name: str, output: Optional[str]):
    """Export a profile to file"""
    profile_manager = ctx.obj['profile_manager']
    
    try:
        output_path = Path(output) if output else None
        exported_path = profile_manager.export_profile(name, output_path)
        console.print(f"[green]✓[/green] Exported profile '{name}' to {exported_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Exit(1)


@profile.command('import')
@click.argument('file', type=click.Path(exists=True))
@click.option('--name', '-n', help='Profile name (default: from file)')
@click.pass_context
def profile_import(ctx, file: str, name: Optional[str]):
    """Import a profile from file"""
    profile_manager = ctx.obj['profile_manager']
    
    try:
        imported_name = profile_manager.import_profile(Path(file), name)
        console.print(f"[green]✓[/green] Imported profile as '{imported_name}'")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Exit(1)


@config.command()
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.pass_context
def export(ctx, output: Optional[str]):
    """Export entire configuration"""
    config_manager = ctx.obj['config_manager']
    
    try:
        output_path = Path(output) if output else None
        exported_path = config_manager.export_config(output_path)
        console.print(f"[green]✓[/green] Exported configuration to {exported_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Exit(1)


@config.command('import')
@click.argument('file', type=click.Path(exists=True))
@click.option('--merge', '-m', is_flag=True, help='Merge with existing configuration')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
@click.pass_context
def import_config(ctx, file: str, merge: bool, force: bool):
    """Import configuration from file"""
    config_manager = ctx.obj['config_manager']
    
    action = "merge with" if merge else "replace"
    if not force:
        if not click.confirm(f"Import will {action} current configuration. Continue?"):
            return
    
    try:
        config_manager.import_config(Path(file), merge)
        console.print(f"[green]✓[/green] Imported configuration from {file}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Exit(1)