"""
基础 Blender 工具 - 提供核心功能

遵循 CodeAct 范式：强调 execute-code 方法以获得最大灵活性，
同时保持基本实用功能。

所有函数现在都使用 socket 连接与 Blender 服务器通信。
"""

import json
import logging
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from .utils import BlenderConnection, create_standard_response, send_command

logger = logging.getLogger(__name__)


def get_scene_info(
    host: str = "localhost",
    port: int = 9876,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """
    从 Blender 获取当前场景信息。

    此函数发送 get_scene_info 命令到 Blender 服务器以获取场景信息。

    Args:
        host: Blender 服务器主机 (默认: localhost)
        port: Blender 服务器端口 (默认: 9876)
        timeout: 连接超时（秒） (默认: 5.0)

    Returns:
        包含场景信息的字典

    """
    try:
        # 创建 Blender 服务器命令
        command = {
            "type": "get_scene_info",
            "params": {},
        }

        # 创建连接并发送命令
        connection = BlenderConnection(host=host, port=port, timeout=timeout)
        result = send_command(command, connection)

        # 检查命令是否成功
        if not result.get("status") == "success":
            return create_standard_response(
                success=False,
                error=result.get("message", "从 Blender 服务器获取场景信息时出错"),
                data=result,
            )

        # 提取 Blender 服务器响应的数据
        scene_data = result.get("data", {})

        return create_standard_response(
            success=True,
            message="成功获取场景信息",
            data=scene_data,
        )

    except Exception as e:
        return create_standard_response(
            success=False,
            error=f"获取场景信息失败: {e!s}",
            data={
                "error_type": type(e).__name__,
            },
        )


def get_server_status(
    host: str = "localhost",
    port: int = 9876,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """
    获取 Blender 服务器状态信息。

    此函数发送 get_server_status 命令到 Blender 服务器以获取状态信息。

    Args:
        host: Blender 服务器主机 (默认: localhost)
        port: Blender 服务器端口 (默认: 9876)
        timeout: 连接超时（秒） (默认: 5.0)

    Returns:
        包含服务器状态信息的字典

    """
    try:
        # 创建 Blender 服务器命令
        command = {
            "type": "get_server_status",
            "params": {},
        }

        # 创建连接并发送命令
        connection = BlenderConnection(host=host, port=port, timeout=timeout)
        result = send_command(command, connection)

        # 检查命令是否成功
        if not result.get("status") == "success":
            return create_standard_response(
                success=False,
                error=result.get("message", "从 Blender 服务器获取状态信息时出错"),
                data=result,
            )

        # 提取 Blender 服务器响应的数据
        status_data = result.get("data", {})

        return create_standard_response(
            success=True,
            message="成功获取服务器状态",
            data=status_data,
        )

    except Exception as e:
        return create_standard_response(
            success=False,
            error=f"获取服务器状态失败: {e!s}",
            data={
                "error_type": type(e).__name__,
            },
        )


# 为 MCP 工具注册功能
def register_base_tools(app: FastMCP) -> None:
    """向 FastMCP 注册基础工具。"""

    @app.tool()
    def get_blender_scene_info(
        ctx: Context,
    ) -> str:
        """
        获取当前 Blender 场景信息。

        返回有关当前 Blender 场景的详细信息，包括对象、材质和渲染设置。
        这对于了解场景状态、诊断问题或计划下一步操作非常有用。

        返回信息包括:
        - 场景中的对象列表（名称、类型、位置、旋转、缩放）
        - 材质库（名称、类型、属性）
        - 灯光设置（类型、强度、颜色）
        - 渲染设置（引擎类型、分辨率、采样数）
        - 相机设置（位置、焦距、视野）
        - 活动对象和选择状态

        Returns:
            场景信息的JSON字符串

        Example:
            ```python
            # 获取当前场景信息
            scene_info = get_blender_scene_info(ctx)
            print(f"场景中有 {len(scene_info['objects'])} 个对象")
            ```

        """
        result = get_scene_info()
        return json.dumps(result, indent=2)

    @app.tool()
    def get_blender_server_status(
        ctx: Context,
    ) -> str:
        """
        获取 Blender 服务器状态。

        返回有关 Blender 服务器的详细状态信息，包括运行时间、连接统计和性能指标。
        这对于监控服务器健康状况、诊断连接问题或了解服务器负载非常有用。

        返回信息包括:
        - 服务器运行时间
        - 处理的命令总数
        - 活动连接数和历史连接总数
        - 最后连接时间
        - 服务器版本和配置信息
        - 系统资源使用情况
        - 可能的错误或警告消息

        Returns:
            服务器状态的JSON字符串

        Example:
            ```python
            # 检查服务器状态
            status = get_blender_server_status(ctx)
            print(f"服务器已运行: {status['uptime_hours']} 小时")
            ```

        """
        result = get_server_status()
        return json.dumps(result, indent=2)
