"""
MCP Tools registration for Blender MCP Server.

This module provides unified tool registration functionality.
"""

from mcp.server.fastmcp import FastMCP

try:
    from src.core import ConnectionManager, ExecutionResultManager
except ImportError:
    # Fallback for different import contexts
    try:
        from core import ConnectionManager, ExecutionResultManager
    except ImportError:
        # Mock for testing
        ConnectionManager = None
        ExecutionResultManager = None

from .base_operations import register_script_execution_tools
from .connection_tools import register_connection_tools
from .polyhaven_tools import register_polyhaven_tools


def register_all_tools(
    app: FastMCP,
    connection_manager,
    execution_manager,
) -> None:
    """Register essential MCP tools with the FastMCP app."""
    # Register connection monitoring tools
    register_connection_tools(app, connection_manager)

    # Register PolyHaven integration tools
    register_polyhaven_tools(app)

    # Register script execution tools (from base_operations)
    register_script_execution_tools(app)
