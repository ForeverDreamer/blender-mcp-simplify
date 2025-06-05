# 项目特定的PowerShell配置文件
# 保存位置: .vscode/ps-project-profile.ps1

# 设置一个标志变量防止重复加载
if ($global:PS_PROJECT_PROFILE_LOADED) {
    # 如果已加载过，则只执行必要的环境设置
    return
}

# 设置标志表示配置已加载
$global:PS_PROJECT_PROFILE_LOADED = $true

# =====================================================================
# Python虚拟环境管理
# =====================================================================

# Python相关函数
# function Start-PythonVenv {
#     if (Test-Path .\backend\.venv\Scripts\Activate.ps1) {
#         & .\backend\.venv\Scripts\Activate.ps1
#     }
#     elseif (Test-Path .\.venv\Scripts\Activate.ps1) {
#         & .\.venv\Scripts\Activate.ps1
#     }
#     elseif (Test-Path .\venv\Scripts\Activate.ps1) {
#         & .\venv\Scripts\Activate.ps1
#     }
#     else {
#         Write-Warning "找不到虚拟环境，请先创建虚拟环境"
#     }
# }

# Set-Alias -Name venv -Value Start-PythonVenv

# 检查uv是否已安装，如果没有则提供安装指南
function Check-UvInstalled {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "未找到uv工具，建议按以下步骤安装uv：" -ForegroundColor Yellow
        Write-Host "1. 使用pip安装:" -ForegroundColor Yellow
        Write-Host "   pip install uv" -ForegroundColor Cyan
        Write-Host "2. 或使用官方安装脚本:" -ForegroundColor Yellow
        Write-Host "   iwr https://astral.sh/uv/install.ps1 -useb | iex" -ForegroundColor Cyan
        Write-Host "3. 安装后重启终端或运行 . `$PROFILE 重新加载配置" -ForegroundColor Yellow
        Write-Host ""
        return $false
    }
    return $true
}

# 添加uv相关功能 (如果有安装)
$uvInstalled = Check-UvInstalled
if ($uvInstalled) {
    # 为uv创建别名和函数
    function Install-UvPackage {
        param (
            [Parameter(Mandatory=$true)]
            [string]$PackageName
        )
        
        uv add $PackageName
    }
    
    Set-Alias -Name uva -Value Install-UvPackage
    
    # 添加一个函数用于快速启动uv虚拟环境
    function Start-UvVenv {
        if (Test-Path .\backend\.venv\Scripts\Activate.ps1) {
            & .\backend\.venv\Scripts\Activate.ps1
        }
        elseif (Test-Path .\.venv\Scripts\Activate.ps1) {
            & .\.venv\Scripts\Activate.ps1
        }
        else {
            Write-Warning "找不到uv虚拟环境，尝试创建..."
            uv venv .venv
            if (Test-Path .\.venv\Scripts\Activate.ps1) {
                & .\.venv\Scripts\Activate.ps1
            }
        }
    }
    
    Set-Alias -Name uvv -Value Start-UvVenv
}
else {
    # 提供通用Python虚拟环境创建函数（使用标准venv模块）
    function New-PythonVenv {
        param (
            [Parameter(Mandatory=$false)]
            [string]$EnvName = ".venv"
        )
        
        python -m venv $EnvName
        if (Test-Path .\$EnvName\Scripts\Activate.ps1) {
            & .\$EnvName\Scripts\Activate.ps1
        }
    }
    
    Set-Alias -Name mkvenv -Value New-PythonVenv
}

# =====================================================================
# 设置项目特定别名
# =====================================================================

# 设置项目特定别名
# Set-Alias -Name runapi -Value Start-ApiServer
# Set-Alias -Name runweb -Value Start-WebServer

# 启动API服务器函数
# function Start-ApiServer {
#     $apiPath = Join-Path (Get-Location) "backend"
#     if (Test-Path $apiPath) {
#         Set-Location $apiPath
#         Write-Host "启动FastAPI服务器..." -ForegroundColor Green
#         uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
#     }
#     else {
#         Write-Warning "无法找到API服务器目录: $apiPath"
#     }
# }

# # 启动Web服务器函数
# function Start-WebServer {
#     $webPath = Join-Path (Get-Location) "frontend"
#     if (Test-Path $webPath) {
#         Set-Location $webPath
#         if (Test-Path (Join-Path $webPath "package.json")) {
#             Write-Host "启动Web应用..." -ForegroundColor Green
#             yarn dev
#         }
#         else {
#             Write-Warning "Web应用目录中找不到package.json"
#         }
#     }
#     else {
#         Write-Warning "无法找到Web应用目录: $webPath"
#     }
# }

# =====================================================================
# Conda环境管理（如果需要）
# =====================================================================

# 设置Conda不自动激活base环境
if (Get-Command conda -ErrorAction SilentlyContinue) {
    conda config --set auto_activate_base false | Out-Null
    
    # 自定义Conda激活命令
    function Activate-Conda {
        param (
            [Parameter(Mandatory=$false)]
            [string]$EnvName = "base"
        )
        
        conda activate $EnvName
    }
    
    # 为Conda常用命令设置别名
    Set-Alias -Name cona -Value Activate-Conda
    Set-Alias -Name cond -Value conda
}

# =====================================================================
# 欢迎信息
# =====================================================================

# function Show-ProjectWelcome {
#     # 显示项目信息
#     Write-Host ""
#     Write-Host "项目开发环境已就绪" -ForegroundColor Cyan
#     $projectName = Split-Path -Leaf (Get-Location)
#     Write-Host "当前项目: $projectName" -ForegroundColor Green
#     Write-Host "可用命令:" -ForegroundColor Yellow
#     Write-Host "  venv    - 激活Python虚拟环境" -ForegroundColor DarkCyan
#     Write-Host "  uvv     - 使用uv创建并激活虚拟环境" -ForegroundColor DarkCyan
#     Write-Host "  runapi  - 启动后端API服务器" -ForegroundColor DarkCyan
#     Write-Host "  runweb  - 启动前端Web服务器" -ForegroundColor DarkCyan
#     Write-Host ""
    
#     # 检测并显示Python版本
#     if (Get-Command python -ErrorAction SilentlyContinue) {
#         $pythonVersion = (python --version 2>&1).ToString().Replace("Python ", "")
#         Write-Host "Python: $pythonVersion" -ForegroundColor Green
#     }
    
#     # 显示uv版本（如果存在）
#     if (Get-Command uv -ErrorAction SilentlyContinue) {
#         $uvVersion = (uv --version 2>&1).ToString()
#         Write-Host "uv: $uvVersion" -ForegroundColor Green
#     }
    
#     # 检查是否已激活虚拟环境
#     if ($env:VIRTUAL_ENV) {
#         $venvName = Split-Path -Leaf $env:VIRTUAL_ENV
#         Write-Host "已激活虚拟环境: $venvName" -ForegroundColor Green
#     }
    
#     Write-Host ""
# }

# 显示项目欢迎信息（仅首次加载时）
# Show-ProjectWelcome 