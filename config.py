"""
配置文件 - Blender MCP跨平台设置

自动检测运行环境并配置正确的连接参数
"""
import os
import socket
import subprocess


def get_windows_host_ip():
    """
    获取Windows宿主机IP地址（在WSL环境中）
    """
    try:
        # 方法1: 从 /etc/resolv.conf 获取
        with open("/etc/resolv.conf", "r") as f:
            for line in f:
                if line.startswith("nameserver"):
                    ip = line.split()[1].strip()
                    return ip
    except:
        pass
    
    try:
        # 方法2: 从默认路由获取
        result = subprocess.run(
            ["ip", "route", "show", "default"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'default via' in line:
                    ip = line.split()[2]
                    return ip
    except:
        pass
    
    # 默认回退
    return "192.168.112.1"


def is_wsl():
    """检测是否在WSL环境中运行"""
    return (
        os.path.exists("/proc/version") and 
        "microsoft" in open("/proc/version").read().lower()
    )


def get_blender_host():
    """获取Blender服务器主机地址"""
    if is_wsl():
        return get_windows_host_ip()
    else:
        return "localhost"


# 配置常量
BLENDER_HOST = get_blender_host()
BLENDER_PORT = 9876
BLENDER_TIMEOUT = 10.0

print(f"[CONFIG] 检测到运行环境: {'WSL' if is_wsl() else 'Native'}")
print(f"[CONFIG] Blender主机地址: {BLENDER_HOST}")