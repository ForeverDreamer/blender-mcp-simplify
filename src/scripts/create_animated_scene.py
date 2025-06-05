#!/usr/bin/env python3
"""
Blender动画场景创建脚本
包含各种基础对象和动画效果
"""

import math

import bpy
from mathutils import Vector


def clear_scene():
    """清理默认场景"""
    # 删除所有网格对象
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # 清理未使用的数据块
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

    print("场景已清理")


def create_basic_objects():
    """创建基础几何对象"""
    objects = []

    # 1. 立方体
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1))
    cube = bpy.context.active_object
    cube.name = "AnimatedCube"
    objects.append(cube)

    # 2. 球体
    bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 1))
    sphere = bpy.context.active_object
    sphere.name = "AnimatedSphere"
    objects.append(sphere)

    # 3. 圆柱体
    bpy.ops.mesh.primitive_cylinder_add(location=(-3, 0, 1))
    cylinder = bpy.context.active_object
    cylinder.name = "AnimatedCylinder"
    objects.append(cylinder)

    # 4. 锥体
    bpy.ops.mesh.primitive_cone_add(location=(0, 3, 1))
    cone = bpy.context.active_object
    cone.name = "AnimatedCone"
    objects.append(cone)

    # 5. 环形
    bpy.ops.mesh.primitive_torus_add(location=(0, -3, 1))
    torus = bpy.context.active_object
    torus.name = "AnimatedTorus"
    objects.append(torus)

    # 6. 猴子头（Suzanne）
    bpy.ops.mesh.primitive_monkey_add(location=(3, 3, 1))
    monkey = bpy.context.active_object
    monkey.name = "AnimatedMonkey"
    objects.append(monkey)

    print(f"创建了 {len(objects)} 个基础对象")
    return objects


def create_materials():
    """创建各种材质"""
    materials = []

    # 红色材质
    red_mat = bpy.data.materials.new(name="RedMaterial")
    red_mat.use_nodes = True
    red_mat.node_tree.nodes.clear()

    # 添加基本节点
    bsdf = red_mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    output = red_mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    red_mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # 设置颜色
    bsdf.inputs["Base Color"].default_value = (1.0, 0.2, 0.2, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.5
    materials.append(red_mat)

    # 蓝色金属材质
    blue_metal = bpy.data.materials.new(name="BlueMetalMaterial")
    blue_metal.use_nodes = True
    blue_metal.node_tree.nodes.clear()

    bsdf2 = blue_metal.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    output2 = blue_metal.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    blue_metal.node_tree.links.new(bsdf2.outputs["BSDF"], output2.inputs["Surface"])

    bsdf2.inputs["Base Color"].default_value = (0.2, 0.4, 1.0, 1.0)
    bsdf2.inputs["Metallic"].default_value = 0.8
    bsdf2.inputs["Roughness"].default_value = 0.2
    materials.append(blue_metal)

    # 绿色发光材质
    green_emission = bpy.data.materials.new(name="GreenEmissionMaterial")
    green_emission.use_nodes = True
    green_emission.node_tree.nodes.clear()

    emission = green_emission.node_tree.nodes.new(type="ShaderNodeEmission")
    output3 = green_emission.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    green_emission.node_tree.links.new(
        emission.outputs["Emission"],
        output3.inputs["Surface"],
    )

    emission.inputs["Color"].default_value = (0.2, 1.0, 0.2, 1.0)
    emission.inputs["Strength"].default_value = 2.0
    materials.append(green_emission)

    # 黄色玻璃材质
    yellow_glass = bpy.data.materials.new(name="YellowGlassMaterial")
    yellow_glass.use_nodes = True
    yellow_glass.node_tree.nodes.clear()

    bsdf3 = yellow_glass.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    output4 = yellow_glass.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    yellow_glass.node_tree.links.new(bsdf3.outputs["BSDF"], output4.inputs["Surface"])

    bsdf3.inputs["Base Color"].default_value = (1.0, 1.0, 0.2, 1.0)
    # Blender 4.4兼容性：检查Transmission属性是否存在
    if "Transmission" in bsdf3.inputs:
        bsdf3.inputs["Transmission"].default_value = 0.9
    elif "Transmission Weight" in bsdf3.inputs:
        bsdf3.inputs["Transmission Weight"].default_value = 0.9
    bsdf3.inputs["Roughness"].default_value = 0.0
    bsdf3.inputs["IOR"].default_value = 1.45
    materials.append(yellow_glass)

    # 紫色塑料材质
    purple_plastic = bpy.data.materials.new(name="PurplePlasticMaterial")
    purple_plastic.use_nodes = True
    purple_plastic.node_tree.nodes.clear()

    bsdf4 = purple_plastic.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    output5 = purple_plastic.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    purple_plastic.node_tree.links.new(bsdf4.outputs["BSDF"], output5.inputs["Surface"])

    bsdf4.inputs["Base Color"].default_value = (0.8, 0.2, 1.0, 1.0)
    bsdf4.inputs["Metallic"].default_value = 0.0
    bsdf4.inputs["Roughness"].default_value = 0.3
    materials.append(purple_plastic)

    # 彩虹材质（使用ColorRamp）
    rainbow_mat = bpy.data.materials.new(name="RainbowMaterial")
    rainbow_mat.use_nodes = True
    rainbow_mat.node_tree.nodes.clear()

    bsdf5 = rainbow_mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    output6 = rainbow_mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    coord = rainbow_mat.node_tree.nodes.new(type="ShaderNodeTexCoord")
    colorramp = rainbow_mat.node_tree.nodes.new(type="ShaderNodeValToRGB")

    # 连接节点
    rainbow_mat.node_tree.links.new(coord.outputs["Generated"], colorramp.inputs["Fac"])
    rainbow_mat.node_tree.links.new(
        colorramp.outputs["Color"],
        bsdf5.inputs["Base Color"],
    )
    rainbow_mat.node_tree.links.new(bsdf5.outputs["BSDF"], output6.inputs["Surface"])

    # 设置颜色渐变
    colorramp.color_ramp.elements[0].color = (1.0, 0.0, 0.0, 1.0)  # 红色
    colorramp.color_ramp.elements[1].color = (0.0, 0.0, 1.0, 1.0)  # 蓝色
    materials.append(rainbow_mat)

    print(f"创建了 {len(materials)} 种材质")
    return materials


def apply_materials_to_objects(objects, materials):
    """为对象应用材质"""
    for i, obj in enumerate(objects):
        if i < len(materials):
            obj.data.materials.append(materials[i])
        else:
            # 如果材质不够，随机选择一个
            obj.data.materials.append(materials[i % len(materials)])

    print("材质已应用到对象")


def create_animations(objects):
    """创建各种动画效果"""
    # 设置动画帧范围
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 240  # 10秒（24fps）

    for i, obj in enumerate(objects):
        # 清除现有动画
        obj.animation_data_clear()

        # 根据对象索引创建不同的动画
        if i == 0:  # 立方体 - 旋转动画
            create_rotation_animation(obj, "Z", 240)
        elif i == 1:  # 球体 - 上下移动
            create_bounce_animation(obj, 240)
        elif i == 2:  # 圆柱体 - 缩放动画
            create_scale_animation(obj, 240)
        elif i == 3:  # 锥体 - 摆动动画
            create_pendulum_animation(obj, 240)
        elif i == 4:  # 环形 - 8字运动
            create_figure_eight_animation(obj, 240)
        elif i == 5:  # 猴子头 - 组合动画
            create_complex_animation(obj, 240)

    print("动画已创建")


def create_rotation_animation(obj, axis, frames):
    """创建旋转动画"""
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert(data_path="rotation_euler", frame=1)

    if axis == "X":
        obj.rotation_euler = (math.radians(360), 0, 0)
    elif axis == "Y":
        obj.rotation_euler = (0, math.radians(360), 0)
    else:  # Z
        obj.rotation_euler = (0, 0, math.radians(360))

    obj.keyframe_insert(data_path="rotation_euler", frame=frames)

    # 设置插值为线性
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "LINEAR"


def create_bounce_animation(obj, frames):
    """创建弹跳动画"""
    original_z = obj.location.z

    for frame in range(1, frames + 1, 20):
        # 计算弹跳高度
        t = (frame - 1) / (frames - 1)
        height = original_z + abs(math.sin(t * math.pi * 4)) * 2

        obj.location.z = height
        obj.keyframe_insert(data_path="location", frame=frame)


def create_scale_animation(obj, frames):
    """创建缩放动画"""
    obj.scale = (1, 1, 1)
    obj.keyframe_insert(data_path="scale", frame=1)

    obj.scale = (2, 2, 2)
    obj.keyframe_insert(data_path="scale", frame=frames // 2)

    obj.scale = (1, 1, 1)
    obj.keyframe_insert(data_path="scale", frame=frames)


def create_pendulum_animation(obj, frames):
    """创建摆动动画"""
    for frame in range(1, frames + 1, 10):
        t = (frame - 1) / (frames - 1)
        angle = math.sin(t * math.pi * 4) * math.radians(45)

        obj.rotation_euler = (angle, 0, 0)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def create_figure_eight_animation(obj, frames):
    """创建8字运动"""
    original_x = obj.location.x
    original_y = obj.location.y

    for frame in range(1, frames + 1, 5):
        t = (frame - 1) / (frames - 1) * 2 * math.pi

        x = original_x + math.sin(t) * 2
        y = original_y + math.sin(2 * t) * 1

        obj.location.x = x
        obj.location.y = y
        obj.keyframe_insert(data_path="location", frame=frame)


def create_complex_animation(obj, frames):
    """创建复杂组合动画"""
    original_loc = obj.location.copy()

    for frame in range(1, frames + 1, 8):
        t = (frame - 1) / (frames - 1) * 2 * math.pi

        # 位置动画
        x = original_loc.x + math.cos(t) * 1.5
        y = original_loc.y + math.sin(t) * 1.5
        z = original_loc.z + math.sin(t * 2) * 0.5

        obj.location = (x, y, z)
        obj.keyframe_insert(data_path="location", frame=frame)

        # 旋转动画
        obj.rotation_euler = (t, t * 0.5, t * 0.3)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 缩放动画
        scale = 1 + math.sin(t * 3) * 0.3
        obj.scale = (scale, scale, scale)
        obj.keyframe_insert(data_path="scale", frame=frame)


def setup_lighting():
    """设置灯光"""
    # 删除默认灯光
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "LIGHT":
            obj.select_set(True)
            bpy.ops.object.delete()

    # 主灯光
    bpy.ops.object.light_add(type="SUN", location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.name = "MainSun"
    sun.data.energy = 3.0
    sun.data.color = (1.0, 0.95, 0.8)

    # 补光
    bpy.ops.object.light_add(type="AREA", location=(-5, -5, 8))
    area = bpy.context.active_object
    area.name = "FillLight"
    area.data.energy = 100.0
    area.data.color = (0.8, 0.9, 1.0)
    area.data.size = 4.0

    # 环境光
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.1, 0.1, 0.2, 1.0)
    bg.inputs["Strength"].default_value = 0.3

    print("灯光设置完成")


def setup_camera():
    """设置相机"""
    # 删除默认相机
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "CAMERA":
            obj.select_set(True)
            bpy.ops.object.delete()

    # 创建新相机
    bpy.ops.object.camera_add(location=(8, -8, 6))
    camera = bpy.context.active_object
    camera.name = "MainCamera"

    # 设置相机朝向场景中心
    direction = Vector((0, 0, 1)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    # 设置为活动相机
    bpy.context.scene.camera = camera

    print("相机设置完成")


def setup_render_settings():
    """设置渲染参数"""
    scene = bpy.context.scene

    # 渲染引擎
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True

    # 分辨率
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 50  # 50%用于快速预览

    # 输出格式
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = "/tmp/blender_animation_"

    print("渲染设置完成")


def main():
    """主函数"""
    print("开始创建Blender动画场景")
    print("=" * 40)

    # 1. 清理场景
    clear_scene()

    # 2. 创建基础对象
    objects = create_basic_objects()

    # 3. 创建材质
    materials = create_materials()

    # 4. 应用材质
    apply_materials_to_objects(objects, materials)

    # 5. 创建动画
    create_animations(objects)

    # 6. 设置灯光
    setup_lighting()

    # 7. 设置相机
    setup_camera()

    # 8. 设置渲染参数
    setup_render_settings()

    # 9. 切换到Shading工作区以便查看材质
    try:
        bpy.context.window.workspace = bpy.data.workspaces["Shading"]
    except:
        pass

    # 10. 刷新界面显示
    print("正在刷新Blender界面...")
    try:
        # 强制更新场景和UI
        bpy.context.view_layer.update()

        # 强制重绘所有区域
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

        # 特别标记3D视口重绘
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

        print("界面刷新完成")
    except Exception as e:
        print(f"界面刷新时出错: {e}")

    # 注意：如果需要保存场景，请手动执行 Ctrl+S 或使用 File > Save

    print("=" * 40)
    print("场景创建完成！")
    print("包含以下内容：")
    print("- 6个基础几何对象")
    print("- 6种不同材质")
    print("- 各种动画效果（旋转、弹跳、缩放、摆动、8字运动、组合动画）")
    print("- 专业灯光设置")
    print("- 相机和渲染配置")
    print("- 动画时长：240帧（10秒）")
    print()
    print("可以按空格键播放动画预览")
    print("按F12渲染当前帧")


if __name__ == "__main__":
    main()
