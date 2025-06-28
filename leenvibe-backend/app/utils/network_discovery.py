"""
Network discovery utilities for LeenVibe backend.
Auto-detects local IP addresses and generates connection information.
"""

import json
import logging
import platform
import socket
import subprocess
from typing import Dict, List, Optional

import netifaces

logger = logging.getLogger(__name__)


class NetworkDiscovery:
    """Network discovery and connection info generator"""

    def __init__(self, port: int = 8000):
        self.port = port
        self.hostname = platform.node()

    def get_local_ips(self) -> List[Dict[str, str]]:
        """Get all local IP addresses with interface information"""
        ips = []

        try:
            # Get all network interfaces
            interfaces = netifaces.interfaces()

            for interface in interfaces:
                # Skip loopback and inactive interfaces
                if interface.startswith("lo") or interface.startswith("docker"):
                    continue

                addrs = netifaces.ifaddresses(interface)

                # Get IPv4 addresses
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info.get("addr")
                        if ip and not ip.startswith("127."):
                            # Determine interface type
                            interface_type = self._get_interface_type(interface)

                            ips.append(
                                {
                                    "ip": ip,
                                    "interface": interface,
                                    "type": interface_type,
                                    "url": f"ws://{ip}:{self.port}/ws",
                                }
                            )

        except Exception as e:
            logger.warning(f"Error getting network interfaces: {e}")
            # Fallback to simple socket method
            try:
                # Connect to a remote address to get local IP
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    ips.append(
                        {
                            "ip": local_ip,
                            "interface": "default",
                            "type": "wifi",
                            "url": f"ws://{local_ip}:{self.port}/ws",
                        }
                    )
            except Exception:
                # Ultimate fallback
                ips.append(
                    {
                        "ip": "127.0.0.1",
                        "interface": "localhost",
                        "type": "loopback",
                        "url": f"ws://127.0.0.1:{self.port}/ws",
                    }
                )

        return ips

    def _get_interface_type(self, interface: str) -> str:
        """Determine the type of network interface"""
        interface_lower = interface.lower()

        if (
            "wifi" in interface_lower
            or "wlan" in interface_lower
            or "airport" in interface_lower
        ):
            return "wifi"
        elif "eth" in interface_lower or "en" in interface_lower:
            return "ethernet"
        elif "usb" in interface_lower:
            return "usb"
        elif "bluetooth" in interface_lower or "bt" in interface_lower:
            return "bluetooth"
        else:
            return "unknown"

    def get_primary_ip(self) -> str:
        """Get the primary/preferred IP address"""
        ips = self.get_local_ips()

        if not ips:
            return "127.0.0.1"

        # Prefer WiFi, then Ethernet, then others
        for ip_info in ips:
            if ip_info["type"] == "wifi":
                return ip_info["ip"]

        for ip_info in ips:
            if ip_info["type"] == "ethernet":
                return ip_info["ip"]

        # Return the first available IP
        return ips[0]["ip"]

    def get_network_name(self) -> Optional[str]:
        """Get current WiFi network name (SSID)"""
        try:
            # macOS
            if platform.system() == "Darwin":
                result = subprocess.run(
                    [
                        "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                        "-I",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "SSID" in line:
                            return line.split(":")[1].strip()

            # Linux
            elif platform.system() == "Linux":
                result = subprocess.run(
                    ["iwgetid", "-r"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()

        except Exception as e:
            logger.debug(f"Could not get network name: {e}")

        return None

    def generate_connection_config(self) -> Dict:
        """Generate complete connection configuration"""
        primary_ip = self.get_primary_ip()
        network_name = self.get_network_name()
        all_ips = self.get_local_ips()

        config = {
            "leenvibe": {
                "version": "1.0",
                "server": {
                    "host": primary_ip,
                    "port": self.port,
                    "websocket_path": "/ws",
                    "protocol": "ws",
                },
                "metadata": {
                    "server_name": self.hostname,
                    "network": network_name or "Unknown Network",
                    "all_interfaces": all_ips,
                    "timestamp": int(__import__("time").time()),
                },
            }
        }

        return config


def get_connection_info(port: int = 8000) -> Dict:
    """Convenience function to get connection information"""
    discovery = NetworkDiscovery(port)
    return discovery.generate_connection_config()


def get_primary_connection_url(port: int = 8000) -> str:
    """Get the primary WebSocket connection URL"""
    discovery = NetworkDiscovery(port)
    primary_ip = discovery.get_primary_ip()
    return f"ws://{primary_ip}:{port}/ws"
