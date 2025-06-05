"""
Essential Blender Operations - Simplified Core Tools

Following CodeAct paradigm: emphasize execute-code for maximum flexibility
while maintaining essential utility functions.

All functions now use socket connection to communicate with Blender server.
"""

import ast
import json
import logging
import os
import sys
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

try:
    from ..core.connection_manager import ConnectionManager
    from ..core.types import BlenderConnection
    from .utils import create_standard_response
except ImportError:
    # Fallback for direct imports during development
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.connection_manager import ConnectionManager
    from core.types import BlenderConnection
    from tools.utils import create_standard_response

logger = logging.getLogger(__name__)

# Global connection manager instance
_connection_manager = ConnectionManager()

# Security configurations
EXECUTION_TIMEOUT = 30  # seconds
MAX_OUTPUT_LENGTH = 10000  # characters
DANGEROUS_MODULES = {
    "subprocess",
    "os",
    "sys",
    "importlib",
    "pickle",
    "marshal",
    "builtins",
    "__builtin__",
    "eval",
    "exec",
    "compile",
    "open",
}

# Code templates for common Blender operations
CODE_TEMPLATES = {
    "create_cube": """
import bpy

# Create a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "ProgrammaticCube"

print(f"Created cube: {cube.name}")
""",
    "create_animation": """
import bpy

# Get the active object
obj = bpy.context.active_object
if obj:
# Clear existing animation
obj.animation_data_clear()

    # Set keyframes for rotation
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert(data_path="rotation_euler", frame=1)
    
    obj.rotation_euler = (0, 0, 6.28)  # 360 degrees
    obj.keyframe_insert(data_path="rotation_euler", frame=100)
    
    print(f"Added animation to {obj.name}")
else:
    print("No active object to animate")
""",
    "setup_material": """
import bpy

# Get the active object
obj = bpy.context.active_object
if obj and obj.type == 'MESH':
    # Create a new material
    mat = bpy.data.materials.new(name="ProgrammaticMaterial")
    mat.use_nodes = True
    
    # Get the principled BSDF node
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.8, 0.2, 0.2, 1.0)  # Red
    bsdf.inputs["Metallic"].default_value = 0.7
    bsdf.inputs["Roughness"].default_value = 0.3
    
    # Assign material to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    print(f"Applied material to {obj.name}")
else:
    print("No mesh object selected")
""",
    "render_frame": """
import bpy

# Set render settings
scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100

# Render current frame
bpy.ops.render.render(write_still=True)
print("Rendered current frame")
""",
    "list_objects": """
import bpy

# List all objects in the scene
scene = bpy.context.scene
print(f"Scene: {scene.name}")
print(f"Total objects: {len(scene.objects)}")

for obj in scene.objects:
    print(f"- {obj.name} ({obj.type}) at {obj.location}")
""",
}


def _validate_code_security(code: str) -> tuple[bool, str]:
    """
    Validate code for security issues.

    Returns:
        (is_safe, error_message)

    """
    try:
        # Parse code to AST for analysis
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    # Check for dangerous imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in DANGEROUS_MODULES:
                    return False, f"Dangerous import detected: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module in DANGEROUS_MODULES:
                return False, f"Dangerous import detected: {node.module}"
        elif isinstance(node, ast.Call):
            # Check for dangerous function calls
            if isinstance(node.func, ast.Name):
                if node.func.id in ["eval", "exec", "compile", "__import__"]:
                    return False, f"Dangerous function call: {node.func.id}"

    return True, ""


def execute_code(
    code: str,
    template: str | None = None,
    safe_mode: bool = True,
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
        template: Optional template name to use as base code
        safe_mode: Enable security validations (default: True)
        host: Blender server host (default: localhost)
        port: Blender server port (default: 9876)
        timeout: Connection timeout in seconds (default: 30.0)

    """
    try:
        # Handle template usage
        if template:
            if template in CODE_TEMPLATES:
                if code.strip():
                    # Combine template with additional code
                    full_code = (
                        CODE_TEMPLATES[template] + "\n\n# Additional code:\n" + code
                    )
                else:
                    full_code = CODE_TEMPLATES[template]
            else:
                return create_standard_response(
                    success=False,
                    error=f"Unknown template '{template}'. Available templates: {list(CODE_TEMPLATES.keys())}",
                    data={"available_templates": list(CODE_TEMPLATES.keys())},
                )
        else:
            full_code = code

        if not full_code.strip():
            return create_standard_response(
                success=False,
                error="No code provided to execute",
            )

        # Security validation (basic check on MCP server side)
        if safe_mode:
            is_safe, security_error = _validate_code_security(full_code)
            if not is_safe:
                return create_standard_response(
                    success=False,
                    error=f"Security validation failed: {security_error}",
                    data={"code_analysis": {"safe": False, "reason": security_error}},
                )

        # Create command for Blender server
        command = {
            "type": "execute_code",
            "params": {
                "code": full_code,
                "safe_mode": safe_mode,
                "template": template,
            },
        }

        # Create connection and send command
        connection = BlenderConnection(host=host, port=port, timeout=timeout)
        result = _connection_manager.send_command(command, connection)

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
                "template_used": template,
                "code_length": len(full_code),
                "safe_mode": safe_mode,
                "blender_response": result,
            },
        )

    except Exception as e:
        return create_standard_response(
            success=False,
            error=f"Failed to execute code: {e!s}",
            data={
                "error_type": type(e).__name__,
                "template": template,
                "safe_mode": safe_mode,
            },
        )


def get_code_templates() -> dict[str, Any]:
    """Get available code templates for common Blender operations."""
    try:
        templates_info = {}
        for name, code in CODE_TEMPLATES.items():
            # Analyze template for description
            description = "No description available"
            lines = code.split("\n")
            for line in lines:
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    # Try to extract docstring
                    docstring_lines = []
                    in_docstring = False
                    for doc_line in lines:
                        if doc_line.strip().startswith(
                            '"""',
                        ) or doc_line.strip().startswith("'''"):
                            if in_docstring:
                                break
                            in_docstring = True
                            continue
                        if in_docstring:
                            docstring_lines.append(doc_line.strip())
                    if docstring_lines:
                        description = " ".join(docstring_lines[:2])  # First 2 lines
                    break

            templates_info[name] = {
                "description": description,
                "code_preview": code[:200] + "..." if len(code) > 200 else code,
                "line_count": len(code.split("\n")),
                "estimated_complexity": ("Simple" if len(code) < 500 else "Complex"),
            }

        return create_standard_response(
            success=True,
            message=f"Retrieved {len(CODE_TEMPLATES)} code templates",
            data={
                "templates": templates_info,
                "total_count": len(CODE_TEMPLATES),
                "template_names": list(CODE_TEMPLATES.keys()),
            },
        )

    except Exception as e:
        return create_standard_response(
            success=False,
            error=f"Failed to get code templates: {e!s}",
        )


def execute_script_file(
    script_name: str,
    scripts_directory: str = "scripts",
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
        scripts_directory: Directory containing scripts (relative to workspace root)
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
                "scripts_directory": scripts_directory,
                "parameters": parameters,
            },
        }

        # Create connection and send command
        connection = BlenderConnection(host=host, port=port, timeout=timeout)
        result = _connection_manager.send_command(command, connection)

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


def list_available_scripts(scripts_directory: str = "scripts") -> dict[str, Any]:
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
def register_script_execution_tools(app: FastMCP) -> None:
    """Register script execution tools with FastMCP."""

    @app.tool()
    def execute_blender_code(
        ctx: Context,
        code: str,
        template: str | None = None,
        safe_mode: bool = True,
    ) -> str:
        """
        Execute Python code in Blender context.

        Args:
            code: Python code to execute in Blender
            template: Optional template name (create_cube, create_animation, setup_material, render_frame, list_objects)
            safe_mode: Enable security validations

        """
        result = execute_code(code, template, safe_mode)
        return json.dumps(result, indent=2)

    @app.tool()
    def get_blender_code_templates(ctx: Context) -> str:
        """
        Get available code templates for common Blender operations.
        """
        result = get_code_templates()
        return json.dumps(result, indent=2)

    @app.tool()
    def execute_blender_script_file(
        ctx: Context,
        script_name: str,
        scripts_directory: str = "scripts",
        parameters: dict | None = None,
    ) -> str:
        """
        Execute a Python script file from the scripts directory in Blender.

        Args:
            script_name: Name of the script file (with or without .py extension)
            scripts_directory: Directory containing scripts (default: "scripts")
            parameters: Optional parameters to pass to the script

        """
        result = execute_script_file(script_name, scripts_directory, parameters)
        return json.dumps(result, indent=2)

    @app.tool()
    def list_blender_scripts(
        ctx: Context,
        scripts_directory: str = "scripts",
    ) -> str:
        """
        List all available Python scripts in the specified directory.

        Args:
            scripts_directory: Directory to search for scripts (default: "scripts")

        """
        result = list_available_scripts(scripts_directory)
        return json.dumps(result, indent=2)
