# WSL环境下Blender MCP配置指南

## 问题分析

在WSL环境中测试Blender MCP时发现网络连接问题：

1. **环境情况**：Claude Code运行在WSL，Blender运行在Windows宿主机
2. **连接问题**：WSL中的`localhost`无法访问Windows宿主机的`localhost:9876`
3. **解决方案**：使用Windows宿主机IP地址替代localhost

## 自动修复

已创建自动检测和修复机制：

### 1. 配置文件 (`config.py`)
- 自动检测WSL环境
- 获取Windows宿主机IP (通常是 `192.168.112.1`)
- 动态配置Blender连接参数

### 2. 工具文件更新
- `src/tools/base_tools.py` - 更新默认连接参数
- `src/tools/code_tools.py` - 更新代码执行连接参数

## 当前状态

✅ **已完成**：
- WSL环境检测和配置
- 连接参数自动修复
- Windows宿主机IP自动获取 (`192.168.112.1`)

❌ **待解决**：
- Windows防火墙可能阻止9876端口
- Blender addon可能未启动或配置错误

## 下一步操作

### 1. 在Windows宿主机上：

```powershell
# 检查Blender是否运行，MCP addon是否启用
# 检查Windows防火墙设置，确保9876端口开放

# 临时开放端口（管理员权限）
netsh advfirewall firewall add rule name="Blender MCP" dir=in action=allow protocol=TCP localport=9876
```

### 2. 在Blender中：
- 确保MCP addon已安装并启用
- 检查addon面板显示服务器状态为"Running"
- 验证端口配置为9876

### 3. 测试连接：

```bash
# 在WSL中测试
nc -zv 192.168.112.1 9876

# 或使用Python测试
python -c "
import socket
try:
    sock = socket.socket()
    sock.settimeout(3)
    sock.connect(('192.168.112.1', 9876))
    print('连接成功！')
except:
    print('连接失败 - 检查Blender和防火墙')
finally:
    sock.close()
"
```

## 技术细节

### IP地址获取方法：
1. 读取 `/etc/resolv.conf` 中的nameserver
2. 解析 `ip route show default` 输出
3. 默认回退到 `192.168.112.1`

### 连接超时设置：
- 默认超时：10秒
- 代码执行：30秒  
- 脚本执行：60秒

## 故障排除

如果连接仍然失败：

1. **检查Windows IP**：
   ```bash
   cat /etc/resolv.conf | grep nameserver
   ```

2. **手动测试端口**：
   ```bash
   telnet 192.168.112.1 9876
   ```

3. **检查Blender日志**：
   查看Blender控制台是否有MCP服务器启动信息

4. **重启服务**：
   在Blender addon面板中重启MCP服务器