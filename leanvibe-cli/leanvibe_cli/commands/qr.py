"""
QR code command for LeanVibe CLI
Display connection QR code for iOS app
"""

import asyncio
import json
import socket
from typing import Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..config import CLIConfig
from ..client import BackendClient

console = Console()


def get_local_ip() -> str:
    """Get the local IP address"""
    try:
        # Connect to a remote address to get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "localhost"


def generate_ascii_qr(data: str) -> str:
    """Generate ASCII QR code for terminal display"""
    try:
        import qrcode
        from io import StringIO
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        # Generate compact ASCII representation
        output = StringIO()
        matrix = qr.get_matrix()
        
        # Process in pairs of rows for compact display
        for i in range(0, len(matrix), 2):
            line = ""
            for j in range(len(matrix[i])):
                top = matrix[i][j] if i < len(matrix) else False
                bottom = matrix[i + 1][j] if i + 1 < len(matrix) else False
                
                # Use Unicode block characters
                if top and bottom:
                    line += "█"  # Full block
                elif top and not bottom:
                    line += "▀"  # Upper half block
                elif not top and bottom:
                    line += "▄"  # Lower half block
                else:
                    line += " "  # Empty space
            
            output.write(line + "\n")
        
        return output.getvalue()
        
    except ImportError:
        return "[QR code requires 'qrcode' package: pip install qrcode]"
    except Exception as e:
        return f"[QR Code generation failed: {e}]"


def create_connection_config(backend_url: str) -> Dict:
    """Create connection configuration for QR code"""
    # Parse backend URL to get host and port
    if backend_url.startswith("http://"):
        backend_url = backend_url[7:]  # Remove http://
    elif backend_url.startswith("https://"):
        backend_url = backend_url[8:]  # Remove https://
    
    # Split host:port
    if ":" in backend_url:
        host, port = backend_url.split(":", 1)
        # Remove any path
        if "/" in port:
            port = port.split("/")[0]
        port = int(port)
    else:
        host = backend_url
        port = 8000
    
    # If host is localhost, use actual IP
    if host in ["localhost", "127.0.0.1"]:
        host = get_local_ip()
    
    return {
        "leanvibe": {
            "server": {
                "host": host,
                "port": port,
                "websocket_path": "/ws"
            },
            "metadata": {
                "server_name": socket.gethostname(),
                "network": "Local Network",
                "generated_by": "leanvibe-cli"
            }
        }
    }


async def check_backend_status(client: BackendClient) -> bool:
    """Check if backend is running"""
    try:
        response = await client.get("/health")
        return response.get("status") == "healthy"
    except Exception:
        return False


async def qr_command(config: CLIConfig, client: BackendClient, compact: bool = False, json_only: bool = False):
    """Display connection QR code for iOS app"""
    
    # Check if backend is running
    backend_running = await check_backend_status(client)
    
    if not backend_running:
        console.print("[yellow]⚠️  Backend not responding. Showing QR for expected configuration.[/yellow]\n")
    
    # Create connection configuration
    connection_config = create_connection_config(config.backend_url)
    
    if json_only:
        # Show just the JSON configuration
        json_str = json.dumps(connection_config, indent=2)
        console.print(f"[cyan]{json_str}[/cyan]")
        return
    
    # Generate QR code
    json_data = json.dumps(connection_config, separators=(",", ":"))
    qr_ascii = generate_ascii_qr(json_data)
    
    # Extract connection info
    server_info = connection_config["leanvibe"]["server"]
    metadata = connection_config["leanvibe"]["metadata"]
    
    primary_url = f"ws://{server_info['host']}:{server_info['port']}{server_info['websocket_path']}"
    
    # Create status indicator
    status_text = "🟢 Backend Running" if backend_running else "🔴 Backend Offline"
    
    # Create formatted display
    qr_panel = Panel(
        qr_ascii,
        title="📱 iOS Connection QR Code",
        border_style="cyan",
        padding=(0, 1)
    )
    
    info_text = Text()
    info_text.append(f"🔗 WebSocket URL: ", style="bold")
    info_text.append(f"{primary_url}\n", style="cyan")
    info_text.append(f"🏠 Server: ", style="bold")
    info_text.append(f"{metadata['server_name']}\n", style="green")
    info_text.append(f"📡 Network: ", style="bold")
    info_text.append(f"{metadata['network']}\n", style="blue")
    info_text.append(f"📊 Status: ", style="bold")
    info_text.append(f"{status_text}\n", style="green" if backend_running else "red")
    
    info_panel = Panel(
        info_text,
        title="Connection Info",
        border_style="green" if backend_running else "red",
        padding=(0, 1)
    )
    
    # Display everything
    console.print(qr_panel)
    console.print(info_panel)
    console.print("\n[dim]💡 Open LeanVibe iOS app → Settings → Server Settings → Scan QR Code[/dim]")


@click.command()
@click.option('--compact', '-c', is_flag=True, help='Use compact QR code display')
@click.option('--json-only', '-j', is_flag=True, help='Show only JSON configuration')
@click.pass_context
def qr(ctx: click.Context, compact: bool, json_only: bool):
    """Display connection QR code for iOS app"""
    config = ctx.obj['config']
    client = ctx.obj['client']
    
    asyncio.run(qr_command(config, client, compact, json_only))