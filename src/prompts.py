"""
Blender MCP 提示模块

提供Prompts功能，以帮助LLM更高效地使用Blender MCP工具。
提示包括常见建模、渲染和动画任务的结构化提示。
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# 预定义的提示集合
BLENDER_PROMPTS = {
    # 基础建模提示
    "modeling/create_cube": {
        "template": "创建一个立方体，位置在({x}, {y}, {z})，大小为{size}，命名为'{name}'",
        "params": {
            "x": {"type": "float", "default": 0.0, "description": "X坐标位置"},
            "y": {"type": "float", "default": 0.0, "description": "Y坐标位置"},
            "z": {"type": "float", "default": 0.0, "description": "Z坐标位置"},
            "size": {"type": "float", "default": 2.0, "description": "立方体大小"},
            "name": {"type": "string", "default": "Cube", "description": "立方体名称"},
        },
        "description": "创建一个立方体并设置其位置、大小和名称",
    },
    "modeling/create_scene": {
        "template": "创建一个包含{cube_count}个立方体的场景，添加{light_type}光源和相机，设置相机位置在({cam_x}, {cam_y}, {cam_z})",
        "params": {
            "cube_count": {
                "type": "integer",
                "default": 1,
                "description": "场景中的立方体数量",
            },
            "light_type": {
                "type": "string",
                "default": "SUN",
                "description": "光源类型 (SUN, POINT, SPOT, AREA)",
            },
            "cam_x": {"type": "float", "default": 7.0, "description": "相机X坐标位置"},
            "cam_y": {"type": "float", "default": -7.0, "description": "相机Y坐标位置"},
            "cam_z": {"type": "float", "default": 5.0, "description": "相机Z坐标位置"},
        },
        "description": "创建一个包含多个立方体、光源和相机的场景",
    },
    # 材质提示
    "materials/apply_material": {
        "template": "为对象'{object_name}'创建一个{material_type}材质，命名为'{material_name}'，颜色为({r}, {g}, {b})",
        "params": {
            "object_name": {
                "type": "string",
                "default": "Cube",
                "description": "要应用材质的对象名称",
            },
            "material_type": {
                "type": "string",
                "default": "principled",
                "description": "材质类型 (principled, metal, glass, subsurface)",
            },
            "material_name": {
                "type": "string",
                "default": "MyMaterial",
                "description": "材质名称",
            },
            "r": {"type": "float", "default": 0.8, "description": "红色通道值 (0-1)"},
            "g": {"type": "float", "default": 0.8, "description": "绿色通道值 (0-1)"},
            "b": {"type": "float", "default": 0.8, "description": "蓝色通道值 (0-1)"},
        },
        "description": "为指定对象创建并应用材质",
    },
    # 渲染提示
    "render/setup_render": {
        "template": "设置{engine}渲染引擎，分辨率为{width}x{height}，采样数为{samples}，并渲染当前场景",
        "params": {
            "engine": {
                "type": "string",
                "default": "CYCLES",
                "description": "渲染引擎 (CYCLES, EEVEE)",
            },
            "width": {
                "type": "integer",
                "default": 1920,
                "description": "渲染宽度（像素）",
            },
            "height": {
                "type": "integer",
                "default": 1080,
                "description": "渲染高度（像素）",
            },
            "samples": {"type": "integer", "default": 128, "description": "渲染采样数"},
        },
        "description": "配置渲染设置并渲染当前场景",
    },
    # 动画提示
    "animation/create_animation": {
        "template": "为对象'{object_name}'创建一个{anim_type}动画，从第{start_frame}帧到第{end_frame}帧",
        "params": {
            "object_name": {
                "type": "string",
                "default": "Cube",
                "description": "要添加动画的对象名称",
            },
            "anim_type": {
                "type": "string",
                "default": "rotation",
                "description": "动画类型 (rotation, movement, scale)",
            },
            "start_frame": {
                "type": "integer",
                "default": 1,
                "description": "动画开始帧",
            },
            "end_frame": {
                "type": "integer",
                "default": 60,
                "description": "动画结束帧",
            },
        },
        "description": "为指定对象创建动画",
    },
}


def get_prompt(prompt_id: str, params: dict[str, Any] | None = None) -> str | None:
    """
    获取指定ID的提示，并填充参数

    Args:
        prompt_id: 提示ID
        params: 参数字典，用于填充提示模板

    Returns:
        填充了参数的提示字符串，如果提示不存在则返回None

    """
    if prompt_id not in BLENDER_PROMPTS:
        return None

    prompt_data = BLENDER_PROMPTS[prompt_id]
    template = prompt_data["template"]

    # 使用提供的参数或默认值
    if params is None:
        params = {}

    param_values = {}
    for param_name, param_info in prompt_data["params"].items():
        if param_name in params:
            param_values[param_name] = params[param_name]
        else:
            param_values[param_name] = param_info["default"]

    # 填充模板
    try:
        return template.format(**param_values)
    except KeyError as e:
        logger.error(f"提示参数错误: {e}")
        return None


def list_prompts() -> list[dict[str, Any]]:
    """
    列出所有可用的提示

    Returns:
        提示列表，每个提示包含id、描述和参数信息

    """
    prompts = []
    for prompt_id, prompt_data in BLENDER_PROMPTS.items():
        prompts.append(
            {
                "id": prompt_id,
                "description": prompt_data["description"],
                "params": prompt_data["params"],
            },
        )
    return prompts


def register_prompts(app: FastMCP) -> None:
    """向 FastMCP 注册提示工具。"""

    # 注册提示
    @app.prompt("prompts://list")
    def prompts_list() -> list[dict[str, Any]]:
        """列出所有可用的Blender提示"""
        return list_prompts()

    @app.prompt("prompt://{prompt_id}")
    def prompt_get(
        prompt_id: str,
        params: dict[str, Any] | None = None,
    ) -> str | None:
        """获取特定提示，填充参数后返回"""
        return get_prompt(prompt_id, params)
