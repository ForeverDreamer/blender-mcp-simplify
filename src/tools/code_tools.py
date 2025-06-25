"""
Essential Blender Operations - Simplified Core Tools

Following CodeAct paradigm: emphasize execute-code for maximum flexibility
while maintaining essential utility functions.

All functions now use socket connection to communicate with Blender server.
Enhanced with improved JSON handling to fix "Invalid JSON: Unterminated string" errors.
"""

import json
import logging
import os
import sys
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from .utils import (
    BlenderConnection,
    create_standard_response,
    safe_json_dumps,
    send_command,
)

# 添加配置导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import BLENDER_HOST, BLENDER_PORT, BLENDER_TIMEOUT

logger = logging.getLogger(__name__)


def execute_code(
    code: str,
    host: str = BLENDER_HOST,
    port: int = BLENDER_PORT,
    timeout: float = BLENDER_TIMEOUT,
) -> dict[str, Any]:
    """
    Execute arbitrary Python code in Blender context via socket connection.
    Enhanced with improved JSON handling to prevent serialization errors.

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

        # Pre-validate JSON serialization to catch issues early
        try:
            test_json = safe_json_dumps(command)
            logger.debug(f"JSON serialization test passed, length: {len(test_json)}")
        except ValueError as e:
            return create_standard_response(
                success=False,
                error=f"Code contains characters that cannot be safely serialized: {e}",
                data={
                    "code_length": len(code),
                    "error_type": "json_serialization_error",
                },
            )

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
    host: str = BLENDER_HOST,
    port: int = BLENDER_PORT,
    timeout: float = BLENDER_TIMEOUT,
) -> dict[str, Any]:
    """
    Execute a Python script file from the scripts directory in Blender context via socket connection.
    Enhanced with improved JSON handling to prevent serialization errors.

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

        # Pre-validate JSON serialization to catch issues early
        try:
            test_json = safe_json_dumps(command)
            logger.debug(f"JSON serialization test passed for script '{script_name}'")
        except ValueError as e:
            return create_standard_response(
                success=False,
                error=f"Script parameters contain characters that cannot be safely serialized: {e}",
                data={
                    "script_name": script_name,
                    "error_type": "json_serialization_error",
                },
            )

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

        ⚠️ 重要提示和最佳实践:
        1. **代码长度限制**: 建议单次执行的代码长度不超过3000个字符。超长代码可能导致传输错误。
        2. **复杂任务分段**: 对于复杂的多步骤操作，建议分成多个较小的代码块分别执行。
        3. **使用脚本文件**: 对于超长或复杂的代码，建议保存为.py文件并使用execute_blender_script_file工具执行。
        4. **字符处理**: 工具已优化处理包含特殊字符（如嵌套引号、反斜杠）的代码，但仍建议避免过度复杂的字符串操作。
        5. **错误处理**: 如遇到"Invalid JSON"错误，请尝试将代码分段执行或简化字符串处理。

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

            分段执行复杂任务（推荐方式）:
            ```python
            # 第一步：设置场景和对象
            execute_blender_code(ctx, '''
            import bpy

            # 清理场景
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()

            # 创建主要对象
            bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
            cube = bpy.context.active_object
            cube.name = "AnimatedCube"
            ''')

            # 第二步：设置材质
            execute_blender_code(ctx, '''
            import bpy

            obj = bpy.data.objects.get("AnimatedCube")
            if obj:
                mat = bpy.data.materials.new(name="AnimatedMaterial")
                mat.use_nodes = True
                obj.data.materials.append(mat)
            ''')

            # 第三步：设置动画
            execute_blender_code(ctx, '''
            import bpy

            obj = bpy.data.objects.get("AnimatedCube")
            if obj:
                scene = bpy.context.scene
                scene.frame_set(1)
                obj.location = (0, 0, 0)
                obj.keyframe_insert(data_path="location")

                scene.frame_set(60)
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

        ⚠️ 重要：使用前必须完成的步骤:
        1. **拷贝脚本文件**: 将要执行的.py脚本文件拷贝到 "D:\\data_files\\mcps\\blender-mcp-simplify\\scripts" 目录
        2. **验证文件存在**: 使用 list_blender_scripts 工具检查脚本是否已成功拷贝到目录中
        3. **执行脚本**: 使用正确的脚本名称（不包含路径）调用此工具
        4. **清理文件**: 执行完成后，删除临时拷贝的脚本文件以保持目录整洁

        💡 推荐使用场景:
        1. **超长代码**: 当代码超过3000个字符时，建议保存为脚本文件执行
        2. **复杂逻辑**: 包含大量函数定义、类定义或复杂算法的代码
        3. **可重用代码**: 需要多次执行的标准化操作
        4. **参数化操作**: 需要根据不同参数执行相似操作的场景

        Args:
            script_name: 脚本文件名称（仅文件名，不包含路径，可以带或不带.py扩展名）。例如："create_landscape.py"或"create_landscape"
            parameters: 传递给脚本的可选参数字典。这些参数将作为全局变量在脚本中可用。

        Returns:
            一个JSON字符串，包含执行结果、输出、错误信息（如果有）和执行时间。

        Examples:
            完整工作流程示例:
            ```python
            # 步骤1: 首先拷贝脚本文件到指定目录
            # 手动操作：将 my_script.py 拷贝到 "D:\\data_files\\mcps\\blender-mcp-simplify\\scripts" 目录

            # 步骤2: 验证脚本文件是否存在
            list_blender_scripts(ctx)  # 检查脚本列表，确认 my_script.py 存在

            # 步骤3: 执行脚本
            execute_blender_script_file(ctx, "my_script")

            # 步骤4: 执行完成后删除临时脚本文件
            # 手动操作：从 scripts 目录删除 my_script.py
            ```

            带参数的完整流程:
            ```python
            # 步骤1: 拷贝 character_creator.py 到 scripts 目录

            # 步骤2: 验证文件
            list_blender_scripts(ctx)

            # 步骤3: 执行带参数的脚本
            execute_blender_script_file(ctx,
                "character_creator",
                {
                    "character_type": "warrior",
                    "height": 1.8,
                    "add_armor": True
                }
            )

            # 步骤4: 清理文件
            # 删除 character_creator.py
            ```

            ❌ 错误示例（会导致"Script not found"错误）:
            ```python
            # 错误：直接使用路径，未拷贝到scripts目录
            execute_blender_script_file(ctx, "projects/example/entry.py")  # ❌ 错误

            # 正确：先拷贝文件，然后只使用文件名
            # 1. 拷贝 entry.py 到 scripts 目录
            # 2. 验证: list_blender_scripts(ctx)
            # 3. 执行: execute_blender_script_file(ctx, "entry.py")  # ✅ 正确
            ```

            复杂诊断脚本示例:
            ```python
            # 对于超长代码（如Animation Nodes诊断），推荐流程：

            # 步骤1: 创建诊断脚本文件 animation_diagnosis.py 并拷贝到scripts目录
            # 步骤2: 验证
            list_blender_scripts(ctx)

            # 步骤3: 执行诊断
            execute_blender_script_file(ctx,
                "animation_diagnosis",
                {
                    "target_object": "AnimatedCube",
                    "debug_level": "detailed",
                    "frame_to_check": 10
                }
            )

            # 步骤4: 获取结果后删除诊断脚本
            ```

            注意: 脚本中应包含适当的错误处理，并且应该在globals()命名空间中查找传递的参数:
            ```python
            # 脚本中访问参数的示例
            character_type = globals().get("character_type", "default")
            height = globals().get("height", 1.7)
            add_armor = globals().get("add_armor", False)

            # 对于复杂参数的处理
            target_object = globals().get("target_object", "Cube")
            debug_level = globals().get("debug_level", "basic")
            frame_to_check = globals().get("frame_to_check", 1)
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

        🔍 重要用途:
        1. **验证脚本存在**: 在使用 execute_blender_script_file 之前，验证脚本文件是否已正确拷贝到 scripts 目录
        2. **检查脚本信息**: 查看脚本的名称、大小、修改时间和描述信息
        3. **管理脚本库**: 了解可用的脚本资源，便于选择合适的脚本执行
        4. **调试目录问题**: 当 execute_blender_script_file 报告"Script not found"错误时，用此工具确认文件位置

        Args:
            scripts_directory: 要搜索脚本的目录（默认为scripts目录）。可以是相对于工作目录的路径或绝对路径。

        Returns:
            一个JSON字符串，包含可用脚本的列表及其元数据。

        Examples:
            在执行脚本前验证文件存在:
            ```python
            # 步骤1: 手动拷贝 my_script.py 到 scripts 目录

            # 步骤2: 验证脚本是否存在
            result = list_blender_scripts(ctx)
            # 检查输出中是否包含 my_script.py

            # 步骤3: 如果脚本存在，则执行
            execute_blender_script_file(ctx, "my_script")
            ```

            调试脚本未找到的问题:
            ```python
            # 当 execute_blender_script_file 报错时，先检查脚本目录
            scripts = list_blender_scripts(ctx)
            # 查看输出，确认：
            # 1. 目录路径是否正确
            # 2. 脚本文件是否在列表中
            # 3. 文件名拼写是否正确
            ```

            管理脚本库:
            ```python
            # 查看所有可用脚本
            import json

            result = list_blender_scripts(ctx)
            scripts_data = json.loads(result)

            if scripts_data["success"]:
                scripts = scripts_data["data"]["scripts"]
                print(f"找到 {len(scripts)} 个脚本:")

                for script in scripts:
                    name = script['name']
                    desc = script['description'][:100] + "..." if len(script['description']) > 100 else script['description']
                    print(f"- {name}: {desc}")
            ```

            检查特定脚本:
            ```python
            # 查找特定脚本文件
            result = list_blender_scripts(ctx)
            scripts_data = json.loads(result)

            target_script = "animation_diagnosis.py"
            found = any(script['name'] == target_script for script in scripts_data["data"]["scripts"])

            if found:
                print(f"✅ 脚本 {target_script} 已存在，可以执行")
                execute_blender_script_file(ctx, "animation_diagnosis")
            else:
                print(f"❌ 脚本 {target_script} 未找到，请先拷贝到 scripts 目录")
            ```

        """
        result = list_available_scripts(scripts_directory)
        return json.dumps(result, indent=2)
