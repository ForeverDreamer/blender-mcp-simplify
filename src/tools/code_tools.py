"""
Essential Blender Operations - Simplified Core Tools

Following CodeAct paradigm: emphasize execute-code for maximum flexibility
while maintaining essential utility functions.

All functions now use socket connection to communicate with Blender server.
"""

import json
import logging
import os
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from .utils import BlenderConnection, create_standard_response, send_command

logger = logging.getLogger(__name__)


def execute_code(
    code: str,
    host: str = "localhost",
    port: int = 9876,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """
    Execute arbitrary Python code in Blender context via socket connection.

    This function sends the code to the Blender server for execution instead of
    executing locally in the MCP server.

    Args:
        code: Python code to execute
        host: Blender server host (default: localhost)
        port: Blender server port (default: 9876)
        timeout: Connection timeout in seconds (default: 30.0)

    """
    try:
        if not code.strip():
            return create_standard_response(
                success=False,
                error="No code provided to execute",
            )

        # Create command for Blender server
        command = {
            "type": "execute_code",
            "params": {
                "code": code,
            },
        }

        # Create connection and send command
        connection = BlenderConnection(host=host, port=port, timeout=timeout)
        result = send_command(command, connection)

        # Check if the command was successful
        if not result.get("success", True):  # Default to True for compatibility
            return create_standard_response(
                success=False,
                error=result.get("error", "Unknown error from Blender server"),
                data=result.get("data", {}),
            )

        # Extract data from Blender server response
        blender_data = result.get("data", {})

        return create_standard_response(
            success=True,
            message="Code executed successfully in Blender",
            data={
                "execution_time_ms": blender_data.get("execution_time_ms", 0),
                "output": blender_data.get("output", ""),
                "errors": blender_data.get("errors", ""),
                "code_length": len(code),
                "blender_response": result,
            },
        )

    except Exception as e:
        return create_standard_response(
            success=False,
            error=f"Failed to execute code: {e!s}",
            data={
                "error_type": type(e).__name__,
            },
        )


def execute_script_file(
    script_name: str,
    parameters: dict[str, Any] | None = None,
    host: str = "localhost",
    port: int = 9876,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """
    Execute a Python script file from the scripts directory in Blender context via socket connection.

    This function sends the script execution command to the Blender server instead of
    executing locally in the MCP server.

    Args:
        script_name: Name of the script file (with or without .py extension)
        parameters: Optional parameters to pass to the script as globals
        host: Blender server host (default: localhost)
        port: Blender server port (default: 9876)
        timeout: Connection timeout in seconds (default: 60.0)

    """
    try:
        # Create command for Blender server
        command = {
            "type": "execute_script_file",
            "params": {
                "script_name": script_name,
                "parameters": parameters,
            },
        }

        # Create connection and send command
        connection = BlenderConnection(host=host, port=port, timeout=timeout)
        result = send_command(command, connection)

        # Check if the command was successful
        if not result.get("success", True):  # Default to True for compatibility
            return create_standard_response(
                success=False,
                error=result.get("error", "Unknown error from Blender server"),
                data=result.get("data", {}),
            )

        # Extract data from Blender server response
        blender_data = result.get("data", {})

        return create_standard_response(
            success=True,
            message=f"Script '{script_name}' executed successfully in Blender",
            data={
                "execution_time_ms": blender_data.get("execution_time_ms", 0),
                "output": blender_data.get("output", ""),
                "errors": blender_data.get("errors", ""),
                "script_info": blender_data.get("script_info", {}),
                "blender_response": result,
            },
        )

    except Exception as e:
        return create_standard_response(
            success=False,
            error=f"Failed to execute script '{script_name}': {e!s}",
            data={
                "script_name": script_name,
                "scripts_directory": scripts_directory,
                "error_type": type(e).__name__,
            },
        )


def list_available_scripts(
    scripts_directory: str = r"D:\data_files\mcps\blender-mcp-simplify\scripts",
) -> dict[str, Any]:
    """List all available Python scripts in the specified directory."""
    try:
        # This function can run locally since it's just listing files
        scripts = _list_available_scripts(scripts_directory)

        return create_standard_response(
            success=True,
            message=f"Found {len(scripts)} scripts in '{scripts_directory}' directory",
            data={
                "scripts_directory": scripts_directory,
                "scripts": scripts,
                "total_count": len(scripts),
            },
        )

    except Exception as e:
        return create_standard_response(
            success=False,
            error=f"Failed to list scripts: {e!s}",
            data={"scripts_directory": scripts_directory},
        )


def _list_available_scripts(scripts_directory: str) -> list[dict[str, Any]]:
    """Internal function to list available scripts."""
    scripts = []

    # Try to find the scripts directory
    workspace_root = os.getcwd()
    scripts_path = os.path.join(workspace_root, scripts_directory)

    # If not found, try relative to this module's location
    if not os.path.exists(scripts_path):
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        scripts_path = os.path.join(module_dir, scripts_directory)

    if not os.path.exists(scripts_path):
        return scripts

    # List all .py files
    for filename in os.listdir(scripts_path):
        if filename.endswith(".py") and not filename.startswith("_"):
            file_path = os.path.join(scripts_path, filename)
            try:
                file_stat = os.stat(file_path)

                # Try to read first few lines for description
                description = "No description available"
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read(500)  # Read first 500 chars
                        if '"""' in content:
                            start = content.find('"""') + 3
                            end = content.find('"""', start)
                            if end > start:
                                description = content[start:end].strip()
                except:
                    pass

                scripts.append(
                    {
                        "name": filename,
                        "size": file_stat.st_size,
                        "modified": file_stat.st_mtime,
                        "path": file_path,
                        "description": description[:200] + "..."
                        if len(description) > 200
                        else description,
                    },
                )
            except:
                pass

    return sorted(scripts, key=lambda x: x["name"])


# Script registration function for MCP tools
def register_code_tools(app: FastMCP) -> None:
    """Register script execution tools with FastMCP."""

    @app.tool()
    def execute_blender_code(
        ctx: Context,
        code: str,
    ) -> str:
        """
        Execute Python code in Blender context.

        Args:
            code: Python code to execute in Blender

        """
        result = execute_code(code)
        return json.dumps(result, indent=2)

    @app.tool()
    def execute_blender_script_file(
        ctx: Context,
        script_name: str,
        parameters: dict | None = None,
    ) -> str:
        """
        Execute a Python script file from the scripts directory in Blender.

        Args:
            script_name: Name of the script file (with or without .py extension)
            parameters: Optional parameters to pass to the script

        """
        result = execute_script_file(script_name, parameters)
        return json.dumps(result, indent=2)

    @app.tool()
    def list_blender_scripts(
        ctx: Context,
        scripts_directory: str = "D:\\data_files\\mcps\\blender-mcp-simplify\\scripts",
    ) -> str:
        """
        List all available Python scripts in the specified directory.

        Args:
            scripts_directory: Directory to search for scripts (default: "scripts")

        """
        result = list_available_scripts(scripts_directory)
        return json.dumps(result, indent=2)
