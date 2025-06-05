"""
Blender MCP Server - Simplified Architecture

Streamlined design focusing on execute-code approach with essential tools only.
Following best practices from CodeAct paradigm and latest MCP standards.
"""

import logging

from mcp.server.fastmcp import FastMCP

# Import core infrastructure
from .core import ConnectionManager, ExecutionResultManager

# Import modular MCP tools
from .tools.mcp_tools import register_all_tools
from .tools.script_registry import (
    ScriptRegistry,
    create_scene_template_scripts,
    register_all_scripts,
)

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
        # Initialize FastMCP app
        self.app = FastMCP("Blender MCP Server")

        # Initialize core infrastructure
        self.connection_manager = ConnectionManager()
        self.execution_manager = ExecutionResultManager()

        # Initialize script registry
        self.script_registry = ScriptRegistry()

        # Setup registries
        self._setup_script_registry()

        # Register all MCP tools
        self._register_tools()

        logger.info("Simplified Blender MCP Server initialized successfully")

    def _setup_script_registry(self):
        """Initialize and populate essential script registries only."""
        try:
            # Register core scripts only
            register_all_scripts(self.script_registry)
            create_scene_template_scripts(self.script_registry)

            logger.info(
                f"Successfully initialized simplified script registry with "
                f"{len(self.script_registry._scripts)} essential scripts and ",
            )

        except Exception as e:
            logger.error(f"Failed to initialize script registry: {e}")
            raise

    def _register_tools(self):
        """Register essential MCP tools with the FastMCP app."""
        try:
            register_all_tools(
                app=self.app,
                connection_manager=self.connection_manager,
                execution_manager=self.execution_manager,
            )

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
