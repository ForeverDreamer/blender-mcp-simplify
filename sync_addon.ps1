# Blender MCP 插件同步脚本
# 将 addon/__init__.py 和 scripts/utils.py 同步到 Blender 插件目录

param(
    [string]$BlenderPluginPath = "C:\Users\doer\AppData\Roaming\Blender Foundation\Blender\4.4\scripts\addons\blender-mcp"
)

# 设置错误处理
$ErrorActionPreference = 'Stop'

# 获取当前脚本目录的绝对路径
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AddonDir = Join-Path $ScriptDir "addon"
$InitPyFile = Join-Path $AddonDir "__init__.py"
$ScriptsDir = Join-Path $ScriptDir "scripts"
$UtilsFile = Join-Path $ScriptsDir "utils.py"

Write-Host "🔄 开始同步 Blender MCP 插件文件..." -ForegroundColor Green

try {
    if (!(Test-Path $AddonDir)) {
        throw "插件目录不存在: $AddonDir"
    }
    
    if (!(Test-Path $InitPyFile)) {
        throw "插件初始化文件不存在: $InitPyFile"
    }
    
    if (!(Test-Path $UtilsFile)) {
        throw "工具模块不存在: $UtilsFile"
    }
    
    Write-Host "📁 源文件验证完成" -ForegroundColor Yellow
    Write-Host "   - 插件初始化文件: $InitPyFile"
    Write-Host "   - 工具模块: $UtilsFile"
    
    # 创建目标目录（如果不存在）
    if (!(Test-Path $BlenderPluginPath)) {
        Write-Host "📁 创建目标目录: $BlenderPluginPath" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $BlenderPluginPath -Force | Out-Null
    }
    
    # 复制 __init__.py 文件
    Write-Host "📋 复制 addon/__init__.py 文件..." -ForegroundColor Cyan
    Copy-Item -Path $InitPyFile -Destination $BlenderPluginPath -Force
    
    # 复制 utils.py 文件
    Write-Host "📋 复制 utils.py 到插件目录..." -ForegroundColor Cyan
    Copy-Item -Path $UtilsFile -Destination $BlenderPluginPath -Force
    
    Write-Host "✅ 同步完成！所有文件已复制到: $BlenderPluginPath" -ForegroundColor Green
    
    # 显示目标目录内容
    Write-Host "`n📄 目标目录文件列表:" -ForegroundColor Magenta
    Get-ChildItem -Path $BlenderPluginPath | ForEach-Object {
        if ($_.PSIsContainer) {
            Write-Host "   [DIR]  $($_.Name)" -ForegroundColor Blue
        } else {
            Write-Host "   [FILE] $($_.Name)" -ForegroundColor White
        }
    }
    
} catch {
    Write-Host "❌ 同步失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
