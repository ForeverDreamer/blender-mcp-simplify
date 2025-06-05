# Blender MCP调试和测试脚本 (PowerShell) - 优化版
Write-Host "Blender MCP调试和测试脚本 - 控制台日志优化版" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# 设置控制台编码为UTF-8以正确显示中文
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 设置工作目录
$scriptPath = $MyInvocation.MyCommand.Path
$currentDir = Split-Path -Parent $scriptPath
Set-Location $currentDir

Write-Host "当前工作目录: $currentDir" -ForegroundColor Cyan

# Global variable to track cancellation
$global:IsCancelled = $false
$global:BlenderProcess = $null
$global:LogWriter = $null

# 测试结果配置
$addonPath = (Resolve-Path ".\").Path
$testResultsDir = "$addonPath\test_results"

# 确保测试结果目录存在
if (-not (Test-Path $testResultsDir)) {
    New-Item -ItemType Directory -Path $testResultsDir | Out-Null
    Write-Host "创建测试结果目录: $testResultsDir" -ForegroundColor Yellow
}

# 生成时间戳
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$testResultsDir\test_log_$timestamp.txt"
$testBlendFile = "$testResultsDir\test_result_$timestamp.blend"

# 实时日志写入函数
function Write-LogMessage {
    param(
        [string]$Message,
        [string]$Type = "INFO",
        [ConsoleColor]$Color = "White"
    )
    
    $timestampMsg = "[$(Get-Date -Format 'HH:mm:ss')] [$Type] $Message"
    
    # 显示在控制台
    Write-Host $timestampMsg -ForegroundColor $Color
    
    # 写入日志文件
    if ($global:LogWriter -ne $null) {
        try {
            $global:LogWriter.WriteLine($timestampMsg)
            $global:LogWriter.Flush()
        } catch {
            # 如果日志写入失败，不要影响主流程
        }
    }
}

# Enhanced Ctrl+C handler
function Initialize-CancellationHandler {
    # Create a console control handler to catch Ctrl+C
    Add-Type -TypeDefinition @"
    using System;
    using System.Runtime.InteropServices;
    
    public class ConsoleHandler {
        [DllImport("kernel32.dll")]
        public static extern bool SetConsoleCtrlHandler(HandlerRoutine Handler, bool Add);
        
        public delegate bool HandlerRoutine(int dwCtrlType);
        
        public static bool Handler(int dwCtrlType) {
            if (dwCtrlType == 0 || dwCtrlType == 2) { // CTRL_C_EVENT or CTRL_CLOSE_EVENT
                Console.WriteLine("");
                Console.WriteLine("Ctrl+C detected - Shutting down Blender...");
                return true; // Handled
            }
            return false;
        }
    }
"@
    
    # Set the handler
    $handler = [ConsoleHandler]::Handler
    [ConsoleHandler]::SetConsoleCtrlHandler($handler, $true)
}

# Function to check for cancellation
function Test-Cancellation {
    if ($global:IsCancelled) {
        Write-LogMessage "操作已被用户取消" "CANCEL" "Yellow"
        if ($global:BlenderProcess -and -not $global:BlenderProcess.HasExited) {
            Write-LogMessage "正在终止Blender进程..." "TERMINATE" "Yellow"
            try {
                $global:BlenderProcess.Kill()
                $global:BlenderProcess.WaitForExit(5000) # Wait up to 5 seconds
            } catch {
                Write-LogMessage "终止Blender进程时出错: $_" "ERROR" "Red"
            }
        }
        exit 0
    }
}

# Set Blender path (modify according to your installation)
$BlenderPath = "D:\Program Files\Blender Foundation\Blender 4.4\blender.exe"

# Check if Blender exists
if (-not (Test-Path $BlenderPath)) {
    Write-LogMessage "错误: Blender可执行文件未找到: $BlenderPath" "ERROR" "Red"
    Write-Host "请修改脚本中的BlenderPath变量指向正确的Blender安装路径" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "常见Blender路径:" -ForegroundColor Cyan
    Write-Host "- C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"
    Write-Host "- C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
    Write-Host "- D:\Blender\blender.exe"
    Read-Host "按Enter键退出"
    exit 1
}

# Function to close existing Blender instances
function Close-BlenderInstances {
    Write-LogMessage "检查已有的Blender实例..." "CHECK" "Yellow"
    Test-Cancellation
    
    $blenderProcesses = Get-Process -Name "blender" -ErrorAction SilentlyContinue
    
    if ($blenderProcesses) {
        Write-LogMessage "发现 $($blenderProcesses.Count) 个运行中的Blender实例 - 自动关闭中..." "CLEANUP" "Cyan"
        Write-Host "可随时按Ctrl+C取消" -ForegroundColor DarkGray
        
        foreach ($process in $blenderProcesses) {
            Write-LogMessage "关闭进程ID: $($process.Id), 启动时间: $($process.StartTime)" "CLEANUP" "Gray"
        }
        
        Write-LogMessage "正在关闭现有Blender实例..." "CLEANUP" "Yellow"
        
        foreach ($process in $blenderProcesses) {
            Test-Cancellation
            try {
                # Try graceful shutdown first
                $process.CloseMainWindow() | Out-Null
                
                # Wait up to 5 seconds for graceful shutdown with cancellation checks
                $timeout = 50  # 5 seconds in 100ms intervals
                while ($timeout -gt 0 -and -not $process.HasExited) {
                    Test-Cancellation
                    Start-Sleep -Milliseconds 100
                    $timeout--
                }
                
                if (-not $process.HasExited) {
                    Write-LogMessage "强制终止进程ID: $($process.Id)" "FORCE_KILL" "Red"
                    $process.Kill()
                } else {
                    Write-LogMessage "已正常关闭进程ID: $($process.Id)" "CLEANUP" "Green"
                }
            } catch {
                Write-LogMessage "关闭进程ID $($process.Id) 时出错: $_" "ERROR" "Red"
            }
        }
        
        # Wait a moment for processes to fully terminate
        Write-LogMessage "等待进程完全终止..." "WAIT" "DarkGray"
        for ($i = 0; $i -lt 20; $i++) {
            Test-Cancellation
            Start-Sleep -Milliseconds 100
        }
        
        # Verify all instances are closed
        $remainingProcesses = Get-Process -Name "blender" -ErrorAction SilentlyContinue
        if ($remainingProcesses) {
            Write-LogMessage "警告: 仍有部分Blender进程在运行" "WARNING" "Red"
            foreach ($process in $remainingProcesses) {
                Write-LogMessage "进程ID: $($process.Id)" "WARNING" "Red"
            }
        } else {
            Write-LogMessage "已成功关闭所有Blender实例" "SUCCESS" "Green"
        }
    } else {
        Write-LogMessage "未发现正在运行的Blender实例" "INFO" "Green"
    }
    
    Write-Host ""
}

# 创建保存测试结果的Python脚本
function Create-SaveResultScript {
    $saveFilePythonCode = @"
import bpy
import sys
import time

# 保存测试结果到blend文件
try:
    bpy.ops.wm.save_as_mainfile(filepath='$testBlendFile')
    print(f"[SAVE] 测试结果已保存到: $testBlendFile")
except Exception as e:
    print(f"[ERROR] 保存结果时出错: {e}")

# 不再自动退出Blender
print("[INFO] Blender将保持运行，请手动关闭或使用控制台中的Ctrl+C结束进程")
"@

    $saveFilePythonPath = "$testResultsDir\save_test_results.py"
    $saveFilePythonCode | Out-File -FilePath $saveFilePythonPath -Encoding utf8
    Write-LogMessage "创建保存结果脚本: $saveFilePythonPath" "CREATE" "Yellow"
    return $saveFilePythonPath
}

# Initialize log writer
try {
    $global:LogWriter = New-Object System.IO.StreamWriter($logFile, $false, [System.Text.Encoding]::UTF8)
    Write-LogMessage "日志文件初始化: $logFile" "INIT" "Cyan"
} catch {
    Write-Host "警告: 无法创建日志文件 - 仅控制台输出" -ForegroundColor Yellow
    $global:LogWriter = $null
}

# Initialize Ctrl+C handler
Initialize-CancellationHandler

# Close existing Blender instances
Close-BlenderInstances

# Set environment variables for better debugging
Write-LogMessage "设置调试环境变量..." "ENV" "Yellow"
Test-Cancellation
$env:PYDEVD_DISABLE_FILE_VALIDATION = "1"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-LogMessage "正在启动Blender调试模式..." "START" "Green"
Test-Cancellation
Write-Host ""
Write-Host "注意事项:" -ForegroundColor Cyan
Write-Host "- Blender将以调试模式启动"
Write-Host "- 已启用更好的断点支持"
Write-Host "- 已最小化调试器警告"
Write-Host "- 在控制台按Ctrl+C停止Blender（增强支持）"
Write-Host "- 所有通信和执行日志将实时显示在控制台"
Write-Host ""

# 打印调试信息
Write-LogMessage "当前目录: $currentDir" "INFO" "Cyan"
Write-LogMessage "插件路径: $addonPath" "INFO" "Cyan"
Write-LogMessage "Blender: $BlenderPath" "INFO" "Cyan"
Write-LogMessage "测试结果: $testResultsDir" "INFO" "Cyan"
Write-LogMessage "日志文件: $logFile" "INFO" "Cyan"

# Start Blender with better process management
try {
    Test-Cancellation
    
    # 创建保存结果脚本
    $saveFilePythonPath = Create-SaveResultScript
    
    # MCP插件目录路径
    $addonDir = Join-Path -Path (Get-Location) -ChildPath "addon"
    $mcp_init_script = @"
# -*- coding: utf-8 -*-
import sys
import os
import bpy
import time
import traceback
import json

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 打印调试信息
print("[MCP_INIT] MCP启动脚本执行中...")
print(f"[MCP_INIT] 当前工作目录: {os.getcwd()}")
print(f"[MCP_INIT] Python版本: {sys.version}")
print(f"[MCP_INIT] Blender版本: {bpy.app.version_string}")

# 添加插件路径
addon_path = r'$addonDir'
if addon_path not in sys.path:
    sys.path.append(addon_path)
print(f"[MCP_INIT] 添加插件路径: {addon_path}")

# 启用MCP插件
addon_name = "blender-mcp"  # 修正为正确的插件名称
print(f"[MCP_INIT] 尝试启用MCP插件: {addon_name}")

# 检查插件是否已安装
if addon_name not in bpy.context.preferences.addons:
    try:
        print(f"[MCP_INIT] 启用MCP插件: {addon_name}")
        bpy.ops.preferences.addon_enable(module=addon_name)
        
        # 确保插件被启用
        if addon_name in bpy.context.preferences.addons:
            print("[MCP_INIT] MCP插件已成功启用")
        else:
            print("[MCP_INIT] 警告: 无法启用MCP插件，尝试备用方法")
            
            # 备用方法：直接从addon目录加载
            import sys
            import importlib
            if addon_path not in sys.path:
                sys.path.append(addon_path)
            try:
                if 'addon' in sys.modules:
                    importlib.reload(sys.modules['addon'])
                else:
                    import addon
                print("[MCP_INIT] 通过直接导入加载了addon模块")
            except Exception as e:
                print(f"[MCP_INIT] 备用加载方法也失败: {e}")
                traceback.print_exc()
    except Exception as e:
        print(f"[MCP_INIT] 启用插件时出错: {e}")
        traceback.print_exc()
else:
    print("[MCP_INIT] MCP插件已经启用")

# 等待插件完全加载
print("[MCP_INIT] 等待插件完全加载...")
time.sleep(3)

# 确保MCP服务器启动
if hasattr(bpy.ops, 'blendermcp'):
    print("[MCP_SERVER] 启动MCP服务器...")
    try:
        # 先尝试停止现有服务器
        try:
            bpy.ops.blendermcp.emergency_stop()
            time.sleep(2)  # 等待服务器停止
            print("[MCP_SERVER] 已停止现有服务器实例")
        except:
            pass
        # 启动服务器
        bpy.ops.blendermcp.restart_server()
        print("[MCP_SERVER] MCP服务器启动命令已执行")
        
        # 等待服务器启动
        time.sleep(5)
        print("[MCP_SERVER] 等待服务器完全启动...")
        
    except Exception as e:
        print(f"[MCP_SERVER] 启动MCP服务器时出错: {e}")
        traceback.print_exc()
else:
    print("[MCP_SERVER] 警告: blendermcp操作不可用，插件可能未正确加载")

# 执行测试脚本
scripts_dir = os.path.join(os.path.dirname(addon_path), "scripts")
test_scripts = [
    "test_mcp_fixes.py",  # 测试UI更新修复
    "test_queue_printing.py"  # 测试队列打印修复
]

for script_name in test_scripts:
    test_script_path = os.path.join(scripts_dir, script_name)
    print(f"\n[SCRIPT_TEST] 尝试执行测试脚本: {test_script_path}")
    
    if os.path.exists(test_script_path):
        try:
            print(f"[SCRIPT_TEST] ===== 开始执行测试脚本: {script_name} =====")
            with open(test_script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            exec(script_content)
            print(f"[SCRIPT_TEST] ===== 测试脚本 {script_name} 执行完成 =====")
            # 等待3秒以观察效果
            time.sleep(3)
        except Exception as e:
            print(f"[SCRIPT_TEST] 测试脚本 {script_name} 执行失败: {e}")
            traceback.print_exc()
    else:
        print(f"[SCRIPT_TEST] 测试脚本不存在: {test_script_path}")

# 执行保存结果脚本路径
save_script_path = r'$saveFilePythonPath'
print(f"[SAVE_RESULT] 准备执行结果保存脚本: {save_script_path}")
if os.path.exists(save_script_path):
    try:
        print("[SAVE_RESULT] ===== 开始保存测试结果 =====")
        with open(save_script_path, 'r', encoding='utf-8') as f:
            save_script_content = f.read()
        exec(save_script_content)
        print("[SAVE_RESULT] ===== 保存测试结果完成 =====")
    except Exception as e:
        print(f"[SAVE_RESULT] 保存测试结果失败: {e}")
        traceback.print_exc()
else:
    print(f"[SAVE_RESULT] 保存结果脚本不存在: {save_script_path}")

print("[MCP_INIT] MCP启动脚本执行完成")
print("[MCP_INIT] Blender将保持运行状态，请手动关闭Blender窗口或在控制台使用Ctrl+C终止进程")
print("[MCP_INIT] 所有日志将继续显示在控制台中...")
"@

    # 将初始化脚本保存到临时文件
    $tempScriptPath = [System.IO.Path]::GetTempFileName() + ".py"
    $mcp_init_script | Out-File -FilePath $tempScriptPath -Encoding utf8

    Write-LogMessage "创建MCP初始化脚本: $tempScriptPath" "CREATE" "Cyan"
    
    # Start Blender as a separate process with optimized output handling
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = $BlenderPath
    $processInfo.Arguments = "--python-use-system-env --python `"$tempScriptPath`""
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $false
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    # 设置编码
    $processInfo.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $processInfo.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    
    Write-LogMessage "正在启动Blender并实时显示日志..." "START" "Green"
    
    # 创建进程
    $global:BlenderProcess = New-Object System.Diagnostics.Process
    $global:BlenderProcess.StartInfo = $processInfo
    
    # 优化的输出处理 - 使用同步输出以确保实时性
    $global:BlenderProcess.EnableRaisingEvents = $true
    
    # 创建输出数据接收事件处理器
    $outputAction = {
        param($sender, $e)
        if ($e.Data -ne $null -and $e.Data.Trim() -ne "") {
            $data = $e.Data
            
            # 根据日志前缀设置颜色
            $color = "White"
            $logType = "BLENDER"
            
            if ($data -match "\[MCP_") {
                $color = "Cyan"
                $logType = "MCP"
            }
            elseif ($data -match "\[SCRIPT_") {
                $color = "Yellow"
                $logType = "SCRIPT"
            }
            elseif ($data -match "\[SERVER") {
                $color = "Green"
                $logType = "SERVER"
            }
            elseif ($data -match "\[ERROR") {
                $color = "Red"
                $logType = "ERROR"
            }
            elseif ($data -match "\[WARNING") {
                $color = "Yellow"
                $logType = "WARNING"
            }
            elseif ($data -match "\[DEBUG") {
                $color = "DarkGray"
                $logType = "DEBUG"
            }
            
            Write-LogMessage $data $logType $color
        }
    }
    
    $errorAction = {
        param($sender, $e)
        if ($e.Data -ne $null -and $e.Data.Trim() -ne "") {
            Write-LogMessage $e.Data "BLENDER_ERROR" "Red"
        }
    }
    
    # 注册事件处理器
    Register-ObjectEvent -InputObject $global:BlenderProcess -EventName OutputDataReceived -Action $outputAction | Out-Null
    Register-ObjectEvent -InputObject $global:BlenderProcess -EventName ErrorDataReceived -Action $errorAction | Out-Null
    
    # 启动进程和输出捕获
    $global:BlenderProcess.Start() | Out-Null
    $global:BlenderProcess.BeginOutputReadLine()
    $global:BlenderProcess.BeginErrorReadLine()
    
    Write-LogMessage "Blender已启动，进程ID: $($global:BlenderProcess.Id)" "START" "Green"
    
    # 等待几秒钟让服务器启动
    Write-LogMessage "等待MCP服务器启动..." "WAIT" "Yellow"
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 500
        # 检查Ctrl+C
        if ([Console]::KeyAvailable) {
            $keyInfo = [Console]::ReadKey($true)
            if ($keyInfo.Key -eq [ConsoleKey]::C -and $keyInfo.Modifiers -eq [ConsoleModifiers]::Control) {
                Write-LogMessage "Ctrl+C detected - 正在终止Blender..." "TERMINATE" "Yellow"
                $global:IsCancelled = $true
                Test-Cancellation
                break
            }
        }
    }
    
    if (-not $global:IsCancelled) {
        # 提示用户Blender正在运行
        Write-LogMessage "Blender正在运行中，MCP服务器已启动" "RUNNING" "Green"
        Write-LogMessage "所有通信和执行日志将实时显示在控制台中" "INFO" "Cyan"
        Write-LogMessage "如需终止进程，请返回控制台按Ctrl+C" "INFO" "Yellow"
        
        # 等待用户按下Ctrl+C
        Write-Host "`n按Ctrl+C可以随时终止Blender进程..." -ForegroundColor Cyan
        Write-Host "所有MCP通信和脚本执行日志将在下方实时显示：" -ForegroundColor Green
        Write-Host "=================== 实时日志输出 ===================" -ForegroundColor Magenta
        
        # 等待用户的中断信号
        try {
            while (-not $global:IsCancelled -and -not $global:BlenderProcess.HasExited) {
                Start-Sleep -Seconds 1
                
                # 检查键盘输入
                if ([Console]::KeyAvailable) {
                    $keyInfo = [Console]::ReadKey($true)
                    if ($keyInfo.Key -eq [ConsoleKey]::C -and $keyInfo.Modifiers -eq [ConsoleModifiers]::Control) {
                        Write-LogMessage "Ctrl+C detected - 正在终止Blender..." "TERMINATE" "Yellow"
                        $global:IsCancelled = $true
                        Test-Cancellation
                        break
                    }
                }
            }
            
            # 检查进程是否已退出
            if ($global:BlenderProcess.HasExited -and -not $global:IsCancelled) {
                Write-LogMessage "Blender已退出，退出代码: $($global:BlenderProcess.ExitCode)" "EXIT" "Yellow"
            }
        } 
        catch {
            Write-LogMessage "监控Blender进程时出错: $_" "ERROR" "Red"
        }
    }
    
} catch {
    if ($global:IsCancelled) {
        Write-LogMessage "Blender启动已取消" "CANCEL" "Yellow"
    } else {
        Write-LogMessage "启动Blender时出错: $_" "ERROR" "Red"
        Write-LogMessage "堆栈跟踪: $($_.Exception.StackTrace)" "ERROR" "DarkRed"
    }
} finally {
    Write-Host "`n=================== 清理资源 ===================" -ForegroundColor Magenta
    
    # Cleanup
    if ($global:BlenderProcess -and -not $global:BlenderProcess.HasExited) {
        try {
            Write-LogMessage "清理Blender进程..." "CLEANUP" "Yellow"
            $global:BlenderProcess.Kill()
            $global:BlenderProcess.WaitForExit(3000)
        } catch {
            Write-LogMessage "警告: 无法清理Blender进程: $_" "WARNING" "Yellow"
        }
    }
    
    # 取消注册所有事件订阅
    try {
        Get-EventSubscriber | Where-Object {$_.SourceObject -eq $global:BlenderProcess} | Unregister-Event -ErrorAction SilentlyContinue
    } catch {
        Write-LogMessage "清理事件订阅时出错: $_" "WARNING" "Yellow"
    }
    
    # 确保日志文件关闭
    if ($global:LogWriter -ne $null) {
        try { 
            $global:LogWriter.Close() 
            Write-LogMessage "日志文件已关闭" "CLEANUP" "Green"
        } catch {}
    }
    
    # 清理临时脚本文件
    try {
        if (Test-Path $tempScriptPath) {
            Remove-Item $tempScriptPath -Force
            Write-LogMessage "临时脚本已清理" "CLEANUP" "Green"
        }
    } catch {
        Write-LogMessage "清理临时脚本失败: $_" "WARNING" "Yellow"
    }
}

# 显示测试结果
if (-not $global:IsCancelled) {
    Write-Host "`n=================== 测试结果摘要 ===================" -ForegroundColor Magenta
    
    if (Test-Path $logFile) {
        Write-LogMessage "查看日志文件最后20行内容:" "SUMMARY" "Magenta"
        Get-Content $logFile -Tail 20 -Encoding UTF8 | ForEach-Object {
            Write-Host $_ -ForegroundColor DarkGray
        }
        Write-LogMessage "完整日志已保存到: $logFile" "SUMMARY" "Cyan"
    }
    
    if (Test-Path $testBlendFile) {
        Write-LogMessage "测试结果已保存到: $testBlendFile" "SUCCESS" "Green"
    } else {
        Write-LogMessage "警告: 未能保存测试结果文件" "WARNING" "Yellow"
    }
    
    Write-LogMessage "测试完成" "COMPLETE" "Cyan"
    Write-Host "如需查看完整结果，请打开保存的blend文件: $testBlendFile" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
} else {
    Write-LogMessage "操作已被用户取消" "CANCEL" "Yellow"
}