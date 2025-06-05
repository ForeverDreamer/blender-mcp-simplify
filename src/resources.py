"""
Blender MCP 资源模块

提供Resources功能，以帮助LLM更高效地使用Blender MCP工具。
资源包括各种有用的Blender操作模板、材质预设和场景示例。
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# 预定义的资源集合
BLENDER_RESOURCES = {
    # 模型创建模板
    "templates/basic_cube": {
        "content": """
import bpy

# 创建一个基本立方体
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "BasicCube"
""",
        "description": "创建一个基本立方体的模板",
        "mime_type": "text/x-python",
    },
    "templates/basic_scene": {
        "content": """
import bpy

# 清除默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 创建一个平面作为地面
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"

# 创建一个立方体
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
cube = bpy.context.active_object
cube.name = "Cube"

# 添加一个光源
bpy.ops.object.light_add(type='SUN', radius=1, location=(5, 5, 10))
light = bpy.context.active_object
light.name = "Sun"
light.data.energy = 3.0

# 添加一个相机
bpy.ops.object.camera_add(location=(7, -7, 5))
camera = bpy.context.active_object
camera.name = "Camera"
camera.rotation_euler = (0.9, 0, 0.8)

# 设置相机为活动相机
bpy.context.scene.camera = camera
""",
        "description": "创建一个包含地面、立方体、光源和相机的基本场景",
        "mime_type": "text/x-python",
    },
    # 材质预设
    "materials/metal": {
        "content": """
import bpy

def create_metal_material(obj_name=None, material_name="MetalMaterial"):
    # 创建金属材质
    mat = bpy.data.materials.new(name=material_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # 清除默认节点
    for node in nodes:
        nodes.remove(node)
    
    # 添加主要节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    
    # 设置金属材质参数
    principled.inputs['Metallic'].default_value = 1.0
    principled.inputs['Roughness'].default_value = 0.2
    principled.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)
    principled.inputs['Specular'].default_value = 0.5
    
    # 连接节点
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 如果提供了对象名，则将材质应用到该对象
    if obj_name and obj_name in bpy.data.objects:
        obj = bpy.data.objects[obj_name]
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    
    return mat

# 示例调用
# create_metal_material("Cube")
""",
        "description": "创建金属材质的模板",
        "mime_type": "text/x-python",
    },
    "materials/glass": {
        "content": """
import bpy

def create_glass_material(obj_name=None, material_name="GlassMaterial"):
    # 创建玻璃材质
    mat = bpy.data.materials.new(name=material_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # 清除默认节点
    for node in nodes:
        nodes.remove(node)
    
    # 添加主要节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    glass = nodes.new(type='ShaderNodeBsdfGlass')
    
    # 设置玻璃材质参数
    glass.inputs['Color'].default_value = (0.8, 0.8, 0.8, 1.0)
    glass.inputs['Roughness'].default_value = 0.0
    glass.inputs['IOR'].default_value = 1.45
    
    # 连接节点
    links.new(glass.outputs['BSDF'], output.inputs['Surface'])
    
    # 如果提供了对象名，则将材质应用到该对象
    if obj_name and obj_name in bpy.data.objects:
        obj = bpy.data.objects[obj_name]
        # 启用透明渲染
        obj.active_material.use_nodes = True
        obj.active_material.blend_method = 'BLEND'
        
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    
    return mat

# 示例调用
# create_glass_material("Cube")
""",
        "description": "创建玻璃材质的模板",
        "mime_type": "text/x-python",
    },
    # 渲染设置
    "render/cycles_basic": {
        "content": """
import bpy

def setup_cycles_render(resolution_x=1920, resolution_y=1080, samples=128):
    # 设置Cycles渲染器的基本参数
    scene = bpy.context.scene
    
    # 设置渲染引擎为Cycles
    scene.render.engine = 'CYCLES'
    
    # 设置设备为GPU (如果可用)
    cycles_prefs = bpy.context.preferences.addons['cycles'].preferences
    cuda_devices = [d for d in cycles_prefs.devices if d.type == 'CUDA']
    if cuda_devices:
        cycles_prefs.compute_device_type = 'CUDA'
        for device in cuda_devices:
            device.use = True
        scene.cycles.device = 'GPU'
    
    # 设置基本渲染参数
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.resolution_percentage = 100
    
    # 设置采样和降噪
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    
    # 设置输出格式
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '16'
    
    return "Cycles渲染设置已应用"

# 示例调用
# setup_cycles_render(1920, 1080, 128)
""",
        "description": "配置Cycles渲染引擎的基本设置",
        "mime_type": "text/x-python",
    },
    # 动画预设
    "animation/rotation": {
        "content": """
import bpy

def create_rotation_animation(obj_name, start_frame=1, end_frame=60, rotation_degrees=360):
    # 为对象创建简单的旋转动画
    if obj_name not in bpy.data.objects:
        return f"错误：对象 '{obj_name}' 不存在"
    
    obj = bpy.data.objects[obj_name]
    scene = bpy.context.scene
    
    # 设置动画参数
    scene.frame_start = start_frame
    scene.frame_end = end_frame
    
    # 转换角度为弧度
    import math
    rotation_radians = math.radians(rotation_degrees)
    
    # 设置起始关键帧
    scene.frame_current = start_frame
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert(data_path="rotation_euler", index=-1)
    
    # 设置结束关键帧
    scene.frame_current = end_frame
    obj.rotation_euler = (0, 0, rotation_radians)
    obj.keyframe_insert(data_path="rotation_euler", index=-1)
    
    return f"已为 '{obj_name}' 创建旋转动画"

# 示例调用
# create_rotation_animation("Cube", 1, 60, 360)
""",
        "description": "创建对象旋转动画的模板",
        "mime_type": "text/x-python",
    },
}


def get_resource(resource_id: str) -> tuple[str | None, str | None]:
    """
    获取指定ID的资源内容和MIME类型

    Args:
        resource_id: 资源ID

    Returns:
        元组 (内容, MIME类型)，如果资源不存在则返回 (None, None)

    """
    if resource_id in BLENDER_RESOURCES:
        resource = BLENDER_RESOURCES[resource_id]
        return resource["content"], resource["mime_type"]
    return None, None


def list_resources() -> list[dict[str, Any]]:
    """
    列出所有可用的资源

    Returns:
        资源列表，每个资源包含id、描述和mime_type

    """
    resources = []
    for resource_id, resource_data in BLENDER_RESOURCES.items():
        resources.append(
            {
                "id": resource_id,
                "description": resource_data["description"],
                "mime_type": resource_data["mime_type"],
            },
        )
    return resources


def register_resources(app: FastMCP) -> None:
    """向 FastMCP 注册资源工具。"""

    # 注册资源
    @app.resource("resources://list")
    def resources_list() -> list[dict[str, Any]]:
        """列出所有可用的Blender资源"""
        return list_resources()

    @app.resource("resource://{resource_id}")
    def resource_get(resource_id: str) -> tuple[str | None, str | None]:
        """获取特定资源的内容"""
        return get_resource(resource_id)
