# Blender MCP 插件同步脚本
# 将 src 和 addon 目录的文件同步到 Blender 插件目录

param(
    [string]$BlenderPluginPath = "C:\Users\doer\AppData\Roaming\Blender Foundation\Blender\4.4\scripts\addons\blender-mcp"
)

# 设置错误处理
$ErrorActionPreference = 'Stop'

# 获取当前脚本目录的绝对路径
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $ScriptDir "src"
$AddonDir = Join-Path $ScriptDir "addon"

Write-Host "🔄 开始同步 Blender MCP 插件文件..." -ForegroundColor Green

try {
    # 验证源目录是否存在
    if (!(Test-Path $SrcDir)) {
        throw "源目录不存在: $SrcDir"
    }
    
    if (!(Test-Path $AddonDir)) {
        throw "插件目录不存在: $AddonDir"
    }
    
    Write-Host "📁 源目录验证完成" -ForegroundColor Yellow
    Write-Host "   - src: $SrcDir"
    Write-Host "   - addon: $AddonDir"
    
    # 创建目标目录（如果不存在）
    if (!(Test-Path $BlenderPluginPath)) {
        Write-Host "📁 创建目标目录: $BlenderPluginPath" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $BlenderPluginPath -Force | Out-Null
    }
    
    # 复制 src 目录的所有文件
    Write-Host "📋 复制 src 目录文件..." -ForegroundColor Cyan
    Copy-Item -Path "$SrcDir\*" -Destination $BlenderPluginPath -Recurse -Force
    
    # 复制 addon 目录的所有文件
    Write-Host "📋 复制 addon 目录文件..." -ForegroundColor Cyan
    Copy-Item -Path "$AddonDir\*" -Destination $BlenderPluginPath -Recurse -Force
    
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
