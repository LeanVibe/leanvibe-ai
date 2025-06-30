"""
QR Code generation utilities for LeanVibe backend.
Generates ASCII QR codes for terminal display.
"""

import json
import logging
from io import StringIO
from typing import Dict

import qrcode

logger = logging.getLogger(__name__)


class QRCodeGenerator:
    """QR code generator for terminal display"""

    def __init__(self, border: int = 1):
        self.border = border

    def generate_ascii_qr(self, data: str, compact: bool = False) -> str:
        """Generate ASCII QR code for terminal display"""
        try:
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,  # Let it auto-size
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=1,
                border=self.border,
            )

            qr.add_data(data)
            qr.make(fit=True)

            # Generate ASCII representation
            if compact:
                return self._generate_compact_ascii(qr)
            else:
                return self._generate_full_ascii(qr)

        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return f"[QR Code generation failed: {e}]"

    def _generate_full_ascii(self, qr) -> str:
        """Generate full-size ASCII QR code"""
        output = StringIO()

        # Get the QR code matrix
        matrix = qr.get_matrix()

        # Convert to ASCII using full blocks
        for row in matrix:
            line = ""
            for cell in row:
                if cell:
                    line += "██"  # Full block for black
                else:
                    line += "  "  # Spaces for white
            output.write(line + "\n")

        return output.getvalue()

    def _generate_compact_ascii(self, qr) -> str:
        """Generate compact ASCII QR code using Unicode characters"""
        output = StringIO()

        # Get the QR code matrix
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

    def generate_connection_qr(self, config: Dict, compact: bool = True) -> str:
        """Generate QR code for connection configuration"""
        try:
            # Convert config to compact JSON
            json_data = json.dumps(config, separators=(",", ":"))

            # Generate QR code
            qr_ascii = self.generate_ascii_qr(json_data, compact=compact)

            return qr_ascii

        except Exception as e:
            logger.error(f"Error generating connection QR code: {e}")
            return f"[Connection QR generation failed: {e}]"


def generate_connection_qr_code(config: Dict, compact: bool = True) -> str:
    """Convenience function to generate connection QR code"""
    generator = QRCodeGenerator()
    return generator.generate_connection_qr(config, compact=compact)


def create_terminal_qr_display(config: Dict) -> str:
    """Create a formatted terminal display with QR code and info"""
    generator = QRCodeGenerator()
    qr_code = generator.generate_connection_qr(config, compact=True)

    # Extract connection info
    server_info = config["leanvibe"]["server"]
    metadata = config["leanvibe"]["metadata"]

    primary_url = f"ws://{server_info['host']}:{server_info['port']}{server_info['websocket_path']}"

    # Create formatted display
    display = f"""
📱 iOS Connection QR Code:

{qr_code}
🔗 Primary URL: {primary_url}
🏠 Server: {metadata['server_name']}
📡 Network: {metadata['network']}

💡 Open LeanVibe iOS app and tap "Scan QR" to connect automatically
"""

    return display
