"""
Utility functions for Blender MCP tools

Provides standardized response formats and basic validation functions.
Simplified for CodeAct paradigm following MCP 2024 best practices.
"""

import time
import traceback
from collections.abc import Callable
from typing import Any


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
