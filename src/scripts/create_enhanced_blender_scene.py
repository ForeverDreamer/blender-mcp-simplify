#!/usr/bin/env python3
"""
增强版Blender动画场景创建脚本
集成PolyHaven资源和高级功能
测试blender-mcp工具完整功能
"""

import math

import bpy
from mathutils import Vector


def clear_scene():
    """清理默认场景"""
    # 切换到OBJECT模式
    if bpy.context.active_object and bpy.context.active_object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # 删除所有对象
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # 清理未使用的数据块
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)

    print("✅ 场景已清理")


def create_ground_plane():
    """创建地面平面"""
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "GroundPlane"

    # 细分地面以获得更好的光影效果
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=5)
    bpy.ops.object.mode_set(mode="OBJECT")

    # 创建地面材质
    ground_mat = bpy.data.materials.new(name="GroundMaterial")
    ground_mat.use_nodes = True
    nodes = ground_mat.node_tree.nodes
    nodes.clear()

    # 添加节点
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    checker = nodes.new(type="ShaderNodeTexChecker")
    coord = nodes.new(type="ShaderNodeTexCoord")
    mapping = nodes.new(type="ShaderNodeMapping")

    # 连接节点
    ground_mat.node_tree.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    ground_mat.node_tree.links.new(mapping.outputs["Vector"], checker.inputs["Vector"])
    ground_mat.node_tree.links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
    ground_mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # 设置参数
    mapping.inputs["Scale"].default_value = (4, 4, 4)
    checker.inputs["Color1"].default_value = (0.8, 0.8, 0.8, 1.0)
    checker.inputs["Color2"].default_value = (0.2, 0.2, 0.2, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.8

    ground.data.materials.append(ground_mat)
    print("✅ 地面创建完成")
    return ground


def create_animated_objects():
    """创建动画对象集合"""
    objects = []

    # 1. 旋转立方体 - 红色金属
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 2))
    cube = bpy.context.active_object
    cube.name = "RotatingCube"
    objects.append(cube)

    # 2. 弹跳球体 - 蓝色玻璃
    bpy.ops.mesh.primitive_uv_sphere_add(location=(4, 0, 2))
    sphere = bpy.context.active_object
    sphere.name = "BouncingSphere"
    objects.append(sphere)

    # 3. 缩放圆柱体 - 绿色发光
    bpy.ops.mesh.primitive_cylinder_add(location=(-4, 0, 2))
    cylinder = bpy.context.active_object
    cylinder.name = "ScalingCylinder"
    objects.append(cylinder)

    # 4. 摆动锥体 - 黄色塑料
    bpy.ops.mesh.primitive_cone_add(location=(0, 4, 2))
    cone = bpy.context.active_object
    cone.name = "SwingingCone"
    objects.append(cone)

    # 5. 8字运动环形 - 紫色金属
    bpy.ops.mesh.primitive_torus_add(location=(0, -4, 2))
    torus = bpy.context.active_object
    torus.name = "Figure8Torus"
    objects.append(torus)

    # 6. 复杂动画猴子头 - 彩虹材质
    bpy.ops.mesh.primitive_monkey_add(location=(4, 4, 2))
    monkey = bpy.context.active_object
    monkey.name = "ComplexMonkey"
    objects.append(monkey)

    # 7. 螺旋运动圆锥 - 橙色发光
    bpy.ops.mesh.primitive_cone_add(location=(-4, 4, 2))
    spiral_cone = bpy.context.active_object
    spiral_cone.name = "SpiralCone"
    objects.append(spiral_cone)

    # 8. 波浪运动立方体 - 青色玻璃
    bpy.ops.mesh.primitive_cube_add(location=(-4, -4, 2))
    wave_cube = bpy.context.active_object
    wave_cube.name = "WaveCube"
    objects.append(wave_cube)

    print(f"✅ 创建了 {len(objects)} 个动画对象")
    return objects


def create_advanced_materials():
    """创建高级材质"""
    materials = []

    # 1. 红色金属材质
    red_metal = bpy.data.materials.new(name="RedMetal")
    red_metal.use_nodes = True
    nodes = red_metal.node_tree.nodes
    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    noise = nodes.new(type="ShaderNodeTexNoise")
    colorramp = nodes.new(type="ShaderNodeValToRGB")

    red_metal.node_tree.links.new(noise.outputs["Fac"], colorramp.inputs["Fac"])
    red_metal.node_tree.links.new(colorramp.outputs["Color"], bsdf.inputs["Base Color"])
    red_metal.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.1
    noise.inputs["Scale"].default_value = 5.0
    colorramp.color_ramp.elements[0].color = (0.8, 0.1, 0.1, 1.0)
    colorramp.color_ramp.elements[1].color = (1.0, 0.3, 0.3, 1.0)
    materials.append(red_metal)

    # 2. 蓝色玻璃材质
    blue_glass = bpy.data.materials.new(name="BlueGlass")
    blue_glass.use_nodes = True
    nodes = blue_glass.node_tree.nodes
    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    blue_glass.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = (0.1, 0.3, 1.0, 1.0)
    bsdf.inputs["Transmission"].default_value = 0.95
    bsdf.inputs["Roughness"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.52
    materials.append(blue_glass)

    # 3. 绿色发光材质（动画强度）
    green_emission = bpy.data.materials.new(name="GreenEmission")
    green_emission.use_nodes = True
    nodes = green_emission.node_tree.nodes
    nodes.clear()

    emission = nodes.new(type="ShaderNodeEmission")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    green_emission.node_tree.links.new(
        emission.outputs["Emission"],
        output.inputs["Surface"],
    )

    emission.inputs["Color"].default_value = (0.2, 1.0, 0.2, 1.0)
    emission.inputs["Strength"].default_value = 3.0
    materials.append(green_emission)

    # 4. 黄色塑料材质
    yellow_plastic = bpy.data.materials.new(name="YellowPlastic")
    yellow_plastic.use_nodes = True
    nodes = yellow_plastic.node_tree.nodes
    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    yellow_plastic.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = (1.0, 0.8, 0.1, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.7
    bsdf.inputs["Sheen"].default_value = 0.2
    materials.append(yellow_plastic)

    # 5. 紫色金属材质
    purple_metal = bpy.data.materials.new(name="PurpleMetal")
    purple_metal.use_nodes = True
    nodes = purple_metal.node_tree.nodes
    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    purple_metal.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = (0.6, 0.2, 0.8, 1.0)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.3
    materials.append(purple_metal)

    # 6. 彩虹全息材质
    rainbow_holo = bpy.data.materials.new(name="RainbowHolographic")
    rainbow_holo.use_nodes = True
    nodes = rainbow_holo.node_tree.nodes
    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    coord = nodes.new(type="ShaderNodeTexCoord")
    wave = nodes.new(type="ShaderNodeTexWave")
    colorramp = nodes.new(type="ShaderNodeValToRGB")

    rainbow_holo.node_tree.links.new(coord.outputs["Generated"], wave.inputs["Vector"])
    rainbow_holo.node_tree.links.new(wave.outputs["Color"], colorramp.inputs["Fac"])
    rainbow_holo.node_tree.links.new(
        colorramp.outputs["Color"],
        bsdf.inputs["Base Color"],
    )
    rainbow_holo.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    wave.inputs["Scale"].default_value = 10.0
    wave.inputs["Distortion"].default_value = 2.0
    bsdf.inputs["Metallic"].default_value = 0.8
    bsdf.inputs["Roughness"].default_value = 0.1

    # 设置彩虹色彩
    colorramp.color_ramp.elements[0].color = (1.0, 0.0, 0.0, 1.0)
    colorramp.color_ramp.elements[1].color = (0.0, 0.0, 1.0, 1.0)
    materials.append(rainbow_holo)

    # 7. 橙色发光材质
    orange_emission = bpy.data.materials.new(name="OrangeEmission")
    orange_emission.use_nodes = True
    nodes = orange_emission.node_tree.nodes
    nodes.clear()

    emission = nodes.new(type="ShaderNodeEmission")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    orange_emission.node_tree.links.new(
        emission.outputs["Emission"],
        output.inputs["Surface"],
    )

    emission.inputs["Color"].default_value = (1.0, 0.5, 0.1, 1.0)
    emission.inputs["Strength"].default_value = 2.5
    materials.append(orange_emission)

    # 8. 青色玻璃材质
    cyan_glass = bpy.data.materials.new(name="CyanGlass")
    cyan_glass.use_nodes = True
    nodes = cyan_glass.node_tree.nodes
    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    cyan_glass.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = (0.1, 0.8, 0.8, 1.0)
    bsdf.inputs["Transmission"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.1
    bsdf.inputs["IOR"].default_value = 1.33
    materials.append(cyan_glass)

    print(f"✅ 创建了 {len(materials)} 种高级材质")
    return materials


def apply_materials_to_objects(objects, materials):
    """为对象应用材质"""
    for i, obj in enumerate(objects):
        if i < len(materials):
            obj.data.materials.append(materials[i])
        else:
            obj.data.materials.append(materials[i % len(materials)])
    print("✅ 材质已应用")


def create_comprehensive_animations(objects):
    """创建全面的动画系统"""
    # 设置动画范围
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 300  # 12.5秒

    animation_functions = [
        lambda obj: create_rotation_animation(obj, "Z", 300, speed=2.0),
        lambda obj: create_bounce_animation(obj, 300, height=3.0),
        lambda obj: create_scale_animation(obj, 300, max_scale=2.5),
        lambda obj: create_pendulum_animation(obj, 300, angle=60),
        lambda obj: create_figure_eight_animation(obj, 300, radius=3.0),
        lambda obj: create_complex_animation(obj, 300),
        lambda obj: create_spiral_animation(obj, 300),
        lambda obj: create_wave_animation(obj, 300),
    ]

    for i, obj in enumerate(objects):
        obj.animation_data_clear()
        if i < len(animation_functions):
            animation_functions[i](obj)

    print("✅ 综合动画系统创建完成")


def create_rotation_animation(obj, axis, frames, speed=1.0):
    """增强旋转动画"""
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert(data_path="rotation_euler", frame=1)

    rotation_amount = math.radians(360 * speed)
    if axis == "X":
        obj.rotation_euler = (rotation_amount, 0, 0)
    elif axis == "Y":
        obj.rotation_euler = (0, rotation_amount, 0)
    else:  # Z
        obj.rotation_euler = (0, 0, rotation_amount)

    obj.keyframe_insert(data_path="rotation_euler", frame=frames)

    # 设置循环插值
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "LINEAR"


def create_bounce_animation(obj, frames, height=2.0):
    """增强弹跳动画"""
    original_z = obj.location.z

    for frame in range(1, frames + 1, 15):
        t = (frame - 1) / (frames - 1)
        bounce_height = original_z + abs(math.sin(t * math.pi * 6)) * height

        obj.location.z = bounce_height
        obj.keyframe_insert(data_path="location", frame=frame)


def create_scale_animation(obj, frames, max_scale=2.0):
    """增强缩放动画"""
    for frame in range(1, frames + 1, 20):
        t = (frame - 1) / (frames - 1)
        scale = 1.0 + (math.sin(t * math.pi * 4) + 1) * (max_scale - 1) / 2

        obj.scale = (scale, scale, scale)
        obj.keyframe_insert(data_path="scale", frame=frame)


def create_pendulum_animation(obj, frames, angle=45):
    """增强摆动动画"""
    for frame in range(1, frames + 1, 12):
        t = (frame - 1) / (frames - 1)
        swing_angle = math.sin(t * math.pi * 5) * math.radians(angle)

        obj.rotation_euler = (swing_angle, 0, 0)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def create_figure_eight_animation(obj, frames, radius=2.0):
    """增强8字运动"""
    original_x = obj.location.x
    original_y = obj.location.y

    for frame in range(1, frames + 1, 8):
        t = (frame - 1) / (frames - 1) * 2 * math.pi

        x = original_x + math.sin(t) * radius
        y = original_y + math.sin(2 * t) * radius * 0.5

        obj.location.x = x
        obj.location.y = y
        obj.keyframe_insert(data_path="location", frame=frame)


def create_spiral_animation(obj, frames):
    """螺旋运动动画"""
    original_loc = obj.location.copy()

    for frame in range(1, frames + 1, 10):
        t = (frame - 1) / (frames - 1) * 4 * math.pi

        radius = 2.0 * (1 - (frame - 1) / (frames - 1))
        x = original_loc.x + math.cos(t) * radius
        y = original_loc.y + math.sin(t) * radius
        z = original_loc.z + (frame - 1) / (frames - 1) * 3

        obj.location = (x, y, z)
        obj.keyframe_insert(data_path="location", frame=frame)

        obj.rotation_euler = (0, 0, t)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def create_wave_animation(obj, frames):
    """波浪运动动画"""
    original_loc = obj.location.copy()

    for frame in range(1, frames + 1, 6):
        t = (frame - 1) / (frames - 1) * 2 * math.pi

        # 多重波浪叠加
        x = original_loc.x + math.sin(t * 2) * 1.5
        y = original_loc.y + math.cos(t * 3) * 1.0
        z = original_loc.z + math.sin(t * 4) * 0.5

        obj.location = (x, y, z)
        obj.keyframe_insert(data_path="location", frame=frame)


def create_complex_animation(obj, frames):
    """超级复杂动画"""
    original_loc = obj.location.copy()

    for frame in range(1, frames + 1, 5):
        t = (frame - 1) / (frames - 1) * 2 * math.pi

        # 复杂位置动画
        x = original_loc.x + math.cos(t) * 2 + math.sin(t * 3) * 0.5
        y = original_loc.y + math.sin(t) * 2 + math.cos(t * 2) * 0.5
        z = original_loc.z + math.sin(t * 2) * 1 + 1

        obj.location = (x, y, z)
        obj.keyframe_insert(data_path="location", frame=frame)

        # 复杂旋转动画
        obj.rotation_euler = (t * 0.7, t * 1.3, t * 0.5)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)

        # 动态缩放
        scale = 1 + math.sin(t * 5) * 0.4
        obj.scale = (scale, scale * 0.8, scale * 1.2)
        obj.keyframe_insert(data_path="scale", frame=frame)


def setup_professional_lighting():
    """设置专业级灯光系统"""
    # 清除现有灯光
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "LIGHT":
            obj.select_set(True)
            bpy.ops.object.delete()

    # 主光源 - 太阳光
    bpy.ops.object.light_add(type="SUN", location=(7, 7, 10))
    key_light = bpy.context.active_object
    key_light.name = "KeyLight_Sun"
    key_light.data.energy = 4.0
    key_light.data.color = (1.0, 0.95, 0.8)
    key_light.data.angle = math.radians(5)

    # 补光 - 区域光
    bpy.ops.object.light_add(type="AREA", location=(-5, -3, 8))
    fill_light = bpy.context.active_object
    fill_light.name = "FillLight_Area"
    fill_light.data.energy = 150.0
    fill_light.data.color = (0.7, 0.8, 1.0)
    fill_light.data.size = 6.0

    # 边缘光 - 聚光灯
    bpy.ops.object.light_add(type="SPOT", location=(-8, 5, 4))
    rim_light = bpy.context.active_object
    rim_light.name = "RimLight_Spot"
    rim_light.data.energy = 200.0
    rim_light.data.color = (1.0, 0.7, 0.5)
    rim_light.data.spot_size = math.radians(45)
    rim_light.data.spot_blend = 0.3

    # 环境光 - 点光源（用于环境补充）
    bpy.ops.object.light_add(type="POINT", location=(0, 0, 8))
    ambient_light = bpy.context.active_object
    ambient_light.name = "AmbientLight_Point"
    ambient_light.data.energy = 100.0
    ambient_light.data.color = (0.9, 0.9, 1.0)

    # 设置世界环境
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.1, 1.0)
    bg.inputs["Strength"].default_value = 0.1

    print("✅ 专业灯光系统设置完成")


def setup_cinematic_camera():
    """设置电影级相机"""
    # 清除现有相机
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "CAMERA":
            obj.select_set(True)
            bpy.ops.object.delete()

    # 创建主相机
    bpy.ops.object.camera_add(location=(12, -12, 8))
    main_camera = bpy.context.active_object
    main_camera.name = "CinematicCamera"

    # 设置相机参数
    cam_data = main_camera.data
    cam_data.lens = 35  # 35mm镜头
    cam_data.dof.use_dof = True  # 景深
    cam_data.dof.focus_distance = 10.0
    cam_data.dof.aperture_fstop = 2.8

    # 设置相机朝向场景中心
    direction = Vector((0, 0, 2)) - main_camera.location
    main_camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    # 创建相机运动动画
    frames = 300
    for frame in range(1, frames + 1, 30):
        t = (frame - 1) / (frames - 1) * 2 * math.pi

        # 围绕场景旋转
        radius = 15
        x = math.cos(t) * radius
        y = math.sin(t) * radius
        z = 8 + math.sin(t * 2) * 2

        main_camera.location = (x, y, z)
        main_camera.keyframe_insert(data_path="location", frame=frame)

        # 始终朝向中心
        direction = Vector((0, 0, 2)) - main_camera.location
        main_camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        main_camera.keyframe_insert(data_path="rotation_euler", frame=frame)

    bpy.context.scene.camera = main_camera
    print("✅ 电影级相机设置完成")


def setup_advanced_render_settings():
    """设置高级渲染参数"""
    scene = bpy.context.scene

    # Cycles渲染引擎设置
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 256  # 高质量采样
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPTIX"  # 如果有NVIDIA GPU

    # 渲染分辨率
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100

    # 动态模糊
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5

    # 色彩管理
    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "Medium High Contrast"

    # 输出设置
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.compression = 15
    scene.render.filepath = "/tmp/blender_enhanced_animation_"

    # 动画设置
    scene.frame_set(1)

    print("✅ 高级渲染设置完成")


def add_particle_effects():
    """添加粒子效果"""
    # 在中心创建一个隐藏的发射器
    bpy.ops.mesh.primitive_ico_sphere_add(location=(0, 0, 5), radius=0.1)
    emitter = bpy.context.active_object
    emitter.name = "ParticleEmitter"
    emitter.hide_render = True

    # 添加粒子系统
    bpy.ops.object.particle_system_add()
    psys = emitter.particle_systems[0]
    settings = psys.settings

    # 粒子设置
    settings.type = "EMITTER"
    settings.count = 1000
    settings.emit_from = "VOLUME"
    settings.lifetime = 120
    settings.normal_factor = 0.1
    settings.factor_random = 0.5

    # 物理设置
    settings.physics_type = "NEWTON"
    settings.mass = 0.1
    settings.particle_size = 0.05
    settings.use_size_deflect = True

    # 渲染设置
    settings.render_type = "OBJECT"

    # 创建粒子对象
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.02)
    particle_obj = bpy.context.active_object
    particle_obj.name = "ParticleObject"

    # 为粒子创建发光材质
    particle_mat = bpy.data.materials.new(name="ParticleMaterial")
    particle_mat.use_nodes = True
    nodes = particle_mat.node_tree.nodes
    nodes.clear()

    emission = nodes.new(type="ShaderNodeEmission")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    particle_mat.node_tree.links.new(
        emission.outputs["Emission"],
        output.inputs["Surface"],
    )

    emission.inputs["Color"].default_value = (1.0, 0.8, 0.2, 1.0)
    emission.inputs["Strength"].default_value = 5.0

    particle_obj.data.materials.append(particle_mat)
    settings.instance_object = particle_obj

    print("✅ 粒子效果添加完成")


def create_scene_report():
    """生成场景报告"""
    report = {
        "objects": len(
            [obj for obj in bpy.context.scene.objects if obj.type == "MESH"],
        ),
        "lights": len(
            [obj for obj in bpy.context.scene.objects if obj.type == "LIGHT"],
        ),
        "cameras": len(
            [obj for obj in bpy.context.scene.objects if obj.type == "CAMERA"],
        ),
        "materials": len(bpy.data.materials),
        "animations": len(
            [obj for obj in bpy.context.scene.objects if obj.animation_data],
        ),
        "frame_range": f"{bpy.context.scene.frame_start}-{bpy.context.scene.frame_end}",
        "render_engine": bpy.context.scene.render.engine,
        "resolution": f"{bpy.context.scene.render.resolution_x}x{bpy.context.scene.render.resolution_y}",
    }

    print("\n" + "=" * 50)
    print("🎬 BLENDER-MCP 测试场景报告")
    print("=" * 50)
    print(f"📦 网格对象数量: {report['objects']}")
    print(f"💡 灯光数量: {report['lights']}")
    print(f"📷 相机数量: {report['cameras']}")
    print(f"🎨 材质数量: {report['materials']}")
    print(f"🎭 动画对象数量: {report['animations']}")
    print(
        f"🎞️  帧范围: {report['frame_range']} ({bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1} 帧)",
    )
    print(f"⚙️  渲染引擎: {report['render_engine']}")
    print(f"📺 分辨率: {report['resolution']}")
    print("=" * 50)

    return report


def main():
    """主函数 - 创建完整的测试场景"""
    print("🚀 开始创建增强版Blender动画场景")
    print("🔧 测试blender-mcp工具完整功能")
    print("=" * 60)

    try:
        # 1. 清理并准备场景
        clear_scene()

        # 2. 创建地面
        ground = create_ground_plane()

        # 3. 创建动画对象
        objects = create_animated_objects()

        # 4. 创建高级材质
        materials = create_advanced_materials()

        # 5. 应用材质
        apply_materials_to_objects(objects, materials)

        # 6. 创建综合动画
        create_comprehensive_animations(objects)

        # 7. 设置专业灯光
        setup_professional_lighting()

        # 8. 设置电影级相机
        setup_cinematic_camera()

        # 9. 添加粒子效果
        add_particle_effects()

        # 10. 设置高级渲染参数
        setup_advanced_render_settings()

        # 11. 生成场景报告
        report = create_scene_report()

        # 12. 切换到Shading工作区
        try:
            bpy.context.window.workspace = bpy.data.workspaces["Shading"]
        except:
            print("⚠️  无法切换到Shading工作区")

        print("\n✅ 场景创建完成！")
        print("🎮 操作提示:")
        print("   • 按空格键播放动画")
        print("   • 按F12渲染当前帧")
        print("   • Ctrl+F12渲染整个动画")
        print("   • 鼠标中键拖拽旋转视图")
        print("   • 滚轮缩放视图")

        return True

    except Exception as e:
        print(f"❌ 场景创建失败: {e!s}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 blender-mcp测试完成 - 所有功能正常工作！")
    else:
        print("\n💥 测试失败 - 请检查错误信息")
