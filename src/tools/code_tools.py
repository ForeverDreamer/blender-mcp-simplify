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

        # Check if the command was successful - support both "success" and "status" fields
        success = result.get("success", result.get("status") == "success")
        if not success:
            return create_standard_response(
                success=False,
                error=result.get("error", "Unknown error from Blender server"),
                data=result.get("data", {}),
            )

        # Extract data from Blender server response
        blender_data = result.get("data", {})
        
        # Handle different response formats
        if "result" in blender_data:
            # New format from Blender addon
            output = blender_data.get("result", "")
            errors = ""
            execution_time_ms = 0
        else:
            # Legacy format
            output = blender_data.get("output", "")
            errors = blender_data.get("errors", "")
            execution_time_ms = blender_data.get("execution_time_ms", 0)

        return create_standard_response(
            success=True,
            message="Code executed successfully in Blender",
            data={
                "execution_time_ms": execution_time_ms,
                "output": output,
                "errors": errors,
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
    script_path: str,
    parameters: dict[str, Any] | None = None,
    host: str = BLENDER_HOST,
    port: int = BLENDER_PORT,
    timeout: float = BLENDER_TIMEOUT,
) -> dict[str, Any]:
    """
    Execute a Python script file from the scripts directory in Blender context via socket connection.
    Enhanced with improved JSON handling to prevent serialization errors.

    This function sends the script execution command to the Blender server instead of
    executing locally in the MCP server. Now accepts relative paths within the scripts directory.

    Args:
        script_path: Relative path to the script file within the scripts directory (with or without .py extension)
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
                "script_name": script_path,
                "parameters": parameters,
            },
        }

        # Pre-validate JSON serialization to catch issues early
        try:
            test_json = safe_json_dumps(command)
            logger.debug(f"JSON serialization test passed for script '{script_path}'")
        except ValueError as e:
            return create_standard_response(
                success=False,
                error=f"Script parameters contain characters that cannot be safely serialized: {e}",
                data={
                    "script_path": script_path,
                    "error_type": "json_serialization_error",
                },
            )

        # Create connection and send command
        connection = BlenderConnection(host=host, port=port, timeout=timeout)
        result = send_command(command, connection)

        # Check if the command was successful - support both "success" and "status" fields
        success = result.get("success", result.get("status") == "success")
        if not success:
            return create_standard_response(
                success=False,
                error=result.get("error", "Unknown error from Blender server"),
                data=result.get("data", {}),
            )

        # Extract data from Blender server response
        blender_data = result.get("data", {})
        
        # Handle different response formats
        if "result" in blender_data:
            # New format from Blender addon
            output = blender_data.get("result", "")
            errors = ""
            execution_time_ms = 0
        else:
            # Legacy format
            output = blender_data.get("output", "")
            errors = blender_data.get("errors", "")
            execution_time_ms = blender_data.get("execution_time_ms", 0)

        return create_standard_response(
            success=True,
            message=f"Script '{script_path}' executed successfully in Blender",
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
            error=f"Failed to execute script '{script_path}': {e!s}",
            data={
                "script_path": script_path,
                "error_type": type(e).__name__,
            },
        )






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
        script_path: str,
        parameters: dict | None = None,
    ) -> str:
        """
        Execute a Python script file from the scripts directory in Blender.

        该工具可以在Blender中执行预定义的Python脚本文件，支持传递相对路径，允许运行更复杂的操作。
        脚本文件应位于配置的scripts根目录中，支持子目录组织。

        📁 目录结构:
        脚本根目录（默认为 /home/doer/data_files/video_scripts）下可以有以下结构：
        ```
        video_scripts/
        ├── basic/
        │   ├── create_cube.py
        │   └── add_material.py
        ├── advanced/
        │   ├── character_generator.py
        │   └── scene_builder.py
        └── utils/
            └── common_functions.py
        ```

        💡 推荐使用场景:
        1. **超长代码**: 当代码超过3000个字符时，建议保存为脚本文件执行
        2. **复杂逻辑**: 包含大量函数定义、类定义或复杂算法的代码
        3. **可重用代码**: 需要多次执行的标准化操作
        4. **参数化操作**: 需要根据不同参数执行相似操作的场景
        5. **项目组织**: 使用子目录来组织不同类型的脚本

        Args:
            script_path: 脚本文件的相对路径（相对于scripts根目录），可以包含子目录。
                        例如："create_landscape.py"、"basic/create_cube.py"、"advanced/character_generator.py"
            parameters: 传递给脚本的可选参数字典。这些参数将作为全局变量在脚本中可用。

        Returns:
            一个JSON字符串，包含执行结果、输出、错误信息（如果有）和执行时间。

        Examples:
            基本脚本执行:
            ```python
            # 执行根目录下的脚本
            execute_blender_script_file(ctx, "create_landscape.py")
            
            # 或者不带.py扩展名
            execute_blender_script_file(ctx, "create_landscape")
            ```

            子目录脚本执行:
            ```python
            # 执行子目录中的脚本
            execute_blender_script_file(ctx, "basic/create_cube.py")
            execute_blender_script_file(ctx, "advanced/character_generator.py")
            execute_blender_script_file(ctx, "utils/common_functions.py")
            ```

            带参数的脚本执行:
            ```python
            # 执行带参数的脚本
            execute_blender_script_file(ctx,
                "advanced/character_generator.py",
                {
                    "character_type": "warrior",
                    "height": 1.8,
                    "add_armor": True,
                    "weapon_type": "sword"
                }
            )
            ```

            视频制作脚本示例:
            ```python
            # 创建基础场景
            execute_blender_script_file(ctx, "video/setup_scene.py", {
                "resolution": [1920, 1080],
                "frame_rate": 30
            })
            
            # 添加角色动画
            execute_blender_script_file(ctx, "video/animate_character.py", {
                "animation_type": "walk_cycle",
                "duration": 120  # 帧数
            })
            
            # 设置渲染
            execute_blender_script_file(ctx, "video/setup_render.py", {
                "output_path": "/home/doer/output/",
                "quality": "high"
            })
            ```

            复杂项目脚本示例:
            ```python
            # 建筑可视化项目
            execute_blender_script_file(ctx, "architecture/generate_building.py", {
                "building_type": "residential",
                "floors": 3,
                "style": "modern",
                "add_furniture": True
            })
            
            # 自然环境生成
            execute_blender_script_file(ctx, "nature/create_landscape.py", {
                "terrain_size": [100, 100],
                "tree_density": 0.3,
                "add_water": True
            })
            ```

            脚本中参数访问示例:
            ```python
            # 在脚本文件中这样访问传递的参数
            character_type = globals().get("character_type", "default")
            height = globals().get("height", 1.7)
            add_armor = globals().get("add_armor", False)
            weapon_type = globals().get("weapon_type", "none")
            
            # 对于复杂参数
            resolution = globals().get("resolution", [1920, 1080])
            terrain_size = globals().get("terrain_size", [50, 50])
            output_path = globals().get("output_path", "/tmp/")
            ```

            错误处理示例:
            ```python
            # 如果脚本不存在，会返回详细的错误信息
            result = execute_blender_script_file(ctx, "nonexistent/script.py")
            # 检查结果中的错误信息来诊断问题
            ```

        """
        result = execute_script_file(script_path, parameters)
        return json.dumps(result, indent=2)

