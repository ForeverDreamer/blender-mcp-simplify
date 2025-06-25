# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## General

- Start all chats with 🤖
- Respond in simplified Chinese, but keep all code modifications in English

## Standard Workflow

1. First think through the problem, read the codebase for relevant files, and write a plan to todo.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Please every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Finally, add a review section to the todo.md file with a summary of the changes you made and any other relevant information.

## Directory Operations

- Before using cd command, always check current path using pwd
- Verify directory exists before changing to it
- Use absolute paths when possible to ensure accuracy

## Script Execution Rules

- When executing `sync_to_windows.sh` or `restart_blender_wsl.sh`, always run them in a new terminal to avoid blocking the current session
- Use commands like `gnome-terminal -- bash -c './script_name.sh'` or similar terminal spawning methods
- These scripts are long-running processes that should not block the interactive session

## Basic Package Management Commands

- Use `uv` as the primary package management tool
- Install a package: `uv add <package>`
- Install a development dependency: `uv add --dev <package>`
- Install from a requirements file: `uv add --requirements requirements.txt`
- Uninstall a package: `uv remove <package>`
- Show package information: `uv pip show <package>`
- List installed packages: `uv pip list`
- Sync all dependencies: `uv sync`
- Sync only development dependencies: `uv sync --only-dev`
- Sync a specific dependency group: `uv sync --only-group test`
- Create or update the lock file: `uv lock`
- Update the locked version of a specific package: `uv lock --update requests`
- Run a command: `uv run <command>`

## Project Overview

This is a **Blender MCP (Model Context Protocol) Server** that enables AI assistants to interact with Blender programmatically. The system uses a simplified "execute-code" architecture with a two-process design: an MCP server process communicating with a Blender process via socket connection on port 9876.

## Development Commands

### Core Commands

- `python main.py` - Start the MCP server
- `uv run python main.py` - Start with UV package manager
- `uv sync` - Install dependencies
- `uv sync --extra all` - Install with all development dependencies

### Testing

- `python test_tools.py` - Test core MCP tools
- `python test_script_execution.py` - Test script execution

### Blender Setup

- `.\start_blender_debug.ps1` - Start Blender with debug console (Windows)
- Install addon from `addon/` directory in Blender
- Configure scripts directory path in Blender UI panel

## Architecture

### Two-Process Design

1. **MCP Server Process** (`main.py`) - Handles MCP protocol communication
2. **Blender Process** - Runs with addon providing socket server on localhost:9876

### Core Components

- `src/server.py` - Main MCP server using FastMCP framework
- `src/tools/` - Tool implementations (code execution, scene info, PolyHaven integration)
- `addon/` - Complete Blender addon with socket server and UI
- `scripts/` - Python scripts for Blender automation

### Key Tools

- `execute_blender_code` - Execute Python code directly in Blender
- `execute_blender_script_file` - Execute scripts from scripts directory
- `get_blender_scene_info` - Get scene information
- `get_blender_server_status` - Monitor server health

## Development Patterns

### Execute-Code Paradigm

The system emphasizes direct Python code execution in Blender rather than numerous predefined tools. This follows the CodeAct approach for maximum flexibility.

### Queue-Based Execution

The Blender addon uses a queue system to handle commands on the main thread, preventing blocking and ensuring thread safety.

### Enhanced JSON Handling

The system includes robust JSON serialization (`src/tools/utils.py`) to handle Unicode characters and complex Blender data structures.

## Configuration

### Scripts Directory

- Default: `D:\data_files\mcps\blender-mcp-simplify\scripts`
- Configurable via Blender addon UI
- Store reusable Python scripts here for execution

### Socket Communication

- Port: 9876 (localhost)
- Automatic reconnection on failure
- Health monitoring and restart capabilities

## Resource Templates

The system provides structured templates in `src/resources.py`:

- Scene templates (basic cube, complete scenes)
- Material presets (metal, glass, etc.)
- Rendering configurations
- Animation templates

## Important Files

- `pyproject.toml` - Dependencies and project configuration
- `src/prompts.py` - Structured prompts for common Blender tasks
- `addon/__init__.py` - Complete Blender addon implementation
- `src/tools/utils.py` - Enhanced JSON handling and socket utilities

## Debugging

- Use `start_blender_debug.ps1` for full console output
- Monitor server status through Blender addon UI panel
- Check MCP server logs for communication issues
- Scripts directory path must be correctly configured in Blender
