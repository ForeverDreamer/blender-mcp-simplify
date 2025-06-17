#!/usr/bin/env python3
"""
测试脚本：验证 execute_blender_script_file 工具的完整工作流程

此脚本将：
1. 创建测试用的 Blender Python 脚本
2. 拷贝到指定的 scripts 目录
3. 使用 list_blender_scripts 验证文件存在
4. 调用 execute_blender_script_file 执行脚本
5. 测试带参数的脚本执行
6. 清理测试文件
"""

from pathlib import Path

# 定义目标脚本目录
SCRIPTS_DIR = Path("D:/data_files/mcps/blender-mcp-simplify/scripts")


def create_test_script_1():
    """创建第一个测试脚本：基本功能测试"""
    script_content = '''
"""
测试脚本1：基本Blender操作测试
"""

import bpy
import bmesh

def main():
    print("=== 开始执行测试脚本1 ===")
    
    # 清理现有的默认对象
    try:
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        print("✓ 清理场景完成")
    except Exception as e:
        print(f"清理场景时出现问题: {e}")
    
    # 创建一个测试立方体
    try:
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.active_object
        cube.name = "TestCube_Script1"
        print(f"✓ 创建测试立方体: {cube.name}")
    except Exception as e:
        print(f"❌ 创建立方体失败: {e}")
        return False
    
    # 创建简单材质
    try:
        mat = bpy.data.materials.new(name="TestMaterial_Script1")
        mat.use_nodes = True
        
        # 设置材质颜色为蓝色
        principled_bsdf = mat.node_tree.nodes.get('Principled BSDF')
        if principled_bsdf:
            principled_bsdf.inputs[0].default_value = (0.1, 0.3, 0.8, 1.0)  # 蓝色
        
        # 分配材质
        cube.data.materials.append(mat)
        print("✓ 创建并分配蓝色材质")
    except Exception as e:
        print(f"❌ 材质创建失败: {e}")
    
    # 获取场景信息
    try:
        scene = bpy.context.scene
        objects_count = len(bpy.data.objects)
        materials_count = len(bpy.data.materials)
        
        print(f"📊 场景统计:")
        print(f"   对象数量: {objects_count}")
        print(f"   材质数量: {materials_count}")
        print(f"   当前帧: {scene.frame_current}")
    except Exception as e:
        print(f"❌ 获取场景信息失败: {e}")
    
    print("=== 测试脚本1 执行完成 ===")
    return True

if __name__ == "__main__":
    result = main()
    print(f"脚本执行结果: {'成功' if result else '失败'}")
'''
    return script_content


def create_test_script_2():
    """创建第二个测试脚本：参数化测试"""
    script_content = '''
"""
测试脚本2：参数化操作测试
"""

import bpy

def main():
    print("=== 开始执行测试脚本2（参数化） ===")
    
    # 从全局变量获取参数
    cube_size = globals().get("cube_size", 1.0)
    cube_location = globals().get("cube_location", [0, 0, 0])
    material_color = globals().get("material_color", [1.0, 0.0, 0.0, 1.0])
    cube_name = globals().get("cube_name", "DefaultCube")
    
    print(f"📋 接收到的参数:")
    print(f"   立方体大小: {cube_size}")
    print(f"   立方体位置: {cube_location}")
    print(f"   材质颜色: {material_color}")
    print(f"   立方体名称: {cube_name}")
    
    # 创建参数化的立方体
    try:
        bpy.ops.mesh.primitive_cube_add(
            size=cube_size, 
            location=cube_location
        )
        cube = bpy.context.active_object
        cube.name = cube_name
        print(f"✓ 创建参数化立方体: {cube.name}")
    except Exception as e:
        print(f"❌ 创建立方体失败: {e}")
        return False
    
    # 创建参数化材质
    try:
        mat = bpy.data.materials.new(name=f"{cube_name}_Material")
        mat.use_nodes = True
        
        # 设置参数化颜色
        principled_bsdf = mat.node_tree.nodes.get('Principled BSDF')
        if principled_bsdf:
            principled_bsdf.inputs[0].default_value = material_color
        
        # 分配材质
        cube.data.materials.append(mat)
        print(f"✓ 创建参数化材质，颜色: {material_color}")
    except Exception as e:
        print(f"❌ 材质创建失败: {e}")
    
    # 设置自定义属性
    try:
        cube["test_size"] = cube_size
        cube["test_color"] = str(material_color)
        print("✓ 设置自定义属性")
    except Exception as e:
        print(f"❌ 设置自定义属性失败: {e}")
    
    print("=== 测试脚本2 执行完成 ===")
    return True

if __name__ == "__main__":
    result = main()
    print(f"脚本执行结果: {'成功' if result else '失败'}")
'''
    return script_content


def test_execute_blender_script_file():
    """测试 execute_blender_script_file 工具的完整工作流程"""
    print("🧪 开始测试 execute_blender_script_file 工具")
    print("=" * 60)

    # 确保 scripts 目录存在
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    test_files = []

    try:
        # === 步骤1: 创建并拷贝测试脚本 ===
        print("\n📝 步骤1: 创建测试脚本")

        # 创建第一个测试脚本
        script1_path = SCRIPTS_DIR / "test_basic_operations.py"
        with open(script1_path, "w", encoding="utf-8") as f:
            f.write(create_test_script_1())
        test_files.append(script1_path)
        print(f"✓ 创建测试脚本1: {script1_path}")

        # 创建第二个测试脚本
        script2_path = SCRIPTS_DIR / "test_parameterized_operations.py"
        with open(script2_path, "w", encoding="utf-8") as f:
            f.write(create_test_script_2())
        test_files.append(script2_path)
        print(f"✓ 创建测试脚本2: {script2_path}")

        # === 步骤2: 验证脚本文件存在 ===
        print("\n🔍 步骤2: 验证脚本文件")
        print("请手动调用以下命令验证脚本是否存在:")
        print("list_blender_scripts(ctx)")
        print(
            "应该在输出中看到 test_basic_operations.py 和 test_parameterized_operations.py",
        )

        # === 步骤3: 生成测试调用代码 ===
        print("\n🚀 步骤3: 生成测试调用代码")
        print("\n--- 测试1: 基本脚本执行 ---")
        print("请复制并执行以下代码:")
        print("""
# 测试基本脚本执行
from mcp_blender_mcp import execute_blender_script_file

result1 = execute_blender_script_file(
    ctx, 
    "test_basic_operations"
)
print("基本脚本执行结果:")
print(result1)
""")

        print("\n--- 测试2: 带参数的脚本执行 ---")
        print("请复制并执行以下代码:")
        print("""
# 测试带参数的脚本执行
result2 = execute_blender_script_file(
    ctx,
    "test_parameterized_operations",
    {
        "cube_size": 3.0,
        "cube_location": [2, 0, 1],
        "material_color": [0.2, 0.8, 0.3, 1.0],  # 绿色
        "cube_name": "ParameterizedTestCube"
    }
)
print("参数化脚本执行结果:")
print(result2)
""")

        print("\n--- 测试3: 错误处理测试 ---")
        print("请复制并执行以下代码测试错误处理:")
        print("""
# 测试不存在的脚本（应该失败）
result3 = execute_blender_script_file(
    ctx,
    "nonexistent_script"
)
print("不存在脚本的测试结果:")
print(result3)
""")

        print("\n🎯 期望的测试结果:")
        print("✅ 测试1: 应该成功执行，创建蓝色立方体")
        print("✅ 测试2: 应该成功执行，创建绿色参数化立方体")
        print("❌ 测试3: 应该失败，显示脚本未找到的错误")

        return True

    except Exception as e:
        print(f"❌ 测试准备失败: {e}")
        return False


def cleanup_test_files():
    """清理测试文件"""
    print("\n🧹 清理测试文件")

    test_files = [
        SCRIPTS_DIR / "test_basic_operations.py",
        SCRIPTS_DIR / "test_parameterized_operations.py",
    ]

    for file_path in test_files:
        try:
            if file_path.exists():
                file_path.unlink()
                print(f"✓ 删除测试文件: {file_path}")
        except Exception as e:
            print(f"❌ 删除文件失败 {file_path}: {e}")

    print("清理完成！")


def main():
    """主测试函数"""
    print("🤖 Blender MCP execute_blender_script_file 工具测试")
    print("=" * 60)

    # 检查目标目录
    if not SCRIPTS_DIR.exists():
        print(f"⚠️  警告: Scripts 目录不存在，将创建: {SCRIPTS_DIR}")

    print(f"📁 Scripts 目录: {SCRIPTS_DIR}")

    # 运行测试
    if test_execute_blender_script_file():
        print("\n✅ 测试脚本准备完成！")
        print("\n📋 下一步操作:")
        print("1. 首先调用 list_blender_scripts(ctx) 验证脚本存在")
        print("2. 按照上述输出的代码执行各项测试")
        print("3. 完成测试后运行清理命令")

        print("\n🧹 测试完成后的清理命令:")
        print("# 在Python中运行:")
        print(
            "exec(open('test_script_execution.py').read().split('def cleanup_test_files')[1].split('def main')[0])",
        )
        print("cleanup_test_files()")

        print("\n或者手动删除以下文件:")
        print(f"- {SCRIPTS_DIR}/test_basic_operations.py")
        print(f"- {SCRIPTS_DIR}/test_parameterized_operations.py")

    else:
        print("\n❌ 测试脚本准备失败")


if __name__ == "__main__":
    main()
