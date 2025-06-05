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

        该工具允许您执行任意Python代码直接在Blender中运行，提供完全的灵活性来创建、修改和操作3D对象、材质、动画和渲染设置。
        代码在Blender的Python解释器中执行，可访问完整的Blender Python API (bpy)。

        Args:
            code: 要在Blender中执行的Python代码。可以包含多行代码，用于创建对象、修改材质、设置动画关键帧等。

        Returns:
            一个JSON字符串，包含执行结果、输出、错误信息（如果有）和执行时间。

        Examples:
            基本操作:
            ```python
            # 创建一个简单的立方体
            execute_blender_code(ctx, '''
            import bpy

            # 创建一个立方体
            bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))

            # 给立方体命名
            cube = bpy.context.active_object
            cube.name = "MyCube"
            ''')
            ```

            材质操作:
            ```python
            # 为对象添加红色材质
            execute_blender_code(ctx, '''
            import bpy

            # 选择目标对象（假设已存在名为"MyCube"的对象）
            obj = bpy.data.objects.get("MyCube")
            if obj:
                # 创建新材质
                mat = bpy.data.materials.new(name="RedMaterial")
                mat.use_nodes = True

                # 设置基础颜色为红色
                principled_bsdf = mat.node_tree.nodes.get('Principled BSDF')
                if principled_bsdf:
                    principled_bsdf.inputs[0].default_value = (1.0, 0.0, 0.0, 1.0)

                # 分配材质到对象
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
            ''')
            ```

            动画操作:
            ```python
            # 为对象创建简单的动画
            execute_blender_code(ctx, '''
            import bpy

            # 选择对象
            obj = bpy.data.objects.get("MyCube")
            if obj:
                # 设置场景帧范围
                scene = bpy.context.scene
                scene.frame_start = 1
                scene.frame_end = 60

                # 在第1帧设置关键帧
                scene.frame_current = 1
                obj.location = (0, 0, 0)
                obj.keyframe_insert(data_path="location")

                # 在第60帧设置关键帧
                scene.frame_current = 60
                obj.location = (0, 0, 5)
                obj.keyframe_insert(data_path="location")
            ''')
            ```

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

        该工具可以在Blender中执行预定义的Python脚本文件，允许运行更复杂的操作，而无需直接输入大量代码。
        脚本文件应位于指定的scripts目录中，可以选择传递参数以影响脚本行为。

        Args:
            script_name: 脚本文件名称（可以带或不带.py扩展名）。例如："create_landscape.py"或"create_landscape"
            parameters: 传递给脚本的可选参数字典。这些参数将作为全局变量在脚本中可用。

        Returns:
            一个JSON字符串，包含执行结果、输出、错误信息（如果有）和执行时间。

        Examples:
            基本用法:
            ```python
            # 执行create_landscape.py脚本
            execute_blender_script_file(ctx, "create_landscape")
            ```

            带参数的用法:
            ```python
            # 执行create_character.py脚本并传递参数
            execute_blender_script_file(ctx,
                "create_character",
                {
                    "character_type": "warrior",
                    "height": 1.8,
                    "add_armor": True
                }
            )
            ```

            注意: 脚本中应包含适当的错误处理，并且应该在globals()命名空间中查找传递的参数:
            ```python
            # 脚本中访问参数的示例
            character_type = globals().get("character_type", "default")
            height = globals().get("height", 1.7)
            add_armor = globals().get("add_armor", False)
            ```

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

        该工具会列出指定目录中所有可用的Python脚本文件，包括它们的名称、描述、大小和修改时间。
        这对于了解可用的脚本以及选择要执行的脚本非常有用。

        Args:
            scripts_directory: 要搜索脚本的目录（默认为"scripts"）。可以是相对于工作目录的路径或绝对路径。

        Returns:
            一个JSON字符串，包含可用脚本的列表及其元数据。

        Examples:
            列出默认目录中的脚本:
            ```python
            # 获取默认scripts目录中的所有脚本
            scripts = list_blender_scripts(ctx)
            ```

            列出自定义目录中的脚本:
            ```python
            # 获取自定义目录中的所有脚本
            scripts = list_blender_scripts(ctx, "D:\\my_blender_scripts")
            ```

            使用脚本列表结果:
            ```python
            # 获取脚本列表并分析结果
            import json

            result = list_blender_scripts(ctx)
            scripts_data = json.loads(result)

            if scripts_data["success"]:
                scripts = scripts_data["data"]["scripts"]
                print(f"找到 {len(scripts)} 个脚本:")

                for script in scripts:
                    print(f"- {script['name']}: {script['description']}")
            ```

        """
        result = list_available_scripts(scripts_directory)
        return json.dumps(result, indent=2)
