"""
Query command for LeenVibe CLI

Provides natural language interaction with the L3 agent for intelligent
codebase questions and assistance.
"""

import asyncio
from typing import Dict, Any, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config.legacy import CLIConfig
from ..client import BackendClient

console = Console()


@click.command()
@click.argument('question', required=False)
@click.option('--workspace', '-w', default='.', help='Workspace path for analysis context')
@click.option('--interactive', '-i', is_flag=True, help='Start interactive query session')
@click.option('--command', '-c', is_flag=True, help='Execute as slash command')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def query(ctx: click.Context, question: Optional[str], workspace: str, interactive: bool, command: bool, output_json: bool):
    """Query the L3 agent with natural language or slash commands"""
    config = ctx.obj['config']
    client = ctx.obj['client']
    
    if interactive:
        asyncio.run(interactive_query_session(config, client, workspace, output_json))
    elif question:
        asyncio.run(single_query(config, client, question, workspace, command, output_json))
    else:
        console.print("[yellow]Please provide a question or use --interactive mode[/yellow]")
        console.print("[dim]Example: leenvibe query \"What are the main components of this project?\"[/dim]")


async def single_query(config: CLIConfig, client: BackendClient, question: str, workspace: str, is_command: bool, output_json: bool):
    """Execute a single query"""
    try:
        async with client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console if not output_json else None
            ) as progress:
                
                if not output_json:
                    task = progress.add_task("Processing query...", total=None)
                
                # Execute query
                if is_command:
                    response = await client.execute_command(question, workspace)
                else:
                    response = await client.query_agent(question, workspace)
                
                if not output_json:
                    progress.update(task, description="Query complete!")
            
            if output_json:
                import json
                console.print(json.dumps(response, indent=2, default=str))
                return
            
            display_query_response(response, question)
            
    except Exception as e:
        if output_json:
            import json
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Query failed: {e}[/red]")
            console.print("[dim]Make sure the backend is running and accessible[/dim]")


async def interactive_query_session(config: CLIConfig, client: BackendClient, workspace: str, output_json: bool):
    """Start an interactive query session"""
    
    if not output_json:
        show_interactive_header(config)
    
    try:
        async with client:
            # Connect to WebSocket for persistent session
            if not await client.connect_websocket():
                console.print("[red]Failed to connect to backend for interactive session[/red]")
                return
            
            if not output_json:
                console.print("[green]🤖 Interactive session started - Type 'quit' to exit[/green]\n")
            
            while True:
                try:
                    # Get user input
                    if output_json:
                        # In JSON mode, read from stdin
                        try:
                            import sys
                            user_input = input().strip()
                        except EOFError:
                            break
                    else:
                        user_input = console.input("[bold cyan]❯[/bold cyan] ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Check for exit commands
                    if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                        if not output_json:
                            console.print("[yellow]Goodbye![/yellow]")
                        break
                    
                    # Check for help
                    if user_input.lower() in ['help', '?']:
                        if not output_json:
                            show_interactive_help()
                        continue
                    
                    # Process query
                    is_command = user_input.startswith('/')
                    
                    if not output_json:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            console=console
                        ) as progress:
                            task = progress.add_task("Processing...", total=None)
                            
                            if is_command:
                                response = await client.execute_command(user_input, workspace)
                            else:
                                response = await client.query_agent(user_input, workspace)
                            
                            progress.update(task, description="Complete!")
                    else:
                        if is_command:
                            response = await client.execute_command(user_input, workspace)
                        else:
                            response = await client.query_agent(user_input, workspace)
                    
                    # Display response
                    if output_json:
                        import json
                        console.print(json.dumps({
                            "query": user_input,
                            "response": response
                        }, indent=2, default=str))
                    else:
                        console.print()  # Add space
                        display_query_response(response, user_input)
                        console.print()  # Add space
                
                except KeyboardInterrupt:
                    if not output_json:
                        console.print("\n[yellow]Use 'quit' to exit gracefully[/yellow]")
                    continue
                except EOFError:
                    break
    
    except Exception as e:
        if output_json:
            import json
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Interactive session error: {e}[/red]")


def show_interactive_header(config: CLIConfig):
    """Show interactive session header"""
    header_text = Text()
    header_text.append("🤖 Interactive L3 Agent Session\n", style="bold cyan")
    header_text.append(f"Backend: {config.backend_url}\n", style="dim")
    header_text.append("Ask questions about your codebase or use slash commands\n", style="white")
    header_text.append("\nTips:\n", style="bold")
    header_text.append("• Ask natural language questions about your code\n", style="green")
    header_text.append("• Use /help for available slash commands\n", style="green")
    header_text.append("• Type 'help' for interactive commands\n", style="green")
    header_text.append("• Type 'quit' to exit\n", style="green")
    
    panel = Panel(
        header_text,
        title="[bold]LeenVibe Interactive Query[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)


def show_interactive_help():
    """Show help for interactive mode"""
    help_text = Text()
    help_text.append("Interactive Commands:\n", style="bold cyan")
    help_text.append("• help, ?          - Show this help\n", style="white")
    help_text.append("• quit, exit, q    - Exit interactive mode\n", style="white")
    help_text.append("\nSlash Commands:\n", style="bold cyan")
    help_text.append("• /status          - Backend status\n", style="white")
    help_text.append("• /help            - Available slash commands\n", style="white")
    help_text.append("• /analyze         - Trigger analysis\n", style="white")
    help_text.append("• /list-files      - List project files\n", style="white")
    help_text.append("\nNatural Language Examples:\n", style="bold cyan")
    help_text.append("• \"What are the main components?\"\n", style="green")
    help_text.append("• \"Find all classes that inherit from X\"\n", style="green")
    help_text.append("• \"Show me the complexity hotspots\"\n", style="green")
    help_text.append("• \"Explain this function's purpose\"\n", style="green")
    
    panel = Panel(
        help_text,
        title="[bold]Help[/bold]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(panel)


def display_query_response(response: Dict[str, Any], original_query: str):
    """Display formatted query response"""
    
    # Extract response data
    status = response.get('status', 'unknown')
    message = response.get('message', '')
    confidence = response.get('confidence', 0.0)
    timestamp = response.get('timestamp', '')
    
    # Create response panel
    if status == 'success':
        border_style = "green"
        status_icon = "✅"
    elif status == 'error':
        border_style = "red"
        status_icon = "❌"
    else:
        border_style = "yellow"
        status_icon = "⚠️"
    
    # Format confidence
    confidence_text = ""
    if confidence > 0:
        confidence_percent = confidence * 100
        if confidence_percent >= 80:
            confidence_color = "green"
        elif confidence_percent >= 60:
            confidence_color = "yellow"
        else:
            confidence_color = "red"
        confidence_text = f" (Confidence: [{confidence_color}]{confidence_percent:.1f}%[/{confidence_color}])"
    
    # Panel title
    title = f"[bold]{status_icon} Response{confidence_text}[/bold]"
    
    # Panel content
    if message:
        # Try to render as markdown if it looks like markdown
        if any(marker in message for marker in ['#', '*', '`', '-']):
            try:
                content = Markdown(message)
            except:
                content = Text(message)
        else:
            content = Text(message)
    else:
        content = Text("No response message", style="dim")
    
    panel = Panel(
        content,
        title=title,
        border_style=border_style,
        padding=(1, 2)
    )
    
    console.print(panel)
    
    # Show additional response details if available
    if response.get('data') or response.get('analysis'):
        display_additional_response_data(response)


def display_additional_response_data(response: Dict[str, Any]):
    """Display additional response data"""
    
    # Analysis data
    if 'analysis' in response:
        analysis = response['analysis']
        if isinstance(analysis, dict) and analysis:
            console.print("\n[bold cyan]Analysis Details:[/bold cyan]")
            for key, value in analysis.items():
                if isinstance(value, (str, int, float)):
                    console.print(f"• {key.replace('_', ' ').title()}: {value}")
    
    # Data payload
    if 'data' in response:
        data = response['data']
        if isinstance(data, dict) and data:
            console.print("\n[bold cyan]Additional Data:[/bold cyan]")
            for key, value in data.items():
                if isinstance(value, (str, int, float)):
                    console.print(f"• {key.replace('_', ' ').title()}: {value}")
    
    # Suggestions or recommendations
    if 'suggestions' in response:
        suggestions = response['suggestions']
        if isinstance(suggestions, list) and suggestions:
            console.print("\n[bold cyan]Suggestions:[/bold cyan]")
            for i, suggestion in enumerate(suggestions, 1):
                console.print(f"{i}. {suggestion}")
    
    # Error details
    if response.get('status') == 'error' and 'error_details' in response:
        details = response['error_details']
        console.print(f"\n[red]Error Details:[/red] {details}")