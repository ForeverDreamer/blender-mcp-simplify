"""
Blender MCP Server - Simplified Architecture

Streamlined design focusing on execute-code approach with essential tools only.
Following best practices from CodeAct paradigm and latest MCP standards.
"""

import logging

from mcp.server.fastmcp import FastMCP

from .prompts import register_prompts
from .resources import register_resources

# Import modular MCP tools
from .tools.all_tools import register_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("BlenderMCPServer")


class BlenderMCPServer:
    """
    Simplified Blender MCP Server focusing on execute-code approach.

    Follows CodeAct paradigm with minimal predefined tools for maximum flexibility.
    """

    def __init__(self):
        # Initialize FastMCP app with detailed instructions
        self.app = FastMCP(
            name="Blender MCP Server",
            instructions="""
            这是一个用于Blender的MCP服务器，提供以下功能：
            
            1. 执行Blender Python代码 - 使用execute_blender_code工具可以运行任意Python代码
            2. 执行预定义脚本 - 使用execute_blender_script_file可以运行服务器上的脚本文件
            3. 获取场景信息 - 使用get_blender_scene_info可以获取当前场景的详细信息
            4. 获取服务器状态 - 使用get_blender_server_status可以检查服务器状态
            5. PolyHaven资源集成 - 搜索和下载高质量的3D资源
            
            此外，服务器还提供了一系列预定义的资源模板和提示模板，可以帮助您更高效地使用Blender进行建模、渲染和动画制作。
            
            使用resources://list可以查看所有可用的资源
            使用prompts://list可以查看所有可用的提示模板
            """,
        )

        # Register all MCP tools
        self._register_tools()

        # 直接注册资源和提示
        try:
            register_resources(self.app)
            logger.info("成功注册资源模块")

            register_prompts(self.app)
            logger.info("成功注册提示模块")
        except Exception as e:
            logger.error(f"注册资源或提示模块失败: {e}")
            raise

        logger.info("Simplified Blender MCP Server initialized successfully")

    def _register_tools(self):
        """Register essential MCP tools with the FastMCP app."""
        try:
            register_all_tools(app=self.app)

            logger.info("Successfully registered essential MCP tools")

        except Exception as e:
            logger.error(f"Failed to register MCP tools: {e}")
            raise

    def run(self):
        """Start the MCP server."""
        try:
            logger.info("Starting Simplified Blender MCP Server...")
            self.app.run()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


def main():
    """Main entry point for the Blender MCP Server."""
    try:
        server = BlenderMCPServer()
        server.run()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1
    return 0


if __name__ == "__main__":
    main()
