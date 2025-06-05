"""
Core infrastructure modules for Blender MCP Server.

This module contains the fundamental components for connection management,
execution tracking, and shared utilities.
"""

try:
    from .connection_manager import ConnectionManager
    from .execution_manager import ExecutionResultManager
    from .types import BlenderConnection

    __all__ = [
        "BlenderConnection",
        "ConnectionManager",
        "ExecutionResultManager",
    ]
except ImportError:
    # Graceful fallback if modules are not yet available
    __all__ = []
