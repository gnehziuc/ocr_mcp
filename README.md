# 基于ddddocr的MCP验证码识别服务器

一个遵循MCP（Model Context Protocol）标准的验证码识别服务器，使用ddddocr库提供高精度的图形验证码识别功能。

## 功能特性

- ✅ **高精度识别**: 基于ddddocr引擎，支持多种验证码类型
- ✅ **MCP标准协议**: 完全遵循Model Context Protocol规范
- ✅ **双传输模式**: 支持stdio（IDE集成）和SSE（Web服务）
- ✅ **多格式支持**: 支持PNG、JPG、JPEG、BMP、GIF、WebP等图片格式
- ✅ **异步处理**: 高性能异步架构，支持并发请求
- ✅ **完善日志**: 结构化日志记录，便于调试和监控
- ✅ **错误处理**: 完善的异常处理和错误信息返回

## 环境要求

- Python 3.10+
- 支持的操作系统：Windows、Linux、macOS

## 快速开始

### 方式一：NPX 快速安装（推荐）

使用 npx 可以快速安装和配置 MCP 服务器：

```bash
# 全局安装
npx @gnehziuc/ddddocr-mcp-server

# 或者直接运行
npx @gnehziuc/ddddocr-mcp-server start
```

#### IDE 集成配置

**Claude Desktop 配置**：

1. 打开 Claude Desktop 配置文件：
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. 添加 MCP 服务器配置：

```json
{
  "mcpServers": {
    "ddddocr-captcha": {
      "command": "npx",
      "args": ["@gnehziuc/ddddocr-mcp-server", "start", "--transport", "stdio"],
      "env": {}
    }
  }
}
```

**VS Code 配置**：

1. 安装 MCP 扩展
2. 在设置中添加服务器配置：

```json
{
  "mcp.servers": {
    "ddddocr-captcha": {
      "command": "npx",
      "args": ["@gnehziuc/ddddocr-mcp-server", "start", "--transport", "stdio"]
    }
  }
}
```

**其他 IDE 配置**：

对于支持 MCP 协议的其他 IDE，使用以下命令配置：

```bash
# 命令
npx @gnehziuc/ddddocr-mcp-server start --transport stdio

# 或指定配置文件
npx @gnehziuc/ddddocr-mcp-server start --config /path/to/config.yaml
```

### 方式二：本地开发安装

```bash
# 克隆或下载项目到本地
cd free_ocr

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 配置服务器

编辑 `config.yaml` 文件（可选，使用默认配置即可）：

```yaml
server:
  name: "ddddocr-mcp-server"
  version: "1.0.0"
  transport: "stdio"  # stdio 或 sse
  host: "localhost"
  port: 8080

recognition:
  engine: "ddddocr"
  max_image_size: 5242880  # 5MB
  timeout: 30

logging:
  level: "INFO"
  file: "logs/mcp_server.log"
```

### 3. 启动服务器

#### 方式一：使用启动脚本（推荐）

```bash
# 使用默认配置启动
python start.py

# 使用自定义配置
python start.py --config custom.yaml

# 使用SSE传输方式
python start.py --transport sse

# 自定义主机和端口
python start.py --transport sse --host 0.0.0.0 --port 9000

# 查看帮助
python start.py --help
```

#### 方式二：直接运行主程序

```bash
python server.py
```

## 使用方法

### MCP客户端调用

服务器提供三个MCP工具函数：

1. `recognize_captcha` - 识别base64编码的验证码图片
2. `recognize_captcha_from_file` - 从文件路径识别验证码
3. `recognize_captcha_batch` - 批量识别多个验证码文件

#### 工具函数规范

**函数名**: `recognize_captcha`

**参数**:
- `image_data` (string, 必需): 验证码图片数据（base64编码）
- `image_format` (string, 可选): 图片数据格式，默认为"base64"

**返回值**:
```json
{
  "success": true,
  "text": "A3B7",
  "confidence": 0.95,
  "processing_time": 0.12,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**函数名**: `recognize_captcha_from_file`

**参数**:
- `file_path` (string, 必需): 验证码图片文件的完整路径

**返回值**:
```json
{
  "success": true,
  "file_path": "/path/to/captcha.png",
  "text": "A3B7",
  "confidence": 0.95,
  "processing_time": 0.15,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**函数名**: `recognize_captcha_batch`

**参数**:
- `file_paths` (array, 必需): 验证码图片文件路径列表（最多10个）

**返回值**:
```json
{
  "success": true,
  "total_files": 3,
  "successful_count": 2,
  "failed_count": 1,
  "results": [
    {
      "success": true,
      "file_path": "/path/to/captcha1.png",
      "text": "A3B7",
      "confidence": 0.95,
      "processing_time": 0.12
    }
  ],
  "total_processing_time": 0.45,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### 调用示例

**Python MCP客户端示例**:

```python
import asyncio
import base64
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

async def test_captcha_recognition():
    # 读取验证码图片
    with open("captcha.png", "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    # 连接MCP服务器
    async with stdio_client() as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化
            await session.initialize()
            
            # 调用验证码识别工具
            result = await session.call_tool(
                "recognize_captcha",
                {
                    "image_data": image_data,
                    "image_format": "base64"
                }
            )
            
            print(f"识别结果: {result}")

# 运行测试
asyncio.run(test_captcha_recognition())
```

### 传输方式说明

#### stdio模式（默认）
- 适用于IDE集成、命令行工具等场景
- 通过标准输入输出进行通信
- 启动后等待MCP客户端连接

#### SSE模式
- 适用于Web服务部署
- 基于HTTP Server-Sent Events
- 可通过HTTP接口访问

## 项目结构

```
free_ocr/
├── .trae/
│   └── documents/          # 项目文档
│       ├── product_requirements.md
│       └── technical_architecture.md
├── logs/                   # 日志文件目录（自动创建）
├── config.yaml            # 配置文件
├── requirements.txt       # Python依赖
├── server.py              # MCP服务器主程序
├── start.py               # 启动脚本
└── README.md              # 使用说明
```

## 配置说明

### 服务器配置
- `server.name`: 服务器名称
- `server.version`: 服务器版本
- `server.transport`: 传输方式（stdio/sse）
- `server.host`: SSE模式下的主机地址
- `server.port`: SSE模式下的端口号

### 识别配置
- `recognition.engine`: 识别引擎（固定为ddddocr）
- `recognition.max_image_size`: 最大图片大小（字节）
- `recognition.supported_formats`: 支持的图片格式
- `recognition.timeout`: 识别超时时间（秒）

### 日志配置
- `logging.level`: 日志级别（DEBUG/INFO/WARNING/ERROR）
- `logging.format`: 日志格式
- `logging.file`: 日志文件路径
- `logging.max_size`: 日志文件最大大小
- `logging.backup_count`: 日志文件备份数量

## 错误处理

服务器提供完善的错误处理机制：

### 常见错误类型
1. **参数错误**: 缺少必需参数或参数格式错误
2. **图片错误**: 无效的图片数据或不支持的格式
3. **大小限制**: 图片大小超过配置限制
4. **识别失败**: OCR引擎识别过程中的错误
5. **系统错误**: 服务器内部错误

### 错误响应格式
```json
{
  "success": false,
  "text": "",
  "confidence": 0.0,
  "processing_time": 0.0,
  "error": "错误描述信息",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

## 性能优化

1. **延迟加载**: OCR引擎在首次使用时才初始化
2. **异步处理**: 支持并发请求处理
3. **内存管理**: 及时释放图片数据内存
4. **日志优化**: 结构化日志，避免性能影响

## 故障排除

### 常见问题

**Q: 启动时提示"ddddocr库未安装"**
A: 运行 `pip install ddddocr` 安装依赖

**Q: 识别准确率不高**
A: ddddocr对不同类型验证码的识别效果可能不同，可以尝试预处理图片（如去噪、二值化等）

**Q: SSE模式无法访问**
A: 检查防火墙设置，确保端口未被占用

**Q: 内存占用过高**
A: 检查图片大小限制配置，避免处理过大的图片

### 调试模式

启用调试日志：
```yaml
logging:
  level: "DEBUG"
```

## 许可证

本项目基于MIT许可证开源。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 更新日志

### v1.0.0 (2024-01-15)
- 初始版本发布
- 实现基础的验证码识别功能
- 支持MCP协议标准
- 支持stdio和SSE传输方式
- 完善的错误处理和日志记录