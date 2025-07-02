"""
Project command management for LeanVibe CLI

Implements custom project commands that can be defined in .leanvibe/config.yaml
allowing developers to create shortcuts for their most common tasks.
"""

import asyncio
import subprocess
import sys
import os
import shlex
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


@click.group(name="project", invoke_without_command=True)
@click.pass_context
def project(ctx: click.Context):
    """
    Manage custom project commands and workflows
    
    Define custom commands in .leanvibe/config.yaml under the 'project_commands' section.
    These can be shell commands, scripts, or workflows specific to your project.
    """
    if ctx.invoked_subcommand is None:
        # Show available project commands
        try:
            commands = load_project_commands()
            if commands:
                show_available_commands(commands)
            else:
                show_setup_help()
        except Exception as e:
            console.print(f"[red]Error loading project commands: {e}[/red]")


@project.command(name="list")
def list_commands():
    """List all available project commands"""
    try:
        commands = load_project_commands()
        if commands:
            show_available_commands(commands)
        else:
            console.print("[yellow]No project commands configured[/yellow]")
            show_setup_help()
    except Exception as e:
        console.print(f"[red]Error loading project commands: {e}[/red]")


@project.command(name="run")
@click.argument("command_name")
@click.option("--args", "-a", multiple=True, help="Additional arguments to pass to the command")
@click.option("--env", "-e", multiple=True, help="Environment variables (KEY=value)")
@click.option("--dry-run", is_flag=True, help="Show what would be executed without running")
@click.pass_context
def run_command(ctx: click.Context, command_name: str, args: Tuple[str], env: Tuple[str], dry_run: bool):
    """Run a custom project command"""
    try:
        commands = load_project_commands()
        if command_name not in commands:
            console.print(f"[red]Command '{command_name}' not found[/red]")
            available = ", ".join(commands.keys())
            console.print(f"[yellow]Available commands: {available}[/yellow]")
            return
        
        config: CLIConfig = ctx.obj['config']
        client: BackendClient = ctx.obj['client']
        
        asyncio.run(_execute_project_command(
            command_name, 
            commands[command_name], 
            list(args), 
            dict(parse_env_vars(env)), 
            dry_run,
            config,
            client
        ))
        
    except Exception as e:
        console.print(f"[red]Error running command: {e}[/red]")
        if config.verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")


@project.command(name="init")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
def init_project_config(force: bool):
    """Initialize project commands configuration"""
    config_path = get_project_config_path()
    
    if config_path.exists() and not force:
        console.print(f"[yellow]Project configuration already exists at {config_path}[/yellow]")
        console.print("[yellow]Use --force to overwrite[/yellow]")
        return
    
    # Create default project configuration
    default_config = {
        "project_commands": {
            "test": {
                "description": "Run project tests",
                "command": "pytest",
                "args": ["-v"],
                "working_directory": ".",
                "environment": {
                    "PYTHONPATH": "."
                }
            },
            "lint": {
                "description": "Run code linting",
                "command": "flake8",
                "args": ["."],
                "working_directory": "."
            },
            "build": {
                "description": "Build the project",
                "command": "python",
                "args": ["-m", "build"],
                "working_directory": "."
            },
            "start": {
                "description": "Start development server",
                "command": "python",
                "args": ["-m", "uvicorn", "app.main:app", "--reload"],
                "working_directory": "."
            }
        }
    }
    
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False, indent=2)
        
        console.print(f"[green]Project configuration initialized at {config_path}[/green]")
        console.print("\n[cyan]Example commands created:[/cyan]")
        console.print("  • leanvibe project run test")
        console.print("  • leanvibe project run lint")
        console.print("  • leanvibe project run build")
        console.print("  • leanvibe project run start")
        
    except Exception as e:
        console.print(f"[red]Error creating configuration: {e}[/red]")


@project.command(name="add")
@click.argument("command_name")
@click.argument("command")
@click.option("--description", "-d", help="Command description")
@click.option("--args", "-a", multiple=True, help="Default arguments")
@click.option("--env", "-e", multiple=True, help="Environment variables (KEY=value)")
@click.option("--working-dir", "-w", help="Working directory")
def add_command(command_name: str, command: str, description: str, args: Tuple[str], env: Tuple[str], working_dir: str):
    """Add a new project command"""
    try:
        config_path = get_project_config_path()
        
        # Load existing config or create new
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        if "project_commands" not in config:
            config["project_commands"] = {}
        
        # Create new command entry
        new_command = {
            "description": description or f"Run {command_name}",
            "command": command,
            "working_directory": working_dir or "."
        }
        
        if args:
            new_command["args"] = list(args)
            
        if env:
            new_command["environment"] = dict(parse_env_vars(env))
        
        config["project_commands"][command_name] = new_command
        
        # Save updated config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
        
        console.print(f"[green]Added command '{command_name}'[/green]")
        console.print(f"[cyan]Usage: leanvibe project run {command_name}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]Error adding command: {e}[/red]")


def load_project_commands() -> Dict[str, Any]:
    """Load project commands from configuration"""
    config_path = get_project_config_path()
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        return config.get("project_commands", {})
    except Exception as e:
        console.print(f"[red]Error loading project commands: {e}[/red]")
        return {}


def get_project_config_path() -> Path:
    """Get the path to project configuration file"""
    # Look for .leanvibe directory in current directory or parents
    current = Path.cwd()
    
    for path in [current] + list(current.parents):
        leanvibe_dir = path / ".leanvibe"
        if leanvibe_dir.exists():
            return leanvibe_dir / "config.yaml"
    
    # Default to current directory
    return current / ".leanvibe" / "config.yaml"


def show_available_commands(commands: Dict[str, Any]):
    """Display available project commands in a nice table"""
    table = Table(title="Available Project Commands", show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Executable", style="green", no_wrap=True)
    
    for name, config in commands.items():
        cmd = config.get("command", "")
        args = config.get("args", [])
        full_cmd = f"{cmd} {' '.join(args)}" if args else cmd
        
        table.add_row(
            name,
            config.get("description", "No description"),
            full_cmd
        )
    
    console.print(table)
    console.print(f"\n[dim]Run with: leanvibe project run <command>[/dim]")


def show_setup_help():
    """Show help for setting up project commands"""
    help_text = Text()
    help_text.append("Set up custom project commands to streamline your workflow.\n\n", style="white")
    help_text.append("Quick start:\n", style="bold cyan")
    help_text.append("  leanvibe project init", style="green")
    help_text.append(" - Create default configuration\n")
    help_text.append("  leanvibe project add test 'pytest -v'", style="green")
    help_text.append(" - Add a custom command\n")
    help_text.append("  leanvibe project run test", style="green")
    help_text.append(" - Run your command\n\n")
    help_text.append("Commands are stored in .leanvibe/config.yaml", style="dim")
    
    panel = Panel(
        help_text,
        title="[bold]Project Commands Setup[/bold]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(panel)


def parse_env_vars(env_vars: Tuple[str]) -> List[Tuple[str, str]]:
    """Parse environment variable strings"""
    result = []
    for env_var in env_vars:
        if "=" in env_var:
            key, value = env_var.split("=", 1)
            result.append((key.strip(), value.strip()))
        else:
            console.print(f"[yellow]Warning: Invalid environment variable format: {env_var}[/yellow]")
    return result


async def _execute_project_command(
    command_name: str, 
    command_config: Dict[str, Any], 
    extra_args: List[str], 
    extra_env: Dict[str, str],
    dry_run: bool,
    config: CLIConfig,
    client: BackendClient
):
    """Execute a project command with backend notification"""
    
    # Parse command configuration
    cmd = command_config.get("command", "")
    args = command_config.get("args", [])
    working_dir = command_config.get("working_directory", ".")
    env_vars = command_config.get("environment", {})
    description = command_config.get("description", f"Running {command_name}")
    
    # Combine arguments
    all_args = args + extra_args
    
    # Combine environment variables
    env = os.environ.copy()
    env.update(env_vars)
    env.update(extra_env)
    
    # Build full command
    full_command = [cmd] + all_args
    
    if dry_run:
        console.print(f"[yellow]Dry run - would execute:[/yellow]")
        console.print(f"[cyan]Command:[/cyan] {' '.join(full_command)}")
        console.print(f"[cyan]Working Directory:[/cyan] {working_dir}")
        if env_vars or extra_env:
            console.print(f"[cyan]Environment:[/cyan] {dict(env_vars, **extra_env)}")
        return
    
    # Notify backend of command execution
    try:
        await client.notify_command_execution(command_name, full_command, working_dir)
    except Exception as e:
        if config.verbose:
            console.print(f"[yellow]Warning: Could not notify backend: {e}[/yellow]")
    
    # Show execution info
    console.print(f"[cyan]Executing:[/cyan] {description}")
    console.print(f"[dim]Command: {' '.join(full_command)}[/dim]")
    console.print(f"[dim]Working Directory: {working_dir}[/dim]\n")
    
    try:
        # Execute command with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(f"Running {command_name}...", total=None)
            
            # Execute the command
            process = await asyncio.create_subprocess_exec(
                *full_command,
                cwd=working_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Stream output in real-time
            async for line in _stream_output(process):
                progress.stop()
                console.print(line, end="")
                progress.start()
            
            # Wait for completion
            await process.wait()
            progress.update(task, description=f"Completed {command_name}")
        
        # Check exit code
        if process.returncode == 0:
            console.print(f"\n[green]✅ Command '{command_name}' completed successfully[/green]")
        else:
            console.print(f"\n[red]❌ Command '{command_name}' failed with exit code {process.returncode}[/red]")
        
        # Notify backend of completion
        try:
            await client.notify_command_completion(command_name, process.returncode)
        except Exception as e:
            if config.verbose:
                console.print(f"[yellow]Warning: Could not notify backend of completion: {e}[/yellow]")
    
    except Exception as e:
        console.print(f"\n[red]❌ Error executing command: {e}[/red]")
        
        # Notify backend of error
        try:
            await client.notify_command_error(command_name, str(e))
        except Exception:
            pass


async def _stream_output(process):
    """Stream process output line by line"""
    if process.stdout:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            yield line.decode('utf-8', errors='replace')