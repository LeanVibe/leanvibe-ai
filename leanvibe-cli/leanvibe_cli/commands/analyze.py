"""
Analyze command for LeanVibe CLI

Triggers AST analysis and displays codebase insights using the sophisticated
backend analysis capabilities.
"""

import asyncio
from typing import Dict, Any, List

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


@click.command()
@click.option('--symbol', '-s', help='Analyze specific symbol')
@click.option('--complexity', '-c', is_flag=True, help='Show complexity analysis')
@click.option('--architecture', '-a', is_flag=True, help='Show architecture patterns')
@click.option('--dependencies', '-d', is_flag=True, help='Show circular dependencies')
@click.option('--all', 'show_all', is_flag=True, help='Show all analysis types')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def analyze(ctx: click.Context, symbol: str, complexity: bool, architecture: bool, 
           dependencies: bool, show_all: bool, output_json: bool):
    """Analyze codebase using AST and graph analysis"""
    config = ctx.obj['config']
    client = ctx.obj['client']
    
    # If --all is specified, enable all analysis types
    if show_all:
        complexity = architecture = dependencies = True
    
    # If no specific analysis requested, do project overview
    if not any([symbol, complexity, architecture, dependencies]):
        asyncio.run(analyze_project_overview(config, client, output_json))
    else:
        asyncio.run(analyze_command(config, client, symbol, complexity, architecture, dependencies, output_json))


async def analyze_project_overview(config: CLIConfig, client: BackendClient, output_json: bool = False):
    """Show project overview analysis"""
    try:
        async with client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                task = progress.add_task("Analyzing project...", total=None)
                
                # Get project analysis
                analysis_data = await client.get_project_analysis()
                
                progress.update(task, description="Analysis complete!")
                
            if output_json:
                import json
                console.print(json.dumps(analysis_data, indent=2))
                return
            
            display_project_analysis(analysis_data)
            
    except Exception as e:
        if output_json:
            import json
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Analysis failed: {e}[/red]")


async def analyze_command(config: CLIConfig, client: BackendClient, symbol: str, 
                         complexity: bool, architecture: bool, dependencies: bool, output_json: bool):
    """Execute specific analysis commands"""
    results = {}
    
    try:
        async with client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                tasks = []
                
                # Symbol analysis
                if symbol:
                    task = progress.add_task(f"Analyzing symbol '{symbol}'...", total=None)
                    tasks.append(("symbol", task))
                    symbol_data = await client.find_symbol_references(symbol)
                    results['symbol'] = symbol_data
                    progress.update(task, description=f"Symbol '{symbol}' analysis complete!")
                
                # Complexity analysis
                if complexity:
                    task = progress.add_task("Analyzing complexity...", total=None)
                    tasks.append(("complexity", task))
                    complexity_data = await client.get_complexity_analysis()
                    results['complexity'] = complexity_data
                    progress.update(task, description="Complexity analysis complete!")
                
                # Architecture analysis
                if architecture:
                    task = progress.add_task("Detecting architecture patterns...", total=None)
                    tasks.append(("architecture", task))
                    arch_data = await client.get_architecture_patterns()
                    results['architecture'] = arch_data
                    progress.update(task, description="Architecture analysis complete!")
                
                # Dependency analysis
                if dependencies:
                    task = progress.add_task("Finding circular dependencies...", total=None)
                    tasks.append(("dependencies", task))
                    deps_data = await client.get_circular_dependencies()
                    results['dependencies'] = deps_data
                    progress.update(task, description="Dependency analysis complete!")
            
            if output_json:
                import json
                console.print(json.dumps(results, indent=2))
                return
            
            # Display results
            display_analysis_results(results, symbol)
            
    except Exception as e:
        if output_json:
            import json
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Analysis failed: {e}[/red]")


def display_project_analysis(analysis_data: Dict[str, Any]):
    """Display project analysis overview"""
    analysis = analysis_data.get('analysis', {})
    client_id = analysis_data.get('client_id', 'unknown')
    
    if not analysis:
        console.print("[yellow]No analysis data available[/yellow]")
        console.print("[dim]The backend may still be indexing the project[/dim]")
        return
    
    # Project overview panel
    overview_text = Text()
    overview_text.append("🔍 Project Analysis Overview\n", style="bold cyan")
    overview_text.append(f"Client ID: {client_id}\n", style="dim")
    
    # Add summary information
    if isinstance(analysis, dict):
        for key, value in analysis.items():
            if isinstance(value, (str, int, float)):
                overview_text.append(f"{key.replace('_', ' ').title()}: {value}\n")
    
    panel = Panel(
        overview_text,
        title="[bold]Project Analysis[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)
    
    # Display detailed analysis if available
    if isinstance(analysis, dict) and len(analysis) > 5:
        display_detailed_project_info(analysis)


def display_detailed_project_info(analysis: Dict[str, Any]):
    """Display detailed project information in tables"""
    
    # Files and metrics
    if 'files' in analysis or 'metrics' in analysis:
        table = Table(title="Project Metrics", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="dim")
        table.add_column("Value", style="bold")
        
        metrics = analysis.get('metrics', {})
        for metric, value in metrics.items():
            table.add_row(metric.replace('_', ' ').title(), str(value))
        
        console.print(table)


def display_analysis_results(results: Dict[str, Any], symbol: str = None):
    """Display analysis results"""
    
    # Symbol analysis
    if 'symbol' in results and symbol:
        display_symbol_analysis(results['symbol'], symbol)
    
    # Complexity analysis
    if 'complexity' in results:
        display_complexity_analysis(results['complexity'])
    
    # Architecture analysis
    if 'architecture' in results:
        display_architecture_analysis(results['architecture'])
    
    # Dependencies analysis
    if 'dependencies' in results:
        display_dependencies_analysis(results['dependencies'])


def display_symbol_analysis(symbol_data: Dict[str, Any], symbol_name: str):
    """Display symbol analysis results"""
    references = symbol_data.get('references', {})
    
    if not references:
        console.print(f"[yellow]No references found for symbol '{symbol_name}'[/yellow]")
        return
    
    panel_text = Text()
    panel_text.append(f"Symbol: {symbol_name}\n", style="bold cyan")
    
    if isinstance(references, dict):
        for key, value in references.items():
            panel_text.append(f"{key.replace('_', ' ').title()}: {value}\n")
    elif isinstance(references, list):
        panel_text.append(f"Found {len(references)} references\n")
        for i, ref in enumerate(references[:5], 1):  # Show first 5
            if isinstance(ref, dict):
                file_path = ref.get('file', 'unknown')
                line = ref.get('line', 'unknown')
                panel_text.append(f"{i}. {file_path}:{line}\n", style="dim")
    
    panel = Panel(
        panel_text,
        title=f"[bold]Symbol Analysis: {symbol_name}[/bold]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(panel)


def display_complexity_analysis(complexity_data: Dict[str, Any]):
    """Display complexity analysis results"""
    complexity = complexity_data.get('complexity', {})
    
    if not complexity:
        console.print("[yellow]No complexity data available[/yellow]")
        return
    
    table = Table(title="Code Complexity Analysis", show_header=True, header_style="bold yellow")
    table.add_column("File/Function", style="cyan")
    table.add_column("Complexity", style="bold")
    table.add_column("Status", style="bold")
    
    if isinstance(complexity, dict):
        for item, score in complexity.items():
            if isinstance(score, (int, float)):
                # Color code complexity
                if score < 10:
                    status = "[green]Good[/green]"
                elif score < 20:
                    status = "[yellow]Medium[/yellow]"
                else:
                    status = "[red]High[/red]"
                
                table.add_row(item, str(score), status)
    
    console.print(table)


def display_architecture_analysis(arch_data: Dict[str, Any]):
    """Display architecture analysis results"""
    architecture = arch_data.get('architecture', {})
    
    if not architecture:
        console.print("[yellow]No architecture patterns detected[/yellow]")
        return
    
    panel_text = Text()
    panel_text.append("Architecture Patterns Detected:\n", style="bold magenta")
    
    if isinstance(architecture, dict):
        for pattern, details in architecture.items():
            panel_text.append(f"• {pattern.replace('_', ' ').title()}\n", style="cyan")
            if isinstance(details, str):
                panel_text.append(f"  {details}\n", style="dim")
    elif isinstance(architecture, list):
        for pattern in architecture:
            panel_text.append(f"• {pattern}\n", style="cyan")
    
    panel = Panel(
        panel_text,
        title="[bold]Architecture Analysis[/bold]",
        border_style="magenta",
        padding=(1, 2)
    )
    
    console.print(panel)


def display_dependencies_analysis(deps_data: Dict[str, Any]):
    """Display circular dependencies analysis"""
    circular_deps = deps_data.get('circular_dependencies', [])
    
    if not circular_deps:
        console.print("[green]✅ No circular dependencies found[/green]")
        return
    
    table = Table(title="Circular Dependencies", show_header=True, header_style="bold red")
    table.add_column("Dependency Chain", style="red")
    table.add_column("Severity", style="bold")
    
    if isinstance(circular_deps, list):
        for dep in circular_deps:
            if isinstance(dep, dict):
                chain = dep.get('chain', 'unknown')
                severity = dep.get('severity', 'medium')
                table.add_row(chain, severity.upper())
            else:
                table.add_row(str(dep), "MEDIUM")
    
    console.print(table)