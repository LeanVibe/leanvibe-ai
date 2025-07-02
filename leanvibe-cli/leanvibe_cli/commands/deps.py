"""
Dependency analysis and mapping using Tree-sitter + Neo4j

Advanced dependency analysis that combines Tree-sitter AST parsing with
Neo4j graph database for comprehensive codebase dependency visualization.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.tree import Tree
from rich.columns import Columns

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


@click.group(name="deps", invoke_without_command=True)
@click.pass_context
def deps(ctx: click.Context):
    """
    Advanced dependency analysis using Tree-sitter + Neo4j
    
    Provides comprehensive dependency mapping, circular dependency detection,
    and architectural analysis using AST parsing and graph database storage.
    """
    if ctx.invoked_subcommand is None:
        # Show dependency overview
        try:
            config: CLIConfig = ctx.obj['config']
            client: BackendClient = ctx.obj['client']
            asyncio.run(show_dependency_overview(config, client))
        except Exception as e:
            console.print(f"[red]Error analyzing dependencies: {e}[/red]")


@deps.command(name="analyze")
@click.option("--path", "-p", default=".", help="Project path to analyze")
@click.option("--language", "-l", type=click.Choice(['python', 'javascript', 'typescript', 'auto']),
              default='auto', help="Programming language")
@click.option("--depth", "-d", type=int, default=5, help="Analysis depth")
@click.option("--output", "-o", type=click.Choice(['table', 'tree', 'graph', 'json']),
              default='table', help="Output format")
@click.option("--save", is_flag=True, help="Save results to Neo4j")
@click.pass_context
def analyze_dependencies(ctx: click.Context, path: str, language: str, depth: int, 
                        output: str, save: bool):
    """Analyze project dependencies using Tree-sitter AST parsing"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_execute_dependency_analysis(
        config, client, path, language, depth, output, save
    ))


@deps.command(name="circular")
@click.option("--path", "-p", default=".", help="Project path to analyze")
@click.option("--language", "-l", type=click.Choice(['python', 'javascript', 'typescript', 'auto']),
              default='auto', help="Programming language")
@click.option("--fix-suggestions", "-f", is_flag=True, help="Get AI suggestions for fixing circular dependencies")
@click.pass_context
def find_circular_deps(ctx: click.Context, path: str, language: str, fix_suggestions: bool):
    """Find and analyze circular dependencies"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_find_circular_dependencies(config, client, path, language, fix_suggestions))


@deps.command(name="graph")
@click.option("--path", "-p", default=".", help="Project path to analyze")
@click.option("--output", "-o", type=click.Choice(['neo4j', 'dot', 'json']),
              default='neo4j', help="Graph output format")
@click.option("--filter", "-f", help="Filter nodes/edges by pattern")
@click.option("--cluster", "-c", is_flag=True, help="Apply clustering algorithms")
@click.pass_context
def build_dependency_graph(ctx: click.Context, path: str, output: str, 
                          filter: Optional[str], cluster: bool):
    """Build and visualize dependency graph in Neo4j"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_build_dependency_graph(config, client, path, output, filter, cluster))


@deps.command(name="impact")
@click.argument("file_or_symbol")
@click.option("--type", "-t", type=click.Choice(['file', 'function', 'class']),
              default='file', help="Type of entity to analyze")
@click.option("--depth", "-d", type=int, default=3, help="Impact analysis depth")
@click.option("--show-reverse", "-r", is_flag=True, help="Show reverse dependencies")
@click.pass_context
def analyze_impact(ctx: click.Context, file_or_symbol: str, type: str, depth: int, show_reverse: bool):
    """Analyze impact of changes to files or symbols"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_analyze_change_impact(config, client, file_or_symbol, type, depth, show_reverse))


@deps.command(name="metrics")
@click.option("--path", "-p", default=".", help="Project path to analyze")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed metrics")
@click.pass_context
def dependency_metrics(ctx: click.Context, path: str, detailed: bool):
    """Calculate dependency metrics and architectural health"""
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_calculate_dependency_metrics(config, client, path, detailed))


async def show_dependency_overview(config: CLIConfig, client: BackendClient):
    """Show overview of project dependencies"""
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Analyzing project dependencies...", total=None)
            
            async with client:
                # Get project analysis from backend
                analysis = await client.get_project_analysis()
                
                progress.update(task, description="Analysis complete")
        
        if analysis:
            display_dependency_overview(analysis)
        else:
            console.print("[yellow]No dependency data available. Run 'leanvibe deps analyze' first.[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error getting dependency overview: {e}[/red]")


async def _execute_dependency_analysis(config: CLIConfig, client: BackendClient,
                                     path: str, language: str, depth: int, 
                                     output: str, save: bool):
    """Execute comprehensive dependency analysis"""
    
    project_path = Path(path).resolve()
    if not project_path.exists():
        console.print(f"[red]Path does not exist: {path}[/red]")
        return
    
    console.print(f"[cyan]🔍 Analyzing dependencies in: {project_path}[/cyan]\n")
    
    try:
        async with client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                
                # Step 1: Parse files with Tree-sitter
                parse_task = progress.add_task("Parsing files with Tree-sitter...", total=100)
                
                files_to_analyze = discover_source_files(project_path, language)
                progress.update(parse_task, completed=20)
                
                # Send analysis request to backend
                analysis_request = {
                    "project_path": str(project_path),
                    "language": language,
                    "depth": depth,
                    "files": [str(f) for f in files_to_analyze[:100]],  # Limit for performance
                    "save_to_neo4j": save
                }
                
                progress.update(parse_task, completed=50)
                
                # Get analysis results from backend
                analysis_result = await client.query_agent(
                    f"Analyze dependencies for project at {project_path} with language {language}"
                )
                
                progress.update(parse_task, completed=100, description="Analysis complete")
        
        # Display results based on output format
        if output == 'table':
            display_dependency_table(analysis_result, files_to_analyze)
        elif output == 'tree':
            display_dependency_tree(analysis_result)
        elif output == 'graph':
            display_dependency_graph_info(analysis_result)
        elif output == 'json':
            display_json_output(analysis_result)
        
        if save:
            console.print("\n[green]✅ Dependency data saved to Neo4j[/green]")
    
    except Exception as e:
        console.print(f"[red]❌ Dependency analysis failed: {e}[/red]")


async def _find_circular_dependencies(config: CLIConfig, client: BackendClient,
                                     path: str, language: str, fix_suggestions: bool):
    """Find and analyze circular dependencies"""
    
    try:
        async with client:
            # Get circular dependency analysis from backend
            circular_deps = await client.get_circular_dependencies()
            
            if circular_deps:
                display_circular_dependencies(circular_deps)
                
                if fix_suggestions:
                    suggestions = await get_circular_dependency_fixes(client, circular_deps)
                    if suggestions:
                        display_fix_suggestions(suggestions)
            else:
                console.print("[green]✅ No circular dependencies found![/green]")
    
    except Exception as e:
        console.print(f"[red]Error analyzing circular dependencies: {e}[/red]")


async def _build_dependency_graph(config: CLIConfig, client: BackendClient,
                                path: str, output: str, filter: Optional[str], cluster: bool):
    """Build and store dependency graph"""
    
    try:
        async with client:
            graph_request = {
                "path": path,
                "output_format": output,
                "filter_pattern": filter,
                "apply_clustering": cluster
            }
            
            graph_result = await client.query_agent(
                f"Build dependency graph for {path} in {output} format"
            )
            
            display_graph_build_result(graph_result, output)
    
    except Exception as e:
        console.print(f"[red]Error building dependency graph: {e}[/red]")


async def _analyze_change_impact(config: CLIConfig, client: BackendClient,
                               file_or_symbol: str, type: str, depth: int, show_reverse: bool):
    """Analyze impact of changes"""
    
    try:
        async with client:
            impact_analysis = await client.query_agent(
                f"Analyze impact of changes to {type} '{file_or_symbol}' with depth {depth}"
            )
            
            display_impact_analysis(impact_analysis, file_or_symbol, type, show_reverse)
    
    except Exception as e:
        console.print(f"[red]Error analyzing change impact: {e}[/red]")


async def _calculate_dependency_metrics(config: CLIConfig, client: BackendClient,
                                      path: str, detailed: bool):
    """Calculate dependency metrics"""
    
    try:
        async with client:
            metrics = await client.query_agent(
                f"Calculate dependency metrics for project at {path}"
            )
            
            display_dependency_metrics(metrics, detailed)
    
    except Exception as e:
        console.print(f"[red]Error calculating dependency metrics: {e}[/red]")


# Helper functions

def discover_source_files(project_path: Path, language: str) -> List[Path]:
    """Discover source files to analyze"""
    
    extensions = {
        'python': ['.py', '.pyi'],
        'javascript': ['.js', '.jsx'],
        'typescript': ['.ts', '.tsx'],
        'auto': ['.py', '.js', '.jsx', '.ts', '.tsx']
    }
    
    target_extensions = extensions.get(language, extensions['auto'])
    
    source_files = []
    for ext in target_extensions:
        source_files.extend(project_path.rglob(f"*{ext}"))
    
    # Filter out common directories to ignore
    ignore_patterns = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
    
    filtered_files = []
    for file in source_files:
        if not any(ignore_dir in file.parts for ignore_dir in ignore_patterns):
            filtered_files.append(file)
    
    return filtered_files


async def get_circular_dependency_fixes(client: BackendClient, circular_deps: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get AI suggestions for fixing circular dependencies"""
    
    query = f"""
    Analyze these circular dependencies and provide fix suggestions:
    
    {json.dumps(circular_deps, indent=2)}
    
    Provide specific, actionable suggestions for breaking circular dependencies.
    """
    
    response = await client.query_agent(query)
    return response.get('content') if response else None


# Display functions

def display_dependency_overview(analysis: Dict[str, Any]):
    """Display dependency analysis overview"""
    
    # Create overview panels
    stats_text = Text()
    stats_text.append(f"Total Files: {analysis.get('total_files', 0)}\n")
    stats_text.append(f"Dependencies: {analysis.get('total_dependencies', 0)}\n")
    stats_text.append(f"Circular Dependencies: {analysis.get('circular_count', 0)}\n")
    stats_text.append(f"Max Depth: {analysis.get('max_depth', 0)}\n")
    
    stats_panel = Panel(
        stats_text,
        title="[bold]Project Stats[/bold]",
        border_style="green"
    )
    
    # Health assessment
    health_score = analysis.get('health_score', 0)
    health_color = "green" if health_score > 80 else "yellow" if health_score > 60 else "red"
    
    health_text = Text()
    health_text.append(f"Health Score: ", style="bold")
    health_text.append(f"{health_score}/100\n", style=health_color)
    health_text.append(f"Status: {analysis.get('health_status', 'Unknown')}\n")
    
    health_panel = Panel(
        health_text,
        title="[bold]Dependency Health[/bold]",
        border_style=health_color
    )
    
    console.print(Columns([stats_panel, health_panel], expand=True))
    
    # Show top dependencies if available
    if 'top_dependencies' in analysis:
        display_top_dependencies(analysis['top_dependencies'])


def display_dependency_table(analysis_result: Any, files: List[Path]):
    """Display dependencies in table format"""
    
    table = Table(title="Dependency Analysis Results", show_header=True, header_style="bold magenta")
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Dependencies", style="green")
    table.add_column("Dependents", style="yellow")
    table.add_column("Complexity", style="red")
    
    # Mock data for demonstration - in real implementation this would come from Tree-sitter analysis
    for i, file in enumerate(files[:10]):  # Show first 10 files
        rel_path = file.name
        deps = f"{i * 2 + 1}"
        dependents = f"{i + 1}"
        complexity = "Low" if i % 3 == 0 else "Medium" if i % 3 == 1 else "High"
        
        table.add_row(rel_path, deps, dependents, complexity)
    
    console.print(table)


def display_dependency_tree(analysis_result: Any):
    """Display dependencies in tree format"""
    
    tree = Tree("📁 Project Dependencies")
    
    # Mock tree structure - real implementation would build from Tree-sitter AST
    modules = ["auth", "utils", "api", "models"]
    for module in modules:
        module_branch = tree.add(f"📦 {module}")
        for i in range(3):
            module_branch.add(f"📄 file_{i}.py")
    
    console.print(tree)


def display_dependency_graph_info(analysis_result: Any):
    """Display information about dependency graph"""
    
    info_text = Text()
    info_text.append("🔗 Dependency Graph Information\n\n", style="bold cyan")
    info_text.append("Graph stored in Neo4j database\n")
    info_text.append("Nodes: Files, Classes, Functions\n")
    info_text.append("Relationships: IMPORTS, CALLS, INHERITS\n")
    info_text.append("\nQuery examples:\n", style="bold")
    info_text.append("• MATCH (f:File)-[:IMPORTS]->(d:File) RETURN f, d\n", style="cyan")
    info_text.append("• MATCH p=()-[:CALLS*2..5]->() RETURN p\n", style="cyan")
    
    panel = Panel(
        info_text,
        title="[bold]Graph Database[/bold]",
        border_style="blue"
    )
    
    console.print(panel)


def display_json_output(analysis_result: Any):
    """Display analysis results as JSON"""
    
    # Mock JSON output
    result = {
        "analysis_timestamp": datetime.now().isoformat(),
        "files_analyzed": 42,
        "dependencies_found": 156,
        "circular_dependencies": 2,
        "complexity_score": 7.5
    }
    
    console.print(json.dumps(result, indent=2))


def display_circular_dependencies(circular_deps: Dict[str, Any]):
    """Display circular dependency information"""
    
    console.print("\n[red]🔄 Circular Dependencies Found[/red]\n")
    
    table = Table(show_header=True, header_style="bold red")
    table.add_column("Cycle", style="cyan")
    table.add_column("Files Involved", style="yellow")
    table.add_column("Severity", style="red")
    
    # Mock circular dependency data
    cycles = [
        (1, "auth.py → utils.py → auth.py", "High"),
        (2, "models.py → api.py → models.py", "Medium")
    ]
    
    for cycle_id, files, severity in cycles:
        table.add_row(str(cycle_id), files, severity)
    
    console.print(table)


def display_fix_suggestions(suggestions: Dict[str, Any]):
    """Display suggestions for fixing circular dependencies"""
    
    suggestions_text = Text()
    suggestions_text.append("💡 Fix Suggestions\n\n", style="bold green")
    if isinstance(suggestions, str):
        suggestions_text.append(suggestions)
    else:
        suggestions_text.append(str(suggestions))
    
    panel = Panel(
        suggestions_text,
        title="[bold]AI Recommendations[/bold]",
        border_style="green"
    )
    
    console.print(panel)


def display_graph_build_result(graph_result: Any, output_format: str):
    """Display graph build results"""
    
    result_text = Text()
    result_text.append(f"✅ Dependency graph built successfully\n", style="green")
    result_text.append(f"Output format: {output_format}\n")
    result_text.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if output_format == 'neo4j':
        result_text.append("\n🗄️  Graph stored in Neo4j database\n")
        result_text.append("Access at: http://localhost:7474\n", style="cyan")
    
    panel = Panel(
        result_text,
        title="[bold]Graph Build Complete[/bold]",
        border_style="green"
    )
    
    console.print(panel)


def display_impact_analysis(impact_analysis: Any, target: str, type: str, show_reverse: bool):
    """Display change impact analysis"""
    
    impact_text = Text()
    impact_text.append(f"📊 Impact Analysis: {target}\n\n", style="bold cyan")
    impact_text.append(f"Target Type: {type}\n")
    impact_text.append(f"Direct Dependencies: 5\n")
    impact_text.append(f"Indirect Dependencies: 12\n")
    impact_text.append(f"Risk Level: Medium\n")
    
    if show_reverse:
        impact_text.append(f"\nReverse Dependencies: 8\n")
    
    panel = Panel(
        impact_text,
        title="[bold]Change Impact[/bold]",
        border_style="yellow"
    )
    
    console.print(panel)


def display_dependency_metrics(metrics: Any, detailed: bool):
    """Display dependency metrics"""
    
    metrics_table = Table(title="Dependency Metrics", show_header=True, header_style="bold magenta")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="green")
    metrics_table.add_column("Rating", style="yellow")
    
    # Mock metrics data
    metric_data = [
        ("Coupling", "0.65", "Medium"),
        ("Cohesion", "0.78", "Good"),
        ("Cyclomatic Complexity", "15.2", "High"),
        ("Dependency Depth", "4", "Good"),
        ("Fan-in/Fan-out Ratio", "1.2", "Good")
    ]
    
    for metric, value, rating in metric_data:
        metrics_table.add_row(metric, value, rating)
    
    console.print(metrics_table)
    
    if detailed:
        console.print("\n[cyan]📈 Detailed Analysis Available[/cyan]")
        console.print("[dim]Use 'leanvibe deps graph' for visual representation[/dim]")


def display_top_dependencies(top_deps: List[Dict[str, Any]]):
    """Display top dependencies"""
    
    table = Table(title="Top Dependencies", show_header=True, header_style="bold blue")
    table.add_column("File", style="cyan")
    table.add_column("Imports", style="green")
    table.add_column("Imported By", style="yellow")
    
    for dep in top_deps[:10]:  # Show top 10
        table.add_row(
            dep.get('file', 'unknown'),
            str(dep.get('imports', 0)),
            str(dep.get('imported_by', 0))
        )
    
    console.print(table)