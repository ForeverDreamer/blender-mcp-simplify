"""
工具测试脚本

用于测试 Blender MCP 工具的基本功能。
"""

import json

# 使用绝对导入
from src.tools.base_tools import get_scene_info, get_server_status
from src.tools.code_tools import (
    execute_code,
    execute_script_file,
    list_available_scripts,
)
from src.tools.polyhaven_tools import (
    download_polyhaven_asset_impl,
    search_polyhaven_assets_impl,
)


def test_scene_info():
    """测试获取场景信息"""
    print("测试获取场景信息...")
    result = get_scene_info()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("-" * 50)


def test_server_status():
    """测试获取服务器状态"""
    print("测试获取服务器状态...")
    result = get_server_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("-" * 50)


def test_execute_code():
    """测试执行Blender代码"""
    print("测试执行代码...")
    test_code = """
import bpy
cube = bpy.data.objects.get('Cube')
if cube:
    cube.location.z += 1
    print(f"提升了立方体的Z坐标，新位置: {cube.location}")
else:
    print("未找到名为'Cube'的对象")
"""
    result = execute_code(test_code)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("-" * 50)


def test_execute_script_file():
    """测试执行脚本文件"""
    print("测试执行脚本文件...")
    # 尝试执行 final_test.py 脚本
    script_name = "final_test.py"
    parameters = {
        "cube_size": 2.5,
        "add_materials": True,
    }
    result = execute_script_file(script_name, "scripts", parameters)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("-" * 50)


def test_list_scripts():
    """测试列出可用脚本"""
    print("测试列出脚本...")
    result = list_available_scripts()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("-" * 50)


def test_search_polyhaven_assets():
    """测试搜索PolyHaven资产"""
    print("测试搜索PolyHaven资产...")
    # 搜索材质资产
    result = search_polyhaven_assets_impl(None, "hdri", "outdoor")
    print(result)
    print("-" * 50)

    # 搜索3D模型资产
    result = search_polyhaven_assets_impl(None, "model", "furniture")
    print(result)
    print("-" * 50)


def test_download_polyhaven_asset():
    """测试下载PolyHaven资产"""
    print("测试下载PolyHaven资产...")
    # 下载HDRI环境贴图
    result = download_polyhaven_asset_impl(
        None,
        "abandoned_factory_canteen",
        "hdri",
        "2k",
    )
    print(result)
    print("-" * 50)

    # 下载3D模型
    result = download_polyhaven_asset_impl(
        None,
        "couch_03",
        "model",
        file_format="blend",
    )
    print(result)
    print("-" * 50)


if __name__ == "__main__":
    print("开始 Blender MCP 工具测试")
    print("=" * 50)

    test_scene_info()
    test_server_status()
    test_execute_code()
    test_execute_script_file()
    test_list_scripts()
    test_search_polyhaven_assets()
    test_download_polyhaven_asset()

    print("测试完成")
