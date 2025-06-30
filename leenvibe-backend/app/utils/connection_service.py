"""
Connection service for managing iOS app connections.
Handles QR code generation and connection management.
"""

import logging
from typing import Dict

from .network_discovery import NetworkDiscovery
from .qr_generator import create_terminal_qr_display

logger = logging.getLogger(__name__)


class ConnectionService:
    """Service for managing iOS connections"""

    def __init__(self, port: int = 8000):
        self.port = port
        self.network_discovery = NetworkDiscovery(port)

    def get_connection_config(self) -> Dict:
        """Get complete connection configuration"""
        return self.network_discovery.generate_connection_config()

    def get_qr_display(self) -> str:
        """Get formatted QR code display for terminal"""
        config = self.get_connection_config()
        return create_terminal_qr_display(config)

    def print_connection_info(self):
        """Print connection information to console"""
        config = self.get_connection_config()

        print("\n" + "=" * 60)
        print("🚀 LeanVibe Backend - Ready for iOS Connection")
        print("=" * 60)

        # Print network interfaces
        print("\n📡 Available Network Interfaces:")
        for interface in config["leanvibe"]["metadata"]["all_interfaces"]:
            icon = self._get_interface_icon(interface["type"])
            print(f"   {icon} {interface['type'].title()}: {interface['url']}")

        # Print QR code
        qr_display = self.get_qr_display()
        print(qr_display)

        print("=" * 60)
        print("✅ Backend is ready! Start the iOS app and scan the QR code.")
        print("=" * 60 + "\n")

    def _get_interface_icon(self, interface_type: str) -> str:
        """Get emoji icon for interface type"""
        icons = {
            "wifi": "📶",
            "ethernet": "🔌",
            "usb": "🔗",
            "bluetooth": "📘",
            "loopback": "🔁",
            "unknown": "❓",
        }
        return icons.get(interface_type, "❓")


# Global connection service instance
connection_service = ConnectionService()


def print_startup_qr(port: int = 8000):
    """Print startup QR code and connection info"""
    service = ConnectionService(port)
    service.print_connection_info()


def get_connection_qr_data(port: int = 8000) -> str:
    """Get QR code data as JSON string"""
    import json

    service = ConnectionService(port)
    config = service.get_connection_config()
    return json.dumps(config)
