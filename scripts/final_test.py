#!/usr/bin/env python3
"""
最终测试脚本 - 创建多个高亮显示的对象以确保可见性
"""

import math
import random
import sys

import bpy

# 添加默认脚本目录到sys.path，以便可以导入utils模块
sys.path.append("D:\\data_files\\mcps\\blender-mcp-simplify\\scripts")

# 导入工具模块并设置脚本路径
import utils

utils.setup_script_path()

print("🚀 开始最终测试 - 创建多个高亮对象")

# 1. 清理现有场景
utils.clear_scene(verbose=True)


# 2. 创建多个明显的测试对象
def create_object(name, location, color, size=1.0):
    # 随机选择一种基础类型
    object_type = random.choice(["CUBE", "SPHERE", "CONE", "TORUS"])

    if object_type == "CUBE":
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    elif object_type == "SPHERE":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=size / 2, location=location)
    elif object_type == "CONE":
        bpy.ops.mesh.primitive_cone_add(radius1=size / 2, location=location)
    elif object_type == "TORUS":
        bpy.ops.mesh.primitive_torus_add(
            major_radius=size / 2,
            minor_radius=size / 4,
            location=location,
        )

    obj = bpy.context.active_object
    obj.name = name

    # 创建发光材质
    mat = bpy.data.materials.new(name=f"Material_{name}")
    mat.use_nodes = True

    # 清理节点
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # 添加发光节点
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)
    emission.inputs["Strength"].default_value = 2.0  # 更亮

    output = nodes.new(type="ShaderNodeOutputMaterial")
    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    # 应用材质
    obj.data.materials.append(mat)

    # 设置父级
    if bpy.context.scene.objects.get("FinalTest_Parent"):
        obj.parent = bpy.context.scene.objects["FinalTest_Parent"]

    return obj


# 创建一个空对象作为父级
bpy.ops.object.empty_add(type="ARROWS", location=(0, 0, 0))
parent = bpy.context.active_object
parent.name = "FinalTest_Parent"
parent.empty_display_size = 2.0

# 创建一组彩色对象
colors = [
    (1.0, 0.0, 0.0),  # 红
    (0.0, 1.0, 0.0),  # 绿
    (0.0, 0.0, 1.0),  # 蓝
    (1.0, 1.0, 0.0),  # 黄
    (1.0, 0.0, 1.0),  # 紫
    (0.0, 1.0, 1.0),  # 青
]

# 创建一个环形排列的对象
radius = 3.0
num_objects = len(colors)
objects = []

for i in range(num_objects):
    angle = (2 * math.pi * i) / num_objects
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    z = 1.0

    obj = create_object(
        f"FinalTest_Object_{i + 1}",
        (x, y, z),
        colors[i],
        size=1.0,
    )
    objects.append(obj)
    print(
        f"创建了对象: {obj.name} - 位置: ({x:.1f}, {y:.1f}, {z:.1f}), 颜色: {colors[i]}",
    )

# 3. 添加动画
print("添加动画...")
# 为父对象添加旋转动画
parent.rotation_euler = (0, 0, 0)
parent.keyframe_insert(data_path="rotation_euler", frame=1)

parent.rotation_euler = (0, 0, math.radians(360))
parent.keyframe_insert(data_path="rotation_euler", frame=100)

# 设置循环
if parent.animation_data and parent.animation_data.action:
    parent.animation_data.action.use_cyclic = True
    print("设置了循环动画")

# 4. 设置摄像机和视图
try:
    # 找到或创建摄像机
    if "Camera" in bpy.context.scene.objects:
        camera = bpy.context.scene.objects["Camera"]
    else:
        bpy.ops.object.camera_add()
        camera = bpy.context.active_object

    # 设置摄像机位置
    camera.location = (10, -10, 8)
    camera.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = camera
    print("摄像机已设置")
except Exception as e:
    print(f"摄像机设置失败: {e}")

# 5. 强制UI刷新
print("执行UI刷新...")

# 更新视图层
bpy.context.view_layer.update()

# 更新依赖图
depsgraph = bpy.context.evaluated_depsgraph_get()
depsgraph.update()

# 设置视图
try:
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            for region in area.regions:
                if region.type == "WINDOW":
                    with bpy.context.temp_override(area=area, region=region):
                        bpy.ops.view3d.view_all()

            # 设置为摄像机视图
            with bpy.context.temp_override(area=area):
                bpy.ops.view3d.view_camera()

            # 设置阴影模式
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.type = "MATERIAL"  # 使用材质视图以便看到发光效果

    print("视图已设置为摄像机视图，并开启材质显示")
except Exception as e:
    print(f"视图设置失败: {e}")

# 标记所有区域重绘
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        area.tag_redraw()

print("\n" + "=" * 50)
print("🎬 最终测试完成!")
print("=" * 50)
print(f"✅ 创建了 {len(objects)} 个彩色发光对象")
print("✅ 对象以环形排列")
print("✅ 添加了旋转动画 (100帧)")
print("✅ 设置了摄像机视图")
print("✅ 强制刷新了UI")
print("=" * 50)

print("\n💡 如果你看不到这些彩色对象，请尝试:")
print("  1. 手动点击'视图 > 定位 > 框选全部' (View > Frame All)")
print("  2. 按数字键盘1、7、3分别切换前视图、顶视图、右视图")
print("  3. 按Home键聚焦所有对象")
print("  4. 按Alt+Z切换视图着色模式")
