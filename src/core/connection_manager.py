"""
Connection Manager for Blender MCP Server.

Handles socket communication with Blender and connection monitoring.
"""

import json
import logging
import socket
import time
from datetime import datetime
from typing import Any

from .types import BlenderConnection, ConnectionMonitor, ConnectionStatus

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages connections and communication with Blender."""

    def __init__(self):
        self.monitor = ConnectionMonitor()

    def send_command(
        self, command: dict[str, Any], connection: BlenderConnection
    ) -> dict[str, Any]:
        """Send command to Blender via socket connection."""
        start_time = time.time()
        self.monitor.connection_attempts += 1

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(connection.timeout)
                sock.connect((connection.host, connection.port))

                # Send command
                command_json = json.dumps(command)
                sock.sendall(command_json.encode("utf-8"))

                # Receive response
                response = sock.recv(4096).decode("utf-8")
                result = json.loads(response)

                # Record successful connection
                response_time = time.time() - start_time
                self.monitor.successful_connections += 1
                self.monitor.last_successful_command = datetime.now()
                self.monitor.blender_status = "connected"

                # Record response time
                self.monitor.response_times.append(response_time)
                if len(self.monitor.response_times) > self.monitor.max_response_history:
                    self.monitor.response_times.pop(0)

                return result

        except Exception as e:
            self.monitor.failed_connections += 1
            self.monitor.blender_status = "disconnected"
            logger.error(f"Blender connection failed: {e}")
            return {"success": False, "error": str(e)}

    def check_connection(
        self, host: str = "localhost", port: int = 9876
    ) -> ConnectionStatus:
        """Check Blender connection status."""
        try:
            # Send heartbeat command
            heartbeat_command = {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "params": {},
            }

            connection = BlenderConnection(host=host, port=port, timeout=5.0)
            result = self.send_command(heartbeat_command, connection)

            if result.get("success", False) or result.get("status") == "success":
                self.monitor.last_heartbeat = datetime.now()
                self.monitor.blender_status = "connected"
                return ConnectionStatus(
                    connected=True,
                    status="healthy",
                    response=result,
                    timestamp=datetime.now().isoformat(),
                )

            self.monitor.blender_status = "error"
            return ConnectionStatus(
                connected=False,
                status="error",
                error=result.get("error", "Unknown error"),
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            self.monitor.blender_status = "disconnected"
            return ConnectionStatus(
                connected=False,
                status="disconnected",
                error=str(e),
                timestamp=datetime.now().isoformat(),
            )

    def get_connection_statistics(self) -> dict[str, Any]:
        """Get connection performance statistics."""
        avg_response_time = (
            sum(self.monitor.response_times) / len(self.monitor.response_times)
            if self.monitor.response_times
            else 0
        )

        return {
            "current_status": self.monitor.blender_status,
            "last_heartbeat": self.monitor.last_heartbeat.isoformat()
            if self.monitor.last_heartbeat
            else None,
            "last_successful_command": self.monitor.last_successful_command.isoformat()
            if self.monitor.last_successful_command
            else None,
            "connection_stats": {
                "total_attempts": self.monitor.connection_attempts,
                "successful": self.monitor.successful_connections,
                "failed": self.monitor.failed_connections,
                "success_rate": (
                    self.monitor.successful_connections
                    / self.monitor.connection_attempts
                    * 100
                    if self.monitor.connection_attempts > 0
                    else 0
                ),
            },
            "performance": {
                "avg_response_time_ms": round(avg_response_time * 1000, 2),
                "recent_response_times_ms": [
                    round(t * 1000, 2) for t in self.monitor.response_times[-10:]
                ],
                "total_recorded_responses": len(self.monitor.response_times),
            },
            "generated_at": datetime.now().isoformat(),
        }

    def reset_statistics(self) -> dict[str, Any]:
        """Reset connection statistics."""
        self.monitor.connection_attempts = 0
        self.monitor.successful_connections = 0
        self.monitor.failed_connections = 0
        self.monitor.response_times = []

        return {
            "success": True,
            "message": "Connection statistics reset successfully",
            "reset_at": datetime.now().isoformat(),
        }

    def get_detailed_status(
        self, host: str = "localhost", port: int = 9876
    ) -> dict[str, Any]:
        """Get comprehensive connection status information."""
        connection_result = self.check_connection(host, port)
        stats = self.get_connection_statistics()

        return {
            "connection_check": connection_result.__dict__,
            "connection_monitor": self.monitor.to_dict(),
            "statistics": stats,
            "server_info": {
                "host": host,
                "port": port,
                "checked_at": datetime.now().isoformat(),
            },
        }
