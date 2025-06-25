# WSL Blender MCP 开发环境配置脚本
# 配置WSL2 mirror模式、端口转发、防火墙规则
# 专门用于WSL开发环境与Windows Blender MCP通信
# 需要以管理员权限运行

param(
    [string]$WSLDistro = "Ubuntu",
    [int]$Port = 9876,
    [switch]$Remove = $false,
    [switch]$Status = $false,
    [switch]$ConfigureWSL = $true,
    [int]$Memory = 8,
    [int]$Processors = 4
)

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ 此脚本需要管理员权限运行" -ForegroundColor Red
    Write-Host "请以管理员身份运行PowerShell" -ForegroundColor Yellow
    exit 1
}

Write-Host "🔧 WSL Blender MCP 开发环境配置工具" -ForegroundColor Blue
Write-Host "=" * 50 -ForegroundColor Blue

# 检查Windows版本是否支持mirror模式
function Test-WindowsVersionForMirrorMode {
    $osVersion = [System.Environment]::OSVersion.Version
    $buildNumber = (Get-ItemProperty "HKLM:SOFTWARE\Microsoft\Windows NT\CurrentVersion").CurrentBuild
    
    Write-Host "🖥️  检查Windows版本..." -ForegroundColor Blue
    Write-Host "   Windows版本: $($osVersion.Major).$($osVersion.Minor) Build $buildNumber" -ForegroundColor Cyan
    
    # Windows 11 22H2 (Build 22621) 或更高版本支持mirror模式
    if ($buildNumber -ge 22621) {
        Write-Host "✅ Windows版本支持WSL2 mirror模式" -ForegroundColor Green
        return $true
    } else {
        Write-Host "⚠️  当前Windows版本不支持mirror模式，将使用传统端口转发" -ForegroundColor Yellow
        Write-Host "   建议升级到Windows 11 22H2或更高版本以获得最佳体验" -ForegroundColor Yellow
        return $false
    }
}

# 创建或更新.wslconfig文件
function Set-WSLConfig {
    param(
        [bool]$UseMirrorMode,
        [int]$Memory,
        [int]$Processors
    )
    
    $wslConfigPath = "$env:USERPROFILE\.wslconfig"
    Write-Host "📝 配置WSL设置文件: $wslConfigPath" -ForegroundColor Blue
    
    $configContent = @"
[wsl2]
# 内存限制 (GB)
memory=${Memory}GB

# 处理器核心数
processors=$Processors

# 网络模式
$(if ($UseMirrorMode) { "networkingMode=mirrored" } else { "# networkingMode=mirrored # 需要Windows 11 22H2+" })

# 禁用页面文件以提高性能
pageReporting=false

# 启用本地主机转发
localhostForwarding=true

# 启用DNS隧道
dnsTunneling=true

# 启用防火墙自动配置
autoProxy=true

$(if ($UseMirrorMode) { 
@"
# Mirror模式额外设置
[proxy]
# 当Windows使用代理时，自动应用到WSL
autoProxy=true
"@ })
"@

    try {
        $configContent | Out-File -FilePath $wslConfigPath -Encoding UTF8 -Force
        Write-Host "✅ .wslconfig配置文件已创建/更新" -ForegroundColor Green
        Write-Host "   配置内容:" -ForegroundColor Cyan
        Write-Host "   - 内存限制: ${Memory}GB" -ForegroundColor Cyan
        Write-Host "   - 处理器: $Processors 核心" -ForegroundColor Cyan
        Write-Host "   - 网络模式: $(if ($UseMirrorMode) { "Mirror模式" } else { "NAT模式（兼容模式）" })" -ForegroundColor Cyan
        return $true
    } catch {
        Write-Host "❌ 创建.wslconfig文件失败: $_" -ForegroundColor Red
        return $false
    }
}

$supportsMirrorMode = Test-WindowsVersionForMirrorMode

# 获取WSL IP地址
try {
    $wslIP = (wsl -d $WSLDistro hostname -I).Trim()
    Write-Host "✅ WSL IP地址: $wslIP" -ForegroundColor Green
} catch {
    Write-Host "❌ 无法获取WSL IP地址" -ForegroundColor Red
    Write-Host "请确保WSL正在运行且指定的发行版存在" -ForegroundColor Yellow
    exit 1
}

# 获取Windows主机IP
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -like "*WSL*" -or $_.InterfaceAlias -like "*vEthernet*"} | Select-Object -First 1).IPAddress
if (-not $windowsIP) {
    $windowsIP = "0.0.0.0"
}
Write-Host "✅ Windows主机IP: $windowsIP" -ForegroundColor Green

# 增强的网络诊断功能
function Test-NetworkConnectivity {
    param(
        [string]$WSLDistro,
        [int]$Port
    )
    
    Write-Host "🔍 网络连接诊断..." -ForegroundColor Blue
    
    # 1. 检查WSL状态
    try {
        $wslStatus = wsl -l -v | Select-String $WSLDistro
        Write-Host "✅ WSL发行版状态: $wslStatus" -ForegroundColor Green
    } catch {
        Write-Host "❌ 无法获取WSL状态" -ForegroundColor Red
    }
    
    # 2. 检查Windows网关IP（WSL访问Windows用这个IP）
    try {
        $gatewayIP = (wsl -d $WSLDistro ip route show default | Select-String "default").Line.Split()[2]
        Write-Host "🌐 Windows网关IP (WSL→Windows): $gatewayIP" -ForegroundColor Yellow
        
        # 测试从WSL到Windows的连接
        $testCmd = "nc -zv $gatewayIP $Port 2>&1 || telnet $gatewayIP $Port 2>&1 || timeout 3 bash -c '</dev/tcp/$gatewayIP/$Port' 2>&1"
        $testResult = wsl -d $WSLDistro bash -c $testCmd
        
        if ($testResult -match "succeeded|Connected|Connection.*established") {
            Write-Host "✅ WSL可以连接到Windows端口$Port" -ForegroundColor Green
        } else {
            Write-Host "⚠️  WSL无法连接到Windows端口$Port" -ForegroundColor Yellow
            Write-Host "   测试结果: $testResult" -ForegroundColor Gray
        }
    } catch {
        Write-Host "⚠️  网关连接测试失败: $_" -ForegroundColor Yellow
    }
    
    # 3. 检查端口占用
    $portInUse = netstat -an | Select-String ":$Port.*LISTENING"
    if ($portInUse) {
        Write-Host "✅ Windows端口$Port正在监听: $portInUse" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Windows端口$Port未在监听，请确保Blender插件已启动" -ForegroundColor Yellow
    }
}

# 状态查看功能（增强版）
if ($Status) {
    Write-Host "📊 WSL Blender MCP 环境状态" -ForegroundColor Green
    Write-Host "=" * 40 -ForegroundColor Green
    
    # 显示.wslconfig配置
    $wslConfigPath = "$env:USERPROFILE\.wslconfig"
    if (Test-Path $wslConfigPath) {
        Write-Host "📝 .wslconfig配置:" -ForegroundColor Blue
        Get-Content $wslConfigPath | ForEach-Object { Write-Host "   $_" -ForegroundColor Cyan }
    } else {
        Write-Host "⚠️  .wslconfig文件不存在" -ForegroundColor Yellow
    }
    
    # 显示所有端口代理
    Write-Host "`n📋 当前端口代理规则:" -ForegroundColor Blue
    $portProxy = netsh interface portproxy show v4tov4
    if ($portProxy) {
        $portProxy | ForEach-Object { Write-Host "   $_" -ForegroundColor Cyan }
    } else {
        Write-Host "   无端口代理规则" -ForegroundColor Gray
    }
    
    # 显示WSL IP
    try {
        $currentWSLIP = (wsl -d $WSLDistro hostname -I).Trim()
        Write-Host "`n🌐 当前WSL IP地址: $currentWSLIP" -ForegroundColor Yellow
    } catch {
        Write-Host "`n⚠️  无法获取WSL IP地址" -ForegroundColor Yellow
    }
    
    # 显示防火墙规则
    Write-Host "`n🔥 WSL相关防火墙规则:" -ForegroundColor Blue
    $firewallRules = Get-NetFirewallRule -DisplayName "*WSL*Blender*MCP*" -ErrorAction SilentlyContinue
    if ($firewallRules) {
        $firewallRules | Select-Object DisplayName, Enabled, Direction, Action | Format-Table | Out-String | ForEach-Object { Write-Host $_.Trim() -ForegroundColor Cyan }
    } else {
        Write-Host "   无相关防火墙规则" -ForegroundColor Gray
    }
    
    # 网络连接诊断
    Test-NetworkConnectivity -WSLDistro $WSLDistro -Port $Port
    
    exit 0
}

if ($Remove) {
    # 删除端口转发规则
    Write-Host "🗑️  删除端口转发规则..." -ForegroundColor Yellow
    
    try {
        # 删除netsh端口代理
        netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=$windowsIP
        Write-Host "✅ 已删除端口代理规则" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  删除端口代理规则失败或不存在" -ForegroundColor Yellow
    }
    
    try {
        # 删除防火墙规则
        Remove-NetFirewallRule -DisplayName "WSL Blender MCP Port $Port" -ErrorAction SilentlyContinue
        Write-Host "✅ 已删除防火墙规则" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  删除防火墙规则失败或不存在" -ForegroundColor Yellow
    }
    
    Write-Host "🎉 端口转发规则删除完成" -ForegroundColor Green
    exit 0
}

# 配置WSL环境
if ($ConfigureWSL) {
    Write-Host "`n🔧 配置WSL环境..." -ForegroundColor Green
    
    if (Set-WSLConfig -UseMirrorMode $supportsMirrorMode -Memory $Memory -Processors $Processors) {
        Write-Host "✅ WSL配置完成，建议重启WSL以应用更改" -ForegroundColor Green
        
        $restartChoice = Read-Host "是否现在重启WSL？(y/N)"
        if ($restartChoice -eq 'y' -or $restartChoice -eq 'Y') {
            Write-Host "🔄 重启WSL..." -ForegroundColor Blue
            try {
                wsl --shutdown
                Start-Sleep -Seconds 3
                wsl -d $WSLDistro echo "WSL已重启"
                Write-Host "✅ WSL重启完成" -ForegroundColor Green
                
                # 重新获取WSL IP
                try {
                    $wslIP = (wsl -d $WSLDistro hostname -I).Trim()
                    Write-Host "✅ 新的WSL IP地址: $wslIP" -ForegroundColor Green
                } catch {
                    Write-Host "⚠️  获取新WSL IP失败，将使用默认配置" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "⚠️  WSL重启可能失败: $_" -ForegroundColor Yellow
            }
        }
    }
}

# 创建端口转发规则（如果不使用mirror模式）
if (-not $supportsMirrorMode) {
    Write-Host "`n🚀 创建端口转发规则..." -ForegroundColor Green
    Write-Host "   从 $windowsIP:$Port 转发到 $wslIP:$Port" -ForegroundColor Cyan
} else {
    Write-Host "`n🌐 使用Mirror模式，跳过端口转发配置" -ForegroundColor Blue
    Write-Host "   WSL可以直接访问Windows的localhost:$Port" -ForegroundColor Cyan
}

# 1. 创建netsh端口代理（仅在非mirror模式下）
if (-not $supportsMirrorMode) {
    try {
        # 先删除可能存在的规则
        netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=$windowsIP 2>$null
        
        # 添加新规则
        netsh interface portproxy add v4tov4 listenport=$Port listenaddress=$windowsIP connectport=$Port connectaddress=$wslIP
        Write-Host "✅ 端口代理规则创建成功" -ForegroundColor Green
        
        # 显示当前规则
        Write-Host "📋 当前端口代理规则:" -ForegroundColor Blue
        netsh interface portproxy show v4tov4
    } catch {
        Write-Host "❌ 创建端口代理失败: $_" -ForegroundColor Red
    }
}

# 2. 配置防火墙规则
try {
    # 删除可能存在的规则
    Remove-NetFirewallRule -DisplayName "WSL Blender MCP Port $Port" -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName "WSL Blender MCP Port $Port Outbound" -ErrorAction SilentlyContinue
    
    # 添加入站规则
    New-NetFirewallRule -DisplayName "WSL Blender MCP Port $Port" -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow
    Write-Host "✅ 防火墙入站规则创建成功" -ForegroundColor Green
    
    # 添加出站规则
    New-NetFirewallRule -DisplayName "WSL Blender MCP Port $Port Outbound" -Direction Outbound -Protocol TCP -LocalPort $Port -Action Allow
    Write-Host "✅ 防火墙出站规则创建成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 创建防火墙规则失败: $_" -ForegroundColor Red
}

# 3. 测试连接
Write-Host "🔍 测试端口连接..." -ForegroundColor Blue
try {
    $testConnection = Test-NetConnection -ComputerName $wslIP -Port $Port -WarningAction SilentlyContinue
    if ($testConnection.TcpTestSucceeded) {
        Write-Host "✅ 端口连接测试成功" -ForegroundColor Green
    } else {
        Write-Host "⚠️  端口连接测试失败 - 可能Blender服务器未运行" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  无法测试端口连接" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 WSL Blender MCP 环境配置完成!" -ForegroundColor Green
Write-Host "📝 使用说明:" -ForegroundColor Blue

if ($supportsMirrorMode) {
    Write-Host "   💡 Mirror模式已启用，网络配置简化:" -ForegroundColor Yellow
    Write-Host "   - WSL中的应用可以直接连接到 localhost:$Port" -ForegroundColor Cyan
    Write-Host "   - 无需复杂的端口转发设置" -ForegroundColor Cyan
} else {
    Write-Host "   🔗 传统NAT模式，已配置端口转发:" -ForegroundColor Yellow
    Write-Host "   - WSL中的应用连接到 localhost:$Port" -ForegroundColor Cyan
    Write-Host "   - Windows应用连接到 $windowsIP:$Port" -ForegroundColor Cyan
    Write-Host "   - 重启WSL后可能需要重新运行此脚本" -ForegroundColor Yellow
}

Write-Host "   - 查看状态: .\wsl_setup.ps1 -Status" -ForegroundColor Cyan
Write-Host "   - 删除配置: .\wsl_setup.ps1 -Remove" -ForegroundColor Cyan
Write-Host "   - 配置WSL: .\wsl_setup.ps1 -Memory 16 -Processors 8" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 下一步:" -ForegroundColor Blue
Write-Host "   1. 启动Blender并确保插件监听端口$Port" -ForegroundColor Cyan
Write-Host "   2. 在WSL中运行 'python main.py' 启动MCP服务器" -ForegroundColor Cyan
Write-Host "   3. 使用 '.\wsl_setup.ps1 -Status' 验证连接" -ForegroundColor Cyan