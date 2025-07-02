"""
LeanVibe CLI initialization command

Sets up a new project with LeanVibe CLI integration, including
backend connection, project configuration, and development workflow setup.
"""

import asyncio
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


@click.command(name="init")
@click.option("--name", "-n", help="Project name")
@click.option("--type", "-t", "project_type", 
              type=click.Choice(['python', 'node', 'rust', 'go', 'generic']), 
              default='python', help="Project type")
@click.option("--backend-url", help="LeanVibe backend URL")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option("--minimal", is_flag=True, help="Create minimal configuration")
@click.pass_context
def init(ctx: click.Context, name: Optional[str], project_type: str, 
         backend_url: Optional[str], force: bool, minimal: bool):
    """
    Initialize a new project with LeanVibe CLI integration
    
    Sets up project configuration, development workflows, and backend connection
    for optimal LeanVibe CLI integration with your development environment.
    """
    config: CLIConfig = ctx.obj['config']
    client: BackendClient = ctx.obj['client']
    
    asyncio.run(_execute_project_init(
        config, client, name, project_type, backend_url, force, minimal
    ))


async def _execute_project_init(config: CLIConfig, client: BackendClient, 
                               name: Optional[str], project_type: str,
                               backend_url: Optional[str], force: bool, minimal: bool):
    """Execute the project initialization process"""
    
    current_dir = Path.cwd()
    project_name = name or current_dir.name
    
    console.print(f"[cyan]🚀 Initializing LeanVibe CLI project: {project_name}[/cyan]\n")
    
    # Check if already initialized
    leanvibe_dir = current_dir / ".leanvibe"
    if leanvibe_dir.exists() and not force:
        console.print("[yellow]Project already initialized. Use --force to overwrite.[/yellow]")
        return
    
    try:
        # Create project structure
        await create_project_structure(current_dir, project_name, project_type, force)
        
        # Setup backend connection
        backend_url = backend_url or await discover_backend_url(client)
        await setup_backend_connection(current_dir, backend_url)
        
        # Create project configuration
        await create_project_configuration(current_dir, project_name, project_type, backend_url, minimal)
        
        # Setup development workflows
        if not minimal:
            await setup_development_workflows(current_dir, project_type)
        
        # Initialize Git hooks (optional)
        if await check_git_repository(current_dir):
            if not minimal and Confirm.ask("Setup Git hooks for LeanVibe integration?"):
                await setup_git_hooks(current_dir)
        
        # Test backend connection
        await test_backend_connection(client, backend_url)
        
        console.print(f"\n[green]✅ Project '{project_name}' initialized successfully![/green]")
        show_next_steps(project_name, project_type)
        
    except Exception as e:
        console.print(f"[red]❌ Initialization failed: {e}[/red]")


async def create_project_structure(project_dir: Path, project_name: str, 
                                 project_type: str, force: bool):
    """Create the basic LeanVibe project structure"""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Creating project structure...", total=None)
        
        # Create .leanvibe directory
        leanvibe_dir = project_dir / ".leanvibe"
        if force and leanvibe_dir.exists():
            shutil.rmtree(leanvibe_dir)
        
        leanvibe_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (leanvibe_dir / "cache").mkdir(exist_ok=True)
        (leanvibe_dir / "logs").mkdir(exist_ok=True)
        (leanvibe_dir / "workflows").mkdir(exist_ok=True)
        
        progress.update(task, description="Project structure created")


async def discover_backend_url(client: BackendClient) -> str:
    """Discover or prompt for backend URL"""
    
    # Try default URL first
    default_url = "http://localhost:8000"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Discovering backend...", total=None)
        
        try:
            # Test default URL
            test_client = BackendClient(type('Config', (), {
                'backend_url': default_url,
                'websocket_url': default_url.replace('http', 'ws') + '/ws',
                'timeout_seconds': 5,
                'verbose': False
            })())
            
            async with test_client:
                health = await test_client.health_check()
                if health.get('status') == 'healthy':
                    progress.update(task, description="Backend discovered")
                    return default_url
        except:
            pass
        
        progress.update(task, description="Backend discovery failed")
    
    # Prompt user for URL
    return Prompt.ask(
        "Backend URL", 
        default=default_url,
        console=console
    )


async def setup_backend_connection(project_dir: Path, backend_url: str):
    """Setup backend connection configuration"""
    
    connection_config = {
        'backend': {
            'url': backend_url,
            'websocket_url': backend_url.replace('http', 'ws') + '/ws',
            'timeout': 30,
            'retry_attempts': 3
        },
        'client': {
            'id': f"project_{project_dir.name}_{int(time.time())}",
            'session_persistence': True,
            'auto_reconnect': True
        }
    }
    
    config_file = project_dir / ".leanvibe" / "connection.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(connection_config, f, default_flow_style=False, indent=2)


async def create_project_configuration(project_dir: Path, project_name: str, 
                                     project_type: str, backend_url: str, minimal: bool):
    """Create comprehensive project configuration"""
    
    # Base configuration
    project_config = {
        'project': {
            'name': project_name,
            'type': project_type,
            'version': '1.0.0',
            'description': f'{project_name} - LeanVibe integrated project'
        },
        'leanvibe': {
            'version': '1.0.0',
            'backend_url': backend_url,
            'features': {
                'ai_assistance': True,
                'code_analysis': True,
                'auto_commits': False if minimal else True,
                'live_monitoring': False if minimal else True
            }
        }
    }
    
    # Add project-specific commands based on type
    if not minimal:
        project_config['project_commands'] = get_project_commands_template(project_type)
    
    # Add development configuration
    if not minimal:
        project_config['development'] = get_development_config_template(project_type)
    
    config_file = project_dir / ".leanvibe" / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(project_config, f, default_flow_style=False, indent=2)


async def setup_development_workflows(project_dir: Path, project_type: str):
    """Setup development workflow templates"""
    
    workflows_dir = project_dir / ".leanvibe" / "workflows"
    
    # Create workflow templates based on project type
    workflows = get_workflow_templates(project_type)
    
    for workflow_name, workflow_config in workflows.items():
        workflow_file = workflows_dir / f"{workflow_name}.yaml"
        with open(workflow_file, 'w') as f:
            yaml.dump(workflow_config, f, default_flow_style=False, indent=2)


async def check_git_repository(project_dir: Path) -> bool:
    """Check if the project is a Git repository"""
    
    result = subprocess.run(
        ['git', 'rev-parse', '--git-dir'],
        cwd=project_dir,
        capture_output=True,
        text=True
    )
    return result.returncode == 0


async def setup_git_hooks(project_dir: Path):
    """Setup Git hooks for LeanVibe integration"""
    
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        return
    
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    # Pre-commit hook for AI-powered analysis
    pre_commit_hook = hooks_dir / "pre-commit"
    pre_commit_content = """#!/bin/bash
# LeanVibe CLI pre-commit hook

echo "🔍 Running LeanVibe pre-commit analysis..."

# Check if leanvibe CLI is available
if command -v leanvibe &> /dev/null; then
    # Run quick analysis on staged files
    leanvibe analyze --staged --quick
    if [ $? -ne 0 ]; then
        echo "❌ LeanVibe analysis found issues. Fix them or use --no-verify to skip."
        exit 1
    fi
    
    echo "✅ LeanVibe pre-commit analysis passed"
else
    echo "⚠️  LeanVibe CLI not found in PATH"
fi

exit 0
"""
    
    with open(pre_commit_hook, 'w') as f:
        f.write(pre_commit_content)
    
    # Make executable
    os.chmod(pre_commit_hook, 0o755)
    
    console.print("[green]✅ Git hooks setup complete[/green]")


async def test_backend_connection(client: BackendClient, backend_url: str):
    """Test connection to LeanVibe backend"""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Testing backend connection...", total=None)
        
        try:
            # Update client configuration
            client.config.backend_url = backend_url
            client.config.websocket_url = backend_url.replace('http', 'ws') + '/ws'
            
            async with client:
                health = await client.health_check()
                if health.get('status') == 'healthy':
                    progress.update(task, description="Backend connection successful")
                    console.print("[green]✅ Backend connection verified[/green]")
                else:
                    console.print(f"[yellow]⚠️  Backend health check returned: {health}[/yellow]")
        
        except Exception as e:
            progress.update(task, description="Backend connection failed")
            console.print(f"[yellow]⚠️  Backend connection failed: {e}[/yellow]")
            console.print("[dim]Project will work offline until backend is available[/dim]")


def get_project_commands_template(project_type: str) -> Dict[str, Any]:
    """Get project-specific command templates"""
    
    templates = {
        'python': {
            'test': {
                'description': 'Run Python tests',
                'command': 'pytest',
                'args': ['-v'],
                'working_directory': '.'
            },
            'lint': {
                'description': 'Run Python linting',
                'command': 'ruff',
                'args': ['check', '.'],
                'working_directory': '.'
            },
            'format': {
                'description': 'Format Python code',
                'command': 'ruff',
                'args': ['format', '.'],
                'working_directory': '.'
            },
            'dev': {
                'description': 'Start development server',
                'command': 'python',
                'args': ['-m', 'uvicorn', 'main:app', '--reload'],
                'working_directory': '.'
            }
        },
        'node': {
            'test': {
                'description': 'Run Node.js tests',
                'command': 'npm',
                'args': ['test'],
                'working_directory': '.'
            },
            'lint': {
                'description': 'Run ESLint',
                'command': 'npm',
                'args': ['run', 'lint'],
                'working_directory': '.'
            },
            'build': {
                'description': 'Build project',
                'command': 'npm',
                'args': ['run', 'build'],
                'working_directory': '.'
            },
            'dev': {
                'description': 'Start development server',
                'command': 'npm',
                'args': ['run', 'dev'],
                'working_directory': '.'
            }
        },
        'rust': {
            'test': {
                'description': 'Run Rust tests',
                'command': 'cargo',
                'args': ['test'],
                'working_directory': '.'
            },
            'lint': {
                'description': 'Run Clippy linting',
                'command': 'cargo',
                'args': ['clippy'],
                'working_directory': '.'
            },
            'build': {
                'description': 'Build Rust project',
                'command': 'cargo',
                'args': ['build'],
                'working_directory': '.'
            },
            'run': {
                'description': 'Run Rust application',
                'command': 'cargo',
                'args': ['run'],
                'working_directory': '.'
            }
        },
        'go': {
            'test': {
                'description': 'Run Go tests',
                'command': 'go',
                'args': ['test', './...'],
                'working_directory': '.'
            },
            'lint': {
                'description': 'Run Go linting',
                'command': 'golangci-lint',
                'args': ['run'],
                'working_directory': '.'
            },
            'build': {
                'description': 'Build Go project',
                'command': 'go',
                'args': ['build'],
                'working_directory': '.'
            },
            'run': {
                'description': 'Run Go application',
                'command': 'go',
                'args': ['run', '.'],
                'working_directory': '.'
            }
        }
    }
    
    return templates.get(project_type, {
        'build': {
            'description': 'Build project',
            'command': 'make',
            'args': [],
            'working_directory': '.'
        },
        'test': {
            'description': 'Run tests',
            'command': 'make',
            'args': ['test'],
            'working_directory': '.'
        }
    })


def get_development_config_template(project_type: str) -> Dict[str, Any]:
    """Get development configuration template"""
    
    return {
        'monitoring': {
            'file_patterns': get_file_patterns(project_type),
            'ignore_patterns': get_ignore_patterns(project_type),
            'auto_analysis': True,
            'notification_level': 'medium'
        },
        'ai_assistance': {
            'auto_suggest_commits': True,
            'code_review_hints': True,
            'refactoring_suggestions': True,
            'dependency_analysis': True
        },
        'workflows': {
            'pre_commit_analysis': True,
            'auto_formatting': False,
            'test_on_change': False
        }
    }


def get_file_patterns(project_type: str) -> List[str]:
    """Get file patterns to monitor for project type"""
    
    patterns = {
        'python': ['*.py', '*.pyi', 'requirements.txt', 'pyproject.toml'],
        'node': ['*.js', '*.ts', '*.jsx', '*.tsx', 'package.json', '*.json'],
        'rust': ['*.rs', 'Cargo.toml', 'Cargo.lock'],
        'go': ['*.go', 'go.mod', 'go.sum']
    }
    
    return patterns.get(project_type, ['*'])


def get_ignore_patterns(project_type: str) -> List[str]:
    """Get ignore patterns for project type"""
    
    patterns = {
        'python': ['__pycache__/*', '*.pyc', '.venv/*', 'venv/*', '.pytest_cache/*'],
        'node': ['node_modules/*', 'dist/*', 'build/*', '*.log'],
        'rust': ['target/*', 'Cargo.lock'],
        'go': ['vendor/*', '*.exe', '*.test']
    }
    
    base_patterns = ['.git/*', '.leanvibe/cache/*', '.leanvibe/logs/*', '*.tmp', '*.bak']
    return base_patterns + patterns.get(project_type, [])


def get_workflow_templates(project_type: str) -> Dict[str, Dict[str, Any]]:
    """Get workflow templates for project type"""
    
    return {
        'ci': {
            'name': 'Continuous Integration',
            'trigger': 'on_push',
            'steps': [
                {'name': 'lint', 'command': 'leanvibe project run lint'},
                {'name': 'test', 'command': 'leanvibe project run test'},
                {'name': 'analyze', 'command': 'leanvibe analyze --full'}
            ]
        },
        'release': {
            'name': 'Release Preparation',
            'trigger': 'manual',
            'steps': [
                {'name': 'test', 'command': 'leanvibe project run test'},
                {'name': 'build', 'command': 'leanvibe project run build'},
                {'name': 'analyze', 'command': 'leanvibe analyze --security'},
                {'name': 'tag', 'command': 'git tag -a v${VERSION} -m "Release ${VERSION}"'}
            ]
        }
    }


def show_next_steps(project_name: str, project_type: str):
    """Show next steps after initialization"""
    
    next_steps = Text()
    next_steps.append("🎉 Next steps to get started:\n\n", style="bold green")
    
    next_steps.append("1. ", style="bold")
    next_steps.append("Check the configuration:\n")
    next_steps.append("   leanvibe config show\n\n", style="cyan")
    
    next_steps.append("2. ", style="bold")
    next_steps.append("Test backend connection:\n")
    next_steps.append("   leanvibe status\n\n", style="cyan")
    
    next_steps.append("3. ", style="bold")
    next_steps.append("View available project commands:\n")
    next_steps.append("   leanvibe project list\n\n", style="cyan")
    
    next_steps.append("4. ", style="bold")
    next_steps.append("Start monitoring your project:\n")
    next_steps.append("   leanvibe monitor\n\n", style="cyan")
    
    next_steps.append("5. ", style="bold")
    next_steps.append("Get AI assistance:\n")
    next_steps.append("   leanvibe query \"How can I improve this code?\"\n\n", style="cyan")
    
    next_steps.append("📚 Configuration files created in .leanvibe/\n", style="dim")
    next_steps.append("🔧 Customize workflows in .leanvibe/workflows/\n", style="dim")
    next_steps.append("⚙️  Edit project commands in .leanvibe/config.yaml\n", style="dim")
    
    panel = Panel(
        next_steps,
        title=f"[bold]Welcome to LeanVibe CLI - {project_name}[/bold]",
        border_style="green",
        padding=(1, 2)
    )
    
    console.print(panel)