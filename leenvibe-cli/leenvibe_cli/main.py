#!/usr/bin/env python3
"""
LeenVibe CLI Main Entry Point

Minimal viable CLI that connects to the sophisticated LeenVibe backend
for enterprise codebase analysis and real-time monitoring.
"""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .config import CLIConfig, load_config
from .client import BackendClient
from .commands import status, analyze, monitor, query, info, config


console = Console()


@click.group(invoke_without_command=True)
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--backend-url', help='Backend URL (overrides config)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], backend_url: Optional[str], verbose: bool):
    """
    LeenVibe CLI - Enterprise codebase analysis and monitoring
    
    A terminal-native interface that connects to the LeenVibe backend
    for real-time code analysis, architectural insights, and intelligent
    suggestions powered by AST analysis and graph databases.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Load configuration
    cli_config = load_config(config_path=config)
    if backend_url:
        cli_config.backend_url = backend_url
    if verbose:
        cli_config.verbose = verbose
    
    ctx.obj['config'] = cli_config
    ctx.obj['client'] = BackendClient(cli_config)
    
    # If no command provided, show welcome message and status
    if ctx.invoked_subcommand is None:
        show_welcome()
        # Try to show status by default
        try:
            asyncio.run(status.status_command(cli_config, ctx.obj['client']))
        except Exception as e:
            console.print(f"[red]Error connecting to backend: {e}[/red]")
            console.print("\n[yellow]Run 'leenvibe status' to check connection[/yellow]")


def show_welcome():
    """Display welcome message and basic information"""
    welcome_text = Text()
    welcome_text.append("LeenVibe CLI", style="bold cyan")
    welcome_text.append(" - Enterprise Codebase Analysis\n\n")
    welcome_text.append("🔍 Real-time code monitoring\n", style="green")
    welcome_text.append("🧠 AI-powered analysis\n", style="blue")  
    welcome_text.append("📊 Architecture insights\n", style="magenta")
    welcome_text.append("⚡ Terminal-native interface\n", style="yellow")
    
    panel = Panel(
        welcome_text,
        title="[bold]Welcome to LeenVibe[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)
    console.print("\n[dim]Use 'leenvibe --help' for available commands[/dim]\n")


# Register commands
cli.add_command(status.status)
cli.add_command(analyze.analyze)
cli.add_command(monitor.monitor)
cli.add_command(query.query)
cli.add_command(info.info)
cli.add_command(config.config)


def main():
    """Main entry point for the CLI"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()