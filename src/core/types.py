"""
Shared type definitions for Blender MCP Server.

Contains common data structures and type hints used across modules.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class BlenderConnection:
    """Configuration for Blender socket connection."""

    host: str
    port: int
    timeout: float


@dataclass
class ConnectionStatus:
    """Status information for Blender connection."""

    connected: bool
    status: str
    error: str | None = None
    timestamp: str | None = None
    response: dict[str, Any] | None = None


@dataclass
class ExecutionResult:
    """Result of script execution."""

    script: str
    parameters: dict[str, Any] | None
    result: dict[str, Any]
    timestamp: str
    validation_info: dict[str, Any] | None = None


class ConnectionMonitor:
    """Connection monitoring data structure."""

    def __init__(self):
        self.blender_status = "unknown"
        self.last_heartbeat = None
        self.last_successful_command = None
        self.connection_attempts = 0
        self.successful_connections = 0
        self.failed_connections = 0
        self.response_times: list[float] = []
        self.max_response_history = 50

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "blender_status": self.blender_status,
            "last_heartbeat": self.last_heartbeat.isoformat()
            if self.last_heartbeat
            else None,
            "last_successful_command": self.last_successful_command.isoformat()
            if self.last_successful_command
            else None,
            "connection_attempts": self.connection_attempts,
            "successful_connections": self.successful_connections,
            "failed_connections": self.failed_connections,
            "response_times": self.response_times,
            "max_response_history": self.max_response_history,
        }
