# 精简版Blender调试脚本 (PowerShell)
Write-Host "Blender调试脚本 - 精简版" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green

# 1. 设置PowerShell控制台为UTF-8编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 设置工作目录
$scriptPath = $MyInvocation.MyCommand.Path
$currentDir = Split-Path -Parent $scriptPath
Set-Location $currentDir

Write-Host "当前工作目录: $currentDir" -ForegroundColor Cyan

# 简单日志函数
function Write-LogMessage {
    param(
        [string]$Message,
        [string]$Type = "INFO",
        [ConsoleColor]$Color = "White"
    )
    
    $timestampMsg = "[$(Get-Date -Format 'HH:mm:ss')] [$Type] $Message"
    Write-Host $timestampMsg -ForegroundColor $Color
}

# 设置Blender路径 (根据实际安装位置修改)
$BlenderPath = "D:\Program Files\Blender Foundation\Blender 4.4\blender.exe"

# 检查Blender是否存在
if (-not (Test-Path $BlenderPath)) {
    Write-LogMessage "错误: Blender可执行文件未找到: $BlenderPath" "ERROR" "Red"
    Write-Host "请修改脚本中的BlenderPath变量指向正确的Blender安装路径" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

# 创建简化版Python日志脚本
$loggingScript = @"
# -*- coding: utf-8 -*-
import sys
import os
import bpy

# 设置编码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

print("===== Blender Python调试环境初始化 =====")
print(f"当前工作目录: {os.getcwd()}")
print(f"Python版本: {sys.version}")
print(f"Blender版本: {bpy.app.version_string}")

# 确保MCP服务器启动
if hasattr(bpy.ops, 'blendermcp'):
    print("尝试启动MCP服务器...")
    try:
        # 先尝试停止现有服务器
        try:
            bpy.ops.blendermcp.emergency_stop()
            print("已停止现有服务器实例")
        except:
            pass
        # 启动服务器
        bpy.ops.blendermcp.restart_server()
        print("MCP服务器启动命令已执行")
    except Exception as e:
        print(f"启动MCP服务器时出错: {e}")
else:
    print("警告: blendermcp操作不可用，插件可能未正确加载")

print("===== 初始化完成 =====")
print("所有Python脚本执行的日志将实时显示在控制台")
"@

# 将初始化脚本保存到临时文件
$tempScriptPath = [System.IO.Path]::GetTempFileName() + ".py"
$loggingScript | Out-File -FilePath $tempScriptPath -Encoding utf8

Write-LogMessage "创建日志脚本: $tempScriptPath" "CREATE" "Cyan"

# 设置环境变量以改进调试
Write-LogMessage "设置调试环境变量..." "ENV" "Yellow"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"

# 启动Blender (直接方式，输出将显示在控制台)
Write-LogMessage "正在启动Blender..." "START" "Green"
Write-Host "`n=================== Blender日志输出 ===================" -ForegroundColor Magenta

# 使用&操作符直接启动Blender，输出将直接显示在控制台
& $BlenderPath --python-use-system-env --python "$tempScriptPath"

# 清理临时脚本文件
if (Test-Path $tempScriptPath) {
    Remove-Item $tempScriptPath -Force
    Write-LogMessage "临时脚本已清理" "CLEANUP" "Green"
}

Write-LogMessage "脚本执行完毕" "END" "Cyan" 