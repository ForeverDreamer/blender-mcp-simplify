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
                    # 验证IP地址格式
                    if ip and not ip.startswith("127."):
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
    
    try:
        # 方法3: 使用 hostname -I 获取 WSL 网卡地址的网关
        result = subprocess.run(
            ["hostname", "-I"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            wsl_ip = result.stdout.strip().split()[0]
            # 通常 Windows 主机 IP 是 WSL IP 的 .1
            ip_parts = wsl_ip.split('.')
            ip_parts[-1] = '1'
            return '.'.join(ip_parts)
    except:
        pass
    
    # 默认回退 - 常见的 WSL2 网关地址
    return "192.168.112.1"  # 根据实际环境设置


def is_wsl():
    """检测是否在WSL环境中运行"""
    return (
        os.path.exists("/proc/version") and 
        "microsoft" in open("/proc/version").read().lower()
    )


def get_blender_host():
    """获取Blender服务器主机地址"""
    if is_wsl():
        # 使用Windows宿主机IP地址
        return get_windows_host_ip()
    else:
        return "localhost"


# 配置常量
BLENDER_HOST = get_blender_host()
BLENDER_PORT = 9876
BLENDER_TIMEOUT = 30.0  # 增加超时时间以提高连接稳定性

# 代理模式配置（临时解决方案）
USE_PROXY = False  # 设置为 True 使用本地代理
PROXY_PORT = 9877  # 本地代理端口

print(f"[CONFIG] 检测到运行环境: {'WSL' if is_wsl() else 'Native'}")
print(f"[CONFIG] Blender主机地址: {BLENDER_HOST}")