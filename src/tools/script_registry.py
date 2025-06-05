"""
Simplified Script Registry System for Blender MCP

简化的脚本注册和管理系统，专注于执行效率和可靠性。
遵循CodeAct架构模式，emphasis on execute-code approach.
"""

import logging
from collections.abc import Callable
from typing import Any

try:
    from .utils import create_standard_response, execute_with_error_handling
except ImportError:
    # Fallback for Blender environment
    from utils import create_standard_response

logger = logging.getLogger(__name__)


class ScriptRegistry:
    """Simple script registry for core functionality only."""

    def __init__(self):
        self._scripts: dict[str, dict[str, Any]] = {}

    def register_script(
        self,
        name: str,
        func: Callable,
        description: str = "",
        category: str = "general",
    ) -> None:
        """Register a script in the registry."""
        self._scripts[name] = {
            "name": name,
            "function": func,
            "description": description,
            "category": category,
        }
        logger.info(f"Registered script: {name} in category: {category}")

    def get_script(self, name: str) -> dict[str, Any] | None:
        """Get script information."""
        return self._scripts.get(name)

    def list_scripts(self, category: str | None = None) -> list[dict[str, Any]]:
        """List all scripts or scripts in a specific category."""
        scripts = []
        for name, script_info in self._scripts.items():
            if category is None or script_info["category"] == category:
                scripts.append(
                    {
                        "name": name,
                        "description": script_info["description"],
                        "category": script_info["category"],
                    },
                )
        return scripts

    def execute_script(
        self,
        name: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a script by name."""
        script_info = self.get_script(name)
        if not script_info:
            return create_standard_response(
                success=False,
                error=f"Script '{name}' not found",
                data={"available_scripts": list(self._scripts.keys())},
            )

        try:
            func = script_info["function"]
            if parameters:
                result = func(**parameters)
            else:
                result = func()

            return result

        except Exception as e:
            return create_standard_response(
                success=False,
                error=f"Script execution failed: {e!s}",
                data={"script_name": name, "parameters": parameters},
            )

    def get_categories(self) -> dict[str, int]:
        """Get all categories and their script counts."""
        categories = {}
        for script_info in self._scripts.values():
            category = script_info["category"]
            categories[category] = categories.get(category, 0) + 1
        return categories


# Create global registry instances
script_registry = ScriptRegistry()


def register_script(
    name: str,
    func: Callable,
    description: str = "",
    category: str = "general",
) -> None:
    """Register a script to the global registry."""
    script_registry.register_script(name, func, description, category)


def register_all_scripts(registry: ScriptRegistry | None = None) -> None:
    """Register all core scripts to the registry."""
    if registry is None:
        registry = script_registry

    # Import and register base operations
    try:
        from .base_operations import register_scripts

        register_scripts(registry)
        logger.info("Successfully registered base operation scripts")
    except Exception as e:
        logger.error(f"Failed to register base operations: {e}")


def create_scene_template_scripts(registry: ScriptRegistry | None = None) -> None:
    """Create scene template scripts."""
    if registry is None:
        registry = script_registry

    logger.info("Scene template scripts registered via base_operations")
    # Template scripts are now part of base_operations.py
