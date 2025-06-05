"""
Simplified Blender MCP Tools Package

Core tools following CodeAct paradigm with emphasis on execute-code approach.
"""

# Core essential modules only
from .base_operations import *
from .polyhaven_tools import *
from .script_registry import script_registry

__all__ = [
    # Base operations - core functionality
    "get_scene_info",
    "clear_scene",
    "execute_code",
    "create_scene_template",
    "get_code_templates",
    # PolyHaven integration
    "search_polyhaven_assets",
    "download_polyhaven_asset",
    # Registry
    "script_registry",
]
