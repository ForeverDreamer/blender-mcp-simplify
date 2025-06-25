#!/bin/bash

# WSL环境下重启Blender的脚本
# 功能：调用Windows宿主机的PowerShell 7重启Blender，并实时查看控制台日志

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置路径
PWSH_PATH="/mnt/c/Program Files/PowerShell/7/pwsh.exe"
BLENDER_PATH="/mnt/d/Program Files/Blender Foundation/Blender 4.4/blender.exe"
PROJECT_PATH="${1:-projects/linear_algebra/Linear_systems_in_two_unknowns/assets/Main.blend}"
TEMP_DIR="/tmp/blender_wsl_$$"

# 创建临时目录
mkdir -p "$TEMP_DIR"

# 清理函数
cleanup() {
    echo -e "${YELLOW}🧹 清理临时文件...${NC}"
    rm -rf "$TEMP_DIR"
    # 杀死可能残留的Blender进程
    /mnt/c/Windows/System32/taskkill.exe //F //IM blender.exe //T 2>/dev/null || true
}

# 设置退出时清理
trap cleanup EXIT

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  WSL Blender 重启控制脚本${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "${CYAN}项目文件: $PROJECT_PATH${NC}"
echo -e "${CYAN}时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# 检查PowerShell 7是否存在
if [ ! -f "$PWSH_PATH" ]; then
    echo -e "${RED}❌ 错误: PowerShell 7 未找到: $PWSH_PATH${NC}"
    echo -e "${YELLOW}请确保PowerShell 7已安装到默认位置${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 找到PowerShell 7: $PWSH_PATH${NC}"

# 检查Blender是否存在
if [ ! -f "$BLENDER_PATH" ]; then
    echo -e "${RED}❌ 错误: Blender 未找到: $BLENDER_PATH${NC}"
    echo -e "${YELLOW}请检查Blender安装路径${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 找到Blender: $BLENDER_PATH${NC}"

# 创建PowerShell启动脚本
cat > "$TEMP_DIR/start_blender.ps1" << 'EOF'
param(
    [string]$BlenderPath,
    [string]$ProjectPath = ""
)

# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 设置环境变量
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "🚀 WSL Blender 启动器 (PowerShell 7)" -ForegroundColor Blue
Write-Host "===========================================" -ForegroundColor Blue

# 日志函数
function Write-LogMessage {
    param(
        [string]$Message,
        [string]$Type = "INFO",
        [ConsoleColor]$Color = "White"
    )
    $timestamp = Get-Date -Format 'HH:mm:ss'
    Write-Host "[$timestamp] [$Type] $Message" -ForegroundColor $Color
}

# 杀死现有Blender进程
Write-LogMessage "检查并结束现有Blender进程..." "CLEANUP" "Yellow"
try {
    Get-Process -Name "blender" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-LogMessage "已结束现有Blender进程" "CLEANUP" "Green"
} catch {
    Write-LogMessage "没有找到运行中的Blender进程" "CLEANUP" "Cyan"
}

# 创建Blender初始化脚本
$initScript = @"
# -*- coding: utf-8 -*-
import sys
import os
import bpy
import time

# 设置编码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

print("🔧 Blender MCP 环境初始化")
print("=" * 50)
print(f"⏰ 启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📂 工作目录: {os.getcwd()}")
print(f"🐍 Python版本: {sys.version}")
print(f"🎨 Blender版本: {bpy.app.version_string}")
print(f"🎯 当前场景: {bpy.context.scene.name}")
print(f"📦 场景对象数: {len(bpy.context.scene.objects)}")

# 尝试启动MCP服务器
print("\n🔌 MCP服务器初始化...")
try:
    # 检查插件是否加载
    if hasattr(bpy.ops, 'blendermcp'):
        print("✅ BlenderMCP插件已加载")
        
        # 尝试重启服务器
        try:
            bpy.ops.blendermcp.emergency_stop()
            print("🛑 已停止现有MCP服务器")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️  停止服务器时出现警告: {e}")
        
        # 启动新的服务器实例
        try:
            bpy.ops.blendermcp.restart_server()
            print("🚀 MCP服务器重启命令已执行")
            time.sleep(2)
            
            # 验证服务器状态
            print("🔍 验证服务器状态...")
            # 这里可以添加服务器状态检查逻辑
            
        except Exception as e:
            print(f"❌ 启动MCP服务器失败: {e}")
    else:
        print("⚠️  BlenderMCP插件未找到或未正确加载")
        print("   请检查插件是否已正确安装并启用")
        
except Exception as e:
    print(f"❌ MCP初始化失败: {e}")

print("\n✨ 初始化完成！")
print("=" * 50)
print("📝 所有后续操作的日志将在此控制台显示")
print("🔄 您现在可以通过MCP工具与Blender交互")
print("💡 提示: 使用Ctrl+C可以优雅退出")
"@

# 保存初始化脚本到临时文件
$tempScriptPath = [System.IO.Path]::GetTempFileName() + ".py"
$initScript | Out-File -FilePath $tempScriptPath -Encoding utf8

Write-LogMessage "创建初始化脚本: $tempScriptPath" "CREATE" "Cyan"

# 构建Blender启动参数
$blenderArgs = @(
    "--python-use-system-env"
    "--python", "`"$tempScriptPath`""
)

# 如果指定了项目文件，添加到参数中
if ($ProjectPath -and $ProjectPath -ne "") {
    $blenderArgs += "`"$ProjectPath`""
    Write-LogMessage "加载项目文件: $ProjectPath" "PROJECT" "Green"
}

Write-LogMessage "正在启动Blender..." "START" "Green"
Write-Host ""
Write-Host "=================== Blender 实时日志 ===================" -ForegroundColor Magenta
Write-Host ""

try {
    # 启动Blender并等待其完成
    $process = Start-Process -FilePath "`"$BlenderPath`"" -ArgumentList $blenderArgs -NoNewWindow -Wait -PassThru
    
    Write-Host ""
    Write-LogMessage "Blender进程已退出，退出代码: $($process.ExitCode)" "END" "Yellow"
    
} catch {
    Write-LogMessage "启动Blender时发生错误: $_" "ERROR" "Red"
} finally {
    # 清理临时文件
    if (Test-Path $tempScriptPath) {
        Remove-Item $tempScriptPath -Force
        Write-LogMessage "已清理临时脚本文件" "CLEANUP" "Green"
    }
}

Write-LogMessage "PowerShell会话结束" "END" "Cyan"
EOF

# 将路径转换为Windows格式
WINDOWS_BLENDER_PATH=$(echo "$BLENDER_PATH" | sed 's|/mnt/\([a-z]\)/|\1:/|' | sed 's|/|\\|g')
WINDOWS_PROJECT_PATH=""

if [ -n "$PROJECT_PATH" ]; then
    # 检查项目路径是否存在
    FULL_PROJECT_PATH="/mnt/d/data_files/video_scripts/$PROJECT_PATH"
    if [ -f "$FULL_PROJECT_PATH" ]; then
        WINDOWS_PROJECT_PATH=$(echo "$FULL_PROJECT_PATH" | sed 's|/mnt/\([a-z]\)/|\1:/|' | sed 's|/|\\|g')
        echo -e "${GREEN}✅ 找到项目文件: $FULL_PROJECT_PATH${NC}"
    else
        echo -e "${YELLOW}⚠️  项目文件不存在: $FULL_PROJECT_PATH${NC}"
        echo -e "${YELLOW}   将启动Blender默认场景${NC}"
    fi
fi

echo ""
echo -e "${YELLOW}🔄 正在结束现有Blender进程...${NC}"
/mnt/c/Windows/System32/taskkill.exe //F //IM blender.exe //T 2>/dev/null || true
sleep 2

echo -e "${GREEN}🚀 启动Blender (通过PowerShell 7)...${NC}"
echo -e "${CYAN}命令: pwsh.exe -File start_blender.ps1${NC}"
echo ""

# 启动PowerShell脚本并实时显示输出
cd "$TEMP_DIR"
"$PWSH_PATH" -NoProfile -ExecutionPolicy Bypass -File "start_blender.ps1" -BlenderPath "$WINDOWS_BLENDER_PATH" -ProjectPath "$WINDOWS_PROJECT_PATH"

echo ""
echo -e "${GREEN}✨ 脚本执行完成${NC}"