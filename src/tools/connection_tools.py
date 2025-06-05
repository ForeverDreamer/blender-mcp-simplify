"""
Connection monitoring tools for Blender MCP Server.

Provides MCP tools for checking connection status and monitoring performance.
"""

import json
from mcp.server.fastmcp import Context, FastMCP

from ..core import ConnectionManager


def register_connection_tools(app: FastMCP, connection_manager: ConnectionManager) -> None:
    """Register connection monitoring tools with the FastMCP app."""
    
    @app.tool()
    def check_connection_status(
        ctx: Context,
        host: str = "localhost",
        port: int = 9876,
    ) -> str:
        """
        检查与Blender的连接状态

        Args:
            host: Blender主机地址 (default: localhost)
            port: Blender端口 (default: 9876)

        Returns:
            连接状态信息的JSON字符串
        """
        status_info = connection_manager.get_detailed_status(host, port)
        return json.dumps(status_info, indent=2)

    @app.tool()
    def get_connection_statistics(ctx: Context) -> str:
        """
        获取连接统计信息

        Returns:
            连接统计信息的JSON字符串
        """
        stats = connection_manager.get_connection_statistics()
        return json.dumps(stats, indent=2)

    @app.tool()
    def reset_connection_statistics(ctx: Context) -> str:
        """
        重置连接统计信息

        Returns:
            操作结果的JSON字符串
        """
        result = connection_manager.reset_statistics()
        return json.dumps(result, indent=2) 