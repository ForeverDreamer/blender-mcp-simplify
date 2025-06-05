"""
Execution Result Manager for Blender MCP Server.

Manages script execution results and provides result formatting capabilities.
"""

from datetime import datetime
from typing import Any

from .types import ExecutionResult


class ExecutionResultManager:
    """Manages script execution results and history."""

    def __init__(self):
        self._last_result: ExecutionResult | None = None

    def store_result(
        self,
        script: str,
        parameters: dict[str, Any] | None,
        result: dict[str, Any],
        validation_info: dict[str, Any] | None = None,
    ) -> None:
        """Store the result of a script execution."""
        self._last_result = ExecutionResult(
            script=script,
            parameters=parameters,
            result=result,
            timestamp=datetime.now().isoformat(),
            validation_info=validation_info,
        )

    def get_last_result(self) -> ExecutionResult | None:
        """Get the last execution result."""
        return self._last_result

    def format_result(
        self, format_type: str = "formatted", include_metadata: bool = True
    ) -> dict[str, Any]:
        """Format the last execution result for output."""
        if not self._last_result:
            return {
                "success": False,
                "error": "No previous script execution found",
            }

        if format_type == "raw":
            return self._last_result.__dict__

        if format_type == "summary":
            result = self._last_result.result
            summary = {
                "script": self._last_result.script,
                "success": result.get("success", False),
                "message": result.get("message", "No message"),
            }
            if include_metadata:
                summary["timestamp"] = self._last_result.timestamp
            return summary

        if format_type == "debug":
            return self._last_result.__dict__

        # Default: formatted
        result = self._last_result.result
        formatted = {
            "execution_info": {
                "script": self._last_result.script,
                "parameters": self._last_result.parameters,
                "timestamp": self._last_result.timestamp if include_metadata else None,
            },
            "result": result,
        }

        if self._last_result.validation_info and include_metadata:
            formatted["validation_info"] = self._last_result.validation_info

        return formatted

    def clear_results(self) -> None:
        """Clear stored execution results."""
        self._last_result = None
