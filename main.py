#!/usr/bin/env python3
"""
启动Blender MCP服务器
"""

import os
import sys

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.server import main

if __name__ == "__main__":
    main()
