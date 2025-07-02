"""
Enhanced Git integration for LeanVibe CLI

AI-powered Git operations including semantic commits, branch analysis,
and intelligent merge conflict resolution using the backend L3 agent.
"""

import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.columns import Columns

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


@click.group(name="git", invoke_without_command=True)
@click.pass_context
def git(ctx: click.Context):
    """
    Enhanced Git operations with AI-powered assistance
    
    Provides intelligent Git workflow integration using the LeanVibe backend
    for semantic commit messages, branch analysis, and merge conflict resolution.
    """
    if ctx.invoked_subcommand is None:
        # Show Git repository status with AI insights
        try:
            config: CLIConfig = ctx.obj['config']
            client: BackendClient = ctx.obj['client']
            asyncio.run(show_git_status_with_insights(config, client))
        except Exception as e:
            console.print(f"[red]Error analyzing Git repository: {e}[/red]")


@git.command(name="commit")
@click.option("--message", "-m", help="Commit message (will be enhanced by AI)")
@click.option("--auto", "-a", is_flag=True, help="Automatically stage all modified files")
@click.option("--semantic", "-s", is_flag=True, help="Generate semantic commit message")
@click.option("--scope", help="Commit scope for semantic messages")
@click.option("--dry-run", is_flag=True, help="Show what would be committed without executing")
@click.pass_context
def ai_commit(ctx: click.Context, message: Optional[str], auto: bool, semantic: bool, scope: Optional[str], dry_run: bool):
    """Create AI-enhanced commit with semantic messaging"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_execute_ai_commit(config, client, message, auto, semantic, scope, dry_run))


@git.command(name="analyze")
@click.option("--branch", "-b", help="Branch to analyze (default: current)")
@click.option("--since", help="Analyze commits since date/hash")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed analysis")
@click.pass_context
def analyze_branch(ctx: click.Context, branch: Optional[str], since: Optional[str], detailed: bool):
    """Analyze branch history and patterns with AI insights"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_analyze_branch_history(config, client, branch, since, detailed))


@git.command(name="suggest")
@click.option("--type", "suggestion_type", type=click.Choice(['branch', 'commit', 'merge', 'refactor']), 
              default='branch', help="Type of suggestion to generate")
@click.option("--context", help="Additional context for suggestions")
@click.pass_context
def suggest_workflow(ctx: click.Context, suggestion_type: str, context: Optional[str]):
    """Get AI-powered Git workflow suggestions"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_generate_git_suggestions(config, client, suggestion_type, context))


@git.command(name="conflicts")
@click.option("--resolve", "-r", is_flag=True, help="Attempt automatic conflict resolution")
@click.option("--strategy", type=click.Choice(['ours', 'theirs', 'smart']), 
              default='smart', help="Conflict resolution strategy")
@click.pass_context
def handle_conflicts(ctx: click.Context, resolve: bool, strategy: str):
    """Analyze and resolve merge conflicts with AI assistance"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_handle_merge_conflicts(config, client, resolve, strategy))


async def show_git_status_with_insights(config: CLIConfig, client: BackendClient):
    """Show Git status enhanced with AI insights"""
    
    try:
        # Get basic Git status
        git_status = await get_git_status()
        if not git_status['is_repo']:
            console.print("[yellow]Not a Git repository[/yellow]")
            return
        
        # Display basic status
        display_git_status(git_status)
        
        # Get AI insights if there are changes
        if git_status['has_changes']:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Getting AI insights...", total=None)
                
                try:
                    async with client:
                        insights = await get_ai_git_insights(client, git_status)
                        progress.update(task, description="AI analysis complete")
                    
                    if insights:
                        display_ai_insights(insights)
                
                except Exception as e:
                    console.print(f"[yellow]AI insights unavailable: {e}[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error analyzing Git status: {e}[/red]")


async def _execute_ai_commit(config: CLIConfig, client: BackendClient, message: Optional[str], 
                           auto: bool, semantic: bool, scope: Optional[str], dry_run: bool):
    """Execute AI-enhanced commit process"""
    
    # Check if we're in a Git repository
    git_status = await get_git_status()
    if not git_status['is_repo']:
        console.print("[red]Not a Git repository[/red]")
        return
    
    # Stage files if auto flag is set
    if auto:
        console.print("[cyan]Staging modified files...[/cyan]")
        result = subprocess.run(['git', 'add', '-u'], capture_output=True, text=True)
        if result.returncode != 0:
            console.print(f"[red]Failed to stage files: {result.stderr}[/red]")
            return
    
    # Check for staged changes
    result = subprocess.run(['git', 'diff', '--cached', '--name-only'], capture_output=True, text=True)
    if not result.stdout.strip():
        console.print("[yellow]No staged changes to commit[/yellow]")
        return
    
    # Generate or enhance commit message
    try:
        async with client:
            enhanced_message = await generate_commit_message(
                client, git_status, message, semantic, scope
            )
    except Exception as e:
        enhanced_message = message or "Update files"
        console.print(f"[yellow]Using fallback message (AI unavailable): {e}[/yellow]")
    
    # Show what will be committed
    console.print(f"\n[cyan]Commit message:[/cyan] {enhanced_message}")
    console.print(f"[cyan]Files to commit:[/cyan]")
    staged_files = result.stdout.strip().split('\n')
    for file in staged_files:
        console.print(f"  • {file}")
    
    if dry_run:
        console.print(f"\n[yellow]Dry run - would execute: git commit -m \"{enhanced_message}\"[/yellow]")
        return
    
    # Execute commit
    commit_result = subprocess.run(['git', 'commit', '-m', enhanced_message], 
                                 capture_output=True, text=True)
    
    if commit_result.returncode == 0:
        console.print(f"\n[green]✅ Commit successful![/green]")
        console.print(f"[dim]{commit_result.stdout.strip()}[/dim]")
    else:
        console.print(f"[red]❌ Commit failed: {commit_result.stderr}[/red]")


async def _analyze_branch_history(config: CLIConfig, client: BackendClient, 
                                branch: Optional[str], since: Optional[str], detailed: bool):
    """Analyze branch history with AI insights"""
    
    # Get Git log data
    cmd = ['git', 'log', '--oneline', '--graph']
    if branch:
        cmd.append(branch)
    if since:
        cmd.extend(['--since', since])
    
    cmd.extend(['--max-count=20'])  # Limit to recent commits
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]Failed to get Git log: {result.stderr}[/red]")
        return
    
    console.print("[cyan]Recent commit history:[/cyan]")
    console.print(result.stdout)
    
    if detailed:
        try:
            async with client:
                analysis = await analyze_commit_patterns(client, result.stdout)
                if analysis:
                    display_branch_analysis(analysis)
        except Exception as e:
            console.print(f"[yellow]Detailed analysis unavailable: {e}[/yellow]")


async def _generate_git_suggestions(config: CLIConfig, client: BackendClient, 
                                  suggestion_type: str, context: Optional[str]):
    """Generate AI-powered Git workflow suggestions"""
    
    try:
        async with client:
            git_status = await get_git_status()
            suggestions = await get_workflow_suggestions(client, git_status, suggestion_type, context)
            
            if suggestions:
                display_workflow_suggestions(suggestions, suggestion_type)
            else:
                console.print("[yellow]No suggestions available[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error generating suggestions: {e}[/red]")


async def _handle_merge_conflicts(config: CLIConfig, client: BackendClient, 
                                resolve: bool, strategy: str):
    """Handle merge conflicts with AI assistance"""
    
    # Check for merge conflicts
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]Failed to get Git status: {result.stderr}[/red]")
        return
    
    conflicts = [line for line in result.stdout.split('\n') if line.startswith('UU ')]
    
    if not conflicts:
        console.print("[green]No merge conflicts detected[/green]")
        return
    
    console.print(f"[yellow]Found {len(conflicts)} merge conflicts:[/yellow]")
    for conflict in conflicts:
        console.print(f"  • {conflict[3:]}")
    
    if resolve:
        try:
            async with client:
                resolution_plan = await generate_conflict_resolution(client, conflicts, strategy)
                if resolution_plan:
                    display_conflict_resolution(resolution_plan)
                    
                    if click.confirm("Apply suggested resolutions?"):
                        await apply_conflict_resolutions(resolution_plan)
        except Exception as e:
            console.print(f"[red]Error resolving conflicts: {e}[/red]")


# Helper functions

async def get_git_status() -> Dict[str, Any]:
    """Get comprehensive Git repository status"""
    
    # Check if in Git repo
    result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        return {'is_repo': False}
    
    # Get various status information
    status_data = {'is_repo': True}
    
    # Current branch
    result = subprocess.run(['git', 'branch', '--show-current'], 
                          capture_output=True, text=True)
    status_data['current_branch'] = result.stdout.strip() if result.returncode == 0 else 'unknown'
    
    # Modified files
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True)
    status_data['modified_files'] = result.stdout.strip().split('\n') if result.stdout.strip() else []
    status_data['has_changes'] = bool(status_data['modified_files'])
    
    # Recent commits
    result = subprocess.run(['git', 'log', '--oneline', '-5'], 
                          capture_output=True, text=True)
    status_data['recent_commits'] = result.stdout.strip().split('\n') if result.stdout.strip() else []
    
    return status_data


async def get_ai_git_insights(client: BackendClient, git_status: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get AI insights about current Git state"""
    
    query = f"""
    Analyze this Git repository status and provide insights:
    
    Current branch: {git_status['current_branch']}
    Modified files: {len(git_status['modified_files'])}
    Recent commits: {len(git_status['recent_commits'])}
    
    Files changed:
    {chr(10).join(git_status['modified_files'][:10])}
    
    Please provide:
    1. Change pattern analysis
    2. Suggested commit message themes
    3. Workflow recommendations
    4. Potential issues or concerns
    """
    
    response = await client.query_agent(query)
    return response.get('content') if response else None


async def generate_commit_message(client: BackendClient, git_status: Dict[str, Any], 
                                base_message: Optional[str], semantic: bool, 
                                scope: Optional[str]) -> str:
    """Generate AI-enhanced commit message"""
    
    # Get staged changes for context
    result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                          capture_output=True, text=True)
    staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
    
    # Get diff summary
    result = subprocess.run(['git', 'diff', '--cached', '--stat'], 
                          capture_output=True, text=True)
    diff_summary = result.stdout.strip()
    
    context = f"""
    Generate a commit message for these changes:
    
    Staged files: {', '.join(staged_files)}
    Diff summary: {diff_summary}
    Base message: {base_message or 'None provided'}
    Semantic format: {semantic}
    Scope: {scope or 'None'}
    
    Requirements:
    - Clear and descriptive
    - Follow conventional commit format if semantic=True
    - Maximum 72 characters for first line
    - Focus on what and why, not how
    """
    
    try:
        response = await client.query_agent(context)
        if response and 'content' in response:
            # Extract just the commit message from AI response
            content = response['content']
            lines = content.split('\n')
            # Find the actual commit message (usually the first non-empty line after analysis)
            for line in lines:
                line = line.strip()
                if line and not line.startswith(('I', 'Based', 'Here', 'The', 'This will')):
                    return line
        
        # Fallback to base message or generate simple one
        if base_message:
            return base_message
        elif semantic:
            file_types = set(Path(f).suffix for f in staged_files if Path(f).suffix)
            if '.py' in file_types:
                return f"feat: update Python modules{f' ({scope})' if scope else ''}"
            else:
                return f"feat: update project files{f' ({scope})' if scope else ''}"
        else:
            return "Update files"
    
    except Exception:
        return base_message or "Update files"


async def analyze_commit_patterns(client: BackendClient, git_log: str) -> Optional[Dict[str, Any]]:
    """Analyze commit patterns using AI"""
    
    query = f"""
    Analyze these recent commits for patterns and insights:
    
    {git_log}
    
    Provide analysis on:
    1. Commit message quality and consistency
    2. Development patterns and frequency
    3. Suggested improvements
    4. Branch health assessment
    """
    
    response = await client.query_agent(query)
    return response.get('content') if response else None


async def get_workflow_suggestions(client: BackendClient, git_status: Dict[str, Any], 
                                 suggestion_type: str, context: Optional[str]) -> Optional[Dict[str, Any]]:
    """Get AI-powered workflow suggestions"""
    
    query = f"""
    Provide Git workflow suggestions for:
    Type: {suggestion_type}
    Current branch: {git_status.get('current_branch', 'unknown')}
    Has changes: {git_status.get('has_changes', False)}
    Context: {context or 'None provided'}
    
    Provide specific, actionable Git workflow recommendations.
    """
    
    response = await client.query_agent(query)
    return response.get('content') if response else None


async def generate_conflict_resolution(client: BackendClient, conflicts: List[str], 
                                     strategy: str) -> Optional[Dict[str, Any]]:
    """Generate conflict resolution plan"""
    
    query = f"""
    Help resolve these Git merge conflicts:
    
    Conflicts: {', '.join(conflicts)}
    Strategy: {strategy}
    
    Provide specific resolution steps and recommendations.
    """
    
    response = await client.query_agent(query)
    return response.get('content') if response else None


async def apply_conflict_resolutions(resolution_plan: Dict[str, Any]):
    """Apply AI-suggested conflict resolutions"""
    console.print("[yellow]Automatic conflict resolution not yet implemented[/yellow]")
    console.print("[cyan]Please resolve conflicts manually using the suggestions above[/cyan]")


# Display functions

def display_git_status(git_status: Dict[str, Any]):
    """Display Git status information"""
    
    status_text = Text()
    status_text.append(f"Branch: ", style="bold")
    status_text.append(f"{git_status['current_branch']}\n", style="cyan")
    
    if git_status['has_changes']:
        status_text.append(f"Modified files: {len(git_status['modified_files'])}\n", style="yellow")
        for file in git_status['modified_files'][:5]:
            status_text.append(f"  • {file}\n", style="dim")
        if len(git_status['modified_files']) > 5:
            status_text.append(f"  ... and {len(git_status['modified_files']) - 5} more\n", style="dim")
    else:
        status_text.append("Working tree clean\n", style="green")
    
    panel = Panel(
        status_text,
        title="[bold]Git Status[/bold]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(panel)


def display_ai_insights(insights: Any):
    """Display AI insights about Git repository"""
    
    insight_text = Text()
    if isinstance(insights, str):
        insight_text.append(insights)
    else:
        insight_text.append(str(insights))
    
    panel = Panel(
        insight_text,
        title="[bold]AI Insights[/bold]",
        border_style="green",
        padding=(1, 2)
    )
    
    console.print(panel)


def display_branch_analysis(analysis: Any):
    """Display branch analysis results"""
    
    analysis_text = Text()
    if isinstance(analysis, str):
        analysis_text.append(analysis)
    else:
        analysis_text.append(str(analysis))
    
    panel = Panel(
        analysis_text,
        title="[bold]Branch Analysis[/bold]",
        border_style="magenta",
        padding=(1, 2)
    )
    
    console.print(panel)


def display_workflow_suggestions(suggestions: Any, suggestion_type: str):
    """Display workflow suggestions"""
    
    suggestion_text = Text()
    if isinstance(suggestions, str):
        suggestion_text.append(suggestions)
    else:
        suggestion_text.append(str(suggestions))
    
    panel = Panel(
        suggestion_text,
        title=f"[bold]{suggestion_type.title()} Suggestions[/bold]",
        border_style="yellow",
        padding=(1, 2)
    )
    
    console.print(panel)


def display_conflict_resolution(resolution_plan: Any):
    """Display conflict resolution plan"""
    
    resolution_text = Text()
    if isinstance(resolution_plan, str):
        resolution_text.append(resolution_plan)
    else:
        resolution_text.append(str(resolution_plan))
    
    panel = Panel(
        resolution_text,
        title="[bold]Conflict Resolution Plan[/bold]",
        border_style="red",
        padding=(1, 2)
    )
    
    console.print(panel)