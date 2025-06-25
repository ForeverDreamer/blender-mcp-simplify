"""
Utility functions for Blender MCP tools

Provides standardized response formats and basic validation functions.
Enhanced with improved JSON handling to fix "Invalid JSON: Unterminated string" errors.
"""

import json
import logging
import socket
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class BlenderConnection:
    """Configuration for Blender socket connection."""

    host: str
    port: int
    timeout: float


logger = logging.getLogger(__name__)


def safe_json_dumps(data: dict[str, Any], **kwargs) -> str:
    """
    Safely serialize data to JSON with proper error handling.

    This function addresses common JSON serialization issues by:
    1. Using ensure_ascii=False to handle Unicode properly
    2. Adding fallback serialization methods
    3. Validating the result can be parsed

    Args:
        data: Dictionary to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string

    Raises:
        ValueError: If serialization fails

    """
    try:
        # First attempt: use ensure_ascii=False for better Unicode handling
        json_str = json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":"),
            **kwargs,
        )

        # Validate by attempting to parse
        json.loads(json_str)
        return json_str

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(f"First JSON serialization attempt failed: {e}")

        try:
            # Second attempt: with ensure_ascii=True (default)
            json_str = json.dumps(
                data,
                ensure_ascii=True,
                separators=(",", ":"),
                **kwargs,
            )

            # Validate by attempting to parse
            json.loads(json_str)
            return json_str

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(f"Second JSON serialization attempt failed: {e}")

            try:
                # Third attempt: manual string escaping for problematic code
                if "params" in data and "code" in data["params"]:
                    # Create a copy and escape the code string manually
                    data_copy = data.copy()
                    code = data["params"]["code"]

                    # Manual escaping for problematic characters
                    escaped_code = (
                        code.replace("\\", "\\\\")  # Escape backslashes first
                        .replace('"', '\\"')  # Escape double quotes
                        .replace("\n", "\\n")  # Escape newlines
                        .replace("\r", "\\r")  # Escape carriage returns
                        .replace("\t", "\\t")
                    )  # Escape tabs

                    data_copy["params"] = data["params"].copy()
                    data_copy["params"]["code"] = escaped_code

                    json_str = json.dumps(data_copy, ensure_ascii=True)

                    # Note: We don't validate this one since the code is manually escaped
                    # The receiving end will need to handle the escaping
                    logger.info("Used manual string escaping for JSON serialization")
                    return json_str
                raise

            except Exception as e:
                logger.error(f"All JSON serialization attempts failed: {e}")
                raise ValueError(f"Failed to serialize data to JSON: {e}")


def get_windows_host_ip() -> str:
    """获取Windows宿主机IP地址"""
    try:
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if 'nameserver' in line:
                    return line.split()[1]
    except Exception:
        pass
    return '127.0.0.1'


def send_command(
    command: dict[str, Any],
    connection: BlenderConnection,
) -> dict[str, Any]:
    """
    通过 socket 连接向 Blender 发送命令。
    Enhanced with improved JSON handling and better error recovery.
    Fixed WSL2 bidirectional communication issue.

    Args:
        command: 要发送的命令字典
        connection: Blender连接配置

    Returns:
        Blender服务器的响应字典

    """
    max_retries = 3
    retry_delay = 1.0
    
    # 在WSL2环境中，使用Windows宿主机IP
    host = get_windows_host_ip() if connection.host in ['localhost', '127.0.0.1'] else connection.host
    
    for attempt in range(max_retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(connection.timeout)
                
                # 设置socket选项以改善连接稳定性
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                try:
                    sock.connect((host, connection.port))
                    logger.debug(f"Connected to {host}:{connection.port}")
                except ConnectionRefusedError:
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection refused to {host}:{connection.port}, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise

                # 使用改进的JSON序列化
                try:
                    command_json = safe_json_dumps(command)
                except ValueError as e:
                    logger.error(f"JSON serialization failed: {e}")
                    return {"success": False, "error": f"JSON serialization failed: {e}"}

                # 发送命令
                sock.sendall(command_json.encode("utf-8"))
                logger.debug(f"Sent command: {command.get('command', 'unknown')}")

                # 接收响应 - 改进的响应处理逻辑
                response_data = b""
                start_time = time.time()
                
                # 等待初始响应
                sock.settimeout(2.0)  # 短超时等待响应开始
                
                try:
                    # 首先等待一些数据到达
                    initial_chunk = sock.recv(1024)
                    if initial_chunk:
                        response_data += initial_chunk
                        
                        # 如果看起来是完整的JSON，尝试解析
                        try:
                            response_str = response_data.decode("utf-8")
                            if response_str.strip():
                                result = json.loads(response_str)
                                logger.debug(f"Received complete response: {len(response_str)} chars")
                                return result
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # 不是完整的JSON，继续接收
                            pass
                        
                        # 继续接收剩余数据
                        sock.settimeout(connection.timeout)
                        while True:
                            try:
                                chunk = sock.recv(8192)
                                if not chunk:
                                    break
                                response_data += chunk
                                
                                # 检查是否接收到完整的JSON
                                try:
                                    response_str = response_data.decode("utf-8")
                                    result = json.loads(response_str)
                                    logger.debug(f"Received complete response: {len(response_str)} chars")
                                    return result
                                except (json.JSONDecodeError, UnicodeDecodeError):
                                    # 还没有接收到完整的数据，继续接收
                                    continue
                                    
                            except socket.timeout:
                                # 超时，检查是否有可用数据
                                if time.time() - start_time > connection.timeout:
                                    break
                                continue
                            except socket.error:
                                break
                    else:
                        # 没有接收到初始数据
                        logger.warning("No initial response received")
                        
                except socket.timeout:
                    logger.warning("Timeout waiting for initial response")
                except socket.error as e:
                    logger.error(f"Socket error during response: {e}")

                # 最后尝试解析接收到的数据
                if response_data:
                    try:
                        response_str = response_data.decode("utf-8")
                        if response_str.strip():
                            result = json.loads(response_str)
                            logger.debug(f"Parsed final response: {len(response_str)} chars")
                            return result
                        else:
                            logger.warning("Received empty response")
                            return {"success": False, "error": "Empty response received from server"}
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.error(f"Failed to parse response: {e}")
                        logger.error(f"Response data: {response_data[:500]}...")
                        return {
                            "success": False,
                            "error": f"Invalid response format: {e}",
                            "raw_response": response_data.decode("utf-8", errors="replace")[:500],
                        }
                else:
                    logger.warning("No response received from server")
                    return {"success": False, "error": "No response received from server"}

        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Blender 连接失败: {e}, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                continue
            else:
                logger.error(f"Blender 连接失败 after {max_retries} attempts: {e}")
                return {"success": False, "error": str(e)}


def create_standard_response(
    success: bool = True,
    message: str = "",
    data: Any = None,
    error: str = "",
    execution_time: float = 0.0,
    **kwargs,
) -> dict[str, Any]:
    """
    Create standardized response format for all Blender MCP tools.

    Args:
        success: Whether the operation succeeded
        message: Human-readable message
        data: Result data
        error: Error message if failed
        execution_time: Time taken for execution
        **kwargs: Additional response fields

    """
    response = {
        "success": success,
        "timestamp": time.time(),
        "execution_time": execution_time,
    }

    if message:
        response["message"] = message

    if success:
        if data is not None:
            response["data"] = data
    else:
        response["error"] = error or "Unknown error occurred"

    # Add any additional fields
    response.update(kwargs)

    return response


def execute_with_error_handling(
    func: Callable,
    *args,
    operation_name: str = "operation",
    **kwargs,
) -> dict[str, Any]:
    """
    Execute a function with standardized error handling and timing.

    Args:
        func: Function to execute
        *args: Function arguments
        operation_name: Name of the operation for error reporting
        **kwargs: Function keyword arguments

    """
    start_time = time.time()

    try:
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        if isinstance(result, dict) and "success" in result:
            # Already formatted response
            result["execution_time"] = execution_time
            return result
        # Raw result, wrap in standard format
        return create_standard_response(
            success=True,
            message=f"{operation_name} completed successfully",
            data=result,
            execution_time=execution_time,
        )

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = str(e)

        # Add traceback in debug mode
        if hasattr(e, "__traceback__"):
            error_msg += f"\n{traceback.format_exc()}"

        return create_standard_response(
            success=False,
            error=f"{operation_name} failed: {error_msg}",
            execution_time=execution_time,
        )


def validate_blender_context():
    """Validate that we're in a proper Blender context."""
    try:
        import bpy

        if bpy.context is None:
            raise RuntimeError("No Blender context available")
        return True
    except ImportError:
        raise RuntimeError("Blender Python API not available")


def validate_object_exists(object_name: str) -> bool:
    """Check if an object exists in the current scene."""
    import bpy

    return object_name in bpy.data.objects


def get_safe_name(base_name: str, existing_names: list[str]) -> str:
    """Generate a unique name by appending numbers if necessary."""
    if base_name not in existing_names:
        return base_name

    counter = 1
    while f"{base_name}.{counter:03d}" in existing_names:
        counter += 1

    return f"{base_name}.{counter:03d}"


def validate_enum_choice(
    value: str,
    valid_choices: list[str],
    param_name: str = "parameter",
):
    """Validate that a value is in the list of valid choices."""
    if value not in valid_choices:
        raise ValueError(f"{param_name} must be one of {valid_choices}, got '{value}'")


def validate_numeric_range(
    value: float,
    min_val: float | None = None,
    max_val: float | None = None,
    param_name: str = "parameter",
):
    """Validate that a numeric value is within a specified range."""
    if min_val is not None and value < min_val:
        raise ValueError(f"{param_name} must be >= {min_val}, got {value}")
    if max_val is not None and value > max_val:
        raise ValueError(f"{param_name} must be <= {max_val}, got {value}")
