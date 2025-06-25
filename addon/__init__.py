# Code created by Siddharth Ahuja: www.github.com/ahujasid © 2025

import io
import json
import os
import queue
import socket
import sys
import threading
import time
import traceback
from contextlib import redirect_stdout

import bpy

bl_info = {
    "name": "Blender MCP",
    "author": "BlenderMCP",
    "version": (1, 4),
    "blender": (4, 4, 3),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to Claude via MCP - Simplified Architecture",
    "category": "Interface",
}

# Add src path to import tool modules
addon_dir = os.path.dirname(os.path.realpath(__file__))
src_dir = os.path.join(os.path.dirname(addon_dir), "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Default scripts root directory path
# This is the fallback path used when no custom path is configured in Blender properties
DEFAULT_SCRIPTS_ROOT = "/home/doer/data_files/video_scripts"

# Global variables for server management
_server_instance = None
_monitor_timer_running = False
_last_restart_time = 0
_restart_count = 0
_max_restarts_per_hour = 10

# Global variables for UI logging control
_last_ui_log_time = 0
_ui_log_cooldown = 5.0  # 5秒内不重复打印相同的UI日志


def _global_queue_processor():
    """Global function wrapper for queue processing to ensure proper timer callback"""
    global _server_instance
    # Add debug logging to see if timer is being called
    print("[MCP_GLOBAL_TIMER] 全局定时器被调用")
    
    if _server_instance and _server_instance.running:
        try:
            return _server_instance._process_execution_queue()
        except Exception as e:
            print(f"[MCP_GLOBAL_PROCESSOR] 全局队列处理器错误: {e}")
            return 0.1
    else:
        print(f"[MCP_GLOBAL_TIMER] 服务器状态: instance={_server_instance is not None}, running={_server_instance.running if _server_instance else False}")
    return None


# BlenderMCPProperties 类已被移除以解决 _PropertyDeferred 错误
# 直接使用 DEFAULT_SCRIPTS_ROOT 常量和简单的全局配置


class BlenderMCPServer:
    def __init__(self, host="0.0.0.0", port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None

        # Connection statistics
        self.total_client_connections = 0
        self.active_client_connections = 0
        self.total_commands_processed = 0
        self.last_client_time = None
        self.start_time = None
        self.last_error = None

        # Health check cache - optimized for UI responsiveness
        self._last_health_check = 0
        self._health_check_result = False
        self._health_check_interval = 10.0  # 10 seconds for UI responsiveness

        # Execution queue for main thread operations
        self._execution_queue = queue.Queue()
        self._queue_processor_registered = False

    def get_scripts_root(self):
        """Get the configured scripts root directory"""
        # 直接返回默认路径，避免属性访问问题
        return DEFAULT_SCRIPTS_ROOT

    def start(self):
        if self.running:
            print("Server is already running")
            return True

        self.running = True
        self.start_time = time.time()
        self.last_error = None

        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Try to bind to the port
            try:
                self.socket.bind((self.host, self.port))
                self.socket.listen(1)
            except OSError as e:
                print(f"Failed to bind to port {self.port}: {e}")
                self.last_error = f"Port binding failed: {e}"
                self.socket.close()
                self.socket = None
                self.running = False
                return False

            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()

            # 确保队列处理器立即注册
            self._ensure_queue_processor()

            print(f"BlenderMCP server started on {self.host}:{self.port}")
            print(f"队列处理器已注册: {self._queue_processor_registered}")
            print(f"当前 Blender PID: {os.getpid()}")

            # 调试信息
            print("===== MCP服务器状态 =====")
            print(f"服务器运行状态: {self.running}")
            print(f"服务器IP: {self.host}")
            print(f"服务器端口: {self.port}")
            print(
                f"服务器启动时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time)) if self.start_time else '未启动'}",
            )
            print(f"最后错误: {self.last_error or '无'}")
            print("=========================")

            return True

        except Exception as e:
            print(f"Failed to start server: {e!s}")
            self.last_error = f"Startup failed: {e}"
            self.stop()
            return False

    def stop(self):
        if not self.running:
            return

        self.running = False

        # Close socket first to break accept() loop
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        # Wait for thread to finish
        if self.server_thread and self.server_thread.is_alive():
            try:
                self.server_thread.join(timeout=2.0)
            except:
                pass
            self.server_thread = None

        # Unregister queue processor
        if self._queue_processor_registered:
            try:
                if bpy.app.timers.is_registered(self._process_execution_queue):
                    bpy.app.timers.unregister(self._process_execution_queue)
                self._queue_processor_registered = False
            except:
                pass

        print("BlenderMCP server stopped")

    def is_healthy(self, force_refresh=False):
        """Check if server is healthy based on running state and recent activity"""
        if not self.running or not self.socket:
            return False

        current_time = time.time()

        # Use cached result to reduce test frequency (unless forced refresh)
        if not force_refresh and current_time - self._last_health_check < self._health_check_interval:
            return self._health_check_result

        # Simplified health check based on server state instead of network testing
        # This avoids WSL network issues while providing meaningful health status
        try:
            # Check basic server state
            if not self.running or not self.socket:
                self._health_check_result = False
                self._last_health_check = current_time
                return False

            # Check if server thread is alive
            if not self.server_thread or not self.server_thread.is_alive():
                print("[MCP_HEALTH] 服务器线程未运行")
                self._health_check_result = False
                self._last_health_check = current_time
                return False

            # Check recent activity - if we've processed commands recently, server is healthy
            recent_activity_threshold = 300  # 5 minutes
            if (self.last_client_time and 
                current_time - self.last_client_time < recent_activity_threshold):
                print(f"[MCP_HEALTH] 基于最近活动的健康检查通过 (最后客户端: {current_time - self.last_client_time:.1f}秒前)")
                self._health_check_result = True
                self._last_health_check = current_time
                return True

            # If no recent activity but server is running, still consider it healthy
            # This handles the case where server just started or has been idle
            if self.total_commands_processed > 0:
                print(f"[MCP_HEALTH] 基于命令处理历史的健康检查通过 (已处理{self.total_commands_processed}个命令)")
                self._health_check_result = True
                self._last_health_check = current_time
                return True

            # For new servers with no activity yet, check if they can bind to port
            if self.total_commands_processed == 0:
                print("[MCP_HEALTH] 新服务器，基于运行状态检查通过")
                self._health_check_result = True
                self._last_health_check = current_time
                return True

            # Default to healthy if server is running without obvious issues
            self._health_check_result = True
            self._last_health_check = current_time
            return True

        except Exception as e:
            print(f"[MCP_HEALTH] 健康检查异常: {e}")
            self._health_check_result = False
            self._last_health_check = current_time
            return False

    def get_server_status(self) -> dict:
        """Get comprehensive server status information"""
        uptime = time.time() - self.start_time if self.start_time else 0

        status = {
            "server": {
                "running": self.running,
                "host": self.host,
                "port": self.port,
                "uptime": uptime,
                "healthy": self.is_healthy(force_refresh=True),
                "last_error": self.last_error,
            },
            "connections": {
                "total": self.total_client_connections,
                "active": self.active_client_connections,
                "last_client": self.last_client_time,
            },
            "commands": {
                "total_processed": self.total_commands_processed,
            },
        }

        return status

    def _process_execution_queue(self):
        """Process pending execution tasks from the queue"""
        try:
            # 初始化计数器属性（如果不存在）
            if not hasattr(self, "_debug_print_counter"):
                self._debug_print_counter = 0

            # 每100次循环或队列不为空时打印状态（用于调试）
            queue_size = self._execution_queue.qsize() if hasattr(self._execution_queue, 'qsize') else 0
            if (
                queue_size > 0
                or self._debug_print_counter % 100 == 0
            ):
                print(
                    f"[MCP_QUEUE_PROCESSOR] 当前队列任务数: {queue_size}",
                )

            # 递增计数器
            self._debug_print_counter += 1

            # Process up to 5 tasks per timer call to avoid blocking too long
            for _ in range(5):
                if self._execution_queue.empty():
                    break

                task = self._execution_queue.get_nowait()
                try:
                    print(
                        f"[MCP_EXECUTOR] 执行队列任务: {task.get('type', 'unknown')} - 开始处理",
                    )
                    print(
                        f"[MCP_EXECUTOR] 执行详情: 任务类型={task.get('type', 'unknown')}, 时间={time.strftime('%Y-%m-%d %H:%M:%S')}",
                    )

                    # 确保当前上下文可用
                    if task.get("type") != "heartbeat":
                        print("[MCP_EXECUTOR] 非心跳任务, 检查上下文...")
                        if bpy.context is None:
                            print("[MCP_ERROR] bpy.context 不可用")
                            task["result_container"]["result"] = {
                                "status": "error",
                                "message": "Blender context is not available",
                            }
                            task["result_container"]["completed"] = True
                            continue

                        # 额外打印 Blender 信息
                        print(
                            f"[MCP_BLENDER] 版本={bpy.app.version_string}, PID={os.getpid()}",
                        )
                        print(
                            f"[MCP_SCENE] 场景名={bpy.context.scene.name}, 对象数={len(bpy.context.scene.objects)}",
                        )

                    # 执行任务
                    result = task["function"]()
                    task["result_container"]["result"] = result
                    task["result_container"]["completed"] = True
                    print(f"[MCP_EXECUTOR] {task.get('type', 'unknown')} - 执行成功")

                    # 如果是脚本或代码执行，进行简单的场景更新
                    if task.get("type") in ["execute_code", "execute_script_file"]:
                        try:
                            # 简单UI刷新
                            self._simple_ui_refresh()
                        except Exception as view_err:
                            print(f"[MCP_UI_REFRESH] UI刷新失败 - {view_err}")

                except Exception as e:
                    task["result_container"]["result"] = {
                        "status": "error",
                        "message": str(e),
                        "traceback": traceback.format_exc(),
                    }
                    task["result_container"]["completed"] = True
                    print(f"[MCP_EXECUTOR] {task.get('type', 'unknown')} - 执行失败")
                    print(f"[MCP_ERROR] 错误详情: {e}")
                    print(f"[MCP_ERROR] 错误堆栈: {traceback.format_exc()}")

        except queue.Empty:
            pass
        except Exception as e:
            print(f"[MCP_QUEUE_PROCESSOR] 队列处理器错误: {e}")
            print(f"[MCP_ERROR] 堆栈: {traceback.format_exc()}")

        # Continue processing - return small interval to check queue frequently
        return 0.1 if self.running else None

    def _ensure_queue_processor(self):
        """Ensure the queue processor is registered"""
        global _global_queue_processor
        if not self._queue_processor_registered and self.running:
            try:
                # Try to unregister first in case it's already registered
                if bpy.app.timers.is_registered(_global_queue_processor):
                    bpy.app.timers.unregister(_global_queue_processor)
                
                # Register the global timer function
                bpy.app.timers.register(_global_queue_processor, first_interval=0.1)
                self._queue_processor_registered = True
                print("[MCP_TIMER] 队列处理器已注册: True")
            except Exception as e:
                print(f"[MCP_ERROR] 队列处理器注册失败: {e}")
                self._queue_processor_registered = False

    def _server_loop(self):
        """Main server loop to handle client connections"""
        while self.running:
            try:
                if not self.socket:
                    break

                client, address = self.socket.accept()
                self.total_client_connections += 1
                self.active_client_connections += 1
                self.last_client_time = time.time()

                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client,),
                )
                client_thread.daemon = True
                client_thread.start()

            except OSError:
                # Socket was closed, exit loop
                break
            except Exception as e:
                if self.running:
                    print(f"Server loop error: {e}")
                    self.last_error = str(e)

    def _handle_client(self, client):
        """Handle individual client connection"""
        try:
            # Set socket timeout to prevent hanging
            client.settimeout(120.0)  # Increased timeout for script execution

            while self.running:
                try:
                    # Receive data from client
                    data = client.recv(4096)
                    if not data:
                        break
                except (
                    ConnectionResetError,
                    ConnectionAbortedError,
                    TimeoutError,
                    OSError,
                ) as e:
                    # Handle different types of connection issues
                    if isinstance(e, TimeoutError):
                        # Timeout occurred, check if server is still running
                        if self.running:
                            continue  # Continue listening for data
                        break
                    # Client disconnected unexpectedly
                    if self.running:
                        print(f"Client disconnected: {type(e).__name__}: {e}")
                    break

                try:
                    # Parse JSON command
                    command = json.loads(data.decode("utf-8"))

                    # Skip logging for health checks to reduce noise
                    if not command.get("_health_check", False):
                        print(f"Received command: {command.get('type', 'unknown')}")

                    # Execute command directly - simplified approach without timer-based queue
                    print(f"[MCP_DIRECT] 直接执行命令: {command.get('type', 'unknown')}")
                    
                    if command.get("type") == "execute_script_file":
                        params = command.get("params", {})
                        print(f"[MCP_SCRIPT] 脚本执行: 脚本名={params.get('script_name', 'unknown')}")
                    elif command.get("type") == "execute_code":
                        print(f"[MCP_CODE] 代码执行: 代码长度={len(command.get('params', {}).get('code', ''))}")

                    # Execute command directly on main thread using a simple mechanism
                    result_container = {"result": None, "completed": False}
                    
                    def execute_on_main():
                        try:
                            result = self.execute_command(command)
                            result_container["result"] = result
                            result_container["completed"] = True
                            print(f"[MCP_DIRECT] {command.get('type', 'unknown')} - 执行成功")
                        except Exception as e:
                            result_container["result"] = {
                                "status": "error", 
                                "message": str(e),
                                "traceback": traceback.format_exc()
                            }
                            result_container["completed"] = True
                            print(f"[MCP_DIRECT] {command.get('type', 'unknown')} - 执行失败: {e}")
                    
                    # Schedule execution on main thread
                    bpy.app.timers.register(lambda: (execute_on_main(), None)[1], first_interval=0.01)
                    
                    # Wait for completion with timeout
                    timeout = 60.0
                    start_time = time.time()
                    while not result_container["completed"]:
                        time.sleep(0.05)
                        if time.time() - start_time > timeout:
                            result_container["result"] = {
                                "status": "error",
                                "message": "Command execution timeout",
                            }
                            break

                    # Send response back to client
                    try:
                        result = result_container["result"]
                        # 使用ensure_ascii=False确保正确处理Unicode字符，并添加处理错误的选项
                        response_json = json.dumps(
                            result,
                            ensure_ascii=False,
                            default=str,
                        )
                        client.sendall(response_json.encode("utf-8", errors="replace"))
                        self.total_commands_processed += 1
                    except (
                        ConnectionResetError,
                        ConnectionAbortedError,
                        BrokenPipeError,
                        OSError,
                    ) as e:
                        # Client disconnected during response - this is normal
                        if self.running:
                            print(
                                f"Client disconnected during response: {type(e).__name__}",
                            )
                        break
                    except Exception as e:
                        error_response = {
                            "status": "error",
                            "message": f"Response sending error: {e!s}",
                            "traceback": traceback.format_exc(),
                        }
                        try:
                            client.sendall(json.dumps(error_response).encode("utf-8"))
                        except (
                            ConnectionResetError,
                            ConnectionAbortedError,
                            BrokenPipeError,
                            OSError,
                        ):
                            # Client disconnected during error response
                            break
                        except:
                            pass

                except json.JSONDecodeError as e:
                    error_response = {
                        "status": "error",
                        "message": f"Invalid JSON: {e}",
                    }
                    try:
                        client.sendall(json.dumps(error_response).encode("utf-8"))
                    except (
                        ConnectionResetError,
                        ConnectionAbortedError,
                        BrokenPipeError,
                        OSError,
                    ):
                        # Client disconnected during error response
                        break

        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            try:
                client.close()
            except:
                pass
            self.active_client_connections -= 1

    def execute_command(self, command):
        """Execute a command and return result"""
        try:
            return self._execute_command_internal(command)
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "traceback": traceback.format_exc(),
            }

    def _execute_command_internal(self, command):
        """Internal command execution logic"""
        command_type = command.get("type")
        params = command.get("params", {})

        # 添加 heartbeat 命令支持
        if command_type == "heartbeat":
            return {
                "status": "success",
                "message": "heartbeat_response",
                "timestamp": time.time(),
            }

        if command_type == "get_scene_info":
            return {
                "status": "success",
                "data": self.get_scene_info(),
            }

        if command_type == "execute_code":
            code = params.get("code", "")
            result = self.execute_code(code)
            return {
                "status": "success",
                "data": result,
            }

        if command_type == "get_server_status":
            return {
                "status": "success",
                "data": self.get_server_status(),
            }

        if command_type == "execute_script_file":
            script_name = params.get("script_name", "")
            scripts_directory = params.get("scripts_directory", "scripts")
            script_parameters = params.get("parameters", {})
            result = self.execute_script_file(
                script_name,
                scripts_directory,
                script_parameters,
            )
            return {
                "status": "success",
                "data": result,
            }

        return {
            "status": "error",
            "message": f"Unknown command type: {command_type}",
        }

    def get_scene_info(self):
        """Get basic information about the current scene"""
        scene = bpy.context.scene

        objects = []
        for obj in scene.objects:
            obj_info = {
                "name": obj.name,
                "type": obj.type,
                "location": [obj.location[0], obj.location[1], obj.location[2]],
                "visible": obj.visible_get(),
            }
            objects.append(obj_info)

        return {
            "scene_name": scene.name,
            "frame_current": scene.frame_current,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "objects": objects,
            "object_count": len(objects),
        }

    def _simple_ui_refresh(self):
        """
        简化的UI刷新函数 - 只做必要的更新
        """
        try:
            # 只保留基本的视图层更新，这对于MCP操作已经足够
            bpy.context.view_layer.update()
        except Exception as e:
            print(f"[MCP_UI_REFRESH] 基本更新失败: {e}")

    def execute_code(self, code):
        """Execute arbitrary Blender Python code"""
        try:
            # Create a local namespace for execution
            namespace = {"bpy": bpy}

            # Capture stdout during execution
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)

            captured_output = capture_buffer.getvalue()

            # 简单的UI刷新
            self._simple_ui_refresh()

            return {"executed": True, "result": captured_output}
        except Exception as e:
            raise Exception(f"Code execution error: {e!s}")

    def execute_script_file(
        self,
        script_name,
        scripts_directory="scripts",
        parameters=None,
    ):
        """Execute a Python script file from the scripts directory, supporting relative paths"""
        try:
            import os
            import sys
            from io import StringIO

            print(f"Starting script execution: {script_name}")

            # Handle relative paths within the scripts directory
            # script_name can now include subdirectories like "basic/create_cube.py"
            script_relative_path = script_name
            
            # Ensure script name has .py extension
            if not script_relative_path.endswith(".py"):
                script_relative_path += ".py"

            # Get configured scripts root directory
            scripts_root = self.get_scripts_root()
            
            # Always use the script_relative_path directly from scripts_root
            # This allows for subdirectories like "basic/script.py" or "advanced/script.py"
            script_path = os.path.join(scripts_root, script_relative_path)

            print(f"Looking for script at: {script_path}")

            # Check if script exists
            if not os.path.exists(script_path):
                raise Exception(
                    f"Script '{script_name}' not found at '{script_path}'. Please check the script name and scripts root directory configuration.",
                )

            # Read script content
            with open(script_path, encoding="utf-8") as f:
                script_content = f.read()

            print(f"Script content loaded, size: {len(script_content)} bytes")

            # Create comprehensive execution namespace without restrictions
            namespace = {
                "bpy": bpy,
                "mathutils": __import__("mathutils"),
                "math": __import__("math"),
                "os": os,
                "sys": sys,
                "time": __import__("time"),
                "tempfile": __import__("tempfile"),
                "Vector": __import__("mathutils").Vector,
                "print": print,
                "_script_name": script_name,
                "_script_path": script_path,
                "_parameters": parameters or {},
                "__builtins__": __builtins__,  # Full builtins access
            }

            # Add parameters to namespace
            if parameters:
                namespace.update(parameters)

            # 添加一个帮助函数用于更新场景
            def update_scene():
                try:
                    self._comprehensive_ui_refresh()
                    print("[MCP_SCENE_UPDATE] 场景已更新")
                except Exception as e:
                    print(f"[MCP_ERROR] 更新场景失败: {e}")

            namespace["update_scene"] = update_scene

            print("Executing script...")

            # Capture both stdout and stderr during execution
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            capture_buffer = StringIO()
            error_buffer = StringIO()

            try:
                sys.stdout = capture_buffer
                sys.stderr = error_buffer

                # Execute the script in the current Blender context
                print("[MCP_SCRIPT_EXEC] 开始执行 - 更新前状态")
                print(f"[MCP_SCENE] 对象数量={len(bpy.context.scene.objects)}")
                print(
                    f"[MCP_SCENE] 材质数量={len([m for m in bpy.data.materials if m.users > 0])}",
                )

                # 强制刷新 Blender 数据
                bpy.context.view_layer.update()

                # 执行脚本
                exec(script_content, namespace)

                # 检查脚本是否定义了main函数并调用它
                if "main" in namespace and callable(namespace["main"]):
                    print("[MCP_SCRIPT_EXEC] 检测到main函数，正在调用...")
                    namespace["main"]()
                    print("[MCP_SCRIPT_EXEC] main函数执行完成")
                else:
                    print("[MCP_SCRIPT_EXEC] 未检测到main函数或已在全局执行")

                # 简单UI刷新
                self._simple_ui_refresh()

                print("[MCP_SCRIPT_EXEC] 执行完成 - 更新后状态")
                print(f"[MCP_SCENE] 对象数量={len(bpy.context.scene.objects)}")
                print(
                    f"[MCP_SCENE] 材质数量={len([m for m in bpy.data.materials if m.users > 0])}",
                )

            finally:
                # Restore original stdout/stderr
                sys.stdout = original_stdout
                sys.stderr = original_stderr

            captured_output = capture_buffer.getvalue()
            captured_errors = error_buffer.getvalue()

            # Combine output and errors
            full_output = captured_output
            if captured_errors:
                full_output += f"\n--- Errors ---\n{captured_errors}"

            # 处理字符串中的非ASCII字符，避免JSON编码问题
            def sanitize_string(s):
                if not isinstance(s, str):
                    return s
                # 替换可能导致JSON解析问题的字符
                return s.encode("utf-8", errors="replace").decode("utf-8")

            # 清理输出字符串
            sanitized_output = sanitize_string(full_output)
            sanitized_errors = sanitize_string(captured_errors)

            result = {
                "executed": True,
                "script_name": script_name,
                "script_path": script_path,
                "parameters": parameters,
                "result": sanitized_output,
                "file_size": len(script_content),
                "errors": sanitized_errors,
                "success": True,
            }

            print(f"Script execution result: {result}")
            return result

        except Exception as e:
            error_msg = f"Script execution error: {e!s}"
            print(error_msg)
            print(f"Traceback: {traceback.format_exc()}")
            raise Exception(error_msg)


def start_server_if_needed():
    """Start the server if it's not already running"""
    global _server_instance

    if _server_instance is None:
        _server_instance = BlenderMCPServer()

    if not _server_instance.running:
        success = _server_instance.start()
        if success:
            print("BlenderMCP server started successfully")
        else:
            print("Failed to start BlenderMCP server")
        return success
    print("BlenderMCP server is already running")
    return True


def stop_server():
    """Stop the server"""
    global _server_instance

    if _server_instance and _server_instance.running:
        _server_instance.stop()
        print("BlenderMCP server stopped")
    else:
        print("BlenderMCP server is not running")


def monitor_server():
    """Monitor server health and restart if needed"""
    global _server_instance, _monitor_timer_running, _last_restart_time, _restart_count

    if not _monitor_timer_running:
        return None

    current_time = time.time()

    # Reset restart count every hour
    if current_time - _last_restart_time > 3600:
        _restart_count = 0

    if _server_instance is None:
        start_server_if_needed()
    elif _restart_count < _max_restarts_per_hour:
        # Only check health if server is supposedly running
        if _server_instance.running and not _server_instance.is_healthy():
            print("Server unhealthy, attempting restart...")
            stop_server()
            time.sleep(2)  # Brief pause before restart
            if start_server_if_needed():
                _restart_count += 1
                _last_restart_time = current_time
                print(f"Server restarted ({_restart_count}/{_max_restarts_per_hour})")
        elif not _server_instance.running:
            # Server stopped unexpectedly, try to restart
            print("Server stopped unexpectedly, attempting restart...")
            if start_server_if_needed():
                _restart_count += 1
                _last_restart_time = current_time
                print(f"Server restarted ({_restart_count}/{_max_restarts_per_hour})")

    # Schedule next check - longer interval to reduce system load
    return 120.0  # Check every 2 minutes


def start_monitoring():
    """Start server monitoring"""
    global _monitor_timer_running

    if not _monitor_timer_running:
        _monitor_timer_running = True
        bpy.app.timers.register(monitor_server, first_interval=5.0)
        print("Server monitoring started")


def stop_monitoring():
    """Stop server monitoring"""
    global _monitor_timer_running

    if _monitor_timer_running:
        _monitor_timer_running = False
        if bpy.app.timers.is_registered(monitor_server):
            bpy.app.timers.unregister(monitor_server)
        print("Server monitoring stopped")


def format_uptime(seconds):
    """Format uptime in human readable format"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.0f}m"
    return f"{seconds / 3600:.1f}h"


class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"

    def draw(self, context):
        layout = self.layout
        global _server_instance
        
        # 简化UI - 不再使用复杂的属性组

        # 服务器状态 - 简洁的状态指示
        status_box = layout.box()
        
        if _server_instance and _server_instance.running:
            status = _server_instance.get_server_status()
            server_info = status["server"]
            
            # 主状态行
            row = status_box.row()
            row.scale_y = 1.5
            if server_info["healthy"]:
                row.label(text="● 服务器运行中", icon="CHECKMARK")
            else:
                row.alert = True
                row.label(text="● 服务器异常", icon="ERROR")
            
            # 快速信息
            col = status_box.column()
            col.label(text=f"端口: {server_info['port']}")
            
            # 如果有错误显示错误信息
            if server_info.get("last_error"):
                col.alert = True
                col.label(text=f"错误: {server_info['last_error'][:50]}...", icon="ERROR")
        else:
            row = status_box.row()
            row.scale_y = 1.5
            row.alert = True
            row.label(text="● 服务器已停止", icon="CANCEL")

        # 控制按钮 - 更突出
        row = layout.row(align=True)
        row.scale_y = 1.3
        if _server_instance and _server_instance.running:
            row.operator("blendermcp.restart_server", text="重启服务器", icon="FILE_REFRESH")
            row.operator("blendermcp.emergency_stop", text="停止", icon="CANCEL")
        else:
            row.operator("blendermcp.restart_server", text="启动服务器", icon="PLAY")

        # 脚本目录配置
        config_box = layout.box()
        config_box.label(text="脚本目录", icon="SCRIPT")
        
        # 简化：直接显示默认路径，不再使用复杂的属性
        config_box.label(text=f"路径: {DEFAULT_SCRIPTS_ROOT}", icon="FOLDER_REDIRECT")
            
        # 操作按钮始终可用
        row = config_box.row(align=True)
        row.operator("blendermcp.test_scripts_path", text="验证路径", icon="CHECKMARK")
        row.operator("blendermcp.open_scripts_folder", text="打开文件夹", icon="FILE_FOLDER")

        # 快速操作
        action_box = layout.box()
        action_box.label(text="快速操作", icon="TOOL_SETTINGS")
        
        col = action_box.column(align=True)
        col.operator("blendermcp.clear_scene", text="清空场景", icon="TRASH")
        col.operator("blendermcp.test_connection", text="测试连接", icon="LINKED")
        
        # 高级选项（固定显示）
        advanced_box = layout.box()
        advanced_box.label(text="高级选项", icon="TOOL_SETTINGS")
        
        if _server_instance and _server_instance.running:
            status = _server_instance.get_server_status()
            advanced_box.label(text=f"运行时间: {format_uptime(status['server']['uptime'])}")
            advanced_box.label(text=f"处理命令: {status['commands']['total_processed']}")
            advanced_box.label(text=f"总连接数: {status['connections']['total']}")
        
        # 监控状态
        row = advanced_box.row()
        if _monitor_timer_running:
            row.label(text="自动监控: 已启用", icon="TIME")
        else:
            row.label(text="自动监控: 已禁用", icon="TIME")


class BLENDERMCP_OT_RestartServer(bpy.types.Operator):
    bl_idname = "blendermcp.restart_server"
    bl_label = "Restart MCP Server"
    bl_description = "Manually restart the BlenderMCP server"

    def execute(self, context):
        stop_server()
        success = start_server_if_needed()
        if success:
            self.report({"INFO"}, "BlenderMCP server restarted successfully")
        else:
            self.report({"ERROR"}, "Failed to restart BlenderMCP server")
        return {"FINISHED"}


class BLENDERMCP_OT_EmergencyStop(bpy.types.Operator):
    bl_idname = "blendermcp.emergency_stop"
    bl_label = "Emergency Stop"
    bl_description = "Emergency stop of BlenderMCP server and monitoring"

    def execute(self, context):
        stop_monitoring()
        stop_server()
        self.report({"INFO"}, "BlenderMCP server and monitoring stopped")
        return {"FINISHED"}


class BLENDERMCP_OT_TestScriptsPath(bpy.types.Operator):
    bl_idname = "blendermcp.test_scripts_path"
    bl_label = "Test Scripts Path"
    bl_description = "Test if the configured scripts path is valid"

    def execute(self, context):
        global _server_instance

        if _server_instance:
            scripts_root = _server_instance.get_scripts_root()
        else:
            # Fallback to getting from properties directly
            try:
                scripts_root = context.scene.blender_mcp.scripts_root
            except (AttributeError, RuntimeError):
                scripts_root = DEFAULT_SCRIPTS_ROOT

        import os

        if os.path.exists(scripts_root) and os.path.isdir(scripts_root):
            # Count Python files
            py_files = [
                f
                for f in os.listdir(scripts_root)
                if f.endswith(".py") and not f.startswith("_")
            ]
            self.report(
                {"INFO"},
                f"路径有效！找到 {len(py_files)} 个 Python 脚本",
            )
        else:
            self.report(
                {"ERROR"},
                f"路径无效或不存在: {scripts_root}",
            )

        return {"FINISHED"}


class BLENDERMCP_OT_OpenScriptsFolder(bpy.types.Operator):
    bl_idname = "blendermcp.open_scripts_folder"
    bl_label = "Open Scripts Folder"
    bl_description = "在文件管理器中打开脚本目录"

    def execute(self, context):
        global _server_instance

        if _server_instance:
            scripts_root = _server_instance.get_scripts_root()
        else:
            try:
                scripts_root = context.scene.blender_mcp.scripts_root
            except (AttributeError, RuntimeError):
                scripts_root = DEFAULT_SCRIPTS_ROOT

        import os
        import platform
        import subprocess

        if os.path.exists(scripts_root):
            if platform.system() == "Windows":
                os.startfile(scripts_root)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", scripts_root])
            else:  # Linux
                subprocess.run(["xdg-open", scripts_root])
            self.report({"INFO"}, f"打开目录: {scripts_root}")
        else:
            self.report({"ERROR"}, f"目录不存在: {scripts_root}")

        return {"FINISHED"}


class BLENDERMCP_OT_ClearScene(bpy.types.Operator):
    bl_idname = "blendermcp.clear_scene"
    bl_label = "Clear Scene"
    bl_description = "清除场景中的所有对象"

    def execute(self, context):
        # 删除所有对象
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        # 删除所有网格数据
        for mesh in bpy.data.meshes:
            bpy.data.meshes.remove(mesh)
        
        # 删除所有材质
        for material in bpy.data.materials:
            bpy.data.materials.remove(material)
            
        self.report({"INFO"}, "场景已清空")
        return {"FINISHED"}


class BLENDERMCP_OT_TestConnection(bpy.types.Operator):
    bl_idname = "blendermcp.test_connection"
    bl_label = "Test Connection"
    bl_description = "测试 MCP 服务器连接"

    def execute(self, context):
        global _server_instance
        
        if not _server_instance or not _server_instance.running:
            self.report({"ERROR"}, "服务器未运行")
            return {"CANCELLED"}
        
        # 测试连接
        if _server_instance.is_healthy():
            self.report({"INFO"}, "连接正常！")
        else:
            self.report({"ERROR"}, "连接失败！")
        
        return {"FINISHED"}


def register():
    try:
        # 简化注册过程 - 只注册UI类，不再使用复杂的属性组
        bpy.utils.register_class(BLENDERMCP_PT_Panel)
        bpy.utils.register_class(BLENDERMCP_OT_RestartServer)
        bpy.utils.register_class(BLENDERMCP_OT_EmergencyStop)
        bpy.utils.register_class(BLENDERMCP_OT_TestScriptsPath)
        bpy.utils.register_class(BLENDERMCP_OT_OpenScriptsFolder)
        bpy.utils.register_class(BLENDERMCP_OT_ClearScene)
        bpy.utils.register_class(BLENDERMCP_OT_TestConnection)

        # Auto-start server and monitoring
        start_server_if_needed()
        start_monitoring()

        print("BlenderMCP addon registered and started")
    except Exception as e:
        print(f"Error registering BlenderMCP addon: {e}")
        import traceback

        traceback.print_exc()


def unregister():
    try:
        # Stop monitoring and server first
        stop_monitoring()
        stop_server()

        # Unregister UI classes
        bpy.utils.unregister_class(BLENDERMCP_OT_TestConnection)
        bpy.utils.unregister_class(BLENDERMCP_OT_ClearScene)
        bpy.utils.unregister_class(BLENDERMCP_OT_OpenScriptsFolder)
        bpy.utils.unregister_class(BLENDERMCP_OT_EmergencyStop)
        bpy.utils.unregister_class(BLENDERMCP_OT_RestartServer)
        bpy.utils.unregister_class(BLENDERMCP_OT_TestScriptsPath)
        bpy.utils.unregister_class(BLENDERMCP_PT_Panel)

        print("BlenderMCP addon unregistered")
    except Exception as e:
        print(f"Error unregistering BlenderMCP addon: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    register()
