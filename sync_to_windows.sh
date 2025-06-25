#!/bin/bash

# Blender MCP 插件自动同步脚本
# 用途：将Linux端修改的__init__.py同步到Windows的Blender插件目录并重启Blender

set -e  # 遇到错误立即退出

# 配置路径
LINUX_ADDON_PATH="/home/doer/data_files/mcps/blender-mcp-simplify/addon/__init__.py"
WINDOWS_ADDON_DIR="/mnt/c/Users/doer/AppData/Roaming/Blender Foundation/Blender/4.4/scripts/addons/blender-mcp"
WINDOWS_ADDON_PATH="$WINDOWS_ADDON_DIR/__init__.py"
BLENDER_START_SCRIPT="/mnt/d/data_files/video_scripts/start_blender_debug.ps1"
BLENDER_PROJECT_PATH="projects/linear_algebra/Linear_systems_in_two_unknowns/assets/Main.blend"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Blender MCP 插件同步脚本 ===${NC}"
echo -e "${YELLOW}开始同步 Linux 端修改到 Windows Blender 插件...${NC}"

# 1. 检查源文件是否存在
if [ ! -f "$LINUX_ADDON_PATH" ]; then
    echo -e "${RED}❌ 错误: 源文件不存在: $LINUX_ADDON_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 找到源文件: $LINUX_ADDON_PATH${NC}"

# 2. 检查目标目录是否存在
if [ ! -d "$WINDOWS_ADDON_DIR" ]; then
    echo -e "${RED}❌ 错误: Windows插件目录不存在: $WINDOWS_ADDON_DIR${NC}"
    echo -e "${YELLOW}请确保Blender插件已安装到正确位置${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 找到目标目录: $WINDOWS_ADDON_DIR${NC}"

# 3. 备份原有文件（如果存在）
if [ -f "$WINDOWS_ADDON_PATH" ]; then
    BACKUP_PATH="$WINDOWS_ADDON_PATH.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}📁 备份原有文件到: $BACKUP_PATH${NC}"
    cp "$WINDOWS_ADDON_PATH" "$BACKUP_PATH"
fi

# 4. 拷贝新文件
echo -e "${YELLOW}📋 拷贝文件: $LINUX_ADDON_PATH -> $WINDOWS_ADDON_PATH${NC}"
if cp "$LINUX_ADDON_PATH" "$WINDOWS_ADDON_PATH"; then
    echo -e "${GREEN}✅ 文件拷贝成功${NC}"
else
    echo -e "${RED}❌ 文件拷贝失败${NC}"
    exit 1
fi

# 5. 验证文件完整性
LINUX_SIZE=$(stat -c%s "$LINUX_ADDON_PATH")
WINDOWS_SIZE=$(stat -c%s "$WINDOWS_ADDON_PATH")

if [ "$LINUX_SIZE" -eq "$WINDOWS_SIZE" ]; then
    echo -e "${GREEN}✅ 文件大小验证通过 ($LINUX_SIZE bytes)${NC}"
else
    echo -e "${RED}❌ 文件大小不匹配: Linux($LINUX_SIZE) vs Windows($WINDOWS_SIZE)${NC}"
    exit 1
fi

# 6. 检查Blender启动脚本是否存在
if [ ! -f "$BLENDER_START_SCRIPT" ]; then
    echo -e "${RED}❌ 错误: Blender启动脚本不存在: $BLENDER_START_SCRIPT${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 找到Blender启动脚本: $BLENDER_START_SCRIPT${NC}"

# 7. 杀死现有的Blender进程（如果有）
echo -e "${YELLOW}🔄 检查并结束现有Blender进程...${NC}"
# 通过WSL执行Windows命令来杀死Blender进程
/mnt/c/Windows/System32/taskkill.exe //F //IM blender.exe //T 2>/dev/null || true
sleep 2

# 8. 启动Blender (使用新的WSL脚本)
WSL_RESTART_SCRIPT="/home/doer/data_files/mcps/blender-mcp-simplify/restart_blender_wsl.sh"

if [ -f "$WSL_RESTART_SCRIPT" ]; then
    echo -e "${YELLOW}🚀 使用WSL Blender重启脚本启动...${NC}"
    echo -e "${BLUE}脚本: $WSL_RESTART_SCRIPT${NC}"
    
    # 执行WSL Blender重启脚本
    if "$WSL_RESTART_SCRIPT" "$BLENDER_PROJECT_PATH"; then
        echo -e "${GREEN}✅ WSL Blender重启脚本执行完成${NC}"
    else
        echo -e "${RED}❌ WSL Blender重启脚本执行失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  WSL重启脚本不存在，使用传统方式...${NC}"
    echo -e "${BLUE}命令: powershell.exe -File \"$BLENDER_START_SCRIPT\" \"$BLENDER_PROJECT_PATH\"${NC}"
    
    # 切换到脚本目录并执行
    cd "/mnt/d/data_files/video_scripts"
    
    # 使用PowerShell执行启动脚本
    if /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -File "./start_blender_debug.ps1" "$BLENDER_PROJECT_PATH" & then
        echo -e "${GREEN}✅ Blender启动命令已执行${NC}"
        echo -e "${BLUE}📝 请查看Blender控制台输出以确认插件加载状态${NC}"
    else
        echo -e "${RED}❌ Blender启动失败${NC}"
        exit 1
    fi
fi

# 9. 完成提示
echo -e "${GREEN}🎉 同步完成！${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}操作摘要:${NC}"
echo -e "  📁 源文件: $LINUX_ADDON_PATH"
echo -e "  📁 目标文件: $WINDOWS_ADDON_PATH"
echo -e "  📁 备份文件: $BACKUP_PATH"
echo -e "  🚀 Blender项目: $BLENDER_PROJECT_PATH"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ 请在Blender中检查插件是否正常加载${NC}"