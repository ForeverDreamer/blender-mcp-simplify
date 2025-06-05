#!/usr/bin/env python3
"""
Blender MCP - 通用工具函数
包含各个脚本共用的功能
"""

import sys

import bpy


def get_scripts_path():
    """
    获取脚本路径，优先使用Blender插件配置中的路径

    返回:
        str: 脚本路径
    """
    # 默认脚本路径
    default_path = "D:\\data_files\\mcps\\blender-mcp-simplify\\scripts"

    try:
        # 从 Blender 插件配置中获取脚本路径
        scripts_path = bpy.context.scene.blender_mcp.scripts_root
        if not scripts_path or not scripts_path.strip():
            # 如果路径为空，使用默认路径
            scripts_path = default_path
    except (AttributeError, TypeError):
        # 如果出现异常，使用默认路径
        scripts_path = default_path

    return scripts_path


def setup_script_path():
    """
    设置脚本路径并将其添加到sys.path中

    返回:
        str: 使用的脚本路径
    """
    scripts_path = get_scripts_path()

    # 确保脚本路径在 sys.path 中
    if scripts_path not in sys.path:
        sys.path.append(scripts_path)

    return scripts_path


def clear_scene(verbose=True, extra_blocks=None):
    """
    清理默认场景 - 通用版本

    参数:
        verbose (bool): 是否打印清理信息
        extra_blocks (list): 额外要清理的数据块类型列表
    """
    # 切换到OBJECT模式
    if bpy.context.active_object and bpy.context.active_object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # 删除所有对象
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # 需要清理的基本数据块类型
    block_types = ["meshes", "materials", "textures", "images", "actions"]

    # 添加额外的数据块类型（如果有）
    if extra_blocks:
        block_types.extend(extra_blocks)

    # 清理未使用的数据块
    for block_type in block_types:
        if hasattr(bpy.data, block_type):
            data_collection = getattr(bpy.data, block_type)
            for block in data_collection:
                if block.users == 0:
                    data_collection.remove(block)

    # 可选打印信息
    if verbose:
        print("✅ 场景已清理")

    return True
