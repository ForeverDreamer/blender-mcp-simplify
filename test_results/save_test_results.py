import bpy
import sys
import time

# 保存测试结果到blend文件
try:
    bpy.ops.wm.save_as_mainfile(filepath='D:\data_files\mcps\blender-mcp-simplify\test_results\test_result_20250605_192706.blend')
    print(f"[SAVE] 测试结果已保存到: D:\data_files\mcps\blender-mcp-simplify\test_results\test_result_20250605_192706.blend")
except Exception as e:
    print(f"[ERROR] 保存结果时出错: {e}")

# 不再自动退出Blender
print("[INFO] Blender将保持运行，请手动关闭或使用控制台中的Ctrl+C结束进程")
