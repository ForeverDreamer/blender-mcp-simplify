"""
MCP Tools registration for Blender MCP Server.

This module provides unified tool registration functionality.
"""

from mcp.server.fastmcp import FastMCP

from .base_tools import register_base_tools
from .code_tools import register_code_tools
from .polyhaven_tools import register_polyhaven_tools


def register_all_tools(app: FastMCP) -> None:
    """向 FastMCP 注册基本 MCP 工具。"""
    register_base_tools(app)
    register_code_tools(app)
    register_polyhaven_tools(app)
